import logging
import pynn_spinnaker as sim
from matplotlib import pyplot as plt
from pynn_spinnaker_if_curr_dual_exp import IF_curr_dual_exp
from pyNN.utility.plotting import Figure, Panel

logger = logging.getLogger("pynn_spinnaker")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# SpiNNaker setup
sim.setup(timestep=1.0, max_delay=8.0,
          spinnaker_hostname="192.168.1.1")


    
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

'''

# Extract currents and voltages
recorded_voltages = [d.get_voltage(cell, spinnaker) for cell in cells]
recorded_currents = [d.get_current(cell, spinnaker) for cell in cells]

#print recorded_voltages
def plot_trace(trace, axis, title, y_axis_label, colour):
    axis.plot([t[2] for t in trace], color=colour) 
    axis.set_xlabel('Time/ms')
    axis.set_ylabel(y_axis_label)
    axis.set_title(title)
    
figure, axisArray = pylab.subplots(len(cells), 2)

for i, (voltage, current) in enumerate(zip(recorded_voltages, recorded_currents)):
    plot_trace(voltage, axisArray[i][0], "Cell %u voltage" % i, "Voltage/mV", "blue")
    plot_trace(current, axisArray[i][1], "Cell %u current" % i, "Current/nA", "blue")
    '''
plt.show()
p.end()
'''
if spinnaker:
    p.end(stop_on_board=True)
else:
    p.end()

'''