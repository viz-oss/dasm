"""
AST classes.

All nodes are immutable (frozen, slots), hence hashable and comparable.
Macros and resolve() create new nodes (dataclasses.replace) instead of
mutating existing ones.
"""

from dataclasses import dataclass


# --- values ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Reg:
    """rN

    Virtual register.
    """
    n: int


@dataclass(frozen=True, slots=True)
class Int:
    """Integer literal (undefined abstract range)."""
    value: int


@dataclass(frozen=True, slots=True)
class Ptr:
    """<name> or <number>   (as an operand of Mov / Arg)

    Reference to memory. The target is a symbol name (str) or a literal
    address (Int). Created by the parser from a bare name or, on the left
    side of '=', from a bare number.
    """
    target: str | Int


# --- statements ----------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Mov:
    """<to> = <fr>

    Assign.
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


# --- labels and calls ------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Param:
    """name: rN   (in a label definition)

    Declares which virtual register receives the parameter `name`.
    """
    name: str
    reg: Reg


@dataclass(frozen=True, slots=True)
class Label:
    """name:  or  name(p1: r0, p2: r1):"""
    name: str
    params: tuple[Param, ...] = ()


@dataclass(frozen=True, slots=True)
class Arg:
    """<name> = <value>   (inside a call)

    Value passed to the parameter `name` declared in the target's label.
    The register is NOT known to the parser; resolve() fills `reg` from
    the label's Param by creating a new node (dataclasses.replace).
    """
    name: str
    value: Reg | Int | Ptr
    reg: Reg | None = None


@dataclass(frozen=True, slots=True)
class Call:
    """name(...)  or  r<N> = name(...)

    `result` is the register receiving the value of `return <int>`;
    None means the result is discarded.
    Arguments are passed in parallel, not sequentially.
    """
    target: str
    args: tuple[Arg, ...] = ()
    result: Reg | None = None


@dataclass(frozen=True, slots=True)
class Return:
    """return  or  return <int>

    Leaves the current call. The optional value is a literal number;
    None is intentional and means "no value".
    """
    value: Int | None = None


# --- directives --------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Start:
    """.start <label>

    Entry point of the program.
    """
    target: str


@dataclass(frozen=True, slots=True)
class Exit:
    """.exit

    Architecture-specific program exit directive.
    """


@dataclass(frozen=True, slots=True)
class Raw:
    """.raw  or  .raw(<type>) <values> [* <count>]

    type: 8, 16, 32, 64 (size in bits) or an encoding name
          ('ascii', 'utf-8', 'utf-16', 'petscii').
    values: tuple of Int for numeric types, str for encodings.
    count: the whole values list is repeated `count` times (not expanded
           here, so reserving space stays cheap).
    Not yet bytes: encoding and byte order belong to the backend.
    """
    type: int | str
    values: tuple[Int, ...] | str
    count: int = 1
