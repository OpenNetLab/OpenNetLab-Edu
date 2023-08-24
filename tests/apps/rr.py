from functools import partial
from random import expovariate

from onl.sim import Environment
from onl.packet import DistPacketGenerator, PacketSink
from onl.scheduler import RR
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
rr = RR(env, source_rate, [0, 1], debug=True)

splitter_1 = Splitter()
splitter_2 = Splitter()

pg1.out = splitter_1
pg2.out = splitter_2

splitter_1.out1 = rr
splitter_1.out2 = sink_1
splitter_2.out1 = rr
splitter_2.out2 = sink_2

rr.out = ps

env.run(until=1000)

print("At the packet sink, packet arrival times for flow 0 are:")
print(ps.arrivals[0])

print("At the packet sink, packet arrival times for flow 1 are:")
print(ps.arrivals[1])
