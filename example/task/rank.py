from profane import Dependency

from profane.task import Command, Task


@Task.register
class Rank(Task):
    module_name = "rank"
    dependencies = [
        Dependency(key="benchmark", module="benchmark", name="wsdm20demo", provide_this=True, provide_children=["collection"]),
        Dependency(key="searcher", module="searcher", name="BM25"),
    ]
    commands = [Command("run")]
    default_command = "run"

    def run(self):
        print("in rank.run")
        print("benchmark:", self.benchmark)
        print("searcher:", self.searcher)
