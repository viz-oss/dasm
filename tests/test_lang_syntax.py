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
        foo:
        foo()
        r0 = foo()
        r0 = bar
        foo2(color: r0, size: r1, buf: r2):
        foo2(color = 1, size = 2, buf = 3)
    """)
    
    assert ast == [
        Label('foo'),
        Call('foo'),
        Call('foo', (), Reg(0)),
        Mov(Reg(0), Ptr('bar')),
        Label('foo2', (
            Param('color', Reg(0)),
            Param('size', Reg(1)),
            Param('buf', Reg(2)))
        ),
        Call('foo2', (
            Arg('color', Int(1), _reg=Reg(n=0)),
            Arg('size', Int(2), _reg=Reg(n=1)),
            Arg('buf', Int(3), _reg=Reg(n=2)))
        )
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
       foo_é:
       foo_é()
       r1x:
       start🚀()
       r1x()
    """)

    assert ast == [
        Label('start🚀'),
        Label('żółć'),
        Mov(Reg(0), Ptr('żółć')),
        Label('foo_é'),
        Call('foo_é'),
        Label('r1x'),
        Call('start🚀'),
        Call('r1x'),
    ]
