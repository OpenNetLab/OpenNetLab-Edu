import asyncio
import json
from collections import deque

from OpenNetLab.node import TCPClientNode
from OpenNetLab.utils import Timer
from gbn_packet import new_packet
from gbn_logger import logger


class BaseGBNSender(TCPClientNode):
    async def setup(self):
        with open('./lab_config.json') as fp:
            cfg = json.load(fp)
            self.absno = 0
            self.seqno_width = int(cfg['seqno_width'])
            self.loss_rate = float(cfg['loss_rate'])
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
        ret = await self.student_task(message)
        ret = False
        if self.test_idx == len(self.testcases) - 1:
            ret = True
        self.test_idx += 1
        return ret


class GBNSender(BaseGBNSender):
    async def setup(self):
        await super().setup()

    async def student_task(self, message):
        for idx, c in enumerate(message):
            pkt = new_packet(idx, idx % self.seqno_range, 0, c)
            for _ in range(10):
                await self.send(pkt)
            await self.recv_next_packet()
            await asyncio.sleep(0.01)


async def main():
    sender = GBNSender()
    await sender.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
