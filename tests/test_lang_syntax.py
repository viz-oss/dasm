"""Unit tests for parsing syntax"""

import pytest
from lang.abstract import Start, Label, Mov, Reg, Ptr, Arg, Call, Int, Param
from lang.syntax import parse, DasmSyntaxError


def test_missing_value():
    with pytest.raises(DasmSyntaxError) as e:
        parse('r0 = ')

    assert e.value.line == 1
    assert e.value.col == 6
    assert 'number' in str(e.value) and 'register' in str(e.value)


def test_label():
    with pytest.raises(DasmSyntaxError) as e:
        parse('r0:')

    assert e.value.line == 1
    assert e.value.col == 3
    
    with pytest.raises(DasmSyntaxError) as e:
        parse('1abc:')

    assert e.value.line == 1
    assert e.value.col == 2


def test_call():
    ast = parse("""
        foo()
        r0 = foo()
        r0 = bar
        foo(color = 1, size = r5, buf = label)
    """)
    
    assert ast == [
        Call('foo'),
        Call('foo', (), Reg(0)),
        Mov(Reg(0), Ptr('bar')),
        Call('foo', (Arg('color', Int(1)), Arg('size', Reg(5)), Arg('buf', Ptr('label'))))
    ]


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
    ast = parse("""
       start🚀:
       żółć:
       r0 = żółć
       foo_é()
       r1🚀()
       r1x()
    """)

    assert ast == [
        Label('start🚀'),
        Label('żółć'),
        Mov(Reg(0), Ptr('żółć')),
        Call('foo_é'),
        Call('r1🚀'),
        Call('r1x'),
    ]
