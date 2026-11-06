"""Kind fixtures for the contract suites. Each module here registers the kinds it can build with `@kind`;
`tests/contracts/conftest.py` imports every module at collection, so a new kind is one new module."""

import importlib.util
import os
from collections import defaultdict
from collections.abc import Callable
from typing import Any

import pytest

KINDS: dict[str, dict[str, Callable[..., Any]]] = defaultdict(dict)


def kind(capability: str, name: str):
    def register(fn):
        KINDS[capability][name] = fn
        return fn

    return register


def _fail_rule() -> bool:
    """True where a missing backend must fail the run instead of skipping: `HADAVIN_REQUIRE_PG` is set and not
    "0", or `CI` is "true" or "1" (GitHub Actions sets `CI=true`)."""
    require = os.environ.get("HADAVIN_REQUIRE_PG", "")
    return (require != "" and require != "0") or os.environ.get("CI", "") in ("true", "1")


def require_backend(name: str, *, dsn: bool = True, module_level: bool = False) -> None:
    """Return when backend `name` can be used; else fail (under the fail rule) or skip with a reason that starts
    `require_backend:`, which the session-end check in `conftest.py` looks for. Only "postgres" exists: it needs
    the driver and, unless `dsn=False`, the `HADAVIN_TEST_PG_DSN` of the CI service."""
    if name != "postgres":
        raise ValueError(f"require_backend: unknown backend {name!r}")
    reason = None
    if importlib.util.find_spec("psycopg") is None:
        reason = "the postgres driver is not installed (install the `pg` extra)"
    elif dsn and not os.environ.get("HADAVIN_TEST_PG_DSN"):
        reason = "HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)"
    if reason is None:
        return
    if _fail_rule():
        pytest.fail(f"require_backend: {name}: {reason}", pytrace=False)
    pytest.skip(f"require_backend: {name}: {reason}", allow_module_level=module_level)
