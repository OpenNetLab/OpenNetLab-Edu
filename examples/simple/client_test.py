from OpenNetLab.node.client import *

class MyOwnClientNode(TCPClientNode):
    def testcase_handler(self, filename):
        pass

if __name__ == '__main__':
    cli = TCPClientNode('localhost', 9001, 'localhost', 9002)
    cli.send('haha')
    cli.send({'nice': '????', '4': 432434})
    cli.finish()
