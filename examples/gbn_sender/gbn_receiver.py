import asyncio
import json

from OpenNetLab.node import TCPServerNode
from gbn_packet import new_packet
from gbn_logger import logger


class GBNReceiver(TCPServerNode):
    async def setup(self):
        with open('./lab_config.json') as fp:
            cfg = json.load(fp)
            self.seq_no_width = int(cfg['seqno_width'])
            self.loss_rate = float(cfg['loss_rate'])
            self.max_delay = int(cfg['max_delay'])
            self.testcases = cfg['testcases']
            self.testcases_ranks = cfg['testcase_ranks']
        self.grade = 0
        self.next_msg_idx = 0
        self.test_idx = 0
        self.seqno_range = 2**self.seq_no_width
        self.window_size = self.seqno_range - 1
        self.next_seqno = 0
        self.message = ''
        self.failed_test = []
        self.success_test = []
        self.verbose = True
        self.evaulate_here = True

    async def recv_callback(self, data):
        if data['absno'] < len(self.message):
            pkt = new_packet(0, 0, self.next_seqno, '')
            await self.send(pkt)
            await self.log('ACK', data)
            return
        if data['seqno'] != self.next_seqno:
            await self.log('DISCARD', data)
            return
        self.message += data['message']
        self.next_seqno = (self.next_seqno + 1) % self.seqno_range
        pkt = new_packet(0, 0, self.next_seqno, '')
        await self.send(pkt)
        await self.log('ACK', data)

    async def evaulate_testcase(self):
        assert self.test_idx < len(self.testcases)
        expected_msg = self.testcases[self.test_idx]
        # print(self.message)
        if expected_msg == self.message:
            self.success_test.append(self.test_idx)
            self.grade += self.testcases_ranks[self.test_idx]
        else:
            self.failed_test.append(self.test_idx)
        self.test_idx += 1
        self.message = ''
        self.next_seqno = 0

    async def teardown(self):
        print('[TEST CASES]: %d/%d PASSED' %
              (len(self.success_test), len(self.testcases)))
        if len(self.failed_test) == 0:
            print('ACCEPT')
        else:
            print('PARTIALLY_ACCEPTED')
        print('PASSED TESTS: %s' % self.success_test)
        print('FAILED TESTS: %s' % self.failed_test)
        print('GRADE: %d' % self.grade)

    async def log(self, act, data):
        if not self.verbose:
            return
        if act == 'ACK':
            logger.info('[ACK]: Sending ackno %d on received message %s' % (
                self.next_seqno, self.message[data['absno']]))
        elif act == 'DISCARD':
            logger.warning('[DISCARD]: Invalid seqno %d, expected %d' % (
                data['seqno'], self.next_seqno))
        elif act == 'LOST':
            logger.warning('[LOST]: seqno %d on message %s is lost' %
                           (data['seqno'], data['message']))


async def main():
    receiver = GBNReceiver()
    await receiver.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
