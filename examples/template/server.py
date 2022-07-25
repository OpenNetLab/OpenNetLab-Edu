from OpenNetLab.node import TCPServerNode

class UserServer(TCPServerNode):
    async def setup(self):
        pass

    async def recv_callback(self):
        pass

    async def evaulate_testcase(self):
        pass

    async def teardown(self):
        pass


async def main():
    receiver = UserServer()
    await receiver.run()
