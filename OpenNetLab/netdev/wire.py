import random
from typing import (
    Callable,
    Optional
)

from ..packet import Packet
from ..device import Device
from ..sim import Environment, Store


class Wire(Device):
    """Implements a network wire (cable) that introduces a propagation delay.
       Set the "out" member variable to the entity to receive the packet.

    """

    def __init__(
        self,
        env: 'Environment',
        delay_dist: Callable[[], float],
        loss_dict: Optional[Callable[[int], float]] = None,
        wire_id: int = 0,
        debug: bool = False
    ):
        self.env = env
        self.store = Store(env)
        self.delay_dist = delay_dist
        self.loss_dist_fn = loss_dict
        self.wire_id = wire_id
        self.debug = debug
        self.packets_rec = 0
        self.action = env.process(self.run(env))

    def run(self, env):
        while True:
            packet = yield self.store.get()
            if self.loss_dist_fn is None or random.uniform(0, 1) >= self.loss_dist_fn(packet.packet_id):
                # The amount of time for this packet to stay in my store
                queued_time = self.env.now - packet.current_time
                delay = self.delay_dist()

                # If queued time for this packet is greater than its propagation delay,
                # it implies that the previous packet had experienced a longer delay.
                # Since out-of-order delivery is not supported in simulation, deliver
                # to the next component immediately.
                if queued_time < delay:
                    yield self.env.timeout(delay - queued_time)

                if self.debug:
                    print("Left wire #{} at {:.2f}: {}".format(
                        self.wire_id, self.env.now, packet))

                assert self.out
                self.out.put(packet)
            else:
                if self.debug:
                    print("Dropped on wire #{} at {:.2f}: {}".format(
                        self.wire_id, self.env.now, packet))

    def put(self, packet: Packet):
        """send packet to next device"""
        self.packets_rec += 1
        if self.debug:
            print(f'Entered wire #{self.wire_id} at {self.env.now}: {packet}')
        packet.current_time = self.env.now
        return self.store.put(packet)
