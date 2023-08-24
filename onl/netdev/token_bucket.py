from ..device import Device
from ..packet import Packet
from ..sim import Store, PriorityItem, Environment


class TokenBucket(Device):
    """Implements a token bucket shaper.

    The token bucket size should be greater than the size of the largest packet
    that can occur on input. If this is not the case we always accumulate enough
    tokens to let the current packet pass based on the average rate. This may not
    be the behavior you desire.

    """
    def __init__(
        self, env, rate: float, bucket_size: int, peak=None, debug: bool = False
    ):
        self.env = env
        self.store = Store(env)
        self.rate = rate
        self.out = None
        self.packets_received = 0
        self.packets_sent = 0
        self.bucket_size = bucket_size
        self.peak = peak
        # current size of the bucket in bytes
        self.current_bucket = bucket_size
        # last time the bucket was updated
        self.update_time = 0.0
        self.debug = debug
        # used to track if a packet is current being sent
        self.busy = 0
        self.action = env.process(self.run(env))

    def run(self, env: Environment):
        while True:
            item: PriorityItem = yield self.store.get()
            packet: Packet = item.item
            now = env.now

            self.current_bucket = min(
                self.bucket_size,
                self.current_bucket + self.rate * (now - self.update_time) / 8.0,
            )
            self.update_time = now

            # Check if there are a sufficient number of tokens to allow the packet
            # to be sent; if not, we will then wait to accumulate enough tokens to
            # allow this packet to be sent regardless of the bucket size.
            if packet.size > self.current_bucket:
                yield env.timeout((packet.size - self.current_bucket) * 8.0 / self.rate)
                self.current_bucket = 0.0
                self.update_time = env.now
            else:
                self.current_bucket -= packet.size
                self.update_time = env.now

            if not self.out:
                raise ValueError("token bucket's out is None")
            if self.peak:
                yield env.timeout(packet.size * 8.0 / self.peak)
            self.out.put(packet)

            self.packets_sent += 1
            if self.debug:
                print(f"Sent packet {packet.packet_id} from flow {packet.flow_id}.")

    def put(self, packet):
        self.packets_received += 1
        self.store.put(packet)
