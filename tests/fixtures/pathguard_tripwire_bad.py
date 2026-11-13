"""SEEDED BAD fixture for tests/test_pathguard_tripwire.py: every function below must be reported. Never imported."""

import os
import shutil
from pathlib import Path

from hadavin_sdk import pathguard


def reads_a_parameter(path):
    return path.read_bytes()


def reads_a_fresh_path(name):
    return Path(name).read_text()


def opens_a_name(name):
    with open(name) as f:
        return f.read()


def writes_after_a_plain_assignment(base):
    target = Path(base) / "x.txt"
    target.write_text("x")


def mkdirs_a_division(base):
    (base / "sub").mkdir()


def unlinks_a_listing_item(folder):
    safe = pathguard.operator_dir(folder, what="x")
    for p in safe.iterdir():
        p.unlink()


def reassigns_after_a_safe_call(base, name):
    p = pathguard.join(base, "ok", what="x")
    p = Path(name)
    p.read_text()


def replaces_with_an_unchecked_target(base, name):
    tmp = pathguard.join(base, "t", what="x")
    os.replace(tmp, name)


def copies(src, dst):
    shutil.copy(src, dst)


def os_calls(name):
    os.remove(name)
    os.listdir(name)
