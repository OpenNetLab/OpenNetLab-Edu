from onl.sim import Environment
from onl.packet import DistPacketGenerator, PacketSink
from onl.netdev import TokenBucket


def packet_arrival():
    return 2.5


def packet_size():
    return 100


env = Environment()
pg1 = DistPacketGenerator(
    env, "flow_1", packet_arrival, packet_size, initial_delay=7.0, finish=35, flow_id=1, debug=True
)
pg2 = DistPacketGenerator(
    env, "flow_2", packet_arrival, packet_size, initial_delay=7.0, finish=35, flow_id=2, debug=True
)
ps = PacketSink(env, rec_flow_ids=False)

source_rate = 8.0 * packet_size() / packet_arrival()

shaper = TokenBucket(env, rate=0.5*source_rate, peak=0.7*source_rate, bucket_size=packet_size())

pg1.out = ps
pg2.out = shaper
shaper.out = ps

env.run(until=100)

print(f"Packet arrival times in flow 1: {ps.arrivals['flow_1']}")
print(f"Packet arrival times in flow 2: {ps.arrivals['flow_2']}")

def is_module_importable(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


if is_module_importable("matplotlib"):
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots()

    axis.vlines(ps.arrivals['flow_1'],
                0.0,
                1.0,
                colors="g",
                linewidth=2.0,
                label='input stream of packets')
    axis.vlines(ps.arrivals['flow_2'],
                0.0,
                0.7,
                colors="r",
                linewidth=2.0,
                label='output stream of packets')

    axis.set_title("Arrival times")
    axis.set_xlabel("time")
    axis.set_ylim([0, 1.5])
    axis.set_xlim([0, max(ps.arrivals['flow_1']) + 10])
    axis.legend()
    fig.savefig("token_bucket.png")
    plt.show()
