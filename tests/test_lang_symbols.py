"""Unit tests for symbol collection and semantic resolution."""

import pytest

from lang.abstract import Arg, Call, Int, Reg
from lang.exceptions import DasmSyntaxError
from lang.symbols import resolve
from lang.syntax import parse


def test_resolve_fills_argument_registers_without_mutating_parser_ast():
    parsed = parse("foo(value: r3):\nfoo(value = 7)\n")

    resolved = resolve(parsed)

    assert parsed[1] == Call("foo", (Arg("value", Int(7)),))
    assert resolved[1] == Call("foo", (Arg("value", Int(7), reg=Reg(3)),))


def test_resolve_rejects_unknown_label():
    with pytest.raises(DasmSyntaxError, match="call: unknown label 'missing'"):
        resolve(parse("missing()\n"))


def test_resolve_rejects_missing_argument():
    with pytest.raises(DasmSyntaxError, match="missing arguments \\['value'\\]"):
        resolve(parse("foo(value: r0):\nfoo()\n"))


def test_resolve_rejects_unknown_pointer_symbol():
    with pytest.raises(DasmSyntaxError, match="unknown symbol 'missing'"):
        resolve(parse("foo:\nr0 = missing\n"))


def test_resolve_allows_external_call_without_signature():
    resolved = resolve(parse("external()\n"), externs={"external"})

    assert resolved == parse("external()\n")


def test_resolve_rejects_duplicate_label_definitions():
    with pytest.raises(DasmSyntaxError, match="label 'foo' defined twice"):
        resolve(parse("foo:\nfoo:\n"))
