# DASM
v2.0.2

DASM is a multi-architecture assembler with a small, high-level assembly language. It combines familiar low-level concepts—registers, labels, calls, jumps, and directives—with a modular compiler pipeline and interchangeable architecture and output-format backends.

The project is intentionally focused on a small and understandable core. It is suitable for experimenting with assembly-language design, code generation, binary formats, retro-computing targets, and WebAssembly.

## Design principles

DASM follows these principles:

1. **Simplicity and minimalism** — the language should remain small enough to understand.
2. **Unambiguous behavior** — source code should have one clear interpretation.
3. **One straightforward way to solve a problem** — avoid unnecessary alternatives and special cases.
4. **Portability** — keep the language and compiler architecture usable across platforms and targets.
5. **Readability and speed** — clear, efficient code is more valuable than trying to prevent every possible mistake. Just don’t make any mistakes.
6. **In-place memory-oriented work** — prefer direct work with memory and avoid unnecessary dynamic allocations.
7. **Pragmatic syntax** — minor stylistic details should not get in the way where the language permits flexibility. Semantic distinctions still matter; for example, labels are case-sensitive.

## Current status

DASM is an active, partially implemented project. The language, compiler pipeline, and extension interfaces are usable, but architecture support is intentionally incomplete.

### Architecture backends

| Backend | Status |
|---|---|
| `arm64` | Partial: moving constants to registers is supported through `MOVZ`; most other operations are not implemented yet. |
| `mos6502` | Partial: immediate loads, absolute stores, `call`, `ret`, `exit`, and `jmp` are supported; most addressing modes are still stubs. |
| `wasm` | Partial: register operations, `load`, `store`, `return`, and `exit` are supported; calls, jumps, and label addresses are incomplete. |
| `x86` | Placeholder. |
| `alu48` | Experimental backend for a custom handmade ALU; available through the module loader but outside the normal CPU-oriented path. |

### Output formats

| Format | Status |
|---|---|
| `bin` | Implemented. |
| `prg` | Implemented for Commodore 64-style PRG output. |
| `hex` | Implemented as textual hexadecimal output. |
| `macho` | Implemented for a single `__text` section. |
| `wasm` | Implemented for a single function. |
| `elf` | Placeholder. |
| `exe` | Placeholder. |

On macOS, the default target is `arm64` with `macho`. Linux defaults to `x86` with `elf`, and Windows defaults to `x86` with `exe`. Because those Linux and Windows backends are placeholders, use an explicit supported target such as `--arch wasm --format wasm` or `--arch mos6502 --format prg` when testing on those platforms.

## Requirements

- Python 3.14
- lark
- pytest (for development only)

Run commands from the `dasm/` directory, or make that directory available through `PYTHONPATH`.

## Quick start

Compile a source file using the host-platform defaults:

```bash
python3 dasm.py program.dasm
```

Select an architecture and output format explicitly:

```bash
python3 dasm.py program.dasm --arch mos6502 --format prg
python3 dasm.py program.dasm --arch wasm --format wasm -o build/program
```

Show command-line help:

```bash
python3 dasm.py --help
```

A successful compilation runs through parsing, architecture assembly, format encoding, and binary output. If no output path is provided, the source filename is reused with the selected format extension:

```
program.dasm -> program.wasm
program.dasm -> program.prg
```

When `-o name` is used, the appropriate extension is added if it is missing.

## A small language

DASM source files use the `.dasm` extension. A program is made up of labels, assignments, calls, directives, and returns. Indentation is optional.

Registers are virtual. An architecture backend maps them to physical registers, WebAssembly locals, or another target-specific representation:

```asm
.start main

main:
    r0 = 1
    r1 = r0
    return
```

Assignments can use constants, registers, labels, or addresses:

```asm
r0 = 42
r1 = 0x20
r2 = message
0xD020 = r0

message:
    .raw("ascii") "Hello\\n"
```

Labels may contain Unicode characters, digits, underscores, and emoji, provided they do not begin with a digit. The language supports `;`, `#`, and `//` line comments.

The exact instructions and addressing modes available depend on the selected architecture backend. Unsupported operations are reported explicitly rather than silently accepted.

