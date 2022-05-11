import argparse

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--local', metavar='host:port',
                        help='specify local port', required=True)
    parser.add_argument('-r', '--remote', metavar='host:port',
                        help='specify remote port', required=True)
    args = parser.parse_args()
    host, port = args.local.split(':')
    port = int(port)
    remote_host, remote_port = args.remote.split(':')
    remote_port = int(remote_port)
    return (host, int(port), remote_host, int(remote_port))
