"""Unit tests for parser exceptions."""

from lang.exceptions import DasmSyntaxError


def test_location_includes_file_and_position():
    error = DasmSyntaxError(line=3, col=7, file='source.dasm')
    assert error.location() == 'source.dasm:3:7'


def test_defaults():
    error = DasmSyntaxError()

    assert error.line is None
    assert error.col is None
    assert error.expected is None
    assert error.message == ''
    assert error.file is None
    assert error.map_columns is False
    assert error.context is False
    assert str(error) == ''


def test_str_lists_expected_tokens():
    error = DasmSyntaxError(
        line=1, col=2, expected=['register', 'number'], message='bad input'
    )

    assert str(error) == 'Expected register or number\n\nbad input'


def test_str_without_expected():
    error = DasmSyntaxError(line=1, col=1, message='bad input')

    assert str(error) == 'bad input'
