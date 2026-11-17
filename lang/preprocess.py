"""
Preprocessor for .set statements and config constants.

Works on tokens, not on raw text, so a constant `art` is never substituted
inside `start:`, `.art`, a string literal or a comment.
"""

import ast, json, re, unicodedata, logging
from dataclasses import dataclass
from .exceptions import DasmSyntaxError
from .lexical import expand, IDENT
from .sourcemap import ColumnMap, ColumnSegment
from utils.log import red, green


_TOKEN_RE = re.compile(expand(r'''
    (?P<comment>;[^\r\n]*|\#[^\r\n]*|//[^\r\n]*)
  | (?P<string><<QUOTED_STRING>>)
  | (?P<label><<IDENT>>:)
  | (?P<directive>\.[a-z]\w*)
  | (?P<number>[0-9]\w*)
  | (?P<name><<IDENT>>)
  | (?P<ws>[ \t]+)
  | (?P<other>.)
'''), re.VERBOSE)

_MASK_RE = re.compile(r'''
    (?P<line>;[^\r\n]*|\#[^\r\n]*|//[^\r\n]*)
  | (?P<block>/\*[\s\S]*?\*/|"""[\s\S]*?""")
  | (?P<string><<QUOTED_STRING>>)
''', re.VERBOSE)

_REG_RE = re.compile(r'r[0-9]+')
_NUM_RE = re.compile(r'-?[0-9]\w*')
_NAME_RE = re.compile(IDENT)

Value = int | str


@dataclass(frozen=True)
class PreprocessedSource:
    """Processed text with per-line column maps back to the original text."""

    text: str
    column_maps: list[ColumnMap]


# --- validation -------------------------------------------------------------

def _check_name(name: str, lineno=None, col=None) -> None:
    if _REG_RE.fullmatch(name):
        raise DasmSyntaxError(lineno, col, message=f"'{name}' is reserved for registers")
    if not _NAME_RE.fullmatch(name):
        raise DasmSyntaxError(lineno, col, message=f"invalid constant name {name!r}")


def _parse_number(text: str, lineno=None, col=None) -> int:
    if not _NUM_RE.fullmatch(text):
        raise DasmSyntaxError(
            lineno, col, message=f"constant value must be a number or a string: {text!r}")
    try:
        return int(text, 0)
    except ValueError:
        raise DasmSyntaxError(lineno, col, message=f"invalid number {text!r}") from None


def _check_config(name: str, value) -> Value:
    """Validate a constant coming from the project config (TOML)."""
    _check_name(name)
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise DasmSyntaxError(
            message=f"config constant {name!r}: expected int or string, "
                    f"got {type(value).__name__}")
    return value


# --- .set handling ----------------------------------------------------------

def _define(consts: dict[str, Value], external: dict[str, Value],
            defined: set[str], sig: list, lineno: int) -> None:
    col = sig[0][2] + 1
    if len(sig) < 4 or sig[1][0] != 'name' or sig[2][1] != '=':
        raise DasmSyntaxError(lineno, col, message="expected: .set NAME = <number or string>")

    name = sig[1][1]
    _check_name(name, lineno, col)

    rest = sig[3:]
    if len(rest) == 1 and rest[0][0] == 'string':
        try:
            value: Value = ast.literal_eval(rest[0][1])
        except (ValueError, SyntaxError):
            raise DasmSyntaxError(lineno, col, message="invalid string literal") from None
    else:
        value = _parse_number(''.join(v for _, v, _ in rest), lineno, col)

    if name in defined:
        raise DasmSyntaxError(lineno, col, message=f"constant '{name}' already defined")
    defined.add(name)

    if name in external:
        return                      # config wins over .set (the line is still validated)
    consts[name] = value


def _render(value: Value) -> str:
    """Text inserted in place of a constant name."""
    return str(value) if isinstance(value, int) else json.dumps(value)

# --- block comments ---------------------------------------------------------

def _mask_block_comments(text: str) -> str:
    def repl(m):
        if m.lastgroup != 'block':
            return m.group()
        return re.sub(r'[^\r\n]', ' ', m.group())
    return _MASK_RE.sub(repl, text)

# --- public API -------------------------------------------------------------

def preprocess_with_map(text: str, defines: dict[str, Value] | None = None) -> PreprocessedSource:
    """Process .set lines and substitute constants, keeping column maps.

    defines: constants from the project config; visible from the first line
    and not overridable by .set. A constant must be defined before use.
    """
    logger = logging.getLogger(__name__)
    text = unicodedata.normalize('NFC', text)
    defines = {unicodedata.normalize('NFC', k): v for k, v in (defines or {}).items()}
    text = _mask_block_comments(text)
    external = {k: _check_config(k, v) for k, v in (defines or {}).items()}
    consts: dict[str, Value] = dict(external)
    defined: set[str] = set()
    out = []
    column_maps = []

    # split('\n'), not splitlines(): the numbering must match the Lark lexer
    for lineno, line in enumerate(text.split('\n'), 1):
        toks = [(m.lastgroup, m.group(), m.start()) for m in _TOKEN_RE.finditer(line)]
        sig = [t for t in toks if t[0] not in ('ws', 'comment')]

        if sig and sig[0][:2] == ('directive', '.set'):
            _define(consts, external, defined, sig, lineno)
            out.append('')          # an empty line remains, the numbering does not shift
            column_maps.append(ColumnMap())
            continue

        parts = []
        segments = []
        out_col = 1
        for kind, value, start in toks:
            original_col = start + 1
            if kind == 'name' and value in consts:
                rendered = _render(consts[value])
                segments.append(ColumnSegment(
                    out_col, out_col + len(rendered) - 1,
                    original_col, fixed=True
                ))
                parts.append(rendered)
                out_col += len(rendered)
            else:
                segments.append(ColumnSegment(
                    out_col, out_col + len(value) - 1, original_col
                ))
                parts.append(value)
                out_col += len(value)

        result = ''.join(parts)
        out.append(result)
        if (line == result):
            logger.info(f"{lineno}: {line}")
        else:
            logger.info(red(f"{lineno}: {line}"))
            logger.info(green(f"{lineno}: {result}"))
        column_maps.append(ColumnMap(segments))

    return PreprocessedSource('\n'.join(out), column_maps)


def preprocess(text: str, defines: dict[str, Value] | None = None) -> str:
    """Process .set lines and substitute constants."""
    return preprocess_with_map(text, defines).text
