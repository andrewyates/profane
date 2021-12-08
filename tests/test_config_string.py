import os
import pytest
import yaml

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


def test_config_string_with_files_to_dict(tmpdir):
    mainfn = os.path.join(tmpdir, "main.txt")
    with open(mainfn, "wt") as f:
        print("main=24  # comment", file=f)
        print("#main=25", file=f)

    foofn = os.path.join(tmpdir, "foo.txt")
    with open(foofn, "wt") as f:
        print("test1=20  submod1.test1=21 ", file=f)
        print("submod1.submod2.test1=22", file=f)
        print("test3=extra", file=f)
        print(f"FILE={mainfn}", file=f)

    args = ["foo.test1=1", f"foo.file={foofn}", "main=42", f"file={mainfn}"]
    assert config_list_to_dict(args) == {
        "foo": {"test1": "20", "test3": "extra", "main": "24", "submod1": {"test1": "21", "submod2": {"test1": "22"}}},
        "main": "24",
    }

def test_config_string_with_yaml_files_to_dict(tmpdir):
    mainfn = os.path.join(tmpdir, "main.yaml")

    main_data = dict(
        main = 24,
    )
    with open(mainfn, "wt") as f:
        yaml.dump(main_data, f, default_flow_style=False)
    
    foo_data = dict(
        test1=20,
        submod1=dict(test1=21, submod2=dict(test1=22)),
        test3="extra",
        FILE=mainfn
    )  

    foofn = os.path.join(tmpdir, "foo.yaml")
    with open(foofn, "wt") as f:
        yaml.dump(foo_data, f, default_flow_style=False)

    args = ["foo.test1=1", f"foo.file={foofn}", "main=42", f"file={mainfn}"]
    assert config_list_to_dict(args) == {
        "foo": {"test1": "20", "test3": "extra", "main": "24", "submod1": {"test1": "21", "submod2": {"test1": "22"}}},
        "main": "24",
    }
    
