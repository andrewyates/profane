def config_list_to_dict(l):
    d = {}

    for k, v in _config_list_to_pairs(l):
        _dot_to_dict(d, k, v)

    return d


def _dot_to_dict(d, k, v):
    if k.startswith(".") or k.endswith("."):
        raise ValueError(f"invalid path: {k}")

    if "." in k:
        path = k.split(".")
        current_k = path[0]
        remaining_path = ".".join(path[1:])

        d.setdefault(current_k, {})
        _dot_to_dict(d[current_k], remaining_path, v)
    elif k.lower() == "file":
        with open(v, "rt") as f:
            pairs = [pair for line in f for pair in line.strip().split(" ")]

        for new_k, new_v in _config_list_to_pairs(pairs):
            _dot_to_dict(d, new_k, new_v)
    else:
        d[k] = v


def _config_list_to_pairs(l):
    pairs = []
    for kv in l:
        kv = kv.strip()

        if len(kv) == 0:
            continue

        if kv.count("=") != 1:
            raise ValueError(f"invalid 'key=value' pair: {kv}")

        k, v = kv.split("=")
        if len(v) == 0:
            raise ValueError(f"invalid 'key=value' pair: {kv}")

        pairs.append((k, v))

    return pairs
