import pytest

from profane.base import ModuleBase, PipelineConstructionError, InvalidConfigError, Dependency, module_registry
from profane.config_option import ConfigOption


@pytest.fixture
def test_modules():
    module_registry.reset()

    class ModuleTypeA(ModuleBase):
        module_type = "Atype"

    @ModuleTypeA.register
    class AParent(ModuleTypeA):
        module_name = "AParent"
        config_spec = [ConfigOption(key="key1", default_value="val1", description="test option")]
        dependencies = [
            Dependency(key="myfoo", module="Atype", name="AFoo", default_config_overrides={"changethis": 42}),
            Dependency(key="bar", module="Atype", name="ABar"),
        ]

    @ModuleTypeA.register
    class AFoo(ModuleTypeA):
        module_name = "AFoo"
        config_spec = [
            ConfigOption(key="foo1", default_value="val1", description="test option"),
            ConfigOption(key="changethis", default_value=0, description="something to override"),
        ]
        dependencies = [Dependency(key="myfoobar", module="Atype", name="AFooBar")]

    @ModuleTypeA.register
    class ABar(ModuleTypeA):
        module_name = "ABar"
        config_spec = [ConfigOption(key="bar1", default_value="val1", description="test option")]

    @ModuleTypeA.register
    class AFooBar(ModuleTypeA):
        module_name = "AFooBar"
        config_spec = [ConfigOption(key="foobar1", default_value="val1", description="test option")]

    return ModuleTypeA, AParent


def test_module_creation():
    class SimpleModuleType(ModuleBase):
        module_type = "SimpleType"

    @SimpleModuleType.register
    class ModuleA(SimpleModuleType):
        module_name = "A"
        config_spec = [ConfigOption(key="key1", default_value="val1", description="test option")]

    with pytest.raises(ValueError):
        SimpleModuleType.create(name="invalid")

    # check that default config options are filled
    mod1 = SimpleModuleType.create(name="A", config={})
    assert mod1.config["key1"] == "val1"

    # check that the default config option was overwritten
    mod2 = SimpleModuleType.create(name="A", config={"key1": "val2"})
    assert mod2.config["key1"] == "val2"

    # check that this is equivalent to calling init
    mod2same = ModuleA(config={"key1": "val2"})
    assert mod2.__class__ == mod2same.__class__
    assert mod2.config == mod2same.config
    assert mod2.dependencies == mod2same.dependencies

    # check that invalid config options raise an exception
    with pytest.raises(InvalidConfigError):
        SimpleModuleType.create(name="A", config={"invalid": "yes"})


def test_module_creation_with_dependencies(test_modules):
    ModuleTypeA, AParent = test_modules

    # override myfoo.myfoobar.foobar1 and use default values for all other options
    config = {"myfoo": {"myfoobar": {"foobar1": "val2"}}}
    mod = ModuleTypeA.create(name="AParent", config=config)

    # check that all dependency objects have been created
    myfoo = mod.myfoo
    myfoobar = mod.myfoo.myfoobar
    bar = mod.bar

    # check that top level module and dependencies have the correct configs
    correct_parent_config = {
        "name": "AParent",
        "key1": "val1",
        "myfoo": {"foo1": "val1", "changethis": 42, "name": "AFoo", "myfoobar": {"foobar1": "val2", "name": "AFooBar"}},
        "bar": {"bar1": "val1", "name": "ABar"},
    }
    assert mod.config == correct_parent_config
    assert myfoo.config == correct_parent_config["myfoo"]
    assert bar.config == correct_parent_config["bar"]
    assert myfoobar.config == correct_parent_config["myfoo"]["myfoobar"]

    # test that creating AParent via init behaves the same
    mod2 = AParent(config=config)
    assert mod2.config == correct_parent_config
    assert mod2.dependencies == mod.dependencies


def test_module_creation_with_provided_dependencies(test_modules):
    ModuleTypeA, AParent = test_modules

    # override AFoo's 'myfoobar' dependency to be an instance of 'ABar'
    foo = ModuleTypeA.create(name="AFoo", config={"foo1": "provided1", "myfoobar": {"name": "ABar"}})
    # check myfoobar is an 'ABar' rather than the default of 'AFooBar'
    assert foo.myfoobar.module_name == "ABar"

    provided = {"myfoo": foo}
    mod = ModuleTypeA.create(name="AParent", config={}, provide=provided)

    # check that provided module was used
    assert mod.myfoo == foo
    assert mod.config["myfoo"]["foo1"] == "provided1"

    # test that creating AParent via init behaves the same
    mod2 = AParent(provide=provided)
    assert mod2.config == mod.config
    assert mod2.dependencies == mod.dependencies


def test_module_compute_config(test_modules):
    ModuleTypeA, AParent = test_modules

    default_parent_config = {
        "name": "AParent",
        "key1": "val1",
        "myfoo": {"foo1": "val1", "changethis": 42, "name": "AFoo", "myfoobar": {"foobar1": "val1", "name": "AFooBar"}},
        "bar": {"bar1": "val1", "name": "ABar"},
    }

    mod = AParent(config={"key1": "non_default_value"})

    # the default config is returned, not the active config
    assert AParent.compute_config() == default_parent_config

    # the config is computed from the default and the given config
    modified_config = default_parent_config.copy()
    modified_config["myfoo"]["foo1"] = "different"
    assert AParent.compute_config(config={"myfoo": {"foo1": "different"}}) == modified_config

    # the config is computed based on the provided module also
    modified_config["bar"]["bar1"] = "providedval"
    abar = ModuleTypeA.create("ABar", config={"bar1": "providedval"})
    assert AParent.compute_config(config={"myfoo": {"foo1": "different"}}, provide={"bar": abar}) == modified_config
