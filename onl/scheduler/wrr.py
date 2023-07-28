from typing import Dict
from ..types import *
from ..sim import Environment, ProcessGenerator
from ..packet import Packet
from .base import MultiQueueScheduler


class WRR(MultiQueueScheduler):
    """Implements a weighted round robin MultiQueueScheduler
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
        self.proc = env.process(self.run(env))

    def run(self, env: Environment) -> ProcessGenerator:
        while True:
            for flow_id, weight in self.weights.items():
                for _ in range(weight):
                    if self.queue_count[flow_id] > 0:
                        store = self.stores.get(flow_id)
                        assert store
                        packet: Packet = yield store.get()
                        yield env.process(self.send_packet(packet))
                    else:
                        break
            if self.total_packets == 0:
                yield self.packets_available.get()
