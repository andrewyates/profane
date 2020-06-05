import setuptools
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install

from profane import __version__ as profane_version


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

setuptools.setup(
    name="profane",
    version=profane_version,
    author="Andrew Yates",
    author_email="",
    description="A library for creating complex experimental pipelines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/andrewyates/profane",
    packages=setuptools.find_packages(),
    install_requires=["colorama", "docopt", "numpy>=1.17", "sqlalchemy", "sqlalchemy-utils"],
    classifiers=["Programming Language :: Python :: 3", "Operating System :: OS Independent"],
    python_requires=">=3.6",
    cmdclass={"develop": PostDevelopCommand, "install": PostInstallCommand},
    include_package_data=True,
)
