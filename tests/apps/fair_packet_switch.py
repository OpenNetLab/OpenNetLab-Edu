from onl.netdev import FairPacketSwitch
from onl.packet import DistPacketGenerator, PacketSink
from onl.sim import Environment

def packet_arrival():
    return 1.0

def const_size():
    return 1000


env = Environment()
pg1 = DistPacketGenerator(
    env,
    "flow_0",
    packet_arrival,
    const_size,
    initial_delay=0.0,
    finish=3,
    flow_id=0,
    rec_flow=True
)

pg2 = DistPacketGenerator(
    env,
    "flow_1",
    packet_arrival,
    const_size,
    initial_delay=0.1,
    finish=3,
    flow_id=1,
    rec_flow=True
)

ps = PacketSink(env)

port_rate = 8000
buffer_size = 1100

switch = FairPacketSwitch(
    env,
    nports=1,
    port_rate=port_rate,
    buffer_size=buffer_size,
    weights={0: 1, 1: 2},
    server="DRR",
    debug=True
)
switch.egress_ports[0].limit_bytes = True
pg1.out = switch
pg2.out = switch
switch.ports[0].out = ps
switch.demux._fib = {0: 0, 1: 0}

env.run()

print("\n==========Basic Info==========")

print(
    f"The buffer size is {buffer_size} bytes, the port rate is {port_rate / 8} bytes/sec, "
    f"and the packet size is {const_size()} bytes."
)

print("==========Result==========")
print("For the switch, the packet arrival times for flow 0 are:")
print(pg1.time_rec)

print("For the switch, the packet arrival times for flow 1 are:")
print(pg2.time_rec)

print("At the packet sink, packet arrival times for flow 0 are:")
print(ps.arrivals[0])

print("At the packet sink, packet arrival times for flow 1 are:")
print(ps.arrivals[1])
