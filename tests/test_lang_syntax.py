"""Unit tests for parsing syntax"""

import pytest
from lang.abstract import Start, Label, Mov, Reg, Ptr, Arg, Call, Int
from lang.syntax import parse, DasmSyntaxError


def test_missing_value():
    with pytest.raises(DasmSyntaxError) as e:
        parse('r0 = ')

    assert e.value.line == 1
    assert e.value.col == 6
    assert 'number' in str(e.value) and 'register' in str(e.value)


def test_error_label():
    with pytest.raises(DasmSyntaxError) as e:
        parse('r0:')

    assert e.value.line == 1
    assert e.value.col == 3
    
    with pytest.raises(DasmSyntaxError) as e:
        parse('1abc:')

    assert e.value.line == 1
    assert e.value.col == 2


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


def test_unicode():
    ast = parse('start🚀:\nżółć:\nr0 = żółć\nfoo_é()\nr1🚀()\nr1x()')

    assert ast == [
        Label('start🚀'),
        Label('żółć'),
        Mov(Reg(0), Ptr('żółć')),
        Call('foo_é'),
        Call('r1🚀'),
        Call('r1x'),
    ]

def test_call():
    ast = parse("foo()\nfoo(r0 = 1)\nfoo(r0 = 1, r1 = r2, r3 = label)")
    
    assert ast == [Call('foo'),
        Call('foo', (Arg(Reg(0), Int(1)),)),
        Call('foo', (Arg(Reg(0), Int(1)), Arg(Reg(1), Reg(2)), Arg(Reg(3), Ptr('label'))))
    ]
