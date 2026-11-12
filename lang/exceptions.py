"""Parser exceptions"""

class DasmSyntaxError(Exception):
    line: int | None
    col: int | None
    expected: list[str] | None
    message: str
    file: str | None
    map_columns: bool
    context: bool
    def __init__(self, line: int | None = None, col: int | None = None, expected: list[str] | None = None, message: str = '', file: str | None = None, map_columns: bool = False, context: bool = False):
        self.line, self.col, self.expected, self.message = line, col, expected, message
        self.file = file
        self.map_columns = map_columns
        self.context = context
        msg = ""
        if expected is not None: msg += f"Expected {' or '.join(expected)}\n\n"
        msg += message
        super().__init__(msg)

    def __str__(self):
        msg = ""
        if self.expected is not None:
            msg += f"Expected {' or '.join(self.expected)}\n\n"
        msg += self.message
        return msg

