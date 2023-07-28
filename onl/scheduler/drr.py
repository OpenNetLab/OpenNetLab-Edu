from typing import Dict
from ..types import *
from ..sim import Environment, ProcessGenerator
from ..packet import Packet
from .base import MultiQueueScheduler


class DRR(MultiQueueScheduler):
    """Implements a static priority server
    """
    MIN_QUANTUM = 1500

    def __init__(
        self,
        env: Environment,
        rate: float,
        weights: Dict[FlowId, int],
        debug: bool = False,
    ):
        super().__init__(env, rate, debug)
        self.deficit: Dict[FlowId, float] = dict()
        self.quantum: Dict[FlowId, float] = dict()
        min_weight = min(weights.values())
        for flow_id, weight in weights.items():
            self.deficit[flow_id] = 0.0
            self.queue_count[flow_id] = 0
            self.quantum[flow_id] = self.MIN_QUANTUM * weight / min_weight
        self.head_of_line = dict()
        self.active_set = set()
        # self.proc = env.process(self.run(env))

    def run(self, env: Environment) -> ProcessGenerator:
        while True:
            while self.total_packets > 0:
                counts = self.queue_count.items()
                for flow_id, count in counts:
                    if count > 0:
                        self.deficit[flow_id] += self.quantum[flow_id]
                        self.dprint(
                            f"Flow queue length: {self.queue_count}, "
                            f"deficit counters: {self.deficit}")
                    while self.deficit[flow_id] > 0 and self.queue_count[flow_id] > 0:
                        if flow_id in self.head_of_line:
                            packet = self.head_of_line[flow_id]
                            del self.head_of_line[flow_id]
                        else:
                            store = self.stores[flow_id]
                            packet = yield store.get()

                        if packet.size <= self.deficit[flow_id]:
                            self.current_packet = packet
                        
                        assert flow_id == packet.flow_id

                        if packet.size <= self.deficit[flow_id]:
                            yield env.process(self.send_packet(packet))
                        else:
                            assert not flow_id in self.head_of_line
                            self.head_of_line[flow_id] = packet
                            break
                if self.total_packets == 0:
                    yield self.packets_available.get()
