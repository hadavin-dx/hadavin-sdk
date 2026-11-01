"""T-E9: the command line, in-process, against the test database (scripted model, no network)."""

import pytest
from askdata.cli import cmd_ask, main
from askdata.pgsource import PgError

ESC = chr(27)


@pytest.fixture
def cli(db, monkeypatch, capsys):
    monkeypatch.setenv("ASKDATA_DSN", db.ro_dsn)

    def run(*argv):
        code = main(list(argv))
        return code, capsys.readouterr().out

    return run


def test_verify_readonly_is_green(cli):
    code, out = cli("verify-readonly")
    assert (
        code == 0
        and "all checks green" in out
        and "RED" not in out
        and "Staged on synthetic data" in out
    )


def test_ask_sql_shows_canonical_sql_hash_and_table(cli):
    code, out = cli(
        "ask", "--sql", "SELECT category, count(*) FROM analytics.products_v GROUP BY 1"
    )
    assert code == 0
    assert "canonical: SELECT category, COUNT(*) FROM analytics.products_v GROUP BY 1" in out
    assert "sha256   : 610c0f4070db307684f6f81478a79617d58ef69230ec05f50b213a489c2e9f6b" in out
    assert "5 row(s)" in out


@pytest.mark.parametrize(
    ("sql", "rule"),
    [("DELETE FROM shop.orders", "V03"), ("SELECT email FROM analytics.customers_v", "V05")],
)
def test_ask_rejects_before_the_database(cli, sql, rule):
    code, out = cli("ask", "--sql", sql)
    assert code == 3 and f"rejected {rule}" in out and "nothing was sent" in out


def test_ask_question_uses_the_scripted_model_and_unknown_questions_abstain(cli):
    code, out = cli("ask", "How many orders per country?")
    assert code == 0 and "scripted (offline, no API call)" in out and "orders" in out
    code, out = cli("ask", "What is the meaning of life?")
    assert code == 7 and "abstains" in out


def test_terminal_control_plant_never_reaches_the_output(cli):
    code, out = cli("ask", "List the customers")
    assert (
        code == 0 and "Plant" in out
    )  # the planted row is shown, but without its control sequences
    assert ESC not in out and chr(7) not in out


def test_database_refusal_is_reported_as_a_sqlstate_only(cli):
    # the validator accepts this (a CTE named like nothing exposed would not), so use a view the login lacks nothing on:
    # force a runtime failure instead: division by zero in an allowed expression
    code, out = cli("ask", "--sql", "SELECT 1 / 0 FROM analytics.orders_v")
    assert code == 3 and "SQLSTATE 22012" in out


def test_demo_runs_end_to_end_offline(cli):
    code, out = cli("demo")
    assert code == 0
    assert out.count("rejected") == 2 and "all checks green" in out


def test_missing_dsn_is_a_startup_error(monkeypatch, capsys):
    monkeypatch.delenv("ASKDATA_DSN", raising=False)
    assert main(["verify-readonly"]) == 4
    assert "ASKDATA_DSN" in capsys.readouterr().out


def test_ask_refuses_to_start_when_a_read_only_check_is_red(db, monkeypatch, capsys):
    """G7: a red check means exit 4 and nothing is sent. The shared admin DSN is a superuser: every check is red."""
    monkeypatch.setenv("ASKDATA_DSN", db.admin_dsn)
    assert main(["ask", "--sql", "SELECT count(*) FROM analytics.orders_v"]) == 4
    out = capsys.readouterr().out
    assert "refusing to run" in out and "RED" in out and "canonical" not in out


class _Refuses:
    def run(self, *args, **kwargs):
        raise PgError(self.sqlstate, "OperationalError")

    def __init__(self, sqlstate):
        self.sqlstate = sqlstate


@pytest.mark.parametrize(
    ("sqlstate", "code"), [("28P01", 4), ("28000", 4), (None, 4), ("42501", 3)]
)
def test_exit_code_by_sqlstate(sqlstate, code):
    assert cmd_ask(_Refuses(sqlstate), "SELECT 1", who="t") == code
