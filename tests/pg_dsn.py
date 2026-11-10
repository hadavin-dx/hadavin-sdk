"""One rule for a missing HADAVIN_TEST_PG_DSN, shared by every database test helper (the store contract
``tests/contracts/kinds/store_postgres.py`` and ``tests/demo_askdata/conftest.py``): on a developer machine the
database tests skip; in CI (``CI=true``) they FAIL, because a silent skip there would hide every database test."""

import os

import pytest


def need_dsn_or_skip(reason: str) -> None:
    """Fail when CI=true, skip otherwise. Never returns."""
    if os.environ.get("CI") == "true":
        pytest.fail(reason, pytrace=False)
    pytest.skip(reason)
