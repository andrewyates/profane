from functools import wraps
import importlib
import os
import sys

from pathlib import Path

from docopt import docopt
from profane import config_list_to_dict, constants, module_registry, ModuleBase


class Command:
    """Represents a command accepted by a Task module

    Args:
       command_name (str): a name for the command, which must correspond to a function in the task class
       description (str): a description of the command to show in help messages
    """

    def __init__(self, command_name, description=""):
        self.command_name = command_name
        self.description = description


class Task(ModuleBase):
    module_type = "task"
    help_commands = [Command("describe"), Command("print_config"), Command("print_pipeline")]
    default_command = "describe"
    requires_random_seed = True

    def print_config(self):
        print("Configuration:")
        self.print_module_config(prefix="  ")

    def print_pipeline(self):
        print("Module graph:")
        self.print_module_graph(prefix="  ")

    def describe(self):
        self.print_pipeline()
        print("\n")
        self.print_config()

    def command(self, description=""):
        if not hasattr(self, "commands"):
            self.commands = {}

        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                return f(*args, **kwargs)

            self.commands[f.__name__] = description
            return decorated

        return decorator


def _parse_task_string(s):
    """Parses a string of the form "<task name>.<command name>". Returns a `cls` task object and a command `str`"""
    fields = s.split(".")
    taskstr = fields[0]
    task_cls = Task.lookup(taskstr)

    if len(fields) == 2:
        cmdstr = fields[1]
    else:
        cmdstr = task_cls.default_command

    return taskstr, cmdstr


def _prepare_task(fullcommand, config):
    taskstr, cmdstr = _parse_task_string(fullcommand)
    task = Task.create(taskstr, config=config)
    task_entry_function = getattr(task, cmdstr)

    if not hasattr(task, cmdstr):
        print("error: invalid command:", cmdstr)
        print(f"valid commands for task={task.module_name}: {sorted(task.commands)}")
        sys.exit(2)

    return task, task_entry_function


def _construct_docopt_help(filename, valid_loglevels):
    pad = "              "
    command_help = ""
    for task_name in module_registry.get_module_names("task"):
        command_help += "\n"
        for cmd in Task.lookup(task_name).commands:
            command_help += pad + f"{task_name + '.' + cmd.command_name:<28} {cmd.description}\n"

    # Tasks: {', '.join(module_registry.get_module_names('task'))}
    hlp = f"""
            Usage:
              {filename} COMMAND [(with CONFIG...)] [options]
              {filename} help [COMMAND]
              {filename} (-h | --help)


            Options:
              -h --help                     Print this help message and exit.
              -l VALUE --loglevel=VALUE     Set the log level: {', '.join(valid_loglevels)}
              -p VALUE --priority=VALUE     Sets the priority for a queued up experiment. No effect without -q flag.
              -q --queue                    Only queue this run, do not start it.


            Arguments:
              COMMAND   Name of command to run (see below for list of commands)
              CONFIG    Configuration assignments of the form foo.bar=17

            Commands:{command_help}

            Help commands are shared across all of the above tasks:
              {', '.join([x.command_name for x in Task.help_commands])}
    """

    hlp = "\n".join([x[12:] for x in hlp.split("\n")])

    return hlp


def run(base_package, package_path, filename, version="none", argv=None):
    argv = argv if argv else sys.argv[1:]
    # specify a base package that we should look for modules under (e.g., <BASE>.task)
    # constants must be specified before importing Task (or any other modules!)
    constants["BASE_PACKAGE"] = str(base_package)
    constants["PACKAGE_PATH"] = Path(package_path)
    constants["ENV_LOGGING"] = constants["BASE_PACKAGE"] + "_LOGGING"
    constants["ENV_DB"] = constants["BASE_PACKAGE"] + "_DB"

    # ensure the task modules have been loaded
    importlib.import_module(f"{constants['BASE_PACKAGE']}.task")

    # hack to make docopt print full help message if no arguments are give
    if len(sys.argv) == 1:
        sys.argv.append("-h")

    valid_loglevels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    hlp = _construct_docopt_help(filename, valid_loglevels)
    arguments = docopt(hlp, version=version, argv=argv)

    if arguments["--loglevel"]:
        loglevel = arguments["--loglevel"].upper()
        if loglevel not in valid_loglevels:
            print("error: --loglevel must be one of:", ", ".join(valid_loglevels))
            sys.exit(1)

        os.environ[constants["ENV_LOGGING"]] = loglevel

    # prepare task even if we're queueing, so that we validate the config
    config = config_list_to_dict(arguments["CONFIG"])
    task, task_entry_function = _prepare_task(arguments["COMMAND"], config)

    if arguments["--queue"]:
        from profane import DBManager

        if not arguments["--priority"]:
            arguments["--priority"] = 0

        db = DBManager(os.environ.get(constants["ENV_DB"]))
        db.queue_run(command=arguments["COMMAND"], config=config, priority=arguments["--priority"])
    else:
        print(f"starting {arguments['COMMAND']} with config: {task.config}\n")
        task_entry_function()
