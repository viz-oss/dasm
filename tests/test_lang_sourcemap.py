"""Unit tests for the source line map."""

from pathlib import Path

from lang.exceptions import DasmSyntaxError
from lang.sourcemap import (
    ColumnMap,
    ColumnSegment,
    SourceLocation,
    SourceMap,
)


def test_lookup_single_file():
    main = Path("main.dasm")
    source_map = SourceMap([
        SourceLocation(main, 1),
        SourceLocation(main, 2),
        SourceLocation(main, 3),
    ])

    assert source_map.lookup(1) == SourceLocation(main, 1)
    assert source_map.lookup(2) == SourceLocation(main, 2)
    assert source_map.lookup(3) == SourceLocation(main, 3)
    assert source_map.lookup(4) is None
    assert source_map.lookup(0) is None


def test_lookup_with_imported_segment():
    main = Path("main.dasm")
    lib = Path("lib.dasm")
    source_map = SourceMap([
        SourceLocation(main, 1),
        SourceLocation(lib, 1),
        SourceLocation(lib, 2),
        SourceLocation(main, 2),
    ])

    assert source_map.lookup(1) == SourceLocation(main, 1)
    assert source_map.lookup(2) == SourceLocation(lib, 1)
    assert source_map.lookup(3) == SourceLocation(lib, 2)
    assert source_map.lookup(4) == SourceLocation(main, 2)


def test_relocate_preserves_details():
    main = Path("main.dasm")
    lib = Path("lib.dasm")
    source_map = SourceMap([
        SourceLocation(main, 1),
        SourceLocation(lib, 1),
    ])
    error = DasmSyntaxError(
        line=2, col=7, expected=["register"], message="context"
    )

    result = source_map.relocate(error)

    assert result is error
    assert result.file == str(lib)
    assert result.line == 1
    assert result.col == 7
    assert result.expected == ["register"]
    assert result.message == "context"


def test_relocate_skips_error_with_file():
    source_map = SourceMap([SourceLocation(Path("main.dasm"), 1)])
    error = DasmSyntaxError(line=2, col=1, message="x", file="already.dasm")

    result = source_map.relocate(error)

    assert result is error
    assert result.file == "already.dasm"
    assert result.line == 2


def test_relocate_without_line_or_mapping():
    source_map = SourceMap([SourceLocation(Path("main.dasm"), 1)])

    no_line = DasmSyntaxError(message="x")
    assert source_map.relocate(no_line) is no_line

    outside = DasmSyntaxError(line=99, col=1, message="x")
    assert source_map.relocate(outside) is outside
    assert outside.line == 99


def test_column_map_copies_one_to_one():
    column_map = ColumnMap([
        ColumnSegment(1, 3, 1),
        ColumnSegment(4, 4, 4),
    ])

    assert [column_map.lookup(col) for col in range(1, 5)] == [1, 2, 3, 4]


def test_column_map_substitution_longer():
    # X = 1  ->  1000 = 1
    column_map = ColumnMap([
        ColumnSegment(1, 4, 1, fixed=True),
        ColumnSegment(5, 5, 2),
        ColumnSegment(6, 6, 3),
        ColumnSegment(7, 7, 4),
        ColumnSegment(8, 8, 5),
    ])

    assert [column_map.lookup(col) for col in range(1, 5)] == [1, 1, 1, 1]
    assert column_map.lookup(5) == 2
    assert column_map.lookup(6) == 3
    assert column_map.lookup(7) == 4
    assert column_map.lookup(8) == 5


def test_column_map_substitution_shorter():
    # LONG_NAME = 1  ->  1 = 1
    column_map = ColumnMap([
        ColumnSegment(1, 1, 1, fixed=True),
        ColumnSegment(2, 2, 10),
        ColumnSegment(3, 3, 11),
        ColumnSegment(4, 4, 12),
        ColumnSegment(5, 5, 13),
    ])

    assert column_map.lookup(1) == 1
    assert column_map.lookup(2) == 10
    assert column_map.lookup(3) == 11
    assert column_map.lookup(4) == 12
    assert column_map.lookup(5) == 13


def test_empty_column_map_is_identity():
    column_map = ColumnMap()

    assert column_map.lookup(7) == 7


def test_column_map_before_first_segment_is_identity():
    column_map = ColumnMap([ColumnSegment(5, 6, 5)])

    assert column_map.lookup(1) == 1


def test_original_line_reads_and_caches_file(tmp_path):
    src = tmp_path / "main.dasm"
    src.write_text("one\ntwo\n", encoding="utf-8")
    source_map = SourceMap([SourceLocation(src, 1)])

    assert source_map.original_line(SourceLocation(src, 2)) == "two"
    assert source_map.original_line(SourceLocation(src, 2)) == "two"
    assert source_map.original_line(SourceLocation(src, 99)) is None


def test_original_line_missing_file():
    source_map = SourceMap([])

    assert source_map.original_line(SourceLocation(Path("missing.dasm"), 1)) is None


def test_relocate_maps_columns_and_formats_context(tmp_path):
    src = tmp_path / "main.dasm"
    src.write_text("r0 = X +\n", encoding="utf-8")
    source_map = SourceMap([SourceLocation(src, 1)])
    column_map = ColumnMap([
        ColumnSegment(1, 1, 1),
        ColumnSegment(2, 2, 5),
    ])
    error = DasmSyntaxError(
        line=1, col=2, message="context", map_columns=True, context=True,
    )

    result = source_map.relocate(error, [column_map])

    assert result.col == 5
    assert "r0 = X +" in result.message
    assert result.message.splitlines()[-1] == "    ^"


def test_relocate_without_column_maps_skips_context(tmp_path):
    src = tmp_path / "main.dasm"
    src.write_text("r0 = X +\n", encoding="utf-8")
    source_map = SourceMap([SourceLocation(src, 1)])
    error = DasmSyntaxError(
        line=1, col=2, message="context", map_columns=True, context=True,
    )

    result = source_map.relocate(error)

    assert result.col == 2
    assert result.message == "context"
