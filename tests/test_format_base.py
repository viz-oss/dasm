"""Unit tests for the base output format."""

import pytest

from format.base import Format


class _BaseProbe(Format):
    """Concrete subclass used to reach the abstract output body."""

    def output(self, words: list[int], entry: int | None = None) -> bytes:
        return super().output(words, entry)


def test_defaults():
    fmt = _BaseProbe()

    assert fmt.ext == ''
    assert fmt.origin == 0
    assert fmt.entry_jump is False


def test_abstract_output_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        _BaseProbe().output([])
