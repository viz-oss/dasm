"""Unit tests for parser exceptions."""

from lang.exceptions import DasmSyntaxError


def test_annotations_describe_error_fields():
    assert DasmSyntaxError.__annotations__ == {
        'line': int | None,
        'col': int | None,
        'expected': list[str] | None,
        'message': str,
        'file': str | None,
        'map_columns': bool,
        'context': bool,
    }


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
