# Preprocessor: `.set` and configuration constants

The preprocessor runs **before the parser**, on the text after `.import`
resolution (and before error mapping). It replaces selected names with values
and removes `.set` lines while preserving line numbering.

## Syntax

```asm
.set NAME = 123
.set COLOR = 0xD020
.set NEGATIVE = -5
.set BIN = 0b1010
.set SEP = 1_000
.set TEXT = "Hello\n"
```

- A constant name is an identifier: Unicode letters, digits, `_`, and emoji; it
  cannot start with a digit or be named `rN`.
- A value is a number or a string in double quotes.
- Numbers are parsed like Python numbers with base 0: decimal, `0x...`, `0b...`,
  `0o...`, with `_` separators and an optional `-` sign.
- Strings use Python escapes (`\n`, `\"`, `\\`). The result is inserted again in
  JSON form, meaning in double quotes.
- `.set` must be the first meaningful thing on a line (apart from spaces/tabs).

## Single-pass behavior

A constant must be defined **before it is used**. The preprocessor goes from
top to bottom and does not collect definitions in advance:

```asm
r0 = X          ; X is not known yet → remains as Ptr('X')
.set X = 1
```

Using a constant before its definition is not an error; the name simply remains
a name (a label/address). To use constants throughout a file, define them at the
beginning or in an imported file that is inserted before the code.

## Configuration constants

Keys from `[dasm.env]` in `*.toml` are available as constants **from the first
line**:

```toml
[dasm.env]
OS = "c64"
VIC_BORDER = 0xD020
```

```asm
r0 = VIC_BORDER
```

Rules:

- Configuration **takes precedence** over a `.set` with the same name (the TOML
  value is not overwritten).
- A `.set` line for such a name is still validated (it must be valid).
- Only `int` and `str` are allowed; `bool` is rejected even though it inherits
  from `int`.
- Key names are validated in the same way as constant names.

The same `[dasm.env]` values are used to expand `{NAME}` in `.import`; see
[import.md](import.md).

## What gets replaced

Only **name** tokens (names in the code) are replaced. These are not replaced:

- comments (`;`, `#`, `//`),
- strings,
- labels (`X:` is a separate token),
- directive names (`.set`, `.raw`, `.start`, ...).

```asm
.set X = 1
; X              ← comment, unchanged
// X             ← comment, unchanged
r0 = "X"         ← string, unchanged
X:               ← label, unchanged
.raw("ascii") "X" ← string, unchanged
r0 = X           ← replaced with 1
```

## Line numbering and columns

A `.set` line is replaced with a **blank line**, so line numbers in parser errors
continue to match the source file.

`preprocess_with_map()` returns `PreprocessedSource(text, column_maps)`.
A `ColumnMap` is created for each line, mapping columns after substitution back
to their original columns. The entire substituted value (for example, `1000`
in place of `X`) points to the first column of the constant's name. This means
an error in `r0 = 1000 +` is reported at `X`, and the context shows the original
`r0 = X +`.

Details: [errors.md](errors.md).

## Errors

| Situation | Message |
|---|---|
| name `rN` | `'r1' is reserved for registers` |
| invalid name (for example, from TOML) | `invalid constant name 'bad-name'` |
| value is not a number or string | `constant value must be a number or a string: 'abc'` |
| invalid number (for example, `09`) | `invalid number '09'` |
| invalid string (for example, `"\\x"`) | `invalid string literal` |
| missing name/value | `expected: .set NAME = <number or string>` |
| duplicate `.set` | `constant 'X' already defined` |
| invalid TOML type | `config constant 'X': expected int or string, got bool` |

## Design decisions

- A constant must be defined before it is used; preprocessing is a single
  top-to-bottom pass. To make constants available throughout the file regardless
  of order, the preprocessor would need one pass to collect `.set` definitions
  and a second pass to substitute them.
- Constants cannot be named `rN`, consistent with the register naming rule.
- `.set` leaves a blank line so parser error line numbers remain accurate.
- Numeric values are normalized to decimal: `0xFF` is returned to the text as
  `255`. Strings are returned in JSON form (double quotes).
- Columns after substitution are corrected through `ColumnMap`.

## Open questions

- **Constant used as a call.** `art()` is a `name` token, so the constant `art`
  would be substituted, producing `1()` and a confusing syntax error. It may be
  useful to add an exception: if the next meaningful token is `(`, report
  `constant used as a call`.
- **Constant on the left-hand side.** After substitution, `art = r0` becomes
  `1 = r0`, which silently writes to address 1. This may be intentional, but it
  is easy to do by mistake.
- **Duplicated lexical rules.** `_TOKEN_RE` in the preprocessor repeats parts of
  the grammar (comments, strings, `NAME`, `LABEL`). Changing the syntax in one
  place but not the other can make the preprocessor and parser disagree. Shared
  regex constants or a test that compares both on the same examples may help.
- **Constant name and label collision.** With `.set art = 1` and a label `art:`,
  the label remains (it is a separate token), but `r0 = art` becomes `r0 = 1`
  instead of the label's address. Detecting this would require knowing all labels
  in advance, which means an extra pass.
