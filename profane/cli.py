import numpy as np


def config_list_to_dict(l):
    d = {}
    for kv in l:
        if kv.count("=") != 1:
            raise ValueError(f"invalid 'key=value' pair: {kv}")

        k, v = kv.split("=")
        if len(v) == 0:
            raise ValueError(f"invalid 'key=value' pair: {kv}")

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
    else:
        d[k] = v


def convert_string_to_list(values, item_type):
    if isinstance(values, str):
        as_range = _parse_string_as_range(values, item_type)
        if as_range:
            return tuple(as_range)

        values = values.split(",")
    elif isinstance(values, (tuple, list)):
        pass
    else:
        values = [values]

    return tuple(item_type(item) for item in values)


def _parse_string_as_range(s, item_type):
    parts = s.split(",")
    if len(parts) != 2:
        return None

    ends = parts[0].split("..")
    if len(ends) != 2:
        return None

    start, stop = ends
    start, stop = item_type(start), item_type(stop)
    step = item_type(parts[1])

    if stop <= start:
        raise ValueError(f"invalid range: {s}")

    if item_type == int:
        return list(range(start, stop, step))
    elif item_type == float:
        precision = max(_rounding_precision(x) for x in (start, stop, step))
        return [round(item, precision) for item in np.arange(start, stop, step)]

    raise ValueError(f"unsupported type: {item_type}")


def convert_list_to_string(lst, item_type):
    lst = [item_type(x) for x in lst]

    # check whether we can represent lst as "start..stop,step"
    if len(lst) > 2 and item_type in (float, int):
        # for floating point lists, determine the number of significant digits to keep based on the user's input
        # e.g., 1.01 --> 2 or 3e-05 --> 5; this is necessary to avoid floating point weirdness when adding step
        if item_type == int:
            precision = 0
        else:
            precision = max(_rounding_precision(x) for x in lst)

        # is the distance between successive list elements always the same as the distance between the first two elements?
        step = round(lst[1] - lst[0], precision)
        is_range = all(lst[idx + 1] == round(lst[idx] + step, precision) for idx in range(len(lst) - 1))

        if is_range:
            start = round(lst[0], precision)
            stop = round(lst[-1] + step, precision)

            start, stop, step = _unnecessary_floats_to_ints([start, stop, step])
            return f"{start}..{stop},{step}"
        else:
            lst = _unnecessary_floats_to_ints(lst)

    return ",".join(str(item) for item in lst)


def _rounding_precision(x):
    x = str(x)
    if len(x.split(".")) == 2:
        return len(x.split(".")[1])
    elif len(x.split("e-")) == 2:
        return int(x.split("e-")[1])

    raise ValueError(f"cannot parse: {x}")


def _unnecessary_floats_to_ints(lst):
    return [int(x) if int(x) == x else x for x in lst]
