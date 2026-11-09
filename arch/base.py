"""Base file inherited by all architectures"""

class Architecture:
    
    def assembly(self, ast: []) -> list[int]:
        output: list[int] = []
        for instr in ast:
            match instr.__class__.__name__:
                case 'Label':
                    output += self.label(instr)
                case 'Mov':
                    output += self.mov(instr)
        return output
