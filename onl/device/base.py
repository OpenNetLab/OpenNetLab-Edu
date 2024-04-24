from abc import ABC, abstractmethod

from typing import Optional


class Device(ABC):
    def put(self, packet):
        """Put packet in this device.
        This function will be called in previous hop.
        """
        pass

    @property
    def element_id(self):
        return self._element_id

    @element_id.setter
    def element_id(self, val):
        self._element_id = val


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


class SingleDevice(Device, OutMixIn):
    def __init__(self):
        pass
