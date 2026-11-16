"""Unit tests for the raw binary format."""

from format.bin import FormatBin


def test_extension():
    assert FormatBin.ext == 'bin'


def test_output_is_raw_bytes():
    assert FormatBin().output([0x00, 0x60, 0xFF]) == b'\x00\x60\xff'


def test_entry_is_ignored():
    assert FormatBin().output([0x01], entry=0x1234) == b'\x01'
