"""F-money-definer step 6, the operator commands `limits set-cap`, `limits sync-caps` and `limits check-caps`, end to
end through `cli.main` against a real PostgreSQL 16: a throwaway schema and real non-superuser logins with unique
names, dropped after. The commands run under the reset login only, intent first, audited per agent.

Exit codes: 0 done; 1 (`check-caps` only) a cap differs or a row is missing; 2 refused (config, missing reset
ref, bad argument, no `--yes` when not interactive, the login lacks the right); 3 the audit store is unavailable
(nothing changed); 4 the store is unreachable. Needs HADAVIN_TEST_PG_DSN; skipped without it."""

from __future__ import annotations

import json
import os
from decimal import Decimal

import pytest
import yaml

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql

from hadavin_sdk import cli
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.audit import AuditUnavailable
from hadavin_sdk.store.postgres import PostgresStore
from tests.conftest import make_cfg
from tests.test_stop_state_roles import SETTINGS, World

D = Decimal
pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)
REF = "reset-dsn"  # a secret NAME
EXTRA = [  # the fixture config has one live agent, test-agent (1.00 / 10.00)
    ("agent-two", "live", "2.00", "20.00"),
    ("agent-draft", "draft", "3.00", "30.00"),
    ("agent-old", "retired", "4.00", "40.00"),
]
SYNCED = {"agent-draft", "agent-two", "test-agent"}  # live and draft; never the retired one
BY = "user:op"


@pytest.fixture(name="w")
def caps_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        world.migrate()
        yield world
    finally:
        for s in world.stores:
            s._db.close()
        with psycopg.connect(world.dsn, autocommit=True) as db:
            for schema in world.schemas:
                db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            for r in world.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def _edit(cfg, name, fn):
    path = cfg / name
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _config(tmp_path, ref=REF, store=None, agents=EXTRA):
    cfg = make_cfg(tmp_path)

    def conf(d):
        d["backends"]["store"] = (
            dict(SETTINGS) | ({"caps_credential_ref": ref} if ref else {}) | (store or {})
        )
        d["backends"]["audit"] = {"kind": "chain"}

    def reg(rows):
        base = rows[0]
        for agent_id, status, daily, monthly in agents:
            rows.append(
                base
                | {
                    "id": agent_id,
                    "status": status,
                    "budget_usd": {"daily": daily, "monthly": monthly},
                }
            )

    _edit(cfg, "config.yaml", conf)
    _edit(cfg, "agents.yaml", reg)
    return cfg


class Spy:
    """Every capability the CLI builds, in order; the secrets kind answers from `held`."""

    def __init__(self, w, monkeypatch, held):
        self.made, self.held, self.w = [], held, w
        real = cli.make

        def fake(capability, settings, *a, **k):
            self.made.append(capability)
            if capability == "secrets":
                return FakeSecretProvider(dict(self.held))
            made = real(capability, settings, *a, **k)
            if capability == "store":
                w.stores.append(made)
            return made

        monkeypatch.setattr(cli, "make", fake)

    @property
    def connected(self):
        return "store" in self.made


@pytest.fixture(name="spy")
def spy_fixture(w, monkeypatch):
    return Spy(w, monkeypatch, {"pg-dsn": w.dsn_of(w.runtime), REF: w.dsn_of(w.caps)})


def _run(cfg, *args):
    return cli.main(["--config", str(cfg), "limits", *args])


def _sync(cfg, *extra):
    return _run(cfg, "sync-caps", "--by", BY, *extra)


def _table(w):
    return {
        a: (d, m, by)
        for a, d, m, by in w.run(
            "SELECT agent_id, day_cap, month_cap, set_by FROM hadavin_caps ORDER BY agent_id"
        )
    }


def _audit(w):
    out = []
    for kind, body in w.run("SELECT kind, body FROM audit_entries ORDER BY seq"):
        if kind == "limits.set_cap":
            event = json.loads(body)
            out.append((event["object_ref"], event["result"].split()[0]))
    return out


# ---- refusals before any connection (B3, T12) ----------------------------------------------------------------------

