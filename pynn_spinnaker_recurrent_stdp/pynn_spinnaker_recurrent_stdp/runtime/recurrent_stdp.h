#pragma once

// Standard includes
#include <cstdint>
#include <cstring>

// Common includes
#include "common/exp_decay_lut.h"
#include "common/fixed_point_number.h"
#include "common/inverse_transform_sample_lut.h"
#include "common/log.h"

// Synapse processor includes
#include "synapse_processor/plasticity/post_events.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// ExtraModels::RecurrentSTDP
//-----------------------------------------------------------------------------
namespace ExtraModels
{
template<typename C, unsigned int D, unsigned int I,
  unsigned int TauALUTNumEntries, unsigned int TauALUTShift,
  unsigned int T,
  typename RNG>
class RecurrentSTDP
{
private:
  //-----------------------------------------------------------------------------
  // Unions
  //-----------------------------------------------------------------------------
  union Pair
  {
    Pair(){}
    Pair(uint16_t a, uint16_t b) : m_HalfWords{a, b} {}
    Pair(uint32_t w) : m_Word(w) {}

    uint16_t m_HalfWords[2];
    uint32_t m_Word;
  };

  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef Pair PlasticSynapse;
  typedef uint16_t Trace;
  typedef Trace PreTrace;
  typedef Trace PostTrace;
  typedef SynapseProcessor::Plasticity::PostEventHistory<PostTrace, T> PostEventHistory;
  typedef Common::InverseTransformSampleLUT<11, uint16_t, uint32_t, RNG> ExpDistLUT;

  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const unsigned int PreTraceWords = (sizeof(PreTrace) / 4) + (((sizeof(PreTrace) % 4) == 0) ? 0 : 1);
  static const uint32_t DelayMask = ((1 << D) - 1);
  static const uint32_t IndexMask = ((1 << I) - 1);

public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  // One word for a synapse-count, two delay words, a time of last update, 
  // time and trace associated with last presynaptic spike and 512 synapses
  static const unsigned int MaxRowWords = 256 + 5 + PreTraceWords;

  //-----------------------------------------------------------------------------
  // Public methods
  //-----------------------------------------------------------------------------
  template<typename F, typename E, typename R>
  bool ProcessRow(uint tick, uint32_t (&dmaBuffer)[MaxRowWords], uint32_t *sdramRowAddress, bool flush,
                  F applyInputFunction, E addDelayRowFunction, R writeBackRowFunction)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\tProcessing recurrent STDP row with %u synapses at tick:%u (flush:%u)",
              dmaBuffer[0], tick, flush);

    // If this row has a delay extension, call function to add it
    if(dmaBuffer[1] != 0)
    {
      addDelayRowFunction(dmaBuffer[1] + tick, dmaBuffer[2], flush);
    }

    // Get time of last update from DMA buffer and write back updated time
    const uint32_t lastUpdateTick = dmaBuffer[3];
    dmaBuffer[3] = tick;

    // Get time of last presynaptic spike and associated trace entry from DMA buffer
    const uint32_t lastPreTick = dmaBuffer[4];
    const PreTrace lastPreTrace = GetPreTrace(dmaBuffer);

