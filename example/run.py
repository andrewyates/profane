import os

from profane.task import run

if __name__ == "__main__":
    run(base_package="example", package_path=os.path.dirname(__file__), filename="run.py")
