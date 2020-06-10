import os
import setuptools
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)


with open("README.md", "r") as fh:
    long_description = fh.read()

# from https://packaging.python.org/guides/single-sourcing-package-version/
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), "rt") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name="profane",
    version=get_version("profane/__init__.py"),
    author="Andrew Yates",
    author_email="",
    description="A library for creating complex experimental pipelines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/andrewyates/profane",
    packages=setuptools.find_packages(),
    install_requires=["colorama", "docopt", "sqlalchemy", "sqlalchemy-utils"],
    classifiers=["Programming Language :: Python :: 3", "Operating System :: OS Independent"],
    python_requires=">=3.6",
    cmdclass={"develop": PostDevelopCommand, "install": PostInstallCommand},
    include_package_data=True,
)
