#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "common/fixed_point_number.h"
#include "common/log.h"
#include "common/random/mars_kiss64.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// ExtraModels::RecurrentTimingDependence
//-----------------------------------------------------------------------------
namespace ExtraModels
{
template<typename R>
class RecurrentTimingDependence
{
public:
  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef uint16_t PostTrace;
  typedef uint16_t PreTrace;

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  PostTrace UpdatePostTrace(uint32_t tick, PostTrace lastTrace, uint32_t lastTick) const
  {
    // Get time since last spike
    uint32_t elapsedTicks = tick - lastTick;

    // Decay previous trace
    int32_t newTrace = Mul16S2011(lastTrace, m_TauMinusLUT.Get(elapsedTicks));

    // Add energy caused by new spike to trace
    newTrace += S2011One;

    LOG_PRINT(LOG_LEVEL_TRACE, "\tElapsed ticks:%d, New trace:%d",
              elapsedTicks, newTrace);

    // Return new trace_value
    return (PostTrace)newTrace;
  }

  PreTrace UpdatePreTrace(uint32_t tick, PreTrace lastTrace, uint32_t lastTick) const
  {
    // Get time since last spike
    uint32_t elapsedTicks = tick - lastTick;

    // Decay previous trace
    int32_t newTrace = Mul16S2011(lastTrace, m_TauPlusLUT.Get(elapsedTicks));

    // Add energy caused by new spike to trace
    newTrace += S2011One;

    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tElapsed ticks:%d, New trace:%d",
              elapsedTicks, newTrace);

    // Return new trace_value
    return (PreTrace)newTrace;
  }

  template<typename D, typename P>
  void ApplyPreSpike(D applyDepression, P,
                     uint32_t time, PreTrace,
                     uint32_t, PreTrace,
                     uint32_t lastPostTime, PostTrace lastPostTrace)
  {
    // Get time of event relative to last post-synaptic event
    uint32_t elapsedTicksSinceLastPost = time - lastPostTime;
    if (elapsedTicksSinceLastPost > 0)
    {
        S2011 decayedPostTrace = Mul16S2011(
          lastPostTrace, m_TauMinusLUT.Get(elapsedTicksSinceLastPost));

        LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tElapsed ticks since last post:%u, last post trace:%d, decayed post trace=%d",
                  elapsedTicksSinceLastPost, lastPostTrace, decayedPostTrace);

        // Apply depression
        applyDepression(decayedPostTrace);
    }
  }

  template<typename D, typename P>
  void ApplyPostSpike(D, P applyPotentiation,
                      uint32_t time, PostTrace,
                      uint32_t lastPreTime, PreTrace lastPreTrace,
                      uint32_t, PostTrace)
  {
    // Get time of event relative to last pre-synaptic event
    uint32_t elapsedTicksSinceLastPre = time - lastPreTime;
    if (elapsedTicksSinceLastPre > 0)
    {
        S2011 decayedPreTrace = Mul16S2011(
          lastPreTrace, m_TauPlusLUT.Get(elapsedTicksSinceLastPre));

        LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tElapsed ticks since last pre:%u, last pre trace:%d, decayed pre trace=%d",
                  elapsedTicksSinceLastPre, lastPreTrace, decayedPreTrace);

        // Apply potentiation
        applyPotentiation(decayedPreTrace);
    }
  }

  bool ReadSDRAMData(uint32_t *&region, uint32_t)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tExtraModels::RecurrentTimingDependence::ReadSDRAMData");

    // Read RNG seed
    uint32_t seed[R::StateSize];
    LOG_PRINT(LOG_LEVEL_TRACE, "\tSeed:");
    for(unsigned int s = 0; s < R::StateSize; s++)
    {
      seed[s] = *region++;
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\t%u", seed[s]);
    }
    m_RNG.SetState(seed);


    m_TauPlusLUT.ReadSDRAMData(region);
    m_TauMinusLUT.ReadSDRAMData(region);
    return true;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_AccumulatorDepressionPlusOne;
  int32_t m_AccumulatorPotentiationMinusOne;

  R m_RNG;
};
} // ExtraModels