"""
An example of using the Weighted Fair Queueing (WFQ) scheduler.
"""
from functools import partial
from random import expovariate

from onl.sim import Environment
from onl.packet import DistPacketGenerator, PacketSink
from onl.scheduler import Monitor, WFQ
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
pg3 = DistPacketGenerator(
    env, "flow_2", packet_arrival, const_size, initial_delay=10.0, finish=50, flow_id=2
)
ps = PacketSink(env)
sink_1 = PacketSink(env)
sink_2 = PacketSink(env)
sink_3 = PacketSink(env)

source_rate = 8.0 * const_size() / packet_arrival()
wfq = WFQ(env, source_rate, {0: 1, 1: 2, 2: 3}, debug=False)
monitor = Monitor(env, wfq, partial(expovariate, 0.1), service_included=True)

splitter_1 = Splitter()
splitter_2 = Splitter()
splitter_3 = Splitter()

pg1.out = splitter_1
pg2.out = splitter_2
pg3.out = splitter_3

splitter_1.out1 = wfq
splitter_1.out2 = sink_1
splitter_2.out1 = wfq
splitter_2.out2 = sink_2
splitter_3.out1 = wfq
splitter_3.out2 = sink_3

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
    font_options = {
        'family' : 'serif', # 设置字体家族
        'serif' : 'simsun', # 设置字体
        'size': 10,
    }
    plt.rc('font',**font_options)

    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True)
    ax1.vlines(sink_1.arrivals[0], 0.0, 1.0, colors="g", linewidth=2.0, label="流0")
    ax1.vlines(sink_2.arrivals[1], 0.0, 0.7, colors="r", linewidth=2.0, label="流1")
    ax1.vlines(sink_3.arrivals[2], 0.0, 0.5, colors="b", linewidth=2.0, label="流2")
    ax1.set_title("流的到达时间")
    ax1.set_ylim([0, 1.5])
    ax1.set_xlim([0, max(sink_1.arrivals[0]) + 10])
    ax1.grid(True)
    ax1.legend()

    ax2.vlines(ps.arrivals[0], 0.0, 1.0, colors="g", linewidth=2.0, label="流0")
    ax2.vlines(ps.arrivals[1], 0.0, 0.7, colors="r", linewidth=2.0, label="流1")
    ax2.vlines(ps.arrivals[2], 0.0, 0.5, colors="b", linewidth=2.0, label="流2")
    ax2.set_title("流的离开时间")
    ax2.set_xlabel("模拟时间")
    ax2.set_ylim([0, 1.5])
    ax2.set_xlim([0, max(ps.arrivals[0]) + 10])
    ax2.grid(True)
    ax2.legend()

    fig.savefig("wfq.pdf")

    plt.show()
