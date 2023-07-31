import json
from pathlib import Path
from typing import Optional, List
from onl.packet import Packet
from onl.device import Device, OutMixIn
from onl.sim import Environment


class SRReceiver(Device, OutMixIn):
    def __init__(self, env: Environment, debug: bool = False):
        cfgpath = Path(__file__).parent.joinpath('lab_config.json')
        with cfgpath.open() as fp:
            cfg = json.load(fp)
            # the bits of the sequence number, which decides the sequence
            # number range and window size of selective repeat
            self.seqno_width = int(cfg["seqno_width"])
            # time interval for timeout resending
            self.timeout = float(cfg["timeout"])
        self.env = env
        self.seqno_range = 2**self.seqno_width
        self.window_size = self.seqno_range // 2
        self.seqno_start = 0
        self.message = ""
        self.recv_window: List[Optional[Packet]] = [None] * self.window_size
        self.recv_start = 0
        self.debug = debug

    def new_packet(self, ackno: int) -> Packet:
        return Packet(time=self.env.now, size=40, packet_id=ackno)

    def put(self, packet: Packet):
        seqno = packet.packet_id
        data = packet.payload
        dist = (seqno + self.seqno_range - self.seqno_start) % self.window_size
        if dist >= self.window_size:
            self.dprint(
                f"discard {data} on invalid seqno: {seqno}"
            )
            return
        self.recv_window[(self.recv_start + dist) % self.window_size] = packet
        while self.recv_window[self.recv_start] is not None:
            cached_pkt = self.recv_window[self.recv_start]
            assert cached_pkt
            self.message += cached_pkt.payload
            self.recv_window[self.recv_start] = None
            self.recv_start = (self.recv_start + 1) % self.window_size
            self.seqno_start = (self.seqno_start + 1) % self.seqno_range
            ack_pkt = self.new_packet(self.seqno_start)
            assert self.out
            self.out.put(ack_pkt)
            self.dprint(
                f"send ack {self.seqno_start}"
            )

    def dprint(self, s: str):
        if self.debug:
            print(f"[receiver](time: {self.env.now:.2f})", end=" -> ")
            print(s)
