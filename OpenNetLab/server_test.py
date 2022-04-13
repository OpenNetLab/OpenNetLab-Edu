from server_node import ServerNode, SocketType

class MyServerNode(ServerNode):
    def recv_callback(self, data):
        print(data)

# test locally
if __name__ == '__main__':
    serv = MyServerNode('localhost', 9002, 'localhost', 9001, SocketType.UDP)
    serv.receive_process()
