"""Base file inherited by all architectures"""

from abc import ABC, abstractmethod


class Architecture(ABC):

    def __init__(self):
        self.labels = {}
    
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

    @abstractmethod
    def mov(self, instr) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    def bytes(self, instr) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    def text(self, instr) -> list[int]:
        raise NotImplementedError
