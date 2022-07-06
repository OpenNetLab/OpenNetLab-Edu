import os
import json
from collections import deque
from enum import IntEnum, auto

SEND = 1
RECV = 0
DEBUG = False

def dprint(msg):
    if DEBUG:
        print(msg)

class ErrorType(IntEnum):
    NoError = auto()
    NoPacketSent = auto()
    PacketNotSent = auto()
    WrongPacket = auto()
    ResendBeforeTimeout = auto()


class GBNJudge:
    def __init__(self) -> None:
        self.test_dir = os.getcwd() + '/judge/'
        with open('./lab_config.json') as fp:
            cfg = json.load(fp)
            self.absno = 0
            self.seqno_width = int(cfg['seqno_width'])
            self.loss_rate = float(cfg['loss_rate'])
            self.max_delay = int(cfg['max_delay'])
            self.testcases = cfg['testcases']
            self.timeout = float(cfg['timeout'])
            self.seqno_range = 2**self.seqno_width
            self.window_size = self.seqno_range - 1
        self.outbound = deque()
        self.error_type = ErrorType.NoError

    def judge(self):
        for testcase_idx in range(len(self.testcases)):
            with open(self.test_dir + f'test_record{testcase_idx}.json') as fp:
                records = json.load(fp)
                if self.check(testcase_idx, records):
                    print(f'TESTCASE {testcase_idx} passed')
                else:
                    print(f'TESTCASE {testcase_idx} not passed')
                    if self.error_type == ErrorType.NoPacketSent:
                        print('Error: no packet is not sent')
                    elif self.error_type == ErrorType.PacketNotSent:
                        print('Error: some packet is not sent')
                    elif self.error_type == ErrorType.WrongPacket:
                        print('Error: sending wrong packet')
                    elif self.error_type == ErrorType.ResendBeforeTimeout:
                        print('Error: resending packet before timer times out')


    def is_valid_ackno(self, ackno):
        if not(0 <= ackno < self.seqno_range and len(self.outbound) > 0):
            return False
        if not any((pkt['seqno'] + 1) % self.window_size == ackno for pkt in self.outbound):
            return False
        return True

    def check(self, testcase_idx, records) -> bool:
        next_seqno = 0
        msg_len = len(self.testcases[testcase_idx])
        length = len(records)
        if length == 0:
            self.error_type = ErrorType.NoPacketSent
            return False
        last_time = records[0]['packet']['time']
        last_packet_sent = False
        last_packet_seqno = 0
        for i in range(min(self.window_size, msg_len)):
            motion = records[i]['type']
            packet = records[i]['packet']
            if motion != SEND:
                self.error_type = ErrorType.PacketNotSent
                return False
            if packet['seqno'] != next_seqno:
                self.error_type = ErrorType.WrongPacket
                return False
            if packet['absno'] == msg_len - 1:
                last_packet_sent = True
                last_packet_seqno = packet['seqno']
            dprint(packet)
            next_seqno = (next_seqno + 1) % self.seqno_range
            self.outbound.append(records[i]['packet'])
        i = self.window_size
        while i < length:
            motion = records[i]['type']
            packet = records[i]['packet']
            if motion == SEND:
                if packet['time'] - last_time < self.timeout:
                    self.error_type = ErrorType.ResendBeforeTimeout
                    return False
                else:
                    dprint('----TIMEOUT----')
                    last_time = packet['time']
                    dprint(f'outbound len: {len(self.outbound)}')
                    for pkt in self.outbound:
                        dprint(packet)
                        if motion != SEND:
                            self.error_type = ErrorType.PacketNotSent
                            return False
                        if pkt['seqno'] != packet['seqno']:
                            self.error_type = ErrorType.WrongPacket
                            return False
                        i += 1
                        motion = records[i]['type']
                        packet = records[i]['packet']
                    continue
            else:
                ackno = packet['ackno']
                if not self.is_valid_ackno(ackno):
                    i += 1
                    continue
                else:
                    cnt = 0
                    while len(self.outbound) > 0 and self.outbound[0]['seqno'] != ackno:
                        cnt += 1
                        self.outbound.popleft()
                    dprint(f'ack = {ackno},  cnt = {cnt}')
                    for _ in range(cnt):
                        if last_packet_sent:
                            break
                        i += 1
                        motion = records[i]['type']
                        packet = records[i]['packet']
                        dprint(packet)
                        if motion != SEND:
                            self.error_type = ErrorType.PacketNotSent
                            return False
                        if packet['seqno'] != next_seqno:
                            self.error_type = ErrorType.WrongPacket
                            return False
                        if packet['absno'] == msg_len - 1:
                            last_packet_sent = True
                            last_packet_seqno = packet['seqno']
                        next_seqno = (next_seqno + 1) % self.seqno_range
                        self.outbound.append(packet)
            i += 1
        if last_packet_sent and (last_packet_seqno + 1) % self.seqno_range == records[-1]['packet']['ackno']:
            return True
        return False


if __name__ == '__main__':
    j = GBNJudge()
    j.judge()
