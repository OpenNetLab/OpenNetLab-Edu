import json

START_NOTIFY    = 1
END_NOTIFY      = 2
STATUS_QUERY    = 3
STATUS_REPLY    = 4
EXPIREMENT_DATA = 5
RESULT_DATA     = 6

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

if __name__ == '__main__':
    bts = ONLPacket(START_NOTIFY, "haha").to_bytes()
    print(bts)
    pack = ONLPacket.from_bytes(bts)
    print(pack)
