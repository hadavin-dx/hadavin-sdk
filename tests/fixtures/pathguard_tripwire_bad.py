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


def replaces_a_path(a, b):
    a.replace(b)


def renames_a_path(a, b):
    a.rename(b)


def removes_a_folder(a):
    a.rmdir()


def touches_a_path(a):
    a.touch()


def links_a_path(a, b):
    a.symlink_to(b)


def changes_a_mode(a):
    a.chmod(0o600)


def writes_bytes_to_a_parameter(a):
    a.write_bytes(b"x")


def writes_text_to_a_parameter(a):
    a.write_text("x")


def opens_a_method_path(a):
    a.open()


def counts_component_as_a_guard(base, name):
    safe = pathguard.component(name, what="x")
    (base / safe).read_text()
    target = pathguard.component(name, what="y")
    target.unlink()


def counts_operator_text_as_a_guard(path):
    pathguard.operator_text(path, what="x")
    path.read_text()
