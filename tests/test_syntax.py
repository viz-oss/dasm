"""Unit tests for parsing syntax"""

import pytest
from syntax import parse, DasmSyntaxError

def test_missing_value():
    with pytest.raises(DasmSyntaxError) as e:
        parse('r0 = ')
    assert e.value.line == 1
    assert e.value.col == 6
    assert 'number' in str(e.value) and 'register' in str(e.value)
