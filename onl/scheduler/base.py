import uuid
from collections import defaultdict as dd
from typing import DefaultDict
from ..types import *
from ..sim import Environment, Store
from ..packet import Packet
from ..device import Device


class Scheduler(Device):
    """Implements a generic scheduler
    """
    def __init__(
        self,
        env: Environment,
        rate: float,
        debug: bool = False,
    ):
        self.env = env
        self.rate = rate
        self.debug = debug

        self.element_id = uuid.uuid4()
        self.stores: DefaultDict[FlowId, Store] = dd(lambda: Store(env))
        self.queue_byte_size: DefaultDict[FlowId, int] = dd(lambda: 0)
        self.queue_count: DefaultDict[FlowId, int] = dd(lambda: 0)

        self.current_packet = None
        self.packets_received = 0
        self.packets_available = Store(env)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}-{str(self.element_id)[:4]}"

    def dprint(self, s: str):
        if self.debug:
            print(f"At time {self.env.now}: {self} ", end="")
            print(s)

    @property
    def total_packets(self):
        return sum(self.queue_count.values())

    def send_packet(self, packet: Packet):
        flow_id = packet.flow_id
        self.current_packet = packet

        yield self.env.timeout(packet.size * 8.0 / self.rate)

        self.queue_count[flow_id] -= 1
        self.queue_byte_size[flow_id] -= packet.size
        if self.out:
            self.dprint(
                f"sent out packet {packet.packet_id} from flow {packet.flow_id}"
                f" of priority {packet.priorities[self.element_id]}"
            )
            self.out.put(packet)
        self.current_packet = None


    def put(self, packet: Packet):
        flow_id = packet.flow_id
        self.packets_received += 1
        if self.total_packets == 0:
            self.packets_available.put(True)
        self.queue_byte_size[flow_id] += packet.size
        self.queue_count[flow_id] += 1
        self.dprint(f"received packet {packet.packet_id} from flow {flow_id}".format())
        self.stores[flow_id].put(packet)
