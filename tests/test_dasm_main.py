"""Integration tests for the command line entry point."""

import runpy
import struct
import sys
from pathlib import Path

import pytest

import dasm


MAGIC = b'\x00asm'
MACHO_MAGIC = b'\xcf\xfa\xed\xfe'
MOV_X0_1 = 0xD2800020


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def test_display_path_none():
    assert dasm._display_path(None) is None


def test_display_path_relative():
    assert dasm._display_path('src/main.dasm') == 'src/main.dasm'


def test_display_path_absolute(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert dasm._display_path(tmp_path / 'src' / 'main.dasm') == str(
        Path('src') / 'main.dasm'
    )


def test_missing_source(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    assert dasm.main(['missing.dasm']) == 1
    assert 'File not found: missing.dasm' in capsys.readouterr().err


def test_build_wasm_with_explicit_output(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / 'prog.dasm', 'r0 = 1\n')

    code = dasm.main([
        'prog.dasm', '--arch', 'wasm', '--format', 'wasm', '-o', 'out',
    ])

    assert code == 0
    assert (tmp_path / 'out.wasm').read_bytes().startswith(MAGIC)
    out = capsys.readouterr().out
    assert 'dasm v' in out
    assert '"out.wasm"' in out


def test_default_output_name_and_debug_flag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / 'prog.dasm', 'r0 = 1\n')

    code = dasm.main(['prog.dasm', '--arch', 'wasm', '--format', 'wasm', '-d'])

    assert code == 0
    assert (tmp_path / 'prog.wasm').exists()


def test_output_extension_is_not_duplicated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / 'prog.dasm', 'r0 = 1\n')

    code = dasm.main([
        'prog.dasm', '--arch', 'wasm', '--format', 'wasm',
        '-o', 'prog.wasm',
    ])

    assert code == 0
    assert (tmp_path / 'prog.wasm').exists()
    assert not (tmp_path / 'prog.wasm.wasm').exists()


def test_syntax_error_is_reported(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / 'bad.dasm', 'r0 = \n')

    code = dasm.main(['bad.dasm', '--arch', 'wasm', '--format', 'wasm'])

    assert code == 1
    err = capsys.readouterr().err
    assert 'bad.dasm:1:6: syntax error' in err
    assert 'Expected' in err


def test_options_from_toml(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write(
        tmp_path / 'dasm.toml',
        '[dasm.options]\narch = "wasm"\nformat = "wasm"\n',
    )
    _write(tmp_path / 'prog.dasm', 'r0 = 1\n')

    code = dasm.main(['prog.dasm'])

    assert code == 0
    assert (tmp_path / 'prog.wasm').exists()
    assert 'Architecture...wasm' in capsys.readouterr().out


def test_entry_jump_from_start_label(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(
        tmp_path / 'dasm.toml',
        '[dasm.options]\narch = "mos6502"\nformat = "prg"\n',
    )
    _write(tmp_path / 'start.dasm', '.start main\nmain:\nr0 = 1\n')

    code = dasm.main(['start.dasm'])

    assert code == 0
    output = (tmp_path / 'start.prg').read_bytes()
    # Header + BASIC stub (14 bytes), then JMP main (0x0810) and LDA #1.
    assert output[14:17] == bytes([0x4C, 0x10, 0x08])
    assert output[17:] == bytes([0xA9, 0x01])


def test_mos6502_call_resolves_named_argument_register(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(
        tmp_path / 'call.dasm',
        'foo(value: r0):\nreturn\nfoo(value = 14)\n',
    )

    code = dasm.main([
        'call.dasm', '--arch', 'mos6502', '--format', 'prg',
    ])

    assert code == 0
    output = (tmp_path / 'call.prg').read_bytes()
    assert output[15:17] == bytes([0xA9, 0x0E])


def test_default_target_per_platform():
    assert dasm.default_target('darwin') == ('arm64', 'macho')
    assert dasm.default_target('linux') == ('x86', 'elf')
    assert dasm.default_target('linux2') == ('x86', 'elf')
    assert dasm.default_target('win32') == ('x86', 'exe')
    assert dasm.default_target('freebsd13') == ('arm64', 'macho')


def test_default_target_uses_current_platform():
    expected = next(
        (target for prefix, target in dasm.DEFAULT_TARGETS.items()
         if dasm.sys.platform.startswith(prefix)),
        ('arm64', 'macho'),
    )

    assert dasm.default_target() == expected


def test_default_arch_and_format(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(dasm.sys, 'platform', 'darwin')
    _write(tmp_path / 'prog.dasm', 'r0 = 1\n')

    code = dasm.main(['prog.dasm'])

    assert code == 0
    output = (tmp_path / 'prog.o').read_bytes()
    assert output.startswith(MACHO_MAGIC)
    # __text starts after the 32-byte header and 176 bytes of load commands.
    assert struct.unpack_from('<I', output, 208)[0] == MOV_X0_1


def test_module_entry_point(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / 'prog.dasm', 'r0 = 1\n')
    monkeypatch.setattr(sys, 'argv', [
        'dasm.py', 'prog.dasm', '--arch', 'wasm', '--format', 'wasm',
    ])

    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(Path(dasm.__file__)), run_name='__main__')

    assert exc.value.code == 0
    assert (tmp_path / 'prog.wasm').exists()
