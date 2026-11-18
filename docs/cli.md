# Running and Configuration

## Basic Usage

```bash
python3 dasm.py program.dasm
python3 dasm.py program.dasm --arch mos6502 --format prg
python3 dasm.py program.dasm --arch wasm --format wasm -o build/program
python3 dasm.py program.dasm -d
```

`dasm.py` does not require installation or a package — it only needs to be run from the project directory (or have that directory added to `PYTHONPATH`). The version is displayed at startup: `dasm vX.Y.Z`.

## Options

| Option | Meaning |
|---|---|
| `source` | path to the input `.dasm` file (required) |
| `--arch NAME` | architecture: `alu48`, `arm64`, `mos6502`, `wasm`, `x86` |
| `--format NAME` | format: `bin`, `elf`, `hex`, `macho`, `prg`, `wasm`, `exe` |
| `-o`, `--output PATH` | output filename |
| `-d`, `--debug` | sets `debug = True` in options; currently has no other effect (prepared for generate debug symbols) |
| `-l`, `--log [GROUPS]` | enables logging: without value, all modules; with value, selected groups (`lang`, `lang.preprocess`, `lang+utils`) |
| `-h`, `--help` | argparse help |
## Logging

The `-l`/`--log` argument enables assembler logging. An empty argument logs all modules; a value filters by groups named like packages (`lang`, `lang.preprocess`, `lang+utils`):

```bash
python3 dasm.py program.dasm --log
python3 dasm.py program.dasm --log lang
python3 dasm.py program.dasm --log lang.preprocess
python3 dasm.py program.dasm --log lang+format
```

Entries are in the format `[logger.name] message` and go to stdout. By default, logging is disabled. `--log` is independent of `-d`/`--debug`, which only sets the `debug` option. Details on logging, groups, and how to add logs in new modules can be found in [logging.md](logging.md).

## Default Architecture and Format

The default pair depends on `sys.platform`:

| System | `sys.platform` | Default Architecture | Default Format |
|---|---|---|---|
| macOS | `darwin` | `arm64` | `macho` |
| Linux | `linux`, `linux2` | `x86` | `elf` |
| Windows | `win32` | `x86` | `exe` |
| Other | — | `arm64` | `macho` |

> On Linux and Windows, the default run will not work until `x86`, `elf`, and `exe` are implemented. For testing, explicitly use `--arch wasm --format wasm` or `--arch mos6502 --format prg`.

**Selection Order:** **CLI arguments > `*.toml` > platform defaults**.

## `*.toml` Files

When DASM runs, it loads **all** `*.toml` files from the current directory (sorted by name). Later files override earlier ones in `options` and `env`, while `paths` are concatenated and deduplicated while preserving order.

```toml
[dasm.options]
arch = "mos6502"
format = "prg"
debug = false

[dasm.env]
OS = "c64"
VIC_BORDER = 0xD020

[dasm.imports]
paths = ["../lib", "lib"]
```

| Section | Meaning |
|---|---|
| `[dasm.options]` | default `arch`, `format`, `debug` (overridden by CLI) |
| `[dasm.env]` | variables for `{NAME}` in `.import` **and** constants available in the preprocessor from the first line |
| `[dasm.imports].paths` | additional search directories for imports (relative to execution directory) |
## Output Filename

- `-o out` results in `out.<ext>` (extension is appended if missing).
- `-o out.wasm` results in `out.wasm` (no double extension).
- Without `-o`, the source name is used, replacing `.dasm` with `.<ext>`, e.g., `program.dasm` → `program.wasm`, `program.dasm` → `program.prg`.
- Output is written in binary mode (`wb`), so `Format.output()` must return `bytes`.

## Exit Codes and Messages

| Situation | Code | Message |
|---|---|---|
| Success | `0` | subsequent stages: `Parsing...OK`, `Architecture...<arch>`, `Assembly...OK`, `Format...<format>`, `"file"` |
| Source file not found | `1` | `File not found: <path>` on `stderr` |
| Syntax/Preprocessor error | `1` | `<file>:<line>:<column>: syntax error` + error content on `stderr` |
| Argument error | `2` | argparse message |
| Module/Formatting error | — | uncaught exception (Python traceback) |

Logs (`--log`) go to stdout and do not change exit codes; diagnostics are on stderr. The logging system description is in [logging.md](logging.md).

Syntax errors are relocated to the original file and line (including after `.import`), and the column to the original text before constant substitution. Details: [errors.md](errors.md).

## Module Loading

Architectures and formats are dynamically imported via `utils.modules.load_module(dir, name)`:

1. `dir` and `name` may only contain letters, numbers, and `_`.
2. The module `dir.name` is imported (with `lru_cache(32)`),
3. the module must export `EXPORTS` as a class or function,
4. `load_module()` returns `EXPORTS()` (a ready instance).

Lack of `EXPORTS` results in `DasmSyntaxError: Module <dir>/<name>.py does not contain EXPORTS`. The contracts for architectures and formats are described in [architectures.md](architectures.md) and [formats.md](formats.md).
