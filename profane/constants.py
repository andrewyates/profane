class ConstantsRegistry:
    """ Write-once registry that keeps track of constants shared by modules.
        ConstantsRegistry behaves like a dict, but keys can only be assigned to once.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._d = {}

    def __getitem__(self, key):
        return self._d[key]

    def __setitem__(self, key, val):
        if key in self._d:
            raise TypeError(
                f"ConstantsRegistry does not support re-assignment of existing entries; already contains: {key}={self._d[key]}"
            )
        else:
            self._d[key] = val

    def __repr__(self):
        return repr(self._d)

    def __len__(self):
        return len(self._d)

    def __contains__(self, item):
        return item in self._d
