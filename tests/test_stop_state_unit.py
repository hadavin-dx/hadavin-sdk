"""Step B, the stop state: the cases of the ticket that need no database (U1, U2, U4, F2), the `migrate` warning
when a runtime role is named without a reset role, and the exit codes of `limits reset` when the store cannot be
reached or cannot be read back.

Written by a different agent than the builder, from the ticket (handover/core-b/tickets/B-stop-state.md, S7, S9 and
B-2), with hand-made stand-ins for the store and the audit: they record calls and raise what the case names."""

from __future__ import annotations

import pytest
import yaml

from hadavin_sdk import cli
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.audit.protocol import AuditUnavailable
from hadavin_sdk.config import ConfigError
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.store import migrate as migrate_mod
from hadavin_sdk.store.migrate import GRANTS, check_grants, check_ledger
from hadavin_sdk.store.protocol import StoreUnavailable

DSN_NAME = "pg-dsn"  # the NAME of a secret (config), never a value
RESET_REF = "reset-dsn"


class Audit:
    def __init__(self, intent_down=False):
        self.rows, self.intent_down = [], intent_down

    def write_intent(self, event):
        if self.intent_down:
            raise AuditUnavailable("audit store down")
        self.rows.append(("intent", f"{event.domain}.{event.operation}", event.result))

    def write_outcome(self, event):
        self.rows.append(("outcome", f"{event.domain}.{event.operation}", event.result))

    def kinds(self):
        return [kind for _, kind, _ in self.rows]


class StoreStub:
    """`set_error` is raised by a reset, `read` is returned (or raised) by the read-back."""

    def __init__(self, set_error=None, read=None):
        self.set_error, self.read, self.sets, self.reads = set_error, read, [], 0

    def set_kill_switch(self, ks):
        self.sets.append(ks)
        if self.set_error is not None and not ks.on:
            raise self.set_error

    def open_stops(self):  # E6: a reset reads the open stops first, then clears exactly those ids
        return []

    def clear_stops(self, by, stop_ids):
        self.set_kill_switch(KillSwitch(on=False, by=by))

    def get_kill_switch(self):
        self.reads += 1
        if isinstance(self.read, BaseException):
            raise self.read
        return self.read if self.read is not None else KillSwitch(on=False)


def _limits(store, audit=None):
    audit = audit or Audit()
    return Limits(store, audit, None), audit


# ---- U1, U2 ----------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "error", [PermissionError("refused"), ConfigError("kill_switch row missing"), KeyError("x")]
)
def test_u1_a_reset_the_store_refuses_leaves_reset_then_reset_failed_and_the_error_leaves(error):
    store = StoreStub(set_error=error)
    limits, audit = _limits(store)
    with pytest.raises(type(error)) as caught:
        limits.reset("user:op")
    assert caught.value is error
    assert audit.rows == [
        ("intent", "limits.reset", "off"),
        ("outcome", "limits.reset_failed", "on"),
    ]
    assert [(ks.on, ks.by) for ks in store.sets] == [(False, "user:op")]


def test_u1_a_reset_that_works_writes_no_reset_failed():
    store = StoreStub()
    limits, audit = _limits(store)
    limits.reset("user:op")
    assert audit.kinds() == ["limits.reset"]
    assert [(ks.on, ks.by) for ks in store.sets] == [(False, "user:op")]


def test_u2_an_intent_that_cannot_be_written_means_the_store_is_never_asked_to_clear():
    store = StoreStub()
    limits, audit = _limits(store, Audit(intent_down=True))
    with pytest.raises(AuditUnavailable):
        limits.reset("user:op")
    assert store.sets == [] and audit.rows == []
    assert cli.kill_switch(limits, "reset", "user:op") == 3
    assert store.sets == [] and store.reads == 0


def test_a_stop_switches_first_and_is_audited_after():
    store = StoreStub()
    limits, audit = _limits(store)
    limits.stop("user:op")
    assert [(ks.on, ks.by) for ks in store.sets] == [(True, "user:op")]
    assert audit.rows == [("outcome", "limits.stop", "on")]


# ---- U4, F2: the grant map -------------------------------------------------------------------------------------------

