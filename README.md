# Overview
This repository illustrates a "profane-style" pipeline for conducting complex experiments. This pipeline is based on two key ideas:
1. An experiment is a *function of its configuration*. In other words, an experiment should be deterministic given a set of experimental parameters (random seed, specific algorithms to run, etc).
2. An experiment is described as a *DAG* representing control flow in which the *state of a node is independent of its parent's state*. That is, a *node's operation is a function of its configuration and the configurations of its children*. This means that a node may not modify the configuration (or state) of its children (or descendants).

These allow for the construction of a flexible pipeline with automatic caching. Each node's configuration can be modified to change experimental parameters, and a node's output can be safely cached in a path derived from its configuration and the configurations of its children.

This library is heavily inspired by [sacred](https://sacred.readthedocs.io/en/stable/). Among other differences, `profane` imposes a specific structure on the pipeline and leverages this to allow profane modules to be dynamically configured (which would be similar to dynamic sacred ingredients). 

## Example
The `example/` directory contains a module graph similar to that used in Capreolus. Run it with the `run.sh` script.
