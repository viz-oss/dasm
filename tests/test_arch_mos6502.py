"""Unit tests for the MOS 6502/6510 architecture."""

import pytest

from arch.mos6502 import MOSArchitecture
from lang.abstract import Arg, Raw, Call, Exit, Int, Label, Mov, Ptr, Reg, Return, Start


def test_call_backward_label():
    arch = MOSArchitecture()
    ast = [
        Label('start'),
        Raw(1, (Int(0x60),)),
        Call('start'),
    ]

    words = arch.assembly(ast, origin=0x080D)

    assert words == [0x60, 0x20, 0x0D, 0x08]


def test_call_forward_label():
    arch = MOSArchitecture()
    ast = [
        Call('start'),
        Label('start'),
        Raw(1, (Int(0x60),)),
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
            Arg('a', Int(1), reg=Reg(0)),
            Arg('b', Int(2), reg=Reg(1)),
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
        Raw(1, (Int(0x60),)),
        Label('main'),
        Raw(1, (Int(0xA9),)),
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
        Raw(1, (Int(0x60),)),
        Label('main'),
        Raw(1, (Int(0xA9),)),
    ]

    words = arch.assembly(ast, origin=0x080D, start='main')

    assert words == [0x60, 0xA9]
    assert arch.entry == 0x080E


def test_undefined_start_label():
    arch = MOSArchitecture()

    with pytest.raises(ValueError, match='Undefined start label: missing'):
        arch.assembly([Start('missing')], start='missing')


def test_register_immediates():
    arch = MOSArchitecture()

    assert arch.assembly([Mov(to=Reg(0), fr=Int(1))]) == [0xA9, 0x01]
    assert arch.assembly([Mov(to=Reg(1), fr=Int(2))]) == [0xA2, 0x02]
    assert arch.assembly([Mov(to=Reg(2), fr=Int(3))]) == [0xA0, 0x03]


def test_absolute_stores():
    arch = MOSArchitecture()

    assert arch.assembly([Mov(to=Ptr(Int(0x1234)), fr=Reg(0))]) == [
        0x8D, 0x34, 0x12,
    ]
    assert arch.assembly([Mov(to=Ptr(Int(0x1234)), fr=Reg(1))]) == [
        0x8E, 0x34, 0x12,
    ]
    assert arch.assembly([Mov(to=Ptr(Int(0x1234)), fr=Reg(2))]) == [
        0x8C, 0x34, 0x12,
    ]


def test_immediate_out_of_range():
    arch = MOSArchitecture()

    with pytest.raises(AssertionError):
        arch.assembly([Mov(to=Reg(0), fr=Int(256))])


def test_absolute_address_out_of_range():
    arch = MOSArchitecture()

    with pytest.raises(AssertionError):
        arch.assembly([Mov(to=Ptr(Int(0x10000)), fr=Reg(0))])


@pytest.mark.parametrize(
    "instruction",
    [
        Mov(to=Reg(3), fr=Int(1)),
        Mov(to=Ptr(Int(1)), fr=Reg(3)),
        Mov(to=Ptr(Int(1)), fr=Int(1)),
        Mov(to=Reg(0), fr=Ptr('data')),
    ],
)
def test_unsupported_mov_forms(instruction):
    arch = MOSArchitecture()

    with pytest.raises(NotImplementedError):
        arch.assembly([instruction])


@pytest.mark.parametrize(
    "method",
    [
        '_lda_zero_page', '_lda_zero_page_x', '_lda_absolute',
        '_lda_absolute_x', '_lda_absolute_y', '_lda_indirect_x',
        '_lda_indirect_y',
        '_ldx_zero_page', '_ldx_zero_page_y', '_ldx_absolute',
        '_ldx_absolute_y',
        '_ldy_zero_page', '_ldy_zero_page_y', '_ldy_absolute',
        '_ldy_absolute_y',
        '_sta_zero_page', '_sta_zero_page_x', '_sta_absolute_x',
        '_sta_absolute_y', '_sta_indirect_x', '_sta_indirect_y',
        '_stx_zero_page', '_stx_zero_page_y',
        '_sty_zero_page', '_sty_zero_page_x',
    ],
)
def test_unimplemented_addressing_modes(method):
    arch = MOSArchitecture()

    with pytest.raises(NotImplementedError):
        getattr(arch, method)(None)

