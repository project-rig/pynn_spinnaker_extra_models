# Import modules
import lazyarray as la
import math
import numpy as np
from pynn_spinnaker.spinnaker import lazy_param_map
from pynn_spinnaker.spinnaker import regions

# Import classes
from pyNN.standardmodels.synapses import StandardSynapseType

# Import functions
from copy import deepcopy
from functools import partial
from pyNN.standardmodels import build_translations
from pynn_spinnaker.spinnaker.utils import get_homogeneous_param

# Import globals
from pynn_spinnaker.simulator import state

# ------------------------------------------------------------------------------
# RecurrentSTDPSynapse
# ------------------------------------------------------------------------------
class RecurrentSTDPSynapse(StandardSynapseType):
    """
    Recurrent STDP synapse

    Arguments:
        `w_min`:
            Minimum synaptic weight (uS/nA).
        `w_max`:
            Maximum synaptic weight (uS/nA).
        `A_plus`:
            When accumulator reaches 1.0 maximum proportion of
            w_max weight increases by.
        `A_minus`:
            When accumulator reaches -1.0 maximum proportion of
            w_min weight decreases by.
        `accumulator_increase`:
            How much accumulator increases with each postsynaptic spike that
            comes in within presynaptic window (expressed as a number (0,1))
        `accumulator_decrease`:
            How much accumulator decreases with each presynaptic spike that
            comes in within postsynaptic window (expressed as a number (0,1))
        `lambda_pre`:
            mean presynaptic window length.
        `lambda_post`:
            .
        `tau_a`:
            Is plasticity enabled.
    """
    default_parameters = {
        "weight": 0.0,
        "delay": None,
        "w_min": 0.0,
        "w_max": 1.0,
        "A_plus" : 0.01,
        "A_minus": 0.01,
        "accumulator_increase": 0.1,
        "accumulator_decrease": 0.1,
        "lambda_pre": 20.0,
        "lambda_post": 20.0,
        "tau_a": 100.0,
    }


    translations = build_translations(
        ("weight",                "weight"),
        ("delay",                 "delay"),

        ("w_min",                 "w_min"),
        ("w_max",                 "w_max"),
        ("A_plus",                "a_plus"),
        ("A_minus",               "a_minus"),

        ("accumulator_increase",  "accumulator_increase"),
        ("accumulator_decrease",  "accumulator_decrease"),

        ("lambda_pre",            "lambda_pre"),
        ("lambda_post",           "lambda_post"),

        ("tau_a",                 "tau_a"),
    )

    plasticity_param_map = [
        (lazy_param_map.mars_kiss_64_random_seed, "4i4"),

        ("w_min",                 "i4", lazy_param_map.s2211),
        ("w_max",                 "i4", lazy_param_map.s2211),
        ("a_plus",                "i4", lazy_param_map.s2211),
        ("a_minus",               "i4", lazy_param_map.s2211),

        ("accumulator_increase",  "i4", lazy_param_map.s2211),
        ("accumulator_decrease",  "i4", lazy_param_map.s2211),

        ("lambda_pre",            "2048i2", lazy_param_map.s411_exp_dist_its_lut),
        ("lambda_post",           "2048i2", lazy_param_map.s411_exp_dist_its_lut),

        ("tau_a",                 "1500i2", partial(lazy_param_map.s411_exp_decay_lut,
                                                    num_entries=1500, time_shift=5)),
    ]

    comparable_param_names = ("w_min", "w_max", "A_plus", "A_minus",
                              "accumulator_increase", "accumulator_decrease",
                              "lambda_pre", "lambda_post", "tau_a")

    # How many post-synaptic neurons per core can a
    # SpiNNaker synapse_processor of this type handle
    max_post_neurons_per_core = 256

    # Assuming relatively long row length, at what rate can a SpiNNaker
    # synapse_processor of this type process synaptic events (hZ)
    max_synaptic_event_rate = 0.6E6

    # Recurrent STDP requires a synaptic matrix region
    # with support for extra per-synapse data
    synaptic_matrix_region_class = regions.ExtendedPlasticSynapticMatrix

    # How many timesteps of delay can DTCM ring-buffer handle
    # **NOTE** only 7 timesteps worth of delay can be handled by
    # 8 element delay buffer - The last element is purely for output
    max_dtcm_delay_slots = 7

    # Static weights are unsigned
    signed_weight = False

    # Recurrent STDP synapses require post-synaptic
    # spikes back-propagated to them
    requires_back_propagation = True

    # The presynaptic state for recurrent STDP synapses consists of a
    # uint32 containing time of last update a uint32 containing time of last
    # presynaptic spike and uint16 containing presynaptic window length
    pre_state_bytes = 10

    # Each synape has an additional 16-bit trace: accumulator
    synapse_trace_bytes = 2

    def _get_minimum_delay(self):
        d = state.min_delay
        if d == "auto":
            d = state.dt
        return d

    def update_weight_range(self, weight_range):
        weight_range.update(get_homogeneous_param(self.parameter_space, "w_max"))
        weight_range.update(get_homogeneous_param(self.parameter_space, "w_min"))