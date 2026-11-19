# `.import` — inserting source files

`.import` inserts an entire `.dasm` file in place of the import line, **before**
preprocessing. This makes `.set` constants from the imported file visible in the
rest of the combined source.

## Syntax

```asm
.import 'sys/c64/vic.dasm'
.import "sys/c64/vic.dasm"
.import 'sys/{OS}/vic'
.import 'lib.dasm' ; comment
```

- `.import` must be the first thing on a line; only spaces and tabs may precede
  it. It cannot appear after other code.
- Single and double quotes are equivalent, but each opening quote must match its
  closing quote.
- A comment may follow the path: `;`, `#`, or `//`.
- The directive name is case-sensitive: `.import`, not `.IMPORT`.
- A line where `.import` appears inside a comment is ignored.
- The imported file is read as UTF-8. Its trailing newline is removed to avoid
  adding an empty line.

## File lookup

For a relative import, paths are searched in this order:

1. The directory containing the file with the `.import` directive.
2. The entries in `[dasm.imports].paths` (paths are resolved relative to the
   **current working directory when the program is run**).
3. The current working directory.

Directories are deduplicated after resolving their paths. If a name has no
extension, both `name` and `name.dasm` are checked.

Absolute paths are not combined with the directories above. If the extension is
omitted, the `name` and `name.dasm` variants are still checked.

```toml
[dasm.imports]
paths = ["../lib", "lib"]
```

The `[dasm.imports].repos` key is not currently used.

## Environment variables

You can use `{NAME}` in a path. Its value comes from `[dasm.env]`:

```toml
[dasm.env]
OS = "c64"
```

```asm
.import 'sys/{OS}/vic'
```

A variable name must match `[A-Za-z_]\\w*`. A variable missing from `env` is an
error: `unknown environment variable 'MISSING' in import path ...`.

## Duplicates and cycles

- Each file is inserted only once across the entire import tree.
- A subsequent import of the same file is replaced with an **empty line** (line
  numbering stays the same).
- An import cycle (`a -> b -> a`) is an error:
  `circular import: a -> b -> a`.
- Importing a file into itself is an error (the main file is also on the stack).
- Insertion order is depth-first: an imported file is inserted at the directive,
  before the remaining lines of the importing file.

## Line numbers and columns

Inserting a file replaces one line with multiple lines, shifting the line numbers
that follow in the combined text. Along with the text, `resolve_with_map()`
returns a `SourceMap` that keeps track of segments:

```text
[1..11]   examples/c64.dasm      line 1
[12..89]  ../sys/c64/vic.dasm    line 1
[90..]    examples/c64.dasm      line 13
```

This lets an error on a virtual line be reported against its original file and
line. `preprocess_with_map()` also adds a `ColumnMap` to adjust columns after
constant substitution. Error context is reconstructed from the original source
line, not from the substituted text.

Import errors themselves (missing file, cycle, invalid environment variable)
already have the importing file's name and the line and column of `.import`.
Preprocessor and parser errors are mapped by `SourceMap` in `dasm.py`.

For a full description of the mechanism, see [errors.md](errors.md).

## Example

`main.dasm`:

```asm
.import 'sys/{OS}/vic'

start:
  r0 = VIC_LIGHT_BLUE
  VIC_FRAME_COLOR = r0
```

`../sys/c64/vic.dasm`:

```asm
.set VIC_LIGHT_BLUE = 14
.set VIC_FRAME_COLOR = 0xD020
```

`build.toml`:

```toml
[dasm.env]
OS = "c64"

[dasm.imports]
paths = ["../sys"]
```

After import resolution, the preprocessor sees both `.set` directives before
their use. After substitution, the code looks like this:

```asm
start:
  r0 = 14
  [53280] = r0
```

## Limitations

- There is no conditional import, macro support, or `include` directive with
  different semantics.
- Unused imports are not detected; the entire file is inserted.
- Imports are not resolved again against paths added later in `paths`; the search
  directories are determined when the directive is encountered.
- `{NAME}` is replaced with the raw value from `env` (without type conversion).
