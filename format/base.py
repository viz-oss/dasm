"""Base file inherited by all formats"""

from abc import ABC, abstractmethod


class Format(ABC):

    # File extension
    ext = ''

    @abstractmethod
    def output(self) -> bytes:
        raise NotImplementedError
