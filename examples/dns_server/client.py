import socket
from dnslib import DNSRecord
from dns_packet import DNSPacket

urls = ['www.baidu.com', 'www.jdklfjdslfjsdklf.com',
        'pic1.zhimg.com']

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 4321))


for url in urls:
    q = DNSRecord.question(url)
    # print(q.pack())
    sock.sendto(q.pack(), ('', 1234))
    data = sock.recv(512)
    p = DNSPacket(data)
    print(p.RCODE)
