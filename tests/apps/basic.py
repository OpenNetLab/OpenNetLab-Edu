from functools import partial
import random
from random import expovariate

from OpenNetLab.packet import *
from OpenNetLab.netdev import *
from OpenNetLab import sim


# Packets arrive with a constant interval of 1.5 seconds.
def arrival_1(): return 1.5
# Packets arrive with a constant interval of 2.0 seconds.
def arrival_2(): return 2.0
def packet_size(): return int(expovariate(0.01))
def delay_dist(): return 0.1


env = sim.Environment()

ps = PacketSink(env, rec_flow_ids=False, debug=True)

pg1 = DistPacketGenerator(env, "flow_1", arrival_1, packet_size, flow_id=0)
pg2 = DistPacketGenerator(env, "flow_2", arrival_2, packet_size, flow_id=1)

wire1 = Wire(env, partial(random.gauss, 0.1, 0.02), wire_id=1, debug=True)
wire2 = Wire(env, delay_dist, wire_id=2, debug=True)

pg1.out = wire1
pg2.out = wire2
wire1.out = ps
wire2.out = ps

env.run(until=100)

print("Flow 1 packet delays: " +
      ", ".join(["{:.2f}".format(x) for x in ps.waits['flow_1']]))
print("Flow 2 packet delays: " +
      ", ".join(["{:.2f}".format(x) for x in ps.waits['flow_2']]))

print("Packet arrival times in flow 1: " +
      ", ".join(["{:.2f}".format(x) for x in ps.arrivals['flow_1']]))

print("Packet arrival times in flow 2: " +
      ", ".join(["{:.2f}".format(x) for x in ps.arrivals['flow_2']]))
