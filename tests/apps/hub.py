from onl.netdev import Hub, Wire
from onl.device import Device
from onl.packet import Packet
from onl.sim import Environment


class Endpoint(Device):
    def __init__(self, env, element_id: str):
        self.env = env
        self.element_id = element_id
        self.out = None

    def send(self):
        pkt = Packet(self.env.now, 40, packet_id=0, src=self.element_id)
        assert self.out
        self.out.put(pkt)

    def put(self, packet):
        print(f"{self.element_id} receive packet from {packet.src} at time {self.env.now}")


def test1():
    env = Environment()
    endpoints = []
    for i in range(5):
        endpoints.append(Endpoint(env, f"endpoint_{i}"))
    hub = Hub(env, endpoints, [None] * 5)
    for end in endpoints:
        end.send()
    env.run()


def test2():
    env = Environment()
    endpoints = []
    for i in range(5):
        endpoints.append(Endpoint(env, f"endpoint_{i}"))
    hub = Hub(env, endpoints, [Wire(env, lambda: 30, 0) for _ in range(5)])
    for end in endpoints:
        end.send()
    env.run()

test1()
print('------------')
test2()
