"""PR #48 result review 4: M-A (clamp + a real release operation), M-B (provably unbilled refusals are released),
M-C (month exposure text/path), M-D (a billed answer is never settled at zero), m2 (sticky probe), K1b charge."""

from __future__ import annotations  # noqa: I001

import threading
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk.limits import OverBudget, counter_key
from hadavin_sdk.llm import retry
from hadavin_sdk.llm.metered import MeteredLLM
from hadavin_sdk.llm.protocol import (
    DeadlineExceeded,
    ProviderError,
    ProviderExhausted,
    SpendLimitReached,
    UnusableAnswer,
    cost_to_settle,
)
from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM
from hadavin_sdk.llm.retry import with_retry
from hadavin_sdk.store.memory import MemoryStore
from tests.test_core_hardening_review import _doc, _Raises, build
from tests.contracts.kinds.store_postgres import pg_schema
from tests.test_k1b_replay import env  # noqa: F401 - fixture
from tests.test_core_hardening_round2 import (  # noqa: F401 - fixtures are used by name
    DAY,
    MID,
    ROUTES,
    Stub,
    _limits,
    _pg_store,
    clock,
    roles,
)

D = Decimal


class Http(Exception):
    def __init__(self, code):
        super().__init__(f"http {code}")
        self.status_code = code


Billed = UnusableAnswer  # defined in llm/protocol.py (round 6): answered, billed, body unusable


def _fail(*errors):
    it = iter(errors)

    def call():
        raise next(it)

    return call


def _caught(**kw):
    kw.setdefault("sleep", lambda s: None)
    kw.setdefault("label", "t")
    kw.setdefault("max_attempts", 3)
    with pytest.raises(ProviderError) as e:
        with_retry(**kw)
    return e.value


# --- the billing contract ---------------------------------------------------------------------------------------------


def test_cost_to_settle_table():
    R = D("0.40")
    assert cost_to_settle(ProviderError("bad"), R) == 0  # one request, refused (class default)
    assert cost_to_settle(SpendLimitReached("cap"), R) == 0
    assert cost_to_settle(ProviderExhausted("x"), R) == R  # unknown by default
    assert cost_to_settle(DeadlineExceeded("late"), R) == R
    e = ProviderExhausted("none sent")
    e.attempts, e.refused = 0, 0
    assert cost_to_settle(e, R) == 0
    e = ProviderExhausted("429 only")
    e.attempts, e.refused = 3, 3
    assert cost_to_settle(e, R) == 0
    e = ProviderExhausted("429, 429, timeout")
    e.attempts, e.refused = 3, 2
    assert cost_to_settle(e, R) == R
    b = Billed("unusable")
    b.billed_usd = D("0.013")
    assert cost_to_settle(b, R) == D("0.013")  # a billed answer is booked at its cost
    assert cost_to_settle(Billed("unpriced"), R) == R  # billed but unpriced: never zero
    b = Billed("nan")
    b.billed_usd = D("NaN")
    assert cost_to_settle(b, R) == R


# --- M-B: the retry layer stamps what was really sent ---------------------------------------------------------------


def test_mb_nothing_sent_when_the_slots_are_full_or_the_deadline_is_gone(monkeypatch):
    monkeypatch.setattr(retry, "_SLOTS", threading.BoundedSemaphore(1))
    retry._SLOTS.acquire()  # every slot taken
    err = _caught(call=lambda: "never", deadline_s=5.0)
    assert isinstance(err, ProviderExhausted) and err.attempts == 0
    assert cost_to_settle(err, D("1")) == 0
    ticks = iter([0.0, 9.0, 9.0, 9.0])
    err = _caught(call=lambda: "never", deadline_s=1.0, clock=lambda: next(ticks))
    assert isinstance(err, DeadlineExceeded) and err.attempts == 0
    assert cost_to_settle(err, D("1")) == 0


