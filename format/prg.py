"""Format: C=64 prg"""

from format.bin import FormatBin


class FormatPrg(FormatBin):

    def __init__(self):
        self.ext = 'prg'
        
    def _header(self) -> int:
        start = 0x1000
        return start
        
    def _basic_stub(self) -> list[int]:
        pass

    def output(self, words: list[int]) -> bytes:
        return super().output([self._header(), *words])

EXPORTS = FormatPrg
