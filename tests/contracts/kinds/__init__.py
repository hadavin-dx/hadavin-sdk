"""Kind fixtures for the contract suites. Each module here registers the kinds it can build with `@kind`;
`tests/contracts/conftest.py` imports every module at collection, so a new kind is one new module."""

import importlib.util
import os
from collections import defaultdict
from collections.abc import Callable
from typing import Any

import pytest

KINDS: dict[str, dict[str, Callable[..., Any]]] = defaultdict(dict)

# The import name of the Postgres driver, named once in the contract suite's helpers besides the namespace in
# `store_postgres.py` (this module must test for the driver before that one can be imported). A test that needs to
# know whether the driver is installed calls `require_backend("postgres", dsn=False)`; the driver swap of P4d-c
# changes this line and `store_postgres.py`, not the tests.
PG_DRIVER_MODULE = "psycopg"


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
    if importlib.util.find_spec(PG_DRIVER_MODULE) is None:
        reason = "the postgres driver is not installed (install the `pg` extra)"
    elif dsn and not os.environ.get("HADAVIN_TEST_PG_DSN"):
        reason = "HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)"
    if reason is None:
        return
    if _fail_rule():
        pytest.fail(f"require_backend: {name}: {reason}", pytrace=False)
    pytest.skip(f"require_backend: {name}: {reason}", allow_module_level=module_level)


def pg_test_dsn() -> str:
    """The `HADAVIN_TEST_PG_DSN` of the CI service, for a test that connects. Skips (or fails under the fail rule)
    when the driver or the variable is missing, so no test dies with a KeyError. This is the only place in the tests
    that reads the variable by key; `test_pg_dsn_guard.py` fails on any other `environ[...]` read of it."""
    require_backend("postgres")
    return os.environ["HADAVIN_TEST_PG_DSN"]
