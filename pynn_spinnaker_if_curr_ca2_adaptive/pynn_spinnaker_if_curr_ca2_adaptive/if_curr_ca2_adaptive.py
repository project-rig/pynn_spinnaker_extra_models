# Import modules
from pynn_spinnaker.spinnaker import lazy_param_map
from pynn_spinnaker.spinnaker import regions

# Import classes
from pyNN.standardmodels.cells import StandardCellType

# Import functions
from copy import deepcopy
from pyNN.standardmodels import build_translations

# Import globals
from pynn_spinnaker.standardmodels.cells import (exp_synapse_translations,
                                                 exp_synapse_immutable_param_map,
                                                 exp_synapse_curr_mutable_param_map)

# ----------------------------------------------------------------------------
# Neuron type translations
# ----------------------------------------------------------------------------
# Build translations from PyNN to SpiNNaker neuron model parameters
if_curr_ca2_adaptive_neuron_translations = build_translations(
    ("tau_m",       "tau_m"),
    ("cm",          "r_membrane", "tau_m / cm", ""),
    ("v_rest",      "v_rest"),
    ("v_thresh",    "v_thresh"),
    ("v_reset",     "v_reset"),
    ("tau_refrac",  "tau_refrac"),
    ("tau_ca2",     "tau_ca2"),
    ("i_offset",    "i_offset"),
    ("i_alpha",     "i_alpha"),
)

# ----------------------------------------------------------------------------
# Neuron region maps
# ----------------------------------------------------------------------------
# Build maps of where and how parameters need to be written into neuron regions
if_curr_ca2_adaptive_neuron_immutable_param_map = [
    ("v_thresh",    "i4", lazy_param_map.s1615),
    ("v_reset",     "i4", lazy_param_map.s1615),
    ("v_rest",      "i4", lazy_param_map.s1615),
    ("i_offset",    "i4", lazy_param_map.s1615),
    ("r_membrane",  "i4", lazy_param_map.s1615),
    ("tau_m",       "i4", lazy_param_map.s1615_exp_decay),
    ("tau_refrac",  "u4", lazy_param_map.integer_time_divide),
    ("i_alpha",     "i4", lazy_param_map.s1615),
    ("tau_ca2",     "i4", lazy_param_map.s1615_exp_decay),
]

if_curr_ca2_adaptive_neuron_mutable_param_map = [
    ("v", "i4", lazy_param_map.s1615),
    (0,   "i4"),
    (0,   "i4"),
]

# ------------------------------------------------------------------------------
# IF_curr_ca2_adaptive_exp
# ------------------------------------------------------------------------------
class IF_curr_ca2_adaptive_exp(StandardCellType):
    """
    Leaky integrate and fire model with fixed threshold and
    decaying-exponential post-synaptic current.
    Adaption mechanism taken from Liu, Y. H., & Wang, X. J. (2001).

    Spike-frequency adaptation of a generalized
    leaky integrate-and-fire model neuron.

    Journal of Computational Neuroscience, 10(1), 25-45.
    doi:10.1023/A:1008916026143
    """
    default_parameters = {
        "v_rest"     : -65.0,   # Resting membrane potential in mV.
        "cm"         : 1.0,     # Capacity of the membrane in nF
        "tau_m"      : 20.0,    # Membrane time constant in ms.
        "tau_refrac" : 0.1,     # Duration of refractory period in ms.
        "tau_ca2"    : 50.0,    # Time contant of CA2 adaption current
        "tau_syn_E"  : 5.0,     # Decay time of excitatory synaptic current in ms.
        "tau_syn_I"  : 5.0,     # Decay time of inhibitory synaptic current in ms.
        "i_offset"   : 0.0,     # Offset current in nA
        "v_reset"    : -65.0,   # Reset potential after a spike in mV.
        "v_thresh"   : -50.0,   # Spike threshold in mV.
    }
    recordable = ["spikes", "v"]
    conductance_based = False
    default_initial_values = {
        "v": -65.0,  # 'v_rest',
        "isyn_exc": 0.0,
        "isyn_inh": 0.0,
        "i_ca2": 0.0,
    }
    units = {
        "v": "mV",
        "isyn_exc": "nA",
        "isyn_inh": "nA",
        "i_ca2": "nA",
    }
    receptor_types = ("excitatory", "inhibitory")

    # How many of these neurons per core can
    # a SpiNNaker neuron processor handle
    max_neurons_per_core = 1024

    # JK: not necessary
    neuron_region_class = regions.Neuron
    synapse_region_class = regions.Synapse

    directly_connectable = False

    translations = deepcopy(if_curr_ca2_adaptive_neuron_translations)
    translations.update(exp_synapse_translations)

    neuron_immutable_param_map = if_curr_ca2_adaptive_neuron_immutable_param_map
    neuron_mutable_param_map = if_curr_ca2_adaptive_neuron_mutable_param_map

    synapse_immutable_param_map = exp_synapse_immutable_param_map
    synapse_mutable_param_map = exp_synapse_curr_mutable_param_map