"""T-E2: the DBA script and PgSource.verify_readonly() are one implementation, green for the real login, red (exit 3)
for a deliberately over-privileged one."""

import re
import secrets
from pathlib import Path

import pytest
from askdata.allowed import VIEWS
from askdata.pgsource import PgError, PgSource
from psycopg.conninfo import make_conninfo

from tests.demo_askdata.conftest import DEMO, _need, load_script

SCRIPT = DEMO / "trust" / "verify_readonly.psql"


def _rows(stdout: str) -> list[tuple[str, str, str]]:
    return [tuple(line.split("|")) for line in stdout.splitlines() if line.count("|") == 2]  # type: ignore[misc]


def _psql_verify(db, user, password):
    return db.run_psql(user, password, "-A", "-t", "-F", "|", "-f", str(SCRIPT))


def test_wrapper_is_current():
    build = load_script("build_verify")
    assert build.main(["--check"]) == 0
    assert SCRIPT.read_text(encoding="utf-8").replace("\r\n", "\n") == build.build()


def test_checks_name_exactly_the_allowlisted_views_and_columns():
    expected = ",".join(f"{v}.{c}" for v in sorted(VIEWS) for c in sorted(VIEWS[v]))
    text = (DEMO / "db" / "verify_checks.sql").read_text(encoding="utf-8")
    block = text.split("SELECT 9,")[1].split("UNION ALL")[0]
    literals = re.findall(r"'([^']*)'", block)
    assert "".join(x for x in literals if "_v." in x) == expected
    assert "email" not in expected


def test_green_for_the_real_login(db):
    done = _psql_verify(db, db.ro_role, db.ro_password)
    assert done.returncode == 0, done.stdout + done.stderr
    rows = _rows(done.stdout)
    assert len(rows) == 16 and all(r[1] == "t" for r in rows), rows


def test_psql_rows_equal_pgsource_rows(db):
    psql_rows = _rows(_psql_verify(db, db.ro_role, db.ro_password).stdout)
    app_rows = [
        (c.check, "t" if c.ok else "f", c.detail) for c in PgSource(db.ro_dsn).verify_readonly()
    ]
    assert app_rows == psql_rows


def test_over_privileged_login_turns_the_script_red(db):
    role, pw = db.name + "_scratch", secrets.token_urlsafe(18)
    db.create_login(
        role, pw, "CREATE ON SCHEMA scratch", "INSERT ON shop.orders", "USAGE ON SCHEMA shop"
    )
    with db.admin() as c:
        c.execute(
            f'CREATE TABLE scratch.owned (x integer); ALTER TABLE scratch.owned OWNER TO "{role}"'
        )
    done = _psql_verify(db, role, pw)
    assert done.returncode == 3, done.stdout + done.stderr
    red = {r[0] for r in _rows(done.stdout) if r[1] == "f"}
    assert any("owns no object" in r for r in red)
    assert any("CREATE on any non-system schema" in r for r in red)
    assert any("write-type privilege" in r for r in red)
    assert any("schema shop" in r for r in red)
    assert "verify_readonly: RED" in done.stderr
    # the same checks through the app connection report the same red rows
    app_red = {c.check for c in PgSource(db.dsn(role, pw)).verify_readonly() if not c.ok}
    assert app_red == red


def test_connection_failure_is_a_pgerror_without_the_password(db):
    dead = make_conninfo(db.ro_dsn, port=1)  # nothing listens on port 1
    with pytest.raises(PgError) as caught:
        PgSource(dead).verify_readonly()
    assert db.ro_password not in str(caught.value) and caught.value.sqlstate is None


def test_script_files_are_ascii_and_lf():
    for path in Path(DEMO / "db").glob("*.sql"):
        data = path.read_bytes()
        assert data.isascii(), path.name


GRANTS = [
    "UPDATE (total_amount) ON analytics.orders_v",
    "INSERT (status) ON analytics.orders_v",
    "SELECT (customer_id) ON shop.customers",
    "UPDATE ON SEQUENCE scratch.sq",
    "EXECUTE ON FUNCTION scratch.fn()",
    "EXECUTE ON FUNCTION pg_read_file(text)",
    "EXECUTE ON FUNCTION pg_ls_dir(text)",
    "EXECUTE ON FUNCTION lo_import(text)",
    "EXECUTE ON FUNCTION lo_export(oid, text)",
]


@pytest.mark.parametrize("grant", GRANTS)
def test_column_sequence_and_function_grants_turn_the_script_red(db, grant):
    role, pw = db.name + "_g" + secrets.token_hex(3), secrets.token_urlsafe(18)
    with db.admin() as c:
        c.execute("CREATE SEQUENCE IF NOT EXISTS scratch.sq")
        c.execute("CREATE OR REPLACE FUNCTION scratch.fn() RETURNS int LANGUAGE sql AS 'SELECT 1'")
    dsn = db.create_login(
        role, pw, "USAGE ON SCHEMA scratch", "USAGE ON SCHEMA analytics", "USAGE ON SCHEMA shop"
    )
    with db.admin() as c:
        c.execute("REVOKE EXECUTE ON FUNCTION scratch.fn() FROM PUBLIC")
        c.execute(f'GRANT {grant} TO "{role}"')
    red = [r.check for r in PgSource(dsn).verify_readonly() if not r.ok]
    assert red, grant
    done = _psql_verify(db, role, pw)
    assert done.returncode == 3, grant


def test_file_and_network_extension_turns_the_script_red(make_db):
    env = make_db()  # its own database: the extension must not leak into the shared one
    with env.admin() as c:
        if not c.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'dblink'").fetchone():
            _need("the dblink extension is not available on this server")
        c.execute("CREATE EXTENSION dblink")
    red = [r.check for r in PgSource(env.ro_dsn).verify_readonly() if not r.ok]
    assert any("extensions installed" in r for r in red), red


def test_default_transaction_read_only_is_informational_only(db):
    rows = {c.check: c for c in PgSource(db.ro_dsn).verify_readonly()}
    info = [c for k, c in rows.items() if "default_transaction_read_only" in k]
    assert len(info) == 1 and info[0].ok and info[0].check.startswith("INFO")
