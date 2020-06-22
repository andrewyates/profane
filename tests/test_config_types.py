import random
import pytest
import numpy as np
from hypothesis import given
from hypothesis.strategies import lists, integers, floats, composite

from profane.base import ModuleBase, PipelineConstructionError, InvalidConfigError, Dependency, module_registry
from profane.config_option import ConfigOption, convert_string_to_list, convert_list_to_string


def test_types():
    module_registry.reset()

    class ModuleFoo(ModuleBase):
        module_type = "Atype"
        module_name = "foo"
        config_spec = [
            ConfigOption(key="str1", default_value="foo"),
            ConfigOption(key="str2", default_value=9, value_type=str),
            ConfigOption(key="int1", default_value=2),
            ConfigOption(key="int2", default_value="3", value_type=int),
            ConfigOption(key="float1", default_value=2.2),
            ConfigOption(key="float2", default_value="3.3", value_type=float),
            ConfigOption(key="bool1", default_value=False),
            ConfigOption(key="bool2", default_value="false", value_type=bool),
            ConfigOption(key="bool3", default_value="true", value_type=bool),
            ConfigOption(key="strlist1", default_value=3, value_type="strlist"),
            ConfigOption(key="strlist2", default_value=[4, 5], value_type="strlist"),
            ConfigOption(key="strlist3", default_value="4,5", value_type="strlist"),
            ConfigOption(key="intlist1", default_value=3, value_type="intlist"),
            ConfigOption(key="intlist2", default_value="3", value_type="intlist"),
            ConfigOption(key="intlist3", default_value=(4, 5), value_type="intlist"),
            ConfigOption(key="intlist4", default_value="4,5", value_type="intlist"),
            ConfigOption(key="floatlist1", default_value=3, value_type="floatlist"),
            ConfigOption(key="none-or-str", default_value=None),
        ]

    foo = ModuleFoo()
    assert type(foo.config["str1"]) == str
    assert type(foo.config["str2"]) == str
    assert type(foo.config["int1"]) == int
    assert type(foo.config["int2"]) == int
    assert type(foo.config["float1"]) == float
    assert type(foo.config["float2"]) == float

    assert type(foo.config["none-or-str"]) == type(None)

    assert foo.config["bool1"] is False
    assert foo.config["bool2"] is False
    assert foo.config["bool3"] is True

    assert foo.config["strlist1"] == ("3",)
    assert foo.config["strlist2"] == ("4", "5")
    assert foo.config["strlist3"] == ("4", "5")
    assert foo.config["intlist1"] == (3,)
    assert foo.config["intlist2"] == (3,)
    assert foo.config["intlist3"] == (4, 5)
    assert foo.config["intlist4"] == (4, 5)
    assert foo.config["floatlist1"] == (3.0,)

    foo = ModuleFoo({"none-or-str": "str"})
    assert type(foo.config["none-or-str"]) == str
    assert foo.config["none-or-str"] == "str"


def test_convert_string_to_list():
    # test typed conversions
    assert convert_string_to_list("1,2", int) == (1, 2)
    assert convert_string_to_list("1", int) == (1,)
    assert convert_string_to_list("1.1,1.2", float) == (1.1, 1.2)
    assert convert_string_to_list("1.1", float) == (1.1,)
    assert convert_string_to_list("1,2", str) == ("1", "2")
    assert convert_string_to_list("1", str) == ("1",)

    # test range conversions
    assert convert_string_to_list("1..4,1", int) == (1, 2, 3)
    assert convert_string_to_list("1..4,0.5", float) == (1, 1.5, 2, 2.5, 3, 3.5)
    assert convert_string_to_list("0.65..0.8,0.05", float) == (0.65, 0.7, 0.75)
    assert convert_string_to_list("0.00001..0.00002,2e-06", float) == (1e-05, 1.2e-05, 1.4e-05, 1.6e-05, 1.8e-05)

    # test range checking endpoints
    assert convert_string_to_list("1,2,3,4,6", int) == (1, 2, 3, 4, 6)
    assert convert_string_to_list("0,2,3,4,5", int) == (0, 2, 3, 4, 5)

    with pytest.raises(ValueError):
        convert_string_to_list("1..4,1", str)

    with pytest.raises(ValueError):
        convert_string_to_list("3..1,1", int)


def test_convert_list_to_string():
    assert convert_list_to_string([1.1, 1.3, 1.5, 1.7], float) == "1.1..1.9,0.2"
    assert convert_list_to_string([1, 3, 5], int) == "1..7,2"

    assert convert_list_to_string([1, 3, 4], int) == "1,3,4"
    assert convert_list_to_string([1, 3, 4.9999], float) == "1,3,4.9999"
    assert convert_list_to_string([1.0, 3, 4.9999], float) == "1,3,4.9999"
    assert convert_list_to_string([1.001, 3, 4.9999], float) == "1.001,3,4.9999"

    assert convert_list_to_string([1, 3], int) == "1,3"
    assert convert_list_to_string([1.0, 3.0], float) == "1.0,3.0"

    assert convert_list_to_string([1], int) == "1"
    assert convert_list_to_string([1.0], float) == "1.0"

    assert convert_list_to_string(["1"], str) == "1"
    assert convert_list_to_string(["1", "2"], str) == "1,2"
    assert convert_list_to_string(["1", "2", "3", "4"], str) == "1,2,3,4"

    assert convert_list_to_string([1, 2, 3.0], float) == "1..4,1"
    assert convert_list_to_string([1.5, 2, 2.5], float) == "1.5..3,0.5"


@composite
def arithmetic_sequence(draw, dtype):
    if dtype == "int":
        start = draw(integers(min_value=0, max_value=3))
        end = start + draw(integers(min_value=1, max_value=10))
        step = draw(integers(min_value=1, max_value=3))
    elif dtype == "float":
        if random.random() < 0.5:
            start = draw(floats(min_value=0.0, max_value=1.0))  # step=0.01
            end = start + draw(floats(min_value=1.0, max_value=3.0))  # , 0.01)
            step = draw(floats(min_value=0.01, max_value=0.51))
        else:
            start = draw(floats(min_value=0.0, max_value=1.0))
            end = start + draw(floats(min_value=0.0001, max_value=0.002))
            step = draw(floats(min_value=0.0001, max_value=0.0005))
    else:
        raise ValueError(f"Unexpected dtype {dtype}")

    lst = np.around(np.arange(start, end, step), decimals=4).tolist()
    assert len(lst) > 0
    return lst


@given(lst=lists(elements=integers(min_value=0, max_value=100), min_size=1, max_size=10, unique=True))
def test_string_list_inversion_random_int(lst):
    lst = sorted(lst) 
    assert tuple(lst) == convert_string_to_list(convert_list_to_string(lst, int), int)


@given(lst=lists(elements=floats(min_value=0.0, max_value=5), min_size=1, max_size=10, unique=True))
def test_string_list_inversion_random_float(lst):
    assert tuple(lst) == convert_string_to_list(convert_list_to_string(lst, float), float)


@given(arithmetic_sequence(dtype="int"))
def test_string_list_inversion_arithmetic_int(lst):
    assert tuple(lst) == convert_string_to_list(convert_list_to_string(lst, int), int)


@given(arithmetic_sequence(dtype="float"))
def test_string_list_inversion_arithmetic_float(lst):
    assert tuple(lst) == convert_string_to_list(convert_list_to_string(lst, float), float)
