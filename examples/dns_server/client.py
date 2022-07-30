import socket
from dns_packet import DNSPacket

urls = []
expected_rcode = []
expected_ip = []
with open('./example.txt') as f:
    for line in f:
        ip, url = line.strip().split(' ')
        urls.append(url)
        expected_rcode.append(3 if ip == '0.0.0.0' else 0)
        expected_ip.append(ip)


right_comb = (
    ('www.baidu.com', 0, 'any'),
    ('www.douban.com', 0, 'any'),
    ('www.youdao.com', 0, 'any')
)

for comb in right_comb:
    urls.append(comb[0])
    expected_rcode.append(comb[1])
    expected_ip.append(comb[2])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 4321))

def decode_ip(data: bytes) -> str:
    ip_tup = []
    ip_tup.append(str(data[-4]))
    ip_tup.append(str(data[-3]))
    ip_tup.append(str(data[-2]))
    ip_tup.append(str(data[-1]))
    return '.'.join(ip_tup)

for idx, url in enumerate(urls):
    # print(q.pack())
    sock.sendto(DNSPacket.generate_request(url), ('', 1234))
    data = sock.recv(512)
    p = DNSPacket(data)
    if p.RCODE != expected_rcode[idx]:
        print('false rcode for url', url)
    if p.RCODE == 0:
        ip = decode_ip(data)
        if expected_ip[idx] != ip and expected_ip[idx] != 'any':
            print('false ip for url', url)
            print(f'expected: {expected_ip[idx]}, actual: {ip}')
