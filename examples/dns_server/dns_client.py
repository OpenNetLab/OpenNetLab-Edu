from OpenNetLab.node import TCPClientNode
import json
from dns_packet import DNSPacket
import asyncio


def decode_ip(data: bytes) -> str:
    ip_tup = []
    ip_tup.append(str(data[-4]))
    ip_tup.append(str(data[-3]))
    ip_tup.append(str(data[-2]))
    ip_tup.append(str(data[-1]))
    return '.'.join(ip_tup)


class DNSClient(TCPClientNode):
    async def setup(self):
        with open('./lab_config.json', 'r') as fp:
            self.testcases = json.load(fp)['testcases']
        self.test_idx = 0
        self.rank = 0

    async def testcase_handler(self):
        assert self.test_idx < len(self.testcases)
        objs = self.testcases[self.test_idx]
        judge_res = True
        for obj in objs:
            await self.send(DNSPacket.generate_request(obj['url']))
            resp = await self.recv_data()
            p = DNSPacket(resp)
            if p.RCODE != obj['rcode']:
                judge_res = False
            if p.RCODE == 0:
                ip = decode_ip(resp)
                if obj['ip'] != ip and obj['ip'] != 'any':
                    judge_res = False
        if judge_res:
            print(f'TESTCASE {self.test_idx} PASSED')
        ret = False
        if self.test_idx == len(self.testcases) - 1:
            ret = True
        self.test_idx += 1
        return ret


async def main():
    sender = DNSClient()
    await sender.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as _:
        print('keyboard interrupt accept, exit')
    except Exception as _:
        raise
