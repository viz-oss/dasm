"""Map virtual line numbers back to the original source files.

The resolver inlines imported files, so line numbers in the combined text no
longer match the files on disk.  A SourceMap stores contiguous segments and
translates a virtual line back to (file, line).
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from pathlib import Path

from .exceptions import DasmSyntaxError


@dataclass(frozen=True)
class SourceLocation:
    """An original source location."""

    path: Path | str
    line: int


@dataclass(frozen=True)
class SourceSegment:
    """A contiguous range of virtual lines coming from one source file."""

    start: int          # first virtual line, 1-based
    end: int            # last virtual line, 1-based
    path: Path | str
    line: int           # original line corresponding to `start`


@dataclass(frozen=True)
class ColumnSegment:
    """A contiguous range of processed columns from one original token."""

    start: int          # first processed column, 1-based
    end: int            # last processed column, 1-based
    source: int         # original column corresponding to `start`
    fixed: bool = False  # substituted constant: all columns map to `source`


class ColumnMap:
    """Translate processed columns in one line back to original columns."""

    def __init__(self, segments: list[ColumnSegment] | None = None):
        self.segments = segments or []
        self._starts = [segment.start for segment in self.segments]

    def lookup(self, processed_col: int) -> int:
        if not self.segments:
            return processed_col
        index = bisect.bisect_right(self._starts, processed_col) - 1
        if index < 0:
            return processed_col
        segment = self.segments[index]
        if segment.fixed:
            return segment.source
        return segment.source + (processed_col - segment.start)


@dataclass(frozen=True)
class ResolvedSource:
    """Combined source text together with its line map."""

    text: str
    source_map: SourceMap


def _format_context(line: str, col: int) -> str:
    """Build a Lark-style context line with a caret at `col`."""
    before = line[:max(col - 1, 0)]
    return f"{line}\n{' ' * len(before.expandtabs())}^\n"


class SourceMap:
    """Translate virtual line numbers to original source locations."""

    def __init__(self, locations: list[SourceLocation]):
        self.segments: list[SourceSegment] = []
        for virtual_line, location in enumerate(locations, 1):
            if self.segments:
                last = self.segments[-1]
                next_line = last.line + (virtual_line - last.start)
                if (last.end == virtual_line - 1
                        and last.path == location.path
                        and next_line == location.line):
                    self.segments[-1] = SourceSegment(
                        last.start, virtual_line, last.path, last.line
                    )
                    continue
            self.segments.append(SourceSegment(
                virtual_line, virtual_line, location.path, location.line
            ))
        self._starts = [segment.start for segment in self.segments]
        self._file_lines: dict[str, list[str]] = {}

    def lookup(self, virtual_line: int) -> SourceLocation | None:
        """Return the original location for a 1-based virtual line."""
        index = bisect.bisect_right(self._starts, virtual_line) - 1
        if index < 0:
            return None
        segment = self.segments[index]
        if virtual_line > segment.end:
            return None
        return SourceLocation(
            segment.path, segment.line + (virtual_line - segment.start)
        )

    def original_line(self, location: SourceLocation) -> str | None:
        """Read the original source line for a location, with caching."""
        path = str(location.path)
        if path not in self._file_lines:
            try:
                text = Path(path).read_text(encoding="utf-8")
            except (OSError, ValueError):
                self._file_lines[path] = []
            else:
                self._file_lines[path] = text.split("\n")
        lines = self._file_lines[path]
        if 1 <= location.line <= len(lines):
            return lines[location.line - 1]
        return None

    def relocate(self, error: DasmSyntaxError,
                 column_maps: list[ColumnMap] | None = None) -> DasmSyntaxError:
        """Translate an error's virtual location to the original source.

        Errors that already carry a file (for example import resolution errors)
        are returned unchanged.
        """
        if error.file is not None or error.line is None:
            return error
        location = self.lookup(error.line)
        if location is None:
            return error

        columns_mapped = False
        if (error.map_columns and column_maps is not None
                and error.col is not None):
            index = error.line - 1
            if 0 <= index < len(column_maps):
                error.col = column_maps[index].lookup(error.col)
                columns_mapped = True

        error.file = str(location.path)
        error.line = location.line

        if (error.context and error.col is not None
                and (columns_mapped or not error.map_columns)):
            line = self.original_line(location)
            if line is not None:
                error.message = _format_context(line, error.col)

        error.args = (str(error),)
        return error
