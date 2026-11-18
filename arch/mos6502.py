"""
Architecture: MOS 6502/6510 for C=64

Data transfer    
LDA, LDX, LDY
STA, STX, STY
Loading data from memory into registers (Load) and storing register contents in memory (Store).

Arithmetic operations    
ADC, SBC
Addition with carry (Add with Carry) and subtraction with borrow (Subtract with Borrow).

Logical and bitwise operations
AND, ORA, EOR, BIT
AND, OR, exclusive OR (XOR), and bit testing.

Increment and decrement    
INC, DEC
INX, INY, DEX, DEY
Increasing or decreasing by 1 the value in memory or in the X and Y index registers.

Unconditional jumps and subroutines
JMP, JSR, RTS
Jumping to a specified address (Jump), jumping to a subroutine while preserving the return address (Jump to Subroutine), and returning from a subroutine (Return from Subroutine).

Conditional jumps (branches)
BEQ, BNE, BMI, BPL, BCS, BCC
Relative jumps based on the state of the flags (for example, jumping if the result of the previous operation is zero – BEQ).

Stack operations
PHA, PLA, PHP, PLP
Pushing the accumulator or flag register onto the system stack and pulling it back.

Processor control
NOP, SEC, CLC, SEI, CLI
No operation (No Operation), setting or clearing flags (for example, carry or interrupt flags).
"""

from arch.base import Architecture, Relocation
from lang.abstract import Mov


# Opcodes used by this backend.
OP_LDA_IMMEDIATE = 0xA9
OP_LDX_IMMEDIATE = 0xA2
OP_LDY_IMMEDIATE = 0xA0
OP_STA_ABSOLUTE = 0x8D
OP_STX_ABSOLUTE = 0x8E
OP_STY_ABSOLUTE = 0x8C
OP_JSR = 0x20
OP_RTS = 0x60
OP_JMP = 0x4C


class MOSArchitecture(Architecture):

    word_size = 1     # 8-bit CPU
    endian = 'little' # little endian
    entry_jump_size = 3  # JMP $xxxx

    # Helpers

    def _absolute16(self, address) -> list[int]:
        assert isinstance(address, int)
        assert 0 <= address <= 65535
        byte0, byte1 = address.to_bytes(2, byteorder=self.endian)
        return [byte0, byte1]
        
    def _arg(self, instr):
        return self.mov(Mov(to = instr.reg, fr = instr.value))
        
    # MOV

    def mov(self, instr) -> list[int]:
        if instr.to_reg():
            if instr.fr_int():
                assert 0 <= instr.fr.value <= 255
                match instr.to.n:
                    case 0: return self._lda_immediate(instr)
                    case 1: return self._ldx_immediate(instr)
                    case 2: return self._ldy_immediate(instr)
                raise NotImplementedError(instr)
        elif instr.to_mem():
            if instr.fr_reg():
                match instr.fr.n:
                    case 0: return self._sta_absolute(instr)
                    case 1: return self._stx_absolute(instr)
                    case 2: return self._sty_absolute(instr)
                raise NotImplementedError(instr)
        raise NotImplementedError(instr)

    # LDA

    def _lda_immediate(self, instr) -> list[int]:
        assert 0 <= instr.fr.value <= 255
        return [OP_LDA_IMMEDIATE, instr.fr.value]

    def _lda_zero_page(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _lda_zero_page_x(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _lda_absolute(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _lda_absolute_x(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _lda_absolute_y(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _lda_indirect_x(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _lda_indirect_y(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    # LDX

    def _ldx_immediate(self, instr) -> list[int]:
        assert 0 <= instr.fr.value <= 255
        return [OP_LDX_IMMEDIATE, instr.fr.value]

    def _ldx_zero_page(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _ldx_zero_page_y(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _ldx_absolute(self, instr) -> list[int]:
        """
        Encodes the instruction to load a value into the X register using absolute addressing.
        """
        raise NotImplementedError(instr)

    def _ldx_absolute_y(self, instr) -> list[int]:
        """
        Encodes the instruction to load a value into the X register using absolute addressing and Y displacement.
        """
        raise NotImplementedError(instr)
        
    # LDY

    def _ldy_immediate(self, instr) -> list[int]:
        """
        Encodes the instruction to load an immediate value into the Y register.
        """
        assert 0 <= instr.fr.value <= 255
        return [OP_LDY_IMMEDIATE, instr.fr.value]

    def _ldy_zero_page(self, instr) -> list[int]:
        """
        Encodes the instruction to load a value into the Y register from zero page memory.
        """
        raise NotImplementedError(instr)

    def _ldy_zero_page_y(self, instr) -> list[int]:
        """
        Encodes the instruction to load a value into the Y register from zero page memory, using Y displacement.
        """
        raise NotImplementedError(instr)

    def _ldy_absolute(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _ldy_absolute_y(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    # STA

    def _sta_zero_page(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _sta_zero_page_x(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _sta_absolute(self, instr) -> list[int]:
        return [OP_STA_ABSOLUTE, *self._absolute16(instr.to.base.value)]

    def _sta_absolute_x(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _sta_absolute_y(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _sta_indirect_x(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _sta_indirect_y(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    # STX

    def _stx_zero_page(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _stx_zero_page_y(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _stx_absolute(self, instr) -> list[int]:
        return [OP_STX_ABSOLUTE, *self._absolute16(instr.to.base.value)]

    # STY

    def _sty_zero_page(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _sty_zero_page_x(self, instr) -> list[int]:
        raise NotImplementedError(instr)

    def _sty_absolute(self, instr) -> list[int]:
        return [OP_STY_ABSOLUTE, *self._absolute16(instr.to.base.value)]

    # CALL

    def call(self, instr, offset: int = 0) -> list[int]:
        args_bytes = [subarg for arg in instr.args for subarg in self._arg(arg)]
        call_bytes = [OP_JSR, 0x00, 0x00] # JSR, 0x00, 0x00 address ready for a relocation
        self.relocations.append(
            Relocation(offset + 1 + len(args_bytes), instr.target, 2, self.endian)
        )
        return args_bytes + call_bytes

    # RET

    def ret(self, instr) -> list[int]:
        return [OP_RTS]

    # EXIT

    def exit(self, instr) -> list[int]:
        return [OP_RTS]  # RTS

    # JMP

    def jmp(self, target: str, offset: int = 0) -> list[int]:
        self.relocations.append(
            Relocation(offset + 1, target, 2, self.endian)
        )
        return [OP_JMP, 0x00, 0x00] # JMP, 0x00, 0x00 address ready for a relocation


EXPORTS = MOSArchitecture
