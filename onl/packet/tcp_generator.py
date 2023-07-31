from abc import abstractmethod
from typing import Callable, Optional, Dict

from dataclasses import dataclass
from ..sim import Environment, Store, ProcessGenerator
from ..packet import Packet
from ..utils import Timer
from ..device import Device, OutMixIn


@dataclass
class Flow:
    """Keeping track of all the properties of a network flow"""

    flow_id: int
    src: str
    dst: str
    start_time: float
    finish_time: float
    # the total data size in bytes from this flow
    size: Optional[int] = None
    # arrival time distribution
    arrival_dist: Optional[Callable[[], float]] = None
    size_dist: Optional[Callable[[], int]] = None
    pkt_gen: object = None
    pkt_sink: object = None
    path: Optional[list] = None

    def __repr__(self) -> str:
        return f"Flow {self.flow_id} on {self.path}"


class CongestionControl:
    def __init__(
        self,
        mss: int = 512,
        cwnd: int = 512,
        ssthresh: int = 65535,
        debug: bool = False,
    ) -> None:
        self.mss = mss
        self.cwnd = cwnd
        self.ssthresh = ssthresh
        self.debug = debug

    def __repr__(self) -> str:
        return f"cwnd: {self.cwnd}, ssthresh: {self.ssthresh}"

    @abstractmethod
    def ack_received(self, rtt: float = 0, current_time: float = 0):
        """Actions to be taken when a new ack has been received"""

    def timer_expired(self):
        """Actions to be taken when a timer expired."""
        self.cwnd = self.mss

    def dupack_over(self):
        """Actions to be taken when a new ack is received after previous dupacks."""
        # RFC 2001 and TCP Reno
        self.cwnd = self.ssthresh

    def consecutive_dupacks_received(self):
        """Actions to be taken when three consecutive dupacks are received."""
        # fast retransmit in RFC 2001 and TCP Reno
        self.ssthresh = max(2 * self.mss, self.cwnd / 2)
        self.cwnd = self.ssthresh + 3 * self.mss

    def more_dupacks_received(self):
        """Actions to be taken when more than three consecutive dupacks are received."""
        self.cwnd += self.mss


class TCPReno(CongestionControl):
    def ack_received(self, rtt: float = 0, current_time: float = 0):
        if self.cwnd <= self.ssthresh:
            # slow start
            self.cwnd += self.mss
        else:
            # congestion avoidance
            self.cwnd += self.mss * self.mss / self.cwnd


