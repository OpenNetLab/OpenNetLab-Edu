import asyncio
import hashlib
import random
import socket
import sys

from OpenNetLab.protocol.packet import *


def override(f):
    return f


class TCPClientNode:
    def __init__(self, host, port, server_host, server_port) -> None:
        self.debug = True
        self.host = host
        self.port = port
        self.server_host = server_host
        self.server_port = server_port
        self.buffer = b''
        self.chunk_size = 4096
        self.id = self._generate_id()
        self.EOT_CHAR = 0x04.to_bytes(1, 'big')
        self.loop = asyncio.get_event_loop()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        # bind to allocated address
        self.sock.bind((self.host, self.port))

    async def connect(self):
        MAX_RETRY = 10
        ret = False
        for i in range(MAX_RETRY):
            try:
                await self.loop.sock_connect(self.sock, (self.server_host, self.server_port))
                ret = True
                break
            except Exception as exc:
                self._debug_print("Error: time %d failed to connect to %s:%d" % (i, self.server_host, self.server_port))
                await asyncio.sleep(2)
        if not ret:
            sys.exit(1)

    async def run(self):
        await self.setup()
        await self.connect()
        await self.process()
        await self.teardown()
        pass

    @override
    async def setup(self):
        pass

    @override
    async def process(self):
        pass

    @override
    async def teardown(self):
        pass

    async def send(self, data):
        await self.loop.sock_sendall(self.sock, ONLPacket(ONLPacket.EXPIREMENT_DATA, data).to_bytes() + self.EOT_CHAR)

    async def recv_next_packet(self):
        chunk = b''
        try:
            # chunk = await self.loop.sock_recv(self.sock, self.chunk_size)
            chunk = self.sock.recv(self.chunk_size)
        except BlockingIOError as _:
            pass
        except Exception as e:
            self._debug_print('Error: ' + str(e))

        if chunk != b'':
            self.buffer += chunk
        eot_pos = self.buffer.find(self.EOT_CHAR)
        if eot_pos != -1:
            packet_bytes = self.buffer[:eot_pos]
            self.buffer = self.buffer[eot_pos+1:]
            return ONLPacket.from_bytes(packet_bytes).payload
        else:
            return None

    async def finish(self):
        await self.loop.sock_sendall(self.sock, ONLPacket(ONLPacket.END_NOTIFY, '').to_bytes() + self.EOT_CHAR)

    def __str__(self):
        return 'Node %s (%s : %d)' % (self.id, self.host, self.port)

    def _generate_id(self):
        uid = hashlib.sha256()
        t = self.host + str(self.port) + str(random.randint(1, 99999999))
        uid.update(t.encode('ascii'))
        return uid.hexdigest()

    def _debug_print(self, msg):
        if self.debug:
            print(msg)
