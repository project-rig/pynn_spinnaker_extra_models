#pragma once

// Common includes
#include "common/fixed_point_number.h"
#include "common/spinnaker.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// ExtraModels::CA2Adaptive
//-----------------------------------------------------------------------------
namespace ExtraModels
{
class CA2Adaptive
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  enum RecordingChannel
  {
    RecordingChannelV,
    RecordingChannelMax,
  };

  //-----------------------------------------------------------------------------
  // MutableState
  //-----------------------------------------------------------------------------
  struct MutableState
  {
    // Membrane voltage [mV]
    S1615 m_V_Membrane;

    // Countdown to end of next refractory period [machine timesteps]
    int32_t m_RefractoryTimer;

    // Calcium adaption current [nA]
    S1615 m_I_CA2;
  };

  //-----------------------------------------------------------------------------
  // ImmutableState
  //-----------------------------------------------------------------------------
  struct ImmutableState
  {
    // Membrane voltage threshold at which neuron spikes [mV]
    S1615 m_V_Threshold;

    // Post-spike reset membrane voltage [mV]
    S1615 m_V_Reset;

    // Membrane resting voltage [mV]
    S1615 m_V_Rest;

    // Offset current [nA] but take care because actually 'per timestep charge'
    S1615 m_I_Offset;

    // Membrane resistance [MegaOhm]
    S1615 m_R_Membrane;

    // 'Fixed' computation parameter - time constant multiplier for
    // Closed-form solution
    // exp( -(machine time step in ms)/(R * C) ) [.]
    S1615 m_ExpTC;

    // Refractory time of neuron [machine timesteps]
    int32_t m_T_Refractory;

    // Influx of CA2 caused by each spike [nA]
    S1615 m_I_Alpha;

    // Decay for CA2
    // exp( -(machine time step in ms)/(TauCa))
    S1615 m_ExpTauCa;
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static inline bool Update(MutableState &mutableState, const ImmutableState &immutableState,
                            S1615 excInput, S1615 inhInput, S1615 extCurrent)
  {
    // Decay Ca2 trace
    mutableState.m_I_CA2 = MulS1615(mutableState.m_I_CA2, immutableState.m_ExpTauCa);

    // If outside of the refractory period
    if (mutableState.m_RefractoryTimer <= 0)
    {
      // Get the input in nA
      S1615 inputThisTimestep = excInput - inhInput - mutableState.m_I_CA2
        + extCurrent + immutableState.m_I_Offset;

      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tInput this timestep:%.4knA", inputThisTimestep);

      // Convert input from current to voltage
      S1615 alpha = MulS1615(inputThisTimestep, immutableState.m_R_Membrane) + immutableState.m_V_Rest;

      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tAlpha:%.4kmV", alpha);

      // Perform closed form update
      mutableState.m_V_Membrane = alpha - MulS1615(immutableState.m_ExpTC,
                                                   alpha - mutableState.m_V_Membrane);

      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tMembrane voltage:%.4knA", mutableState.m_V_Membrane);

      // Neuron spikes if membrane voltage has crossed threshold
      if (mutableState.m_V_Membrane >= immutableState.m_V_Threshold)
      {
        // Reset membrane voltage
        mutableState.m_V_Membrane = immutableState.m_V_Reset;

        // Reset refractory timer
        mutableState.m_RefractoryTimer = immutableState.m_T_Refractory;

        // Apply influx of calcium to trace
        mutableState.m_I_CA2 += immutableState.m_I_Alpha;

        return true;
      }
    }
    // Otherwise, count down refractory timer
    else
    {
      mutableState.m_RefractoryTimer--;
    }

    return false;
  }

  static S1615 GetRecordable(RecordingChannel c,
                             const MutableState &mutableState, const ImmutableState &,
                             S1615, S1615, S1615)
  {
    switch(c)
    {
      case RecordingChannelV:
        return mutableState.m_V_Membrane;

      default:
        LOG_PRINT(LOG_LEVEL_WARN, "Attempting to get data from non-existant recording channel %u", c);
        return 0;
    }
  }

  static void Print(char *stream, const MutableState &mutableState, const ImmutableState &immutableState)
  {
    io_printf(stream, "\tMutable state:\n");
    io_printf(stream, "\t\tV_Membrane       = %11.4k [mV]\n", mutableState.m_V_Membrane);
    io_printf(stream, "\t\tRefractoryTimer  = %10d [timesteps]\n", mutableState.m_RefractoryTimer);
    io_printf(stream, "\t\tI_CA2            = %11.4k [nA]\n", mutableState.m_I_CA2);

    io_printf(stream, "\tImmutable state:\n");
    io_printf(stream, "\t\tV_Threshold      = %11.4k [mV]\n", immutableState.m_V_Threshold);
    io_printf(stream, "\t\tV_Reset          = %11.4k [mV]\n", immutableState.m_V_Reset);
    io_printf(stream, "\t\tV_Rest           = %11.4k [mV]\n", immutableState.m_V_Rest);
    io_printf(stream, "\t\tI_Offset         = %11.4k [nA]\n", immutableState.m_I_Offset);
    io_printf(stream, "\t\tR_Membrane       = %11.4k [MegaOhm]\n", immutableState.m_R_Membrane);
    io_printf(stream, "\t\tExpTC            = %11.4k\n", immutableState.m_ExpTC);
    io_printf(stream, "\t\tT_Refractory     = %10d [timesteps]\n", immutableState.m_T_Refractory);
    io_printf(stream, "\t\tI_Alpha          = %11.4k [nA]\n", immutableState.m_I_Alpha);
    io_printf(stream, "\t\tExpTauCa         = %11.4k\n", immutableState.m_ExpTauCa);
  }
};
} // ExtraModels