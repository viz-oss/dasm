"""Architecture: MOS 6502/6510 for C=64"""

from arch.base import Architecture


class MOSArchitecture(Architecture):

    def mov(self, instr) -> list[int]:
        return []

    def bytes(self, instr) -> list[int]:
        return []

    def text(self, instr) -> list[int]:
        return []


EXPORTS = MOSArchitecture
