from abc import ABC, abstractmethod

from .sim import Environment, ProcessGenerator
from .packet import Packet
from typing import Optional


class Device(ABC):
    def __init__(self):
        self._out = None
        pass

    @abstractmethod
    def run(self, env: Environment) -> ProcessGenerator:
        pass

    @abstractmethod
    def put(self, packet: Packet):
        """Put packet in this device.
        This function will be called in previous hop.
        """
        pass

    @property
    def out(self) -> Optional["Device"]:
        """The next hop of current device."""
        return self._out

    @out.setter
    def out(self, val) -> None:
        self._out = val
