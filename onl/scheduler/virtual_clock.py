from typing import Dict

from ..types import *
from ..sim import Environment, ProcessGenerator, PriorityStore, SimTime
from ..packet import Packet
from .base import Scheduler


class VC(Scheduler):
    """Implement a virtual clock scheduler"""

    def __init__(
        self,
        env: Environment,
        rate: float,
        vticks: Dict[FlowId, SimTime],
        debug: bool = False,
    ):
        super().__init__(env, rate, debug)
        self.vticks = vticks
        """Decides the clock increasing speed.
        Represents the virtual time increasement for each bit received.
        """
        self.vc: Dict[FlowId, SimTime] = dict()
        self.aux_vc: Dict[FlowId, SimTime] = dict()
        self.store = PriorityStore(env)
        for flow_id in vticks.keys():
            self.aux_vc[flow_id] = 0
            self.vc[flow_id] = 0
        self.proc = env.process(self.run(env))

    def run(self, env: Environment) -> ProcessGenerator:
        while True:
            packet: Packet = yield self.store.get()
            yield env.process(self.send_packet(packet))

    def put(self, packet: Packet):
        flow_id = packet.flow_id
        now = self.env.now
        # upon receiving the first packet from flow_i,
        # VirtualClock_i <- real time
        if self.vc[flow_id] == 0:
            self.vc[flow_id] = self.env.now
        # for each packet, update VC and auxVC
        self.aux_vc[flow_id] = max(now, self.aux_vc[flow_id])
        self.vc[flow_id] = (
            self.vc[flow_id] + self.vticks[flow_id] * packet.size * 8.0
        )
        self.aux_vc[flow_id] += self.vticks[flow_id]
        # TODO: add AR: average transmission rate
        # add AI: average interval to check
        self.add_packet_to_queue(packet)
        # transmite packets by the order of increasing stamp values
        # use aux_vc as stamp value
        self.store.put((self.aux_vc[flow_id], packet))
