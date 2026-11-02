# ruff: noqa: S608  - table names in these statements come from a fixed parametrize list
"""K6 round 4 (PR #41 result review 1): the false-abstain report, bounded and strict numbers, one bucketing rule,
the csv import that must not overwrite a newer label, append-only triggers on a real postgres, the guarded caught
view, and the migration number. Hostile inputs first."""

from __future__ import annotations

from pathlib import Path

import pytest

from hadavin_sdk import measure
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import RunState
from hadavin_sdk.store.migrate import MIGRATIONS, check_ledger
from tests.test_k6_measure import ACTION, NOW, WEEK, World, day

S = RunState


@pytest.fixture
def w(tmp_path):
    return World(tmp_path)


# --- M2: strict ASCII digits, bounded numbers -------------------------------------------------------------

HOSTILE_SEQ = [
    "\u0663",  # Arabic-Indic three: int() reads it as 3, a second spelling of the same seq
    "\u00b2",  # superscript two: isdigit() true, int() raises
    "\uff13",  # full-width three
    "+3",
    "-3",
    "3_0",
    " 3",
    "3 ",
    "",
    "9" * 19,
    "9" * 5000,
]


@pytest.mark.parametrize("seq", HOSTILE_SEQ)
def test_k6_clear_value_with_a_loose_seq_does_not_parse(seq):
    assert measure.parse_action_value(f"clear|test-agent|{ACTION}|{seq}") is None


def test_k6_clear_value_with_a_plain_seq_parses():
    got = measure.parse_action_value(f"clear|test-agent|{ACTION}|{'9' * 18}")
    assert got is not None and got.args[2] == "9" * 18


@pytest.mark.parametrize("seq", HOSTILE_SEQ)
def test_k6_a_signed_click_with_a_loose_seq_is_200_malformed_never_503(w, seq):
    status, _ = w.click("owner", f"clear|test-agent|{ACTION}|{seq}")
    assert status == 200


def test_k6_a_client_side_value_error_is_a_4xx_and_the_claim_stays_spent(w):
    """A request that cannot be acted on must not be retryable for the whole signature window."""
    rid = w.run()

    def boom(*a, **k):
        raise ValueError("bad value")

    w.measure.record_label = boom
    body = f"label|{rid}|agree"
    assert w.click("u1", body)[0] == 400
    assert w.click("u1", body)[0] == 200  # the same signed request: replay, refused, not re-run
    assert w.store.list_labels(rid) == []


def test_k6_a_server_side_error_still_releases_the_claim(w):
    rid = w.run()
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise RuntimeError("down")

    real = w.measure.record_label
    w.measure.record_label = boom
    assert w.click("u1", f"label|{rid}|agree")[0] == 503
    w.measure.record_label = real
    assert w.click("u1", f"label|{rid}|agree")[0] == 200  # not a replay: the claim was given back
    assert len(w.store.list_labels(rid)) == 1 and calls


def _baseline(tmp_path: Path, **ceil: str) -> None:
    fields = {
        "metric": "m",
        "max": "1",
        "window_days": "30",
        "source": "s",
    } | ceil
    lines = "\n".join(f"  {k}: {v}" for k, v in fields.items())
    (tmp_path / "baseline.yaml").write_text(
        f"ceiling:\n{lines}\n  counts: [harmful]\n", encoding="utf-8"
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("window_days", "99999999999999999999"),  # timedelta(days=...) would overflow later
        ("window_days", "3651"),
        ("window_days", "0"),
        ("window_days", '"\u0663"'),
        ("window_days", '"1_0"'),
        ("window_days", '"+5"'),
        ("max", "99999999999999999999"),
        ("max", "1000001"),
        ("max", '"\u00b2"'),
        ("max", "-1"),
    ],
)
def test_k6_ceiling_numbers_are_bounded_and_ascii(tmp_path, key, value):
    _baseline(tmp_path, **{key: value})
    with pytest.raises(ConfigError):
        measure.load_baseline(tmp_path)


def test_k6_ceiling_numbers_at_the_bounds_load(tmp_path):
    _baseline(tmp_path, max="1000000", window_days="3650")
    c = measure.load_baseline(tmp_path)
    assert (c.max, c.window_days) == (10**6, 3650)


