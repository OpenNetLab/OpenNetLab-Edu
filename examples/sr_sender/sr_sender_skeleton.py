import asyncio
import json

from onl.node.client import TCPClientNode


class SRSender(TCPClientNode):
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


class StudentSRSender(SRSender):
    async def setup(self):
        await super().setup()
        """
        @TODO: setup user data structure
        """

    async def student_task(self, message):
        """
        @TODO: main sr sender logic
        """


async def main():
    sender = StudentSRSender()
    await sender.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
