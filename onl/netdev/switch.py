from ..device import Device
from .port import Port
from .demux import FIBDemux, FlowDemux
from ..scheduler import *


class SimplePacketSwitch(Device):
    """Implements a packet switch with a FIFO bounded buffer on each of the
    outgoing port.
    """

    def __init__(
        self,
        env,
        nports: int,
        port_rate: float,
        buffer_size: int,
        element_id: str = "",
        debug: bool = False,
    ):
        self.env = env
        self.ports = []
        for port in range(nports):
            self.ports.append(
                Port(env, port_rate, buffer_size, False, f"{element_id}.{port}", debug)
            )
        self.demux = FlowDemux(self.ports, None)

    def put(self, packet):
        self.demux.put(packet)


class FairPacketSwitch(Device):
    """Implements a fair packet switch with a choice of different kinds of
    schedulers.
    """

    def __init__(
        self,
        env,
        nports: int,
        port_rate: float,
        buffer_size: int,
        weights: dict,
        server: str,
        element_id: str = "",
        debug: bool = False,
    ):
        self.env = env
        self.ports = []
        self.egress_ports = []

        for port in range(nports):
            egress_port = Port(
                env,
                rate=0,
                qlimit=buffer_size,
                limit_bytes=False,
                element_id=f"{element_id}_{port}",
                debug=debug,
            )

            scheduler = None
            if server == "SP":
                scheduler = SP(env, rate=port_rate, priorities=weights, debug=debug)
            elif server == "VirtualClock":
                scheduler = VC(env, rate=port_rate, vticks=weights, debug=debug)
            elif server == "WFQ":
                scheduler = WFQ(env, rate=port_rate, weights=weights, debug=debug)
            elif server == "DRR":
                scheduler = DRR(env, rate=port_rate, weights=weights, debug=debug)
            else:
                raise ValueError(
                    "Scheduler type must be 'WFQ', 'DRR', 'SP', or 'VirtualClock'."
                )

            egress_port.out = scheduler
            self.egress_ports.append(egress_port)
            self.ports.append(scheduler)

        self.demux = FIBDemux(fib=None, outs=self.egress_ports, default_out=None)

    def put(self, packet):
        self.demux.put(packet)
