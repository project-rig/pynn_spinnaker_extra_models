#pragma once

// Model includes
#include "common/input_buffer.h"
#include "common/neuron_models/if_curr.h"
#include "../dual_exp.h"

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Typedefines
//-----------------------------------------------------------------------------
typedef NeuronModels::IFCurr Neuron;
typedef DualExp Synapse;

typedef InputBufferBase<uint32_t> InputBuffer;
};