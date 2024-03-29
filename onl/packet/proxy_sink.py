from collections import defaultdict as dd
import socket
from select import select
import time
import threading

from ..sim import Environment, Store
from ..device import SingleDevice
from ..packet import Packet


class ProxySink(SingleDevice):
    def __init__(
        self,
        env: Environment,
        element_id: str,
        destination,
        packet_size: int = 40960,
        protocol: str = "tcp",
        rec_arrivals: bool = False,
        absolute_arrivals: bool = False,
        rec_waits: bool = False,
        rec_flow_ids: bool = False,
        debug: bool = False,
    ):
        self.init_realtime = time.time()

        self.store = Store(env)
        self.env = env
        self.element_id = element_id
        self.destination = destination
        self.packet_size = packet_size
        self.protocol = protocol
        self.rec_arrivals = rec_arrivals
        self.absolute_arrivals = absolute_arrivals
        self.rec_waits = rec_waits
        self.rec_flow_ids = rec_flow_ids
        self.debug = debug

        self.waits = dd(list)
        self.arrivals = dd(list)
        self.packets_received = dd(lambda: 0)
        self.bytes_received = dd(lambda: 0)
        self.packet_sizes = dd(list)
        self.packet_times = dd(list)
        self.perhop_times = dd(list)

        self.first_arrival = dd(lambda: 0.0)
        self.last_arrival = dd(lambda: 0.0)

        # socket to flow_id
        self.flow_ids = {}
        # flow_id to socket
        self.sockets = {}

        self.last_response_time = 0
        self.last_response_realtime = 0
        self.responses_sent = 0

        self.udpserver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def on_tcp_accept(self, packet):
        """When a new client arrives at the proxy sink."""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            server_sock.connect(self.destination)
        except socket.timeout:
            print(f"Timed out connecting to server {self.destination}.")

        self.flow_ids[server_sock] = packet.flow_id
        self.sockets[packet.flow_id] = server_sock

    def on_tcp_close(self, sock):
        """Removes relevant states when a server disconnects."""
        print(f"{self.element_id}: {sock.getpeername()} has disconnected.")

        flow_id = self.flow_ids[sock]
        del self.flow_ids[sock]
        del self.sockets[flow_id]

        sock.close()

    def send_to_app(self, packet: Packet):
        """Sends a packet to the application-layer real-world server."""
        if self.protocol == "tcp":
            server_sock = self.sockets[packet.flow_id]
            server_sock.send(packet.payload)
        elif self.protocol == "udp":
            self.udpserver_sock.sendto(packet.payload, self.destination)
        else:
            raise ValueError("Protocol should be either 'tcp' or 'udp'.")

    def run(self, env: Environment):
        while True:
            inputs = [self.udpserver_sock] + list(self.flow_ids.keys())
            input_ready, _, _ = select(inputs, [], inputs, 0.01)

            for selected_sock in input_ready:
                data = selected_sock.recv(self.packet_size)

                if not data and self.protocol == "tcp":
                    self.on_tcp_close(selected_sock)
                else:
                    if self.debug:
                        if self.protocol == "tcp":
                            print(
                                f"{self.element_id} received response from "
                                f"{selected_sock.getpeername()}: {data}"
                            )
                        else:
                            print(
                                f"{self.element_id} received data from "
                                f"{self.destination}: {data}"
                            )

                    if self.last_response_time > 0:
                        current_realtime = time.time()
                        inter_arrival_time = env.now - self.last_response_time
                        inter_arrival_realtime = (
                            current_realtime - self.last_response_realtime
                        )
                        self.last_response_time = env.now
                        self.last_response_realtime = current_realtime

                        assert inter_arrival_realtime > inter_arrival_time

                        yield self.env.timeout(
                            inter_arrival_realtime - inter_arrival_time
                        )

                    self.responses_sent += 1

                    if self.protocol == "tcp":
                        packet = Packet(
                            env.now,
                            self.packet_size,
                            self.responses_sent,
                            realtime=time.time() - self.init_realtime,
                            flow_id=self.flow_ids[selected_sock],
                            payload=data,
                        )
                    else:
                        packet = Packet(
                            env.now,
                            self.packet_size,
                            self.responses_sent,
                            realtime=time.time() - self.init_realtime,
                            payload=data,
                        )

                    if self.debug:
                        print(
                            f"{self.element_id} sent packet {packet.packet_id} "
                            f"with flow_id {packet.flow_id} at time {self.env.now}."
                        )

                    assert self.out
                    self.out.put(packet)

                if not input_ready:
                    yield env.timeout(time.time() - self.init_realtime - self.env.now)

    def put(self, packet: Packet):
        # If the packet is closing a flow
        if packet.size == 0 and not packet.payload and self.protocol == "tcp":
            if packet.flow_id in self.sockets:
                sock = self.sockets[packet.flow_id]
                del self.flow_ids[sock]
                del self.sockets[packet.flow_id]
        else:
            now = self.env.now

            if packet.flow_id not in self.flow_ids.values():
                if self.protocol == "tcp":
                    # new client arrived, establishing a new connection to the server
                    self.on_tcp_accept(packet)

            packet_delay = now - packet.time
            packet_delay_realtime = time.time() - self.init_realtime - packet.realtime

            if packet_delay > packet_delay_realtime:
                delayed_action = threading.Timer(
                    packet_delay - packet_delay_realtime,
                    self.send_to_app,
                    args=[packet],
                )
                delayed_action.start()
            else:
                self.send_to_app(packet)

            if self.rec_flow_ids:
                rec_index = packet.flow_id
            else:
                rec_index = packet.src

            if self.rec_waits:
                self.waits[rec_index].append(packet_delay)
                self.packet_sizes[rec_index].append(packet.size)
                self.packet_times[rec_index].append(packet.time)
                self.perhop_times[rec_index].append(packet.perhop_time)

            if self.rec_arrivals:
                self.arrivals[rec_index].append(now)
                if len(self.arrivals[rec_index]) == 1:
                    self.first_arrival[rec_index] = now

                if not self.absolute_arrivals:
                    self.arrivals[rec_index][-1] = now - self.last_arrival[rec_index]

                self.last_arrival[rec_index] = now

            if self.debug:
                print(
                    "At time {:.2f}, packet {:d} arrived at {}.".format(
                        now, packet.packet_id, self.element_id
                    )
                )
                if self.rec_waits and len(self.packet_sizes[rec_index]) >= 10:
                    bytes_received = sum(self.packet_sizes[rec_index][-9:])
                    time_elapsed = self.env.now - (
                        self.packet_times[rec_index][-10] + self.waits[rec_index][-10]
                    )
                    if time_elapsed > 0:
                        print(
                            "Average throughput (last 10 packets): {:.2f} bytes/second.".format(
                                bytes_received / time_elapsed
                            )
                        )

            self.packets_received[rec_index] += 1
            self.bytes_received[rec_index] += packet.size