def test_k6_every_digit_pattern_in_measure_is_ascii_only():
    """Class guard: no `.isdigit()` or bare `int(` on text from outside in the measurement module."""
    text = Path(measure.__file__).read_text(encoding="utf-8")
    assert ".isdigit()" not in text
    assert "\\d" not in text  # a regex \d matches non-ASCII digits too


# --- M1: the false-abstain rate and the abstention label coverage -----------------------------------------


def test_k6_report_false_abstain_uses_the_answerable_denominator_and_states_coverage(w):
    w.labelled("agree", 4, when=day(7))
    w.labelled("wrong", 1, when=day(7))
    for name in ("abstain_ok", "missed", "missed"):
        rid = w.run(plan=False, state=S.NEEDS_PERSON, reason="tool_error", created=day(7))
        assert w.label(rid, name, when=day(7)).ok
    for _ in range(3):  # abstained and never labelled
        w.run(plan=False, state=S.NEEDS_PERSON, reason="ungrounded", created=day(7))
    text = w.measure.render_report(WEEK, NOW)
    fa = next(ln for ln in text.splitlines() if ln.startswith("- False-abstain rate"))
    ok = next(ln for ln in text.splitlines() if ln.startswith("- Correct abstentions"))
    # answerable = 5 labelled proposals + 2 missed = 7; NOT missed / (missed + abstain_ok) = 2 of 3
    assert "2 of 7 (29%)" in fa and "95% upper bound" in fa and "n = 7" in fa
    assert "1 of 3 labelled abstentions" in ok and "coverage 3 of 6 abstained runs" in ok
    assert "Miss rate" not in text


def test_k6_report_false_abstain_with_nothing_answerable_says_so(w):
    text = w.measure.render_report(WEEK, NOW)
    assert "False-abstain rate" in text and "n/a (nothing labelled)" in text


# --- M4: the mapping line and ONE bucketing rule -----------------------------------------------------------


def test_k6_report_has_the_mapping_to_the_scorecard(w):
    text = w.measure.render_report(WEEK, NOW)
    assert "right = agree + partial" in text and "agree rate counts agree only" in text
    assert "'Cumulative' = the per-action lines" in text


def test_k6_counts_and_the_wrong_list_use_the_run_week(w):
    """A run belongs to the week it was created in; its latest label counts there, whenever it was given."""
    late = w.run(created=day(7))  # a run of the report week, labelled a week after it ended
    assert w.label(late, "wrong", when=day(1)).ok
    early = w.run(created=day(14))  # a run of the week before, labelled inside the report week
    assert w.label(early, "wrong", when=day(7)).ok
    pw = w.store.pilot_week(WEEK)
    text = w.measure.render_report(WEEK, NOW)
    listed = text.split("## Every wrong and harmful label on this week's runs")[1].split("##")[0]
    assert pw.wrong == 1  # the count (view or memory store) is by run week ...
    assert late in listed and early not in listed  # ... and so is the list
    assert listed.count("- run-") == pw.wrong


def test_k6_the_wrong_list_takes_the_latest_label_of_the_run(w):
    rid = w.run(created=day(7))
    assert w.label(rid, "wrong", when=day(7)).ok
    assert w.label(rid, "agree", when=day(1)).ok  # corrected after the week ended
    listed = w.measure.render_report(WEEK, NOW).split("on this week's runs")[1].split("##")[0]
    assert rid not in listed and w.store.pilot_week(WEEK).wrong == 0


# --- m1: a csv import must not silently overwrite a newer label -------------------------------------------


def _import(w, rows, by="fake:u1"):
    text = "run_id,label\n" + "".join(f"{r},{lab}\n" for r, lab in rows)
    stored, problems = w.measure.import_csv(text, by)
    assert (stored, problems) == (len(rows), [])
    import_id = measure.csv_import_id(text)
    return import_id


def test_k6_approve_import_refuses_a_row_that_would_overwrite_a_newer_chat_label(w):
    rid = w.run()
    import_id = _import(w, [(rid, "agree")])
    assert w.label(rid, "wrong").ok  # chat verdict AFTER the csv row was written
    status, reason = w.measure.approve_import("fake:owner", import_id)
    assert status == 200 and "newer_label_exists" in reason
    assert w.store.list_labels(rid)[-1].label == "wrong"
    assert (
        len(w.store.list_labels(rid)) == 2
    )  # the pending row and the chat label; nothing approved


