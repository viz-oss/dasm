# DASM Documentation

DASM is a multi-architecture assembler with its own high-level language (virtual
registers, labels, functions, and directives) and interchangeable architecture
backends and output formats.

## Contents

| Document | Contents |
|---|---|
| [cli.md](cli.md) | running `dasm.py`, options, `*.toml`, output file names, and exit codes |
| [syntax.md](syntax.md) | language syntax: labels, registers, assignments, calls, and directives |
| [preprocess_set.md](preprocess_set.md) | preprocessor: `.set`, configuration constants, substitutions, and column mapping |
| [import.md](import.md) | `.import`, file lookup, environment variables, duplicates, and cycles |
| [logging.md](logging.md) | `utils/log.py` logging system, `--log` argument, groups, and filters |
| [architectures.md](architectures.md) | architecture interface and backend implementation status |
| [formats.md](formats.md) | format interface and descriptions of output formats |
| [wasm.md](wasm.md) | WebAssembly backend and format details |
| [errors.md](errors.md) | `DasmSyntaxError`, source maps, and line and column mapping |

## Code structure

```
dasm.py              # CLI: argument parsing, compilation pipeline, writing output
arch/                # architecture backends (selected with --arch)
format/              # output formats (selected with --format)
lang/                # lexer, imports, preprocessor, parser, AST, symbols, errors, source maps
utils/               # loading modules and *.toml files, logging system
tests/               # unit and integration tests
examples/            # examples (some are design notes, not working code)
```

## Compilation pipeline

```
.dasm source
  → resolve_with_map()    # .import: insert files + SourceMap
  → preprocess_with_map() # .set and TOML constants + ColumnMap
  → parse()               # AST
  → lang.symbols.resolve() # semantic validation
  → Architecture.assembly()
  → Format.output()
  → output file
```

`dasm.py` calls `resolve()` before assembly, which populates argument registers
for calls and reports symbol errors before code generation.

## Implementation status

| Architecture | Status |
|---|---|
| `arm64` | partial: move a constant into a register (`MOVZ`); everything else raises `NotImplementedError` |
| `mos6502` | partial: immediate values, absolute stores, `call`/`ret`/`exit`/`jmp`; most addressing modes are stubs |
| `wasm` | `mov`/`load`/`store`, `return`, `exit`; no `call`/`jmp` or label addresses |
| `x86` | placeholder (no code or `EXPORTS`) |
| `alu48` | legacy, outside the `Architecture` interface; not available through the CLI |

| Format | Status |
|---|---|
| `bin` | complete |
| `prg` | complete (C64) |
| `hex` | complete (text hex) |
| `macho` | complete for a single `__text` section |
| `wasm` | complete for a single function |
| `elf` | placeholder (no `EXPORTS`) |
| `exe` | placeholder (no `EXPORTS`) |

> Default pairs depend on the operating system: macOS `arm64` + `macho`, Linux
> `x86` + `elf`, and Windows `x86` + `exe`. On Linux and Windows, running with
> the default settings will fail while `x86`, `elf`, and `exe` remain placeholders.
