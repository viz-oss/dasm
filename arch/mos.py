"""Architecture: MOS 6502/6510 for C=64"""

import operator
from arch.base import Architecture


class MOSArchitecture(Architecture):

    def mov(self, instr) -> list[int]:
        return []

EXPORTS = MOSArchitecture
