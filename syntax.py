"""
Lark parser
"""

import sys
from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput, UnexpectedToken, UnexpectedCharacters
from abstract import Reg, Int, Mov, Label


class DasmSyntaxError(Exception):
    def __init__(self, line = None, col = None, message = ''):
        msg = ""
        if line is not None and col is not None: msg += f"Line: {line} Column: {col}\n\n"
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


def parse(text: str) -> list:
    if not text.endswith('\n'):
        text += '\n'
    try:
        ast = ToAst().transform(_parser.parse(text))
    except (UnexpectedToken, UnexpectedCharacters) as e:
        raise DasmSyntaxError(e.line, e.column, e.get_context(text))
    except UnexpectedInput:
        raise DasmSyntaxError(message=e.get_context(text))
    return ast

