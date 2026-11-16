"""Unit tests for parsing syntax"""

import pytest
from lang.abstract import (
    Start, Label, Mov, Reg, Ptr, Arg, Call, Int, Param,
    Bytes, Exit, Return, Text,
)
from lang.syntax import AST, parse, DasmSyntaxError


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


def test_statement_to_memory():
    assert parse('foo = r0\n') == [Mov(Ptr('foo'), Reg(0))]


def test_text_directive():
    assert parse('.text "hello"\n') == [Text('hello')]


@pytest.mark.parametrize("text, size, values", [
    ('.b 1\n', 1, (1,)),
    ('.b8 1, 2\n', 1, (1, 2)),
    ('.b16 0x10, 0x20\n', 2, (0x10, 0x20)),
    ('.b32 -1\n', 4, (-1,)),
    ('.b64 0\n', 8, (0,)),
])
def test_bytes_directives(text, size, values):
    assert parse(text) == [Bytes(size, tuple(Int(v) for v in values))]


def test_exit_directive():
    assert parse('.exit\n') == [Exit()]


def test_return_directive():
    assert parse('return\n') == [Return()]
    assert parse('return 5\n') == [Return(Int(5))]
    assert parse('return -5\n') == [Return(Int(-5))]


@pytest.mark.parametrize("text", [
    '.bogus\n',
    '.foo 1, 2\n',
    '.b8 "x"\n',
    '.text 1\n',
])
def test_unknown_or_misused_directives(text):
    with pytest.raises(DasmSyntaxError, match='unknown or misused directive'):
        parse(text)


def test_arg_name_becomes_pointer():
    ast = parse('f(v: r0):\nf(v = data)\n')

    assert ast[1].args[0].value == Ptr('data')


def test_invalid_string_literal():
    with pytest.raises(DasmSyntaxError, match='invalid literal'):
        parse('.text "\\x"\n')


def test_undefined_call_label():
    with pytest.raises(DasmSyntaxError, match='Label missing not found'):
        parse('missing()\n')


def test_call_args_mismatch():
    with pytest.raises(DasmSyntaxError, match='Args mismatch in f'):
        parse('f(a: r0):\nf()\n')


def test_ast_filter():
    ast = parse('a:\na()\nb:\n')

    assert isinstance(ast, AST)
    assert ast.filter(typeof=Label) == [Label('a'), Label('b')]
    assert ast.filter(name='a') == [Label('a')]
    assert ast.filter(typeof=Call) == [Call('a')]
    assert ast.filter() == list(ast)


def test_block_comments():
    ast = parse("/* a */ r0 = 1\n\"\"\"\nopis\n\"\"\"\nr1 = 2")
    assert ast == [Mov(Reg(0), Int(1)), Mov(Reg(1), Int(2))]
