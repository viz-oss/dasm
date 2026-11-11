"""Format: C=64 prg"""

from format.bin import FormatBin


class FormatPrg(FormatBin):

    def __init__(self):
        self.ext = 'prg'
        
    def _header(self) -> list[int]:
        return [0x01, 0x08]
        
    def _basic_stub(self) -> list[int]:
        return [
            0x0B, 0x08, # end address
            0x0A, 0x00, # line 10
            0x9E, 0x32, 0x30, 0x36, 0x31, # SYS 2061
            0x00, # end of line
            0x00, 0x00 # end of basic
        ]

    def output(self, words: list[int]) -> bytes:
        return super().output([
            *self._header(),
            *self._basic_stub(),
            *words
        ])


EXPORTS = FormatPrg
