"""Unit tests for the 4-bit ALU architecture backend."""

import pytest

import arch.alu48 as alu48
from arch.alu48 import Alu4Architecture
from utils.modules import load_module
from lang.abstract import Raw, Int


def test_loader_uses_the_new_exports_name():
    assert isinstance(load_module("arch", "alu48"), Alu4Architecture)
    assert not hasattr(alu48, "ARCHITECTURE")


def test_backend_uses_the_current_architecture_interface():
    arch = Alu4Architecture()

    assert arch.word_size == 1
    assert arch.endian == "little"
    assert arch.assembly([Raw(1, (Int(0xA5),))]) == [0xA5]


@pytest.mark.parametrize(
    ("mnemonic", "operand", "opcode"),
    [
        ("ADD", "5", 0b000),
        ("SUB", "10", 0b001),
        ("AND", "0b1010", 0b010),
        ("OR", "0xF", 0b011),
        ("XOR", "3", 0b100),
        ("NOT", "0", 0b101),
        ("SHL", "4", 0b110),
        ("SHR", "8", 0b111),
    ],
)
def test_encode_packs_opcode_and_operand(mnemonic, operand, opcode):
    word = Alu4Architecture().encode(mnemonic, [operand], {})

    assert word == (opcode << 5) | (int(operand, 0) << 1)


def test_encode_supports_carry_override():
    arch = Alu4Architecture()

    assert arch.encode("add", ["5", "1"], {}) == 0b00001011


@pytest.mark.parametrize("value", ["16", "-1"])
def test_encode_rejects_operand_a_out_of_range(value):
    with pytest.raises(ValueError, match="Operand A out of range"):
        Alu4Architecture().encode("ADD", [value], {})


@pytest.mark.parametrize("operands", [[], ["1", "0", "1"], ["1", "2"]])
def test_encode_rejects_invalid_operands(operands):
    with pytest.raises(ValueError):
        Alu4Architecture().encode("ADD", operands, {})


def test_encode_resolves_labels_from_context():
    arch = Alu4Architecture()

    assert arch.encode("OR", ["value"], {"labels": {"value": 15}}) == 0b01111110


def test_microcode_table_contains_all_opcodes():
    table = Alu4Architecture().microcode_table()

    assert [entry["opcode"] for entry in table] == list(range(8))
    assert table[0]["mnemonic"] == "ADD"
    assert table[-1] == {
        "opcode": 7,
        "mnemonic": "SHR",
        "data_bin": "0000001",
        "data_hex": "01",
    }


@pytest.mark.parametrize("method", ["mov", "call", "ret", "exit", "jmp"])
def test_cpu_operations_are_not_part_of_the_alu_backend(method):
    arch = Alu4Architecture()

    with pytest.raises(NotImplementedError):
        getattr(arch, method)(None)
