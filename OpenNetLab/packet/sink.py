from .. import sim
from ..sim import Environment

class PacketSink:
    def __init__(
        self,
        env: 'Environment',
        rec_arrivals: bool = True,
        abs_arrivals: bool = True,
        rec_waits: bool = True,
        rec_flow_ids: bool = True,
        debug: bool = True,
    ):
