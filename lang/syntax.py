"""
Lark parser
"""

import ast
from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput, VisitError
from .abstract import Reg, Int, Mov, Label, Bytes, Text, Ptr
from .exceptions import DasmSyntaxError


GRAMMAR = r'''
start: (line? _NL)*

?line: LABEL
     | statement
     | directive

statement: REG "=" (REG | NUMBER | ptr)
         | ptr "=" REG
directive: DIRECTIVE value_list
         | DIRECTIVE STRING

value_list: NUMBER ("," NUMBER)*

REG: /r\d+/
LABEL.2: /[A-Za-z_]\w*:/
NUMBER: /-?(?:0[xX][0-9a-fA-F]+(?:_[0-9a-fA-F]+)*|\d+(?:_\d+)*)/
DIRECTIVE: /\.[a-z]\w*/
ptr: "@" (NAME | NUMBER)
NAME: /[A-Za-z_]\w*/
STRING: /"(\\.|[^"\\\r\n])*"/
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
    'AT': '"@"',
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

    def statement(self, children):
        to, fr = children
        return Mov(to, fr)

    def value_list(self, c):
        return tuple(c)

    def STRING(self, tok):
        return ast.literal_eval(str(tok))
        
    def NAME(self, tok):
        return str(tok)

    def ptr(self, c):
        return Ptr(c[0])

    def directive(self, c):
        name, arg = c
        if isinstance(arg, tuple) and name in _BYTES_DIRECTIVES:
            return Bytes(_BYTES_DIRECTIVES[name], arg)
        if isinstance(arg, str) and name == '.text':
            return Text(arg)
        raise DasmSyntaxError(name.line, name.column, message=f"unknown or misused directive {name}")


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
            message=context
        ) from e
    try:
        return ToAst().transform(parsed)
    except VisitError as e:
        if isinstance(e.orig_exc, DasmSyntaxError):
            raise e.orig_exc from None
        tok = getattr(e.obj, 'line', None)
        raise DasmSyntaxError(message=f"invalid literal: {e.orig_exc}") from e
    
