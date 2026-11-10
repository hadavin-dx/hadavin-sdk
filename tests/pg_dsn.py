"""One rule for a missing HADAVIN_TEST_PG_DSN, shared by two helpers: the store contract
``tests/contracts/kinds/store_postgres.py`` and ``tests/demo_askdata/conftest.py``. On a developer machine their
database tests skip; in CI (``CI=true``) they FAIL, because a silent skip there would hide those tests. Other test
files that read the variable keep their own skip."""

import os
from typing import NoReturn

import pytest


def need_dsn_or_skip(reason: str) -> NoReturn:
    """Fail when CI=true, skip otherwise. Never returns."""
    if os.environ.get("CI") == "true":
        pytest.fail(reason, pytrace=False)
    pytest.skip(reason)
