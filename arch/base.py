"""Base file inherited by all architectures"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True)
class Relocation:
    """A reference to a label that still has to be patched into the output."""
    offset: int          # index in the output where the address starts
    target: str          # label name
    size: int = 2        # number of bytes occupied by the address
    endian: str = 'little'


class Architecture(ABC):

    # Size of one emitted item in bytes. Byte-oriented CPUs use 1.
    word_size: int = 1
    # Endiannes
    endian: Literal['little', 'big'] | None = None

    def __init__(self):
        # Store labels
        self.labels: dict[str, int] = {}
        # Relocation table
        self.relocations: list[Relocation] = []
        # Position pointer
        self.origin: int = 0
    
    def assembly(self, ast: [], origin: int = 0) -> list[int]:
        self.labels.clear()
        self.relocations.clear()
        self.origin = origin

        output: list[int] = []
        for instr in ast:
            match instr.__class__.__name__:
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
        self.apply_relocations(output)
        return output

    def apply_relocations(self, output: list[int]) -> None:
        """Patch placeholder operands with label addresses."""
        for reloc in self.relocations:
            if reloc.target not in self.labels:
                raise ValueError(f"Undefined label: {reloc.target}")
            address = self.origin + self.labels[reloc.target]
            if not 0 <= address < (1 << (reloc.size * 8)):
                raise ValueError(
                    f"Address out of range for {reloc.target}: {address:#x}"
                )
            output[reloc.offset:reloc.offset + reloc.size] = list(
                address.to_bytes(reloc.size, byteorder=reloc.endian)
            )

    def bytes(self, instr) -> list[int]:
        result = []
        for byte in instr.values:
            assert 0 <= byte.value < 255
            result.append(byte.value)
        return result

    def text(self, instr) -> list[int]:
        return []

    @abstractmethod
    def mov(self, instr) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    def call(self, instr, offset: int = 0) -> list[int]:
        raise NotImplementedError
