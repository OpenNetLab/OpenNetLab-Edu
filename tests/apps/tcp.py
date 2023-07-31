from onl.sim import Environment
from onl.packet import Flow, TCPPacketGenerator, TCPSink, TCPCubic
from onl.netdev import Wire

def packet_arrival():
    return 0.1

def packet_size():
    return 512

def delay_dist():
    return 0.1

env = Environment()

flow = Flow(
    flow_id=0,
    src="flow 1",
    dst="flow 1",
    start_time=0,
    finish_time=10,
    arrival_dist=packet_arrival,
    size_dist=packet_size
)

sender = TCPPacketGenerator(
    env,
    flow=flow,
    cc=TCPCubic(),
    rtt_estimate=0.5,
    debug=True
)
wire1downstream = Wire(env, delay_dist)
wire1upstream = Wire(env, delay_dist)
receiver = TCPSink(env, rec_waits=True, debug=True)

sender.out = wire1downstream
wire1downstream.out = receiver
receiver.out = wire1upstream
wire1upstream.out = sender

env.run(until=100)
