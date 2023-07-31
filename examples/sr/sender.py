import json
from typing import Deque
from pathlib import Path
from dataclasses import dataclass
from collections import deque
from onl.packet import Packet
from onl.device import Device, OutMixIn
from onl.sim import Environment, Store, Event
from onl.utils import Timer


@dataclass
class QueueItem:
    packet: Packet
    ack_received: bool = False


class SRSender(Device, OutMixIn):
    def __init__(self, env: Environment, message: str, debug: bool = False):
        cfgpath = Path(__file__).parent.joinpath("lab_config.json")
        with cfgpath.open() as fp:
            cfg = json.load(fp)
            # the bits of the sequence number, which decides the sequence
            # number range and window size of selective repeat
            self.seqno_width = int(cfg["seqno_width"])
            # time interval for timeout resending
            self.timeout = float(cfg["timeout"])
        self.env = env
        self.debug = debug
        self.message = message
        self.seqno_range = 2**self.seqno_width
        self.window_size = self.seqno_range // 2
        # the sequence number of the next character to be sent
        self.seqno = 0
        # the absolute index of the next character to be sent
        self.absno = 0
        # sequence number of first packet in outbound buffer
        self.seqno_start = 0
        # packet buffer to save the packets that havn't been acknowledged by receiver
        self.outbound: Deque[QueueItem] = deque()
        self.timers: Deque[Timer] = deque()
        # use `self.finish_channel.put(True)` to termiate the sending process
        self.finish_channel: Store = Store(env)

        self.proc = env.process(self.run(env))

    def new_packet(self, seqno: int, data: str) -> Packet:
        return Packet(time=self.env.now, size=40, packet_id=seqno, payload=data)

    def send_available(self):
        while len(self.outbound) > 0 and self.outbound[0].ack_received:
            self.outbound.popleft()
            timer = self.timers.popleft()
            timer.stop()
            self.seqno_start = (self.seqno_start + 1) % self.seqno_range
        if self.absno < len(self.message):
            while len(self.outbound) < self.window_size:
                packet = self.new_packet(self.seqno, self.message[self.absno])
                self.send_packet(packet)
                self.seqno = (self.seqno + 1) % self.seqno_range
                self.absno += 1
                self.outbound.append(QueueItem(packet))
                timer = Timer(self.env, self.timeout, self.timeout_callback, auto_restart=True, args=[packet])
                self.timers.append(timer)

    def timeout_callback(self, packet: Packet):
        self.dprint("timeout")
        self.send_packet(packet)

    def send_packet(self, packet: Packet):
        """Timeout callback for timer"""
        self.dprint(f"send {packet.payload} on seqno {packet.packet_id}")
        assert self.out
        self.out.put(packet)

    def run(self, env: Environment):
        self.send_available()
        yield self.finish_channel.get()

    def put(self, packet: Packet):
        """Receiving acknowledgement packet from receiver"""
        ackno = packet.packet_id
        dist = (ackno + self.seqno_range - self.seqno_start) % self.seqno_range
        if dist >= self.window_size:
            self.dprint(f"outdated ack {ackno}")
        else:
            self.outbound[dist].ack_received = True
            self.send_available()
        if len(self.outbound) == 0 and self.absno == len(self.message):
            self.finish_channel.put(True)

    def dprint(self, s):
        if self.debug:
            print(f"[sender](time: {self.env.now:.2f})", end=" -> ")
            print(s)
