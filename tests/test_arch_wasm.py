"""Unit tests for the WASM architecture."""

import pytest

from arch.wasm import WasmArchitecture, sleb128, uleb128
from utils.modules import load_module
from lang.abstract import Call, Exit, Int, Mov, Ptr, Reg, Return


def test_exports():
    arch = load_module('arch', 'wasm')
    assert isinstance(arch, WasmArchitecture)


def test_uleb128():
    assert uleb128(0) == [0x00]
    assert uleb128(1) == [0x01]
    assert uleb128(127) == [0x7F]
    assert uleb128(128) == [0x80, 0x01]
    assert uleb128(300) == [0xAC, 0x02]


def test_sleb128():
    assert sleb128(0) == [0x00]
    assert sleb128(1) == [0x01]
    assert sleb128(63) == [0x3F]
    assert sleb128(64) == [0xC0, 0x00]
    assert sleb128(-1) == [0x7F]
    assert sleb128(-64) == [0x40]
    assert sleb128(-65) == [0xBF, 0x7F]


def test_empty_program_ends_with_end():
    arch = WasmArchitecture()
    assert arch.assembly([]) == [0x0B]


def test_mov_int_to_reg():
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Reg(n=0), fr=Int(value=1))])
    assert words == [0x41, 0x01, 0x21, 0x00, 0x0B]


def test_mov_large_int_to_reg():
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Reg(n=0), fr=Int(value=300))])
    assert words == [0x41, 0xAC, 0x02, 0x21, 0x00, 0x0B]


def test_mov_reg_to_reg():
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Reg(n=0), fr=Reg(n=1))])
    assert words == [0x20, 0x01, 0x21, 0x00, 0x0B]


def test_mov_large_register_number():
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Reg(n=128), fr=Reg(n=300))])
    assert words == [0x20, 0xAC, 0x02, 0x21, 0x80, 0x01, 0x0B]


def test_store_to_fixed_address():
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Ptr(target=Int(value=100)), fr=Reg(n=0))])
    assert words == [0x41, 0xE4, 0x00, 0x20, 0x00, 0x36, 0x02, 0x00, 0x0B]


def test_load_from_fixed_address():
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Reg(n=0), fr=Ptr(target=Int(value=100)))])
    assert words == [0x41, 0xE4, 0x00, 0x28, 0x02, 0x00, 0x21, 0x00, 0x0B]


def test_label_address_is_not_supported():
    arch = WasmArchitecture()
    with pytest.raises(NotImplementedError, match='label address'):
        arch.assembly([Mov(to=Reg(n=0), fr=Ptr(target='data'))])


def test_ret():
    arch = WasmArchitecture()
    assert arch.assembly([Return()]) == [0x0F, 0x0B]


def test_return_value():
    arch = WasmArchitecture()
    assert arch.assembly([Return(Int(value=5))]) == [0x41, 0x05, 0x0F, 0x0B]


def test_exit():
    arch = WasmArchitecture()
    assert arch.assembly([Exit()]) == [0x0F, 0x0B]


def test_call_is_not_supported_yet():
    arch = WasmArchitecture()
    with pytest.raises(NotImplementedError, match='function indices'):
        arch.assembly([Call('missing')])


def test_uleb128_requires_non_negative():
    with pytest.raises(AssertionError, match='non-negative'):
        uleb128(-1)


def test_sleb128_negative_boundaries():
    assert sleb128(-128) == [0x80, 0x7F]
    assert sleb128(-8192) == [0x80, 0x40]


def test_unsupported_mov_raises():
    arch = WasmArchitecture()

    with pytest.raises(NotImplementedError):
        arch.assembly([Mov(to=Ptr(target=Int(value=1)), fr=Int(value=1))])


def test_negative_address_is_rejected():
    arch = WasmArchitecture()

    with pytest.raises(AssertionError, match='negative address'):
        arch.assembly([Mov(to=Reg(n=0), fr=Ptr(target=Int(value=-1)))])


def test_jmp_is_not_supported():
    arch = WasmArchitecture()
    with pytest.raises(NotImplementedError, match='direct jump'):
        arch.jmp('missing')
