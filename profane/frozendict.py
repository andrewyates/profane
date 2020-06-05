import collections
import json


class FrozenDict(collections.abc.Mapping):
    """ Based on frozen dict implementation from https://stackoverflow.com/a/2704866 by Mike Graham """

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        _freeze_dicts(self._d)

        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __str__(self):
        return self._d.__str__()

    def __repr__(self):
        return self._d.__repr__()

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(frozenset(self._d.items()))
        return self._hash

    def _as_dict(self):
        return self._d.copy()


def _freeze_dicts(d):
    for k in list(d.keys()):
        if isinstance(d[k], dict):
            d[k] = FrozenDict(d[k])
