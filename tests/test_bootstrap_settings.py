"""Unit tests for loading *.toml settings."""

import pytest

from bootstrap.settings import load_all, load_toml


def test_load_toml(tmp_path):
    path = tmp_path / 'dasm.toml'
    path.write_text('[dasm.options]\narch = "wasm"\n', encoding='utf-8')

    assert load_toml(str(path)) == {'dasm': {'options': {'arch': 'wasm'}}}


def test_load_toml_missing_file(tmp_path, capsys):
    settings = load_toml(str(tmp_path / 'missing.toml'))

    assert settings == {}
    assert 'not found' in capsys.readouterr().out


def test_load_toml_syntax_error(tmp_path, capsys):
    path = tmp_path / 'broken.toml'
    path.write_text('x = [\n', encoding='utf-8')

    with pytest.raises(SystemExit) as exc:
        load_toml(str(path))

    assert exc.value.code == 1
    assert 'syntax error in the TOML file' in capsys.readouterr().out


def test_load_toml_io_error(tmp_path, capsys):
    with pytest.raises(OSError):
        load_toml(str(tmp_path))

    assert 'I/O error reading' in capsys.readouterr().out


def test_load_all_merges_files_in_order(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'a.toml').write_text(
        '[dasm.options]\n'
        'arch = "wasm"\n'
        'common = 1\n'
        '[dasm.env]\n'
        'A = "1"\n'
        '[dasm.imports]\n'
        'paths = ["x", "y"]\n',
        encoding='utf-8',
    )
    (tmp_path / 'b.toml').write_text(
        '[dasm.options]\n'
        'arch = "mos6502"\n'
        'extra = 2\n'
        '[dasm.env]\n'
        'B = "2"\n'
        '[dasm.imports]\n'
        'paths = ["y", "z"]\n',
        encoding='utf-8',
    )
    (tmp_path / 'ignored.txt').write_text('not toml', encoding='utf-8')

    settings = load_all()

    assert settings['options'] == {
        'arch': 'mos6502', 'common': 1, 'extra': 2,
    }
    assert settings['env'] == {'A': '1', 'B': '2'}
    assert settings['paths'] == ['x', 'y', 'z']


def test_load_all_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert load_all() == {'options': {}, 'env': {}, 'paths': []}
