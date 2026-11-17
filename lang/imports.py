"""Resolve .import directives by inlining the imported source files.

The resolver works on raw text, before preprocess(), so .set definitions from
imported files are visible in the rest of the combined source.  Every file is
inlined at most once; later imports of the same file are replaced with an empty
line.

Besides the combined text, resolve_with_map() also returns a SourceMap that
translates virtual line numbers back to the original files.
"""

import re
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from .exceptions import DasmSyntaxError
from .sourcemap import ResolvedSource, SourceLocation, SourceMap
from utils.log import anonymize_path


_IMPORT_RE = re.compile(
    r"""^[ \t]*\.import[ \t]+(?P<quote>['"])(?P<path>.+?)(?P=quote)[ \t]*(?:[;#].*|//.*)?$"""
)
_ENV_RE = re.compile(r"\{([A-Za-z_]\w*)\}")
_DEFAULT_SUFFIX = ".dasm"


def _error(lineno: int, col: int, message: str,
           source_path: Path) -> DasmSyntaxError:
    return DasmSyntaxError(lineno, col, message=message,
                           file=str(source_path))


def _expand_env(name: str, env: dict, lineno: int, col: int,
                source_path: Path) -> str:
    """Substitute {NAME} placeholders from the project environment."""
    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in env:
            raise _error(
                lineno, col,
                f"unknown environment variable '{key}' in import path {name!r}",
                source_path,
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
                 source_path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        raise _error(
            lineno, col, f"cannot read import {path}: {e}", source_path
        ) from e


def _resolve_text(text: str, base_dir: Path, env: dict,
                  search_paths: list[str], seen: set[Path], stack: list[Path],
                  source_path: Path) -> tuple[list[str], list[SourceLocation]]:
    out = []
    locations = []
    for lineno, line in enumerate(text.split("\n"), 1):
        match = _IMPORT_RE.match(line)
        if not match:
            out.append(line)
            locations.append(SourceLocation(source_path, lineno))
            continue

        raw_name = match.group("path")
        col = match.start("path") + 1
        name = _expand_env(raw_name, env, lineno, col, source_path)

        found, candidates = _find_import(name, base_dir, search_paths)
        if found is None:
            searched = "\n".join(f"  {candidate}" for candidate in candidates)
            raise _error(
                lineno, col,
                f"cannot import {raw_name!r}: file not found\n"
                f"searched:\n{searched}",
                source_path,
            )

        if found in stack:
            chain = " -> ".join(str(path) for path in [*stack, found])
            raise _error(
                lineno, col, f"circular import: {chain}", source_path
            )

        if found in seen:
            out.append("")          # keep one line in place of the import
            locations.append(SourceLocation(source_path, lineno))
            continue

        seen.add(found)
        stack.append(found)
        try:
            imported = _read_import(found, lineno, col, source_path)
            logger.info(f"File {anonymize_path(found)}")
            if imported.endswith("\n"):
                imported = imported[:-1]
            imported_lines, imported_locations = _resolve_text(
                imported, found.parent, env, search_paths, seen, stack, found
            )
            out.extend(imported_lines)
            locations.extend(imported_locations)
        finally:
            stack.pop()

    return out, locations


def resolve_with_map(text: str, env: dict | None = None,
                     paths: list[str] | None = None,
                     source_path: Path | str | None = None) -> ResolvedSource:
    """Inline all .import directives and return text plus a source map.

    Search order for a relative import: the importing file's directory, every
    entry from [dasm.imports].paths, then the current working directory.  When
    the name has no suffix, .dasm is tried as well.  Each file is inlined only
    once; repeated imports are replaced with an empty line.
    """
    env = env or {}
    search_paths = list(paths or [])

    if source_path is not None:
        root_path = Path(source_path)
        try:
            root_path = root_path.resolve()
        except OSError:
            pass
        base_dir = root_path.parent
        stack = [root_path]
    else:
        root_path = Path("<source>")
        base_dir = Path.cwd()
        stack = []

    seen: set[Path] = set()
    lines, locations = _resolve_text(
        text, base_dir, env, search_paths, seen, stack, root_path
    )
    return ResolvedSource(
        text="\n".join(lines),
        source_map=SourceMap(locations),
    )


def resolve(text: str, env: dict | None = None,
            paths: list[str] | None = None,
            source_path: Path | str | None = None) -> str:
    """Inline all .import directives and return one combined source string."""
    return resolve_with_map(text, env, paths, source_path).text