class TCPCubic(CongestionControl):
    def __init__(
        self,
        mss: int = 512,
        cwnd: int = 512,
        ssthresh: int = 65535,
        debug: bool = False,
    ) -> None:
        super().__init__()
        self.W_last_max: float = 0
        self.epoch_start = 0
        self.origin_point = 0
        self.d_min: float = 0
        self.W_tcp = 0
        self.K = 0
        self.ack_cnt = 0
        self.tcp_friendliness = True
        self.fast_convergence = True
        self.beta = 0.2
        self.C = 0.4
        self.cwnd_cnt = 0
        self.cnt = 0

    def __repr__(self):
        return f"cwnd: {self.cwnd}, ssthresh: {self.ssthresh}"

    def cubic_reset(self):
        """Resetting the states in CUBIC"""
        self.W_last_max = 0
        self.epoch_start = 0
        self.origin_point = 0
        self.d_min = 0
        self.W_tcp = 0
        self.K = 0
        self.ack_cnt = 0

    def cubic_update(self, current_time):
        """Updating CUBIC parameters upon the arrival of a new ack."""
        self.ack_cnt += 1
        if self.epoch_start <= 0:
            self.epoch_start = current_time
            if self.cwnd < self.W_last_max:
                self.K = ((self.W_last_max - self.cwnd) / self.C) ** (1.0 / 3)
            else:
                self.K = 0
                self.origin_point = self.cwnd
            self.ack_cnt = 1
            self.W_tcp = self.cwnd
        t = current_time + self.d_min - self.epoch_start
        target = self.origin_point + self.C * (t - self.K) ** 3
        if target > self.cwnd:
            self.cnt = self.cwnd / (target - self.cwnd)
        else:
            self.cnt = 100 * self.cwnd
        if self.tcp_friendliness:
            self.cubic_tcp_friendliness()

    def cubic_tcp_friendliness(self):
        """CUBIC actions in TCP mode."""
        self.W_tcp += 3 * self.beta / (2 - self.beta) * (self.ack_cnt / self.cwnd)
        self.ack_cnt = 0
        if self.W_tcp > self.cwnd:
            max_cnt = self.cwnd / (self.W_tcp - self.cwnd)
            if self.cnt > max_cnt:
                self.cnt = max_cnt

    def timer_expired(self):
        """Actions to be taken when a timer expired."""
        # setting the congestion window to 1 segment
        self.cwnd = self.mss
        self.cubic_reset()

    def ack_received(self, rtt: float = 0, current_time: float = 0):
        """Actions to be taken when a new ack has been received."""
        if self.d_min > 0:
            self.d_min = min(self.d_min, rtt)
        else:
            self.d_min = rtt

        if self.cwnd <= self.ssthresh:
            # slow start
            self.cwnd += self.mss
        else:
            # congestion avoidance
            self.cubic_update(current_time)

            if self.cwnd_cnt > self.cnt:
                self.cwnd += self.mss
                self.cwnd_cnt = 0
            else:
                self.cwnd_cnt += 1


