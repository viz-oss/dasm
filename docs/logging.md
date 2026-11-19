# Logging

DASM has a built-in logging system based on the standard library's `logging`
module. The implementation is in `utils/log.py`; enable logging with the
`-l`/`--log` command-line argument.

## The `--log` argument

| Form | Effect |
|---|---|
| no argument | logging is disabled (default) |
| `-l`, `--log` | logs all groups (`*`) |
| `-l GROUP`, `--log GROUP` | logs only the specified groups |
| `-l GROUP1+GROUP2` | logs multiple groups separated by `+` |

```bash
python3 dasm.py program.dasm --arch mos6502 --format prg
python3 dasm.py program.dasm --arch mos6502 --format prg --log
python3 dasm.py program.dasm --arch mos6502 --format prg --log lang
python3 dasm.py program.dasm --arch mos6502 --format prg --log lang.preprocess
```

Because `--log` takes an optional value, put the source path before the flag
(`... --log lang`) or use `--log=lang`. A bare `-l` at the end of the command
logs everything.

### Groups

A group is the first component of a logger's name, meaning the package name.
The full logger name can also be used as a filter:

| Filter | What it logs |
|---|---|
| `lang` | all modules in `lang/` (`lang.syntax`, `lang.preprocess`, …) |
| `lang.preprocess` | the preprocessor only |
| `lang+utils` | modules in `lang/` and `utils/` |
| `*` | everything (same as `-l` with no value) |

An unknown group is not an error; nothing matches, so no logs appear. The filter
matches either the full logger name (`record.name`) or its first component.

## Format and output destination

Logs are sent to **stdout** through a `StreamHandler` attached to the root
logger. Each entry has this form:

```
[%(name)s] %(message)s
```

For example, given this source:

```asm
.set BORDER = 0xD020
0xD020 = BORDER
```

The log looks like this (the line before and after substitution; `.set` is not
logged):

```
dasm v2.0.2
Parsing...[lang.preprocess] 2: 0xD020 = BORDER
[lang.preprocess] 2: 0xD020 = 53280
[lang.preprocess] 3:
```

Unchanged lines are logged once, while lines with substituted constants are
logged twice.

The root logger and handler are set to `DEBUG`, so `logger.debug()`,
`logger.info()`, and other levels reach the group filter. The filter decides
only *which* entries are shown, not their log level.

Because logs and stage messages (`Parsing...`, `Assembly...OK`) go to stdout,
while syntax errors go to stderr, their order in the terminal may be mixed. In
pipelines, stdout is buffered, so logs may appear after an error message.

## `utils/log.py`

The module provides:

| Item | Meaning |
|---|---|
| `setup(groups_arg)` | configures the root logger and adds a handler with a filter; called once in `dasm.py` before the version header |
| `LogGroupFilter(allowed_groups)` | filters entries by logger name; `None` blocks everything, `{'*'}` allows everything |
| `red(s)`, `green(s)`, `gray(s)` | helper functions for coloring text (ANSI) |

`setup()` takes the raw CLI string and converts `A+B` into a set of groups. With
no argument, the set is empty, so nothing is logged by default.

The `red()`, `green()`, and `gray()` functions add ANSI codes only when
`sys.stdout.isatty()` is true, so text stays plain in pipelines and files. The
preprocessor uses `red()` for a line before constant substitution and `green()`
for the resulting line (see [preprocess_set.md](preprocess_set.md)).

## Adding logs in a new module

Use the standard logger named after the module; there is no need to create a
custom handler or configuration:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("details")
logger.info("operation step")
```

A logger named `lang.mymodule` will appear with `--log lang`,
`--log lang.mymodule`, and `--log` with no value. Groups do not need to be
registered anywhere.

## `--log` vs. `-d/--debug`

These are independent options:

- `-l`/`--log` enables diagnostics from the assembler itself on stdout.
- `-d`/`--debug` sets `debug = True` in the options passed to backends and does
  not affect logging.
