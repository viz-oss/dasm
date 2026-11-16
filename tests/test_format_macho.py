"""Unit tests for the Mach-O output format."""

import struct

from format.macho import (
    S_ATTR_PURE_INSTRUCTIONS,
    S_ATTR_SOME_INSTRUCTIONS,
    FormatMacho,
)


MAGIC = 0xFEEDFACF
CPU_TYPE_ARM64 = 0x0100000C
HEADER_SIZE = 32
SEGMENT_SIZE = 152
SYMTAB_SIZE = 24
COMMANDS_SIZE = SEGMENT_SIZE + SYMTAB_SIZE
TEXT_OFFSET = HEADER_SIZE + COMMANDS_SIZE


def test_extension():
    assert FormatMacho.ext == 'o'


def test_pad16_pads_and_truncates():
    fmt = FormatMacho()

    assert fmt._pad16('__TEXT') == b'__TEXT' + b'\x00' * 10
    assert fmt._pad16('a' * 20) == b'a' * 16


def test_header():
    data = FormatMacho().output([0x11223344])

    header = struct.unpack_from('<8I', data, 0)
    assert header == (
        MAGIC,
        CPU_TYPE_ARM64,
        0,          # cpusubtype
        1,          # MH_OBJECT
        2,          # ncmds
        COMMANDS_SIZE,
        0x2000,     # flags
        0,          # reserved
    )


def test_segment_command():
    words = [0xD2800020, 0xD65F03C0]
    data = FormatMacho().output(words)

    cmd, cmdsize = struct.unpack_from('<II', data, HEADER_SIZE)
    assert cmd == 0x19  # LC_SEGMENT_64
    assert cmdsize == SEGMENT_SIZE
    assert data[HEADER_SIZE + 8:HEADER_SIZE + 24].rstrip(b'\x00') == b'__TEXT'

    vmaddr, vmsize, fileoff, filesize = struct.unpack_from(
        '<QQQQ', data, HEADER_SIZE + 24
    )
    assert (vmaddr, vmsize) == (0, len(words) * 4)
    assert (fileoff, filesize) == (TEXT_OFFSET, len(words) * 4)

    maxprot, initprot, nsects, flags = struct.unpack_from(
        '<IIII', data, HEADER_SIZE + 56
    )
    assert (maxprot, initprot, nsects, flags) == (5, 5, 1, 0)


def test_text_section():
    words = [0xD2800020, 0xD65F03C0]
    data = FormatMacho().output(words)
    section = HEADER_SIZE + 72

    assert data[section:section + 16].rstrip(b'\x00') == b'__text'
    assert data[section + 16:section + 32].rstrip(b'\x00') == b'__TEXT'

    addr, size, offset, align = struct.unpack_from('<QQII', data, section + 32)
    assert (addr, size) == (0, len(words) * 4)
    assert (offset, align) == (TEXT_OFFSET, 2)

    flags = struct.unpack_from('<I', data, section + 32 + 32)[0]
    assert flags == S_ATTR_PURE_INSTRUCTIONS | S_ATTR_SOME_INSTRUCTIONS


def test_symtab_command():
    data = FormatMacho().output([0xD2800020])

    symtab = struct.unpack_from('<6I', data, HEADER_SIZE + SEGMENT_SIZE)
    assert symtab[:2] == (0x2, SYMTAB_SIZE)
    symoff, nsyms, stroff, strsize = symtab[2:]
    assert symoff == TEXT_OFFSET + 4
    assert nsyms == 0
    assert stroff == symoff
    assert strsize == 1


def test_text_and_string_table():
    words = [0xD2800020, 0xD65F03C0]
    data = FormatMacho().output(words)

    assert data[TEXT_OFFSET:TEXT_OFFSET + len(words) * 4] == struct.pack(
        '<2I', *words
    )
    assert data[TEXT_OFFSET + len(words) * 4:] == b'\x00'