def test_mb_429_only_exhaustion_and_a_retry_after_over_the_ceiling_are_released():
    err = _caught(call=_fail(Http(429), Http(429), Http(429)))
    assert isinstance(err, ProviderExhausted) and (err.attempts, err.refused) == (3, 3)
    assert cost_to_settle(err, D("1")) == 0

    class Slow(Http):
        headers = {"retry-after": "100000"}  # noqa: RUF012

    err = _caught(call=_fail(Slow(429)))
    assert isinstance(err, ProviderExhausted) and (err.attempts, err.refused) == (1, 1)
    assert cost_to_settle(err, D("1")) == 0


def test_mb_5xx_timeouts_and_resets_stay_booked_and_one_unknown_attempt_taints_the_rest():
    err = _caught(call=_fail(Http(503), Http(503), Http(503)))
    assert (err.attempts, err.refused) == (3, 0) and cost_to_settle(err, D("1")) == D("1")
    err = _caught(call=_fail(TimeoutError("read"), Http(429), Http(429)))
    assert (err.attempts, err.refused) == (3, 2) and cost_to_settle(err, D("1")) == D("1")
    err = _caught(call=_fail(Http(401)))  # a plain refusal
    assert type(err) is ProviderError and cost_to_settle(err, D("1")) == 0


def test_mb_a_local_refusal_by_the_circuit_sends_nothing_and_is_released(clock):  # noqa: F811
    br = CircuitBreaker(failures=1, reset_after_s=60.0)
    llm = ResilientLLM(Stub(ProviderExhausted("down")), None, br)
    with pytest.raises(ProviderExhausted):
        llm.chat([], system="", route="r")  # opens the circuit
    with pytest.raises(ProviderExhausted) as e:
        llm.chat([], system="", route="r")  # open, no fallback: the primary is not called
    assert e.value.attempts == 0 and cost_to_settle(e.value, D("1")) == 0
    store = MemoryStore()
    lim = _limits(store, daily="1")
    for _ in range(5):  # a polling agent must not drain the cap while the circuit is open
        with pytest.raises(ProviderExhausted):
            MeteredLLM(llm, lim, "a", ROUTES).chat([], system="", route="r")
    assert store.spend_totals("a", DAY)[0] == 0


def test_mb_a_streak_of_429s_does_not_drain_the_daily_cap(clock):  # noqa: F811
    store = MemoryStore()
    lim = _limits(store, daily="1")
    inner = SimpleNamespace(
        chat=lambda *a, **k: with_retry(
            _fail(Http(429), Http(429), Http(429)),
            label="t",
            max_attempts=3,
            sleep=lambda s: None,
        )
    )
    for _ in range(20):
        with pytest.raises(ProviderExhausted):
            MeteredLLM(inner, lim, "a", ROUTES).chat([], system="", route="r")
    assert store.spend_totals("a", DAY) == (0, 0)


# --- M-D: a billed answer is never settled at zero (UnusableAnswer from #43) ----------------------------------------------


def test_md_the_loop_books_a_billed_unusable_answer_and_does_not_release_it(cfg_dir):
    rt, cfg = build(cfg_dir)
    err = Billed("unusable body")
    err.billed_usd = D("0.0123")
    rt.llm = _Raises(err)
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert run.reason_code == "provider_error"
    assert rt.store.spend_totals("test-agent", run.created_at.date())[0] == D("0.0123")


def test_md_metered_llm_books_a_billed_answer_at_its_cost_and_the_worst_case_when_unpriced(clock):  # noqa: F811
    store = MemoryStore()
    lim = _limits(store, daily="1")
    err = Billed("unusable")
    err.billed_usd = D("0.0004")
    with pytest.raises(Billed):
        MeteredLLM(Stub(err), lim, "a", ROUTES).chat([], system="", route="r")
    assert store.spend_totals("a", DAY)[0] == D("0.0004")
    with pytest.raises(Billed):
        MeteredLLM(Stub(Billed("unpriced")), lim, "a", ROUTES).chat([], system="", route="r")
    assert store.spend_totals("a", DAY)[0] > D(
        "0.0004"
    )  # the worst case of the second stays booked


