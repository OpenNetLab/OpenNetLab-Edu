import hashlib
import random
import socket
import time

from OpenNetLab.protocol.packet import *

class TCPServerNode:
    def __init__(self, host, port, client_host, client_port) -> None:
        self.debug = True
        self.host = host
        self.port = port
        self.id = self.generate_id()
        # receiving chunk sizee
        self.chunk_size = 4096
        # end of each transmission
        self.EOT_CHAR = 0x04.to_bytes(1, 'big')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind socket to listen
        self.sock.bind((self.host, self.port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # socket options
        self.sock.setblocking(False)
        self.sock.settimeout(10.0)
        # if socket type is TCP, wait for peer node's connection
        self.debug_print('listen for connections')

        self.client_host = client_host
        self.client_port = client_port
        self.sock.listen(1)
        self.receive_client_connection()

    def receive_client_connection(self):
        while True:
            conn, addr = self.sock.accept()
            if addr[0] == self.client_host or addr[1] == self.client_port:
                self.debug_print('recieve connection from %s:%d' % addr)
                self.conn = conn
                break
            else:
                conn.close()

    def generate_id(self):
        uid = hashlib.sha256()
        t = self.host + str(self.port) + str(random.randint(1, 99999999))
        uid.update(t.encode('ascii'))
        return uid.hexdigest()

    def debug_print(self, msg):
        if self.debug:
            print(msg)

    def run(self):
        ending = False
        buffer = b''
        chunk = b''
        self.debug_print('waiting for message from client')
        while not ending:
            try:
                chunk = self.conn.recv(self.chunk_size)
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
                    if packet.packet_type == ONLPacket.END_NOTIFY:
                        ending = True
                        break
                    elif packet.packet_type == ONLPacket.EXPIREMENT_DATA:
                        self.recv_callback(packet.payload)
                        eot_pos = buffer.find(self.EOT_CHAR)
                    else:
                        break
            time.sleep(0.01)

    def send(self, data):
        if self.conn is not None:
            self.conn.sendall(ONLPacket(ONLPacket.EXPIREMENT_DATA, data).to_bytes())

    def recv_callback(self, data):
        pass