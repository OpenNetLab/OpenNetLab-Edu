from .sink import PacketSink
from .packet import Packet
from ..sim import Environment
from ..device import OutMixIn


class TCPSink(PacketSink, OutMixIn):
    def __init__(
        self,
        env: Environment,
        rec_arrivals: bool = True,
        absolute_arrivals: bool = True,
        rec_waits: bool = True,
        rec_flow_ids: bool = True,
        debug: bool = False,
    ):
        super().__init__(
            env, rec_arrivals, absolute_arrivals, rec_waits, rec_flow_ids, debug
        )
        self.recv_buffer = list()
        self.next_seq_expected = 0

    def packet_arrived(self, packet: Packet):
        """Insert the packet into the receive buffer, which is a priority queue
        that is sorted based on the sequence number of the packet (packet_id)
        """
        self.recv_buffer.append([packet.packet_id, packet.packet_id + packet.size])
        self.recv_buffer.sort()

        merge_stats = []
        for start, end in self.recv_buffer:
            if merge_stats and start <= merge_stats[-1][1]:
                merge_stats[-1][1] = max(merge_stats[-1][1], end)
            else:
                merge_stats.append([start, end])
        self.recv_buffer = merge_stats

    def put(self, packet: Packet):
        super().put(packet)

        self.packet_arrived(packet)

        if len(self.recv_buffer) == 1:
            # in-order delivery: all data up to but not including
            # `next_seq_expected' have been received
            self.next_seq_expected = packet.packet_id + packet.size
        else:
            # out-of-order delivery or retransmissions: needs
            # to go through the receive buffer and find out
            # what the last in-order packet's sequence number is
            self.next_seq_expected = self.recv_buffer[0][1]


        acknowledgement = Packet(
            packet.time,
            size=40,
            packet_id=packet.packet_id,
            flow_id=packet.flow_id + 10000,
        )
        acknowledgement.ack = self.next_seq_expected

        assert self.out is not None
        self.out.put(acknowledgement)
