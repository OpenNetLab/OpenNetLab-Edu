import asyncio
import json
from datetime import datetime

from OpenNetLab.node.server import TCPServerNode
from sr_packet import new_packet
from sr_logger import logger

class GBNReceiver(TCPServerNode):
    async def setup(self):
        with open('./lab_config.json') as fp:
            cfg = json.load(fp)
            # lab
            self.next_msg_idx = 0
            self.seq_no_width = int(cfg['seqno_width'])
            self.loss_rate = float(cfg['loss_rate'])
            self.max_delay = int(cfg['max_delay'])
            self.seqno_range = 2**self.seq_no_width
            self.window_size = self.seqno_range // 2
            self.next_seqno = 0
            self.message = ''
            self.recv_window = [None for _ in range(self.window_size)]
            self.recv_start = 0
            # test
            self.test_idx = 0
            self.testcases = cfg['testcases']
            self.failed_test = []
            self.success_test = []
            # record
            self.recorder.set_headers(
                ('time', 'absno', 'seqno', 'message', 'status'))
            self.verbose = False

    def is_valid_seqno(self, seqno):
        last_seqno = (seqno + self.window_size - 1)
        if last_seqno <= self.seqno_range - 1:
            return self.next_seqno <= seqno <= last_seqno
        return (0 <= seqno <= last_seqno) or (self.next_seqno <= seqno <= self.seqno_range - 1)

    async def recv_callback(self, data):
        if data['absno'] < len(self.message):
            pkt = new_packet(0, 0, self.next_seqno, '')
            await self.send(pkt)
            await self.log('ACK', data)
            await self.record('DUP', data)
            return
        seqno = data['seqno']
        if not self.is_valid_seqno(seqno):
            await self.log('DISCARD', data)
            await self.record('DISCARD', data)
            return
        rel_idx = ((seqno + self.seqno_range) - self.next_seqno) % self.window_size
        await self.record('RCVD', data)
        pkt = new_packet(0, 0, self.next_seqno, '')
        await self.send(pkt)
        await self.log('ACK', data)

    async def evaulate_testcase(self):
        assert self.test_idx < len(self.testcases)
        expected_msg = self.testcases[self.test_idx]
        # print(self.message)
        if expected_msg == self.message:
            self.success_test.append(self.test_idx)
            print('TESTCASE %d PASSED' % self.test_idx)
        else:
            self.failed_test.append(self.test_idx)
            print('TESTCASE %d FAILED' % self.test_idx)
        self.test_idx += 1
        self.message = ''
        self.next_seqno = 0

    async def teardown(self):
        print('[TEST CASES]: %d/%d PASSED' %
              (len(self.success_test), len(self.testcases)))
        print('PASSED TESTS: %s' % self.success_test)
        print('FAILED TESTS: %s' % self.failed_test)

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

    async def record(self, act, data):
        self.recorder.add_record(self.test_idx, (datetime.now().strftime(
            '%H:%M:%S.%f'), data['absno'], self.next_seqno, data['message'], act))


async def main():
    receiver = GBNReceiver()
    await receiver.run()

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
