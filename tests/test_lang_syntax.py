"""Unit tests for parsing syntax"""

import pytest
from lang.abstract import Start
from lang.syntax import parse, DasmSyntaxError

def test_missing_value():
    with pytest.raises(DasmSyntaxError) as e:
        parse('r0 = ')
    assert e.value.line == 1
    assert e.value.col == 6
    assert 'number' in str(e.value) and 'register' in str(e.value)


def test_start_directive():
    ast = parse('.start main\nmain:\n  r0 = 1\n')

    assert isinstance(ast[0], Start)
    assert ast[0].target == 'main'


def test_start_directive_requires_label():
    with pytest.raises(DasmSyntaxError, match='unknown or misused directive'):
        parse('.start 1\n')


def test_duplicate_start_directive():
    with pytest.raises(DasmSyntaxError, match='duplicate .start directive'):
        parse('.start main\n.start other\nmain:\n  r0 = 1\n')
