"""Integration tests for error line relocation after .import."""

from pathlib import Path

import pytest

from lang.exceptions import DasmSyntaxError
from lang.imports import resolve_with_map
from lang.preprocess import preprocess
from lang.syntax import parse


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _relocated_error(text, source_path):
    resolved = resolve_with_map(text, source_path=source_path)
    try:
        processed_text = preprocess(resolved.text)
        parse(processed_text)
    except DasmSyntaxError as e:
        return resolved.source_map.relocate(e)
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
        preprocess(resolved.text)

    error = resolved.source_map.relocate(exc.value)

    assert Path(error.file) == lib.resolve()
    assert error.line == 2
