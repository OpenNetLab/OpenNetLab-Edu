from typing import List
from ..types import *
from ..sim import Environment, ProcessGenerator
from ..packet import Packet
from .base import MultiQueueScheduler


class RR(MultiQueueScheduler):
    """Implements a round robin MultiQueueScheduler
    """
    def __init__(
        self,
        env: Environment,
        rate: float,
        flows: List[int],
        debug: bool = False,
    ):
        super().__init__(env, rate, debug)
        self.flows = flows
        self.proc = env.process(self.run(env))

    def run(self, env: Environment) -> ProcessGenerator:
        while True:
            for flow_id in self.flows:
                if self.queue_count[flow_id] > 0:
                    store = self.stores.get(flow_id)
                    assert store
                    packet: Packet = yield store.get()
                    yield env.process(self.send_packet(packet))
            if self.total_packets == 0:
                yield self.packets_available.get()
