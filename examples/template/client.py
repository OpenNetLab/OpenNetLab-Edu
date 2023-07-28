import asyncio
from onl.node import TCPClientNode


class Obj:
    def __init__(self, a, b) -> None:
        self.a = a
        self.b = b


class UserClient(TCPClientNode):
    async def setup(self):
        pass

    async def testcase_handler(self):
        await self.send(1234)
        await self.send(b'\x11\x11\x11')
        await self.send({'a': 12, 'b': 22})
        await self.send(Obj(13, 'abc'))
        return True


async def main():
    sender = UserClient()
    await sender.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
