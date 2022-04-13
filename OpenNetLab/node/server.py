import hashlib
import random
from enum import Enum, auto
import socket
import time

from ..protocol.packet import *

class SocketType(Enum):
    UDP = auto()
    TCP = auto()

class ServerNode:
    def __init__(self, host, port, peer_host, peer_port, sock_type) -> None:
        self.debug = True
        self.host = host
        self.port = port
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.id = self.generate_id()
        # receiving chunk sizee
        self.chunk_size = 4096
        # end of each transmission
        self.EOT_CHAR = 0x04.to_bytes(1, 'big')
        if sock_type == SocketType.UDP:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bind socket to listen
        self.sock.bind((self.host, self.port))
        # socket options
        self.sock.setblocking(False)
        self.sock.settimeout(10.0)
        # if socket type is TCP, wait for peer node's connection
        if sock_type == SocketType.TCP:
            self.debug_print('listen for connections')
            self.sock.listen(1)
            while True:
                self.conn, peer_addr = self.sock.accept()
                if peer_addr[0] != peer_host and peer_addr[1] != peer_port:
                    continue
                self.debug_print('accept connection from peer node')
                break
        
        self.debug_print('%s is created' % str(self))

    def generate_id(self):
        uid = hashlib.sha256()
        t = self.host + str(self.port) + str(random.randint(1, 99999999))
        uid.update(t.encode('ascii'))
        return uid.hexdigest()

    def debug_print(self, msg):
        if self.debug:
            print(msg)

    def receive_process(self):
        ending = False
        buffer = b''
        chunk = b''
        while not ending:
            try:
                chunk = self.sock.recv(self.chunk_size)
            except socket.timeout:
                self.debug_print('node_connection: timeout')
            except Exception as e:
                self.debug_print('unexpected error: ' + str(e))

            if chunk != b'':
                buffer += chunk
                eot_pos = buffer.find(self.EOT_CHAR)
                while eot_pos != -1:
                    packet_bytes = buffer[:eot_pos]
                    buffer = buffer[eot_pos+1:]
                    packet = ONLPacket.from_bytes(packet_bytes)
                    if packet.packet_type == END_NOTIFY:
                        ending = True
                        break
                    elif packet.packet_type == EXPIREMENT_DATA:
                        self.recv_callback(packet.payload)
                        eot_pos = buffer.find(self.EOT_CHAR)
                    else:
                        break
            time.sleep(0.01)

    def send(self, data):
        if self.conn is not None:
            self.conn.sendall(ONLPacket(EXPIREMENT_DATA, data).to_bytes())

    def recv_callback(self, data):
        pass