def test_md_the_loop_releases_a_call_proved_unsent(cfg_dir):
    rt, cfg = build(cfg_dir)
    err = ProviderExhausted("nothing left this process")
    err.attempts, err.refused = 0, 0
    rt.llm = _Raises(err)
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert run.reason_code == "provider_exhausted"
    assert rt.store.spend_totals("test-agent", run.created_at.date()) == (0, 0)


# --- m2: a failed probe does not unconfirm a spend cap -------------------------------------------------------------------


def test_m2_a_failed_probe_for_another_reason_keeps_the_circuit_open_for_spend():
    t = [0.0]
    br = CircuitBreaker(failures=1, reset_after_s=10.0, clock=lambda: t[0])
    br.failure(br.allow(), spend=True)
    assert br.open_for_spend
    t[0] = 11.0
    probe = br.allow()
    assert probe is not None and probe.probe
    br.failure(probe, spend=False)  # the probe failed with a plain outage
    assert br.open_for_spend


# --- M-A: the stores never go below zero ---------------------------------------------------------------------------------


def test_ma_memory_store_two_take_backs_never_go_below_zero():
    store = MemoryStore()
    store.settle_spend([("a", DAY, D("1.00"))])
    store.settle_spend([("a", DAY, D("-1.00"))])
    store.settle_spend([("a", DAY, D("-1.00"))])
    assert store.spend_totals("a", DAY) == (0, 0)


def test_ma_postgres_two_take_backs_never_go_below_zero(roles, clock):  # noqa: F811
    store = _pg_store(roles.runtime)
    try:
        lim = _limits(store, daily="5")
        lim.reserve("a", D("1.00"))
        store.settle_spend([("a", DAY, D("-1.00"))])
        store.settle_spend([("a", DAY, D("-1.00"))])
        assert store.spend_totals("a", DAY) == (0, 0)
    finally:
        store.close()


