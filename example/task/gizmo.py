from profane import Dependency

from profane.task import Command, Task


@Task.register
class Gizmo(Task):
    module_name = "gizmo"
    dependencies = [
        Dependency(key="collection", module="collection", name="MSMARCO"),
    ]
    default_command = "thing1"
    commands = [Command("thing1"), Command("thing2")]

    def thing1(self):
        print("thing1")
        print(self.collection)

    def thing2(self):
        print("thing2")
