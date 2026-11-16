"""Unit tests for the MOS 6502/6510 architecture."""

import pytest

from arch.mos6502 import MOSArchitecture
from lang.abstract import Arg, Bytes, Call, Exit, Int, Label, Reg, Return, Start

def test_call_backward_label():
    arch = MOSArchitecture()
    ast = [
        Label('start'),
        Bytes(1, (Int(0x60),)),
        Call('start'),
    ]

    words = arch.assembly(ast, origin=0x080D)

    assert words == [0x60, 0x20, 0x0D, 0x08]

def test_call_forward_label():
    arch = MOSArchitecture()
    ast = [
        Call('start'),
        Label('start'),
        Bytes(1, (Int(0x60),)),
    ]

    words = arch.assembly(ast, origin=0x080D)

    assert words == [0x20, 0x10, 0x08, 0x60]


def test_call_uses_origin():
    arch = MOSArchitecture()
    ast = [
        Call('start'),
        Label('start'),
    ]

    words = arch.assembly(ast, origin=0)

    assert words == [0x20, 0x03, 0x00]


def test_call_with_args_relocates_after_arguments():
    arch = MOSArchitecture()
    ast = [
        Label('fn'),
        Call('fn', (
            Arg('a', Int(1), _reg=Reg(0)),
            Arg('b', Int(2), _reg=Reg(1)),
        )),
    ]

    words = arch.assembly(ast, origin=0x080D)

    # LDA #1, LDX #2, then JSR fn (address patched after the arguments).
    assert words == [0xA9, 0x01, 0xA2, 0x02, 0x20, 0x0D, 0x08]


def test_return_emits_rts():
    arch = MOSArchitecture()

    assert arch.assembly([Return()]) == [0x60]


def test_exit_emits_rts():
    arch = MOSArchitecture()

    assert arch.assembly([Exit()]) == [0x60]


def test_call_undefined_label():
    arch = MOSArchitecture()

    with pytest.raises(ValueError, match='Undefined label: missing'):
        arch.assembly([Call('missing')])


def test_duplicate_label():
    arch = MOSArchitecture()

    with pytest.raises(ValueError, match='Duplicate label: start'):
        arch.assembly([Label('start'), Label('start')])


def test_entry_jump_shifts_labels_and_relocations():
    arch = MOSArchitecture()
    ast = [
        Start('main'),
        Label('exit'),
        Bytes(1, (Int(0x60),)),
        Label('main'),
        Bytes(1, (Int(0xA9),)),
        Call('exit'),
    ]

    words = arch.assembly(ast, origin=0x080D, start='main', entry_jump=True)

    assert words == [0x4C, 0x11, 0x08, 0x60, 0xA9, 0x20, 0x10, 0x08]
    assert arch.entry == 0x0811
    assert arch.origin + arch.labels['exit'] == 0x0810


def test_entry_without_jump():
    arch = MOSArchitecture()
    ast = [
        Start('main'),
        Label('exit'),
        Bytes(1, (Int(0x60),)),
        Label('main'),
        Bytes(1, (Int(0xA9),)),
    ]

    words = arch.assembly(ast, origin=0x080D, start='main')

    assert words == [0x60, 0xA9]
    assert arch.entry == 0x080E


def test_undefined_start_label():
    arch = MOSArchitecture()

    with pytest.raises(ValueError, match='Undefined start label: missing'):
        arch.assembly([Start('missing')], start='missing')
