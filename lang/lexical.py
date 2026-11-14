"""
Shared lexical building blocks (used by the grammar and by the preprocessor).
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

REG = 'r[0-9]+'


def expand(pattern: str) -> str:
    """Replace <<IDENT>>, <<CONT>> and <<REG>> placeholders."""
    return (pattern
            .replace('<<IDENT>>', IDENT)
            .replace('<<CONT>>', IDENT_CONT)
            .replace('<<REG>>', REG))
