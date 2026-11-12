"""Unit tests for the source line map."""

from pathlib import Path

from lang.exceptions import DasmSyntaxError
from lang.sourcemap import SourceLocation, SourceMap


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
