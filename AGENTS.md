# AGENTS.md

## Purpose

This file provides working instructions for coding agents contributing to DASM. Follow it together with the user's request and the existing project documentation. Keep changes focused, explain assumptions, and avoid unrelated refactors.

## Project overview

DASM is a multi-architecture assembler with a small high-level language. Its compilation pipeline is:

```
.dasm source
  -> import resolution and source mapping
  -> preprocessing (.set and TOML constants)
  -> parsing into an AST
  -> semantic resolution with lang.symbols.resolve()
  -> architecture backend assembly
  -> output-format encoding
  -> output file
```

The project is a Python script-based project. It does not currently require installation as a package; run commands from the `dasm/` directory, or ensure that directory is on `PYTHONPATH`.

## Repository layout

- `dasm.py`: command-line entry point and compilation pipeline.
- `lang/`: lexical analysis, imports, preprocessing, parsing, AST types, symbol resolution, errors, and source maps.
- `arch/`: architecture backends selected with `--arch`.
- `format/`: output format backends selected with `--format`.
- `utils/`: dynamic module loading, TOML settings loading and logging system.
- `tests/`: unit and integration tests.
- `examples/`: example and exploratory `.dasm` sources; not every example is expected to be runnable.
- `docs/`: developer documentation.
- `build.toml`: project-local default configuration.

Read the relevant document in `docs/` before changing language syntax, preprocessing, imports, architecture contracts, formats, or CLI behavior.

## Development workflow

1. Inspect the relevant implementation, tests, and documentation before editing.
2. Make the smallest change that satisfies the request.
3. Add or update tests for behavior changes and regression fixes.
4. Update documentation when user-visible behavior, CLI options, language syntax, or backend contracts change.
5. Run focused tests first, then the full test suite when practical.
6. Review the final diff for accidental generated files, unrelated formatting, or changes outside the requested scope.

Use Python 3. Run commands from `dasm/`:

```bash
python3 -m pytest
python3 -m pytest tests/test_<relevant_area>.py
python3 dasm.py examples/<program>.dasm --arch wasm --format wasm
python3 dasm.py examples/<program>.dasm --arch mos6502 --format prg
```

The host-platform defaults are not equally implemented on every platform. On Linux and Windows, use explicit `--arch wasm --format wasm` or `--arch mos6502 --format prg` for smoke tests unless the task specifically concerns the default target.

## Architecture and format extensions

Architecture and format modules are loaded dynamically by `utils.modules.load_module`. A module must expose `EXPORTS` as a class or factory. Preserve this contract when adding or renaming modules.

Before implementing a new backend:

- Read `docs/architectures.md` or `docs/formats.md`.
- Follow the existing abstract interfaces and data types.
- Add the module export and focused tests.
- Prefer explicit, deterministic behavior over silently accepting unsupported instructions.
- Keep unsupported operations as clear errors unless the task explicitly adds support.

Remember that the current implementation is intentionally partial:

- `arm64`, `mos6502`, and `wasm` support only subsets of the language.
- `x86`, `elf`, and `exe` are placeholders.
- `alu48` is legacy and is not part of the normal supported path in the same way as the other backends.

Do not treat a placeholder or `NotImplementedError` as an accidental bug without checking the requested scope and project documentation.

## Language, imports, and diagnostics

Preserve source-location quality. Errors should continue to map back through imported files and preprocessing substitutions to the original source line and column.

When changing lexer, parser, preprocessor, import resolution, or AST behavior:

- Cover valid input and invalid input.
- Test line and column reporting where relevant.
- Test interactions with `.import`, `.set`, TOML constants, duplicate imports, and import cycles when applicable.
- Avoid changing public syntax or error wording without updating the corresponding documentation and tests.

## CLI and configuration

The effective option precedence is:

```
CLI arguments > *.toml settings > host-platform defaults
```

The CLI accepts a source path, `--arch`, `--format`, `-o/--output`, `-d/--debug`, and `-l/--log`. TOML settings may define `[dasm.options]`, `[dasm.env]`, and `[dasm.imports].paths`.

Keep output behavior compatible unless the task explicitly changes it:

- Output is written in binary mode.
- The selected format supplies the output extension.
- `-o name` receives the format extension when it is missing.
- Import, syntax, preprocessing, and semantic-resolution failures return a non-zero status and include source location information where available.

## Python style

- Use clear, idiomatic Python compatible with the project's supported interpreter.
- Preserve the existing public names and module layout unless a migration is requested.
- Prefer small functions with explicit inputs and outputs.
- Use type annotations where they improve clarity and match surrounding code.
- Avoid introducing unnecessary dependencies, global state, or framework abstractions.
- Do not use forceful or destructive filesystem operations in application code.
- Keep comments for non-obvious behavior, especially source mapping, binary encoding, relocation, and platform defaults.

## Tests and generated files

Tests use `pytest`. New tests should be deterministic and should not depend on the developer's current platform unless platform behavior is the subject under test.

Do not commit generated or local-development artifacts, including:

- `__pycache__/`
- `.pytest_cache/`
- virtual environments
- generated binary output such as `.bin`, `.elf`, `.hex`, `.o`, `.prg`, and `.wasm`
- local configuration such as `local.toml`

Use temporary directories for test outputs whenever possible.

## Documentation and handoff

Documentation is currently partly written in Polish; new agent-facing instructions belong in English, while user-facing documentation should follow the language and style of the document being edited.

In the final handoff, summarize:

- what changed;
- which tests or smoke checks were run;
- any known limitations or tests that could not be run.

Never claim that a test or build passed unless it was actually executed.
