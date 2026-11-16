"""
SourceMap module.

This module provides classes and functions necessary to map virtual line numbers
(used during the parsing/resolution phase after inlining) back to the original
source file locations.

When the resolver inlines multiple source files into a single combined text,
the line numbers in the combined text no longer correspond directly to the
line numbers in the original files on disk. A SourceMap tracks contiguous
segments of lines and translates a virtual line number back to its original
(file, line) coordinates.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from pathlib import Path

from .exceptions import DasmSyntaxError


@dataclass(frozen=True)
class SourceLocation:
    """
    Represents a specific location within the original source code.

    This object pinpoints where a particular line or column originated.
    """
    path: Path | str
    line: int


@dataclass(frozen=True)
class SourceSegment:
    """
    Represents a contiguous range of virtual lines that originated from a single source file.

    This is used when multiple original lines are combined into a single block
    in the virtual text.
    """
    start: int          # The first virtual line number (1-based) covered by this segment.
    end: int            # The last virtual line number (1-based) covered by this segment.
    path: Path | str    # The path to the original source file.
    line: int           # The original line number corresponding to the `start` virtual line.


@dataclass(frozen=True)
class ColumnSegment:
    """
    Represents a contiguous range of processed columns within a single line.

    This is used to map processed column indices back to the original source column indices,
    especially when dealing with variable-width tokens or substitutions.
    """
    start: int          # The first processed column number (1-based).
    end: int            # The last processed column number (1-based).
    source: int         # The original column number corresponding to the `start` processed column.
    fixed: bool = False  # If True, the column is a substituted constant, meaning all columns in the segment map to `source`.


class ColumnMap:
    """
    Provides translation between processed column indices and original source column indices
    for a single line.
    """
    def __init__(self, segments: list[ColumnSegment] | None = None):
        """
        Initializes the ColumnMap with segments defining the mapping.

        Args:
            segments: An optional list of ColumnSegment objects defining the mapping.
        """
        self.segments = segments or []
        # Pre-calculate starting points for efficient lookup using binary search.
        self._starts = [segment.start for segment in self.segments]

    def lookup(self, processed_col: int) -> int:
        """
        Translates a processed column index back to its original source column index.

        Args:
            processed_col: The column index in the processed text (1-based).

        Returns:
            The original source column index (1-based).
        """
        if not self.segments:
            return processed_col

        # Find the segment that contains the processed column index.
        index = bisect.bisect_right(self._starts, processed_col) - 1
        if index < 0:
            return processed_col

        segment = self.segments[index]
        if segment.fixed:
            # If the segment is fixed, all columns map to the same source column.
            return segment.source
        
        # Otherwise, calculate the offset within the segment.
        return segment.source + (processed_col - segment.start)


@dataclass(frozen=True)
class ResolvedSource:
    """
    Holds the combined source text along with the SourceMap required to translate
    virtual line numbers back to original source locations.
    """
    text: str
    source_map: SourceMap


def _format_context(line: str, col: int) -> str:
    """
    Builds a context line, similar to those used in Lark parsers, indicating the caret position.

    Args:
        line: The original source line text.
        col: The column index (1-based) where the error occurred.

    Returns:
        A string containing the line followed by a caret pointing to the error column.
    """
    # Calculate the number of spaces needed to reach the column index.
    before = line[:max(col - 1, 0)]
    # Use expandtabs() to handle potential tab characters in the original line.
    return f"{line}\n{' ' * len(before.expandtabs())}^\n"


class SourceMap:
    """
    Manages the mapping between virtual line numbers (in the combined text) and
    the original source locations.

    This class is responsible for tracking how original lines map to the combined
    virtual lines.
    """
    def __init__(self, locations: list[SourceLocation]):
        """
        Initializes the SourceMap by processing a list of SourceLocation objects
        into contiguous SourceSegment objects.

        Args:
            locations: A list of SourceLocation objects, ordered by virtual line number.
        """
        self.segments: list[SourceSegment] = []
        for virtual_line, location in enumerate(locations, 1):
            if self.segments:
                # Check if we can extend the last segment
                last = self.segments[-1]
                next_line = last.line + (virtual_line - last.start)
                
                # If the path is the same and the line number is contiguous, extend the segment.
                if (last.end == virtual_line - 1
                        and last.path == location.path
                        and next_line == location.line):
                    # Update the end boundary of the existing segment.
                    self.segments[-1] = SourceSegment(
                        last.start, virtual_line, last.path, last.line
                    )
                    continue
            
            # Otherwise, start a new segment.
            self.segments.append(SourceSegment(
                virtual_line, virtual_line, location.path, location.line
            ))
        
        # Store starting points for efficient lookup.
        self._starts = [segment.start for segment in self.segments]
        # Cache for original file contents read during error reporting.
        self._file_lines: dict[str, list[str]] = {}

    def lookup(self, virtual_line: int) -> SourceLocation | None:
        """
        Translates a 1-based virtual line number back to the original SourceLocation.

        Args:
            virtual_line: The line number in the combined text.

        Returns:
            The SourceLocation object if found, otherwise None.
        """
        # Find the segment that covers this virtual line.
        index = bisect.bisect_right(self._starts, virtual_line) - 1
        if index < 0:
            return None
        
        segment = self.segments[index]
        if virtual_line > segment.end:
            return None
        
        # Calculate the original line number based on the segment's starting line and offset.
        return SourceLocation(
            segment.path, segment.line + (virtual_line - segment.start)
        )

    def original_line(self, location: SourceLocation) -> str | None:
        """
        Retrieves the original source line corresponding to a given SourceLocation.

        This method reads the file content only once and caches it.

        Args:
            location: The SourceLocation object specifying the file and line.

        Returns:
            The original line string, or None if the line cannot be retrieved.
        """
        path = str(location.path)
        if path not in self._file_lines:
            try:
                # Read the file content if it hasn't been read yet.
                text = Path(path).read_text(encoding="utf-8")
            except (OSError, ValueError):
                self._file_lines[path] = []
            else:
                # Split into lines for indexed access.
                self._file_lines[path] = text.split("\n")
        
        lines = self._file_lines[path]
        if 1 <= location.line <= len(lines):
            return lines[location.line - 1]
        return None

    def relocate(self, error: DasmSyntaxError, column_maps: list[ColumnMap] | None = None) -> DasmSyntaxError:
        """
        Translates an error object from its virtual location (in the combined text)
        to the original source file location and context.

        This is crucial for providing helpful error messages to the user.

        Args:
            error: The DasmSyntaxError object containing virtual location data.
            column_maps: Optional list of ColumnMap objects, one for each line in the error context.

        Returns:
            The DasmSyntaxError object, updated with original file path, line, and message.
        """
        # If the error already has a file or line (e.g., it's an import resolution error),
        # no translation is needed.
        if error.file is not None or error.line is None:
            return error

        # 1. Find the original location corresponding to the error's virtual line.
        location = self.lookup(error.line)
        if location is None:
            return error

        # 2. Translate the column index if column maps are provided.
        columns_mapped = False
        if (error.map_columns and column_maps is not None
                and error.col is not None):
            # The error line index corresponds to the index in column_maps.
            index = error.line - 1
            if 0 <= index < len(column_maps):
                # Use the map to find the original column index.
                error.col = column_maps[index].lookup(error.col)
                columns_mapped = True

        # 3. Update the error object with original file and line information.
        error.file = str(location.path)
        error.line = location.line

        # 4. Generate the detailed error message context.
        if (error.context and error.col is not None
                and (columns_mapped or not error.map_columns)):
            # Retrieve the original line text.
            line = self.original_line(location)
            if line is not None:
                # Format the error message to include the caret pointing to the error column.
                error.message = _format_context(line, error.col)

        # 5. Finalize the error object.
        error.args = (str(error),)
        return error
