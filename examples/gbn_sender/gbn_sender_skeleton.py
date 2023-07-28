import asyncio
import json
from collections import deque

from onl.node import TCPClientNode
from onl.utils import Timer
from gbn_packet import new_packet


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

    async def send_message(self, message):
        pass

    async def testcase_handler(self) -> bool:
        assert self.test_idx < len(self.testcases)
        message = self.testcases[self.test_idx]
        ret = await self.send_message(message)
        ret = False
        if self.test_idx == len(self.testcases) - 1:
            ret = True
        self.test_idx += 1
        return ret


class GBNSender(BaseGBNSender):
    async def setup(self):
        await super().setup()
        '''
        TODO: 创建你自己所需要的数据结构
        '''

    async def send_message(self, message: str):
        '''
        TODO: message是一个字符串，将message中每个字符封装为帧以GBN协议发送给接收方。
        '''
        pass


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
