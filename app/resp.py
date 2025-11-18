#from typing_extensions import override

from abc import ABC, abstractmethod
from enum import Enum, auto

class RESPType(Enum):
    RESP_BULK_STRING = auto()

class RESPValue(ABC):
    """A base class for all representable RESP types."""

    @abstractmethod
    def encode(self) -> bytes:
        """Serialies the object into its RESP byte representation."""
        pass

    @abstractmethod
    def resp_type(self) -> RESPType:
        pass

class RESPBulkString(RESPValue):
    """A class representing a bulk binary string"""

    def __init__(self, value: bytes):
        self.value = value

    # @override
    def encode(self) -> bytes:
        return f"${len(self.value)}\r\n".encode() + self.value + "\r\n".encode()

    # @override
    def resp_type(self) -> RESPType:
        return RESPType.RESP_BULK_STRING

    def data(self) -> bytes:
        return self.value