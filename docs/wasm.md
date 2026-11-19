# WebAssembly (`wasm`)

The WASM backend consists of two modules:

- `arch/wasm.py` — generates an opcode stream for a single function.
- `format/wasm.py` — wraps the stream in a complete `.wasm` module.

## Model

- The entire program is **one function** with no parameters and no result (`() -> ()`).
- Register `rN` is the WASM local with index `N`.
- There is no call stack, labels, jumps, or static data.
- The architecture always appends `end` (`0x0B`) at the end.
- `word_size = 1`, `endian = 'little'`, `entry_jump_size = 0`.

## Architecture instructions

| Source | Emitted opcodes |
|---|---|
| `rN = <number>` | `i32.const <sleb128>` + `local.set <uleb128 N>` |
| `rN = rM` | `local.get <uleb128 M>` + `local.set <uleb128 N>` |
| `rN = <address>` | `i32.const <address>` + `i32.load 2 0` + `local.set N` |
| `<address> = rN` | `i32.const <address>` + `local.get N` + `i32.store 2 0` |
| `return` | `return` (`0x0F`) |
| `return <number>` | `i32.const <number>` + `return` |
| `.exit` | `return` |

- `<address>` must be a numeric literal (`Ptr(Int(...))`), not a label; the
  address must be non-negative. A label raises `NotImplementedError`.
- `call` and `jmp` raise `NotImplementedError` (function indices and jumps are
  not supported).
- `memarg` is fixed: `align = 2`, `offset = 0`.

### Opcodes used by the architecture

| Constant | Value |
|---|---|
| `OP_END` | `0x0B` |
| `OP_RETURN` | `0x0F` |
| `OP_LOCAL_GET` | `0x20` |
| `OP_LOCAL_SET` | `0x21` |
| `OP_I32_LOAD` | `0x28` |
| `OP_I32_STORE` | `0x36` |
| `OP_I32_CONST` | `0x41` |

Integers are encoded as LEB128: `uleb128()` for non-negative values and
`sleb128()` for signed values.

## Module format

`FormatWasm.output(words)`:

1. Rejects `entry` values other than `None` or `0`.
2. Scans the stream (`_scan`) to find:
   - the highest local index (`max_local`),
   - whether memory is used (`i32.load`/`i32.store`),
   - whether the stream ends with `end`.
3. Builds the sections:
   - **type (1)**: one `() -> ()` type,
   - **function (3)**: one function of type 0,
   - **memory (5)**: only when memory is used; `[min = memory_pages]` with no
     maximum,
   - **export (7)**: the `main` function (index 0) and, if memory is used, the
     `memory` export (index 0),
   - **code (10)**: a declaration for `max_local + 1` `i32` locals (one group)
     followed by the opcode stream.

Class attributes:

| Attribute | Default | Meaning |
|---|---|---|
| `ext` | `wasm` | file extension |
| `origin` | `0` | base address |
| `entry_jump` | `False` | no entry jump |
| `memory_pages` | `1` | minimum number of memory pages (64 KiB) |
| `export_name` | `main` | exported function name |

### Scanning and supported opcodes

`_scan` accepts only:

| Opcode | Additional data |
|---|---|
| `0x00` (`unreachable`) | none |
| `0x0B` (`end`) | none |
| `0x0F` (`return`) | none |
| `0x10` (`call`) | `uleb128` function index |
| `0x20`, `0x21` (`local.get/set`) | `uleb128` local index |
| `0x28`, `0x36` (`i32.load/store`) | `uleb128` align + `uleb128` offset |
| `0x41` (`i32.const`) | `sleb128` value |

Any other opcode raises
`ValueError: unsupported WASM opcode 0xXX at offset N`.
Truncated LEB128 data raises `ValueError: unexpected end of WASM code`.
A stream without a final `end` raises `ValueError: ... end opcode ...`.

## Examples

An empty program:

```python
arch.assembly([])  # [0x0B]
```

The module has sections `[1, 3, 7, 10]`; the code section is `01 02 00 0B`
(one function, 2-byte body: no locals + `end`).

`r0 = 1`:

```python
arch.assembly([Mov(Reg(0), Int(1))])
# [0x41, 0x01, 0x21, 0x00, 0x0B]
```

Code section: `01 08 01 01 7F 41 01 21 00 0B` (one `i32` local, then the body).

`100 = r0`:

```python
arch.assembly([Mov(Ptr(Int(100)), Reg(0))])
# [0x41, 0xE4, 0x00, 0x20, 0x00, 0x36, 0x02, 0x00, 0x0B]
```

The module gets a memory section `01 00 01` and a `memory` export.

A complete CLI example:

```bash
printf 'r0 = 1\n' > prog.dasm
python3 dasm.py prog.dasm --arch wasm --format wasm
```

## Limitations

- No function calls (`call`), jumps, or labels.
- No static data or data section.
- Only one function type and one function.
- Memory is exported, but there is no start function other than `main`.
- No support for multiple results, parameters, or types other than `i32`.
- `.start` works only for a label at offset 0 (the format rejects other
  `entry` values).
