import asyncio
import hashlib
import random
import socket
import os
import abc
import logging

from ..protocol.packet import *
from .common import _parse_args
from ..utils.recorder import Recorder


class TCPServerNode(abc.ABC):
    def __init__(self):
        self._debug = True
        self.host, self.port, self.client_host, self.client_port = _parse_args()
        self._chunk_size = 4096
        self._loop = asyncio.get_event_loop()
        self._sock = self._create_socket()
        self._EOT_CHAR = 0x04.to_bytes(1, 'big')
        self._id = self._generate_id()
        self._recorder = Recorder(os.getcwd() + '/results')

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
    async def teardown(self):
        """Tear down the client node

        This function should be overriden by derived class. teardown is
        executed when all the test cases have finished. Derived class can
        teardown its data structure in this function.
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

    @abc.abstractmethod
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
                    logging.error(f'TIMEOUT before receiving any data: %s' % str(e))
                    break
                except Exception as e:
                    logging.error('ERROR: ' + str(e))
                    break

                if chunk != b'':
                    buffer += chunk
                    eot_pos = buffer.find(self._EOT_CHAR)
                    while eot_pos != -1:
                        packet_bytes = buffer[:eot_pos]
                        buffer = buffer[eot_pos+1:]
                        packet = ONLPacket.from_bytes(packet_bytes)
                        if packet.packet_type == PacketType.END_EXPERIMENT:
                            ending = True
                            break
                        elif packet.packet_type == PacketType.EXPIREMENT_DATA:
                            await self.recv_callback(packet.payload)
                            eot_pos = buffer.find(self._EOT_CHAR)
                        elif packet.packet_type == PacketType.END_TESTCASE:
                            await self.evaulate_testcase()
                            await self.send('', PacketType.START_TESTCASE)
                            eot_pos = buffer.find(self._EOT_CHAR)
                        else:
                            logging.error('Erorr: unrecgonized packet type: %d' % packet.packet_type)
                            break
        self.recorder.close()
        await self.teardown()

    async def send(self, data, packet_type=PacketType.EXPIREMENT_DATA):
        """Send expirement data to client, the type of data can be any python
        basic data types
        """
        if self.conn is not None:
            await self._loop.sock_sendall(self.conn, ONLPacket(packet_type, data).to_bytes() + self._EOT_CHAR)

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
            logging.error('Error: socket times out before receiving any viable connection')
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

    def _generate_id(self):
        """Generate the unique node ID.
        """
        uid = hashlib.sha256()
        t = self.host + str(self.port) + str(random.randint(1, 99999999))
        uid.update(t.encode('ascii'))
        return uid.hexdigest()

    def _debug_print(self, msg):
        if self._debug:
            print(msg)
