import os
import sys

from docopt import docopt

from profane import DBManager, config_list_to_dict, constants

# specify a base package that we should look for modules under (e.g., <BASE>.task)
# constants must be specified before importing Task (or any other modules!)
constants["BASE_PACKAGE"] = "example"

from task import Task


def parse_task_string(s):
    fields = s.split(".")
    task = fields[0]
    task_cls = Task.lookup(task)

    if len(fields) == 2:
        cmd = fields[1]
    else:
        cmd = task_cls.default_command

    if not hasattr(task_cls, cmd):
        print("error: invalid command:", s)
        print(f"valid commands for task={task}: {sorted(task_cls.commands)}")
        sys.exit(2)

    return task, cmd


def prepare_task(fullcommand, config):
    taskstr, commandstr = parse_task_string(fullcommand)
    task = Task.create(taskstr, config)
    task_entry_function = getattr(task, commandstr)
    return task, task_entry_function


if __name__ == "__main__":
    help = """
            Usage:
              run.py COMMAND [(with CONFIG...)] [options]
              run.py help [COMMAND]
              run.py (-h | --help)


            Options:
              -h --help                     Print this help message and exit.
              -l VALUE --loglevel=VALUE     Set the log level: DEBUG, INFO, WARNING, ERROR, or CRITICAL.
              -p VALUE --priority=VALUE     Sets the priority for a queued up experiment. No effect without -q flag.
              -q --queue                    Only queue this run, do not start it.


            Arguments:
              COMMAND   Name of command to run (see below for list of commands)
              CONFIG    Configuration assignments of the form foo.bar=17


            Commands:
              rank.run                   ...description here...
              rank.describe              ...description here...
           """

    # hack to make docopt print full help message if no arguments are give
    if len(sys.argv) == 1:
        sys.argv.append("-h")

    arguments = docopt(help, version="example")

    if arguments["--loglevel"]:
        loglevel = arguments["--loglevel"].upper()
        valid_loglevels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

        if loglevel not in valid_loglevels:
            print("error: log level must be one of:", ", ".join(valid_loglevels))
            sys.exit(1)

        os.environ["EXAMPLE_LOGGING"] = loglevel

    # prepare task even if we're queueing, so that we validate the config
    config = config_list_to_dict(arguments["CONFIG"])
    task, task_entry_function = prepare_task(arguments["COMMAND"], config)

    if arguments["--queue"]:
        if not arguments["--priority"]:
            arguments["--priority"] = 0

        db = DBManager(os.environ.get("EXAMPLE_DB"))
        db.queue_run(command=arguments["COMMAND"], config=config, priority=arguments["--priority"])
    else:
        print(f"starting {arguments['COMMAND']} with config: {task.config}\n")
        task_entry_function()
