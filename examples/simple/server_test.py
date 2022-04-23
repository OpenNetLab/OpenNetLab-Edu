import asyncio

from OpenNetLab.node.server import TCPServerNode

class MyServerNode(TCPServerNode):
    async def recv_callback(self, data):
        print(data)
        await self.send(data)

# test locally
if __name__ == '__main__':
    serv = MyServerNode('localhost', 9002, 'localhost', 9001)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(serv.run())
