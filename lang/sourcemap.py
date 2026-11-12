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
class ResolvedSource:
    """Combined source text together with its line map."""

    text: str
    source_map: SourceMap


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

    def relocate(self, error: DasmSyntaxError) -> DasmSyntaxError:
        """Translate an error's virtual line to its original file and line.

        Errors that already carry a file (for example import resolution errors)
        are returned unchanged.
        """
        if error.file is not None or error.line is None:
            return error
        location = self.lookup(error.line)
        if location is None:
            return error
        error.file = str(location.path)
        error.line = location.line
        return error
