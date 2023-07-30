from copy import copy
from typing import Optional, List
from ..device import Device
from ..packet import Packet


class Splitter(Device):
    def __init__(self):
        self.out1: Optional[Device] = None
        self.out2: Optional[Device] = None

    def put(self, packet: Packet):
        if self.out1:
            self.out1.put(packet)
        if self.out2:
            self.out2.put(copy(packet))

    def run(self, env):
        raise RuntimeError("splitter should not execute run()")


class NSplitter(Device):
    def __init__(self, N: int):
        if isinstance(N, int):
            if N <= 1:
                raise ValueError("N should be larger than 1")
            self.outs: List[Optional[Device]] = [None] * N
        else:
            raise TypeError("N should be an interger larger than 1")

    def put(self, packet: Packet):
        if self.outs[0]:
            self.outs[0].put(packet)
        for out in self.outs[1:]:
            if out:
                out.put(copy(packet))

    def run(self, env):
        raise RuntimeError("splitter should not execute run()")
