"""Formats assembled code into a hexadecimal file, typically used for AVR microcontrollers."""

from format.base import Format


class FormatHex(Format):

    # File extension
    ext = 'hex'

    def output(self, words: list[int], entry: int | None = None) -> bytes:
        word_size = 2  # bytes per word
        hex_digits = word_size * 2
        text = '\n'.join(format(w, f"0{hex_digits}X") for w in words)
        return text.encode('ascii')

EXPORTS = FormatHex
