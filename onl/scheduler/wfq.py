from typing import Dict, Set

from ..types import *
from ..sim import Environment, ProcessGenerator, SimTime, PriorityStore, PriorityItem
from ..packet import Packet
from .base import Scheduler


class WFQ(Scheduler):
    """Implements a Weighted Fair Queueing (WFQ) scheduler"""

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
        """The calculated finish time of each packet
        """
        self.active_set: Set[FlowId] = set()
        """The flow_id set of all non-empty subqueue
        """
        self.vtime: SimTime = 0.0
        """Virtual clock time, the time elasping speed is based
        on the size of active set
        """
        self.last_time: SimTime = 0.0
        """Clock time of most recent put and send operation"""
        self.store = PriorityStore(env)

        self.action = env.process(self.run(env))

    def update_vtime(self):
        """Update vtime according to
        1. clock time elapsed since last put or send
        2. weights of current active set
        """
        weight_sum = 0.0
        now = self.env.now
        for i in self.active_set:
            weight_sum += self.weights[i]
        self.vtime += (now - self.last_time) / weight_sum

    def reset_vtime(self):
        self.vtime = 0
        for flow_id in self.weights.keys():
            self.finish_times[flow_id] = 0.0

    def run(self, env: Environment) -> ProcessGenerator:
        while True:
            item: PriorityItem = yield self.store.get()
            packet: Packet = item.item
            # print(f"flow {packet.flow_id} finish at : {item.priority}")
            yield env.process(self.send_packet(packet))
            self.update_vtime()
            flow_id = packet.flow_id
            if self.queue_count[flow_id] == 0:
                self.active_set.remove(flow_id)
            if len(self.active_set) == 0:
                self.reset_vtime()
            self.last_time = env.now

    def put(self, packet: Packet):
        flow_id = packet.flow_id
        now = self.env.now
        if len(self.active_set) == 0:
            self.reset_vtime()
        else:
            self.update_vtime()
            self.finish_times[flow_id] = max(
                self.finish_times[flow_id], self.vtime
            ) + packet.size * 8.0 / (self.rate * self.weights[flow_id])

        self.add_packet_to_queue(packet)
        self.active_set.add(flow_id)
        self.last_time = now

        self.dprint(
            f"Packet arrived at {now}, with flow_id {flow_id}, "
            f"packet_id {packet.packet_id}, "
            f"finish_time {self.finish_times[flow_id]}"
        )

        self.store.put(PriorityItem((self.finish_times[flow_id], now), packet))
