"""Unit tests for an Arm64 architecture"""

import pytest
from lang.abstract import Label, Mov, Ptr, Reg, Int
from arch.arm64 import Arm64Architecture


def test_arch_arm64():
    arch = Arm64Architecture()

    # r0 = 1
    ast = [Mov(to=Reg(n=0), fr=Int(value=1))]
    words = arch.assembly(ast)
    assert hex(words[0]) == '0xd2800020'


def test_movz_64bit():
    arch = Arm64Architecture()

    assert arch._movz(1, 2) == 0xD2800041
    assert arch._movz(2, 0x1234, hw=1) == 0xD2A24682


def test_movz_32bit():
    arch = Arm64Architecture()

    assert arch._movz(3, 0xFFFF, x=False) == 0x529FFFE3


@pytest.mark.parametrize(
    "argument, value, message",
    [
        ("rd", 32, "rd out of range"),
        ("imm16", 0x10000, "imm16 out of range"),
        ("hw", 4, "hw must be 0..3"),
    ],
)
def test_movz_validates_arguments(argument, value, message):
    arch = Arm64Architecture()
    kwargs = {"rd": 0, "imm16": 0}
    kwargs[argument] = value

    with pytest.raises(AssertionError, match=message):
        arch._movz(**kwargs)


def test_mov_reg_to_reg_is_not_implemented():
    arch = Arm64Architecture()

    with pytest.raises(NotImplementedError):
        arch.assembly([Mov(to=Reg(n=0), fr=Reg(n=1))])


def test_mov_large_constant_is_not_implemented():
    arch = Arm64Architecture()

    with pytest.raises(NotImplementedError):
        arch.assembly([Mov(to=Reg(n=0), fr=Int(value=0x10000))])


@pytest.mark.parametrize(
    "instruction",
    [
        Mov(to=Ptr(target=Int(value=0)), fr=Reg(n=0)),
        Mov(to=Reg(n=0), fr=Ptr(target='data')),
    ],
)
def test_other_mov_forms_are_not_implemented(instruction):
    arch = Arm64Architecture()

    with pytest.raises(NotImplementedError):
        arch.assembly([instruction])


@pytest.mark.parametrize(
    "operation",
    [
        lambda arch: arch.call(None),
        lambda arch: arch.ret(None),
        lambda arch: arch.exit(None),
        lambda arch: arch.jmp('main'),
    ],
)
def test_unimplemented_operations(operation):
    arch = Arm64Architecture()

    with pytest.raises(NotImplementedError):
        operation(arch)


def test_labels_are_ignored_by_assembly():
    arch = Arm64Architecture()

    assert arch.assembly([Label('main'), Mov(Reg(0), Int(1))]) == [0xD2800020]
