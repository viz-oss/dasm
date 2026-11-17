"""
Lark parser: text -> AST.

Pure syntax. Name resolution (labels, call arguments) lives in symbols.py.
"""

from __future__ import annotations

import ast, logging
logger = logging.getLogger(__name__)
from collections import UserList
from dataclasses import dataclass

from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput, VisitError

from .abstract import (
    Start, Reg, Int, Mov, Label, Param, Raw, Ptr, Arg, Call, Return, Exit,
)
from .exceptions import DasmSyntaxError
from .lexical import expand


# --- grammar ----------------------------------------------------------------

GRAMMAR = expand(r'''
start: (line? _NL)*

?line: LABEL
     | label_def
     | statement
     | raw_stmt
     | directive
     | call
     | return_stmt

statement: REG "=" (REG | NUMBER | NAME)
         | (NUMBER | NAME) "=" REG

label_def: NAME "(" params? ")" ":"
params: param ("," param)*
param: NAME ":" REG

call: (REG "=")? NAME "(" args? ")"
args: arg ("," arg)*
arg: NAME "=" (REG | NUMBER | NAME)

raw_stmt: RAW type_spec? bytes_arg repeat?
type_spec: "(" (NUMBER | STRING) ")"
bytes_arg: value_list | STRING
repeat: "*" NUMBER
value_list: NUMBER ("," NUMBER)*

directive: DIRECTIVE
         | DIRECTIVE value_list
         | DIRECTIVE STRING
         | DIRECTIVE NAME

return_stmt: RETURN NUMBER?

// --- terminals: identifiers
REG.3: /r[0-9]+(?!<<CONT>>)/
NAME: /(?!<<REG>>(?!<<CONT>>))(?!return(?!<<CONT>>))<<IDENT>>/
LABEL.2: /(?!<<REG>>:)(?!return:)<<IDENT>>:/
DIRECTIVE: /\.[a-z]\w*/
RETURN.4: /return(?!<<CONT>>)/
RAW.4: /\.raw(?!<<CONT>>)/

// --- terminals: literals
NUMBER: /-?(?:0[xX][0-9a-fA-F]+(?:_[0-9a-fA-F]+)*|[0-9]+(?:_[0-9]+)*)/
STRING: /"(\\.|[^"\\\r\n])*"|'(\\.|[^'\\\r\n])*'/

// --- terminals: whitespace and comments
COMMENT: /;[^\r\n]*|#[^\r\n]*|\/\/[^\r\n]*/
BLOCK_COMMENT.5: /\/\*[\s\S]*?\*\/|"""[\s\S]*?"""/
WHITESPACE: /[ \t]+/
_NL: /(\r?\n)+/

// --- ignores
%ignore COMMENT
%ignore BLOCK_COMMENT
%ignore WHITESPACE
''')


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
    'COLON': '":"',
    'RAW': '".raw"',
    'RETURN': '"return"',
    'STAR': '"*"',
}

_INT_TYPES = frozenset({8, 16, 32, 64})
_ENCODINGS = frozenset({'utf-8', 'utf-16', 'ascii', 'petscii'})


# --- intermediate nodes (live only inside the transformer) -------------------

@dataclass(frozen=True, slots=True)
class _TypeSpec:
    """The (...) part of .raw(...)."""
    value: int | str


@dataclass(frozen=True, slots=True)
class _Repeat:
    """The '* N' part of .raw."""
    count: int


# --- AST container -----------------------------------------------------------

class AST(UserList):

    def filter(self, typeof=None, name: str | None = None) -> AST:
        return AST([
            el for el in self.data
            if (typeof is None or isinstance(el, typeof))
            and (name is None or getattr(el, 'name', None) == name)
        ])


# --- transformer -------------------------------------------------------------

