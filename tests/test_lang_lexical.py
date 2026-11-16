"""Unit tests for the shared lexical patterns."""

import re

from lang.lexical import IDENT, IDENT_CONT, IDENT_START, REG, expand


def test_expand_replaces_placeholders():
    pattern = expand('<<IDENT>>-<<CONT>>-<<REG>>')

    assert IDENT in pattern
    assert IDENT_CONT in pattern
    assert REG in pattern
    assert '<<' not in pattern


def test_expand_without_placeholders():
    assert expand('plain') == 'plain'


def test_identifier_accepts_unicode_and_emoji():
    assert re.fullmatch(IDENT, 'żółć')
    assert re.fullmatch(IDENT, 'start🚀')
    assert re.fullmatch(IDENT, '_name')
    assert re.fullmatch(IDENT_START, 'é')


def test_identifier_rejects_leading_digit():
    assert re.fullmatch(IDENT, '1abc') is None


def test_register_pattern():
    assert re.fullmatch(REG, 'r0')
    assert re.fullmatch(REG, 'r128')
    assert re.fullmatch(REG, 'r') is None