def test_k6_approve_import_accepts_a_row_that_agrees_with_the_latest_label(w):
    rid = w.run()
    import_id = _import(w, [(rid, "agree")])
    assert w.label(rid, "agree", who="u2").ok
    status, reason = w.measure.approve_import("fake:owner", import_id)
    assert status == 200 and "newer_label_exists" not in reason


# --- migration number ---------------------------------------------------------------------------------------


def test_k6_migration_number_documented():
    """The changelog names the measure migration; a rename at rebase must update both."""
    names = [p.name for p in MIGRATIONS.glob("*_measure.sql")]
    assert len(names) == 1
    changelog = (Path(measure.__file__).parents[2] / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"`{names[0]}`" in changelog
    assert check_ledger(sorted(MIGRATIONS.glob("*.sql"))) == []


def test_k6_a_second_file_with_the_same_number_is_caught(tmp_path):
    for p in MIGRATIONS.glob("*.sql"):
        (tmp_path / p.name).write_text("-- x", encoding="utf-8")
    number = next(MIGRATIONS.glob("*_measure.sql")).name[:4]
    (tmp_path / f"{number}_reservations.sql").write_text("-- x", encoding="utf-8")
    assert f"two migrations are numbered {number}" in check_ledger(sorted(tmp_path.glob("*.sql")))


# --- M3: append-only triggers, the guarded view (real postgres) ---------------------------------------------


@pytest.fixture
def owner_db():
    pytest.importorskip("psycopg")
    import psycopg

    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema():
        with psycopg.connect(dsn, autocommit=True) as db:
            yield db


@pytest.mark.parametrize("table", ["labels", "level_events", "reports"])
def test_k6_the_table_owner_cannot_update_delete_or_truncate(owner_db, table):
    import psycopg

    rows = {
        "labels": "INSERT INTO labels (label_id, run_id, label, principal_id, channel, created_at) "
        "VALUES ('l1', 'r1', 'agree', 'p', 'chat', now())",
        "level_events": 'INSERT INTO level_events (agent_id, action_id, kind, reason, "by", at) '
        "VALUES ('a', 'x', 'demote', 'r', 'p', now())",
        "reports": "INSERT INTO reports (week_start, body_md, created_at) VALUES ('2026-10-26', 'b', now())",
    }
    owner_db.execute(rows[table])
    col = {"labels": "label_id", "level_events": "agent_id", "reports": "body_md"}[table]
    for stmt in (f"UPDATE {table} SET {col} = {col}", f"DELETE FROM {table}", f"TRUNCATE {table}"):
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            owner_db.execute(stmt)
    assert owner_db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 1


def test_k6_the_runtime_role_is_denied_update_and_delete_on_the_append_only_tables():
    import psycopg

    pytest.importorskip("psycopg")
    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema(runtime=True):
        with psycopg.connect(dsn, autocommit=True) as db:
            db.execute(
                "INSERT INTO labels (label_id, run_id, label, principal_id, channel, created_at) "
                "VALUES ('l1', 'r1', 'agree', 'p', 'chat', now())"
            )
            for stmt in (
                "UPDATE labels SET label = 'wrong'",
                "DELETE FROM labels",
                "UPDATE reports SET body_md = 'x'",
                "DELETE FROM level_events",
            ):
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    db.execute(stmt)


def test_k6_a_non_json_audit_body_does_not_break_the_caught_view(owner_db):
    for i, body in enumerate(["not json", "[1, 2]", '"caught_by"', '{"caught_by": "gate"}']):
        owner_db.execute(
            "INSERT INTO audit_entries (seq, at, run_id, kind, body, prev, hash, event_id) "
            "VALUES (%s, '2026-10-27T10:00:00+00:00', %s, 'k', %s, 'p', 'h', %s)",
            (i + 1, f"r{i}", body, f"e{i}"),
        )
    rows = owner_db.execute("SELECT caught_by, n FROM v_caught_week").fetchall()
    assert rows == [("gate", 1)]
