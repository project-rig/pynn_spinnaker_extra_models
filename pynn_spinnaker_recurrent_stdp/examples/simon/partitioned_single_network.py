"""
Simple Associative Memory

File: partitioned_single_network.py

"""
#!/usr/bin/python
#import pyNN.spiNNaker as p
#import spynnaker_extra_pynn_models as q
import math, numpy, pylab, pickle
import os, sys
import logging
from pyNN.random import NumpyRNG, RandomDistribution
import patternGenerator as pg
import spikeTrains as st

numpy.random.seed(seed=1)
rng = NumpyRNG(seed=1)

# From JK:
import pynn_spinnaker as p
import pynn_spinnaker_recurrent_stdp as r
logger = logging.getLogger("pynn_spinnaker")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
#setup_kwargs = {"spalloc_num_boards": 6}
setup_kwargs = {"spinnaker_hostname": "192.168.1.1", "stop_on_spinnaker": False, "disable_software_watchdog": True}
# end JK

timeStep = 0.1

fullyConnected = False

p.setup(timestep=timeStep, min_delay = timeStep, max_delay = timeStep * 14, **setup_kwargs)

nSourceNeurons = 3200 # number of input (excitatory) neurons
nExcitNeurons  = 3200 # number of excitatory neurons in the recurrent memory
sourcePartitionSz = 50 # Number of spike sources in a single projection
numPartitions = 1.0 * nSourceNeurons / sourcePartitionSz
if numPartitions != int(numPartitions):
   print "Invalid partition size! Exiting!!!"
   quit()
numPartitions = int(numPartitions)
nInhibNeurons  = 10  # number of inhibitory neurons in the recurrent memory
nTeachNeurons  = nExcitNeurons
nNoiseNeurons  = 10
ProbFiring     = 0.05
connProb       = 0.11   # was 11
myJitter       = 0.0 # was 0.25 # was 0.119
tolerance      = 2.5 # ms
total_delay    = 2.0 # ms
dendriticDelayFraction = 1.0

nSourceFiring  = int(nSourceNeurons * ProbFiring)
nExcitFiring   = int(nExcitNeurons * ProbFiring)

patternCycleTime = 35
numPatterns = int(sys.argv[1]) 
numRepeats  = 15 # was 8
numRecallRepeats  = 1
binSize = 4
numBins = patternCycleTime/binSize
interPatternGap = 0    # was 10
potentiationRate = 0.80
accPotThreshold = 5 
depressionRate = 0.0  # was 0.4
accDepThreshold = -5 
meanPreWindow  = 8.0
meanPostWindow = 8.0

windowSz = 10.0 # tolerance for errors during recall

baseline_excit_weight = 0.0
weight_to_force_firing = 18.0
# Max_weight for 30K neurons: 0.18, for 40K neurons: 0.135
max_weight = 0.6 # was 0.25          # 0.8               # Max weight! was 0.66 in best run so far
min_weight = 0.0
print "Pattern cycle time: ", patternCycleTime

print "Source neurons: ", nSourceNeurons
print "Excit neurons: ", nExcitNeurons
print "Source firing: ", nSourceFiring
print "Excit firing: ", nExcitFiring
print "Jitter SD: ", myJitter
print "Pattern cycle time: ", patternCycleTime, "ms"
print "Num patterns: ", numPatterns
print "Num repeats during learning: ", numRepeats
print "Num repeats during recall: ", numRecallRepeats
print "Num partitions: ", numPartitions
print "Partition size: ", sourcePartitionSz

cell_params_lif   = {'cm'        : 0.25, # nF was 0.25
                     'i_offset'  : 0.0,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 0.5,
                     'tau_syn_I' : 0.5,
                     'v_reset'   : -10.0,
                     'v_rest'    : 0.0,
                     'v_thresh'  : 20.0
                     }

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Construct pattern set

inPatterns = list()
outPatterns = list()
for i in range(numPatterns):
   patt = pg.pattern(nSourceNeurons, nSourceFiring, patternCycleTime, numBins, rng, spikeTrain=False, jitterSD = myJitter, spuriousSpikeProb = 0.0)
   inPatterns.append(patt)
   patt = pg.pattern(nExcitNeurons, nExcitFiring, patternCycleTime, numBins, rng, spikeTrain=False, jitterSD = myJitter, spuriousSpikeProb = 0.0)
   outPatterns.append(patt)

