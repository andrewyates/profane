from functools import partial

import numpy as np

from profane.exceptions import InvalidModuleError


class ConfigOption:
    """ Represents a config option required by a module.
        When a module is created, any unspecified config options will receive `default_value`, 
        and all config options will be cast to value_type. The None type is considered to be a string.
        If one of the list types is used, the config option's value will always be provided to the module as a list.
        These lists can be converted to strings in list or range format when needed (see `ModuleBase._config_as_strings`).

    Args:
       key (str): a name for the config option
       default_value (str): the default value the config option should take
       description (str): a description to be shown in help messages
       value_type: either built-in type bool, int, float, or str; or "intlist", "floatlist", "strlist"
    """

    def __init__(self, key, default_value, description="", value_type=None):
        self.key = key
        self.default_value = default_value
        self.description = description

        if value_type == "strlist":
            self.string_representation = partial(convert_list_to_string, item_type=str)
        elif value_type == "intlist":
            self.string_representation = partial(convert_list_to_string, item_type=int)
        elif value_type == "floatlist":
            self.string_representation = partial(convert_list_to_string, item_type=float)
        else:
            self.string_representation = str

        if value_type is None:
            value_type = type(self.default_value)

        if value_type == bool:
            self.type = lambda x: str(x).lower() == "true"
        elif value_type in [str, type(None)]:
            self.type = lambda x: None if str(x).lower() == "none" else str(x)
        elif value_type == "strlist":
            self.type = partial(convert_string_to_list, item_type=str)
        elif value_type == "intlist":
            self.type = partial(convert_string_to_list, item_type=int)
        elif value_type == "floatlist":
            self.type = partial(convert_string_to_list, item_type=float)
        elif value_type in [list, tuple]:
            raise InvalidModuleError(
                "ConfigOptions with a default_value of list must set value_type to one of: 'strlist', 'intlist', 'floatlist'"
            )
        else:
            self.type = value_type


def convert_string_to_list(values, item_type):
    """ Convert a comma-seperated string '1,2,3' to a list of item_type elements. """

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
    """ Convert a list to a string.
        Try to represent it as a range if the list has more than two elements and item_type is float or int.
        [1,2]       -> "1,2"
        [1,2,3,4]   -> "1..5,1"
    """

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
