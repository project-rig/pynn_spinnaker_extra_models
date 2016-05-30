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
  PostTrace UpdatePostTrace(uint32_t, PostTrace, uint32_t) const
  {
    // Pick random number and use to draw from exponential distribution
    uint32_t random = (m_RNG.GetNext() & (S2011One - 1));
    uint32_t windowLength = m_PostExpDistLookup[random];
    LOG_PRINT(LOG_LEVEL_TRACE, "\tResetting post-window: random=%d, window_length=%u",
              random, windowLength);

    // Return window length
    return (PostTrace)windowLength;
  }

  PreTrace UpdatePreTrace(uint32_t, PreTrace, uint32_t) const
  {
    // Pick random number and use to draw from exponential distribution
    uint32_t random = (m_RNG.GetNext() & (S2011One - 1));
    uint32_t windowLength = m_PreExpDistLookup[random];
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tResetting pre-window: random=%d, window_length=%u",
              random, windowLength);

    // Return window length
    return (PreTrace)windowLength;
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
    uint32_t timeSinceLastPre = time - lastPreTime;

    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\ttime since last pre:%u, pre window length:%u",
              timeSinceLastPre, lastPreTrace);

    applyPotentiation(lastPreTrace, timeSinceLastPre);
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

  uint16_t m_PreExpDistLookup[S2011One];
  uint16_t m_PostExpDistLookup[S2011One];

  R m_RNG;
};
} // ExtraModels