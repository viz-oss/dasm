"""
Defines custom exceptions raised during the parsing phase of the Dasm assembler.
These exceptions carry detailed context about where and why the parsing failed.
"""

class DasmSyntaxError(Exception):
    """Syntax or semantic error with optional source position."""

    def __init__(self, line: int | None = None, col: int | None = None,
                 expected: list[str] | None = None, message: str = '',
                 file: str | None = None, map_columns: bool = False,
                 context: bool = False):
        super().__init__(message)
        self.line, self.col, self.expected, self.message = line, col, expected, message
        self.file = file
        self.map_columns = map_columns   # col refers to preprocessed text, needs mapping back
        self.context = context           # message already contains a source excerpt

    def location(self) -> str:
        parts = [self.file or '<input>']
        if self.line is not None:
            parts.append(str(self.line))
            if self.col is not None:
                parts.append(str(self.col))
        return ':'.join(parts)

    def __str__(self):
        msg = ""
        if self.expected:
            msg += f"Expected {' or '.join(self.expected)}\n\n"
        return msg + self.message
