"""Unit tests for the WASM output format."""

import shutil
import subprocess

import pytest

from arch.wasm import WasmArchitecture
from utils.modules import load_module
from format.wasm import FormatWasm, _uleb128
from lang.abstract import Int, Mov, Ptr, Reg


MAGIC = b'\x00asm\x01\x00\x00\x00'


def _read_uleb128(data, pos=0):
    result = 0
    shift = 0
    while True:
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result, pos
        shift += 7


def _sections(module):
    assert module[:8] == MAGIC
    sections = []
    pos = 8
    while pos < len(module):
        section_id = module[pos]
        pos += 1
        size, pos = _read_uleb128(module, pos)
        payload = module[pos:pos + size]
        assert len(payload) == size
        sections.append((section_id, payload))
        pos += size
    return sections


def test_exports():
    fmt = load_module('format', 'wasm')
    assert isinstance(fmt, FormatWasm)


def test_header_and_empty_module():
    arch = WasmArchitecture()
    module = FormatWasm().output(arch.assembly([]))
    sections = _sections(module)

    assert [section_id for section_id, _ in sections] == [1, 3, 7, 10]
    assert dict(sections)[1] == bytes([0x01, 0x60, 0x00, 0x00])
    assert dict(sections)[3] == bytes([0x01, 0x00])
    assert dict(sections)[7] == b'\x01\x04main\x00\x00'
    assert dict(sections)[10] == bytes([0x01, 0x02, 0x00, 0x0B])


def test_mov_module_with_locals():
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Reg(n=0), fr=Int(value=1))])
    sections = dict(_sections(FormatWasm().output(words)))

    assert sections[10] == bytes.fromhex('01 08 01 01 7F 41 01 21 00 0B')


def test_memory_section_and_export():
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Ptr(target=Int(value=100)), fr=Reg(n=0))])
    module = FormatWasm().output(words)
    sections = _sections(module)
    payloads = dict(sections)

    assert [section_id for section_id, _ in sections] == [1, 3, 5, 7, 10]
    assert payloads[5] == bytes([0x01, 0x00, 0x01])
    assert payloads[7] == bytes.fromhex(
        '02 04 6D 61 69 6E 00 00 06 6D 65 6D 6F 72 79 02 00'
    )
    assert payloads[10] == bytes.fromhex(
        '01 0C 01 01 7F 41 E4 00 20 00 36 02 00 0B'
    )


def test_large_local_index():
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Reg(n=128), fr=Reg(n=300))])
    sections = dict(_sections(FormatWasm().output(words)))

    # 301 locals: ULEB128(301) = AD 02.
    assert sections[10] == bytes.fromhex(
        '01 0B 01 AD 02 7F 20 AC 02 21 80 01 0B'
    )


def test_unsupported_opcode():
    with pytest.raises(ValueError, match='unsupported WASM opcode'):
        FormatWasm().output([0x6A, 0x0B])


def test_missing_end_opcode():
    with pytest.raises(ValueError, match='end opcode'):
        FormatWasm().output([0x41, 0x01, 0x21, 0x00])


def test_nonzero_entry_is_not_supported():
    with pytest.raises(ValueError, match='entry offset'):
        FormatWasm().output([0x0B], entry=1)


def test_call_opcode_is_scanned():
    module = FormatWasm().output([0x10, 0x00, 0x0B])

    assert module[:8] == MAGIC


@pytest.mark.parametrize("opcode", [0x00, 0x0F])
def test_plain_opcodes_are_scanned(opcode):
    module = FormatWasm().output([opcode, 0x0B])

    assert module[:8] == MAGIC


def test_truncated_constant_is_rejected():
    with pytest.raises(ValueError, match='unexpected end'):
        FormatWasm().output([0x41])


def test_truncated_local_index_is_rejected():
    with pytest.raises(ValueError, match='unexpected end'):
        FormatWasm().output([0x20])


def test_uleb128_requires_non_negative():
    with pytest.raises(AssertionError, match='non-negative'):
        _uleb128(-1)


def test_custom_memory_pages():
    fmt = FormatWasm()
    fmt.memory_pages = 2
    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Ptr(target=Int(value=100)), fr=Reg(n=0))])
    sections = dict(_sections(fmt.output(words)))

    assert sections[5] == bytes([0x01, 0x00, 0x02])


def test_node_validates_module():
    if shutil.which('node') is None:
        pytest.skip('node is not available')

    arch = WasmArchitecture()
    words = arch.assembly([Mov(to=Ptr(target=Int(value=100)), fr=Reg(n=0))])
    module = FormatWasm().output(words)
    script = (
        "const b = Buffer.from(process.argv[1], 'hex');"
        "if (!WebAssembly.validate(b)) process.exit(1);"
    )
    subprocess.run(
        ['node', '-e', script, module.hex()],
        check=True,
        capture_output=True,
    )
