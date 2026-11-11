"""One rule for the database tests of `migrate()`: a skip is allowed only when `HADAVIN_TEST_PG_DSN` is NOT set, and
it always says why. When the DSN is set, a missing driver is a FAILURE, because a skip there would hide the very tests
the DSN was set for."""

from __future__ import annotations

import importlib
import os
from collections.abc import Callable, Mapping
from types import ModuleType

import pytest

DSN_NAME = "HADAVIN_TEST_PG_DSN"


def require_module(
    name: str,
    environ: Mapping[str, str] | None = None,
    importer: Callable[[str], ModuleType] = importlib.import_module,
) -> ModuleType:
    """The module, or (no DSN) a module-level skip with a reason, or (DSN set) a failure that names the module."""
    env = os.environ if environ is None else environ
    try:
        return importer(name)
    except ImportError:
        if env.get(DSN_NAME):
            pytest.fail(
                f"{name} cannot be imported but {DSN_NAME} is set: this is a failure, not a skip",
                pytrace=False,
            )
        pytest.skip(
            f"{name} is not installed (the pg extra) and {DSN_NAME} is not set",
            allow_module_level=True,
        )


def require_test_module(name: str, environ: Mapping[str, str] | None = None) -> ModuleType:
    """A test-only module (pglast): outside CI a missing module skips the test with a reason; when `CI` is set it is a
    FAILURE, so a differential test cannot be skipped without anyone noticing."""
    env = os.environ if environ is None else environ
    try:
        return importlib.import_module(name)
    except ImportError:
        if env.get("CI"):
            pytest.fail(
                f"{name} cannot be imported but CI is set: this is a failure, not a skip",
                pytrace=False,
            )
        pytest.skip(f"{name} is not installed (test-only dependency; CI is not set)")