Parsing and semantic validation are separate steps. `parse()` creates the AST; `lang.symbols.resolve()` can then validate labels, pointer symbols, call signatures, and fill `Arg.reg`. The current CLI invokes the parser but does not yet invoke the resolver.

## Configuration

DASM automatically loads all `*.toml` files in the current directory, in filename order. Later files override earlier option and environment values. Import paths are combined and deduplicated while preserving their order.

A typical `build.toml` looks like this:

```toml
[dasm.options]
arch = "mos6502"
format = "prg"
debug = false

[dasm.env]
OS = "c64"

[dasm.imports]
paths = ["../lib"]
```

The effective precedence is:

```
command-line arguments > *.toml settings > host-platform defaults
```

The main configuration sections are:

| Section | Purpose |
|---|---|
| `[dasm.options]` | Default architecture, output format, and debug flag. |
| `[dasm.env]` | Constants available to the preprocessor and variables used while resolving imports. |
| `[dasm.imports].paths` | Additional import directories, resolved relative to the working directory. |

## Compilation pipeline

The compiler processes a source file in the following order:

```
.dasm source
  -> import resolution and source mapping
  -> preprocessing (.set and TOML constants)
  -> parsing into an AST
  -> optional semantic resolution (lang.symbols.resolve)
  -> architecture backend assembly
  -> output-format encoding
  -> output file
```

Source maps preserve the original file, line, and column information through imports and preprocessing substitutions. This makes syntax errors easier to diagnose even when the failing text came from an imported file or a replacement.

## Project layout

```
dasm.py       # Command-line entry point and compilation pipeline
arch/         # Architecture backends selected with --arch
format/       # Output-format backends selected with --format
lang/         # Lexer, imports, preprocessor, parser, AST, symbols, errors, and source maps
bootstrap/    # Dynamic module loading and TOML settings
tests/        # Unit and integration tests
examples/     # Example and exploratory .dasm source files
docs/         # Detailed language and developer documentation
```

Architecture and format modules are loaded dynamically. Each module must expose an `EXPORTS` class or factory. This keeps new targets independent from the main command-line driver.

## Documentation

Detailed documentation is available in the [`docs/`](docs/) directory:

| Document | Description |
|---|---|
| [CLI and configuration](docs/cli.md) | Command-line options, TOML settings, output names, and exit codes. |
| [Language syntax](docs/syntax.md) | Labels, registers, assignments, calls, directives, strings, and limitations. |
| [Preprocessor](docs/preprocess_set.md) | `.set`, configuration constants, substitutions, and column mapping. |
| [Imports](docs/import.md) | `.import`, search paths, environment variables, duplicates, and cycles. |
| [Architecture backends](docs/architectures.md) | Architecture interfaces, relocation, and backend implementation status. |
| [Output formats](docs/formats.md) | Output-format interfaces and supported formats. |
| [WebAssembly](docs/wasm.md) | WebAssembly backend and binary-format details. |
| [Errors and source maps](docs/errors.md) | Syntax errors, source maps, and location relocation. |

The `examples/` directory contains working examples as well as exploratory design notes. Not every example is expected to compile successfully at this stage.

## Development

Run the test suite from the `dasm/` directory:

```bash
python3 -m pytest
```

Run a focused test module:

```bash
python3 -m pytest tests/test_arch_mos6502.py
```

Run a smoke test with an explicitly implemented target:

```bash
python3 dasm.py examples/1.dasm --arch wasm --format wasm
python3 dasm.py examples/c64.dasm --arch mos6502 --format prg
```

When adding an architecture or output format:

1. Implement the relevant interface in `arch/` or `format/`.
2. Export the implementation through `EXPORTS`.
3. Add the name to the command-line choices where required.
4. Add focused tests.
5. Update the relevant documentation and the implementation-status tables.

## Limitations

The following features are not complete or are intentionally outside the current scope:

- arithmetic expressions in source code;
- local labels, sections, macros, and conditional compilation;
- full support for all addressing modes;
- complete call and return-value semantics across backends;
- complete encoding of every `.raw` variant in all backends;
- production-ready `x86`, `elf`, and `exe` backends.

These limitations are part of the current project status and may change as the compiler evolves.
