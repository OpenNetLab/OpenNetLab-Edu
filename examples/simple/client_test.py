import asyncio

from OpenNetLab.node.client import *

class Foo:
    def __init__(self, foo: int, bar: int):
        self.foo = foo
        self.bar = bar

    def __str__(self) -> str:
        return 'foo: %d   bar: %d\n' % (self.foo, self.bar)

class MyOwnClientNode(TCPClientNode):
    async def run(self):
        await self.connect()
        await self.send(1000)
        await self.send('this is some text')
        await self.send({'nice': '????', '4': 432434})
        await self.send(Foo(12, 13))
        cnt = 0
        while cnt < 3:
            data = await self.recv_next_packet()
            if data:
                print(data)
                cnt += 1
            await asyncio.sleep(0.01)
        await self.finish()

if __name__ == '__main__':
    cli = MyOwnClientNode('localhost', 9001, 'localhost', 9002)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cli.run())
