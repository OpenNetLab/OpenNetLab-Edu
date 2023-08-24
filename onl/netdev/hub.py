from typing import Optional, List
from ..device import SingleDevice, Device
from ..packet import Packet
from ..sim import Environment


class Hub(Device):
    def __init__(
        self,
        env: Environment,
        endpoints: List[SingleDevice] = [],
        ports: List[Optional[SingleDevice]] = [],
    ):
        if ports and len(ports) != len(endpoints):
            raise ValueError("endpoints' length and ports' length are not equal")
        self.env = env
        self.ports = ports
        self.outs = []
        self.endpoints = []
        for idx, endpoint in enumerate(endpoints):
            self.add_endpoint(endpoint, ports[idx])

    def add_endpoint(self, endpoint: SingleDevice, port: Optional[SingleDevice]):
        endpoint.out = self
        if port:
            port.out = endpoint
            self.outs.append(port)
        else:
            self.outs.append(endpoint)
        self.endpoints.append(endpoint)

    def put(self, packet: Packet):
        for idx, endpoint in enumerate(self.endpoints):
            if endpoint.element_id == packet.src:
                continue
            out = self.outs[idx]
            out.put(packet)
