"""Unit tests for the C=64 PRG format."""

from arch.mos import MOSArchitecture
from format.prg import FormatPrg
from lang.abstract import Bytes, Call, Int, Label


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
