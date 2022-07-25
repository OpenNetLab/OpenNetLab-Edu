class DNSPacket:  # 一个DNS Frame实例，用于解析和生成DNS帧
    def __init__(self, data):
        self.default_TTL = 62
        self.data = data
        msg_addr = bytearray(data)
        # ID
        self.ID = (msg_addr[0] << 8) + msg_addr[1]
        # FLAGS
        self.QR = msg_addr[2] >> 7
        self.Opcode = (msg_addr[2] % 128) >> 3
        self.AA = (msg_addr[2] % 8) >> 2
        self.TC = (msg_addr[2] % 4) >> 1
        self.RD = msg_addr[2] % 2
        self.RA = msg_addr[3] >> 7
        self.Z = (msg_addr[3] % 128) >> 4
        self.RCODE = msg_addr[3] % 16
        # 资源记录数量
        self.QDCOUNT = (msg_addr[4] << 8) + msg_addr[5]
        self.ANCOUNT = (msg_addr[6] << 8) + msg_addr[7]
        self.NSCOUNT = (msg_addr[8] << 8) + msg_addr[9]
        self.ARCOUNT = (msg_addr[10] << 8) + msg_addr[11]
        # query内容解析
        self.name = ""
        flag = 12
        self.name_length = 0
        while msg_addr[flag] != 0x0:
            # print(self.name)
            for i in range(flag + 1, flag + msg_addr[flag] + 1):
                self.name = self.name + chr(msg_addr[i])
            self.name_length = self.name_length + msg_addr[flag] + 1
            flag = flag + msg_addr[flag] + 1
            if msg_addr[flag] != 0x0:
                self.name = self.name + "."
        self.name_length = self.name_length + 1
        # print(self.name)
        self.name.casefold()
        flag = flag + 1
        self.qtype = (msg_addr[flag] << 8) + msg_addr[flag + 1]
        self.qclass = (msg_addr[flag + 2] << 8) + msg_addr[flag + 3]

    def generate_response(self, ip, Intercepted):
        if not Intercepted:
            res = bytearray(32 + self.name_length)
            res[0] = self.ID >> 8
            res[1] = self.ID % 256
            res[2] = 0x81
            res[3] = 0x80
            res[4] = 0x0
            res[5] = 0x1
            res[6] = 0x0
            res[7] = 0x1
            res[8] = 0x0
            res[9] = 0x0
            res[10] = 0x0
            res[11] = 0x0
            for i in range(12, 16 + self.name_length):
                res[i] = self.data[i]
            flag = self.name_length + 16
            res[flag] = 0xc0
            res[flag + 1] = 0x0c
            res[flag + 2] = 0x0
            res[flag + 3] = 0x1
            res[flag + 4] = 0x0
            res[flag + 5] = 0x1
            res[flag + 6] = self.default_TTL >> 24
            res[flag + 7] = (self.default_TTL >> 16) % 256
            res[flag + 8] = (self.default_TTL >> 8) % 256
            res[flag + 9] = self.default_TTL % 256
            res[flag + 10] = 0x0
            res[flag + 11] = 0x4
            ip_tup = ip.split(sep='.')
            res[flag + 12] = int(ip_tup[0])
            res[flag + 13] = int(ip_tup[1])
            res[flag + 14] = int(ip_tup[2])
            res[flag + 15] = int(ip_tup[3])
            # print("res")
            # print(res)
            return bytes(res)

        else:
            res = bytearray(16 + self.name_length)
            res[0] = self.ID >> 8
            res[1] = self.ID % 256
            res[2] = 0x81
            res[3] = 0x83
            res[4] = 0x0
            res[5] = 0x1
            res[6] = 0x0
            res[7] = 0x0
            res[8] = 0x0
            res[9] = 0x0
            res[10] = 0x0
            res[11] = 0x0
            for i in range(12, 16 + self.name_length):
                res[i] = self.data[i]
            return bytes(res)
