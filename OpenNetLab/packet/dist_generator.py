from typing import (
    Callable,
    Optional
)

from ..sim import Environment
from ..netdev import Device
from .packet import Packet


class DistPacketGenerator:
    def __init__(
        self,
        env: 'Environment',
        element_id: str,
        arrival_dist: Callable[[], float],
        size_dist: Callable[[], float],
        initial_delay: int = 0,
        finish=float('inf'),
        flow_id=0,
        rec_flow=False,
        debug=False,
    ) -> None:
        self.element_id = element_id
        self.env = env
        self.arrival_dist = arrival_dist
        self.size_dist = size_dist
        self.initial_delay = initial_delay
        self.finish = finish
        self.out: Optional[Device] = None
        self.packets_send = 0
        self.action = env.process(self.run(env))
        self.flow_id = flow_id

        self.rec_flow = rec_flow
        self.time_rec = []
        self.size_rec = []
        self.debug = debug

    def run(self, env: 'Environment'):
        yield env.timeout(self.initial_delay)
        while env.now < self.finish:
            yield env.timeout(self.arrival_dist())
            self.packets_send += 1
            packet = Packet(env.now,
                            self.size_dist(),
                            self.packets_send,
                            src=self.element_id,
                            flow_id=self.flow_id)
            if self.rec_flow:
                self.time_rec.append(packet.time)
                self.size_rec.append(packet.size)
            if self.debug:
                print(
                    f'Send packet {packet.packet_id} with flow_id {packet.flow_id} at '
                    f'time {env.now}'
                )
            if not self.out:
                raise Exception('out of current packet generator is None,\n'
                                '\tYou have to set out for packet generator')
            self.out.put(packet)
