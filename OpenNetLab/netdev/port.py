from ..packet import Packet
from ..device import Device
from ..sim import Environment, Store


class Port(Device):
    """Implements a port with an output buffer, given an output rate and a buffer size (in either bytes
    or the number of packets). This implementation uses the simple tail-drop mechanism to drop packets.

    """

    def __init__(
        self,
        env: 'Environment',
        rate: float,
        qlimit: int,
        limit_bytes: bool,
        element_id: int,
        debug: bool = False
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
        self._byte_size = 0
        self._packets_received = 0
        self._packets_dropped = 0
        self.busy = 0
        self.action = env.process(self.run(env))

        @property
        def byte_size(self):
            """Byte size in port's buffer"""
            return self._byte_size

        @property
        def packets_received(self):
            """Received packets count"""
            return self._packets_received

        @property
        def packets_dropped(self):
            """Dropped packets count"""
            return self._packets_dropped

        def run(self, env: Environment):
            while True:
                packet = yield self.store.get()
                if self.rate > 0:
                    yield env.timeout(packet.size * 8 / self.rate)
                    self._byte_size -= packet.size

                self.out.put(packet)

        def put(self, packet: Packet):
            self.packets_received += 1

            byte_count = self.byte_size + packet.size

            if not self.element_id:
                packet.perhop_time[self.element_id] = self.env.now

            if self.qlimit:
                self.byte_size = byte_count
                self.store.put(packet)
                return

            if (self.limit_bytes and byte_count > self.qlimit) or (not self.limit_bytes and len(self.store.items) >= self.qlimit - 1):
                # if buffer in this port is not enough to hold the incoming packet, drop it.
                self.packets_dropped += 1
                if self.debug:
                    print(
                        f"Packet dropped: flow id = {packet.flow_id} and packet id = {packet.packet_id}")
            else:
                if self.debug:
                    print(
                        f"Queue length at port: {len(self.store.items)} packets.")
                self.byte_size = byte_count
                self.store.put(packet)
