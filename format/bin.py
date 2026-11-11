"""Format: raw binary"""

from format.base import Format


class FormatBin(Format):

    def __init__(self):
        self.ext = 'bin'

    def output(self, words: list[int]) -> bytes:    
        return bytes(words)

EXPORTS = FormatBin
