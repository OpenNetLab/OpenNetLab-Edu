from typing import List, Optional
from random import choices

from ..device import Device
from ..packet import Packet


class FlowDemux(Device):
    def __init__(self, outs: List[Device], default_out: Optional[Device] = None):
        self.outs = outs
        self.default_out = default_out
        self.packets_recevied = 0

    def put(self, packet: Packet):
        self.packets_recevied += 1
        flow_id = packet.flow_id
        if flow_id < len(self.outs):
            self.outs[flow_id].put(packet)
        else:
            if self.default_out:
                self.default_out.put(packet)


class RandomDemux:
    def __init__(self, outs: List[Device], probs: List[float]):
        self.outs = outs
        self.probs = probs
        self.packets_recevied = 0

    def put(self, packet: Packet):
        self.packets_recevied += 1
        choices(self.outs, weights=self.probs)[0].put(packet)