RESET_ROWS = {
    "kill_switch": "SELECT, UPDATE",
    "kill_switch_stops": "SELECT",
    "kill_switch_clears": "SELECT, INSERT",
    "audit_entries": "SELECT, INSERT",
    "audit_checkpoints": "SELECT",
    "kill_switch_resets": "SELECT, INSERT",  # 0009: the reset's own append-only record
}


def _privileges(text):
    return {p.strip() for p in text.split(",") if p.strip()}


def test_u4_the_real_migrations_and_the_grant_map_agree():
    files = migrate_mod._migration_files()
    assert check_ledger(files) == []
    assert check_grants(files) == []
    assert files[-1].name == "0006_stop_state.sql" or "0006_stop_state.sql" in [
        f.name for f in files
    ]


def test_u4_only_the_seven_rows_of_the_ticket_give_the_reset_role_anything():
    held = {name: _privileges(g.reset) for name, g in GRANTS.items() if g.reset}
    assert held == {name: _privileges(text) for name, text in RESET_ROWS.items()}
    assert all(g.reset == "" for g in GRANTS.values() if g.kind == "sequence")
    assert not [n for n in GRANTS if n.startswith("kill_switch") and GRANTS[n].kind == "sequence"]


def test_f2_the_runtime_role_holds_no_right_that_turns_the_switch_off():
    assert GRANTS["kill_switch"].runtime == "SELECT"
    assert GRANTS["kill_switch_clears"].runtime == "SELECT"
    assert _privileges(GRANTS["kill_switch_stops"].runtime) == {"SELECT", "INSERT"}
    for name in ("kill_switch", "kill_switch_stops", "kill_switch_clears"):
        row = GRANTS[name]
        assert (row.portal, row.purge, row.purge_cols) == (False, "", ()), name


# ---- S9: the migrate warning (the database call is replaced; the PostgreSQL case is in test_stop_state_roles.py) -----


def _edit(cfg, fn):
    path = cfg / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _postgres(cfg_dir, ref=None):
    def change(data):
        store = {"kind": "postgres", "dsn_secret_name": DSN_NAME}
        data["backends"]["store"] = store | ({"reset_credential_ref": ref} if ref else {})
        data["backends"]["audit"] = {"kind": "chain"}

    _edit(cfg_dir, change)
    return cfg_dir


WARNING = "warning: no reset role was named, so nobody but the owner can reset the kill switch"


@pytest.mark.parametrize(
    "flags,warned",
    [
        (["--runtime-role", "rt"], True),
        (["--runtime-role", "rt", "--purge-role", "pu", "--portal-role", "po"], True),
        (["--runtime-role", "rt", "--reset-role", "rs"], False),
        (["--reset-role", "rs"], False),
        (
            ["--no-roles"],
            False,
        ),  # a plain migrate with no role named is refused now (step B E5): see test_step_b_e5_no_roles
    ],
)
def test_migrate_warns_on_stderr_when_a_runtime_role_is_named_without_a_reset_role(
    cfg_dir, monkeypatch, capsys, flags, warned
):
    calls = []

    def fake_migrate(dsn, **kw):
        calls.append(kw)
        return []

    monkeypatch.setattr(migrate_mod, "migrate", fake_migrate)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "dbname=never_opened")
    assert cli.main(["--config", str(_postgres(cfg_dir)), "migrate", *flags]) == 0
    out, err = capsys.readouterr()
    assert (WARNING in err) is warned
    assert ("--reset-role <role>" in err) is warned
    assert "warning" not in out  # stderr only: stdout stays the list of applied migrations
    named = dict(zip(flags[::2], flags[1::2], strict=True)) if "--no-roles" not in flags else {}
    assert len(calls) == 1
    assert calls[0]["runtime_role"] == named.get("--runtime-role")
    assert calls[0]["reset_role"] == named.get("--reset-role")


# ---- Exit codes of `limits reset` (ticket: 4 = the store cannot be reached; B-2: the state is read back) -------------


def _unreachable():
    psycopg = pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")
    return [
        psycopg.OperationalError("connection is gone"),
        psycopg.InterfaceError("the connection is closed"),
        StoreUnavailable("store postgres: cannot connect"),
        ConnectionRefusedError("refused"),
        TimeoutError("timed out"),
    ]


