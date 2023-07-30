from typing import Optional

from .application import Application
from ..device import Device
from ..sim import Environment

class Node:
    def __init__(self, env: Environment):
        self._env = env
        self._app: Optional[Application] = None
        self._outbound: Optional[Device] = None
        self._inbound: Optional[Device] = None

    def set_application(self, app: Application):
        """Set application for this node
        """
        self._app = app
        app._node = self

    def set_inbound(self, dev: Device):
        """Set packet for this node.
        Packet will be received from this device.
        """
        self._inbound = dev

    def set_outbound(self, dev: Device):
        """Set packet for this node.
        Packet will be sent through this device.
        """
        self._outbound = dev

    def run(self):
        if not self._app:
            raise ValueError("application must be set before run")
        if not self._outbound:
            raise ValueError("output device must be set before run")
        self._env.process(self._app.start_application(self._env))
