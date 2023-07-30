from abc import ABC, abstractmethod

from .packet import Packet
from typing import Optional


class Device(ABC):
    @abstractmethod
    def put(self, packet: Packet):
        """Put packet in this device.
        This function will be called in previous hop.
        """
        pass


class OutMixIn:
    def __init__(self):
        self._out = None

    @property
    def out(self) -> Optional["Device"]:
        """The next hop of current device."""
        return self._out

    @out.setter
    def out(self, val) -> None:
        self._out = val
