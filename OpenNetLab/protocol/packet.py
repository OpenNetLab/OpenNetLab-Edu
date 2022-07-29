from enum import IntEnum, auto
import pickle


class PacketType(IntEnum):
    START_EXPERIMENT = auto()
    END_EXPERIMENT = auto()
    EXPIREMENT_DATA = auto()
    START_TESTCASE = auto()
    END_TESTCASE = auto()


class ONLPacket:
    def __init__(self, packet_type, payload = None, test_idx = -1) -> None:
        self.packet_type = packet_type
        self.payload = payload
        self.idx = test_idx

    def to_bytes(self):
        return pickle.dumps(self)

    @classmethod
    def from_bytes(cls, data):
        return pickle.loads(data)


if __name__ == '__main__':
    onlp = ONLPacket(PacketType.EXPIREMENT_DATA, None, 0)
    onlp_bytes = onlp.to_bytes()
    onlp2 = ONLPacket.from_bytes(onlp_bytes)
    print(onlp2.payload)
    print(onlp2.idx)
