# -----------------------------------------------------------------------------
# Example of integrate-and-fire neuron with spike-frequency adaption
# Model and example taken from Liu, Y. H., & Wang, X. J. (2001).
# Spike-frequency adaptation of a generalized leaky integrate-and-fire model
# neuron.
# Journal of Computational Neuroscience, 10(1), 25-45.
# doi:10.1023/A:1008916026143
# -----------------------------------------------------------------------------
import logging
import math
import numpy
import pylab

import pynn_spinnaker as sim
from pynn_spinnaker_if_curr_ca2_adaptive import IF_curr_ca2_adaptive_exp

logger = logging.getLogger("pynn_spinnaker")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


# Timestep (ms)
# **NOTE** the 2.5Khz input frequency is not going to work particularily well
# at 1ms
dt = 0.1

# Number of neurons - used to gather enough ISIs to get a smooth estimate
N = 300

# Time (ms) to simulate for
T = 250

# Setup simulator
sim.setup(timestep=dt, min_delay=dt, max_delay=dt * 7, spinnaker_hostname="192.168.1.1")

# Create population of neurons
cell = sim.Population(N, IF_curr_ca2_adaptive_exp(tau_m=20.0, cm=0.5,
                                                  v_rest=-70.0, v_reset=-60.0,
                                                  v_thresh=-54.0, i_alpha=0.1,
                                                  tau_ca2=50.0))

# Create poisson spike source
spike_source = sim.Population(N, sim.SpikeSourcePoisson(rate=2500.0))

sim.Projection(spike_source, cell,
               sim.OneToOneConnector(),
               sim.StaticSynapse(weight=0.1, delay=dt),
               receptor_type="excitatory")

cell.record("spikes")
# cell.record_gsyn()

sim.run(T)

data = cell.get_data()

# Calculate isis and pair these with bin index of last spike time in pair
# **NOTE** using first spike time in pair leads to a dip at the
# end as the end of long pairs goes off the end of the simulation
binned_isis = numpy.hstack([
    numpy.vstack(
        (t[1:] - t[:-1],
         numpy.digitize(t[1:], numpy.arange(T)) - 1))
    for t in data.segments[0].spiketrains])

# Split ISIs into seperate array for each time bin
time_binned_isis = [binned_isis[0, binned_isis[1] == t] for t in range(T)]

# Create a dictionary of non-empty time bins to mean ISI
mean_isis = {t: numpy.average(i)
             for (t, i) in enumerate(time_binned_isis) if len(i) > 0}

# Calculate the coefficient of variance for each time bin
isi_cv = {t: math.sqrt(
    numpy.sum(numpy.power(time_binned_isis[t] - mean_isi, 2)) /
    float(len(time_binned_isis[t]))) / mean_isi
    for (t, mean_isi) in mean_isis.iteritems()}

# Take average CA2 level across all neurons
# average_ca2 = numpy.average(numpy.reshape(ca2[:,2], (N, int(T / dt))),
#                             axis=0)

# Plot
fig, axes = pylab.subplots(2, sharex=True)

axes[0].scatter(list(mean_isis.iterkeys()),
                [1000.0 / i for i in mean_isis.itervalues()], s=2)
axes[0].set_ylabel("Firing rate/Hz")

# axes[1].scatter(numpy.arange(0.0, T, dt), average_ca2, s=2)
# axes[1].set_ylabel("CA2/mA")
# axes[1].set_ylim((0.0, numpy.amax(average_ca2) * 1.25))

axes[1].scatter(list(isi_cv.iterkeys()), list(isi_cv.itervalues()), s=2)
axes[1].set_ylabel("Coefficient of ISI variance")

axes[1].set_xlim((0.0, T))
axes[1].set_xlabel("Time/ms")

sim.end()
pylab.show()
