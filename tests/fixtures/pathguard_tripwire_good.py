"""SEEDED GOOD fixture for tests/test_pathguard_tripwire.py: nothing below may be reported. Never imported."""

import os

from hadavin_sdk import pathguard
from hadavin_sdk.config import confined


def reads_a_guarded_file(base):
    path = pathguard.join(base, "a.json", what="x", must_exist=True, kind="file")
    return path.read_bytes()


def lists_an_operator_folder(folder):
    root = pathguard.operator_dir(folder, what="x")
    return [p.name for p in root.iterdir()]


def guards_after_a_first_plain_assignment(folder):
    root = folder
    root = pathguard.operator_dir(root, what="x")
    return list(root.glob("*"))


def writes_and_replaces(base, name):
    final = pathguard.join(base, name, what="x")
    tmp = pathguard.join(final.parent, "." + name + ".tmp", what="x")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    os.close(fd)
    os.replace(tmp, final)
    tmp.unlink(missing_ok=True)


def calls_that_are_not_file_operations(items):
    items.get("a")
    return items.keys()


def uses_inside(base, path):
    real = pathguard.inside(base, path, what="x")
    return real.read_text()


def uses_operator_file(path):
    real = pathguard.operator_file(path, what="x")
    real.chmod(0o600)
    return real.read_bytes()


def uses_confined(base, name):
    real = confined(base, name)
    real.rmdir()


def a_string_replace_is_not_a_path_call(text):
    return text.replace("a", "b").replace("c", "d")
