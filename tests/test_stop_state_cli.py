"""`cli.kill_switch`: exit codes and what is printed (the typed name never appears, only its keyed label)."""

from __future__ import annotations

from hadavin_sdk import cli
from hadavin_sdk.audit.protocol import AuditUnavailable
from hadavin_sdk.limits import Limits
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import NotMigrated
from tests.stop_state_helpers import KEY, RESET_NAME


class Audit:
    def __init__(self):
        self.down = False

    def write_intent(self, event):
        if self.down:
            raise AuditUnavailable("down")
        return "i"

    def write_outcome(self, event):
        return None


def make(store=None, **kw) -> Limits:
    store = store or MemoryStore()
    return Limits(
        store,
        Audit(),
        None,
        environment="demo",
        label_key=KEY,
        reset_store=kw.pop("reset_store", store),
        reset_names={RESET_NAME},
        **kw,
    )


def test_whois_prints_the_label_not_the_name(capsys):
    lim = make()
    assert cli.kill_switch(lim, "whois", "user:a") == 0
    out = capsys.readouterr().out.strip()
    assert out == lim.label("user:a") and "user:a" not in out


def test_whois_with_a_short_key_is_refused_with_5(capsys):
    lim = Limits(MemoryStore(), Audit(), None, environment="demo", label_key=b"short")
    assert cli.kill_switch(lim, "whois", "user:a") == 5


def test_stop_status_reset_round_trip(capsys):
    lim = make()
    assert cli.kill_switch(lim, "stop", "user:a") == 0
    out = capsys.readouterr().out
    assert "kill switch ON" in out and "user:a" not in out
    assert cli.kill_switch(lim, "status", "") == 0
    assert "open_requests 1" in capsys.readouterr().out
    s = lim.status()
    assert (
        cli.kill_switch(
            lim, "reset", RESET_NAME, expect_version=s.version, expect_open=s.open_requests
        )
        == 0
    )
    assert "kill switch OFF" in capsys.readouterr().out


def test_reset_needs_both_expect_flags_exit_2(capsys):
    lim = make()
    lim.stop("user:a")
    assert cli.kill_switch(lim, "reset", RESET_NAME, expect_version=0) == 2
    assert cli.kill_switch(lim, "reset", RESET_NAME, expect_open=1) == 2
    assert lim.status().on


def test_stale_pair_exit_6_and_switch_stays_on(capsys):
    lim = make()
    lim.stop("user:a")
    assert cli.kill_switch(lim, "reset", RESET_NAME, expect_version=0, expect_open=5) == 6
    assert lim.status().on


def test_unlisted_name_exit_5(capsys):
    lim = make()
    lim.stop("user:a")
    assert cli.kill_switch(lim, "reset", "user:z", expect_version=0, expect_open=1) == 5
    assert lim.status().on


def test_audit_down_on_reset_exit_3_and_switch_stays_on(capsys):
    lim = make()
    lim.stop("user:a")
    lim.audit.down = True
    assert cli.kill_switch(lim, "reset", RESET_NAME, expect_version=0, expect_open=1) == 3
    assert lim.status().on


def test_not_migrated_exit_9(capsys):
    class Old(MemoryStore):
        def set_kill_switch(self, ks):
            raise NotMigrated("no function")

        def reset_kill_switch(self, *a):
            raise NotMigrated("no function")

    lim = make(Old())
    assert cli.kill_switch(lim, "stop", "user:a") == 9
    assert cli.kill_switch(lim, "reset", RESET_NAME, expect_version=0, expect_open=1) == 9


def test_unreachable_store_exit_4_and_says_not_set(capsys):
    class Down(MemoryStore):
        def set_kill_switch(self, ks):
            raise ConnectionError("db down")

    assert cli.kill_switch(make(Down()), "stop", "user:a") == 4
    assert "NOT set" in capsys.readouterr().err


def test_stop_busy_store_exit_7_and_says_not_done(capsys):
    from hadavin_sdk.store.protocol import StoreBusy

    class Busy(MemoryStore):
        def set_kill_switch(self, ks):
            raise StoreBusy("55P03")

    assert cli.kill_switch(make(Busy()), "stop", "user:a") == 7
    assert "NOT" in capsys.readouterr().err


def test_not_migrated_message_points_at_a_runbook_that_exists(capsys):
    import re
    from pathlib import Path

    src = Path(cli.__file__).read_text(encoding="utf-8")
    paths = set(re.findall(r"docs/[A-Za-z0-9_.-]+\.md", src))
    assert "docs/stop-state-runbook.md" in paths
    root = Path(cli.__file__).resolve().parents[2]
    for p in paths:
        assert (root / p).is_file(), p


class _Cfg:
    environment = "pilot"

    class limits:
        runtime_role = "rt"
        stop_role = "sp"
        reset_group = "rg"


def _checker(report=None, busy=False):
    from hadavin_sdk.models import GuardReport
    from hadavin_sdk.store.protocol import StoreBusy

    class S(MemoryStore):
        def guard_report(self, *a):
            if busy:
                raise StoreBusy("57014")
            return report or GuardReport(runtime_connection_limit=5)

    return S()


def test_limits_check_exit_0_10_7_and_2(capsys):
    from hadavin_sdk.models import GuardReport

    assert cli._limits_check(_Cfg, _checker()) == 0
    assert "guard OK" in capsys.readouterr().out
    bad = GuardReport(problems=("the runtime role can execute x",), runtime_connection_limit=5)
    assert cli._limits_check(_Cfg, _checker(bad)) == 10
    assert "problem: the runtime role can execute x" in capsys.readouterr().out
    assert cli._limits_check(_Cfg, _checker(busy=True)) == 7
    assert cli._limits_check(_Cfg, None) == 2


def test_stop_on_pilot_without_a_label_key_name_works_not_a_traceback(capsys):
    from types import SimpleNamespace as NS

    cfg = NS(
        environment="pilot",
        backends=NS(store=NS(stop_credential_ref=None, reset_credential_ref=None)),
        limits=NS(label_key_secret_name=None, reset_names=set(), key_id="k1"),
    )
    inner = MemoryStore()

    class NotMemory:  # Limits refuses a MemoryStore outside demo; this stands in for a database store
        def __getattr__(self, name):
            return getattr(inner, name)

    args = NS(action="stop", by="user:a", name="", expect_version=None, expect_open=None)
    assert cli._limits(cfg, None, None, NotMemory(), Audit(), args) == 0
    assert "kill switch ON" in capsys.readouterr().out
