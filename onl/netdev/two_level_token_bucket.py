from typing import Optional

from ..device import Device
from ..packet import Packet
from ..sim import Store, PriorityItem, Environment


class TwoRateTokenBucket(Device):
    """Implments a two-rate token bucket shaper, with a bucket for committed
    information rate (CIR) and another for the peak information rate (PIR).

    """

    def __init__(
        self,
        env,
        cir: int,
        cbs: int,
        pir: Optional[int] = None,
        pbs: Optional[int] = None,
        debug=False,
    ):
        self.store = Store(env)
        self.env = env
        self.out = None
        self.cir = cir
        """Committed Information Rate(CIR):
        This is the average or sustained rate at which data is allowed to
        be sent or received. The CIR represents the guaranteed bandwidth that a
        network connection or device is allocated over a longer period of time.

        """
        self.cbs = cbs
        """Current size of the committed bucket in bytes"""
        self.pir = pir
        """Peak Information Rate (PIR):
        This is the maximum rate at which data can be sent or received, allowing
        for short bursts of traffic above the committed rate. The PIR represents
        the bandwidth that can be used for short periods without violating the
        overall traffic policy.

        """
        self.pbs = pbs
        """Current size of the peak bucket in bytes"""
        self.packets_received = 0
        self.packets_sent = 0

        self.current_bucket_commit = cbs
        self.current_bucket_peak = pbs
        self.update_time = 0.0  # Last time the bucket was updated
        self.debug = debug
        self.busy = 0  # Used to track if a packet is currently being sent
        self.action = env.process(self.run(env))

    def run(self, env):
        """When data packets arrive for transmission, tokens are consumed from
        the buckets. If there are enough tokens in the Peak Bucket, they are
        used first. If the Peak Bucket is empty but the Committed Bucket has
        tokens, those tokens are used to transmit data packets. If there are no
        tokens available in either bucket, the excess traffic is subject to
        various actions, such as being delayed, dropped, or marked for lower
        priority handling.
        """
        while True:
            item: PriorityItem = yield self.store.get()
            packet: Packet = item.item
            now = env.now

            self.current_bucket_commit = min(
                self.cbs,
                self.current_bucket_commit + self.cir * (now - self.update_time) / 8.0,
            )

            if self.pir:
                assert self.pbs
                self.current_bucket_peak = min(
                    self.pbs,
                    self.current_bucket_peak
                    + self.pir * (now - self.update_time) / 8.0,
                )
            self.update_time = now

            if self.pir:
                assert self.current_bucket_peak
                if packet.size > self.current_bucket_peak:
                    yield env.timeout(
                        (packet.size - self.current_bucket_peak) * 8.0 / self.pir
                    )
                    self.current_bucket_peak = 0.0
                    packet.color = "red"
                    self.update_time = env.now
                elif packet.size > self.current_bucket_commit:
                    self.current_bucket_peak -= packet.size
                    self.current_bucket_commit = 0.0
                    packet.color = "yellow"
                    self.update_time = env.now
                else:
                    self.current_bucket_commit -= packet.size
                    self.current_bucket_peak -= packet.size
                    packet.color = "green"
                    self.update_time = env.now
            else:
                if packet.size > self.current_bucket_commit:
                    yield env.timeout(
                        (packet.size - self.current_bucket_commit) * 8.0 / self.cir
                    )
                    self.current_bucket_commit = 0.0
                    packet.color = "yellow"
                    self.update_time = env.now
                else:
                    self.current_bucket_commit -= packet.size
                    packet.color = "green"
                    self.update_time = env.now

            assert self.out
            self.out.put(packet)

            self.packets_sent += 1
            if self.debug:
                print(
                    f"Sent out packet with id {packet.packet_id} "
                    f"belonging to flow {packet.flow_id} with color {packet.color}."
                )

    def put(self, packet: Packet):
        self.packets_received += 1
        self.store.put(packet)
