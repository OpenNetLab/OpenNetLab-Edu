import argparse
import re
import sys


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--local', metavar=('host', 'port'),
                        help='specify local port', nargs=2, required=True)
    parser.add_argument('-r', '--remote', metavar=('host', 'port'),
                        help='specify remote port', nargs=2, required=True)
    args = parser.parse_args()
    host, port = args.local
    remote_host, remote_port = args.remote
    # ipv4_regex = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[^0-9]|localhost)'
    # port_regex = r'^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$'
    # valid = True
    # if not re.match(ipv4_regex, host) or not re.match(port_regex, port):
    #     print('local address is invalid')
    #     valid = False
    # if not re.match(ipv4_regex, remote_host) or not re.match(port_regex, remote_port):
    #     print('remote address is invalid')
    #     valid = False
    # if not valid:
    #     sys.exit(1)
    return (host, int(port), remote_host, int(remote_port))


def override(f):
    return f
