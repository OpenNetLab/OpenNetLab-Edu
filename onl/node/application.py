from abc import ABC, abstractmethod
from typing import Optional, Any

from .node import Node
from ..packet import Packet
from ..device import Device
from ..sim import Environment, ProcessGenerator

class Application(ABC):
    def __init__(self):
        self._node: Optional[Node] = None
        self._env: Optional[Environment] = None
        pass

    @property
    def inbound(self) -> Device:
        if not self._node:
            raise ValueError("node has not been set for application")
        if not self._node._inbound:
            raise ValueError("outbound of node has not been set yet")
        return self._node._inbound

    @property
    def outbound(self) -> Device:
        if not self._node:
            raise ValueError("node has not been set for application")
        if not self._node._outbound:
            raise ValueError("outbound of node has not been set yet")
        return self._node._outbound

    @abstractmethod
    def start_application(self, env: Environment) -> ProcessGenerator:
        pass

    @abstractmethod
    def stop_application(self):
        pass