timeCount = 0
patternPresentationOrder = list()
patternPresentationOrder.append(-1)
teachingOrder = list()
teachingOrder.append(-1)
# Teaching phase:
for patt in range(numPatterns):
    for rpt in range(numRepeats):
        patternPresentationOrder.append(patt)
        teachingOrder.append(patt)
        timeCount +=1
# Gap:
patternPresentationOrder.append(-1)
patternPresentationOrder.append(-1)
timeCount +=2
# Recall phase:
for patt in range(numPatterns):
    for rpt in range(numRecallRepeats):
        patternPresentationOrder.append(patt)
        patternPresentationOrder.append(patt)
        timeCount +=1

myStimulus=pg.spikeStream()
recordStartTime, patternTiming = myStimulus.buildStream(numSources=nSourceNeurons, patterns=inPatterns, interPatternGap=interPatternGap, offset=0.0, order=patternPresentationOrder)
#print "Pattern timings:"
#print patternTiming
teachingInput=pg.spikeStream()
teachingInput.buildStream(numSources=nExcitNeurons, patterns=outPatterns, interPatternGap=interPatternGap, offset=-0.5, order=teachingOrder)

runTime = myStimulus.endTime + 500
print "Run time is ", runTime, " ms"
print "Start recording at ", recordStartTime, " ms"

# Save network info:
netInfo= dict()
netInfo['sourceNeurons']= nSourceNeurons
netInfo['excitNeurons']= nExcitNeurons
netInfo['probFiring']= ProbFiring
netInfo['connProb']= connProb
netInfo['jitter']= myJitter
netInfo['tolerance']= tolerance
netInfo['totalDelay']= total_delay
netInfo['dendriticFrac']= dendriticDelayFraction
netInfo['cycleTime']= patternCycleTime
netInfo['numPatterns']= numPatterns
netInfo['numRepeats']= numRepeats
netInfo['numRecallRepeats']= numRecallRepeats
netInfo['runTime']= runTime
netInfo['potRate']= potentiationRate
netInfo['depRate']= depressionRate
netInfo['potThresh']= accPotThreshold
netInfo['depThresh']= accDepThreshold
netInfo['meanPreWindow']= meanPreWindow
netInfo['meanPostWindow']= meanPostWindow
netInfo['maxWeight']= max_weight
netInfo['minWeight']= min_weight
dirName = "./myResults/patts_%d" % numPatterns
os.system("mkdir %s" % dirName)
numpy.save(dirName+"/neuronParams", cell_params_lif)
with open(dirName+"/networkParams", "wb") as outfile:
    pickle.dump(netInfo, outfile, protocol=pickle.HIGHEST_PROTOCOL)
with open(dirName+"/inputPatterns", "wb") as outfile:
    pickle.dump(inPatterns, outfile, protocol=pickle.HIGHEST_PROTOCOL)
with open(dirName+"/outputPatterns", "wb") as outfile:
    pickle.dump(outPatterns, outfile, protocol=pickle.HIGHEST_PROTOCOL)
with open(dirName+"/patternTiming", "wb") as outfile:
    pickle.dump(patternTiming, outfile, protocol=pickle.HIGHEST_PROTOCOL)

#with open("mydict", "rb") as outfile:
#    a=pickle.load(outfile)


# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Construct Network

populations = list()
projections = list()

stimulus = 0
inhib = numPartitions
excit  = numPartitions + 1
teacher = numPartitions + 2

teachingSpikeArray = {'spike_times': teachingInput.streams}

for i in range(numPartitions):
    arrayLabel = "ssArray%d" % i
    startIdx = i * sourcePartitionSz
    endIdx = startIdx + sourcePartitionSz
    streamSubset = myStimulus.streams[startIdx:endIdx]
    spikeArray = {'spike_times': streamSubset}
    populations.append(p.Population(sourcePartitionSz, p.SpikeSourceArray, spikeArray, label=arrayLabel))             # 0

