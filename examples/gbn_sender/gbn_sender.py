import asyncio
import json
from collections import deque

from OpenNetLab.node import TCPClientNode
from OpenNetLab.utils import Timer
from gbn_packet import new_packet
from gbn_logger import logger


class GBNSender(TCPClientNode):
    async def setup(self):
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
            self.test_idx = 0
            self.enable_recording = True

    async def student_task(self, message):
        pass

    async def testcase_handler(self) -> bool:
        assert self.test_idx < len(self.testcases)
        message = self.testcases[self.test_idx]
        await self.student_task(message)
        ret = False
        if self.test_idx == len(self.testcases) - 1:
            ret = True
        self.test_idx += 1
        return ret


class StudentGBNSender(GBNSender):
    async def setup(self):
        await super().setup()
        self.outbound = deque([], self.window_size)
        self.next_seqno = 0
        self.timer = Timer(self.timeout, self.timeout_handler)

    async def student_task(self, message):
        self.outbound.clear()
        self.next_seqno = 0
        self.absno = 0
        self.timer.reset()

        await self.send_available(message)
        while True:
            while True:
                packet = await self.recv_next_packet()
                if not packet:
                    break
                resp = packet.payload
                ackno = resp['ackno']
                tmp = []
                tmp.clear()
                if self.is_valid_ackno(ackno):
                    while len(self.outbound) > 0 and self.outbound[0]['seqno'] != ackno:
                        tmp.append(str(self.outbound.popleft()['seqno']))
                # logger.debug('[ACK]: ackno %d received, Packets %s are acked' % (
                #     ackno, ','.join(tmp)))
                await self.send_available(message)
                self.timer.reset()
            if len(self.outbound) == 0 and self.absno == len(message):
                break
            await asyncio.sleep(0.02)

        logger.debug('[TESTCASE %d FINISHED]' % self.test_idx)

    async def teardown(self):
        pass

    def is_valid_ackno(self, ackno):
        if not(0 <= ackno < self.seqno_range and len(self.outbound) > 0):
            return False
        if not any((pkt['seqno'] + 1) % self.window_size == ackno for pkt in self.outbound):
            return False
        return True

    async def send_available(self, message):
        while len(self.outbound) < self.window_size and self.absno < len(message):
            pkt = new_packet(self.absno, self.next_seqno,
                             0, message[self.absno])
            await self.send(pkt)
            # logger.info('[SEND]: Sending seqno %d on message %s' %
            #             (pkt['seqno'], pkt['message']))
            self.next_seqno = (self.next_seqno + 1) % self.seqno_range
            self.absno += 1
            self.outbound.append(pkt)
        self.timer.reset()

    async def timeout_handler(self):
        for pkt in self.outbound:
            # logger.error('[TIMEOUT]: Reseding seqno %d on message %s' %
            #              (pkt['seqno'], pkt['message']))
            await self.send(pkt)
        self.timer.reset()


async def main():
    sender = StudentGBNSender()
    await sender.run()

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
