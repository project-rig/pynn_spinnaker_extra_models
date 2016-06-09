import logging
import pynn_spinnaker as sim
from matplotlib import pyplot as plt
from pynn_spinnaker_if_curr_dual_exp import IF_curr_dual_exp
from pyNN.utility.plotting import Figure, Panel

logger = logging.getLogger("pynn_spinnaker")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# SpiNNaker setup
sim.setup(timestep=1.0, max_delay=8.0, spalloc_num_boards=1)

    
cell_params = {'tau_m'   : 20.0,   'cm'         : 1.0,    'i_offset'   : 0.0,    'tau_refrac' : 3.0,
               'v_rest'  : -65.0,  'v_thresh'   : -51.0,  'tau_syn_E'  : 5.0,    'tau_syn_E2'  : 100.0,
               'tau_syn_I': 5.0,    'v_reset'    : -70.0}

cells = [sim.Population(1, IF_curr_dual_exp(**cell_params)),
         sim.Population(1, IF_curr_dual_exp(**cell_params))]

spike_sourceE = sim.Population(1, sim.SpikeSourceArray(spike_times=[i for i in range(50, 200, 20)]), label="spike_sourceE")
spike_sourceE2 = sim.Population(1, sim.SpikeSourceArray(spike_times=[i for i in range(100, 200, 100)]), label='spike_sourceE2')

synapse = sim.StaticSynapse(weight=0.5)
sim.Projection(spike_sourceE, cells[0], sim.OneToOneConnector(), synapse, receptor_type='excitatory', label="Excitatory - 0")

sim.Projection(spike_sourceE, cells[1], sim.OneToOneConnector(), synapse, receptor_type='excitatory', label="Excitatory - 1")
sim.Projection(spike_sourceE2, cells[1], sim.OneToOneConnector(), synapse, receptor_type='excitatory2', label="Excitatory2 - 1")

# Record all cells
for cell in cells:
    cell.record("v")

# Run simulation
sim.run(200.0)

# Build panels showing membrane potential
panels = [Panel(cell.get_data().segments[0].filter(name="v")[0], ylabel="%s membrane potential (mV)" % cell.label)
          for cell in cells]
Figure(*panels, title="Membrane voltages")

plt.show()
sim.end()