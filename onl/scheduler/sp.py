from typing import Dict, Callable

from ..types import *
from ..sim import Environment, ProcessGenerator
from ..packet import Packet
from .base import MultiQueueScheduler


class SP(MultiQueueScheduler):
    """Implements a static priority server
    """
    def __init__(
        self,
        env: Environment,
        rate: float,
        priorities: Dict[FlowId, Priority],
        flow2class: Callable = lambda fid: fid,
        debug: bool = False,
    ):
        super().__init__(env, rate, flow2class, debug)
        self.priorities = sorted(priorities.items(), key=lambda item: item[1], reverse=True)
        self.proc = env.process(self.run(env))

    def run(self, env: Environment) -> ProcessGenerator:
        while True:
            for flow_id, prio in self.priorities:
                if prio > 0:
                    store = self.stores[flow_id]
                    if store.size() == 0:
                        continue
                    packet: Packet = yield store.get()
                    print(packet)
                    packet.priorities[self.flow2class(packet.flow_id)] = prio
                    yield env.process(self.send_packet(packet))
            if self.total_packets == 0:
                yield self.packets_available.get()
