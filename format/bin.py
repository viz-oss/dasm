"""Format: raw binary"""

from format.base import Format


class FormatBin(Format):

    # File extension
    ext = 'bin'

    def output(self, words: list[int], entry: int | None = None) -> bytes:    
        return bytes(words)

EXPORTS = FormatBin
