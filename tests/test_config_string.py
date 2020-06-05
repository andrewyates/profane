import pytest

from profane.cli import config_list_to_dict


def test_config_string_to_dict():
    args = ["foo.bar=yes", "main=42"]
    assert config_list_to_dict(args) == {"foo": {"bar": "yes"}, "main": "42"}

    args = ["foo.bar=yes", "main=42", "foo.bar=override"]
    assert config_list_to_dict(args) == {"foo": {"bar": "override"}, "main": "42"}

    with pytest.raises(ValueError):
        args = ["invalid"]
        config_list_to_dict(args)

    with pytest.raises(ValueError):
        args = ["invalid="]
        config_list_to_dict(args)

    with pytest.raises(ValueError):
        args = ["invalid.=1"]
        config_list_to_dict(args)

    with pytest.raises(ValueError):
        args = [".invalid=1"]
        config_list_to_dict(args)