class ToAst(Transformer):

    def start(self, children):
        if sum(isinstance(c, Start) for c in children) > 1:
            raise DasmSyntaxError(message="duplicate .start directive")
        return list(children)

    # --- terminals ---------------------------------------------------------

    def REG(self, tok):
        token = Reg(int(tok[1:]))
        return token

    def NAME(self, tok):
        return str(tok)

    def LABEL(self, tok):
        return Label(str(tok)[:-1])

    def NUMBER(self, tok):
        try:
            return Int(int(tok, 0))
        except ValueError:
            raise DasmSyntaxError(
                tok.line, tok.column, message=f"invalid number {str(tok)!r}") from None

    def STRING(self, tok):
        try:
            return ast.literal_eval(str(tok))
        except (ValueError, SyntaxError):
            raise DasmSyntaxError(
                tok.line, tok.column, message=f"invalid string literal {str(tok)!r}") from None

    # --- statements --------------------------------------------------------

    def statement(self, c):
        to, fr = c
        if not isinstance(to, Reg):          # number or name on the left -> memory
            to = Ptr(to)
        if isinstance(fr, str):              # name on the right -> symbol
            fr = Ptr(fr)
        return Mov(to, fr)

    def return_stmt(self, c):
        # c[0] is the RETURN token; the number (if any) is c[1]
        return Return(c[1] if len(c) > 1 else None)

    # --- labels ------------------------------------------------------------

    def param(self, c):
        name, reg = c
        return Param(name, reg)

    def params(self, c):
        return tuple(c)

    def label_def(self, c):
        name, *rest = c
        return Label(name, rest[0] if rest else ())

    # --- call --------------------------------------------------------------

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

    # --- .dot directives (.start, .exit) -----------------------------------

    def directive(self, c):
        name, *args = c
        if not args and name == '.exit':
            return Exit()
        if len(args) == 1 and isinstance(args[0], str) and name == '.start':
            return Start(args[0])
        raise DasmSyntaxError(
            name.line, name.column,
            message=f"unknown or misused directive {name}",
            map_columns=True
        )

    # --- .raw --------------------------------------------------------------

    def value_list(self, c):
        return tuple(c)                      # tuple[Int, ...]

    def bytes_arg(self, c):
        return c[0]                          # tuple[Int, ...] or str

    def type_spec(self, c):
        v = c[0]
        return _TypeSpec(v.value if isinstance(v, Int) else v)

    def repeat(self, c):
        return _Repeat(c[0].value)

    def raw_stmt(self, c):
        tok, *rest = c                       # tok: RAW token (has line/column)

        count = 1
        if rest and isinstance(rest[-1], _Repeat):
            count = rest.pop().count

        typ: int | str = 8                   # `.raw 1, 2` means `.raw(8) 1, 2`
        if rest and isinstance(rest[0], _TypeSpec):
            typ = rest.pop(0).value

        (arg,) = rest                        # exactly one argument is left

        if isinstance(typ, int):
            if typ not in _INT_TYPES:
                raise DasmSyntaxError(
                    tok.line, tok.column,
                    message=f"invalid numeric type {typ}, expected one of {sorted(_INT_TYPES)}")
            if not isinstance(arg, tuple):
                raise DasmSyntaxError(
                    tok.line, tok.column,
                    message=f".raw({typ}) takes numbers, not a string")
        else:
            if typ not in _ENCODINGS:
                raise DasmSyntaxError(
                    tok.line, tok.column,
                    message=f"unknown encoding {typ!r}, expected one of {sorted(_ENCODINGS)}")
            if not isinstance(arg, str):
                raise DasmSyntaxError(
                    tok.line, tok.column,
                    message=f".raw({typ!r}) takes a string, not numbers")

        if count < 1:
            raise DasmSyntaxError(
                tok.line, tok.column, message=f"repeat count must be >= 1, got {count}")

        return Raw(typ, arg, count)


# --- public API --------------------------------------------------------------

_parser = Lark(GRAMMAR, parser='lalr', propagate_positions=True)


def parse(text: str) -> AST:
    if not text.endswith('\n'):
        text += '\n'
    try:
        tree = _parser.parse(text)
        lines = []
        for child in tree.children:
            if hasattr(child, 'meta') and not child.meta.empty:
                lines.append(child.meta.line)
            else:
                lines.append(child.line)
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
        return AST(ToAst().transform(tree)), lines
    except VisitError as e:
        if isinstance(e.orig_exc, DasmSyntaxError):
            raise e.orig_exc from None
        raise DasmSyntaxError(
            line=getattr(e.obj, 'line', None),
            col=getattr(e.obj, 'column', None),
            message=f"invalid literal: {e.orig_exc}",
            map_columns=True
        ) from e
