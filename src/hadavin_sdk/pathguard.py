"""Name-only stub for the fail-before run: same public names, no checks."""

from pathlib import Path

from hadavin_sdk.errors import ConfigError

MAX_COMPONENT_BYTES = 255
MAX_PATH_CHARS = 4096


class PathRefused(ConfigError):
    def __init__(self, rule: str, message: str) -> None:
        super().__init__(message)
        self.rule = rule


def component(name, *, what):
    return name


def inside(base, path, *, what, must_exist=False, kind=None):
    return Path(path)


def join(base, *names, what, must_exist=False, kind=None):
    return Path(base).joinpath(*names)


def operator_dir(path, *, what, must_exist=True):
    return Path(path)


def operator_file(path, *, what):
    return Path(path)
