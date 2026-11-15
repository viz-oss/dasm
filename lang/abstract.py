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
class Ptr:
    """@label or @<number>

    Reference to memory. The target is a symbol name or a literal address.
    """
    target: str | Int


@dataclass(frozen=True, slots=True)
class Mov:
    """<to> = <fr>
    
    Assign
    """
    to: Reg | Ptr
    fr: Reg | Int | Ptr
    
    def to_reg(self):
        return isinstance(self.to, Reg)

    def to_ptr(self):
        return isinstance(self.to, Ptr)

    def fr_reg(self):
        return isinstance(self.fr, Reg)

    def fr_int(self):
        return isinstance(self.fr, Int)

    def fr_ptr(self):
        return isinstance(self.fr, Ptr)


@dataclass(frozen=True, slots=True)
class Param:
    """name: rN   (in a label definition)"""
    name: str
    reg: Reg


@dataclass(frozen=True, slots=True)
class Label:
    """name:  or  name(p1: r0, p2: r1):"""
    name: str
    params: tuple[Param, ...] = ()


@dataclass(frozen=False, slots=True)
class Arg:
    """<name> = <value>   (inside a call)

    Value passed to the parameter `name` declared in the target's label.
    The register is NOT known here; it comes from the label's Param.
    """
    name: str
    value: Reg | Int | Ptr
    _reg: Reg | None = None # cached register from Label's Param


@dataclass(frozen=True, slots=True)
class Call:
    """name(...)  or  r<N> = name(...)

    `result` is the register receiving the value of `return <int>`;
    None means the result is discarded.
    """
    target: str
    args: tuple[Arg, ...] = ()
    result: Reg | None = None


@dataclass(frozen=True, slots=True)
class Start:
    """.start <label>

    Entry point of the program.
    """
    target: str


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


@dataclass(frozen=True, slots=True)
class Return:
    """return  or  return <int>

    Leaves the current call. The optional value is a literal number.
    """
    value: Int | None = None
