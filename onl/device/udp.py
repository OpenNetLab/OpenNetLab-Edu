import random
import socket
from typing import Optional
from abc import abstractmethod


class UDPDevice:
    BUFSIZE = 1024

    def __init__(
        self,
        address: str = "localhost",
        port: int = 0,
    ):
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.out: Optional[UDPDevice] = None
        self.address = address
        self.id = random.randint(0 ,100)
        self.recv_sock.bind(('', 0))
        _, self.recv_port = self.recv_sock.getsockname()

    def send(self, data: bytes):
        """Different usage from Device
        Send message to next hop
            If you're using Device:
                self.out.put(packet)
            If you're using UDPDevice:
                self.out = some UDPDevice
                self.send(data)
        """
        assert self.out
        next_hop = self.out
        # print(self.id, 'send to:', (next_hop.address, next_hop.recv_port))
        self.send_sock.sendto(data, (next_hop.address, next_hop.recv_port))
        next_hop._recv()

    def _recv(self):
        data = self.recv_sock.recv(self.BUFSIZE)
        self.recv_callback(data)

    @abstractmethod
    def recv_callback(self, data: bytes):
        pass
