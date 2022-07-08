import asyncio
import hashlib
import random
import socket
import abc
import logging
import os
import time
from copy import deepcopy

from ..protocol.packet import *
from .common import _parse_args
from ._recorder import Recorder


class TCPClientNode(abc.ABC):
    def __init__(self):
        self._debug = True
        self.host, self.port, self.server_host, self.server_port = _parse_args()
        self._buffer = b''
        self._chunk_size = 4096
        self._loop = asyncio.get_event_loop()
        self._sock = self._create_socket()
        self._id = self._generate_id()
        self._EOT_CHAR = 0x04.to_bytes(1, 'big')
        self._loss_rate = 0
        self._max_delay = 0
        self._recorder = Recorder(os.getcwd() + '/judge')
        self.enable_recording = False
        self._time_start = time.time()
        self._testcase = 0

    @property
    def max_delay(self):
        return self.max_delay

    @max_delay.setter
    def max_delay(self, value):
        self._max_delay = value

    @property
    def loss_rate(self):
        return self._loss_rate

    @loss_rate.setter
    def loss_rate(self, value):
        self._loss_rate = value

    @abc.abstractmethod
    async def setup(self):
        """Setup the client node

        This function should be overriden by derived class. The tasks which
        derived class add to this function might include:

        1. parse the lab config file
        2. create data structure required by expirement
        3. read in all the test cases
        """

    @abc.abstractmethod
    async def testcase_handler(self):
        """Return true if the justed finished test is the last one

        This function should be overriden by derived class. Derived class
        should implement the client node logic of the expirement in this
        function. This function might include the following parts:

        1. reset the data structure used by lab to prepare for this test case
        2. parse the test case, send packets and waiting for server's reponse and handle the packets received.
        3. return when all the packets have been sent and received

        To get intuitive impression, please check the example expirements composed
        using OpenNetLab.
        """

    @abc.abstractmethod
    async def teardown(self):
        """Tear down the client node

        This function should be overriden by derived class. teardown is
        executed when all the test cases have finished. Derived class can
        teardown its data structure in this function.
        """

    async def run(self):
        """Run the client node

        This is the entry function for the client node, which includes the following procedures:

        1. setup the expirement data
        2. try connecting to server
        3. call testcase_handler until all the test cases have been finished
        4. finish the expirement
        5. teardown the expirement data
        """
        await self.setup()
        connected = await self._connect()
        if self.enable_recording:
            self._recorder.open()
        if connected:
            finished = False
            while not finished:
                finished = await self.testcase_handler()
                await self._end_testcase()
                self._testcase += 1
                if finished:
                    self._recorder.close()
                else:
                    self._recorder.start_next_testcase()
                packet = None
                while True:
                    packet = await self.recv_next_packet()
                    if packet:
                        break
                    await asyncio.sleep(0.01)
                # assert packet.packet_type == PacketType.START_TESTCASE
            await self.finish()
        await self.teardown()

    async def send(self, data):
        """Send expirement data to server, the type of data can be any python
        basic data types
        """
        def is_loss():
            if self._loss_rate == 0:
                return False
            return random.random() < self._loss_rate
        if self.enable_recording:
            record = deepcopy(data)
            record['time'] = int((time.time() - self._time_start) * 1000)
            self._recorder.add_send_record(record)
        if is_loss():
            return
        data['testcase'] = self._testcase
        if self._max_delay != 0:
            self._loop.create_task(self._wait_send(data, random.randint(0, self._max_delay)))
        else:
            await self._loop.sock_sendall(self._sock, ONLPacket(PacketType.EXPIREMENT_DATA, data).to_bytes() + self._EOT_CHAR)

    async def _wait_send(self, data, delay):
        await asyncio.sleep(delay / 1000)
        await self._loop.sock_sendall(self._sock, ONLPacket(PacketType.EXPIREMENT_DATA, data).to_bytes() + self._EOT_CHAR)

    async def recv_next_packet(self):
        """Receive the next packet from server

        This function is a NON-BLOCKING function. If it receives a packet, then
        the packet is returned. Else None is returned.
        """
        chunk = b''
        try:
            # chunk = await self.loop.sock_recv(self.sock, self.chunk_size)
            chunk = self._sock.recv(self._chunk_size)
        except BlockingIOError as _:
            pass
        except Exception as e:
            self._debug_print('Error: ' + str(e))

        if chunk != b'':
            self._buffer += chunk
        eot_pos = self._buffer.find(self._EOT_CHAR)
        if eot_pos != -1:
            packet_bytes = self._buffer[:eot_pos]
            self._buffer = self._buffer[eot_pos+1:]
            packet = ONLPacket.from_bytes(packet_bytes)
            data = packet.payload
            if packet.packet_type == PacketType.EXPIREMENT_DATA and data['testcase'] != self._testcase:
                return None
            if self.enable_recording and packet.packet_type == PacketType.EXPIREMENT_DATA:
                del data['testcase']
                self._recorder.add_recv_record(data)
            return packet
        else:
            return None

    async def finish(self):
        """Finish the expirement

        Send a message to server to close the connection.
        """
        await self._loop.sock_sendall(self._sock, ONLPacket(PacketType.END_EXPERIMENT, '').to_bytes() + self._EOT_CHAR)

    def __str__(self):
        return 'Node %s (%s : %d)' % (self._id, self.host, self.port)

    def _create_socket(self):
        """Create socket and set some socket options.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        sock.bind((self.host, self.port))
        return sock

    async def _connect(self):
        """Connect to the server.

        Try 10 times, the interval between each connection is 2s. If all
        connection fails, then exit.
        """
        MAX_RETRY = 10
        ret = False
        for i in range(MAX_RETRY):
            try:
                await self._loop.sock_connect(self._sock, (self.server_host, self.server_port))
                ret = True
                break
            except Exception as _:
                self._debug_print("Error: time %d failed to connect to %s:%d" % (
                    i, self.server_host, self.server_port))
                await asyncio.sleep(2)
        if not ret:
            logging.error('Error: fail to connect to server')
        return ret

    async def _end_testcase(self):
        """Tell the server the current test case has been finished.

        When server receives the END_TESTCASE packet, it can evaluate the
        result. The server will send a START_TESTCASE packet to client if the
        evaluation process has been finished, which means the server is ready
        for handling the next testcase.
        """
        await self._loop.sock_sendall(self._sock, ONLPacket(PacketType.END_TESTCASE, '').to_bytes() + self._EOT_CHAR)

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
