from profane import ModuleBase, Dependency, ConfigOption


class Task(ModuleBase):
    module_type = "task"
    commands = []
    help_commands = ["describe", "print_config", "print_paths", "print_pipeline"]
    default_command = "describe"
    requires_random_seed = True

    def print_config(self):
        print("Configuration:")
        self.print_module_config(prefix="  ")

    def print_paths(self):  # TODO
        pass

    def print_pipeline(self):
        print(f"Module graph:")
        self.print_module_graph(prefix="  ")

    def describe(self):
        self.print_pipeline()
        print("\n")
        self.print_config()