    // If this is an actual spike (rather than a flush event)
    PreTrace newPreTrace;
    if(!flush)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tAdding pre-synaptic event to trace at tick:%u",
                tick);
      // Calculate new pre-trace
      newPreTrace = UpdateTrace(tick, lastPreTrace, lastPreTick,
                                m_PreExpDistLUT);

      // Write back updated last presynaptic spike time and trace to row
      dmaBuffer[4] = tick;
      SetPreTrace(dmaBuffer, newPreTrace);
    }

    // Extract first plastic and control words; and loop through synapses
    uint32_t count = dmaBuffer[0];
    PlasticSynapse *plasticWords = GetPlasticWords(dmaBuffer);
    const C *controlWords = GetControlWords(dmaBuffer, count);
    for(; count > 0; count--)
    {
      // Get the next control word from the synaptic_row
      // (should autoincrement pointer in single instruction)
      const uint32_t controlWord = *controlWords++;

      // Extract control word components
      const uint32_t delayDendritic = GetDelay(controlWord);
      const uint32_t delayAxonal = 0;
      const uint32_t postIndex = GetIndex(controlWord);

      // Extract accumulator and weight components of plastic word
      S2011 accumulator = (int32_t)plasticWords->m_HalfWords[1];
      int32_t weight = (int32_t)plasticWords->m_HalfWords[0];

      // Apply axonal delay to last presynaptic spike and update tick
      const uint32_t delayedLastPreTick = lastPreTick + delayAxonal;
      uint32_t delayedLastUpdateTick = lastUpdateTick + delayAxonal;

      // Get the post-synaptic window of events to be processed
      // **NOTE** this is the window since the last UPDATE rather than the last presynaptic spike
      const uint32_t windowBeginTick = (delayedLastUpdateTick >= delayDendritic) ?
        (delayedLastUpdateTick - delayDendritic) : 0;
      const uint32_t windowEndTick = tick + delayAxonal - delayDendritic;

      // Get post event history within this window
      auto postWindow = m_PostEventHistory[postIndex].GetWindow(windowBeginTick,
                                                                windowEndTick);

      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tPerforming deferred synapse update for post neuron:%u", postIndex);
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tWindow begin tick:%u, window end tick:%u: Previous time:%u, Num events:%u",
          windowBeginTick, windowEndTick, postWindow.GetPrevTime(), postWindow.GetNumEvents());

      // Process events in post-synaptic window
      while (postWindow.GetNumEvents() > 0)
      {
        const uint32_t delayedPostTick = postWindow.GetNextTime() + delayDendritic;

        // Decay accumulator from time of last update to time of this post-spike
        accumulator = Mul16S2011(accumulator,
                                 m_TauALUT.Get(delayedPostTick - delayedLastUpdateTick));
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tDecaying accumulator over %u ticks to %d",
                  delayedPostTick - delayedLastUpdateTick, accumulator);

        LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tApplying post-synaptic event at delayed tick:%u",
                  delayedPostTick);

        // Apply post spike to synapse
        ApplyPostSpike(delayedPostTick,
                       delayedLastPreTick, lastPreTrace,
                       accumulator, weight);

        // Update time of last update
        delayedLastUpdateTick = delayedPostTick;

        // Go onto next event
        postWindow.Next(delayedPostTick);
      }

      // Calculate time of update including axonal delay
      const uint32_t delayedUpdateTick = tick + delayAxonal;

      // Decay accumulator from time of last update to time of update
      accumulator = Mul16S2011(accumulator,
                               m_TauALUT.Get(delayedUpdateTick - delayedLastUpdateTick));
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tDecaying accumulator over %u ticks to %d",
                delayedUpdateTick - delayedLastUpdateTick, accumulator);

      // If this isn't a flush
      if(!flush)
      {
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tApplying pre-synaptic event at tick:%u, last post tick:%u",
                  delayedUpdateTick, postWindow.GetPrevTime());

        // Apply pre-synaptic spike to synapse
        ApplyPreSpike(delayedUpdateTick,
                     postWindow.GetPrevTime(), postWindow.GetPrevTrace(),
                     accumulator, weight);
      }

      // If this isn't a flush, add weight to ring-buffer
      if(!flush)
      {
        applyInputFunction(delayDendritic + delayAxonal + tick,
          postIndex, weight);
      }

      // Write back updated synaptic word to plastic region
      *plasticWords++ = Pair((uint16_t)weight, (uint16_t)accumulator);
    }

    // Write back row and all plastic data to SDRAM
    writeBackRowFunction(&sdramRowAddress[3], &dmaBuffer[3],
      2 + PreTraceWords + GetNumPlasticWords(dmaBuffer[0]));
    return true;
  }

  void AddPostSynapticSpike(uint tick, unsigned int neuronID)
  {
    // If neuron ID is valid
    if(neuronID < 256)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "Adding post-synaptic event to trace at tick:%u",
                tick);

      // Get neuron's post history
      auto &postHistory = m_PostEventHistory[neuronID];

      // Update last trace entry based on spike at tick
      // and add new trace and time to post history
      PostTrace trace = UpdateTrace(tick, postHistory.GetLastTrace(),
                                    postHistory.GetLastTime(),
                                    m_PostExpDistLUT);
      postHistory.Add(tick, trace);
    }
  }

  unsigned int GetRowWords(unsigned int rowSynapses) const
  {
    // Three header word and a synapse
    return 5 + PreTraceWords + GetNumPlasticWords(rowSynapses) + GetNumControlWords(rowSynapses);
  }

  bool ReadSDRAMData(uint32_t *region, uint32_t, uint32_t)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "ExtraModels::RecurrentSTDP::ReadSDRAMData");

    // Read RNG seed
    uint32_t seed[RNG::StateSize];
    LOG_PRINT(LOG_LEVEL_TRACE, "\tSeed:");
    for(unsigned int s = 0; s < RNG::StateSize; s++)
    {
      seed[s] = *region++;
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\t%u", seed[s]);
    }
    m_RNG.SetState(seed);

    // Read parameters
    m_MinWeight = *reinterpret_cast<int32_t*>(region++);
    m_MaxWeight = *reinterpret_cast<int32_t*>(region++);
    m_A2Plus = *reinterpret_cast<S2011*>(region++);
    m_A2Minus = *reinterpret_cast<S2011*>(region++);
    m_AccumulateIncrease = *reinterpret_cast<S2011*>(region++);
    m_AccumulateDecrease = *reinterpret_cast<S2011*>(region++);

    LOG_PRINT(LOG_LEVEL_INFO, "\tMin weight:%d, Max weight:%d, A2+:%d, A2-:%d, Accumulator increase:%d, Accumulator decrease:%d",
              m_MinWeight, m_MaxWeight, m_A2Plus, m_A2Minus, m_AccumulateIncrease, m_AccumulateDecrease);

    // Read inverse-CDF lookup tables
    m_PreExpDistLUT.ReadSDRAMData(region);
    m_PostExpDistLUT.ReadSDRAMData(region);

    // ReadExponential lookup tables
    m_TauALUT.ReadSDRAMData(region);

    return true;
  }

