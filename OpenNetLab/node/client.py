import hashlib
import random
from enum import Enum
import socket

from ..protocol.packet import *

class SocketType(Enum):
    UDP = 0
    TCP = 1

class ClientNode:
    def __init__(self, host, port, peer_host, peer_port, sock_type) -> None:
        self.debug = True
        self.host = host
        self.port = port
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.id = self.generate_id()
        self.EOT_CHAR = 0x04.to_bytes(1, 'big')
        if sock_type == SocketType.UDP:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind to allocated address
        self.sock.bind((self.host, self.port))
        # connect to peer socket
        try:
            self.sock.connect((peer_host, peer_port))
            self.debug_print('connect to peer node')
        except socket.error as e:
            self.debug_print('fail to conenct to %s on port %s: %s' % (peer_host, peer_port, str(e)))

        self.debug_print('Clinet {} is created'.format(self))

    def __str__(self):
        return 'Node %s (%s : %d)' % (self.id, self.host, self.port)

    def generate_id(self):
        uid = hashlib.sha256()
        t = self.host + str(self.port) + str(random.randint(1, 99999999))
        uid.update(t.encode('ascii'))
        return uid.hexdigest()

    def debug_print(self, msg):
        if self.debug:
            print(msg)

    def send(self, data):
        self.sock.sendall(ONLPacket(EXPIREMENT_DATA, data).to_bytes() + self.EOT_CHAR)

    def finish(self):
        self.sock.sendall(ONLPacket(END_NOTIFY, '').to_bytes() + self.EOT_CHAR)

    def testcase_handler(self, filename):
        pass
