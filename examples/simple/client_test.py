import asyncio

from OpenNetLab.node.client import *

class MyOwnClientNode(TCPClientNode):
    async def run(self):
        await self.connect()
        await self.send(1000)
        await self.send('this is some text')
        await self.send({'nice': '????', '4': 432434})
        await self.finish()

if __name__ == '__main__':
    cli = MyOwnClientNode('localhost', 9001, 'localhost', 9002)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cli.run())
