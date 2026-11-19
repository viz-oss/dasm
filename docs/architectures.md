# Architectures

An architecture is a backend that converts the AST into a list of output words
(`list[int]`). Select one with `--arch NAME` or `[dasm.options].arch`.

## `Architecture` interface

The `arch/base.py` file defines the abstract class:

```python
class Architecture(ABC):
    word_size: int = 1          # size of one output element in bytes
    entry_jump_size: int = 0    # size of the entry jump (0 = none)
    endian: Literal['little', 'big'] | None = None

    def assembly(self, ast, origin=0, start=None, entry_jump=False) -> list[int]
    def mov(self, instr) -> list[int]
    def call(self, instr, offset=0) -> list[int]
    def ret(self, instr) -> list[int]
    def exit(self, instr) -> list[int]
    def jmp(self, target: str, offset=0) -> list[int]
```

The `mov`, `call`, `ret`, `exit`, and `jmp` methods are abstract and must be
implemented (they may raise `NotImplementedError` for now). The base
`assembly()` method handles the full process:

1. Clears `labels`, `relocations`, `origin`, `start`, and `entry`.
2. If `start` is specified and `entry_jump=True`, emits `jmp(start)` at the
   beginning (labels are automatically shifted by `entry_jump_size`).
3. Processes each AST instruction:
   - `Start` — no-op (the CLI/format handles the entry point),
   - `Label` — records the offset in bytes (`len(output) * word_size`),
   - `Mov` → `mov()`,
   - `Call` → `call(instr, offset=len(output))`,
   - `Raw` → `raw()` (one byte per value by default),
   - `Return` → `ret()`,
   - `Exit` → `exit()`.
4. `apply_relocations()` fills in label addresses and checks their range.
5. If `start` is specified, sets `entry = origin + labels[start]`.

`Relocation(offset, target, size=2, endian='little')` specifies the index in
`output` where a label address should be written. `apply_relocations()` raises
`Undefined label: ...` and `Address out of range for ...`.

> Relocations are designed for byte-oriented architectures (`word_size = 1`).
> They are not yet used for `arm64` (`word_size = 4`).

## Backend status

### `arm64` — `arch/arm64.py`

- `word_size = 4`, `endian = 'little'`, no entry jump.
- `mov`:
  - `rN = <number 0..0xFFFF>` → one `MOVZ` instruction (a 32-bit word),
  - `rN = rM` → `_orr`, currently raises `NotImplementedError`,
  - `rN = <address>`, `<address> = rN` → `NotImplementedError`.
- `_movz(rd, imm16, hw=0, x=True)` builds a `MOVZ` word; validates that `rd`
  is in `0..31`, `imm16` is in `0..0xFFFF`, and `hw` is in `0..3`.
- `call`, `ret`, `exit`, `jmp` → `NotImplementedError`.
- Labels are recorded by the base `assembly()`, but nothing uses them.

### `mos6502` — `arch/mos6502.py`

Virtual registers: `r0` = A, `r1` = X, `r2` = Y.

- `word_size = 1`, `endian = 'little'`, `entry_jump_size = 3` (`JMP $xxxx`).
- `mov`:
  - `r0/r1/r2 = <0..255>` → `LDA/LDX/LDY #imm` (`0xA9`, `0xA2`, `0xA0`),
  - `<0..65535> = r0/r1/r2` → `STA/STX/STY absolute` (`0x8D`, `0x8E`, `0x8C`),
  - other combinations → `NotImplementedError`.
- `call`: arguments are emitted by `mov()` into the registers specified by
  `Arg.reg`, then `JSR` (`0x20`) is emitted with a 2-byte address relocation.
  `Arg.reg` must first be populated by `lang.symbols.resolve()`; the parser
  itself leaves it as `None`. Numeric arguments currently work; registers and
  pointers require `mov` modes that are not implemented yet.
- `ret` and `exit` → `RTS` (`0x60`).
- `jmp` → `JMP` (`0x4C`) with a 2-byte relocation.
- Addressing modes such as `zero page`, `absolute,X/Y`, and `indirect` have
  helper methods, but all of them raise `NotImplementedError`.
- `_absolute16()` accepts only an `int` in `0..65535`.

### `wasm` — `arch/wasm.py`

- `word_size = 1`, `endian = 'little'`, no entry jump.
- One default function and one local per register: `rN` → local `N`.
- Emits WASM opcodes and always closes the function body with the `end` opcode
  (`0x0B`).
- Details: [wasm.md](wasm.md).

### `x86` — `arch/x86.py`

Placeholder (docstring only). It has no `EXPORTS`, so `--arch x86` fails with
`DasmSyntaxError: Module arch/x86.py does not contain EXPORTS`.

### `alu48` — `arch/alu48.py`

A 4-bit ALU backend that inherits from `Architecture`. It emits single-byte
control words through `encode(mnemonic, operands, context)` and provides
`microcode_table()`. It exports its class through `EXPORTS`, so it works with
`load_module()`; CPU operations (`mov`, `call`, `ret`, `exit`, `jmp`) do not
apply to this backend and raise `NotImplementedError`.

## Adding an architecture

1. Create `arch/name.py` with a class that inherits from `arch.base.Architecture`.
2. Set `word_size`, `endian`, and, if needed, `entry_jump_size`.
3. Implement `mov`, `call`, `ret`, `exit`, and `jmp` (stubs that raise
   `NotImplementedError` are acceptable).
4. Add `EXPORTS = YourClass` at the end of the file (`YourClass` must be callable).
5. Add `name` to the `choices` for `--arch` in `dasm.py`.
6. Add tests in `tests/test_arch_name.py`.

More: [documentation README](README.md) and [AGENTS.md](../AGENTS.md).