def test_ma_the_maintenance_role_releases_a_stranded_reservation_day_and_month(
    roles,  # noqa: F811
    clock,  # noqa: F811
    monkeypatch,
):
    monkeypatch.setattr("hadavin_sdk.models.now", lambda: MID)
    import psycopg

    from hadavin_sdk.store.migrate import release_reservation

    store = _pg_store(roles.runtime)
    try:
        lim = _limits(store, daily="100", monthly="49.2")
        lim.reserve("a", D("0.40"))  # a process that crashed before settle
        lim.reserve("a", D("0.10"))
        assert store.spend_totals("a", DAY) == (D("0.50"), D("0.50"))
        before, after = release_reservation(roles.maint, "a", DAY, D("0.40"), dry_run=True)
        assert before == after == (D("0.50"), D("0.50"))
        before, after = release_reservation(roles.maint, "a", DAY, D("0.40"))
        assert (before, after) == ((D("0.50"), D("0.50")), (D("0.10"), D("0.10")))
        _, again = release_reservation(
            roles.maint, "a", DAY, D("0.40")
        )  # repeated: clamped, not negative
        assert again == (D("0"), D("0"))
        assert store.spend_totals("a", DAY) == (0, 0)
        # month counters are covered too: the stranded booking no longer counts against the monthly cap
        lim.reserve("a", D("49.00"))
    finally:
        store.close()
    # bounded command
    from hadavin_sdk.errors import ConfigError

    for bad in (
        dict(usd=D("0")),  # noqa: C408
        dict(usd=D("-1")),  # noqa: C408
        dict(usd=D("NaN")),  # noqa: C408
        dict(agent="a/b"),  # noqa: C408
        dict(day=DAY.replace(day=28).replace(year=2099)),  # noqa: C408
    ):
        kw = dict(agent="a", usd=D("1"), day=DAY) | bad  # noqa: C408
        with pytest.raises(ConfigError):
            release_reservation(roles.maint, kw["agent"], kw["day"], kw["usd"])
    # negative tests: the maintenance role holds UPDATE (usd) and nothing else beyond SELECT/DELETE
    with psycopg.connect(roles.maint, autocommit=True) as db:
        for stmt in (
            "INSERT INTO spend (agent_id, day, usd) VALUES ('x', current_date, 1)",
            "UPDATE spend SET agent_id = 'y'",
            "UPDATE spend SET day = current_date",
            "UPDATE spend_month SET month = current_date",
            'UPDATE kill_switch SET "on" = true',
            "UPDATE runs SET state = 'x'",
            "DELETE FROM runs",
            "TRUNCATE spend",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(stmt)
    # the runtime role cannot DELETE (it CAN run UPDATE and INSERT: see test_privilege_matrix_on_the_spend_tables in tests/test_pr48_review6.py)
    with psycopg.connect(roles.runtime, autocommit=True) as db:  # noqa: SIM117
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            db.execute("DELETE FROM spend")


def test_ma_the_cli_refuses_without_the_maintenance_dsn(monkeypatch, capsys, cfg_dir):
    from hadavin_sdk import cli

    monkeypatch.delenv("HADAVIN_MAINTENANCE_DSN", raising=False)
    monkeypatch.setenv("HADAVIN_CONFIG_DIR", str(cfg_dir))
    rc = cli.main(["release-reservation", "--agent", "a", "--day", "2026-03-15", "--amount", "0.4"])
    assert rc == 2 and "HADAVIN_MAINTENANCE_DSN" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        cli.main(["release-reservation", "--agent", "a", "--day", "yesterday", "--amount", "0.4"])
    with pytest.raises(SystemExit):
        cli.main(["release-reservation", "--agent", "a", "--day", "2026-03-15", "--amount", "-1"])


def test_ma_counter_key_matches_the_limits_key():
    from hadavin_sdk.limits import Limits

    lim = _limits(MemoryStore(), tenant="clientx")
    assert isinstance(lim, Limits) and lim._key("a") == counter_key("clientx", "a") == "7:clientx/a"
    assert counter_key("", "a") == "a"
    with pytest.raises(OverBudget):  # sanity: the helper did not change reservation behaviour
        _limits(MemoryStore(), daily="0.0000001").reserve("a", D("1"))


# --- K1b has the same assumption: an exhausted call may have been billed -----------------------------------------------


def test_k1b_an_exhausted_call_of_unknown_outcome_is_charged_against_the_cap(env):  # noqa: F811
    from tests.test_k1b_replay import ScriptedLLM, submit_not_sure

    def boom(_):
        raise ProviderExhausted("read timed out")

    env.run(ScriptedLLM([boom, submit_not_sure()]), max_usd="0.0001")
    assert env.case()["status"] == "error"
    assert (
        env.case("case-002")["status"] == "capped"
    )  # the worst case of the first call was charged


def test_k1b_a_call_proved_unsent_charges_nothing(env):  # noqa: F811
    # REGRESSION GUARD against over-charging: it also passed before this PR (old K1b charged nothing for every
    # ProviderError), so it is not proof of the fix; the proof is the test above and the mutant 'K1b charges always'.
    from tests.test_k1b_replay import ScriptedLLM, submit_not_sure

    def boom(_):
        err = ProviderExhausted("circuit open")
        err.attempts, err.refused = 0, 0
        raise err

    env.run(ScriptedLLM([boom, submit_not_sure()]), max_usd="0.0001")
    assert env.case("case-002")["status"] == "ok"


def test_ma_the_cli_passes_the_tenant_agent_day_amount_and_dry_run_to_the_maintenance_operation(
    monkeypatch, capsys
):
    from datetime import date

    from hadavin_sdk import cli
    from hadavin_sdk.store import migrate as migrate_mod
    from hadavin_sdk.store import postgres as postgres_mod

    seen = {}

    def fake(dsn, agent, day, usd, **kw):
        seen.update(dsn=dsn, agent=agent, day=day, usd=usd, **kw)
        return (D("0.5"), D("0.5")), (D("0.1"), D("0.1"))

    store = SimpleNamespace(kind="postgres", iam_auth=False, region=None, sslmode=None)
    cfg = SimpleNamespace(backends=SimpleNamespace(store=store, secrets=None), tenant="clientx")
    monkeypatch.setenv("HADAVIN_MAINTENANCE_DSN", "dsn-for-test")
    monkeypatch.setattr(migrate_mod, "release_reservation", fake)
    monkeypatch.setattr(postgres_mod, "ca_file", lambda *a: None)
    monkeypatch.setattr(cli, "make", lambda *a: SimpleNamespace(get=lambda n: None))
    args = SimpleNamespace(agent="a", day=date(2026, 3, 15), amount=D("0.4"), dry_run=True)
    assert cli._release_reservation(cfg, args) == 0
    assert (seen["tenant"], seen["agent"], seen["day"], seen["usd"], seen["dry_run"]) == (
        "clientx",
        "a",
        date(2026, 3, 15),
        D("0.4"),
        True,
    )
    out = capsys.readouterr().out
    assert "would release" in out and "0.5 -> 0.1" in out
    args.dry_run = False
    cli._release_reservation(cfg, args)
    assert seen["dry_run"] is False and "released up to" in capsys.readouterr().out


def test_ma_a_zero_or_negative_amount_is_refused_before_any_connection(monkeypatch):
    # No database: the validation itself must refuse (a zero amount used to be stopped only by a missing INSERT right).
    import datetime

    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.store import migrate

    def no_connect(*a, **k):
        raise AssertionError("connected before validating")

    monkeypatch.setattr(migrate, "connect", no_connect)
    for amount in (D("0"), D("-0.01"), D("NaN"), D("Infinity")):
        with pytest.raises(ConfigError):
            migrate.release_reservation("dsn", "a", datetime.date(2020, 1, 1), amount)


def test_ma_the_cli_path_against_real_postgres_portal_role_cannot_release_maintenance_role_can():
    # Real roles, the real CLI entry (_release_reservation) with HADAVIN_MAINTENANCE_DSN; the portal (read-only) role is denied.
    import datetime
    import uuid

    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.migrate import migrate, release_reservation

    for dsn in pg_schema():
        pt, mt = "pt_" + uuid.uuid4().hex[:10], "mt_" + uuid.uuid4().hex[:10]
        rt = "rt_" + uuid.uuid4().hex[:10]
        with psycopg.connect(dsn, autocommit=True) as db:
            for n in (pt, mt, rt):
                db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(n)))
        migrate(dsn, runtime_role=rt, portal_role=pt, maintenance_role=mt)
        try:
            day = datetime.date(2026, 3, 15)
            with psycopg.connect(dsn, autocommit=True) as db:
                db.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('p', %s, 2)", (day,))
                db.execute(
                    "INSERT INTO spend_month (agent_id, month, usd) VALUES ('p', %s, 2)",
                    (day.replace(day=1),),
                )
            with pytest.raises(Exception) as err:
                release_reservation(make_conninfo(dsn, user=pt), "p", day, D("1"))
            assert (
                "denied" in str(err.value).lower()
                or "privilege" in str(err.value).lower()
                or err.type.__name__ == "StoreUnavailable"
            )
            with psycopg.connect(dsn, autocommit=True) as db:  # the refused attempt changed nothing
                assert db.execute("SELECT usd FROM spend WHERE agent_id='p'").fetchone()[0] == 2
            before, after = release_reservation(make_conninfo(dsn, user=mt), "p", day, D("1"))
            assert (before, after) == ((D("2"), D("2")), (D("1"), D("1")))
            # a tenant's counter lives under the length-prefixed key: the release must find it, not the bare id
            tkey = counter_key("clientx", "p")
            with psycopg.connect(dsn, autocommit=True) as db:
                db.execute("INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, 3)", (tkey, day))
                db.execute(
                    "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, 3)",
                    (tkey, day.replace(day=1)),
                )
            tb, ta = release_reservation(
                make_conninfo(dsn, user=mt), "p", day, D("2"), tenant="clientx"
            )
            assert (tb, ta) == ((D("3"), D("3")), (D("1"), D("1")))
        finally:
            with psycopg.connect(dsn, autocommit=True) as db:
                for n in (pt, mt, rt):
                    db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(n)))
                    db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(n)))
