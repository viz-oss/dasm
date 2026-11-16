"""Unit tests for the hex format."""

from format.hex import FormatHex


def test_extension():
    assert FormatHex.ext == 'hex'


def test_output_formats_each_word_as_four_hex_digits():
    assert FormatHex().output([0x1234, 0x0001]) == b'1234\n0001'


def test_entry_is_ignored():
    assert FormatHex().output([0x00FF], entry=0x1234) == b'00FF'
