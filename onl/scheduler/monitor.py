from typing import Callable
from collections import defaultdict as dd

from .base import Scheduler
from ..sim import Environment, ProcessGenerator


class Monitor:
    def __init__(
        self,
        env: Environment,
        scheduler: Scheduler,
        dist: Callable[[], float],
        service_included: bool = False,
    ):
        self.env = env
        self.scheduler = scheduler
        self.dist = dist
        self.service_included = service_included
        self.sizes = dd(list)
        self.byte_sizes = dd(list)
        self.action = env.process(self.run(env))

    def run(self, env: Environment) -> ProcessGenerator:
        while True:
            yield env.timeout(self.dist())
            for flow_id in self.scheduler.all_flows():
                total = self.scheduler.size(flow_id)
                total_bytes = self.scheduler.byte_size(flow_id)

                if self.service_included:
                    service_pkt = self.scheduler.packet_in_service
                    if service_pkt and service_pkt.flow_id == flow_id:
                        total += 1
                        total_bytes += service_pkt.size

                self.sizes[flow_id].append(total)
                self.byte_sizes[flow_id].append(total_bytes)
