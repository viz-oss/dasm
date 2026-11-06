"""
Source Lark parser
"""

from lark import Lark, Transformer
from abstract import Reg, Int, Mov


GRAMMAR = r'''
start: (statement? _NL)*

statement: REG "=" (REG | NUMBER)

REG: /r\d+/
NUMBER: /-?(0[xX][0-9a-fA-F]+|\d+)/
_NL: /(\r?\n)+/

%ignore /[ \t]+/
'''


class ToAst(Transformer):
    def REG(self, tok):
        return Reg(int(tok[1:]))

    def NUMBER(self, tok):
        return Int(int(tok, 0))

    def statement(self, children):
        to, fr = children
        return Mov(to, fr)

    def start(self, children):
        return list(children)

_parser = Lark(GRAMMAR, parser='lalr')

def parse(text: str) -> list:
    if not text.endswith('\n'):
        text += '\n'
    return ToAst().transform(_parser.parse(text))
