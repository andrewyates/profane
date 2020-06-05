import datetime
import json
import os
import socket

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()


class Run(Base):
    __tablename__ = "run"

    run_id = sa.Column(sa.Integer, primary_key=True)
    command = sa.Column(sa.String)
    config = sa.Column(sa.JSON)

    hostname = sa.Column(sa.String)
    pid = sa.Column(sa.Integer)

    status = sa.Column(sa.Enum("RUNNING", "COMPLETED", "INTERRUPTED", "FAILED", "QUEUED", name="statuses"))
    priority = sa.Column(sa.Integer)
    tries = sa.Column(sa.Integer, default=0)

    start_time = sa.Column(sa.DateTime(timezone=True))
    stop_time = sa.Column(sa.DateTime(timezone=True))
    queue_time = sa.Column(sa.DateTime(timezone=True))

    idx1 = sa.Index("idx_status_priority_tries", status, priority, tries)


class DBManager:
    def __init__(self, url):
        engine = sa.create_engine(url)
        if not database_exists(engine.url):
            print("creating missing DB")
            create_database(engine.url)

        Base.metadata.create_all(engine)

        self.session = sessionmaker(bind=engine)()

    def queue_run(self, command, config, priority=0):
        run = Run(
            config=config,
            command=command,
            priority=priority,
            status="QUEUED",
            queue_time=datetime.datetime.now(datetime.timezone.utc),
        )

        self.session.add(run)
        self.session.commit()
        return run.run_id

    def clear_zombie_runs(self):
        # TODO first find runs, then do for_update later when clearing them only
        for run in (
            self.session.query(Run)
            .filter(sa.and_(Run.status == "RUNNING", Run.hostname == socket.gethostname()))
            .with_for_update()
        ):
            if not os.path.exists(f"/proc/{run.pid}"):
                print(f"found zombie run_id={run.run_id} with pid: {run.pid}")
                run.status = "FAILED"
                self.session.add(run)

        self.session.commit()

    def get_eligible_run(self, max_tries=3):
        run = (
            self.session.query(Run)
            .filter(sa.or_(Run.status == "QUEUED", Run.status == "FAILED"))
            .filter(Run.tries < max_tries)
            .order_by(Run.priority.desc(), sa.text("random()"))
            .limit(1)
            .with_for_update()
            .first()
        )

        return run

    def started_event(self, run):
        run = self.session.query(Run).filter(Run.run_id == run.run_id).with_for_update().one()
        run.start_time = datetime.datetime.now(datetime.timezone.utc)
        run.hostname = socket.gethostname()
        run.pid = os.getpid()
        run.status = "RUNNING"
        run.tries += 1
        self.session.add(run)
        self.session.commit()

    def _ended_event(self, run, status):
        run = self.session.query(Run).filter(Run.run_id == run.run_id).with_for_update().one()
        run.stop_time = datetime.datetime.now(datetime.timezone.utc)
        run.status = status
        self.session.add(run)
        self.session.commit()

    def completed_event(self, run):
        return self._ended_event(run, "COMPLETED")

    def interrupted_event(self, run):
        return self._ended_event(run, "INTERRUPTED")

    def failed_event(self, run):
        return self._ended_event(run, "FAILED")
