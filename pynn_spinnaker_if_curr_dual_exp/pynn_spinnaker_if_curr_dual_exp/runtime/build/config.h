#pragma once

// Model includes
#include "neuron_processor/input_buffer.h"
#include "neuron_processor/neuron_models/if_curr.h"
#include "../dual_exp.h"

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Typedefines
//-----------------------------------------------------------------------------
typedef NeuronModels::IFCurr Neuron;
typedef ExtraModels::DualExp Synapse;

typedef InputBufferBase<uint32_t> InputBuffer;
};