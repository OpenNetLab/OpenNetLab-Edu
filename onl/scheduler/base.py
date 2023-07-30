import uuid
from collections import defaultdict as dd
from typing import DefaultDict, List

from ..sim.events import ProcessGenerator
from ..types import *
from ..sim import Environment, Store
from ..packet import Packet
from ..device import Device, OutMixIn


class Scheduler(Device, OutMixIn):
    """Implements a generic Scheduler"""

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
        self.queue_byte_size: DefaultDict[FlowId, int] = dd(lambda: 0)
        self.queue_count: DefaultDict[FlowId, int] = dd(lambda: 0)

        self.current_packet = None
        self.packets_received = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}-{str(self.element_id)[:4]}"

    def dprint(self, s: str):
        if self.debug:
            print(f"At time {self.env.now}: {self} ", end="")
            print(s)

    def all_flows(self) -> List[FlowId]:
        """Returns all flow ids in current scheduler"""
        return list(self.queue_count.keys())

    def byte_size(self, flow_id: FlowId) -> int:
        """Returns the byte size sum of the queue for a paticular flow_id"""
        return self.queue_byte_size[flow_id]

    def size(self, flow_id: FlowId) -> int:
        """Returns the size of the queue for a paticular flow_id"""
        return self.queue_count[flow_id]

    @property
    def packet_in_service(self):
        return self.current_packet

    @property
    def total_packets(self) -> int:
        """Return packets count of all subqueues."""
        return sum(self.queue_count.values())

    def send_packet(self, packet: Packet):
        """Remove a packet from subqueue and send it to next hop.
        Usage:
            yield env.process(self.send_packet(packet))
        """
        self.current_packet = packet
        yield self.env.timeout(packet.size * 8.0 / self.rate)
        flow_id = packet.flow_id
        self.queue_count[flow_id] -= 1
        self.queue_byte_size[flow_id] -= packet.size
        if self.out:
            self.dprint(
                f"sent out packet {packet.packet_id} from flow {packet.flow_id} "
            )
            self.out.put(packet)
        self.current_packet = None

    def add_packet_to_queue(self, packet: Packet):
        """Add packet to subqueue according to its packet ID.
        Update queue variables related to the queue information.
        """
        flow_id = packet.flow_id
        self.packets_received += 1
        self.queue_count[flow_id] += 1
        self.queue_byte_size[flow_id] += packet.size

    def run(self, env: Environment) -> ProcessGenerator:
        raise NotImplementedError("run(env) is not implemented in Scheduler class")

    def put(self, pakcet: Packet):
        raise NotImplementedError("put(packet) is not implemented in Scheduler class")


class MultiQueueScheduler(Scheduler):
    """Implements a generic MultiQueueScheduler
    This scheduler has multiple subqueues, and when `put()` is called. The
    packet is added to corresponding subqueue based on its flow id.
    """

    def __init__(
        self,
        env: Environment,
        rate: float,
        debug: bool = False,
    ):
        super().__init__(env, rate, debug)
        self.stores: DefaultDict[FlowId, Store] = dd(lambda: Store(env))
        """Packets with the same flow_id is stored in the same subqueue.
        Each Store is regarded as a subqueue.
        """
        self.packets_available = Store(env)
        """Use this as a channel to tell if any packet is available in any store
        Usage:
            if self.total_packets == 0:
                yield self.packets_available.get()
        """

    def run(self, env: Environment) -> ProcessGenerator:
        raise NotImplementedError(
            "run(env) is not implemented in MultiQueueScheduler class"
        )

    def put(self, packet: Packet):
        flow_id = packet.flow_id
        if self.total_packets == 0:
            self.packets_available.put(True)
        self.add_packet_to_queue(packet)
        self.dprint(f"received packet {packet.packet_id} from flow {flow_id}".format())
        self.stores[flow_id].put(packet)
