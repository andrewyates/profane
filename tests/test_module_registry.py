import pytest

from profane.base import ModuleBase, InvalidModuleError, ModuleRegistry


def test_module_registry():
    registry = ModuleRegistry()

    with pytest.raises(ValueError):
        registry.lookup("missing_type", "missing_name")

    class VeryIncompleteModule(ModuleBase):
        pass

    class HalfIncompleteModule(ModuleBase):
        module_type = "incomplete"

    with pytest.raises(InvalidModuleError):
        registry.register(VeryIncompleteModule)

    with pytest.raises(InvalidModuleError):
        registry.register(HalfIncompleteModule)

    class MinimalRegisterableModule(ModuleBase):
        module_type = "minimal"
        module_name = "MRM"

    registry.register(MinimalRegisterableModule)

    assert registry.lookup("minimal", "MRM") == MinimalRegisterableModule

    with pytest.raises(ValueError):
        registry.lookup("minimal", "missing")

    with pytest.raises(ValueError):
        registry.lookup("missing", "MRM")

    class WrongDependenciesTypeModule:
        module_type = "wrongdependencies"
        module_name = "WDTM"

        dependencies = {}

    with pytest.raises(TypeError):
        registry.register(WrongDependenciesTypeModule)