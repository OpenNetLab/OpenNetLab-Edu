import asyncio
from onl.node import TCPServerNode


class Obj:
    def __init__(self, a, b) -> None:
        self.a = a
        self.b = b


class UserServer(TCPServerNode):
    async def setup(self):
        pass

    async def recv_callback(self, data):
        print(data)

    async def evaulate_testcase(self):
        pass


async def main():
    receiver = UserServer()
    await receiver.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
