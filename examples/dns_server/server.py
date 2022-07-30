import socket
import threading
from dns_packet import DNSPacket


class DNS_Relay_Server:  # 一个relay server实例，通过缓存文件和外部地址来初始化
    def __init__(self, cache_file, name_server):
        # url_IP字典:通过域名查询ID
        self.url_ip = {}
        self.cache_file = cache_file
        self.load_file()
        self.name_server = name_server
        # trans字典：通过DNS响应的ID来获得原始的DNS数据包发送方
        self.trans = {}

    def load_file(self):
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            for line in f:
                ip, name = line.strip().split(' ')
                self.url_ip[name] = ip

    def run(self):
        buffer_size = 512
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('', 1234))
        server_socket.setblocking(True)
        while True:
            try:
                data, addr = server_socket.recvfrom(buffer_size)
                threading.Thread(target=self.handle, args=(
                    server_socket, data, addr)).start()
            except KeyboardInterrupt:
                return
            except:
                continue

    def handle(self, server_socket, data, addr):
        recvdp = DNSPacket(data)
        print("receive DNS packet from "+str(addr)+" for "+recvdp.name)
        if recvdp.QR == 0:  # and RecvDp.qtype == 1
            name = recvdp.name
            #print("query url:"+name)
            if name in self.url_ip:
                ip = self.url_ip[name]
                #print('ip '+ip)
                if ip != '0.0.0.0':
                   # print("reply")
                    res = recvdp.generate_response(ip, False)
                else:
                    #print("reply 0")
                    res = recvdp.generate_response(ip, True)
                print("resolve "+name+" with "+ip)
                server_socket.sendto(res, addr)
            else:
                self.trans[recvdp.ID] = addr, name
                server_socket.sendto(data, self.name_server)

        if recvdp.QR == 1:
            if self.trans.get(recvdp.ID) != None:
                src_ip, name = self.trans[recvdp.ID]
                print("relay reply  "+ name + " to", src_ip)
                server_socket.sendto(data, src_ip)
                self.trans.pop(recvdp.ID)


if __name__ == '__main__':
    cache_file = 'example.txt'
    name_server = ('223.5.5.5', 53)
    relay_server = DNS_Relay_Server(
        cache_file, name_server)  # 构造一个DNS_Relay_Server实例
    relay_server.run()
