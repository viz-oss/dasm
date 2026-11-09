"""
AST classes
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Reg:
    """Virtual registry
    rN
    """
    n: int


@dataclass(frozen=True, slots=True)
class Int:
    """Integer number (undefined abstract range)"""
    value: int


@dataclass(frozen=True, slots=True)
class Mov:
    """Assign
    r<to> = <fr>
    """
    to: Reg
    fr: Reg | Int
    
    def isReg(self):
        return isinstance(self.fr, Reg)

    def isInt(self):
        return isinstance(self.fr, Int)


@dataclass(frozen=True, slots=True)
class Label:
    """Label
    name:
    """
    name: str
