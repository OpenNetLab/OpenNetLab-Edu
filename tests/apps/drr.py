from functools import partial
from random import expovariate

from onl.sim import Environment
from onl.packet import DistPacketGenerator, PacketSink
from onl.scheduler import Monitor, DRR
from onl.netdev import Splitter


def packet_arrival():
    return 2


def const_size():
    return 1000


env = Environment()
pg1 = DistPacketGenerator(
    env, "flow_0", packet_arrival, const_size, initial_delay=0.0, finish=50, flow_id=0
)
pg2 = DistPacketGenerator(
    env, "flow_1", packet_arrival, const_size, initial_delay=10.0, finish=50, flow_id=1
)
ps = PacketSink(env)
sink_1 = PacketSink(env)
sink_2 = PacketSink(env)

source_rate = 8.0 * const_size() / packet_arrival()
wfq = DRR(env, source_rate, {0: 1, 1: 2}, debug=False)
monitor = Monitor(env, wfq, partial(expovariate, 0.1), service_included=True)

splitter_1 = Splitter()
splitter_2 = Splitter()

pg1.out = splitter_1
pg2.out = splitter_2

splitter_1.out1 = wfq
splitter_1.out2 = sink_1
splitter_2.out1 = wfq
splitter_2.out2 = sink_2

wfq.out = ps

env.run(until=1000)

print("At the WFQ server, the queue lengths in # packets for flow 0 are:")
print(monitor.sizes[0])
print("At the WFQ server, the queue lengths in # packets for flow 1 are:")
print(monitor.sizes[1])
print("At the WFQ server, the queue lengths in bytes for flow 0 are:")
print(monitor.byte_sizes[0])
print("At the WFQ server, the queue lengths in bytes for flow 1 are:")
print(monitor.byte_sizes[1])

print("At the packet sink, packet arrival times for flow 0 are:")
print(ps.arrivals[0])

print("At the packet sink, packet arrival times for flow 1 are:")
print(ps.arrivals[1])


def is_module_importable(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


if is_module_importable("matplotlib"):
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True)
    ax1.vlines(sink_1.arrivals[0], 0.0, 1.0, colors="g", linewidth=2.0, label="Flow 0")
    ax1.vlines(sink_2.arrivals[1], 0.0, 0.7, colors="r", linewidth=2.0, label="Flow 1")
    ax1.set_title("Arrival times at the DRR server")
    ax1.set_ylim([0, 1.5])
    ax1.set_xlim([0, max(sink_1.arrivals[0]) + 10])
    ax1.grid(True)
    ax1.legend()

    ax2.vlines(ps.arrivals[0], 0.0, 1.0, colors="g", linewidth=2.0, label="Flow 0")
    ax2.vlines(ps.arrivals[1], 0.0, 0.7, colors="r", linewidth=2.0, label="Flow 1")
    ax2.set_title("Departure times from the DRR server")
    ax2.set_xlabel("time")
    ax2.set_ylim([0, 1.5])
    ax2.set_xlim([0, max(ps.arrivals[0]) + 10])
    ax2.grid(True)
    ax2.legend()

    fig.savefig("drr.png")

    plt.show()
