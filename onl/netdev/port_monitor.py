from typing import Callable
from ..sim import Environment
from .port import Port


class PortMonitor:
    def __init__(
        self,
        env: Environment,
        port: Port,
        dist: Callable[[], float],
        pkt_in_service_included=False,
    ):
        self.env = env
        self.port = port
        self.dist = dist
        self._sizes = []
        self._sizes_byte = []
        self.pkt_in_service_included = pkt_in_service_included

    @property
    def sizes(self):
        """Returns buffered packet count in port over time.
        """
        return self._sizes

    @property
    def sizes_byte(self):
        """Returns buffered packet byte size sum in port over time.
        """
        return self._sizes_byte

    def run(self):
        while True:
            yield self.env.timeout(self.dist())

            if self.pkt_in_service_included:
                total_byte = self.port.byte_size + self.port.busy_packet_size
                total = len(self.port.store.items) + self.port.busy
            else:
                total_byte = self.port.byte_size
                total = len(self.port.store.items)

            self._sizes.append(total)
            self._sizes_byte.append(total_byte)
