import pytest

from profane.base import ModuleBase, PipelineConstructionError, ConfigOption, InvalidConfigError, Dependency, module_registry
from profane.cli import convert_string_to_list, convert_list_to_string


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
    assert convert_string_to_list("0.00001..0.00002,2e-06", float) == (1e-05, 1.2e-05, 1.4e-05, 1.6e-05, 1.8e-05, 2e-05)

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
