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
        # remote DNS server地址
        self.name_server = ('223.5.5.5', 53)
        # trans字典：通过DNS响应的ID来获得原始的DNS数据包发送方
        self.trans = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('', 1088))
        self.server_socket.setblocking(False)
        self._loop.create_task(self.not_found_task())

    async def not_found_task(self):
        buffer_size = 512
        while True:
            # data = self.server_socket.recv(buffer_size)
            data = await self._loop.sock_recv(self.server_socket, buffer_size)
            # print('recv from server:', data)
            await self.send(data)

    async def recv_callback(self, data):
        # print('recv from client:', data)
        recvdp = DNSPacket(data)
        # QUERY
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
