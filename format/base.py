"""Base file inherited by all formats"""

from abc import ABC, abstractmethod


class Format(ABC):

    # File extension
    ext = ''

    # Memory address of the first byte of the assembled code.
    origin = 0

    # Whether an entry jump must precede the assembled code.
    entry_jump = False

    @abstractmethod
    def output(self, words: list[int], entry: int | None = None) -> bytes:
        """
        Generates the final byte sequence for the assembled code.

        Args:
            words: The list of assembled instruction words (integers).
            entry: Optional memory address of the entry point.

        Returns:
            The complete byte sequence of the formatted file.
        """
        raise NotImplementedError
