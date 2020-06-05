[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) 
[![Worfklow](https://github.com/andrewyates/profane/workflows/pytest/badge.svg)](https://github.com/andrewyates/profane/actions)
[![PyPI version fury.io](https://badge.fury.io/py/profane.svg)](https://pypi.python.org/pypi/profane/)


# Overview
*Profane* is a library for creating complex experimental pipelines. Profane pipelines are based on two key ideas:
1. An experiment is a *function of its configuration*. In other words, an experiment should be deterministic given a set of experimental parameters (random seed, specific algorithms to run, etc).
2. An experiment is described as a *DAG* representing control flow in which the *state of a node is independent of its parent's state*. That is, a *node's operation is a function of its configuration and the configurations of its children*. This means that a node may not modify the configuration (or state) of its children (or descendants).

These allow for the construction of a flexible pipeline with automatic caching. Each node's configuration can be modified to change experimental parameters, and a node's output can be safely cached in a path derived from its configuration and the configurations of its children. These nodes are called modules.

This library is heavily inspired by the excellent [sacred](https://sacred.readthedocs.io/en/stable/) library. Among other differences, profane imposes a specific structure on the pipeline and leverages this to allow profane modules to be dynamically configured (which would be similar to dynamic sacred ingredients). Profane was developed based on experiences using sacred with a heavily modified pipeline initialization step.

## Example
The `example/` directory contains a module graph similar to that used in Capreolus. Run it with the `run.sh` script.
