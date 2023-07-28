from typing import Dict

from ..types import *
from ..sim import Environment, ProcessGenerator, SimTime, PriorityStore
from ..packet import Packet
from .base import Scheduler


class WFQ(Scheduler):
    """
    Implements a Weighted Fair Queueing (WFQ) server.

    Reference:
    A. K. Parekh, R. G. Gallager, "A Generalized Processor Sharing Approach to Flow Control
    in Integrated Services Networks: The Single-Node Case," IEEE/ACM Trans. Networking,
    vol. 1, no. 3, pp. 344-357, June 1993.

    https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=234856

    """

    def __init__(
        self,
        env: Environment,
        rate: float,
        weights: Dict[FlowId, int],
        debug: bool = False,
    ):
        super().__init__(env, rate, debug)
        self.weights = weights
        self.finish_times: Dict[FlowId, SimTime] = dict()
        self.active_set = set()
        self.vtime: SimTime = 0.0
        self.last_update: SimTime = 0.0
        self.store = PriorityStore(env)

    def run(self, env: Environment) -> ProcessGenerator:
        while True:
            _, packet = yield self.store.get()
            env.process(self.send_packet(packet))

    def put(self, packet: Packet):
        self.packets_received += 1
        flow_id = packet.flow_id
        now = self.env.now
        if len(self.active_set) == 0:
            self.vtime = 0.0
            for flow_id, _ in self.finish_times.items():
                self.finish_times[flow_id] = 0.0
        else:
            weight_sum = 0.0
            for i in self.active_set:
                weight_sum += self.weights[i]
            self.vtime += (now - self.last_update) / weight_sum
            self.finish_times[flow_id] = (
                max(self.finish_times[flow_id], self.vtime)
                + packet.size * 8.0 / self.rate * self.weights[flow_id]
            )

        self.queue_byte_size[flow_id] += packet.size
        self.queue_count[flow_id] += 1
        self.active_set.add(flow_id)
        self.last_update = now

        self.dprint(
            f"Packet arrived at {now}, with flow_id {flow_id}, "
            f"packet_id {packet.packet_id}, "
            f"finish_time {self.finish_times[flow_id]}"
        )

        self.store.put((self.finish_times[flow_id], packet))
