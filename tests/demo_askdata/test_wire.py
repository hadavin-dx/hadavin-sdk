"""The wire hash: the text actually sent is `DECLARE "<cursor>" CURSOR FOR <canonical>`, hashed apart from the SQL."""

from __future__ import annotations

import re

from askdata.pgsource import PgSource


def test_a_run_reports_a_wire_hash_that_differs_from_the_sql_hash(admin_dsn):
    res = PgSource(admin_dsn).run("SELECT 1 AS one")
    assert res.rows == [(1,)]
    assert re.fullmatch(r"[0-9a-f]{64}", res.wire_sha256) and res.wire_sha256 != res.sql_sha256
