"""Unit tests for .import resolution."""

from pathlib import Path

import pytest

from lang.exceptions import DasmSyntaxError
from lang.imports import resolve, resolve_with_map
from lang.preprocess import preprocess
from lang.sourcemap import SourceLocation


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_import_inlines_file(tmp_path):
    lib = _write(tmp_path / "lib.dasm", "r0 = 1\n")
    src = _write(tmp_path / "main.dasm", ".import 'lib.dasm'\nr0 = 2\n")

    result = resolve(src.read_text(encoding="utf-8"), source_path=src)

    assert result == "r0 = 1\nr0 = 2\n"


def test_import_accepts_double_quotes(tmp_path):
    _write(tmp_path / "lib.dasm", "r0 = 1\n")
    src = _write(tmp_path / "main.dasm", '.import "lib.dasm"\n')

    result = resolve(src.read_text(encoding="utf-8"), source_path=src)

    assert result == "r0 = 1\n"


def test_import_expands_env_and_appends_dasm(tmp_path):
    _write(tmp_path / "sys" / "c64" / "vic.dasm", ".set COLOR = 13\n")
    src = _write(tmp_path / "main.dasm", ".import 'sys/{OS}/vic'\n")

    result = resolve(
        src.read_text(encoding="utf-8"), env={"OS": "c64"}, source_path=src
    )

    assert result == ".set COLOR = 13\n"


def test_import_uses_configured_paths(tmp_path):
    _write(tmp_path / "lib" / "vic.dasm", "r0 = 1\n")
    src = _write(tmp_path / "src" / "main.dasm", ".import 'vic'\n")

    result = resolve(
        src.read_text(encoding="utf-8"),
        paths=[str(tmp_path / "lib")],
        source_path=src,
    )

    assert result == "r0 = 1\n"


def test_import_searches_relative_to_importing_file_first(tmp_path):
    _write(tmp_path / "main.dasm", ".import 'lib.dasm'\n")
    _write(tmp_path / "lib.dasm", "r0 = 1\n")
    _write(tmp_path / "other" / "lib.dasm", "r0 = 2\n")

    result = resolve(
        (tmp_path / "main.dasm").read_text(encoding="utf-8"),
        paths=[str(tmp_path / "other")],
        source_path=tmp_path / "main.dasm",
    )

    assert result == "r0 = 1\n"


def test_nested_import_is_relative_to_imported_file(tmp_path):
    _write(tmp_path / "sub" / "b.dasm", "r0 = 2\n")
    _write(tmp_path / "sub" / "a.dasm", ".import 'b.dasm'\nr0 = 1\n")
    src = _write(tmp_path / "main.dasm", ".import 'sub/a.dasm'\n")

    result = resolve(src.read_text(encoding="utf-8"), source_path=src)

    assert result == "r0 = 2\nr0 = 1\n"


def test_duplicate_import_is_inlined_once(tmp_path):
    _write(tmp_path / "lib.dasm", "r0 = 1\n")
    src = _write(
        tmp_path / "main.dasm",
        ".import 'lib.dasm'\n.import 'lib.dasm'\nr0 = 2\n",
    )

    result = resolve(src.read_text(encoding="utf-8"), source_path=src)

    assert result.count("r0 = 1") == 1
    assert result == "r0 = 1\n\nr0 = 2\n"


def test_circular_import_raises(tmp_path):
    _write(tmp_path / "b.dasm", ".import 'a.dasm'\n")
    src = _write(tmp_path / "a.dasm", ".import 'b.dasm'\n")

    with pytest.raises(DasmSyntaxError) as exc:
        resolve(src.read_text(encoding="utf-8"), source_path=src)

    assert "circular import" in str(exc.value)


def test_missing_import_raises_with_line(tmp_path):
    src = _write(tmp_path / "main.dasm", "r0 = 0\n.import 'missing.dasm'\n")

    with pytest.raises(DasmSyntaxError) as exc:
        resolve(src.read_text(encoding="utf-8"), source_path=src)

    assert exc.value.line == 2
    assert "file not found" in str(exc.value)
    assert "missing.dasm" in str(exc.value)


