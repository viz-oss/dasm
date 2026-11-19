# Errors and source mapping

## `DasmSyntaxError`

All syntax, preprocessing, and import errors are reported as
`lang.exceptions.DasmSyntaxError`:

```python
DasmSyntaxError(
    line=None, col=None, expected=None, message='',
    file=None, map_columns=False, context=False,
)
```

| Field | Meaning |
|---|---|
| `line`, `col` | 1-based position (may be `None`) |
| `expected` | list of expected tokens (displayed as `Expected a or b`) |
| `message` | error message; with `context=True`, also includes the line and `^` |
| `file` | source file (if already known) |
| `map_columns` | whether the column should be translated through `ColumnMap` |
| `context` | whether to reconstruct context from the original line |

`str(error)` returns `Expected ...\\n\\n<message>` or just `message`.

## Where errors originate

| Stage | Sets `line`/`col` | `map_columns` | `context` | `file` |
|---|---|---|---|---|
| parser (Lark `UnexpectedInput`) | yes | `True` | `True` | later |
| parser (`VisitError`, invalid literal) | yes (if the token has a position) | `True` | `False` | later |
| symbol resolver (`lang.symbols.resolve`) | no | `False` | `False` | later |
| preprocessor (`.set`, config) | usually | `False` | `False` | later |
| import (missing file, cycle, env) | yes | `False` | `False` | **yes** |

Symbol resolver errors include `label 'foo' defined twice`,
`call: unknown label 'foo'`, `missing arguments ['a']`, an unknown parameter,
and `unknown symbol 'name'`. They do not yet have a line or column number, but
the CLI calls the resolver before assembly and catches these errors as
`DasmSyntaxError`.

## Source mapping pipeline

`dasm.py` does the following:

```python
resolved = resolve_with_map(...)          # files + SourceMap
preprocessed = preprocess_with_map(...)   # .set + ColumnMap
ast = parse(preprocessed.text)
ast = lang.symbols.resolve(ast)
except DasmSyntaxError as e:
    e = source_map.relocate(e, preprocessed.column_maps)
```

- Import errors already have `file`, so `relocate()` leaves them unchanged.
- Preprocessor and parser errors have virtual line numbers (after imports are
  inserted), which `SourceMap` maps to the source file and line.
- Resolver errors do not yet include source positions because the AST does not
  store the locations of labels, calls, or pointers.
- Parser columns are mapped through `ColumnMap` if the text was changed by
  `.set` (for example, `X` → `1000`).

## `SourceMap`

`SourceMap(locations)` takes a list of `SourceLocation(path, line)` values for
successive virtual lines. Consecutive lines from the same file with consecutive
line numbers are grouped into `SourceSegment(start, end, path, line)`.

- `lookup(virtual_line)` returns a `SourceLocation` or `None` (if out of range).
- `original_line(location)` reads the original UTF-8 file (using a cache) and
  returns the corresponding line; returns `None` if reading fails or the line
  is out of range.
- `relocate(error, column_maps=None)`:
  1. If `error.file` is set or `line is None`, returns the error unchanged.
  2. Calls `lookup()`; if no location is found, returns the error unchanged.
  3. If `map_columns` is set and a `ColumnMap` is available, maps the column.
  4. Sets `file` and `line`.
  5. If `context` is set, replaces `message` with the original line and a `^`
     marker (tabs are expanded when calculating the cursor position).
  6. Refreshes `error.args`.

## `ColumnMap`

`ColumnMap` describes a single line as a list of `ColumnSegment(start, end,
source, fixed=False)` values.

- No segments → the column is unchanged (identity mapping).
- A column before the first segment → unchanged.
- `fixed=True` (a constant was substituted) → **every** column in the segment
  points to `source`, the beginning of the constant's name.
- Otherwise, the mapped column is `source + (processed_col - start)`.

Example: `.set X = 1000` and `r0 = X +` produce `r0 = 1000 +` after
substitution. An error at column 7 (in `1000`) is reported at column 6 (in `X`),
and the context shows the original `r0 = X +`.

## CLI output

```text
program.dasm:2:6: syntax error
Expected register or number

r0 = 
     ^
```

- The path is shown relative to the current directory (`_display_path`).
- Missing `line`/`col` values produce `program.dasm::`.
- Messages are written to `stderr`, and the exit code is `1`.

## Known limitations

- Symbol resolver errors do not have source positions because the AST does not
  yet store the locations of these nodes.
- Assembly errors (`Undefined label`, `Duplicate label`, `Address out of range`)
  and backend errors do not go through source mapping; they are Python exceptions
  (`ValueError`, `NotImplementedError`, `AssertionError`).
- A `ColumnMap` is not created for `.set` lines (it is empty) because the line is
  replaced with an empty line anyway.
