"""
Lark parser
"""

import ast
from typing import Dict
from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput, VisitError
from .abstract import Reg, Int, Mov, Label, Bytes, Text, Ptr, Call
from .exceptions import DasmSyntaxError


GRAMMAR = r'''
start: (line? _NL)*

?line: LABEL
     | statement
     | directive
     | call

call: NAME "(" ")"

statement: REG "=" (REG | NUMBER | NAME)
         | (NUMBER | NAME) "=" REG         

directive: DIRECTIVE value_list
         | DIRECTIVE STRING

value_list: NUMBER ("," NUMBER)*

// --- terminals: identifiers
REG.3: /r\d+(?![A-Za-z_0-9])/
NAME: /(?!r\d+(?![A-Za-z_0-9]))[A-Za-z_]\w*/
LABEL.2: /(?!r\d+:)[A-Za-z_]\w*:/
DIRECTIVE: /\.[a-z]\w*/

// --- terminals: literals
NUMBER: /-?(?:0[xX][0-9a-fA-F]+(?:_[0-9a-fA-F]+)*|\d+(?:_\d+)*)/
STRING: /"(\\.|[^"\\\r\n])*"/

// --- terminals: whitespace and comments
COMMENT: /;[^\r\n]*|#[^\r\n]*|\/\/[^\r\n]*/
WHITESPACE: /[ \t]+/
_NL: /(\r?\n)+/

%ignore COMMENT
%ignore WHITESPACE
'''


_BYTES_DIRECTIVES = {'.b': 1, '.b8': 1, '.b16': 2, '.b32': 4, '.b64': 8}
_TERMINAL_NAMES = {
    'REG': 'register',
    'NUMBER': 'number',
    '_NL': 'end of line',
    'EQUAL': '"="',
    'LABEL': 'label',
    'NAME': 'name',
    'DIRECTIVE': 'directive',
    'STRING': 'string',
    'COMMA': '","',
    'LPAR': '"("',
    'RPAR': '")"',
}


class ToAst(Transformer):

    def start(self, children):
        return list(children)

    def REG(self, tok):
        return Reg(int(tok[1:]))

    def NUMBER(self, tok):
        return Int(int(tok, 0))

    def LABEL(self, tok):
        return Label(str(tok)[:-1])

    def statement(self, c):
        to, fr = c
        if not isinstance(to, Reg):
            to = Ptr(to)
        if isinstance(fr, str):
            fr = Ptr(fr)
        return Mov(to, fr)

    def value_list(self, c):
        return tuple(c)

    def STRING(self, tok):
        return ast.literal_eval(str(tok))
        
    def NAME(self, tok):
        return str(tok)
        
    def call(self, c):
        return Call(c[0])

    def directive(self, c):
        name, arg = c
        if isinstance(arg, tuple) and name in _BYTES_DIRECTIVES:
            return Bytes(_BYTES_DIRECTIVES[name], arg)
        if isinstance(arg, str) and name == '.text':
            return Text(arg)
        raise DasmSyntaxError(
            name.line, name.column,
            message=f"unknown or misused directive {name}",
            map_columns=True
        )


_parser = Lark(GRAMMAR, parser='lalr')


def parse(text: str) -> list:
    if not text.endswith('\n'):
        text += '\n'
    try:
        parsed = _parser.parse(text)
    except UnexpectedInput as e:
        expected = getattr(e, 'expected', None) or getattr(e, 'allowed', None) or []
        names = sorted(_TERMINAL_NAMES.get(t, t) for t in expected)
        context = e.get_context(text) if getattr(e, 'pos_in_stream', None) is not None else ''
        raise DasmSyntaxError(
            line=getattr(e, 'line', None),
            col=getattr(e, 'column', None),
            expected=names,
            message=context,
            map_columns=True,
            context=True
        ) from e
    try:
        return ToAst().transform(parsed)
    except VisitError as e:
        if isinstance(e.orig_exc, DasmSyntaxError):
            raise e.orig_exc from None
        tok = getattr(e.obj, 'line', None)
        col = getattr(e.obj, 'column', None)
        raise DasmSyntaxError(
            line=tok, col=col,
            message=f"invalid literal: {e.orig_exc}",
            map_columns=True
        ) from e
    
