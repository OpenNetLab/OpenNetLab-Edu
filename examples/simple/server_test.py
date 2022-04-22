from OpenNetLab.node.server import TCPServerNode

class MyServerNode(TCPServerNode):
    def recv_callback(self, data):
        print(data)

# test locally
if __name__ == '__main__':
    serv = MyServerNode('localhost', 9002, 'localhost', 9001)
    serv.run()
