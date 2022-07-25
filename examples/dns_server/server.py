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

    def load_file(self,):
        f = open(self.cache_file, 'r', encoding='utf-8')
        for line in f:
            ip, name = line.split(' ')
            self.url_ip[name.strip('\n')] = ip
        f.close()

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
        RecvDp = DNSPacket(data)
        print("receive DNSpackage from "+str(addr)+" for "+RecvDp.name)
        if RecvDp.QR == 0:  # and RecvDp.qtype == 1
            name = RecvDp.name
            #print("query url:"+name)
            if self.url_ip.get(name) != None:
                ip = self.url_ip[name]
                #print('ip '+ip)
                if ip != '0.0.0.0':
                   # print("reply")
                    res = RecvDp.generate_response(ip, False)
                else:
                    #print("reply 0")
                    res = RecvDp.generate_response(ip, True)
                print("resolve "+name+" with "+ip)
                server_socket.sendto(res, addr)
            else:
                self.trans[RecvDp.ID] = addr, name
                server_socket.sendto(data, self.name_server)

        if RecvDp.QR == 1:
            if self.trans.get(RecvDp.ID) != None:
                idSRC, name = self.trans[RecvDp.ID]
                print("relay reply  "+name + " to ")
                print(idSRC)
                server_socket.sendto(data, idSRC)
                self.trans.pop(RecvDp.ID)


if __name__ == '__main__':
    cache_file = 'example.txt'
    name_server = ('223.5.5.5', 53)
    relay_server = DNS_Relay_Server(
        cache_file, name_server)  # 构造一个DNS_Relay_Server实例
    relay_server.run()
