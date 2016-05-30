#pragma once

// Standard includes
#include <cstdint>

//-----------------------------------------------------------------------------
// SynapseProcessor::Plasticity::SynapseStructure::Weight
//-----------------------------------------------------------------------------
namespace ExtraModels
{
template<typename W>
class WeightAccumulator
{
public:
  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef W WeightDependence;
  typedef typename WeightDependence::Weight PlasticSynapse;

  //-----------------------------------------------------------------------------
  // FinalState
  //-----------------------------------------------------------------------------
  class FinalState
  {
  public:
    FinalState(typename WeightDependence::Weight weight) : m_Weight(weight)
    {
    }

    //-----------------------------------------------------------------------------
    // Public API
    //-----------------------------------------------------------------------------
    typename WeightDependence::Weight GetWeight() const
    {
      return m_Weight;
    }

    PlasticSynapse GetPlasticSynapse() const
    {
      return m_Weight;
    }

  private:
    //-----------------------------------------------------------------------------
    // Members
    //-----------------------------------------------------------------------------
    typename WeightDependence::Weight m_Weight;
  };

  Weight(PlasticSynapse plasticSynapse) : m_WeightState(plasticSynapse)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  void ApplyDepression(int32_t depression, const WeightDependence &weightDependence)
  {
    m_WeightState.ApplyDepression(depression, weightDependence);
  }

  void ApplyPotentiation(int32_t potentiation, const WeightDependence &weightDependence)
  {
    // **TODO** decay accumulator
    // If spikes don't coincide
    if (timeSinceLastPre > 0)
    {
      // If this post-spike has arrived within the last pre window
      if (timeSinceLastPre < lastPreTrace)

        if (m_Accumulator < weightDependence.GetAccumulatorPotentiationMinusOne())
        {
          // If accumulator's not going to hit potentiation limit, increment it
          m_Accumulator++;
          LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\t\tIncrementing accumulator=%d",
                    previous_state.accumulator);
        }
        else
        {
          // Otherwise, reset accumulator and apply potentiation
          LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\t\tApplying potentiation");

          m_Accumulator = 0;
          m_WeightState.ApplyPotentiation();
        }
      }
    }
  }

  FinalState CalculateFinalState(const WeightDependence &weightDependence) const
  {
    return FinalState(m_WeightState.CalculateFinalWeight(weightDependence));
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  typename WeightDependence::WeightState m_WeightState;
  int32_t m_Accumulator;
};
} // ExtraModels