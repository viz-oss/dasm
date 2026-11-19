# Language syntax

DASM's language is small and deliberately assembler-like: a program is a list of
lines, each of which is a label, assignment, call, directive, or `return`.
Indentation does not matter. Letter case **does** matter (except for keywords,
which are written in lowercase).

## Comments and whitespace

```asm
; comment
# comment
// comment
```

All three forms extend to the end of the line. Blank lines are ignored. Spaces
and tabs separate tokens.

## Registers

A register is written as `rN`, where `N` is a non-negative integer:

```asm
r0 = 1
r1 = r0
r128 = 2
```

Registers are **virtual** — the backend maps them to physical registers, WASM
locals, or memory cells, depending on the architecture. Names `rN` are reserved
and cannot be used as labels or constants.

## Labels

```asm
start:
main:
loop:
🚀:
```

A label name can contain Unicode letters, digits, `_`, and emoji, but cannot
start with a digit. A label ending in a colon is a separate token, so the
preprocessor does not replace it. Duplicate labels are rejected by symbol
validation (`label 'name' defined twice`) or by the backend when
`Architecture.assembly()` is called directly (`Duplicate label: name`).

## Assignments

```asm
r0 = 1          ; constant number
r1 = 0x20       ; hexadecimal number
r2 = -5          ; negative number
r3 = 1_000       ; thousands separator
r4 = r0          ; register copy
r5 = message     ; label address (Ptr)
message = r0     ; store register at a symbolic address
[0xD020] = r0    ; store register at a numeric address
```

- The left side can be a register (`rN`) or an address (a name or number).
- The right side can be a register, number, or name (treated as a pointer/address).
- Numbers in source can be decimal (with `_` separators), hexadecimal (`0x...`),
  or negative. Binary (`0b...`) and octal (`0o...`) literals are not supported
  by the parser (they work only in `.set` values).
- Supported forms depend on the backend; see
  [architectures.md](architectures.md). For example, `mos6502` does not
  implement register-to-register copies, and `wasm` does not support label
  addresses.

## Functions, parameters, and calls

A function definition with parameters:

```asm
add(a: r0, b: r1):
    r0 = 1
    r1 = 2
    return
```

- `a: r0` means the argument named `a` is associated with `r0`.
- Arguments are named, so their order in a call does not matter.
- `parse()` creates an `Arg` with `reg=None`; `lang.symbols.resolve()` fills in
  the register based on the label definition.
- The resolver reports missing arguments (`missing arguments [...]`), unknown
  parameters, duplicate arguments, and unknown labels
  (`call: unknown label ...`).
- A label can be defined before or after the call.

Calls:

```asm
add(a = 1, b = 2)
r0 = add(a = 1, b = 2)
```

- A call result (`r0 = ...`) is stored in the AST, but current backends do not
  support it.
- Arguments are passed through parameter registers; the backend emits the
  appropriate instructions before the jump (for example, `mos6502` loads
  immediate values and executes `JSR`).
- An argument can be a number, register, or name (Ptr). A backend may support
  only some of these forms.

## `return` and `.exit`

```asm
return
return 5
.exit
```

- `return` ends a function. `return <number>` passes a value on architectures
  that support it (`wasm`); `mos6502` emits only `RTS`.
- `.exit` is a program exit directive. `mos6502` emits `RTS`; `wasm` emits
  `return`; other architectures raise `NotImplementedError`.

## Directives

Directives start with a dot and are written in lowercase. Each directive must
appear on its own line.

| Directive | Argument | Meaning |
|---|---|---|
| `.start <label>` | name | program entry point; duplicates are an error |
| `.exit` | none | exit the program |
| `.raw('ascii') '...'` | string | ASCII text; the parser creates `Raw`, but current backends emit nothing |
| `.raw('petcii') '...'` | string | PETSCII text (Commodore); the parser creates `Raw`, but current backends emit nothing |
| `.raw('utf-8') '...'` | string | UTF-8 text; the parser creates `Raw`, but current backends emit nothing |
| `.raw('utf-16') '...'` | string | UTF-16 text; the parser creates `Raw`, but current backends emit nothing |
| `.raw` / `.raw(8)` | list of numbers | bytes (`Raw`, size 1) |
| `.raw(16)` | list of numbers | 16-bit numbers (`Raw`, size 2) |
| `.raw(32)` | list of numbers | 32-bit numbers (`Raw`, size 4) |
| `.raw(64)` | list of numbers | 64-bit numbers (`Raw`, size 8) |

```asm
.start main
.exit
.raw("ascii") "Hello"
.raw('utf-8') 'Good morning'
.raw(8) 0x60, 0x01
.raw(16) 1, 2
```

An unknown or misused directive produces `unknown or misused directive <name>`.

## Strings

Strings can use single or double quotes and support Python escape sequences:

```asm
.raw("ascii") "Hello\n"
```

## Syntax limitations

- No arithmetic operators in source — `r0 + 2` is not supported.
- No local labels, sections, macros, or conditional compilation.
- No multiline strings.
- No types or variable declarations — everything is a register or an address.
- `return`, `rN`, and directive names are reserved; `return_value` is a valid
  name.
- Labels and names are case-sensitive (`Foo` ≠ `foo`).
- `parse()` handles syntax; symbol validation is a separate step performed by
  `lang.symbols.resolve(ast)`. The CLI runs this step before assembly.
- Resolver errors (duplicate labels, missing labels, missing arguments, unknown
  symbols) do not yet have line or column numbers.
- The parser checks `.start` only for valid directive syntax; the resolver
  checks whether the label exists.
