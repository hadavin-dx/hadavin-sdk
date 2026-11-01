import json
import os

import pytest

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.k1b.causelist import load_cause_list


def _write(d, name, values):
    (d / name).write_text(json.dumps(values), encoding="utf-8")


def test_missing_directory_refused(tmp_path):
    with pytest.raises(ConfigError):
        load_cause_list(tmp_path / "nope")


def test_symlink_escape_refused(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    _write(outside, "services.json", ["a"])
    _write(outside, "fault_types.json", ["x"])
    d = tmp_path / "d"
    d.mkdir()
    _write(d, "fault_types.json", ["x"])
    try:
        os.symlink(outside / "services.json", d / "services.json")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(ConfigError):
        load_cause_list(d)


def test_plain_directory_loads(tmp_path):
    _write(tmp_path, "services.json", ["a"])
    _write(tmp_path, "fault_types.json", ["x"])
    assert load_cause_list(tmp_path).contains("a", "x")
