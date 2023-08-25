from ..packet import Packet
from ..device import Device, OutMixIn
from ..sim import Environment, Store


class Port(Device, OutMixIn):
    """Implements a port with an output buffer, given an output rate and a buffer size (in either bytes
    or the number of packets). This implementation uses the simple tail-drop mechanism to drop packets.

    """

    def __init__(
        self,
        env: "Environment",
        rate: float,
        qlimit: int,
        limit_bytes: bool,
        element_id: str,
        debug: bool = False,
    ):
        self.env = env
        self.store = Store(env)
        self.rate = rate
        """The bit rate of the port"""
        self.qlimit = qlimit
        """A queue limit in bytes or packets (including the packet in service), beyond
        which all packets will be dropped."""
        self.limit_bytes = limit_bytes
        """If True, the queue limit will be based on bytes; if False, the queue limit
        will be based on packets."""
        self.element_id = element_id
        """Element Id of this port"""
        self.debug = debug
        self.byte_size = 0
        """Byte sum of all packets in buffer."""
        self.packets_received = 0
        """Total packets received."""
        self.packets_dropped = 0
        """Total packets dropped."""
        self.busy = 0
        self.busy_packet_size = 0
        self.action = env.process(self.run(env))

    def run(self, env: Environment):
        while True:
            packet = yield self.store.get()

            self.busy = 1
            self.busy_packet_size = packet.size

            if self.rate > 0:
                yield env.timeout(packet.size * 8 / self.rate)
                self.byte_size -= packet.size
            if self.out:
                self.out.put(packet)

            self.busy = 0
            self.busy_packet_size = 0

    def put(self, packet: Packet):
        self.packets_received += 1

        byte_count = self.byte_size + packet.size

        if not self.element_id:
            packet.perhop_time[self.element_id] = self.env.now

        if self.qlimit:
            self.byte_size = byte_count
            self.store.put(packet)
            return

        if (self.limit_bytes and byte_count > self.qlimit) or (
            not self.limit_bytes and len(self.store.items) >= self.qlimit - 1
        ):
            # if buffer in this port is not enough to hold the incoming packet, drop it.
            self.packets_dropped += 1
            if self.debug:
                print(
                    f"Packet dropped: flow id = {packet.flow_id} and packet id = {packet.packet_id}"
                )
        else:
            if self.debug:
                print(f"Queue length at port: {len(self.store.items)} packets.")
            self.byte_size = byte_count
            self.store.put(packet)
