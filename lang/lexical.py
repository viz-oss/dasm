"""
Shared lexical building blocks.

This module provides the raw regex patterns and helper functions used by both
the Lark grammar parser and the preprocessor stage of the Dasm compiler.
It handles complex character sets, including Unicode emojis and combining marks,
to support a wide range of identifiers.
"""

# NOTE: normal (non-raw) strings on purpose: the characters/ranges are real
# code points, so neither Lark nor `re` has to interpret \U escapes.
_EMOJI = '\u2600-\u27BF\u2B50\u2B55\U0001F300-\U0001FAFF'
_JOINERS = '\u200D\uFE0F'          # ZWJ and variation selector (continuation only)
_MARKS = '\u0300-\u036F'           # combining diacritics

# identifier start: a letter (any script), underscore or emoji; never a digit
IDENT_START = '(?:[^\\W\\d]|[' + _EMOJI + '])'
# identifier continuation: \w (letters, digits, _) or emoji, joiners, marks
IDENT_CONT = '(?:\\w|[' + _EMOJI + _JOINERS + _MARKS + '])'
IDENT = IDENT_START + IDENT_CONT + '*'

# r0 | r1 | r2 ... rN
REG = 'r[0-9]+'

# "string" | 'string'
QUOTED_STRING = r"""["'](\\.|[^"'\\\r\n])*["']"""


def expand(pattern: str) -> str:
    """Replace <<*>> placeholders."""
    return (pattern
            .replace('<<IDENT>>', IDENT)
            .replace('<<CONT>>', IDENT_CONT)
            .replace('<<REG>>', REG)
            .replace('<<QUOTED_STRING>>', QUOTED_STRING)
            )
