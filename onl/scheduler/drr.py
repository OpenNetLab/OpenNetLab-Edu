from typing import Dict, Callable

from ..types import *
from ..sim import Environment, ProcessGenerator
from ..packet import Packet
from .base import MultiQueueScheduler


class DRR(MultiQueueScheduler):
    """Implements a deficit round robin (DRR) scheduler.
    """
    MIN_QUANTUM = 1500

    def __init__(
        self,
        env: Environment,
        rate: float,
        weights: Dict[FlowId, int],
        flow2class: Callable = lambda fid: fid,
        debug: bool = False,
    ):
        super().__init__(env, rate, flow2class, debug)
        self.deficit: Dict[FlowId, float] = dict()
        self.quantum: Dict[FlowId, float] = dict()
        min_weight = min(weights.values())
        for class_id, weight in weights.items():
            self.deficit[class_id] = 0.0
            self.queue_count[class_id] = 0
            self.quantum[class_id] = self.MIN_QUANTUM * weight / min_weight
        self.head_of_line = dict()
        self.active_set = set()
        self.flow2class = flow2class
        self.proc = env.process(self.run(env))

    def run(self, env: Environment) -> ProcessGenerator:
        while True:
            while self.total_packets > 0:
                counts = self.queue_count.items()
                for class_id, count in counts:
                    if count > 0:
                        self.deficit[class_id] += self.quantum[class_id]
                        self.dprint(
                            f"Flow queue length: {self.queue_count[class_id]}, "
                            f"deficit counters: {self.deficit}")
                    while self.deficit[class_id] > 0 and self.queue_count[class_id] > 0:
                        if class_id in self.head_of_line:
                            packet = self.head_of_line[class_id]
                            del self.head_of_line[class_id]
                        else:
                            store = self.stores[class_id]
                            packet = yield store.get()

                        if packet.size <= self.deficit[class_id]:
                            self.current_packet = packet
                        
                        assert class_id == self.flow2class(packet.flow_id)

                        if packet.size <= self.deficit[class_id]:
                            yield env.process(self.send_packet(packet))
                            self.deficit[class_id] -= packet.size
                            if self.queue_count[class_id] == 0:
                                self.deficit[class_id] = 0.0
                            self.dprint(f"Deficit reduced to {self.deficit[class_id]} for {class_id}")
                        else:
                            assert not class_id in self.head_of_line
                            self.head_of_line[class_id] = packet
                            break
            if self.total_packets == 0:
                yield self.packets_available.get()
