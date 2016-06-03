"""
Simple Associative Memory
"""
#!/usr/bin/python
import pynn_spinnaker as p
import pynn_spinnaker_recurrent_stdp as r
import numpy, pylab

p.setup(timestep=1.0, min_delay = 1.0, max_delay = 15.0, spalloc_num_boards=1)

nSourceNeurons = 1 # number of input (excitatory) neurons
nExcitNeurons  = 1 # number of excitatory neurons in the recurrent memory
nTeachNeurons  = 1
nNoiseNeurons  = 10
runTime = 3200

cell_params_lif   = {'cm'        : 0.25, # nF was 0.25
                     'i_offset'  : 0.0,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 0.5,
                     'tau_syn_I' : 0.5,
                     'v_reset'   : -70.0,
                     'v_rest'    : -70.0,
                     'v_thresh'  : -50.0
                     }

weight_to_force_firing = 15.0
baseline_excit_weight = 2.0

spikes0 = list()
teachingSpikes = list()
for i in range(runTime/40):
    spikes0.append(i*40)
for i in range(runTime/80):
    teachingSpikes.append(i*40+5+120)

#spikes0 = [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680]
spikes1 = [10, 50, 90, 130, 170, 210, 250, 290]
spikes2 = [20, 60, 100, 140, 180, 220, 260, 300]
spikes3 = [30, 70, 110, 150, 190, 230, 270, 310]
spikes4 = []
arrayEntries = []
for i in range(nSourceNeurons):
    newEntry = []
    for j in range(len(spikes0)):
        newEntry.append(spikes0[j]+i*40.0/100.0)
    arrayEntries.append(newEntry)

teachlist = list()
for i in range(nSourceNeurons):
    teachlist.append(teachingSpikes)

source_pop = p.Population(nSourceNeurons, p.SpikeSourceArray(spike_times=arrayEntries), label='excit_pop_ss_array')
excit_pop = p.Population(nExcitNeurons, p.IF_curr_exp(**cell_params_lif), label='excit_pop')
teaching_pop = p.Population(nTeachNeurons, p.SpikeSourceArray(spike_times=teachlist), label='teaching_ss_array')

'''w_min",                 "w_min"),
        ("w_max",                 "w_max"),
        ("A_plus",                "a_plus"),
        ("A_minus",               "a_minus"),

        ("accumulator_increase",  "accumulator_increase"),
        ("accumulator_decrease",  "accumulator_decrease"),

        ("lambda_pre",            "lambda_pre"),
        ("lambda_post",           "lambda_post"),

        ("tau_a",                 "tau_a'''
plastic_connection = p.Projection(source_pop, excit_pop,
                                  p.AllToAllConnector(),
                                  r.RecurrentSTDPSynapse(w_min=0.0, w_max=16.0, A_plus=0.2, A_minus=0.2,
                                                         accumulator_increase=1.0 / 3.0, accumulator_decrease=1.0 / 6.0,
                                                         lambda_pre=10.0, lambda_post=10.0,
                                                         tau_a=200.0
                                                         weight=baseline_excit_weight, delay=1.0),
                                  receptor_type='excitatory')

p.Projection(teaching_pop, excit_pop, p.OneToOneConnector(), p.StaticSynapse(weight=weight_to_force_firing, delay=1.0), receptor_type='excitatory')

populations[excit].record_v()
populations[excit].record()

p.run(runTime)

final_weights = plastic_connection.getWeights()
print "Final weights: ", final_weights

v = populations[excit].get_v(compatible_output=True)tput=True)
spikes = populations[excit].getSpikes(compatible_output=True)

if spikes != None:
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('Spikes of Excitatory Neurons')
    #pylab.show()
else:
    print "No spikes received"

# Make some graphs
ticks = len(v) / nExcitNeurons

# Excitatory neuron current:
if v != None:
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('mV')
    pylab.title('Potential of neuron 1')
    for pos in range(0, nExcitNeurons, 40):
        v_for_neuron = v[pos * ticks : (pos + 1) * ticks]
        pylab.plot([i[1] for i in v_for_neuron],
                [i[2] for i in v_for_neuron])

pylab.show()

p.end()