@pytest.mark.parametrize("n", range(5))
def test_reset_exits_4_when_the_store_cannot_be_reached_at_the_clear(capsys, n):
    store = StoreStub(set_error=_unreachable()[n])
    limits, audit = _limits(store)
    assert cli.kill_switch(limits, "reset", "user:op") == 4
    out, err = capsys.readouterr()
    assert "kill switch NOT reset: the store is unreachable. The connection was lost" in err
    assert "kill switch OFF" not in out + err
    assert audit.kinds() == ["limits.reset", "limits.reset_failed"]


@pytest.mark.parametrize("n", range(5))
def test_reset_exits_4_when_the_state_cannot_be_read_back_because_the_store_is_gone(capsys, n):
    store = StoreStub(read=_unreachable()[n])
    limits, _ = _limits(store)
    assert cli.kill_switch(limits, "reset", "user:op") == 4
    out, err = capsys.readouterr()
    assert "reset written, but the kill switch could not be read back" in err
    assert "treat it as ON until a read succeeds" in err
    assert "kill switch OFF" not in out + err


def test_reset_exits_2_when_the_read_back_is_answered_with_an_error(capsys):
    store = StoreStub(read=LookupError("no grant"))  # not an OSError: the store answered
    limits, _ = _limits(store)
    assert cli.kill_switch(limits, "reset", "user:op") == 2
    out, err = capsys.readouterr()
    assert "could not be read back (LookupError)" in err
    assert "kill switch OFF" not in out + err


def test_reset_exits_2_and_says_still_on_when_the_read_back_is_on(capsys):
    store = StoreStub(read=KillSwitch(on=True, by="ops:during"))
    limits, audit = _limits(store)
    assert cli.kill_switch(limits, "reset", "user:op") == 2
    out, err = capsys.readouterr()
    assert "kill switch still ON (set by 'ops:during' at " in err and "reset again" not in err
    assert "Check the stop reason" in err
    assert "kill switch OFF" not in out + err
    assert audit.kinds() == ["limits.reset"] and store.reads == 1


def test_reset_exits_0_and_says_off_only_after_reading_off(capsys):
    store = StoreStub(read=KillSwitch(on=False, by="user:op"))
    limits, _ = _limits(store)
    assert cli.kill_switch(limits, "reset", "user:op") == 0
    out, err = capsys.readouterr()
    assert out == "kill switch OFF (by user:op; cleared 0 stop(s))\n" and err == ""
    assert store.reads == 1


@pytest.mark.parametrize("ref", [None, RESET_REF])
def test_cli_limits_reset_exits_4_when_nothing_listens_at_the_store_address(
    cfg_dir, monkeypatch, capsys, ref
):
    """A real connection attempt to a local port nobody listens on (no database is needed for a refusal)."""
    pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")
    from psycopg.conninfo import make_conninfo

    nowhere = make_conninfo(
        host="127.0.0.1", port=1, dbname="none", user="nobody", connect_timeout=3
    )
    real = cli.make

    def fake(capability, settings, *a, **k):
        if capability == "secrets":
            return FakeSecretProvider(
                {DSN_NAME: nowhere, RESET_REF: nowhere + "&application_name=reset"}
            )
        return real(capability, settings, *a, **k)

    monkeypatch.setattr(cli, "make", fake)
    argv = ["--config", str(_postgres(cfg_dir, ref)), "limits", "reset", "--by", "user:op"]
    assert cli.main(argv) == 4
    out, err = capsys.readouterr()
    assert (
        "kill switch NOT reset: the store is unreachable." in err and "Nothing was changed" in err
    )
    assert "Traceback" not in err and "kill switch OFF" not in out + err


def test_b4_a_reset_ref_equal_to_the_runtime_secret_name_exits_2_and_builds_nothing(
    cfg_dir, monkeypatch, capsys
):
    def never(capability, *a, **k):
        raise ConfigError(f"make({capability!r}) was called: the refusal must come first")

    monkeypatch.setattr(cli, "make", never)
    argv = ["--config", str(_postgres(cfg_dir, DSN_NAME)), "limits", "reset", "--by", "user:op"]
    code = cli.main(argv)
    err = capsys.readouterr().err
    assert "was called" not in err, err
    assert code == 2
    assert err.startswith(
        "refused: backends.store.reset_credential_ref names the same secret as "
        "backends.store.dsn_secret_name"
    )
    assert "The kill switch was not changed." in err


