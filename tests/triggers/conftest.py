"""The strict switch for the trigger tests that need a PostgreSQL server.

Without ``HADAVIN_TEST_PG_DSN`` those tests skip (``pg_schema`` of tests/contracts/kinds/store_postgres.py
skips with a reason that names the variable), so a run with no database is green without having run
them. With ``HADAVIN_REQUIRE_PG=1`` in the environment every such skip under tests/triggers is reported
as a FAILURE: the run that is handed in as evidence sets it, and then cannot pass by skipping.

Covered: tests under tests/triggers only (a conftest applies to its own folder). A skip counts as "the
database is missing" when its reason names ``HADAVIN_TEST_PG_DSN`` or the driver ``psycopg`` (the
reason of ``pytest.importorskip("psycopg")``, for a run that has the variable but not the driver).
Any other skip (the Windows guard of the SIGTERM tests, say) stays a skip.
"""

from __future__ import annotations

import os

import pytest

STRICT_VARIABLE = "HADAVIN_REQUIRE_PG"
DSN_VARIABLE = "HADAVIN_TEST_PG_DSN"
MISSING_DATABASE_WORDS = (DSN_VARIABLE, "psycopg")


def strict() -> bool:
    return os.environ.get(STRICT_VARIABLE) == "1"


def skip_reason(report: pytest.TestReport) -> str:
    """The reason text of a skipped report (pytest keeps it as the last part of a three-part tuple)."""
    longrepr = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2])
    return str(longrepr)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    report = outcome.get_result()
    if not (strict() and report.skipped) or hasattr(report, "wasxfail"):
        return
    reason = skip_reason(report)
    if not any(word in reason for word in MISSING_DATABASE_WORDS):
        return
    report.outcome = "failed"
    report.longrepr = (
        f"{STRICT_VARIABLE}=1: this test needs the PostgreSQL server and must not be skipped. "
        f"Set {DSN_VARIABLE} to a reachable server (with the psycopg driver installed), "
        f"or unset {STRICT_VARIABLE}. The skip reason was: {reason}"
    )


def core_b_trigger_config() -> bool:
    """True when this tree has core-b's trigger config (`hadavin_sdk.config.TriggerSettings` and `Config.triggers`)."""
    from hadavin_sdk import config

    return hasattr(config, "TriggerSettings") and "triggers" in config.Config.model_fields


def require_core_b(*, allow_module_level: bool = False) -> None:
    """Skip, or with HADAVIN_REQUIRE_PG=1 FAIL, when core-b's trigger config is not on this tree: a run handed in
    as evidence cannot pass by skipping the tests that read a real config.

    The failure happens at TEST time, never at collection (an error at collection stops the whole pytest run, and
    nothing else is run). So at module level with the switch set this returns, and the module sets
    `REQUIRES_CORE_B = True`: `pytest_pyfunc_call` below then fails each of its tests with the message."""
    if core_b_trigger_config():
        return
    reason = "core-b trigger config (TriggerSettings, Config.triggers) not on this tree"
    if strict():
        if allow_module_level:
            return  # each test of the module fails in `pytest_pyfunc_call`
        pytest.fail(
            f"{STRICT_VARIABLE}=1: {reason}; the tests that need it must run, not skip.",
            pytrace=False,
        )
    pytest.skip(reason, allow_module_level=allow_module_level)


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> None:
    """A test of a module that sets `REQUIRES_CORE_B = True` fails (strict) or skips here when core-b's config is
    missing: in the call phase, so it is reported FAILED, not as a setup ERROR."""
    if getattr(pyfuncitem.module, "REQUIRES_CORE_B", False):
        require_core_b()
