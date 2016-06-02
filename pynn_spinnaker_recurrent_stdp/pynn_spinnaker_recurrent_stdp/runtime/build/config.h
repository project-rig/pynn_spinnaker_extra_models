#pragma once

// Common includes
#include "common/spike_input_buffer.h"
namespace SynapseProcessor
{
  typedef Common::SpikeInputBufferBase<1024> SpikeInputBuffer;
}

// Synapse processor includes
#include "synapse_processor/key_lookup_binary_search.h"
namespace SynapseProcessor
{
  typedef KeyLookupBinarySearch<10> KeyLookup;
}

// Recurrent STDP using 16-bit control words with 3 delay bits and 10 index bits;
// 512 entry lookup table for accumulator decay a Mars Kiss 64 RNG
// and a post-synaptic event history with 10 entries
#include "common/random/mars_kiss64.h"
#include "../recurrent_stdp.h"
namespace SynapseProcessor
{
  typedef ExtraModels::RecurrentSTDP<uint16_t, 3, 10,
                                     512, 0,
                                     10, Common::Random::MarsKiss64> SynapseType;
}


// Ring buffer with 32-bit unsigned entries, large enough for 256 neurons
#include "synapse_processor/ring_buffer.h"
namespace SynapseProcessor
{
  typedef RingBufferBase<uint32_t, 3, 8> RingBuffer;
}

#include "synapse_processor/delay_buffer.h"
namespace SynapseProcessor
{
  typedef DelayBufferBase<10> DelayBuffer;
}
