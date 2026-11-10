"""The postgres test schema helper (``pg_schema``, used by the store contract and every database test) must FAIL in
CI when HADAVIN_TEST_PG_DSN is missing and may skip only on a developer machine. CI sets ``CI=true`` and exports the
DSN of its postgres service in every pytest step (.github/workflows/ci.yml), so a missing DSN there is a broken job,
not a reason to skip the money-ledger tests unseen.
"""

from __future__ import annotations

import pytest

from tests.contracts.kinds.store_postgres import pg_schema


def test_a_missing_dsn_fails_in_ci(monkeypatch):
    monkeypatch.delenv("HADAVIN_TEST_PG_DSN", raising=False)
    monkeypatch.setenv("CI", "true")
    try:
        next(pg_schema())
    except pytest.fail.Exception as failed:
        assert "HADAVIN_TEST_PG_DSN not set" in str(failed)
    except pytest.skip.Exception:
        pytest.fail("a missing DSN in CI was skipped; it must fail")
    else:
        pytest.fail("the schema helper yielded without a DSN")


def test_a_missing_dsn_skips_outside_ci(monkeypatch):
    monkeypatch.delenv("HADAVIN_TEST_PG_DSN", raising=False)
    monkeypatch.delenv("CI", raising=False)
    try:
        next(pg_schema())
    except pytest.skip.Exception as skipped:
        assert "HADAVIN_TEST_PG_DSN not set" in str(skipped)
    except pytest.fail.Exception:
        pytest.fail("a missing DSN on a developer machine must skip, not fail")
    else:
        pytest.fail("the schema helper yielded without a DSN")


def test_the_shared_helper_fails_in_ci_and_skips_elsewhere(monkeypatch):
    """The one rule both database conftests use (tests/pg_dsn.py)."""
    from tests.pg_dsn import need_dsn_or_skip

    monkeypatch.setenv("CI", "true")
    with pytest.raises(pytest.fail.Exception):
        need_dsn_or_skip("no dsn")
    monkeypatch.setenv("CI", "false")
    with pytest.raises(pytest.skip.Exception):
        need_dsn_or_skip("no dsn")
