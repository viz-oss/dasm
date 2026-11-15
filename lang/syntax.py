"""
Lark parser
"""

import ast
from typing import Dict
from collections import UserList
from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput, VisitError
from .abstract import Start, Reg, Int, Mov, Label, Param, Bytes, Text, Ptr, Arg, Call, Return, Exit
from .exceptions import DasmSyntaxError
from .lexical import expand


GRAMMAR = expand(r'''
start: (line? _NL)*

?line: LABEL
     | label_def
     | statement
     | directive
     | call
     | return_stmt

label_def: NAME "(" params? ")" ":"
params: param ("," param)*
param: NAME ":" REG
call: (REG "=")? NAME "(" args? ")"
args: arg ("," arg)*
arg: NAME "=" (REG | NUMBER | NAME)

statement: REG "=" (REG | NUMBER | NAME)
         | (NUMBER | NAME) "=" REG         

directive: DIRECTIVE
         | DIRECTIVE value_list
         | DIRECTIVE STRING
         | DIRECTIVE NAME

value_list: NUMBER ("," NUMBER)*

return_stmt: RETURN NUMBER?

// --- terminals: identifiers
REG.3: /r[0-9]+(?!<<CONT>>)/
NAME: /(?!<<REG>>(?!<<CONT>>))(?!return(?!<<CONT>>))<<IDENT>>/
LABEL.2: /(?!<<REG>>:)(?!return:)<<IDENT>>:/
DIRECTIVE: /\.[a-z]\w*/
RETURN.4: /return(?!<<CONT>>)/

// --- terminals: literals
NUMBER: /-?(?:0[xX][0-9a-fA-F]+(?:_[0-9a-fA-F]+)*|\d+(?:_\d+)*)/
STRING: /"(\\.|[^"\\\r\n])*"/

// --- terminals: whitespace and comments
COMMENT: /;[^\r\n]*|#[^\r\n]*|\/\/[^\r\n]*/
WHITESPACE: /[ \t]+/
_NL: /(\r?\n)+/

%ignore COMMENT
%ignore WHITESPACE
''')


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
    'COLON': '":"'
}


class AST(UserList):
    
    def filter(self, typeof = None, name: str = None) -> AST:
        return AST([
            element for element in self.data
            if (typeof is None or isinstance(element, typeof)) and (name is None or (hasattr(element, 'name') and element.name == name))
        ])

class ToAst(Transformer):

    def start(self, children):
        if sum(isinstance(child, Start) for child in children) > 1:
            raise DasmSyntaxError(message="duplicate .start directive")
        return list(children)

    def REG(self, tok):
        return Reg(int(tok[1:]))

    def NUMBER(self, tok):
        return Int(int(tok, 0))

    def LABEL(self, tok):
        return Label(str(tok)[:-1])

    def param(self, c):
        name, reg = c
        return Param(name, reg)

    def params(self, c):
        return tuple(c)

    def label_def(self, c):
        name, *rest = c
        return Label(name, rest[0] if rest else ())
    
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
        
    def arg(self, c):
        name, value = c
        if isinstance(value, str):
            value = Ptr(value)
        return Arg(name, value)
    
    def args(self, c):
        return tuple(c)

    def call(self, c):
        result = None
        if isinstance(c[0], Reg):
            result, *c = c
        target, *rest = c
        return Call(target, rest[0] if rest else (), result)
    
    def directive(self, c):
        name, *args = c
        if not args and name == '.exit':
            return Exit()
        if len(args) != 1:
            raise DasmSyntaxError(
                name.line, name.column,
                message=f"unknown or misused directive {name}",
                map_columns=True
            )
        arg = args[0]
        if isinstance(arg, tuple) and name in _BYTES_DIRECTIVES:
            return Bytes(_BYTES_DIRECTIVES[name], arg)
        if isinstance(arg, str) and name == '.text':
            return Text(arg)
        if isinstance(arg, str) and name == '.start':
            return Start(arg)
        raise DasmSyntaxError(
            name.line, name.column,
            message=f"unknown or misused directive {name}",
            map_columns=True
        )

    def return_stmt(self, c):
        # c[0] is the RETURN token; the number (if any) is c[1]
        return Return(c[1] if len(c) > 1 else None)


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
        abstract = AST(ToAst().transform(parsed))
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

    labels = abstract.filter(typeof=Label)
    calls = abstract.filter(typeof=Call)
    for call in calls:
        label = labels.filter(name=call.target)
        if len(label) == 0:
            raise DasmSyntaxError(
                message=f"Label {call.target} not found"
            )
        if len(label[0].params) != len(call.args):
            raise DasmSyntaxError(
                message=f"Args mismatch in {call.target}"
            )
        for n in range(len(call.args)):
            arg = call.args[n]
            param = label[0].params[n]
            arg._reg = param.reg

    return abstract
