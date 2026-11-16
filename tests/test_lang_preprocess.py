"""Unit tests for column maps produced by the preprocessor."""

import pytest

from lang.exceptions import DasmSyntaxError
from lang.preprocess import preprocess, preprocess_with_map


def test_column_map_after_longer_substitution():
    result = preprocess_with_map("X = 1\n", {"X": 1000})

    assert result.text == "1000 = 1\n"
    column_map = result.column_maps[0]
    assert [column_map.lookup(col) for col in range(1, 5)] == [1, 1, 1, 1]
    assert column_map.lookup(5) == 2
    assert column_map.lookup(6) == 3
    assert column_map.lookup(8) == 5


def test_column_map_after_shorter_substitution():
    result = preprocess_with_map(
        ".set LONG_NAME = 1\nLONG_NAME = 2\n"
    )

    assert result.text == "\n1 = 2\n"
    column_map = result.column_maps[1]
    assert column_map.lookup(1) == 1
    assert column_map.lookup(2) == 10
    assert column_map.lookup(3) == 11
    assert column_map.lookup(4) == 12
    assert column_map.lookup(5) == 13


def test_set_line_has_empty_column_map():
    result = preprocess_with_map(".set X = 1\nr0 = X\n")

    assert result.column_maps[0].segments == []
    assert result.column_maps[1].lookup(6) == 6


def test_column_map_handles_tabs():
    result = preprocess_with_map("\tX = 1\n", {"X": 1000})

    assert result.text == "\t1000 = 1\n"
    assert result.column_maps[0].lookup(2) == 2


def test_column_maps_match_line_count():
    result = preprocess_with_map(".set X = 1\n\nr0 = X\n")

    assert len(result.column_maps) == len(result.text.split("\n"))


def test_set_number_is_substituted():
    result = preprocess_with_map(".set X = 0x10\nr0 = X\n")

    assert result.text == "\nr0 = 16\n"


def test_set_string_is_quoted():
    assert preprocess('.set NAME = "abc"\n.text NAME\n') == '\n.text "abc"\n'


def test_set_rejects_register_name():
    with pytest.raises(DasmSyntaxError, match='reserved for registers'):
        preprocess(".set r1 = 2\n")


def test_set_rejects_non_number_value():
    with pytest.raises(DasmSyntaxError, match='must be a number or a string'):
        preprocess(".set X = abc\n")


def test_set_rejects_invalid_number():
    with pytest.raises(DasmSyntaxError, match="invalid number '09'"):
        preprocess(".set X = 09\n")


def test_set_requires_name_and_value():
    with pytest.raises(DasmSyntaxError, match='expected: .set NAME'):
        preprocess(".set X\n")


def test_set_rejects_invalid_string_literal():
    with pytest.raises(DasmSyntaxError, match='invalid string literal'):
        preprocess('.set X = "\\x"\n')


def test_set_rejects_duplicate_definition():
    with pytest.raises(DasmSyntaxError, match="constant 'X' already defined"):
        preprocess(".set X = 1\n.set X = 2\n")


def test_config_wins_over_set():
    result = preprocess(".set X = 123\nr0 = X\n", {"X": 7})

    assert result == "\nr0 = 7\n"


def test_config_rejects_bool():
    with pytest.raises(DasmSyntaxError, match='expected int or string, got bool'):
        preprocess("", {"X": True})


def test_config_rejects_invalid_name():
    with pytest.raises(DasmSyntaxError, match="invalid constant name 'bad-name'"):
        preprocess("", {"bad-name": 1})


def test_constants_are_not_substituted_in_special_contexts():
    text = '.set X = 1\n; X\n// X\n# X\nr0 = "X"\nX:\n.text "X"\n'

    assert preprocess(text) == '\n; X\n// X\n# X\nr0 = "X"\nX:\n.text "X"\n'
