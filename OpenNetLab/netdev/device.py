from abc import ABC, abstractmethod
from ..packet import Packet
from ..sim import Environment

from typing import (
    Optional
)


class Device(ABC):

    def __init__(self):
        self._out = None
        pass

    @abstractmethod
    def run(self, env: Environment):
        pass

    @abstractmethod
    def put(self, packet: Packet) -> None:
        pass

    @property
    def out(self) -> Optional['Device']:
        return self._out

    @out.setter
    def out(self, val) -> None:
        self._out = val
