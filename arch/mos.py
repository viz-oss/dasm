"""Architecture: MOS 6502/6510 for C=64"""

from arch.base import Architecture


class MOSArchitecture(Architecture):

    def __init__(self):
        super().__init__()
        self.endian = 'little'

    def mov(self, instr) -> list[int]:
        if instr.to_reg():
            if instr.fr_int():
                assert 0 <= instr.fr.value < 255
                return self._lda_immediate(instr)
        elif instr.to_ptr():
            if instr.fr_reg():
                return self._sta_address(instr)
        raise NotImplementedError(instr)

    def _lda_immediate(self, instr) -> list[int]:
        return [0xA9, instr.fr.value]

    def _sta_address(self, instr) -> list[int]:
        address = instr.to.target.value
        assert isinstance(address, int)
        assert 0 <= address < 65535
        byte0, byte1 = address.to_bytes(2, byteorder=self.endian)
        return [0x8D, byte0, byte1]

    def call(self, instr) -> list[int]:
        return [0x4C, 0x0D, 0x08]


EXPORTS = MOSArchitecture
