import pytest
from syntax import parse, DasmSyntaxError

def test_missing_value():
    with pytest.raises(DasmSyntaxError) as ei:
        parse('r0 = ')
    assert ei.value.line == 1
    assert ei.value.col == 6
    assert 'number' in str(ei.value) and 'register' in str(ei.value)
