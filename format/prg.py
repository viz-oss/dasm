"""
Format: C=64 prg

┌─────────────────────────────┐  offset 0
│ header (2 B)                │
│   load address      = 2     │  ← Adres ładowania
├─────────────────────────────┤  offset 2
│ basic stub                  │  ← Opcjonalny stub w BASIC-u 
├─────────────────────────────┤  offset 14
│ program                     │  ← Właściwy kod programu 
└─────────────────────────────┘
"""

from format.bin import FormatBin


class FormatPrg(FormatBin):

    # 0x0801 (default BASIC starting address allows launch by 'RUN')
    LOAD_ADDRESS = 0x0801
    BASIC_STUB_SIZE = 12
    # File extension
    ext = 'prg'

    @property
    def origin(self) -> int:
        """Memory address of the first byte of the assembled program."""
        return self.LOAD_ADDRESS + self.BASIC_STUB_SIZE

    def _header(self) -> list[int]:
        return list(self.LOAD_ADDRESS.to_bytes(2, byteorder='little'))
        
    def _basic_stub(self) -> list[int]:
        sys_address = self.origin
        digits = str(sys_address).encode('ascii')
        # Address of the 00 00 terminator that follows the BASIC line.
        next_line = self.LOAD_ADDRESS + 6 + len(digits)
        stub = [
            *next_line.to_bytes(2, byteorder='little'), # next line address
            0x0A, 0x00, # line 10
            0x9E, *digits, # SYS <address>
            0x00, # end of line
            0x00, 0x00 # end of basic
        ]
        assert len(stub) == self.BASIC_STUB_SIZE, len(stub)
        return stub

    def output(self, words: list[int]) -> bytes:
        return super().output([
            *self._header(),
            *self._basic_stub(),
            *words
        ])


EXPORTS = FormatPrg
