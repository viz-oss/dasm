"""
AST classes
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Reg:
    """rN
    
    Virtual registry
    """
    n: int


@dataclass(frozen=True, slots=True)
class Int:
    """Integer number (undefined abstract range)"""
    value: int


@dataclass(frozen=True, slots=True)
class Mov:
    """r<to> = <fr>
    
    Assign
    """
    to: Reg
    fr: Reg | Int
    
    def fromReg(self):
        return isinstance(self.fr, Reg)

    def fromInt(self):
        return isinstance(self.fr, Int)


@dataclass(frozen=True, slots=True)
class Label:
    """name:
    
    Label
    """
    name: str


@dataclass(frozen=True, slots=True)
class Bytes:
    """.bN <v1>, <v2>, ...

    Values are numbers, not yet bytes. Each is emitted as `size` bytes;
    the byte order is chosen by the backend (architecture).
    """
    size: int # in bytes 1, 2, 4, 8
    values: tuple[Int, ...]


@dataclass(frozen=True, slots=True)
class Text:
    value: str