ARGS = {
    "set-cap": ("set-cap", "agent-two", "--day", "5", "--month", "50", "--by", BY, "--yes"),
    "sync-caps": ("sync-caps", "--by", BY, "--yes"),
    "check-caps": ("check-caps",),
}


@pytest.mark.parametrize("command", ARGS)
def test_a_missing_reset_ref_is_refused_before_any_connection_in_every_environment(
    w, tmp_path, spy, capsys, command
):
    cfg = _config(tmp_path, ref=None)  # environment: demo
    assert _run(cfg, *ARGS[command]) == 2
    err = capsys.readouterr().err
    assert "caps_credential_ref" in err and "migrate --caps-role" in err
    assert not spy.connected and _table(w) == {}


@pytest.mark.parametrize("command", ARGS)
@pytest.mark.parametrize(
    "case",
    [
        "same name",
        "same value",
        "path form",
        "purge name",
        "purge value",
        "release name",
        "reset name",
        "reset value",
    ],
)
def test_a_caps_ref_that_collides_with_another_secret_or_login_is_refused(
    w, tmp_path, spy, capsys, command, case
):
    store = {}
    if case == "same name":
        store = {"caps_credential_ref": "pg-dsn"}
    elif case == "path form":
        store = {"caps_credential_ref": "a/../reset"}
    elif case == "purge name":
        store = {"purge_dsn_secret_name": REF}
    elif case == "purge value":
        store = {"purge_dsn_secret_name": "pg-purge"}
        spy.held["pg-purge"] = w.dsn_of(w.caps)
    elif case == "release name":
        store = {"release_credential_ref": REF}
    elif case == "reset name":
        store = {"reset_credential_ref": REF}
    elif case == "reset value":
        store = {"reset_credential_ref": "pg-reset"}
        spy.held["pg-reset"] = w.dsn_of(w.caps)
    elif case == "same value":
        spy.held[REF] = w.dsn_of(w.runtime)  # two names, one login
    cfg = _config(tmp_path, store=store)
    assert _run(cfg, *ARGS[command]) == 2
    err = capsys.readouterr().err
    assert "caps_credential_ref" in err and "Traceback" not in err
    # a name clash is refused by NAME, before any secret is read; two names with one DSN by VALUE
    want = {"path form": "path-shaped"}.get(
        case, "same login" if case.endswith("value") else "same secret"
    )
    assert want in err
    assert "postgresql://" not in err and w.runtime not in err  # no value in a message
    assert "store" not in spy.made and _table(w) == {}


@pytest.mark.parametrize("command", ["set-cap", "sync-caps", "check-caps"])
def test_the_memory_store_is_refused_it_has_no_cap_table(tmp_path, capsys, command):
    cfg = make_cfg(tmp_path)  # backends.store: memory
    assert _run(cfg, *ARGS[command]) == 2
    assert "no cap table" in capsys.readouterr().err


