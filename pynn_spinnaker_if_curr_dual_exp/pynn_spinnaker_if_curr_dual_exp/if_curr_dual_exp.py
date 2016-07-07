# Import modules
from pynn_spinnaker.spinnaker import lazy_param_map
from pynn_spinnaker.spinnaker import regions

# Import classes
from pyNN.standardmodels.cells import StandardCellType

# Import functions
from copy import deepcopy
from pyNN.standardmodels import build_translations

# Import globals
from pynn_spinnaker.standardmodels.cells import (if_curr_neuron_translations,
                                                 if_curr_neuron_immutable_param_map,
                                                 if_curr_neuron_mutable_param_map)

# ----------------------------------------------------------------------------
# Synapse type translations
# ----------------------------------------------------------------------------
# Build translations from PyNN to SpiNNaker synapse model parameters
dual_exp_synapse_translations = build_translations(
    ("tau_syn_E",   "tau_syn_e"),
    ("tau_syn_E2",   "tau_syn_e2"),
    ("tau_syn_I",   "tau_syn_i"),
)

# ----------------------------------------------------------------------------
# Synapse shaping region maps
# ----------------------------------------------------------------------------
dual_exp_synapse_immutable_param_map = [
    ("tau_syn_e", "u4", lazy_param_map.u032_exp_decay),
    ("tau_syn_e", "i4", lazy_param_map.s1615_exp_init),
    ("tau_syn_e2", "u4", lazy_param_map.u032_exp_decay),
    ("tau_syn_e2", "i4", lazy_param_map.s1615_exp_init),
    ("tau_syn_i", "u4", lazy_param_map.u032_exp_decay),
    ("tau_syn_i", "i4", lazy_param_map.s1615_exp_init),
]

dual_exp_synapse_curr_mutable_param_map = [
    ("isyn_exc", "i4", lazy_param_map.s1615),
    ("isyn_exc2", "i4", lazy_param_map.s1615),
    ("isyn_inh", "i4", lazy_param_map.s1615),
]

# ------------------------------------------------------------------------------
# IF_curr_dual_exp
# ------------------------------------------------------------------------------
class IF_curr_dual_exp(StandardCellType):
    """
    Leaky integrate and fire model with fixed threshold and
    decaying-exponential post-synaptic current. (Separate synaptic currents for
    two excitatory and one inhibitory synapses.
    """
    default_parameters = {
        "v_rest"     : -65.0,   # Resting membrane potential in mV.
        "cm"         : 1.0,     # Capacity of the membrane in nF
        "tau_m"      : 20.0,    # Membrane time constant in ms.
        "tau_refrac" : 0.1,     # Duration of refractory period in ms.
        "tau_syn_E"  : 5.0,     # Decay time of excitatory synaptic current in ms.
        "tau_syn_E2"  : 5.0,    # Decay time of second excitatory synaptic current in ms.
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
        "isyn_exc2": 0.0,
        "isyn_inh": 0.0,
    }
    units = {
        "v": "mV",
        "isyn_exc": "nA",
        "isyn_exc2": "nA",
        "isyn_inh": "nA",
    }
    receptor_types = ("excitatory", "inhibitory", "excitatory2")

    translations = deepcopy(if_curr_neuron_translations)
    translations.update(dual_exp_synapse_translations)

    # --------------------------------------------------------------------------
    # Internal SpiNNaker properties
    # --------------------------------------------------------------------------
    # How many of these neurons per core can
    # a SpiNNaker neuron processor handle
    _max_neurons_per_core = 1024

    _neuron_region_class = regions.Neuron

    _directly_connectable = False

    _neuron_immutable_param_map = if_curr_neuron_immutable_param_map
    _neuron_mutable_param_map = if_curr_neuron_mutable_param_map

    _synapse_immutable_param_map = dual_exp_synapse_immutable_param_map
    _synapse_mutable_param_map = dual_exp_synapse_curr_mutable_param_map