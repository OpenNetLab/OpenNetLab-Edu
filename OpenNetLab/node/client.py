import asyncio
import hashlib
import random
import socket

from OpenNetLab.protocol.packet import *

class TCPClientNode:
    def __init__(self, host, port, server_host, server_port) -> None:
        self.debug = True
        self.host = host
        self.port = port
        self.server_host = server_host
        self.server_port = server_port
        self.id = self.generate_id()
        self.EOT_CHAR = 0x04.to_bytes(1, 'big')
        self.loop = asyncio.get_event_loop()
        self.has_connect = False

    async def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind to allocated address
        self.sock.bind((self.host, self.port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        # connect to peer socket
        try:
            await self.loop.sock_connect(self.sock, (self.server_host, self.server_port))
            self.debug_print('connect to peer node %s:%d' %
                             (self.server_host, self.server_port))
        except socket.error as e:
            self.debug_print('fail to conenct to %s on port %s: %s' % (
                self.server_host, self.server_port, str(e)))
        else:
            self.has_connect = True

    async def run(self):
        pass

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

    async def send(self, data):
        await self.loop.sock_sendall(self.sock, ONLPacket(ONLPacket.EXPIREMENT_DATA, data).to_bytes() + self.EOT_CHAR)

    async def finish(self):
        await self.loop.sock_sendall(self.sock, ONLPacket(ONLPacket.END_NOTIFY, '').to_bytes() + self.EOT_CHAR)
