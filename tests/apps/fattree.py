from functools import partial

from onl.topo import FatTree
from onl.sim import Environment
from onl.packet import DistPacketGenerator, PacketSink
from onl.netdev import FairPacketSwitch
from onl.topo import FatTree


env = Environment()

n_flows = 50
finish_time = 10.0
k = 4
pir = 1000000000  # 1Gbps
buffer_size = 1000

def size_dist():
    return 1024

def arrival_dist():
    return 0.0008  # 10Mbps

ft = FatTree(k)
all_flows = ft.generate_flows(n_flows)

for fid in all_flows:
    pg = DistPacketGenerator(
        env, f"Flow_{fid}", arrival_dist, size_dist, finish=finish_time, flow_id=fid
    )
    ps = PacketSink(env)

    all_flows[fid].pkt_gen = pg
    all_flows[fid].pkt_sink = ps

ft.generate_fib(all_flows)

n_classes_per_port = n_flows
weights = {c: 1 for c in range(n_classes_per_port)}

def flow_to_classes(flow_id, n_id, fib):
    return (flow_id + n_id + fib[flow_id]) % n_classes_per_port


for node_id in ft.topo.nodes():
    node = ft.topo.nodes[node_id]
    flow_classes = partial(flow_to_classes, n_id=node_id, fib=node["flow_to_port"])

    node["device"] = FairPacketSwitch(
        env, k, pir, buffer_size, weights, "WFQ", element_id=f"{node_id}", flow2class=flow_classes
    )

    # node["device"] = SimplePacketSwitch(
    #     env, k, pir, buffer_size, element_id=f"{node_id}"
    # )

    node["device"].demux.fib = node["flow_to_port"]

for n in ft.topo.nodes():
    node = ft.topo.nodes[n]
    for port_number, next_hop in node["port_to_nexthop"].items():
        node["device"].ports[port_number].out = ft.topo.nodes[next_hop]["device"]

for flow_id, flow in all_flows.items():
    flow.pkt_gen.out = ft.topo.nodes[flow.src]["device"]
    ft.topo.nodes[flow.dst]["device"].demux.ends[flow_id] = flow.pkt_sink

env.run(until=1000)