def test_cli_validate_constraints_runs_only_the_validate_step(cfg_dir, monkeypatch):
    """`migrate --validate-constraints` needs no role, calls the validate step and never `migrate`."""
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")
    seen = []

    def no_migrate(*a, **k):
        raise AssertionError("migrate ran")

    monkeypatch.setattr("hadavin_sdk.store.migrate.migrate", no_migrate)
    monkeypatch.setattr(
        "hadavin_sdk.store.migrate.validate_stop_constraints",
        lambda dsn, **kw: seen.append(dsn) or ["kill_switch_stops_ts_range"],
    )
    assert cli.main(["--config", str(cfg_dir), "migrate", "--validate-constraints"]) == 0
    assert seen == ["postgresql://unused"]


@pytest.mark.parametrize(
    "extra",
    [
        ["--runtime-role", "rt"],
        ["--no-roles"],
        ["--accept-admin-role", "x"],
        ["--accept-changed-draft", "0009_stop_state_hardening"],
        ["--reset-draft", "0009_stop_state_hardening"],
        ["--reset-draft", ""],
    ],
)
def test_cli_validate_constraints_refuses_to_be_combined_with_role_flags(
    cfg_dir, monkeypatch, extra
):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")

    def boom(*a, **k):
        raise AssertionError("ran")

    monkeypatch.setattr("hadavin_sdk.store.migrate.migrate", boom)
    monkeypatch.setattr("hadavin_sdk.store.migrate.validate_stop_constraints", boom)
    argv = ["--config", str(cfg_dir), "migrate", "--validate-constraints", *extra]
    assert cli.main(argv) == 2


def test_cli_validate_constraints_exits_75_for_a_busy_table_not_2(cfg_dir, monkeypatch):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")

    def busy(*a, **k):
        raise migrate_mod.StopTablesBusy("locked by a long transaction")

    monkeypatch.setattr("hadavin_sdk.store.migrate.validate_stop_constraints", busy)
    assert cli.main(["--config", str(cfg_dir), "migrate", "--validate-constraints"]) == 75


def test_cli_passes_every_migrate_flag_by_keyword(cfg_dir, monkeypatch):
    """A role name must never bind to `no_roles` or `validate_constraints` by position (a parallel branch adds a
    parameter to `_migrate`): every value is passed by keyword and the signature has no positional slot."""
    import inspect

    seen = {}

    def fake(cfg, *args, **kw):
        seen["args"], seen["kw"] = args, kw
        return 0

    monkeypatch.setattr(cli, "_migrate", fake)
    argv = [
        "--config",
        str(cfg_dir),
        "migrate",
        *("--runtime-role", "rt", "--portal-role", "pt", "--purge-role", "pu"),
        *("--reset-role", "rs", "--release-role", "re", "--accept-admin-role", "aa"),
        *("--accept-changed-draft", "0009_x", "--reset-draft", "0010_y"),
    ]
    assert cli.main(argv) == 0
    assert seen["args"] == ()
    assert seen["kw"] == {
        "runtime_role": "rt",
        "portal_role": "pt",
        "purge_role": "pu",
        "reset_role": "rs",
        "release_role": "re",
        "no_roles": False,
        "accepted_admin_roles": ("aa",),
        "accept_changed_draft": ("0009_x",),
        "reset_draft": "0010_y",
        "validate_constraints": False,
    }
    monkeypatch.undo()
    params = list(inspect.signature(cli._migrate).parameters.values())[1:]
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params)


def test_cli_migrate_exits_75_when_the_stop_tables_are_busy(cfg_dir, monkeypatch):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")

    def busy(*a, **k):
        raise migrate_mod.StopTablesBusy("locked by a long transaction")

    monkeypatch.setattr("hadavin_sdk.store.migrate.migrate", busy)
    assert cli.main(["--config", str(cfg_dir), "migrate", "--no-roles"]) == 75
