import importlib
import logging
import os
import random
from glob import glob
from pathlib import Path

from colorama import Style, Fore

from profane.exceptions import PipelineConstructionError, InvalidConfigError, InvalidModuleError
from profane.frozendict import FrozenDict
import profane.constants as constants

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


_DEFAULT_RANDOM_SEED = 42
constants = constants.ConstantsRegistry()


class ModuleRegistry:
    """ Keeps track of modules that have been registered with `ModuleBase.register`"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.registry = {}
        self.shared_objects = {}

    def register(self, cls):
        """ Register a class that describes itself via a `module_type` and a `module_name variable. """

        if not hasattr(cls, "module_type"):
            raise InvalidModuleError(f"missing module_type for class: {cls}")

        if not hasattr(cls, "module_name"):
            raise InvalidModuleError(f"missing module_name for class: {cls}")

        module_type_registry = self.registry.setdefault(cls.module_type, {})

        # do we already have a different entry for this module_type and module_name?
        if module_type_registry.get(cls.module_name, cls) != cls:
            logger.warning(f"replacing entry {module_type_registry[cls.module_name]} for {cls.module_name} with {cls}")

        module_type_registry[cls.module_name] = cls

    def lookup(self, module_type, module_name):
        """ Return the class corresponding to a `module_type` and `module_name` pair. """

        if module_type not in self.registry:
            raise ValueError(f"unknown module_type '{module_type}'; known types: {self.get_module_types()}")

        if module_name not in self.registry[module_type]:
            raise ValueError(
                f"unknown module_name '{module_name}'; known modules of type '{module_type}': {sorted(self.get_module_names(module_type))}"
            )

        return self.registry[module_type][module_name]

    def get_module_types(self):
        return sorted(k for k in self.registry.keys() if len(self.registry[k]) > 0)

    def get_module_names(self, module_type):
        return sorted(self.registry[module_type])

    def get_registered_modules(self):
        return [
            (module_type, module_name)
            for module_type in self.get_module_types()
            for module_name in self.get_module_names(module_type)
        ]


module_registry = ModuleRegistry()


class Dependency:
    """ Represents a dependency on another module.

        If name is None, the dependency must be provided by the pipeline (i.e., in `provided_modules`).
        Otherwise, the module class corresponding to `name` will be used.

        If default_config_overrides is a dict, it will be used to override the dependency's default config options.
        Note that user may still override these options e.g. on the command line.
    """

    def __init__(self, key, module, name=None, default_config_overrides=None, provide_this=False, provide_children=None):
        try:
            if "BASE_PACKAGE" in constants:
                importlib.import_module(f"{constants['BASE_PACKAGE']}.{module}")
        except ModuleNotFoundError as e:
            pass

        self.key = key
        self.module = module
        self.name = name
        self.provide_this = provide_this

        if default_config_overrides is None:
            default_config_overrides = {}

        if provide_children is None:
            provide_children = []

        self.default_config_overrides = default_config_overrides
        self.provide_children = provide_children

    def __str__(self):
        return f"<Dependency key={self.key} {self.module}={self.name} overrides={self.default_config_overrides} provide_this={self.provide_this} provide_children={self.provide_children}>"


class ConfigOption:
    """ Represents a config option required by a model. """

    def __init__(self, key, default_value, description="", value_type=None):
        self.key = key
        self.default_value = default_value
        self.description = description

        if value_type is None:
            self.type = type(self.default_value)
        else:
            self.type = value_type

        if self.type == bool:
            self.type = lambda x: str(x).lower() == "true"
        elif self.type in [str, type(None)]:
            self.type = lambda x: None if str(x).lower() == "none" else str(x)
        elif self.type == "strlist":
            self.type = lambda x: self._convert_to_list(x, str)
        elif self.type == "intlist":
            self.type = lambda x: self._convert_to_list(x, int)
        elif self.type == "floatlist":
            self.type = lambda x: self._convert_to_list(x, float)
        if self.type in [list, tuple]:
            raise InvalidModuleError(
                "ConfigOptions with a default_value of list must set value_type to one of: 'strlist', 'intlist', 'floatlist'"
            )

    @staticmethod
    def _convert_to_list(values, item_type):
        if isinstance(values, str):
            values = values.split(",")
        elif isinstance(values, (tuple, list)):
            pass
        else:
            values = [values]

        return tuple(item_type(item) for item in values)


class ModuleBase:
    """ Base class for profane modules.
        Module construction proceeds as follows:
        1) Any config options not present in `config` are filled in with their default values. Config options and their defaults are specified in the `config_spec` class attribute.
        2) Any dependencies declared in the `dependencies` class attribute are recursively instantiated. If the dependency object is present in `provide`, this object will be used instead of instantiating a new object for the dependency.
        3) The module object's `config` variable is updated to reflect the configs of its dependencies and then frozen.

        After construction is complete, the module's dependencies are available as instance variables: self.`dependency key`.

        Args:
            config: dictionary containing a config to apply to this module and its dependencies
            provide: dictionary mapping dependency keys to module objects 
            share_dependency_objects: if true, dependencies will be cached in the registry based on their configs and reused. See the `share_objects` argument of `ModuleBase.create`.
    """

    config_spec = []
    dependencies = []
    _dependency_objects = {}
    config_keys_not_in_path = []
    requires_random_seed = False

    @staticmethod
    def register(cls):
        module_registry.register(cls)
        return cls

    @classmethod
    def _validate_config(cls, config):
        """ Validates `config` and raises an exception if any option present is not recognized or is the wrong type """

        options = {option.key: option for option in cls.config_spec}
        dependencies = set(dependency.key for dependency in cls.dependencies)

        for key in list(config.keys()):
            if key == "name":
                if config[key] != cls.module_name:
                    raise InvalidConfigError(f"key name={config[key]} does not match cls.module_name={cls.module_name}")
            elif key == "seed":
                if not cls.requires_random_seed:
                    raise InvalidConfigError(f"seed={config[key]} was provided but cls.requires_random_seed=False")
                # this cannot happen because we overwrite the seed in module init
                # if config["seed"] != constants.RANDOM_SEED:
                #    raise InvalidConfigError(f"seed={config[key]} does not match constants.RANDOM_SEED={constants.RANDOM_SEED}")
            elif key in dependencies:
                if isinstance(config[key], str):
                    raise InvalidConfigError(
                        f"invalid option: '{key}={config[key]}' ... maybe you meant: '{key}.name={config[key]}'"
                    )
            elif key not in options:
                raise InvalidConfigError(f"received unknown config key: {key}")
            else:
                config[key] = options[key].type(config[key])

        return config

    @classmethod
    def _fill_in_default_config_options(cls, config):
        """ Adds default values to config for any key that is not already present """
        for option in cls.config_spec:
            if option.key not in config:
                config[option.key] = option.type(option.default_value)
        return config

    @classmethod
    def create(cls, name, config=None, provide=None, share_objects=True):
        """ Creates a module by looking up a `name` in the module registry corresponding to the calling class' module type.
            `config` and `provide` are passed to the module's constructor.

            If `share_objects` is true:
            - any instantiated module objects will be cached in the registry based on their configs
            - when a module with the same config is created, the cached object is returned rather than a new instance
            This behavior applies to any module dependencies as well.
        """

        module_cls = module_registry.lookup(cls.module_type, name)
        module_obj = module_cls(config, provide, share_dependency_objects=share_objects)

        if not share_objects:
            return module_obj

        if module_obj.config not in module_registry.shared_objects:
            module_registry.shared_objects[module_obj.config] = module_obj

        return module_registry.shared_objects[module_obj.config]

    @classmethod
    def lookup(cls, name):
        return module_registry.lookup(cls.module_type, name)

    @classmethod
    def compute_config(cls, config=None, provide=None):
        """ Return this module class' effective config after taking the module's defaults, `config`, and `provide` into account. """
        return cls(config, provide=provide, share_dependency_objects=False).config

    def __init__(self, config=None, provide=None, share_dependency_objects=False, build=True):
        if isinstance(config, FrozenDict):
            config = config._as_dict()

        # it is important that we create a new provide object here, because _instantiate_dependencies may add entries to it.
        # we don't want those entries to propagate higher in the module graph.
        # see the test with 'threerank_separate' in test_task_pipeline.py for illustration.
        if not config:
            config = {}
        if not provide:
            provide = {}

        # make a copy so we don't modify the object that was passed
        config = config.copy()

        config["name"] = self.module_name
        self._set_random_seed(config)
        self.config = self._validate_config(config)
        self.config = self._fill_in_default_config_options(self.config)
        self._instantiate_dependencies(self.config, provide, share_dependency_objects)
        # freeze config
        self.config = FrozenDict(self.config)

        if build and hasattr(self, "build"):
            self.build()

    def _instantiate_dependencies(self, config, provide, share_objects):
        dependencies = {}
        for dependency in self.dependencies:
            # if the dependency object has been provided, use it directly
            if dependency.key in provide:
                dependencies[dependency.key] = provide[dependency.key]

                if dependency.key in config:
                    logger.warning(
                        "config['%s']='%s' is being replaced with config from provided module: %s",
                        dependency.key,
                        config[dependency.key],
                        provide[dependency.key].config,
                    )

                continue

            # if not, we need to instantiate the dependency
            # apply any config overrides
            dependency_config = dependency.default_config_overrides.copy()

            # apply any config options we received
            for k, v in config.get(dependency.key, {}).items():
                dependency_config[k] = v

            # identify correct class for this dependency
            dependency_name = dependency_config.get("name", dependency.name)
            if dependency_name is None:
                raise PipelineConstructionError(f"No name provided for dependency {dependency}")
            dependency_cls = module_registry.lookup(dependency.module, dependency_name)

            # instantiate the dependency
            dependencies[dependency.key] = dependency_cls.create(
                dependency_name, dependency_config, provide=provide, share_objects=share_objects
            )

            # provide the dependency for later modules?
            if dependency.provide_this:
                if dependency.key in provide:
                    raise PipelineConstructionError(
                        f"'provide_this' flag on dependency '{dependency}' would replace existing provided module {provide[dependency.key]} with {dependencies[dependency.key]}"
                    )
                provide[dependency.key] = dependencies[dependency.key]

            # provide any of this dependency's children for later modules?
            for child_dep_key in dependency.provide_children:
                if child_dep_key in provide:
                    raise PipelineConstructionError(
                        f"'provide_children' list for dependency '{dependency}' would replace existing provided module"
                    )

                if not hasattr(dependencies[dependency.key], child_dep_key):
                    raise PipelineConstructionError(
                        f"'provide_children' list for dependency '{dependency}' contains key '{child_dep_key}', but the module has no such dependency"
                    )

                provide[child_dep_key] = getattr(dependencies[dependency.key], child_dep_key)

        # add dependency configs and objects to self
        for module_name, module_obj in dependencies.items():
            if hasattr(self, module_name):  # and getattr(self, module_name) != module_obj:
                raise PipelineConstructionError(f"would assign {module_obj} to self.{module_name} but it already exists")

            setattr(self, module_name, module_obj)
            self._dependency_objects[module_name] = module_obj
            self.config[module_name] = module_obj.config

    def _set_random_seed(self, config):
        """ If this module requires a random seed, set one and initialize the RNGs.
            TODO write detailed docs for the behavior. difficulty is that RNGs are shared, so first seed set must be used. """

        if not self.requires_random_seed:
            return

        # must use the same seed for all modules
        if "RANDOM_SEED" not in constants:
            constants["RANDOM_SEED"] = int(config.get("seed", _DEFAULT_RANDOM_SEED))
            random.seed(constants["RANDOM_SEED"])

            try:
                import numpy as np

                np.random.seed(constants["RANDOM_SEED"])
                self.rng = np.random.Generator(np.random.PCG64(constants["RANDOM_SEED"]))
            except ModuleNotFoundError:
                # numpy is not available
                self.rng = None

        config["seed"] = constants["RANDOM_SEED"]

    def get_cache_path(self):
        """ Return an absolute path that can be used for caching.
            The path is a function of the module's config and the configs of its dependencies.
        """

        return constants["CACHE_BASE_PATH"] / self.get_module_path()

    def get_module_path(self):
        """ Return a relative path encoding the module's config and its dependenceis """

        if self.dependencies:
            prefix = os.path.join(
                *[self._dependency_objects[dependency.key].get_module_path() for dependency in self.dependencies]
            )
            return os.path.join(prefix, self._this_module_path_only())
        else:
            return self._this_module_path_only()

    def _this_module_path_only(self):
        """ Return a path encoding only the module's config (and not its dependencies) """

        module_cfg = {
            k: v for k, v in self.config.items() if k not in self._dependency_objects and k not in self.config_keys_not_in_path
        }
        module_name_key = self.module_type + "-" + module_cfg.pop("name")
        return "_".join([module_name_key] + [f"{k}-{v}" for k, v in sorted(module_cfg.items())])

    def print_module_graph(self, prefix=""):
        childprefix = prefix + "    "
        this = f"{self.module_type}={self.module_name}"
        print(prefix + this)
        for dependency in self.dependencies:
            child = self._dependency_objects[dependency.key]
            child.print_module_graph(prefix=childprefix)

    def print_module_config(self, prefix=""):
        lines = []
        self._config_summary(lines, prefix)
        print("\n".join(lines))

    def _config_summary(self, lines, prefix=""):
        options = {option.key: option for option in self.config_spec}
        options["name"] = ConfigOption("name", self.module_name)
        options["seed"] = ConfigOption("seed", _DEFAULT_RANDOM_SEED, "random seed")

        # show name, followed by module config, followed by dependencies
        order = sorted(self.config.keys(), key=lambda x: (x != "name", x in self._dependency_objects, x))
        for key in order:
            if key in self._dependency_objects:
                lines.append(f"{prefix}{key}:{Style.RESET_ALL}")
                self._dependency_objects[key]._config_summary(lines, prefix=prefix + "  ")
            else:
                if options[key].description:
                    lines.append(f"{prefix}{Style.DIM}# {options[key].description}{Style.RESET_ALL}")

                color = ""
                if self.config[key] != options[key].default_value:
                    color = Fore.GREEN
                lines.append(f"{color}{prefix}{key} = {self.config[key]}{Style.RESET_ALL}")


def import_all_modules(file, package):
    pwd = os.path.dirname(file)
    for fn in glob(os.path.join(pwd, "*.py")):
        module_name = os.path.basename(fn)[:-3]
        if not (module_name.startswith("__") or module_name.startswith("flycheck_") or module_name.startswith("#")):
            importlib.import_module(f"{package}.{module_name}")
