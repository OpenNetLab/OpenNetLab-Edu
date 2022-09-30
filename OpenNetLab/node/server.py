import asyncio
import socket
import struct
import os
import abc

from ..protocol.packet import *
from .common import _parse_args
from ._recorder import Recorder


class TCPServerNode(abc.ABC):
    def __init__(self):
        self._debug = True
        self.host, self.port, self.client_host, self.client_port = _parse_args()
        self.evaulate_here = False
        self._chunk_size = 4096
        self._loop = asyncio.get_event_loop()
        self._sock = self._create_socket()
        self._recorder = Recorder(os.getcwd() + '/judge')
        self._testcase = 0

    @property
    def recorder(self):
        return self._recorder

    @abc.abstractmethod
    async def setup(self):
        """Setup the server node

        This function should be overriden by derived class. The tasks which
        derived class add to this function might include:

        1. parse the lab config file
        2. create data structure required by expirement
        3. read in all the test cases
        """

    @abc.abstractmethod
    async def recv_callback(self, data):
        """Handling the received data.

        This function should be overriden by derived class. It is a callback
        function which is called when receiving packet containing the
        expirement data.

        The main logic of the designed expirement should be implemented in this
        function.
        """

    async def teardown(self):
        """
        This function is called when the running phase ends.
        """

    async def evaulate_testcase(self):
        """Evalate the test case.

        This function is called when the END_TESTCASE packet has been received.

        The following tasks should be incorporated in this function:

        1. Evaluate the result
        2. Reset the internal data structure
        """

    async def run(self):
        """Run the server node

        This is the entry function for the server node, which includes the
        following procedures:

        1. setup the expirement's data
        2. wait for client's connection
        3. enter the loop of receiving packet from client
            * if the packet is EXPIREMENT_DATA packet,
               then call recv_callback function
            * if the packet is END_TESTCASE packet, then
               call evaulate_testcase function
            * if the packet is END_NOTIFY packet, then
               break the loop.
        4. tear down the expirement data.
        """
        await self.setup()
        connected = await self._receive_client_connection()
        if connected:
            ending = False
            buffer = b''
            chunk = b''
            self._debug_print('waiting for message from client')
            while not ending:
                try:
                    chunk = await self._loop.sock_recv(self.conn, self._chunk_size)
                except socket.timeout as e:
                    print(f'ERROR: timeout before receiving any data: %s' % str(e))
                    break
                except Exception as e:
                    print('ERROR: ' + str(e))
                    break

                if chunk != b'':
                    buffer += chunk
                    if len(buffer) < 2:
                        continue
                    onlp_len = struct.unpack('!h', buffer[:2])[0]
                    end_pos = 2 + onlp_len
                    while end_pos <= len(buffer):
                        packet_bytes = buffer[2:end_pos]
                        buffer = buffer[end_pos:]
                        packet = ONLPacket.from_bytes(packet_bytes)
                        if packet.packet_type == PacketType.EXPIREMENT_DATA:
                            data = packet.payload
                            if packet.idx == self._testcase:
                                await self.recv_callback(data)
                            if len(buffer) < 2:
                                break
                            onlp_len = struct.unpack('!h', buffer[:2])[0]
                            end_pos = 2 + onlp_len
                        elif packet.packet_type == PacketType.END_TESTCASE:
                            if self.evaulate_here:
                                await self.evaulate_testcase()
                            print(f'TESTCASE {self._testcase} FINISHED')
                            self._testcase += 1
                            await self.send(None, PacketType.START_TESTCASE)
                            if len(buffer) < 2:
                                continue
                            onlp_len = struct.unpack('!h', buffer[:2])[0]
                            end_pos = 2 + onlp_len
                        elif packet.packet_type == PacketType.END_EXPERIMENT:
                            ending = True
                            break
                        else:
                            print('ERROR: unrecgonized packet type: %d' % packet.packet_type)
                            break
            await self.teardown()
        self._recorder.close()

    async def send(self, data, packet_type=PacketType.EXPIREMENT_DATA):
        """Send expirement data to client, the type of data can be any python
        basic data types
        """
        if self.conn:
            onl_bytes = ONLPacket(packet_type, data, self._testcase).to_bytes()
            onl_bytes = struct.pack('!h', len(onl_bytes)) + onl_bytes
            await self._loop.sock_sendall(self.conn,  onl_bytes)

    async def _receive_client_connection(self):
        """Receive the connection from client.

        After receiving the connection. Check if the client's address is valid.
        If not valid, then close the connection and wait for the expected
        client.

        If there is no connection in more than 15s, then exit
        """
        try:
            while True:
                conn, addr = await self._loop.sock_accept(self._sock)
                if addr[0] == self.client_host or addr[1] == self.client_port:
                    self._debug_print('recieve connection from %s:%d' % addr)
                    self.conn = conn
                    break
                else:
                    conn.close()
        except socket.timeout as _:
            print('ERROR: socket times out before receiving any viable connection')
            return False
        else:
            return True

    def _create_socket(self):
        """Create socket and set some socket options.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        sock.settimeout(15.0)
        sock.bind((self.host, self.port))
        sock.listen(1)
        return sock

    def _debug_print(self, msg):
        if self._debug:
            print(msg)
