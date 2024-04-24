import networkx as nx
from random import sample

from ..flow import Flow

class FatTree:
    def __init__(self, k: int):
        if not isinstance(k, int):
            raise TypeError('k argument must be of int type')
        if k < 1 or k % 2 == 1:
            raise ValueError('k must be a positive even integer')

        topo = nx.Graph()
        topo.name = "fat_tree_topology(%d)" % (k)

        # Create core nodes
        n_core = (k // 2)**2
        topo.add_nodes_from([v for v in range(int(n_core))],
                            layer='core',
                            type='switch')

        # Create aggregation and edge nodes and connect them
        for pod in range(k):
            aggr_start_node = topo.number_of_nodes()
            aggr_end_node = aggr_start_node + k // 2
            edge_start_node = aggr_end_node
            edge_end_node = edge_start_node + k // 2
            aggr_nodes = range(aggr_start_node, aggr_end_node)
            edge_nodes = range(edge_start_node, edge_end_node)
            topo.add_nodes_from(aggr_nodes,
                                layer='aggregation',
                                type='switch',
                                pod=pod)
            topo.add_nodes_from(edge_nodes, layer='edge', type='switch', pod=pod)
            topo.add_edges_from([(u, v) for u in aggr_nodes for v in edge_nodes],
                                type='aggregation_edge')

        # Connect core switches to aggregation switches
        for core_node in range(n_core):
            for pod in range(k):
                aggr_node = n_core + (core_node // (k // 2)) + (k * pod)
                topo.add_edge(core_node, aggr_node, type='core_aggregation')

        # Create hosts and connect them to edge switches
        for u in [v for v in topo.nodes() if topo.nodes[v]['layer'] == 'edge']:
            leaf_nodes = range(topo.number_of_nodes(),
                               topo.number_of_nodes() + k // 2)
            topo.add_nodes_from(leaf_nodes,
                                layer='leaf',
                                type='host',
                                pod=topo.nodes[u]['pod'])
            topo.add_edges_from([(u, v) for v in leaf_nodes], type='edge_leaf')

        # for i in range(len(topo.nodes)):
        #     print(i, topo.nodes[i])
        #     print(list(filter(lambda e: e[0] == i, topo.edges)))

        self._topo = topo

        hosts = set()
        for n in topo.nodes():
            if topo.nodes[n]["type"] == "host":
                hosts.add(n)
        self._hosts = hosts

    @property
    def topo(self):
        return self._topo

    @property
    def hosts(self):
        return self._hosts

    def generate_flows(
        self,
        nflows,
        size=None,
        start_time=None,
        finish_time=None,
        arrival_dist=None,
        size_dist=None,
    ):
        all_flows = dict()
        for flow_id in range(nflows):
            src, dst = sample(sorted(self.hosts), 2)
            all_flows[flow_id] = Flow(
                flow_id,
                src,
                dst,
                size=size,
                start_time=start_time,
                finish_time=finish_time,
                arrival_dist=arrival_dist,
                size_dist=size_dist,
            )
            # all_flows[flow_id].path = sample(
            #    list(nx.all_simple_paths(G, src, dst, cutoff=nx.diameter(G))), 1
            all_flows[flow_id].path = sample(list(nx.all_shortest_paths(self.topo, src, dst)), 1)[0]
        return all_flows

    def generate_fib(self, all_flows, tcp=False):
        for n in self.topo.nodes():
            node = self.topo.nodes[n]

            node["port_to_nexthop"] = dict()
            node["nexthop_to_port"] = dict()

            for port, nh in enumerate(nx.neighbors(self.topo, n)):
                node["nexthop_to_port"][nh] = port
                node["port_to_nexthop"][port] = nh

            node["flow_to_port"] = dict()
            node["flow_to_nexthop"] = dict()

        for f in all_flows:
            flow = all_flows[f]
            path = list(zip(flow.path, flow.path[1:]))
            for seg in path:
                a, z = seg
                self.topo.nodes[a]["flow_to_port"][flow.fid] = self.topo.nodes[a]["nexthop_to_port"][z]
                self.topo.nodes[a]["flow_to_nexthop"][flow.fid] = z

                # generates reverse fib for TCPSink sending Ack to TCPSource
                if tcp:
                    self.topo.nodes[z]["flow_to_port"][flow.fid + 10000] = self.topo.nodes[z][
                        "nexthop_to_port"
                    ][a]
                    self.topo.nodes[z]["flow_to_nexthop"][flow.fid + 10000] = a
