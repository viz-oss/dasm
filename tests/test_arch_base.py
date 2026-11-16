"""Unit tests for the base architecture helpers."""

import pytest

from arch.base import Architecture, Relocation
from arch.mos6502 import MOSArchitecture
from lang.abstract import Bytes, Call, Int, Label, Text


def test_relocation_defaults():
    reloc = Relocation(offset=1, target='main')

    assert reloc.size == 2
    assert reloc.endian == 'little'


def test_bytes_are_emitted():
    arch = MOSArchitecture()

    assert arch.assembly([Bytes(1, (Int(0x60), Int(0x01)))]) == [0x60, 0x01]
    assert arch.assembly([Bytes(1, (Int(255),))]) == [255]


def test_byte_out_of_range():
    arch = MOSArchitecture()

    with pytest.raises(AssertionError):
        arch.assembly([Bytes(1, (Int(256),))])


def test_text_emits_nothing():
    arch = MOSArchitecture()

    assert arch.assembly([Text('ignored')]) == []


def test_address_out_of_range():
    arch = MOSArchitecture()

    with pytest.raises(ValueError, match='Address out of range'):
        arch.assembly([Label('x'), Call('x')], origin=0x10000)


class _BaseProbe(Architecture):
    """Concrete subclass used to reach the abstract method bodies."""

    def mov(self, instr):
        return super().mov(instr)

    def call(self, instr, offset: int = 0):
        return super().call(instr, offset)

    def ret(self, instr):
        return super().ret(instr)

    def exit(self, instr):
        return super().exit(instr)

    def jmp(self, target: str, offset: int = 0):
        return super().jmp(target, offset)


def test_abstract_operations_raise_not_implemented():
    arch = _BaseProbe()

    for operation in (
        lambda: arch.mov(None),
        lambda: arch.call(None),
        lambda: arch.ret(None),
        lambda: arch.exit(None),
        lambda: arch.jmp('main'),
    ):
        with pytest.raises(NotImplementedError):
            operation()
