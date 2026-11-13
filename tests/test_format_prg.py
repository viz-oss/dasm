"""Unit tests for the C=64 PRG format."""

from arch.mos import MOSArchitecture
from format.prg import FormatPrg
from lang.abstract import Bytes, Call, Int, Label, Start


def test_origin_points_after_basic_stub():
    assert FormatPrg().origin == 0x080D


def test_header_and_basic_stub():
    output = FormatPrg().output([0x60])

    assert output == bytes([
        0x01, 0x08,                          # load address 0x0801
        0x0B, 0x08,                          # next line
        0x0A, 0x00,                          # line 10
        0x9E, 0x32, 0x30, 0x36, 0x31,        # SYS 2061
        0x00,                                # end of line
        0x00, 0x00,                          # end of BASIC
        0x60,                                # program
    ])


def test_call_is_relocated_to_prg_origin():
    arch = MOSArchitecture()
    fmt = FormatPrg()
    ast = [
        Label('start'),
        Bytes(1, (Int(0x60),)),
        Call('start'),
    ]

    words = arch.assembly(ast, origin=fmt.origin)
    output = fmt.output(words)

    assert output[-3:] == bytes([0x4C, 0x0D, 0x08])


def test_start_adds_jump_to_entry_point():
    arch = MOSArchitecture()
    fmt = FormatPrg()
    ast = [
        Start('main'),
        Label('exit'),
        Bytes(1, (Int(0x60),)),
        Label('main'),
        Bytes(1, (Int(0xA9),)),
        Call('exit'),
    ]

    words = arch.assembly(ast, origin=fmt.origin, start='main', entry_jump=True)
    output = fmt.output(words, entry=arch.entry)

    # Header + BASIC stub still points at 0x080D (SYS 2061).
    assert output[:14] == bytes([
        0x01, 0x08,
        0x0B, 0x08,
        0x0A, 0x00,
        0x9E, 0x32, 0x30, 0x36, 0x31,
        0x00,
        0x00, 0x00,
    ])
    # JMP main, then exit and main shifted by 3 bytes.
    assert output[14:17] == bytes([0x4C, 0x11, 0x08])
    assert output[17:] == bytes([0x60, 0xA9, 0x4C, 0x10, 0x08])
    assert arch.entry == 0x0811
