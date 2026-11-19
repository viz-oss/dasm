# Output formats

A format converts a list of words (`list[int]`) into file bytes. Select one with
`--format NAME` or `[dasm.options].format`.

## `Format` interface

The `format/base.py` file defines:

```python
class Format(ABC):
    ext = ''            # output file extension
    origin = 0          # address of the first code byte (for labels/relocations)
    entry_jump = False  # whether to insert a jump to .start before the code

    def output(self, words: list[int], entry: int | None = None) -> bytes
```

- `origin` is passed to `Architecture.assembly()` as the base address.
- `entry_jump = True` tells the CLI to have the architecture insert a jump to
  the label specified by `.start` (if `.start` is present).
- `entry` is the calculated entry point address; most formats ignore it.
- `output()` **must return `bytes`**, because the CLI writes the file in `wb`
  mode.

## `bin` — raw binary

```python
return bytes(words)
```

- `ext = 'bin'`, `origin = 0`, `entry_jump = False`.
- No header and no load-address relocation; `entry` is ignored.

## `prg` — C64 PRG

The `format/prg.py` file builds:

```
offset 0   : 2 B  header with load address 0x0801 (little endian)
offset 2   : 12 B BASIC stub
offset 14  : program code (starting at address 0x080D)
```

The BASIC stub is the line `10 SYS 2061` (`0x9E` followed by the digits
`2061`), terminated by `0x00` and then `0x00 0x00`. `origin = 0x080D` (`2061`)
and `entry_jump = True`, so when `.start` is present, a `JMP <entry>` is placed
at the beginning of the code.

- `ext = 'prg'`; inherits from `FormatBin` (`output` concatenates the parts).
- `entry` is not used — the address in the BASIC stub is fixed (`SYS 2061`).

## `hex` — text hex

```
1234
0001
```

- `ext = 'hex'`, `origin = 0`, `entry_jump = False`.
- Each word is formatted as at least 4 hexadecimal digits (uppercase), with
  words separated by `\\n` and no trailing newline.
- The result is encoded as ASCII and returned as `bytes`.
- `entry` is ignored. Values greater than `0xFFFF` are printed with more than
  4 digits.

## `macho` — Mach-O for Apple silicon

A single `MH_OBJECT` object with a `__text` section and an empty symbol table:

```
offset 0    : mach_header_64             (32 B)
offset 32   : LC_SEGMENT_64 + section_64 (152 B)
offset 184  : LC_SYMTAB                  (24 B)
offset 208  : __text: words as uint32 LE
             : symbol table              (0 entries)
             : string table              (NUL byte)
```

- `ext = 'o'`, `origin = 0`, `entry_jump = False`.
- Header: magic `0xFEEDFACF`, CPU `0x0100000C` (ARM64), type `MH_OBJECT`,
  `ncmds = 2`, `sizeofcmds = 176`.
- The `__text` section has `align = 2` (4 bytes) and the flags
  `S_ATTR_PURE_INSTRUCTIONS | S_ATTR_SOME_INSTRUCTIONS`.
- Each word is written to the file as a 32-bit little-endian `uint32`; words
  must fit in 32 bits.
- No relocations or symbols; `entry` is ignored.

## `wasm` — WebAssembly module

The format wraps the opcode stream from `arch/wasm.py` in a complete module:
magic/version, type and function sections, optional memory section, and export
and code sections.

- `ext = 'wasm'`, `origin = 0`, `entry_jump = False`.
- `memory_pages = 1` (minimum linear memory), `export_name = 'main'`.
- The `memory` section and `memory` export are included only when `i32.load` or
  `i32.store` is used.
- The stream must end with the `end` opcode (`0x0B`).
- `entry` must be `None` or `0`; any other address raises `ValueError`.

Details: [wasm.md](wasm.md).

## `elf` — placeholder

The `format/elf.py` file contains only a docstring. It has no `EXPORTS`, so
`--format elf` fails with
`DasmSyntaxError: Module format/elf.py does not contain EXPORTS`.

## `exe` — placeholder (Windows)

The `format/exe.py` file contains only the docstring `"""Windows .exe"""`. It
has no `EXPORTS`, so `--format exe` fails with a similar error. This is the
default format on Windows, so running the program with default settings on
Windows will not work until this format is implemented.

## How `.start` interacts with a format

```asm
.start main
main:
    r0 = 1
```

The CLI extracts `main` from the AST and passes `start='main'` to the
architecture, along with `entry_jump = format.entry_jump`. The result is:

| Format | `entry_jump` | Effect of `.start` |
|---|---|---|
| `prg` | `True` | `JMP main` is placed at the beginning of the code |
| `bin`, `hex`, `macho`, `wasm`, `elf`, `exe` | `False` | no jump; `entry` is passed to `output()` (usually ignored) |

In `wasm`, a nonzero `entry` is an error, so `.start` will not work if its label
is at an offset other than 0. For `mos6502` + `prg`, the entry jump is 3 bytes
long and shifts label addresses.

## Adding a format

1. Create `format/name.py` with a class that inherits from `format.base.Format`.
2. Set `ext`, `origin`, and `entry_jump`.
3. Implement `output(words, entry=None) -> bytes`.
4. Add `EXPORTS = YourClass`.
5. Add `name` to the `choices` for `--format` in `dasm.py` and add tests.

More: [documentation README](README.md) and [AGENTS.md](../AGENTS.md).
