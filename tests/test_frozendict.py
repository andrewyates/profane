import pytest

from profane import FrozenDict


def test_frozen():
    d = FrozenDict({1: 2, "tuple": [9, 8], "inner": {"a": "b", "more": {"c": "d"}}})

    with pytest.raises(TypeError):
        d[1] = 3

    with pytest.raises(TypeError):
        d["inner"]["a"] = "c"

    with pytest.raises(TypeError):
        d["inner"]["more"] = "e"

    with pytest.raises(TypeError):
        d["inner"]["more"]["c"] = "e"

    assert isinstance(d["tuple"], tuple)
    assert d["tuple"] == (9, 8)


def test_copy():
    d = FrozenDict({1: 2, 3: 4, "inner": {5: 6, "more": {7: 8, 9: 10}}})
    unfrozen = d.unfrozen_copy()
    unfrozen[1] = 11
    unfrozen["inner"][5] = 7
    unfrozen["inner"]["more"][9] = 12

    modified = FrozenDict({1: 11, 3: 4, "inner": {5: 7, "more": {7: 8, 9: 12}}})
    assert FrozenDict(unfrozen) == modified
