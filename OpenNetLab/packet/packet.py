"""
Simple class that represents a packet.
"""


class Packet:
    def __init__(
        self,
        time: float,
        size: float,
        packet_id: int,
        realtime=0,
        src="source",
        dst="destination",
        flow_id=0,
        payload=None,
    ):
        self.time = time
        self.size = size
        self.packet_id = packet_id
        self.realtime = realtime
        self.src = src
        self.dst = dst
        self.flow_id = flow_id
        self.payload = payload

        self.color = None
        self.priority = {}
        self.ack = 0
        self.current_time = 0
        self.perhop_time = {}  # used by port to record per-hop arrival times

    def __repr__(self) -> str:
        return f'did: {self.packet_id}, src:  {self.src}, time: {self.time}, size: {self.size}'
