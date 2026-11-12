"""Resolve .import directives by inlining the imported source files.

The resolver works on raw text, before preprocess(), so .set definitions from
imported files are visible in the rest of the combined source.  Every file is
inlined at most once; later imports of the same file are replaced with an empty
line.
"""

import re
from pathlib import Path

from .exceptions import DasmSyntaxError


_IMPORT_RE = re.compile(
    r"""^[ \t]*\.import[ \t]+(?P<quote>['"])(?P<path>.+?)(?P=quote)[ \t]*(?:[;#].*|//.*)?$"""
)
_ENV_RE = re.compile(r"\{([A-Za-z_]\w*)\}")
_DEFAULT_SUFFIX = ".dasm"


def _error(lineno: int, col: int, message: str) -> DasmSyntaxError:
    return DasmSyntaxError(lineno, col, message=message)


def _expand_env(name: str, env: dict, lineno: int, col: int,
                source_name: str) -> str:
    """Substitute {NAME} placeholders from the project environment."""
    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in env:
            raise _error(
                lineno, col,
                f"{source_name}:{lineno}: unknown environment variable "
                f"'{key}' in import path {name!r}"
            )
        return str(env[key])

    return _ENV_RE.sub(replace, name)


def _candidate_paths(name: str, base_dir: Path,
                     search_paths: list[str]) -> list[Path]:
    """Build the ordered list of paths to try for an import."""
    target = Path(name)
    variants = [target] if target.suffix else [
        target, target.with_suffix(_DEFAULT_SUFFIX)
    ]

    if target.is_absolute():
        return variants

    roots = [Path(base_dir), *(Path(path) for path in search_paths), Path.cwd()]
    candidates = []
    seen_roots = set()
    for root in roots:
        try:
            root = root.resolve()
        except OSError:
            root = root.absolute()
        if root in seen_roots:
            continue
        seen_roots.add(root)
        candidates.extend(root / variant for variant in variants)
    return candidates


def _find_import(name: str, base_dir: Path,
                 search_paths: list[str]) -> tuple[Path | None, list[Path]]:
    candidates = _candidate_paths(name, base_dir, search_paths)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve(), candidates
    return None, candidates


def _read_import(path: Path, lineno: int, col: int,
                 source_name: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        raise _error(
            lineno, col,
            f"{source_name}:{lineno}: cannot read import {path}: {e}"
        ) from e


def _resolve_text(text: str, base_dir: Path, env: dict,
                  search_paths: list[str], seen: set[Path], stack: list[Path],
                  source_name: str) -> list[str]:
    out = []
    for lineno, line in enumerate(text.split("\n"), 1):
        match = _IMPORT_RE.match(line)
        if not match:
            out.append(line)
            continue

        raw_name = match.group("path")
        col = match.start("path") + 1
        name = _expand_env(raw_name, env, lineno, col, source_name)

        found, candidates = _find_import(name, base_dir, search_paths)
        if found is None:
            searched = "\n".join(f"  {candidate}" for candidate in candidates)
            raise _error(
                lineno, col,
                f"{source_name}:{lineno}: cannot import {raw_name!r}: "
                f"file not found\nsearched:\n{searched}"
            )

        if found in stack:
            chain = " -> ".join(str(path) for path in [*stack, found])
            raise _error(
                lineno, col,
                f"{source_name}:{lineno}: circular import: {chain}"
            )

        if found in seen:
            out.append("")          # keep one line in place of the import
            continue

        seen.add(found)
        stack.append(found)
        try:
            imported = _read_import(found, lineno, col, source_name)
            if imported.endswith("\n"):
                imported = imported[:-1]
            out.extend(_resolve_text(
                imported, found.parent, env, search_paths, seen, stack,
                str(found)
            ))
        finally:
            stack.pop()

    return out


def resolve(text: str, env: dict | None = None,
            paths: list[str] | None = None,
            source_path: Path | str | None = None) -> str:
    """Inline all .import directives and return one combined source string.

    Search order for a relative import: the importing file's directory, every
    entry from [dasm.imports].paths, then the current working directory.  When
    the name has no suffix, .dasm is tried as well.  Each file is inlined only
    once; repeated imports are replaced with an empty line.
    """
    env = env or {}
    search_paths = list(paths or [])

    if source_path is not None:
        source_path = Path(source_path)
        try:
            source_path = source_path.resolve()
        except OSError:
            pass
        base_dir = source_path.parent
        source_name = str(source_path)
        stack = [source_path]
    else:
        base_dir = Path.cwd()
        source_name = "<source>"
        stack = []

    seen: set[Path] = set()
    lines = _resolve_text(
        text, base_dir, env, search_paths, seen, stack, source_name
    )
    return "\n".join(lines)
