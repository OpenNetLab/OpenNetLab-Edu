import asyncio
import hashlib
import random
import socket
import sys

from ..protocol.packet import *
from .common import _parse_args


def override(f):
    return f


class TCPServerNode:
    def __init__(self):
        self.debug = True
        self.host, self.port, self.client_host, self.client_port = _parse_args()
        self.chunk_size = 4096
        self.loop = asyncio.get_event_loop()
        self.sock = self._create_socket()
        self.EOT_CHAR = 0x04.to_bytes(1, 'big')
        self.id = self._generate_id()

    @override
    async def setup(self):
        pass

    @override
    async def teardown(self):
        pass

    @override
    async def recv_callback(self, data):
        pass

    async def run(self):
        await self.setup()
        await self._receive_client_connection()
        ending = False
        buffer = b''
        chunk = b''
        self._debug_print('waiting for message from client')
        while not ending:
            try:
                chunk = await self.loop.sock_recv(self.conn, self.chunk_size)
            except socket.timeout as e:
                self._debug_print(
                    'TIMEOUT before receiving any data: %s' % str(e))
                sys.exit(1)
            except Exception as e:
                self._debug_print('ERROR: ' + str(e))
                sys.exit(1)

            if chunk != b'':
                buffer += chunk
                eot_pos = buffer.find(self.EOT_CHAR)
                while eot_pos != -1:
                    packet_bytes = buffer[:eot_pos]
                    buffer = buffer[eot_pos+1:]
                    packet = ONLPacket.from_bytes(packet_bytes)
                    if packet.packet_type == ONLPacket.END_NOTIFY:
                        ending = True
                        break
                    elif packet.packet_type == ONLPacket.EXPIREMENT_DATA:
                        await self.recv_callback(packet.payload)
                        eot_pos = buffer.find(self.EOT_CHAR)
                    else:
                        break
        await self.teardown()

    async def send(self, data):
        if self.conn is not None:
            await self.loop.sock_sendall(self.conn, ONLPacket(ONLPacket.EXPIREMENT_DATA, data).to_bytes() + self.EOT_CHAR)

    async def _receive_client_connection(self):
        while True:
            conn, addr = await self.loop.sock_accept(self.sock)
            if addr[0] == self.client_host or addr[1] == self.client_port:
                self._debug_print('recieve connection from %s:%d' % addr)
                self.conn = conn
                break
            else:
                conn.close()

    def _create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        sock.settimeout(60.0)
        sock.bind((self.host, self.port))
        sock.listen(1)
        return sock

    def _generate_id(self):
        uid = hashlib.sha256()
        t = self.host + str(self.port) + str(random.randint(1, 99999999))
        uid.update(t.encode('ascii'))
        return uid.hexdigest()

    def _debug_print(self, msg):
        if self.debug:
            print(msg)
