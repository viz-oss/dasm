"""Integration tests for error line relocation after .import."""

from pathlib import Path

import pytest

from lang.exceptions import DasmSyntaxError
from lang.imports import resolve_with_map
from lang.preprocess import preprocess_with_map
from lang.syntax import parse


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _relocated_error(text, source_path):
    resolved = resolve_with_map(text, source_path=source_path)
    preprocessed = None
    try:
        preprocessed = preprocess_with_map(resolved.text)
        parse(preprocessed.text)
    except DasmSyntaxError as e:
        column_maps = preprocessed.column_maps if preprocessed else None
        return resolved.source_map.relocate(e, column_maps)
    raise AssertionError("expected DasmSyntaxError")


def test_error_in_root_after_import(tmp_path):
    _write(tmp_path / "lib.dasm", ".set COLOR = 2\n")
    src = _write(
        tmp_path / "main.dasm", ".import 'lib.dasm'\nr = COLOR\n"
    )

    error = _relocated_error(src.read_text(encoding="utf-8"), src)

    assert Path(error.file) == src.resolve()
    assert error.line == 2


def test_error_in_imported_file(tmp_path):
    lib = _write(tmp_path / "lib.dasm", "r0 = 1\nr = 2\n")
    src = _write(
        tmp_path / "main.dasm", ".import 'lib.dasm'\nr0 = 3\n"
    )

    error = _relocated_error(src.read_text(encoding="utf-8"), src)

    assert Path(error.file) == lib.resolve()
    assert error.line == 2


def test_preprocess_error_in_imported_file(tmp_path):
    lib = _write(tmp_path / "lib.dasm", ".set X = 1\n.set X = 2\n")
    src = _write(tmp_path / "main.dasm", ".import 'lib.dasm'\n")

    resolved = resolve_with_map(
        src.read_text(encoding="utf-8"), source_path=src
    )
    with pytest.raises(DasmSyntaxError) as exc:
        preprocess_with_map(resolved.text)

    error = resolved.source_map.relocate(exc.value)

    assert Path(error.file) == lib.resolve()
    assert error.line == 2
    assert error.col == 1
    assert error.message == "constant 'X' already defined"


def test_column_is_relocated_after_substitution(tmp_path):
    src = _write(
        tmp_path / "main.dasm",
        ".set X = 1000\nr0 = X +\n",
    )

    error = _relocated_error(src.read_text(encoding="utf-8"), src)

    assert Path(error.file) == src.resolve()
    assert error.line == 2
    assert error.col == 8


def test_context_shows_original_line(tmp_path):
    src = _write(
        tmp_path / "main.dasm",
        ".set X = 1000\nr0 = X +\n",
    )

    error = _relocated_error(src.read_text(encoding="utf-8"), src)

    assert "r0 = X +" in error.message
    assert "r0 = 1000 +" not in error.message
    assert error.message.splitlines()[-1] == "       ^"


def test_str_uses_relocated_context(tmp_path):
    src = _write(
        tmp_path / "main.dasm",
        ".set X = 1000\nr0 = X +\n",
    )

    error = _relocated_error(src.read_text(encoding="utf-8"), src)

    assert "r0 = X +" in str(error)
    assert "r0 = 1000 +" not in str(error)


def test_context_aligns_caret_after_tabs(tmp_path):
    src = _write(
        tmp_path / "main.dasm",
        ".set X = 1000\n\tr0 = X +\n",
    )

    error = _relocated_error(src.read_text(encoding="utf-8"), src)

    assert error.col == 9
    assert error.message.splitlines()[-1] == "               ^"


def test_context_shows_original_imported_line(tmp_path):
    lib = _write(
        tmp_path / "lib.dasm", ".set VIC_RED = 2\nr = VIC_RED\n"
    )
    src = _write(tmp_path / "main.dasm", ".import 'lib.dasm'\n")

    error = _relocated_error(src.read_text(encoding="utf-8"), src)

    assert Path(error.file) == lib.resolve()
    assert error.line == 2
    assert error.col == 5
    assert "r = VIC_RED" in error.message
    assert "r = 2" not in error.message
