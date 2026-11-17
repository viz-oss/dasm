"""
Symbol table and name resolution (runs after parsing and macro expansion).

The parser only produces syntax. This module checks and links names:

  collect(ast)  -> SymbolTable   labels, with signature checks
  resolve(ast)  -> AST           new tree in which every Arg knows its register

Nodes are frozen, so resolve() builds new nodes with dataclasses.replace
instead of mutating anything. Run it AFTER macro expansion, because macros
may generate labels (gensym) and calls.

Nodes carry no source positions yet, so errors here have no line/column.
Adding `pos` to Label, Call and Ptr is the next step for better messages.
"""

from __future__ import annotations
from dataclasses import dataclass, replace
import logging
logger = logging.getLogger(__name__)

from .abstract import Arg, Call, Label, Mov, Ptr, Start
from .exceptions import DasmSyntaxError
from .syntax import AST


@dataclass(frozen=True)
class SymbolTable:
    labels: dict[str, Label]            # name -> definition
    externs: frozenset[str]             # names defined outside this program


# --- collecting --------------------------------------------------------------

def _check_signature(label: Label) -> None:
    names: set[str] = set()
    regs: set[int] = set()
    for p in label.params:
        if p.name in names:
            raise DasmSyntaxError(
                message=f"label '{label.name}': duplicate parameter '{p.name}'")
        if p.reg.n in regs:
            raise DasmSyntaxError(
                message=f"label '{label.name}': register r{p.reg.n} used by more than one parameter")
        names.add(p.name)
        regs.add(p.reg.n)


def collect(ast: AST, externs: frozenset[str] | set[str] = frozenset()) -> SymbolTable:
    """Gather all labels. Labels are flat and global, so duplicates are errors."""
    labels: dict[str, Label] = {}
    for node in ast:
        if isinstance(node, Label):
            if node.name in labels:
                raise DasmSyntaxError(message=f"label '{node.name}' defined twice")
            _check_signature(node)
            logger.info(f"Collect '{node.name}' = {node}")
            labels[node.name] = node

    clash = labels.keys() & set(externs)
    if clash:
        raise DasmSyntaxError(message=f"extern symbol defined in this program: {sorted(clash)}")
    return SymbolTable(labels, frozenset(externs))


# --- resolving ---------------------------------------------------------------

def _check_symbol(table: SymbolTable, name: str, where: str) -> None:
    if name not in table.labels and name not in table.externs:
        raise DasmSyntaxError(message=f"{where}: unknown symbol '{name}'")
    logger.info(f"Check symbol {name} @ {where}")


def _check_operand(table: SymbolTable, operand, where: str) -> None:
    # Ptr with an Int target is a literal address: nothing to resolve
    if isinstance(operand, Ptr) and isinstance(operand.target, str):
        _check_symbol(table, operand.target, where)


def _resolve_call(table: SymbolTable, call: Call, require_all_args: bool) -> Call:
    label = table.labels.get(call.target)
    if label is None:
        if call.target in table.externs:
            if call.args:
                # an extern has no signature here, so names cannot be mapped to registers
                raise DasmSyntaxError(
                    message=f"call to extern '{call.target}' cannot take named arguments "
                            f"(no signature available)")
            return call
        raise DasmSyntaxError(message=f"call: unknown label '{call.target}'")

    params = {p.name: p for p in label.params}
    seen: set[str] = set()
    args: list[Arg] = []
    for a in call.args:
        if a.name not in params:
            raise DasmSyntaxError(
                message=f"call to '{call.target}': unknown parameter '{a.name}'")
        if a.name in seen:
            raise DasmSyntaxError(
                message=f"call to '{call.target}': duplicate argument '{a.name}'")
        seen.add(a.name)
        _check_operand(table, a.value, f"call to '{call.target}', argument '{a.name}'")
        logger.info(f"Resolve call {a} = {params[a.name].reg}")
        args.append(replace(a, reg=params[a.name].reg))

    if require_all_args:
        missing = [n for n in params if n not in seen]
        if missing:
            raise DasmSyntaxError(message=f"call to '{call.target}': missing arguments {missing}")

    return replace(call, args=tuple(args))


def resolve(ast: AST, externs: frozenset[str] | set[str] = frozenset(), require_all_args: bool = True) -> AST:
    """Validate names and return a new AST with Arg.reg filled in.

    externs:          symbols defined elsewhere (linker resolves them).
    require_all_args: a call must pass every parameter of the label.
    """
    table = collect(ast, externs)
    out = []

    for node in ast:
        if isinstance(node, Call):
            node = _resolve_call(table, node, require_all_args)
            if node.result is not None and node.target in table.labels:
                pass    # result register is chosen by the caller; nothing to check yet
        elif isinstance(node, Mov):
            _check_operand(table, node.to, "assignment target")
            _check_operand(table, node.fr, "assignment source")
        elif isinstance(node, Start):
            if node.target not in table.labels:
                raise DasmSyntaxError(message=f".start: unknown label '{node.target}'")
        out.append(node)

    return AST(out)
