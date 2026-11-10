"""Format: hex for AVR and other boards"""

from format.base import Format


class FormatHex(Format):

    def __init__(self):
        self.ext = 'hex'

    def output(self, words: list[int]) -> bytes:
        word_size = 2
        hex_digits = (word_size + 3) // 4
        return '\n'.join(format(w, f"0{hex_digits}X") for w in words)

EXPORTS = FormatHex
