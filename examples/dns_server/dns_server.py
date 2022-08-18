import socket
from OpenNetLab.node import TCPServerNode
import asyncio

from dns_packet import DNSPacket


class DNSServer(TCPServerNode):
    async def setup(self):
        await super().setup()
        # url_IP字典:通过域名查询ID
        self.url_ip = {}
        # 读取配置文件
        self.load_file()
        # public DNS server地址
        self.name_server = ('223.5.5.5', 53)
        # trans字典：通过DNS响应的ID来获得原始的DNS数据包发送方
        self.trans = {}
        # 创建与public DNS server通信的socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('', 1088))
        self.server_socket.setblocking(False)
        self._loop.create_task(self.not_found_task())

    async def not_found_task(self):
        buffer_size = 512
        while True:
            # 从public DNS server接收DNS应答
            data = await self._loop.sock_recv(self.server_socket, buffer_size)
            print(data)
            # 将DNS应答转发给client
            await self.send(data)

    async def recv_callback(self, data: bytes):
        '''
        TODO: 处理DNS请求，data参数为DNS请求数据包对应的字节流
        1. 解析data得到构建应答数据包所需要的字段
        2. 根据请求中的domain name进行相应的处理:
            2.1 如果domain name在self.url_ip中，构建对应的应答数据包，发送给客户端
            2.2 如果domain name不再self.url_ip中，将DNS请求发送给public DNS server
        '''
        recvdp = DNSPacket(data)
        if recvdp.QR == 0:  # and RecvDp.qtype == 1
            name = recvdp.name
            print(f'query url: {name}')
            if name in self.url_ip:
                ip = self.url_ip[name]
                print('ip:', ip)
                if ip != '0.0.0.0':
                    print("reply")
                    res = recvdp.generate_response(ip, False)
                else:
                    print("reply 0")
                    res = recvdp.generate_response(ip, True)
                print(f'resolve {name} with {ip}')
                await self.send(res)
            else:
                self.server_socket.sendto(data, self.name_server)

    def load_file(self):
        # 读取配置文件并且建立 Domain Name -> IP 的映射
        with open('./example.txt', 'r', encoding='utf-8') as f:
            for line in f:
                ip, name = line.split(' ')
                self.url_ip[name.strip('\n')] = ip


async def main():
    receiver = DNSServer()
    await receiver.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
