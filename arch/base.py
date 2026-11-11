"""Base file inherited by all architectures"""

from abc import ABC, abstractmethod


class Architecture(ABC):

    def __init__(self):
        self.labels = {}
        self.endian: Literal['little', 'big'] | None = None
    
    def assembly(self, ast: []) -> list[int]:
        output: list[int] = []
        for instr in ast:
            match instr.__class__.__name__:
                case 'Label':
                    if instr.name in self.labels:
                        raise ValueError(f"Duplicate label: {instr.name}")
                    self.labels[instr.name] = len(output)
                case 'Mov':
                    output += self.mov(instr)
                case 'Bytes':
                    output += self.bytes(instr)
                case 'Text':
                    output += self.text(instr)
        return output

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
