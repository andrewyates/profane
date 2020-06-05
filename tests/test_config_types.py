import pytest

from profane.base import ModuleBase, PipelineConstructionError, ConfigOption, InvalidConfigError, Dependency, module_registry


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
            ConfigOption(key="list1", default_value="a", value_type=list),
            ConfigOption(key="list2", default_value="a,b,c", value_type=list),
            ConfigOption(key="bool1", default_value=False),
            ConfigOption(key="bool2", default_value="false", value_type=bool),
            ConfigOption(key="bool3", default_value="true", value_type=bool),
        ]

    foo = ModuleFoo()
    print(foo.config)
    print([(x.key, x.type) for x in ModuleFoo.config_spec])
    assert type(foo.config["str1"]) == str
    assert type(foo.config["str2"]) == str
    assert type(foo.config["int1"]) == int
    assert type(foo.config["int2"]) == int
    assert type(foo.config["float1"]) == float
    assert type(foo.config["float2"]) == float

    assert foo.config["list1"] == ("a",)
    assert foo.config["list2"] == ("a", "b", "c")
    assert type(foo.config["list1"]) == tuple
    assert type(foo.config["list2"]) == tuple

    assert foo.config["bool1"] is False
    assert foo.config["bool2"] is False
    assert foo.config["bool3"] is True
