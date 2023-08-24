import random

from .port import Port


class REDPort(Port):
    """Implements a port with an output buffer, given an output rate and a
    buffer size (in either bytes or the number of packets). This implementation
    uses the Random Early Detection (RED) mechanism to drop packets.

    This element can set the rate of the output port and an upper limit for the
    average queue size (in bytes or the number of packets), and it keeps track
    of the number packets received and dropped.

    """

    def __init__(
        self,
        env,
        rate: float,
        max_threshold: int,
        min_threshold: int,
        max_probability: float,
        element_id: str,
        qlimit: int,
        weight_factor: int = 9,
        limit_bytes: bool = False,
        debug: bool = False,
    ):
        super().__init__(env, rate, qlimit, limit_bytes, element_id, debug)
        self.max_probability = max_probability
        """ The maximum probability is the fraction of packets dropped when the
        average queue length is at the maximum threshold, which is
        'max_threshold'. The rate of packet drop increases linearly as the
        average queue length increases, until the average queue length reaches
        the maximum threshold, 'max_threshold'. All packets will be dropped
        when 'qlimit' is exceeded.
        """
        self.max_threshold = max_threshold
        """ The maximum (average) queue length threshold, beyond which packets
        will be dropped at the maximum probability.
        """
        self.min_threshold = min_threshold
        """ The minimum (average) queue length threshold to start dropping
        packets. This threshold should be set high enough to maximize the link
        utilization. If the minimum threshold is too low, packets may be
        dropped unnecessarily, and the transmission link will not be fully
        used.
        """
        self.weight_factor = weight_factor
        """The exponential weight factor 'n' for computing the average queue size.
        average = (old_average * (1-1/2^n)) + (current_queue_size * 1/2^n)
        """
        self.average_queue_size = 0

    def put(self, packet):
        self.packets_received += 1

        if self.limit_bytes:
            current_queue_size = self.byte_size
        else:
            current_queue_size = len(self.store.items)

        alpha = 2 ** (-self.weight_factor)
        self.average_queue_size = (
            self.average_queue_size * (1 - alpha) + current_queue_size * alpha
        )

        if self.average_queue_size >= self.qlimit:
            self.packets_dropped += 1
            if self.debug:
                print(
                    f"The average queue length {self.average_queue_size} "
                    f"exceeds the upper limit {self.qlimit}."
                )
        elif self.average_queue_size >= self.max_threshold:
            rand = random.uniform(0, 1)
            if rand <= self.max_probability:
                self.packets_dropped += 1
                if self.debug:
                    print(
                        f"The average queue length ({self.average_queue_size}) "
                        f"exceeds the maximum threshold ({self.qlimit}), ",
                        f"packet dropped with probability {self.max_probability}",
                    )
            else:
                self.byte_size += packet.size
                self.store.put(packet)
        elif self.average_queue_size >= self.min_threshold:
            prob = (
                (self.average_queue_size - self.min_threshold)
                / (self.max_threshold - self.min_threshold)
                * self.max_probability
            )
            rand = random.uniform(0, 1)
            if rand <= prob:
                self.packets_dropped += 1
                if self.debug:
                    print(
                        f"The average queue length {self.average_queue_size} "
                        f"exceeds the minimum threshold {self.min_threshold}, "
                        f"packet dropped with probability {prob}."
                    )
            else:
                self.byte_size += packet.size
                self.store.put(packet)
        else:
            self.byte_size += packet.size
            self.store.put(packet)
