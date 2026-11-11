"""
Preprocessor for .set statements.
"""

import re
from .exceptions import DasmSyntaxError

_TOKEN_RE = re.compile(r'''
    (?P<comment>;[^\r\n]*|\#[^\r\n]*|//[^\r\n]*)
  | (?P<string>"(?:\\.|[^"\\\r\n])*")
  | (?P<label>[A-Za-z_]\w*:)
  | (?P<directive>\.[a-z]\w*)
  | (?P<number>\d\w*)
  | (?P<name>[A-Za-z_]\w*)
  | (?P<ws>[ \t]+)
  | (?P<other>.)
''', re.VERBOSE)

_REG_RE = re.compile(r'r\d+')
_NUM_RE = re.compile(r'-?\d\w*')


def _define(consts, sig, lineno):
    col = sig[0][2] + 1
    if len(sig) < 4 or sig[1][0] != 'name' or sig[2][1] != '=':
        raise DasmSyntaxError(lineno, col, message="expected: .set NAME = <number>")
    name = sig[1][1]
    value = ''.join(v for _, v, _ in sig[3:])
    if _REG_RE.fullmatch(name):
        raise DasmSyntaxError(lineno, col, message=f"'{name}' is reserved for registers")
    if name in consts:
        raise DasmSyntaxError(lineno, col, message=f"constant '{name}' already defined")
    if not _NUM_RE.fullmatch(value):
        raise DasmSyntaxError(lineno, col, message="constant value must be a number")
    try:
        consts[name] = int(value, 0)
    except ValueError:
        raise DasmSyntaxError(lineno, col, message=f"invalid number {value!r}") from None


def preprocess(text: str) -> str:
    consts: dict[str, int] = {}
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        toks = [(m.lastgroup, m.group(), m.start()) for m in _TOKEN_RE.finditer(line)]
        sig = [t for t in toks if t[0] not in ('ws', 'comment')]
        if sig and sig[0][:2] == ('directive', '.set'):
            _define(consts, sig, lineno)
            out.append('')                  # zostaje pusta linia, numeracja się nie przesuwa
            continue
        out.append(''.join(
            str(consts[v]) if k == 'name' and v in consts else v
            for k, v, _ in toks
        ))
    return '\n'.join(out) + '\n'
