"""
Lark parser
"""

import sys
from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput, UnexpectedToken, UnexpectedCharacters
from abstract import Reg, Int, Mov, Label


class DasmSyntaxError(Exception):
    line: int
    col: int
    expected: List
    def __init__(self, line: int = None, col:int  = None, expected: List = None, message: str = ''):
        self.line, self.col, self.expected = line, col, expected
        msg = ""
        if line is not None and col is not None: msg += f"Line: {line} Column: {col}\n"
        if expected is not None: msg += f"Expected: {' or '.join(expected)}\n\n"
        msg += message
        super().__init__(msg)


GRAMMAR = r'''
start: (line? _NL)*

?line: LABEL
     | statement

statement: REG "=" (REG | NUMBER)

REG: /r\d+/
LABEL.2: /[A-Za-z_]\w*:/
NUMBER: /-?(?:0[xX][0-9a-fA-F]+(?:_[0-9a-fA-F]+)*|\d+(?:_\d+)*)/
COMMENT: /;[^\r\n]*|#[^\r\n]*|\/\/[^\r\n]*/
WHITESPACE: /[ \t]+/
_NL: /(\r?\n)+/

%ignore COMMENT
%ignore WHITESPACE
'''


class ToAst(Transformer):
    def REG(self, tok):
        return Reg(int(tok[1:]))

    def NUMBER(self, tok):
        return Int(int(tok, 0))

    def LABEL(self, tok):
        return Label(str(tok)[:-1])

    def statement(self, children):
        to, fr = children
        return Mov(to, fr)

    def start(self, children):
        return list(children)


_parser = Lark(GRAMMAR, parser='lalr')
_TERMINAL_NAMES = {
    'REG': 'register',
    'NUMBER': 'number',
    '_NL': 'end of line',
    'EQUAL': '"="',
    'LABEL': 'label'
}


def parse(text: str) -> list:
    if not text.endswith('\n'):
        text += '\n'
    try:
        parsed = _parser.parse(text)
    except (UnexpectedToken, UnexpectedCharacters) as e:
        expected = getattr(e, 'expected', None) or getattr(e, 'allowed', None) or []
        names = sorted(_TERMINAL_NAMES.get(t, t) for t in expected)
        raise DasmSyntaxError(e.line, e.column, names, e.get_context(text))
    except UnexpectedInput as e:
        expected = getattr(e, 'expected', None) or getattr(e, 'allowed', None) or []
        names = sorted(_TERMINAL_NAMES.get(t, t) for t in expected)
        raise DasmSyntaxError(expected=names, message=e.get_context(text))
    return ToAst().transform(parsed)

