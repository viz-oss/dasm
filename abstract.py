"""
AST classes
"""

from dataclasses import dataclass

@dataclass
class Reg:
    """Virtual registry
    rN
    """
    n: int

@dataclass
class Int:
    """Integer number (undefined abstract range)"""
    value: int

@dataclass
class Mov:
    """Assign
    r<to> = <fr>
    """
    to: Reg
    fr: Reg | Int