private:
  //-----------------------------------------------------------------------------
  // Private methods
  //-----------------------------------------------------------------------------
  template<typename Dist>
  PreTrace UpdateTrace(uint32_t tick, Trace lastTrace, uint32_t lastTick,
    const Dist &expDistLUT)
  {
    // Pick random number and use to draw from exponential distribution
    const uint32_t windowLength = expDistLUT.Get(m_RNG);

    // If this new window wil actually extend the previous window
    const uint32_t lastWindowEndTick = lastTick + lastTrace;
    if((tick + windowLength) > lastWindowEndTick)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tResetting current window length %u to %u",
                lastTrace, windowLength);

      // Return window length
      return (Trace)windowLength;
    }
    // Otherwise
    else
    {
      // Calculate how much of last window extends beyond this tick
      const uint32_t remainingWindowLength = lastWindowEndTick - tick;
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tRe-aligning current window length %u to %u",
                lastTrace, remainingWindowLength);

      // Return remaining window length
      return (Trace)remainingWindowLength;
    }
  }

  void ApplyPreSpike(uint32_t time,
                     uint32_t lastPostTime, PostTrace lastPostTrace,
                     S2011 &accumulator, int32_t &weight)
  {
    // Get time of event relative to last post-synaptic event
    uint32_t timeSinceLastPost = time - lastPostTime;

    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\ttime since last post:%u, pre window length:%u",
              timeSinceLastPost, lastPostTrace);

    // If spikes don't coincide
    if (timeSinceLastPost > 0)
    {
      // If this pre-spike has arrived within the last post window
      if (timeSinceLastPost < lastPostTrace)
      {
        // Apply accumulator increase
        accumulator -= m_AccumulateDecrease;
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\t\tAccumulator = %d", accumulator);

        // If it's less than -1
        if (accumulator <= -S2011One)
        {
          LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\t\tApplying depression");

          // Reset accumulator
          accumulator = 0;

          // Subtract depression
          // **NOTE** this will leave weight in dynamic weight fixed point format
          weight -= Mul16S2011(weight - m_MinWeight, m_A2Minus);
        }
      }
    }
  }

  void ApplyPostSpike(uint32_t time,
                      uint32_t lastPreTime, PreTrace lastPreTrace,
                      S2011 &accumulator, int32_t &weight)
  {
    // Get time of event relative to last pre-synaptic event
    uint32_t timeSinceLastPre = time - lastPreTime;

    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\ttime since last pre:%u, pre window length:%u",
              timeSinceLastPre, lastPreTrace);

    // If spikes don't coincide
    if (timeSinceLastPre > 0)
    {
      // If this post-spike has arrived within the last pre window
      if (timeSinceLastPre < lastPreTrace)
      {
        // Apply accumulator increase
        accumulator += m_AccumulateIncrease;
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\t\tAccumulator = %d", accumulator);

        // If it's greater than one
        if (accumulator >= S2011One)
        {
          LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\t\tApplying potentiation");

          // Reset accumulator
          accumulator = 0;

          // Add potentiation
          // **NOTE** this will leave weight in dynamic weight fixed point format
          weight += Mul16S2011(m_MaxWeight - weight, m_A2Plus);
        }
      }
    }
  }

  //-----------------------------------------------------------------------------
  // Private static methods
  //-----------------------------------------------------------------------------
  static uint32_t GetIndex(uint32_t word)
  {
    return (word & IndexMask);
  }

  static uint32_t GetDelay(uint32_t word)
  {
    return ((word >> I) & DelayMask);
  }

  static unsigned int GetNumPlasticWords(unsigned int numSynapses)
  {
    const unsigned int plasticBytes = numSynapses * sizeof(PlasticSynapse);
    return (plasticBytes / 4) + (((plasticBytes % 4) == 0) ? 0 : 1);
  }

  static unsigned int GetNumControlWords(unsigned int numSynapses)
  {
    const unsigned int controlBytes = numSynapses * sizeof(C);
    return (controlBytes / 4) + (((controlBytes % 4) == 0) ? 0 : 1);
  }

  static PreTrace GetPreTrace(uint32_t (&dmaBuffer)[MaxRowWords])
  {
    // **NOTE** GCC will optimise this memcpy out it
    // is simply strict-aliasing-safe solution
    PreTrace preTrace;
    memcpy(&preTrace, &dmaBuffer[5], sizeof(PreTrace));
    return preTrace;
  }

  static void SetPreTrace(uint32_t (&dmaBuffer)[MaxRowWords], PreTrace preTrace)
  {
    // **NOTE** GCC will optimise this memcpy out it
    // is simply strict-aliasing-safe solution
    memcpy(&dmaBuffer[5], &preTrace, sizeof(PreTrace));
  }

  static PlasticSynapse *GetPlasticWords(uint32_t (&dmaBuffer)[MaxRowWords])
  {
    return reinterpret_cast<PlasticSynapse*>(&dmaBuffer[5 + PreTraceWords]);
  }

  static const C *GetControlWords(uint32_t (&dmaBuffer)[MaxRowWords], unsigned int numSynapses)
  {
    return reinterpret_cast<C*>(&dmaBuffer[5 + PreTraceWords + GetNumPlasticWords(numSynapses)]);
  }

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  // Random number generator
  RNG m_RNG;

  // Weight limits
  int32_t m_MinWeight;
  int32_t m_MaxWeight;

  // Size of each weight update
  S2011 m_A2Plus;
  S2011 m_A2Minus;

  // Size of each accumulator step
  S2011 m_AccumulateIncrease;
  S2011 m_AccumulateDecrease;

  // Inverse-CDF lookup tables
  ExpDistLUT m_PreExpDistLUT;
  ExpDistLUT m_PostExpDistLUT;

  // Exponential lookup tables
  Common::ExpDecayLUT<TauALUTNumEntries, TauALUTShift> m_TauALUT;

  // Event history
  PostEventHistory m_PostEventHistory[256];
};
} // BCPNN