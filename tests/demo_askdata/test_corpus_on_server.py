"""T-E3b (A-06): the accepted corpus actually RUNS on the CI server (Postgres 17.10) as the read-only login.
pglast is the PG 18 grammar, so parsing alone does not prove the server accepts what the validator emits."""

import pytest
from askdata.pgsource import PgSource
from askdata.validate import validate

from tests.demo_askdata.corpus import BENIGN


@pytest.mark.parametrize(("name", "sql"), BENIGN, ids=[b[0] for b in BENIGN])
def test_benign_corpus_runs_on_the_ci_server(db, name, sql):
    canonical = validate(sql)
    result = PgSource(db.ro_dsn).run(canonical.canonical_sql, sql_sha256=canonical.sha256)
    assert result.columns and not result.truncated