def test_without_yes_a_non_interactive_run_is_refused_and_writes_nothing(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    assert _run(cfg, "sync-caps", "--by", BY) == 2
    assert "--yes" in capsys.readouterr().err
    assert _run(cfg, "set-cap", "agent-two", "--day", "5", "--month", "50", "--by", BY) == 2
    assert not spy.connected and _table(w) == {}


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-1", "abc", "1E+10", "0.0000000000001"])
def test_a_bad_cap_argument_is_refused(w, tmp_path, spy, capsys, bad):
    cfg = _config(tmp_path)
    with pytest.raises(SystemExit) as e:  # argparse refuses it: exit 2, before any connection
        _run(cfg, "set-cap", "agent-two", "--day", bad, "--month", "50", "--by", BY, "--yes")
    assert e.value.code == 2 and _table(w) == {} and not spy.connected


def test_set_cap_refuses_an_unknown_and_a_retired_agent(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    for agent in ("nobody", "agent-old"):
        assert _run(cfg, "set-cap", agent, "--day", "5", "--month", "50", "--by", BY, "--yes") == 2
    assert _table(w) == {} and not spy.connected


# ---- sync-caps ---------------------------------------------------------------------------------------------------------


def test_sync_writes_the_registry_caps_as_the_reset_login_audited_intent_then_outcome(
    w, tmp_path, spy, capsys
):
    cfg = _config(tmp_path)
    assert _sync(cfg, "--yes") == 0
    table = _table(w)
    assert set(table) == SYNCED  # the retired agent is not synced
    assert table["test-agent"] == (D("1.00"), D("10.00"), BY)
    assert table["agent-two"] == (D("2.00"), D("20.00"), BY)
    assert table["agent-draft"] == (D("3.00"), D("30.00"), BY)
    audit = _audit(w)
    assert len(audit) == 6
    for agent in SYNCED:  # per agent: the intent row, then its outcome row
        assert [r for a, r in audit if a == agent] == ["intent", "set"]
    for i in (0, 2, 4):  # one agent at a time: the intent and its outcome sit next to each other
        assert audit[i][1] == "intent" and audit[i + 1] == (audit[i][0], "set")
    assert "agent-old" not in capsys.readouterr().out  # a retired agent is not named


def test_the_diff_is_printed_before_anything_is_written(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    assert _sync(cfg, "--yes") == 0
    out = capsys.readouterr().out
    assert all(a in out for a in SYNCED) and "missing" in out


def test_a_rerun_is_idempotent_it_writes_and_audits_nothing(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    assert _sync(cfg, "--yes") == 0
    before = (
        _table(w),
        w.run("SELECT agent_id, set_at FROM hadavin_caps ORDER BY agent_id"),
        len(_audit(w)),
    )
    capsys.readouterr()
    assert _sync(cfg, "--yes") == 0
    after = (
        _table(w),
        w.run("SELECT agent_id, set_at FROM hadavin_caps ORDER BY agent_id"),
        len(_audit(w)),
    )
    assert before == after
    assert "nothing to change" in capsys.readouterr().out


def test_a_changed_registry_cap_is_the_only_row_a_later_sync_writes(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    assert _sync(cfg, "--yes") == 0
    n = len(_audit(w))
    _edit(
        cfg,
        "agents.yaml",
        lambda rows: rows[1].update(budget_usd={"daily": "2.50", "monthly": "20.00"}),
    )
    assert _sync(cfg, "--yes") == 0
    assert _table(w)["agent-two"][:2] == (D("2.50"), D("20.00"))
    assert len(_audit(w)) == n + 2  # one intent, one outcome, for the one agent that differed


def test_sync_stops_at_the_first_failure_and_a_rerun_completes(
    w, tmp_path, spy, capsys, monkeypatch
):
    cfg = _config(tmp_path)
    real, calls = PostgresStore.set_cap, []

    def flaky(self, agent_id, day_cap, month_cap, by):
        calls.append(agent_id)
        if len(calls) == 2:
            raise RuntimeError("boom")
        return real(self, agent_id, day_cap, month_cap, by)

    monkeypatch.setattr(PostgresStore, "set_cap", flaky)
    assert _sync(cfg, "--yes") == 2
    assert len(calls) == 2  # the third agent was never tried
    assert set(_table(w)) == {calls[0]}
    audit = _audit(w)
    assert [r for a, r in audit if a == calls[0]] == ["intent", "set"]
    assert [r for a, r in audit if a == calls[1]] == ["intent", "set_cap_failed"]
    assert len(audit) == 4  # nothing for the third agent
    err = capsys.readouterr().err
    assert "boom" not in err  # the class name only
    monkeypatch.setattr(PostgresStore, "set_cap", real)
    assert _sync(cfg, "--yes") == 0
    assert set(_table(w)) == SYNCED


def test_an_audit_outage_is_exit_3_and_nothing_changed(w, tmp_path, spy, capsys, monkeypatch):
    cfg = _config(tmp_path)
    inner = cli.make  # the spy: secrets from `held`, real stores

    def down(capability, settings, *a, **k):
        made = inner(capability, settings, *a, **k)
        if capability == "audit":

            def refuse(event):
                raise AuditUnavailable("down")

            made.write_intent = refuse
        return made

    monkeypatch.setattr(cli, "make", down)
    assert _sync(cfg, "--yes") == 3
    assert _table(w) == {} and _audit(w) == []
    assert "audit" in capsys.readouterr().err
    assert _run(cfg, *ARGS["set-cap"]) == 3 and _table(w) == {}


def test_an_unreachable_store_is_exit_4(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    spy.held[REF] = "postgresql://nobody@127.0.0.1:1/none"  # nothing listens on port 1
    assert _sync(cfg, "--yes") == 4
    assert "unreachable" in capsys.readouterr().err


def test_a_login_without_the_right_is_exit_2_nothing_changed(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    spy.held[REF] = w.dsn_of(w.portal)  # not the reset login
    assert _sync(cfg, "--yes") in (2, 3)
    assert _table(w) == {}


def test_a_caps_login_that_can_clear_a_stop_is_refused_at_start_and_nothing_changes(
    w, tmp_path, spy, capsys
):
    """The caps login is held to the same own-rights check as the runtime login (it holds nothing on the stop
    tables): a hand grant of UPDATE on the kill switch refuses the command before any cap is written."""
    cfg = _config(tmp_path)
    w.grant("GRANT UPDATE ON kill_switch TO {}", w.caps)
    assert _sync(cfg, "--yes") == 2
    err = capsys.readouterr().err
    assert "rights on the stop tables" in err and "UPDATE on kill_switch" in err
    assert _table(w) == {}


# ---- set-cap ---------------------------------------------------------------------------------------------------------------


def test_set_cap_writes_one_agent_audited(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    assert _run(cfg, *ARGS["set-cap"]) == 0
    assert _table(w) == {"agent-two": (D("5"), D("50"), BY)}
    audit = _audit(w)
    assert [a for a, _ in audit] == ["agent-two", "agent-two"] and audit[0][1] == "intent"
    assert "registry" in capsys.readouterr().out  # it says the registry still holds other values


def test_set_cap_twice_with_the_same_values_changes_nothing_more(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    assert _run(cfg, *ARGS["set-cap"]) == 0
    assert _run(cfg, *ARGS["set-cap"]) == 0
    assert _table(w) == {"agent-two": (D("5"), D("50"), BY)}


# ---- check-caps ------------------------------------------------------------------------------------------------------------


def test_check_caps_is_0_when_equal_and_not_for_drift_or_a_missing_row(w, tmp_path, spy, capsys):
    cfg = _config(tmp_path)
    assert _run(cfg, "check-caps") == 1  # nothing synced: every row is missing
    assert "missing" in capsys.readouterr().out
    assert _sync(cfg, "--yes") == 0
    capsys.readouterr()
    assert _run(cfg, "check-caps") == 0  # the retired agent has no row and is not reported
    out = capsys.readouterr().out
    assert "agent-old" not in out and "same" in out
    _edit(
        cfg,
        "agents.yaml",
        lambda rows: rows[1].update(budget_usd={"daily": "0.50", "monthly": "20.00"}),
    )
    assert _run(cfg, "check-caps") == 1  # a lowered registry cap, the table is still high
    out = capsys.readouterr().out
    assert "agent-two" in out and "differs" in out and "0.50" not in out
    _edit(
        cfg,
        "agents.yaml",
        lambda rows: rows[1].update(budget_usd={"daily": "2.00", "monthly": "20.00"}),
    )
    assert _run(cfg, "check-caps") == 0
    w.run("DELETE FROM hadavin_caps WHERE agent_id = %s RETURNING 1", ("agent-draft",))
    assert _run(cfg, "check-caps") == 1
    assert "agent-draft" in capsys.readouterr().out


def test_check_caps_writes_no_audit_line(w, tmp_path, spy):
    cfg = _config(tmp_path)
    _run(cfg, "check-caps")
    assert _audit(w) == [] and "audit" not in spy.made


def test_the_existing_stop_and_reset_actions_still_parse():
    for action in ("stop", "reset"):
        with pytest.raises(SystemExit) as e:  # parsed, then refused: no config folder
            cli.main(["--config", "/nonexistent-folder", "limits", action])
        assert e.value.code == 2  # `--by` is still required
