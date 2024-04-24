from typing import List, Optional, Dict
from random import choices

from ..device import Device
from ..packet import Packet
from ..types import FlowId

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


class FIBDemux(Device):
    def __init__(
        self,
        outs: Optional[List[Device]] = None,
        ends: Optional[Dict[FlowId, Device]] = None,
        fib: Optional[Dict[int, int]] = None,
        default_out: Optional[Device] = None,
    ):
        # forwarding information base. Key: flow id, Value: output port
        self._fib = fib
        #  list of downstream elements corresponding to the output ports
        self.outs = outs
        self.default_out = default_out
        self.packets_recevied = 0
        if ends:
            self.ends = ends
        else:
            self.ends = dict()

    @property
    def fib(self):
        return self._fib

    @fib.setter
    def fib(self, val):
        self._fib = val

    def put(self, packet):
        if not self._fib:
            raise ValueError('fib of FIBDemux is None')
        self.packets_recevied += 1
        flow_id = packet.flow_id

        if flow_id in self.ends:
            self.ends[flow_id].put(packet)
        else:
            try:
                assert self.outs
                self.outs[self._fib[packet.flow_id]].put(packet)
            except (KeyError, IndexError, ValueError) as exc:
                print("FIB Demux Error: " + str(exc))
                if self.default_out:
                    self.default_out.put(packet)
