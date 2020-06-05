import datetime
import os
import random
import sys
import time
import traceback
import sqlalchemy

import sql
from run import prepare_task

db = sql.DBManager(os.environ.get("EXAMPLE_DB"))


def try_run(run):
    if run.status not in ["QUEUED", "FAILED"]:
        return

    db.started_event(run)

    try:
        task, func = prepare_task(run.command, run.config)
        func()
        db.completed_event(run)
        print("run finished")
        return True
    except (Exception, KeyboardInterrupt) as e:
        db.failed_event(run)

        print("\nERROR: failed run for id: %s" % run)
        print("exception {0} with arguments:\n{1!r}".format(type(e).__name__, e.args))
        print(traceback.format_exc())

        return False


print("%s checking for work" % datetime.datetime.now())

try:
    db.clear_zombie_runs()

    run = db.get_eligible_run(max_tries=3)
    if run:
        try_run(run)

    print("%s done" % datetime.datetime.now())
except (sqlalchemy.exc.InvalidRequestError, sqlalchemy.exc.OperationalError) as e:
    if ("%s" % e).find("deadlock detected") != -1:
        print("got exception: %s\n" % e)
        print("%s deadlock detected; sleeping and exiting" % datetime.datetime.now())
        time.sleep(random.randint(60, 450))
        sys.exit(0)
    else:
        raise
