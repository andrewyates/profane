import pytest

from profane.base import InvalidModuleError, ModuleRegistry


def test_module_registry():
    registry = ModuleRegistry()

    with pytest.raises(ValueError):
        registry.lookup("missing_type", "missing_name")

    class VeryIncompleteModule:
        pass

    class HalfIncompleteModule:
        module_type = "incomplete"

    with pytest.raises(InvalidModuleError):
        registry.register(VeryIncompleteModule)

    with pytest.raises(InvalidModuleError):
        registry.register(HalfIncompleteModule)

    class MinimalRegisterableModule:
        module_type = "minimal"
        module_name = "MRM"

    registry.register(MinimalRegisterableModule)

    assert registry.lookup("minimal", "MRM") == MinimalRegisterableModule

    with pytest.raises(ValueError):
        registry.lookup("minimal", "missing")

    with pytest.raises(ValueError):
        registry.lookup("missing", "MRM")
