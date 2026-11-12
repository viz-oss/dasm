"""Unit tests for column maps produced by the preprocessor."""

from lang.preprocess import preprocess_with_map


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
