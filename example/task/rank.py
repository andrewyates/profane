from profane import ModuleBase, Dependency, ConfigOption

from task import Task


@Task.register
class Rank(Task):
    module_name = "rank"
    dependencies = [
        Dependency(key="benchmark", module="benchmark", name="wsdm20demo", provide_this=True, provide_children=["collection"]),
        Dependency(key="searcher", module="searcher", name="BM25"),
    ]
    commands = ["run"] + Task.help_commands
    default_command = "run"

    def run(self):
        print("in rank.run")
        print("benchmark:", self.benchmark)
        print("searcher:", self.searcher)
