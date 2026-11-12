"""Unit tests for the MOS 6502/6510 architecture."""

import pytest

from arch.mos import MOSArchitecture
from lang.abstract import Bytes, Call, Int, Label


def test_call_backward_label():
    arch = MOSArchitecture()
    ast = [
        Label('start'),
        Bytes(1, (Int(0x60),)),
        Call('start'),
    ]

    words = arch.assembly(ast, origin=0x080D)

    assert words == [0x60, 0x4C, 0x0D, 0x08]


def test_call_forward_label():
    arch = MOSArchitecture()
    ast = [
        Call('start'),
        Label('start'),
        Bytes(1, (Int(0x60),)),
    ]

    words = arch.assembly(ast, origin=0x080D)

    assert words == [0x4C, 0x10, 0x08, 0x60]


def test_call_uses_origin():
    arch = MOSArchitecture()
    ast = [
        Call('start'),
        Label('start'),
    ]

    words = arch.assembly(ast, origin=0)

    assert words == [0x4C, 0x03, 0x00]


def test_call_undefined_label():
    arch = MOSArchitecture()

    with pytest.raises(ValueError, match='Undefined label: missing'):
        arch.assembly([Call('missing')])


def test_duplicate_label():
    arch = MOSArchitecture()

    with pytest.raises(ValueError, match='Duplicate label: start'):
        arch.assembly([Label('start'), Label('start')])
