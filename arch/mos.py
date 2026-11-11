"""Architecture: MOS 6502/6510 for C=64"""

from arch.base import Architecture


class MOSArchitecture(Architecture):

    def mov(self, instr) -> list[int]:
        if instr.fromInt():
            assert 0 <= instr.fr.value < 255
            return self._lda_immediate(instr)
        raise NotImplementedError(instr)

    def _lda_immediate(self, instr) -> list[int]:
        return [0xA9, instr.fr.value]

EXPORTS = MOSArchitecture
