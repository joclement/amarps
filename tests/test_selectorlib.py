import pytest
from selectorlib.formatter import Integer


def test_format_Integer():
    formatter = Integer()
    assert formatter.format("1") == 1
    assert formatter.format("11") == 11
    with pytest.raises(ValueError):
        formatter.format("1.111")
    with pytest.raises(ValueError):
        formatter.format("1,111")
