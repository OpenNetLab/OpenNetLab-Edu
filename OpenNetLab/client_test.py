from OpenNetLab.node.client import *

class MyOwnClientNode(ClientNode):
    def testcase_handler(self, filename):
        pass

if __name__ == '__main__':
    cli = ClientNode('localhost', 9001, 'localhost', 9002, SocketType.UDP)
    cli.send('haha')
    cli.send({'nice': '????', '4': 432434})
    cli.finish()