populations.append(p.Population(nInhibNeurons, p.IF_curr_exp, cell_params_lif, label='inhib_pop'))                 # 1
populations.append(p.Population(nExcitNeurons, p.IF_curr_exp, cell_params_lif, label='excit_pop'))                 # 2
populations.append(p.Population(nTeachNeurons, p.SpikeSourceArray, teachingSpikeArray, label='teaching_ss_array')) # 3

# XXXXXXXXXXX finish this! xxxxxxxxxx
for i in range(numPartitions):
    projections.append(p.Projection(populations[i], populations[excit],
        p.FixedProbabilityConnector(p_connect=connProb),
        r.RecurrentSTDPSynapse(w_min=0.0, w_max=16.0, A_plus=0.3, A_minus=0.3,
            accumulator_increase=1.0 / 2.0, accumulator_decrease=1.0 / 6.0,
            lambda_pre=10.0, lambda_post=10.0, tau_a=300.0, weight=baseline_excit_weight, delay=1.0),
        receptor_type='excitatory'))

#plastic_connection = p.Projection(source_pop, excit_pop,
#                                  p.AllToAllConnector(),
#                                  r.RecurrentSTDPSynapse(w_min=0.0, w_max=16.0, A_plus=0.3, A_minus=0.3,
#                                                         accumulator_increase=1.0 / 2.0, accumulator_decrease=1.0 / 6.0,
#                                                         lambda_pre=10.0, lambda_post=10.0,
#                                                         tau_a=3000.0,
#                                                         weight=baseline_excit_weight, delay=1.0),
#                                  receptor_type='excitatory')

# Partition main projections into a number of sub-projections:
#for i in range(numPartitions):
#   if fullyConnected:
#      projections.append(p.Projection(populations[i], populations[excit], p.AllToAllConnector(weights=baseline_excit_weight, delays=total_delay), target='excitatory', synapse_dynamics=p.SynapseDynamics(slow=stdp_model)))
#   else:
#      projections.append(p.Projection(populations[i], populations[excit], p.FixedProbabilityConnector(p_connect=connProb, weights=baseline_excit_weight, delays=total_delay), target='excitatory', synapse_dynamics=p.SynapseDynamics(slow=stdp_model)))

projections.append(p.Projection(populations[teacher], populations[excit], p.OneToOneConnector(),
                           p.StaticSynapse(weight=weight_to_force_firing, delay=timeStep), receptor_type='excitatory'))

# XXXXXXXXXXXXXXXXXXXXX
# Run network

#populations[excit].record_v()
populations[excit].record("spikes")
#populations[excit].record(schedule=[(recordStartTime, runTime)])

p.run(runTime)

# XXXXXXXXXXXXXXXXXXXXXX
# Weight Statistics

if True: # (weight stats)
   count_plus = 0
   count_minus = 0
   weightUse = {}
   for i in range(numPartitions):
       final_weights = projections[i].getWeights(format="array")
       for row in final_weights:
           partCount = 0
           for j in row:
              # NaN is used to signify non-connections so skip
              if math.isnan(j):
                  continue

              myString="%f"%j
              if myString in weightUse:
                  weightUse[myString] += 1
              else:
                  weightUse[myString] = 1
              if j > 0.0:
                  count_plus += 1
                  partCount += 1
              if j <= 0.0:
                  count_minus += 1
           #print "%d " % partCount
       # Clear memory holding unneeded weight data:
       projections[i]._host_based_synapse_list = None

   print "High weights: ", count_plus
   print "Low weights: ", count_minus
   print "Weight usage: ", weightUse
   perPatternUsage = (count_plus*1.0)/(nSourceFiring * numPatterns)
# End if False (weight stats)

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Process output spikes against expected patterns

v = None
gsyn = None
spikes = None

#v = populations[excit].get_v(compatible_output=True)
spikes = populations[excit].getSpikes(compatible_output=True)

# Go through the output spikes and extract sections that should correspond to the
# individual patterns presented:

numpy.save(dirName+"/outputSpikesFile", spikes)

os.system('date')

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Draw Plots

doPlots = False
if doPlots:
    if spikes != None:
        pylab.figure()
        pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".") 
        pylab.xlabel('Time/ms')
        pylab.ylabel('spikes')
        pylab.title('Spikes of Excitatory Neurons')
        #pylab.show()
    else:
        print "No spikes received"

pylab.show()

p.end()

