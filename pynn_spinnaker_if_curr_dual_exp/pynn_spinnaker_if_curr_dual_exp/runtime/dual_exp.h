#pragma once

// Rig CPP common includes
#include "rig_cpp_common/fixed_point_number.h"
#include "rig_cpp_common/spinnaker.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// ExtraModels::DualExp
//-----------------------------------------------------------------------------
namespace ExtraModels
{
class DualExp
{
public:
  //-----------------------------------------------------------------------------
  // MutableState
  //-----------------------------------------------------------------------------
  struct MutableState
  {
    // Excitatory input current
    S1615 m_ISynExc;

    // Second excitatory input current
    S1615 m_ISynExc2;

    // Inhibitory input current
    S1615 m_ISynInh;
  };

  //-----------------------------------------------------------------------------
  // ImmutableState
  //-----------------------------------------------------------------------------
  struct ImmutableState
  {
    // Excitatory decay constants
    U032 m_ExpTauSynExc;

    // Excitatory scale
    S1615 m_InitExc;

    // Second excitatory decay constants
    U032 m_ExpTauSynExc2;

    // Second excitatory scale
    S1615 m_InitExc2;

    // Inhibitory decay constant
    U032 m_ExpTauSynInh;

    // Inhibitory scale
    S1615 m_InitInh;
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static inline void ApplyInput(MutableState &mutableState, const ImmutableState &, S1615 input, unsigned int receptorType)
  {
    // Apply input to correct receptor
    if(receptorType == 0)
    {
      mutableState.m_ISynExc += input;
    }
    else if (receptorType == 1)
    {
      mutableState.m_ISynInh += input;
    }
    else
    {
      mutableState.m_ISynExc2 += input;
    }
  }

  static inline S1615 GetExcInput(const MutableState &mutableState, const ImmutableState &immutableState)
  {
    return MulS1615(mutableState.m_ISynExc, immutableState.m_InitExc)
      + MulS1615(mutableState.m_ISynExc2, immutableState.m_InitExc2);
  }

  static inline S1615 GetInhInput(const MutableState &mutableState, const ImmutableState &immutableState)
  {
    return MulS1615(mutableState.m_ISynInh, immutableState.m_InitInh);
  }

  static inline void Shape(MutableState &mutableState, const ImmutableState &immutableState)
  {
    // Decay both currents
    mutableState.m_ISynExc = MulS1615U032(mutableState.m_ISynExc, immutableState.m_ExpTauSynExc);
    mutableState.m_ISynInh = MulS1615U032(mutableState.m_ISynInh, immutableState.m_ExpTauSynInh);
    mutableState.m_ISynExc2 = MulS1615U032(mutableState.m_ISynExc2, immutableState.m_ExpTauSynExc2);
  }

  static void Print(char *stream, const MutableState &mutableState, const ImmutableState &immutableState)
  {
    io_printf(stream, "\tMutable state:\n");
    io_printf(stream, "\t\tm_ISynExc        = %11.4k [nA]\n", mutableState.m_ISynExc);
    io_printf(stream, "\t\tm_ISynExc2       = %11.4k [nA]\n", mutableState.m_ISynExc2);
    io_printf(stream, "\t\tm_ISynInh        = %11.4k [nA]\n", mutableState.m_ISynInh);

    io_printf(stream, "\tImmutable state:\n");
    io_printf(stream, "\t\tExpTauSynExc      = %11.4k\n", (S1615)(immutableState.m_ExpTauSynExc >> 17));
    io_printf(stream, "\t\tInitExc           = %11.4k [nA]\n", immutableState.m_InitExc);
    io_printf(stream, "\t\tExpTauSynInh      = %11.4k\n", (S1615)(immutableState.m_ExpTauSynInh >> 17));
    io_printf(stream, "\t\tInitInh           = %11.4k [nA]\n", immutableState.m_InitInh);
    io_printf(stream, "\t\tExpTauSynExc2     = %11.4k\n", (S1615)(immutableState.m_ExpTauSynExc2 >> 17));
    io_printf(stream, "\t\tInitExc2          = %11.4k [nA]\n", immutableState.m_InitExc2);
  }
};
} // ExtraModels