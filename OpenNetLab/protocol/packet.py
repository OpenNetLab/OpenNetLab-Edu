import json
from enum import IntEnum, auto


class PacketType(IntEnum):
    START_EXPERIMENT = auto()
    END_EXPERIMENT = auto()
    EXPIREMENT_DATA = auto()
    START_TESTCASE = auto()
    END_TESTCASE = auto()


class ONLPacket:
    def __init__(self, packet_type, payload) -> None:
        self.packet_type = packet_type
        self.payload = payload

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    def to_bytes(self):
        return json.dumps(self, default=lambda o: o.__dict__).encode('utf-8')

    @classmethod
    def from_bytes(cls, data):
        return cls(**json.loads(data))
