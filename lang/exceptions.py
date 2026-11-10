"""Parser exceptions"""

class DasmSyntaxError(Exception):
    line: int | None
    col: int | None
    expected: list[str] | None
    message: str
    def __init__(self, line: int | None = None, col: int | None = None, expected: list[str] | None = None, message: str = ''):
        self.line, self.col, self.expected, self.message = line, col, expected, message
        msg = ""
        if expected is not None: msg += f"Expected {' or '.join(expected)}\n\n"
        msg += message
        super().__init__(msg)

