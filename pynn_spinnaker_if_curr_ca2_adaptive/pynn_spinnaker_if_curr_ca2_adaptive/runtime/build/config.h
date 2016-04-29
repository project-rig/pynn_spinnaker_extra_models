#pragma once

// Model includes
#include "neuron_processor/input_buffer.h"
#include "neuron_processor/intrinsic_plasticity_models/stub.h"
#include "neuron_processor/synapse_models/exp.h"
#include "../ca2_adaptive.h"

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Typedefines
//-----------------------------------------------------------------------------
typedef ExtraModels::CA2Adaptive Neuron;
typedef SynapseModels::Exp Synapse;
typedef IntrinsicPlasticityModels::Stub IntrinsicPlasticity;

typedef InputBufferBase<uint32_t> InputBuffer;
};