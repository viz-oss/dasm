"""Base file inherited by all architectures"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True)
class Relocation:
    """
    Represents a dependency on a label that must be resolved (patched) during assembly.
    This occurs when the instruction needs to jump to a label whose address is not yet known.
    """
    offset: int          # The starting index in the output where the address needs to be written.
    target: str          # The name of the label being referenced.
    size: int = 2        # The number of bytes occupied by the address/target.
    endian: str = 'little' # Byte order for writing the address.


class Architecture(ABC):

    # Size of one emitted item in bytes. Byte-oriented CPUs use 1.
    word_size: int = 1
    # Number of bytes occupied by an entry jump (0 = no jump support).
    entry_jump_size: int = 0
    # Endiannes
    endian: Literal['little', 'big'] | None = None

    def __init__(self):
        # Store labels
        self.labels: dict[str, int] = {}
        # Relocation table
        self.relocations: list[Relocation] = []
        # Position pointer
        self.origin: int = 0
        # Entry point (from .start)
        self.start: str | None = None
        self.entry: int | None = None
    
    def assembly(self, ast: [], origin: int = 0,
                 start: str | None = None,
                 entry_jump: bool = False) -> list[int]:
        self.labels.clear()
        self.relocations.clear()
        self.origin = origin
        self.start = start
        self.entry = None

        output: list[int] = []
        # The entry jump occupies the first bytes of the program, so every
        # label defined below is automatically shifted by its size.
        if start is not None and entry_jump:
            jump = self.jmp(start)
            if self.entry_jump_size:
                assert len(jump) == self.entry_jump_size
            output += jump
        for instr in ast:
            match instr.__class__.__name__:
                case 'Start':
                    pass
                case 'Label':
                    if instr.name in self.labels:
                        raise ValueError(f"Duplicate label: {instr.name}")
                    self.labels[instr.name] = len(output) * self.word_size
                case 'Mov':
                    output += self.mov(instr)
                case 'Call':
                    output += self.call(instr, offset=len(output))
                case 'Bytes':
                    output += self.bytes(instr)
                case 'Text':
                    output += self.text(instr)
                case 'Return':
                    output += self.ret(instr)
                case 'Exit':
                    output += self.exit(instr)
        self.apply_relocations(output)
        if start is not None:
            if start not in self.labels:
                raise ValueError(f"Undefined start label: {start}")
            self.entry = self.origin + self.labels[start]
        return output

    def apply_relocations(self, output: list[int]) -> None:
        """
        Patches placeholder operands in the generated machine code with the correct, resolved label addresses.
        This must be called after all instructions are generated but before the code is finalized.
        """
        for reloc in self.relocations:
            if reloc.target not in self.labels:
                raise ValueError(f"Undefined label: {reloc.target}")
            
            # Calculate the absolute address of the target label.
            address = self.origin + self.labels[reloc.target]
            
            # Basic bounds checking for the address size.
            if not 0 <= address < (1 << (reloc.size * 8)):
                raise ValueError(
                    f"Address out of range for {reloc.target}: {address:#x}"
                )
            
            # Write the calculated address into the output buffer at the specified offset.
            # The address is converted to bytes based on the required size and endianness.
            output[reloc.offset:reloc.offset + reloc.size] = list(
                address.to_bytes(reloc.size, byteorder=reloc.endian)
            )

    def bytes(self, instr) -> list[int]:
        """
        Emits raw byte data as a list of unsigned byte values (0-255).
        :param instr: The instruction object containing byte values.
        :return: A list of integers (0-255).
        """
        result = []
        for byte in instr.values:
            # Ensure each byte value is within the valid range [0, 255].
            assert 0 <= byte.value <= 255
            result.append(byte.value)
        return result

    def text(self, instr) -> list[int]:
        return []

    @abstractmethod
    def mov(self, instr) -> list[int]:
        """
        Translates a MOVE instruction into machine code.
        :param instr: The instruction object specifying the move operation.
        :return: A list of instruction words (integers) representing the machine code.
        """
        raise NotImplementedError

    @abstractmethod
    def call(self, instr, offset: int = 0) -> list[int]:
        """
        Translates a CALL instruction into machine code.
        :param instr: The instruction object specifying the call operation.
        :param offset: The current address/offset where the call instruction is being emitted (useful for relative addressing).
        :return: A list of instruction words (integers) representing the machine code.
        """
        raise NotImplementedError

    @abstractmethod
    def ret(self, instr) -> list[int]:
        """
        Translates a RETURN instruction into machine code.
        :param instr: The instruction object specifying the return operation.
        :return: A list of instruction words (integers) representing the machine code.
        """
        raise NotImplementedError

    @abstractmethod
    def exit(self, instr) -> list[int]:
        """
        Translates an EXIT instruction into machine code.
        This typically halts execution and signals the operating system.
        :param instr: The instruction object specifying the exit operation.
        :return: A list of instruction words (integers) representing the machine code.
        """
        raise NotImplementedError

    @abstractmethod
    def jmp(self, target: str, offset: int = 0) -> list[int]:
        """
        Translates an unconditional JUMP instruction to a specified label.
        :param target: The label name to jump to.
        :param offset: Optional offset/addressing mode details.
        :return: A list of instruction words (integers) representing the machine code.
        """
        raise NotImplementedError
