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


class MOSArchitecture(Architecture):

    word_size = 1     # 8-bit CPU
    endian = 'little' # little endian

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

    def call(self, instr, offset: int = 0) -> list[int]:
        # JMP $xxxx - the address is patched after all labels are known.
        self.relocations.append(
            Relocation(offset + 1, instr.target, 2, self.endian)
        )
        return [0x4C, 0x00, 0x00]


EXPORTS = MOSArchitecture
