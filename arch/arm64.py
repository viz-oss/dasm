"""Architecture: Arm64"""

import operator
from arch.base import Architecture


class Arm64Architecture(Architecture):
    
    def mov(self, instr) -> list[int]:
        # Register to register
        if instr.fromReg():
            return self._orr(instr)
        # Constant number to register
        elif instr.fromInt():
            # 16-bit constants
            if 0 <= instr.fr.value < 0x10000:
                return [self._movz(instr.to.n, instr.fr.value)]
            # Above (movz + movk)
                #return [self._movz(..., ...) , self._movk(..., ...)]
        raise NotImplementedError(instr)

    def _movz(self,
        rd: int,              # Register number 0..31
        imm16: int,           # Constant 16-bit value to move
        hw: int = 0,          # Shift bits 0/16/32/48
        x: bool = True        # Is 64-bit
    ) -> int:
        """Move constant value to a register"""
        rd = operator.index(rd)
        assert 0 <= rd < 32, f"rd out of range: {rd}"
        imm16 = operator.index(imm16)
        assert 0 <= imm16 < 0x10000, f"imm16 out of range: {imm16}"
        hw = operator.index(hw)
        assert hw in (0, 1, 2, 3), f"hw must be 0..3: {hw}"
        sf = 1 if x else 0    # 64-bit operation (X)
        opc = 0b10            # Opcode for MOVZ
        fixed = 0b100101      # "wide immediate" group identifier
        bits = (
            f"{sf:01b}"       # 1 bit
            f"{opc:02b}"      # 2 bits
            f"{fixed:06b}"    # 6 bits
            f"{hw:02b}"       # 2 bits
            f"{imm16:016b}"   # 16 bits
            f"{rd:05b}"       # 5 bits
        )
        assert len(bits) == 32, len(bits)
        return int(bits, 2)


EXPORTS = Arm64Architecture
