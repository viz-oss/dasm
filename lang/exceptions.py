"""
Defines custom exceptions raised during the parsing phase of the Dasm assembler.
These exceptions carry detailed context about where and why the parsing failed.
"""

class DasmSyntaxError(Exception):
    """
    Exception raised when a syntax error is encountered during parsing.
    """

    line: int | None # The line number in the source file where the error occurred.
    col: int | None # The column number in the source file where the error occurred.
    expected: list[str] | None # A list of tokens or constructs that were expected at the error point.
    message: str # A detailed description of the error.
    file: str | None # The path to the source file where the error occurred.
    map_columns: bool # Flag indicating if column mapping information is available/used.
    context: bool # Flag indicating if additional context (e.g., caret visualization) is available.

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