class TCPPacketGenerator(Device, OutMixIn):
    def __init__(
        self,
        env: Environment,
        flow: Flow,
        cc: CongestionControl,
        element_id: Optional[str] = None,
        rtt_estimate: float = 1.0,
        debug: bool = False,
    ):
        self.element_id = element_id
        self.env = env
        self.flow = flow
        self.congestion_control = cc

        # maximum segment size, in bytes
        self.mss = 512
        # the time when data last arrvied from the flow
        self.last_arrival = 0

        # the next sequence number to be sent, in bytes
        self.next_seq = 0
        # the maximum sequence number in the in-transit data buffer
        self.send_buffer = 0
        # the sequence number of the segment that is last acknowledged
        self.last_ack = 0
        # the count of duplicate acknowledgements
        self.dupack = 0
        # the RTT estimate
        self.rtt_estimate = rtt_estimate
        # the retransmission timeout
        self.rto = self.rtt_estimate * 2
        # an estimate of the RTT deviation
        self.est_deviation = 0
        # whether or not space in the congestion window is available
        self.cwnd_avaialbe = Store(env)

        # the timers, one for each in-filght packets (segments) sent
        self.timers: Dict[int, Timer] = dict()
        # the in-flight packets (segments)
        self.sent_packets: Dict[int, Packet] = dict()

        self.action = env.process(self.run(env))
        self.debug = debug

    def dprint(self, msg: str):
        if self.debug:
            print(msg)

    def run(self, env: Environment) -> ProcessGenerator:
        if self.flow.start_time:
            yield env.timeout(self.flow.start_time)

        while env.now < self.flow.finish_time:
            # all bytes in flow has been received
            if self.flow.size and self.next_seq >= self.flow.size:
                return

            while self.next_seq >= self.send_buffer:
                # retrieving more packets from the application-layer flow
                if self.flow.arrival_dist:
                    # if the flow has an arrival distribution, wait for the next arrival
                    wait_time = self.flow.arrival_dist() - (
                        self.env.now - self.last_arrival
                    )
                    if wait_time > 0:
                        yield env.timeout(wait_time)
                    self.last_arrival = env.now

                packet_size = 0
                if self.flow.size_dist:
                    packet_size = self.flow.size_dist()
                else:
                    if self.flow.size:
                        packet_size = min(self.mss, self.flow.size - self.next_seq)
                    else:
                        packet_size = self.mss
                self.send_buffer += packet_size

            #     acked        sent         buffered
            # |----------|-------------|-----------------|
            #          last_ack    next_seq
            #            |--------------------------|
            #                         cwnd
            #                            can be sent
            #                          |------------|
            #
            # send the next packet with size of MSS, if data can be sent is
            # less than MSS, than skip
            if self.next_seq + self.mss <= min(
                self.send_buffer, self.last_ack + self.congestion_control.cwnd
            ):
                packet = Packet(
                    time=env.now,
                    size=self.mss,
                    packet_id=self.next_seq,
                    src=self.flow.src,
                    flow_id=self.flow.flow_id,
                )

                self.sent_packets[packet.packet_id] = packet
                self.dprint(
                    f"Sent packet {packet.packet_id} with size {packet.size}, "
                    f"flow_id {packet.flow_id} at time {env.now:.4f}"
                )
                assert self.out
                self.out.put(packet)

                self.next_seq += packet.size
                self.timers[packet.packet_id] = Timer(
                    env,
                    timer_id=packet.packet_id,
                    timeout=self.rto,
                    timeout_callback=self.timeout_callback,
                )
                self.dprint(
                    f"Setting a timer for packet {packet.packet_id} with an "
                    f"RTO of {self.rto:.4f}"
                )
            else:
                yield self.cwnd_avaialbe.get()

    def timeout_callback(self, packet_id):
        self.dprint(
            "Timer expired for packet {:d} at time {:.4f}.".format(
                packet_id, self.env.now
            )
        )
        self.congestion_control.timer_expired()

        # retransmit the segment
        self.resend_packet(packet_id)

        # start a new timer for this segment and doubling the RTO
        self.rto *= 2
        self.timers[packet_id].restart(self.rto)

    def put(self, ack: Packet):
        """Upon receiving an acknowledgement packet"""
        # the received packet must be an ack
        assert ack.flow_id >= 10000

        ackno = ack.ack
        if ackno == self.last_ack:
            self.dupack += 1
        else:
            # fast recovery
            if self.dupack > 0:
                self.congestion_control.dupack_over()
                self.dupack = 0

        if self.dupack == 3:
            self.congestion_control.consecutive_dupacks_received()
            self.resend_packet(ackno)
            return
        elif self.dupack > 3:
            self.congestion_control.more_dupacks_received()
            if self.last_ack + self.congestion_control.cwnd >= ackno:
                self.resend_packet(ackno)
            return

        if self.dupack == 0:
            # new ack received, update the RTT estimate and the retransmission timout
            sample_rtt = self.env.now - ack.time

            # Congestion Avoidance and Control
            sample_err = sample_rtt - self.rtt_estimate
            self.rtt_estimate += 0.125 * sample_err
            self.est_deviation += 0.25 * (abs(sample_err) - self.est_deviation)
            self.rto = self.rtt_estimate + 4 * self.est_deviation

            self.last_ack = ackno
            self.congestion_control.ack_received(sample_rtt, self.env.now)

            self.dprint(
                f"Ack received till sequence number {ackno} at time {self.env.now:.4f}."
            )
            self.dprint(
                f"Congestion window size = {self.congestion_control.cwnd:.1f}, last ack = {ackno}."
            )

            if ack.packet_id in self.timers:
                self.timers[ack.packet_id].stop()
                del self.timers[ack.packet_id]
                del self.sent_packets[ack.packet_id]

            self.cwnd_avaialbe.put(True)

    def resend_packet(self, seqno: int):
        resent_pkt = self.sent_packets[seqno]
        resent_pkt.time = self.env.now
        self.dprint(
            "Resending packet {:d} with flow_id {:d} at time {:.4f}.".format(
                resent_pkt.packet_id, resent_pkt.flow_id, self.env.now
            )
        )
        assert self.out
        self.out.put(resent_pkt)
