"""Architecture: Arm64"""

import operator
from arch.base import Architecture


class Arm64Architecture(Architecture):

    word_size = 4     # 64bit CPU
    endian = 'little' # little endian

    def mov(self, instr) -> list[int]:
        if instr.to_reg():
            # Register to register
            if instr.fr_reg():
                return self._orr(instr)
            # Constant number to register
            elif instr.fr_int():
                # 16-bit constants
                if 0 <= instr.fr.value < 0x10000:
                    return [self._movz(instr.to.n, instr.fr.value)]
                # Above (movz + movk)
                    #return [self._movz(..., ...) , self._movk(..., ...)]
        raise NotImplementedError(instr)

    def _orr(self, instr) -> int:
        raise NotImplementedError(instr)

    def _movz(self,
        rd: int,              # Destination register number (0-31)
        imm16: int,           # 16-bit constant value to move
        hw: int = 0,          # Hardware word/shift index (0, 1, 2, 3)
        x: bool = True        # Flag indicating 64-bit operation (X)
    ) -> int:
        """
        Constructs the instruction word for MOVZ (Move Immediate to Register).
        This instruction moves a 16-bit constant into a specified register.

        :param rd: Destination register number (0-31).
        :param imm16: 16-bit constant value to move.
        :param hw: Hardware word/shift index (0, 1, 2, 3). Default is 0.
        :param x: Flag indicating 64-bit operation (X). Default is True.
        :return: The 32-bit instruction word.
        """
        rd = operator.index(rd)
        assert 0 <= rd < 32, f"Destination register (rd) out of range: {rd}"
        imm16 = operator.index(imm16)
        assert 0 <= imm16 < 0x10000, f"Immediate value (imm16) out of range: {imm16}"
        hw = operator.index(hw)
        assert hw in (0, 1, 2, 3), f"Hardware word/shift index (hw) must be 0..3: {hw}"

        # --- Bit Packing into 32-bit instruction word ---
        # The instruction word is constructed by packing various fields into specific bit ranges.
        sf = 1 if x else 0    # Bit 31: Sign/Size flag (1 bit). 1 if 64-bit operation (X), 0 otherwise.
        opc = 0b10            # Bits 30-29: Opcode for MOVZ instruction (2 bits).
        fixed = 0b100101      # Bits 28-23: Group identifier for "wide immediate" instructions (6 bits).

        # Assemble the 32-bit instruction word from its fields:
        bits = (
            f"{sf:01b}"       # Bit 31: Size/Sign flag (1 bit)
            f"{opc:02b}"      # Bits 30-29: Opcode (2 bits)
            f"{fixed:06b}"    # Bits 28-23: Instruction Group/Fixed bits (6 bits)
            f"{hw:02b}"       # Bits 22-21: Hardware/Shift index (2 bits)
            f"{imm16:016b}"   # Bits 20-5: Immediate value (16 bits)
            f"{rd:05b}"       # Bits 4-0: Destination Register (5 bits)
        )

        assert len(bits) == 32, f"Instruction word length mismatch: {len(bits)}"
        return int(bits, 2)

    def call(self, instr, offset: int = 0) -> list[int]:
        """
        Translates a CALL instruction into machine code for the Arm64 architecture.

        :param instr: The instruction object containing details about the call.
        :param offset: Optional offset/addressing mode details, usually related to the jump target.
        :return: A list of instruction words (integers) representing the machine code.
        """
        # Implementation for CALL instructions is not yet available for this architecture.
        raise NotImplementedError(instr)

    def ret(self, instr) -> list[int]:
        """
        Translates a RETURN instruction into machine code for the Arm64 architecture.

        :param instr: The instruction object containing details about the return.
        :return: A list of instruction words (integers) representing the machine code.
        """
        # Implementation for RETURN instructions is not yet available for this architecture.
        raise NotImplementedError(instr)

    def exit(self, instr) -> list[int]:
        """
        Translates an EXIT instruction into machine code for the Arm64 architecture.

        :param instr: The instruction object containing details about the exit.
        :return: A list of instruction words (integers) representing the machine code.
        """
        # Implementation for EXIT instructions is not yet available for this architecture.
        raise NotImplementedError(instr)

    def jmp(self, target: str, offset: int = 0) -> list[int]:
        """
        Handles unconditional jump instructions.
        :param target: The label/target to jump to.
        :param offset: Optional offset for the jump target.
        :return: List of instruction words (integers).
        """
        # Implementation for JMP instructions is not yet available for this architecture.
        raise NotImplementedError


EXPORTS = Arm64Architecture
