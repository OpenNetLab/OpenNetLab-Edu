import socket
from OpenNetLab.node import TCPServerNode

from dns_packet import DNSPacket


class DNSServer(TCPServerNode):
    async def setup(self):
        pass

    async def recv_callback(self, data):
        pass

    async def evaulate_testcase(self):
        pass

    async def teardown(self):
        pass


class StudentDNSServer(DNSServer):
    async def setup(self):
        await super().setup()
        # url_IP字典:通过域名查询ID
        self.url_ip = {}
        # 读取配置文件
        self.cache_file = 'exmaple.txt'
        self.load_file()
        # remote DNS server地址
        self.name_server = ('223.5.5.5', 53)
        # trans字典：通过DNS响应的ID来获得原始的DNS数据包发送方
        self.trans = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    async def recv_callback(self, data):
        recvdp = DNSPacket(data)
        if recvdp.QR == 0:  # and RecvDp.qtype == 1
            name = recvdp.name
            if name in self.url_ip:
                ip = self.url_ip[name]
                if ip != '0.0.0.0':
                    res = recvdp.generate_response(ip, False)
                else:
                    res = recvdp.generate_response(ip, True)
                await self.send(res)
            else:
                self.server_socket.sendto(data, self.name_server)

        if recvdp.QR == 1:
            await self.send(data)

    def load_file(self):
        f = open(self.cache_file, 'r', encoding='utf-8')
        for line in f:
            ip, name = line.split(' ')
            self.url_ip[name.strip('\n')] = ip
        f.close()


async def main():
    receiver = DNSServer()
    await receiver.run()
