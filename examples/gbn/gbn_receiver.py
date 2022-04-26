import asyncio
import json
import random
import logging
import coloredlogs

from OpenNetLab.node.server import TCPServerNode
from gbn_packet import new_packet

logger = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG", fmt="%(asctime)s - %(message)s", datefmt="%H:%M:%S")

class GBNReceiver(TCPServerNode):
    async def setup(self):
        with open('./lab_config.json') as fp:
            cfg = json.load(fp)
            self.next_msg_idx = 0
            self.seq_no_width = int(cfg['seqno_width'])
            self.loss_rate = float(cfg['loss_rate'])
            self.seqno_range = 2**self.seq_no_width
            self.window_size = self.seqno_range - 1
            self.next_seqno = 0
            self.message = ''

    async def recv_callback(self, data):
        if data['absno'] < len(self.message):
            pkt = new_packet(0, 0, (data['absno'] + 1) % self.seqno_range, '')
            await self.send(pkt)
            logger.info('[ACK]: Sending ackno %d on received message %s' % (self.next_seqno, self.message[data['absno']]))
        if data['seqno'] != self.next_seqno:
            logger.warning('[DISCARD]: Invalid seqno %d, expected %d' % (data['seqno'], self.next_seqno))
            return
        if self.is_loss():
            logger.warning('[LOST]: seqno %d on message %s is lost' % (data['seqno'], data['message']))
            return
        self.message += data['message']
        self.next_seqno = (self.next_seqno + 1) % self.seqno_range
        pkt = new_packet(0, 0, self.next_seqno, '')
        # print(self.message)
        if not self.is_loss():
            await self.send(pkt)
            logger.info('[ACK]: Sending ackno %d on message %s' % (self.next_seqno, data['message']))

    async def teardown(self):
        logger.info('[MESSAGE]: %s' % self.message)

    def is_loss(self):
        return random.random() < self.loss_rate


async def main():
    receiver = GBNReceiver('localhost', 9001, 'localhost', 9002)
    await receiver.run()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
