import asyncio
import json
from collections import deque

from onl.node.client import TCPClientNode
from onl.utils.timer import Timer
from sr_packet import new_packet
from sr_logger import logger


class BaseSRSender(TCPClientNode):
    async def setup(self):
        with open('./lab_config.json') as fp:
            cfg = json.load(fp)
            self.seqno_width = int(cfg['seqno_width'])
            self.loss_rate = float(cfg['loss_rate'])
            self.max_delay = int(cfg['max_delay'])
            self.testcases = cfg['testcases']
            self.timeout = float(cfg['timeout'])
            self.seqno_range = 2**self.seqno_width
            self.window_size = self.seqno_range // 2
            self.test_idx = 0

    async def send_message(self, message):
        pass

    async def testcase_handler(self) -> bool:
        assert self.test_idx < len(self.testcases)
        message = self.testcases[self.test_idx]
        await self.send_message(message)
        ret = False
        if self.test_idx == len(self.testcases) - 1:
            ret = True
        self.test_idx += 1
        return ret


class SRSender(BaseSRSender):
    async def setup(self):
        await super().setup()
        self.outbound = deque([], self.window_size)
        self.timers = deque([], self.window_size)

    async def send_message(self, message):
        self.cur_seqno = 0
        self.next_seqno = 0
        self.outbound.clear()
        self.absno = 0
        await self.send_available(message)

        while True:
            resp = await self.recv_data()
            ackno = resp['ackno']
            if self.is_valid_ackno(ackno):
                acked_seq = (ackno+self.seqno_range-1) % self.seqno_range
                rel_idx = (acked_seq + self.seqno_range -
                           self.cur_seqno) % self.seqno_range
                self.outbound[rel_idx][1] = True
                # logger.debug('[ACK]: ackno %d received, Packets %s are acked' % (ackno, acked_seq))
                await self.send_available(message)
            if len(self.outbound) == 0 and self.absno == len(message):
                break


    def is_valid_ackno(self, ackno):
        acked_seq = (ackno+self.seqno_range-1) % self.seqno_range
        if self.cur_seqno < self.next_seqno:
            return self.cur_seqno <= acked_seq < self.next_seqno
        else:
            return self.cur_seqno <= acked_seq < self.seqno_range or 0 <= acked_seq < self.next_seqno

    async def send_available(self, message):
        while len(self.outbound) > 0 and self.outbound[0][1] == True:
            self.outbound.popleft()
            timer = self.timers.popleft()
            timer.cancel()
            self.cur_seqno = (self.cur_seqno + 1) % self.seqno_range
        while len(self.outbound) < self.window_size and self.absno < len(message):
            pkt = new_packet(self.absno, self.next_seqno,
                             0, message[self.absno])
            await self.send(pkt)
            # logger.info('[SEND]: Sending seqno %d on message %s' % (pkt['seqno'], pkt['message']))
            self.next_seqno = (self.next_seqno + 1) % self.seqno_range
            self.absno += 1
            self.outbound.append([pkt, False])
            timer = Timer(self.timeout, self.timeout_handler, pkt)
            timer.auto_reset = True
            timer.reset()
            self.timers.append(timer)

    async def timeout_handler(self, pkt):
        # logger.error('[TIMEOUT]: Resending seqno %d on message %s' % (pkt['seqno'], pkt['message']))
        await self.send(pkt)


async def main():
    sender = SRSender()
    await sender.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
