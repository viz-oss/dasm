"""Format: raw binary"""

from format.base import Format


class FormatBin(Format):

    def __init__(self):
        self.ext = 'bin'

    def output(self, words: list[int]) -> bytes:
        word_size = 2
        return '\n'.join(format(w, f"0{word_size}b") for w in words)

EXPORTS = FormatBin