def test_unknown_env_variable_raises(tmp_path):
    src = _write(tmp_path / "main.dasm", ".import 'sys/{MISSING}/vic.dasm'\n")

    with pytest.raises(DasmSyntaxError) as exc:
        resolve(src.read_text(encoding="utf-8"), env={}, source_path=src)

    assert "unknown environment variable 'MISSING'" in str(exc.value)


def test_import_inside_comment_is_ignored(tmp_path):
    src = _write(
        tmp_path / "main.dasm", "; .import 'missing.dasm'\nr0 = 1\n"
    )

    result = resolve(src.read_text(encoding="utf-8"), source_path=src)

    assert result == "; .import 'missing.dasm'\nr0 = 1\n"


def test_imported_set_is_visible_to_preprocess(tmp_path):
    _write(tmp_path / "lib.dasm", ".set COLOR = 13\n")
    src = _write(
        tmp_path / "main.dasm", ".import 'lib.dasm'\nr0 = COLOR\n"
    )

    full_text = resolve(src.read_text(encoding="utf-8"), source_path=src)
    result = preprocess(full_text)

    assert result == "\nr0 = 13\n"


def test_resolve_with_map_marks_imported_lines(tmp_path):
    lib = _write(tmp_path / "lib.dasm", "r0 = 1\nr0 = 2\n")
    src = _write(
        tmp_path / "main.dasm", ".import 'lib.dasm'\nr0 = 3\n"
    )

    resolved = resolve_with_map(
        src.read_text(encoding="utf-8"), source_path=src
    )

    assert resolved.text == "r0 = 1\nr0 = 2\nr0 = 3\n"
    assert resolved.source_map.lookup(1) == SourceLocation(lib.resolve(), 1)
    assert resolved.source_map.lookup(2) == SourceLocation(lib.resolve(), 2)
    assert resolved.source_map.lookup(3) == SourceLocation(src.resolve(), 2)


def test_resolve_with_map_handles_nested_imports(tmp_path):
    _write(tmp_path / "sub" / "b.dasm", "r0 = 2\n")
    _write(tmp_path / "sub" / "a.dasm", ".import 'b.dasm'\nr0 = 1\n")
    src = _write(tmp_path / "main.dasm", ".import 'sub/a.dasm'\n")

    resolved = resolve_with_map(
        src.read_text(encoding="utf-8"), source_path=src
    )

    assert resolved.text == "r0 = 2\nr0 = 1\n"
    assert resolved.source_map.lookup(1) == SourceLocation(
        (tmp_path / "sub" / "b.dasm").resolve(), 1
    )
    assert resolved.source_map.lookup(2) == SourceLocation(
        (tmp_path / "sub" / "a.dasm").resolve(), 2
    )


def test_duplicate_import_maps_to_import_line(tmp_path):
    _write(tmp_path / "lib.dasm", "r0 = 1\n")
    src = _write(
        tmp_path / "main.dasm",
        ".import 'lib.dasm'\n.import 'lib.dasm'\nr0 = 2\n",
    )

    resolved = resolve_with_map(
        src.read_text(encoding="utf-8"), source_path=src
    )

    assert resolved.text == "r0 = 1\n\nr0 = 2\n"
    assert resolved.source_map.lookup(2) == SourceLocation(src.resolve(), 2)
    assert resolved.source_map.lookup(3) == SourceLocation(src.resolve(), 3)


def test_import_error_has_source_file(tmp_path):
    src = _write(tmp_path / "main.dasm", ".import 'missing.dasm'\n")

    with pytest.raises(DasmSyntaxError) as exc:
        resolve(src.read_text(encoding="utf-8"), source_path=src)

    assert Path(exc.value.file) == src.resolve()


def test_preprocess_preserves_line_count(tmp_path):
    _write(tmp_path / "lib.dasm", ".set COLOR = 13\nr0 = 1\n")
    src = _write(
        tmp_path / "main.dasm", ".import 'lib.dasm'\nr0 = COLOR\n"
    )

    full_text = resolve(src.read_text(encoding="utf-8"), source_path=src)
    processed_text = preprocess(full_text)

    assert len(full_text.split("\n")) == len(processed_text.split("\n"))
