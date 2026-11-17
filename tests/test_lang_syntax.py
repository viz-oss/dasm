"""Unit tests for parsing syntax"""

import pytest
from lang.abstract import Start, Label, Mov, Reg, Ptr, Arg, Call, Int, Param, Raw, Exit, Return
from lang.syntax import AST, parse, DasmSyntaxError
from lang.symbols import resolve

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
            Arg('color', Int(1), reg=Reg(n=0)),
            Arg('size', Int(2), reg=Reg(n=1)),
            Arg('buf', Int(3), reg=Reg(n=2)))
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


def test_exit_directive():
    assert parse('.exit\n') == [Exit()]


def test_return_directive():
    assert parse('return\n') == [Return()]
    assert parse('return 5\n') == [Return(Int(5))]
    assert parse('return -5\n') == [Return(Int(-5))]


@pytest.mark.parametrize("text", [
    '.bogus\n',
    '.foo 1, 2\n',
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


def test_raw():
    assert parse(".raw 0 * 1024") == [Raw(8, (Int(0),), 1024)]
    assert parse(".raw 1, 2 * 3") == [Raw(8, (Int(1), Int(2)), 3)]
    assert parse(".raw(16) 0xFFFF * 4") == [Raw(16, (Int(65535),), 4)]
    assert parse(".raw('ascii') 'ab' * 2") == [Raw('ascii', 'ab', 2)]
    assert parse('.raw("utf-8") "zażółć"') == [Raw('utf-8', 'zażółć', 1)]


@pytest.mark.parametrize("src", [
    ".raw(12) 1", ".raw('latin1') 'x'", ".raw(16) 'abc'", ".raw('ascii') 5",
    ".raw 0 * 0", ".raw 0 * -1", ".raw 'abc'", '.raw("\\x4") ', ".raw 007",
])
def test_raw_errors(src):
    with pytest.raises(DasmSyntaxError):
        parse(src)


def test_resolve_named_args_any_order():
    src = "foo(a: r0, b: r1):\nreturn\nfoo(b = 1, a = 2)\n"
    out = resolve(parse(src))
    call = out.filter(typeof=Call)[0]
    assert call.args[0].reg == Reg(1) and call.args[1].reg == Reg(0)
