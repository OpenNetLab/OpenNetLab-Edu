import asyncio
import json
import logging
import coloredlogs

from OpenNetLab.node.server import TCPServerNode
from gbn_packet import new_packet

logger = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG", fmt="%(asctime)s - %(message)s", datefmt="%H:%M:%S")

class GBNReceiver(TCPServerNode):
    seq_no_width: int
    window_size: int
    next_msg_idx: int
    loss_rate: float
    message: str = ''

    async def setup(self):
        with open('./lab_config.json') as fp:
            cfg = json.load(fp)
            self.next_msg_idx = 0
            self.seq_no_width = int(cfg['seq_no_width'])
            self.loss_rate = float(cfg['loss_rate'])
            self.window_size = (2**self.seq_no_width) - 1
            self.next_seqno = 0

    async def recv_callback(self, data):
        seqno = data['seqno']
        if seqno != self.next_seqno:
            logger.warning('[DISCARD]: Invalid packet %s with seqno %d' % (data, seqno))
            return
        self.message += data['message']
        self.next_seqno = (self.next_seqno + 1) % self.window_size
        pkt = new_packet(0, self.next_seqno, '')
        await self.send(pkt)
        logger.info('[SEND]: Sending ackno %d on message %s' % (self.next_seqno, data['message']))

    async def teardown(self):
        logger.info('[MESSAGE]: %s' % self.message)

async def main():
    receiver = GBNReceiver('localhost', 9001, 'localhost', 9002)
    await receiver.run()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
