"""0010 guard, owner first: the owner of the release function returns NEW before the aggregate over the holds is
computed (the per-row cost is one pg_proc lookup); every other login still reaches the aggregate and the refusal."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import pytest

SQL = (
    Path(__file__).resolve().parent.parent / "src/hadavin_sdk/store/migrations/0010_money_guard.sql"
).read_text()
BODY = SQL[SQL.index("AS $fn$") :]


def test_the_owner_check_comes_before_the_aggregate():
    owner = BODY.index("pg_get_userbyid")
    check = BODY.index("IF release_owner IS NULL OR current_user::name IS DISTINCT FROM release_owner THEN")
    aggregate = BODY.index("FROM spend_reservations r")
    assert owner < check < aggregate  # the aggregates sit inside the non-owner branch
    assert BODY.rstrip().endswith("RETURN NEW;\nEND\n$fn$;".rstrip()) or "RETURN NEW;\nEND" in BODY


def test_the_refusal_is_inside_the_non_owner_branch():
    assert BODY.index("RAISE EXCEPTION") > BODY.index("FROM spend_reservations r")


pg = pytest.mark.skipif(not os.environ.get("HADAVIN_TEST_PG_DSN"), reason="HADAVIN_TEST_PG_DSN not set")

if os.environ.get("HADAVIN_TEST_PG_DSN"):
    pytest.importorskip("psycopg")
    from psycopg import errors

    from tests.test_money_guard_pg import AGENT, D, seed
    from tests.test_release_expired_spend_pg import (
        _counters,
        _release,
        release_world,  # noqa: F401 - the fixture
    )

    @pg
    def test_owner_login_lowers_and_a_non_owner_is_still_refused(w):
        seed(w)
        with w.as_(w.runtime) as db, pytest.raises(errors.InsufficientPrivilege):
            db.execute("UPDATE spend SET usd = 0 WHERE agent_id = %s", (AGENT,))
        before = _counters(w)
        _release(w)  # the definer body runs as the owner: returns at the owner check
        assert _counters(w) == before  # nothing expired: no change, no refusal
        assert isinstance(before[0], Decimal) and D(0) <= before[0]
