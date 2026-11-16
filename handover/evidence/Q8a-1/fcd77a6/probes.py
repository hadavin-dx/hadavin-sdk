"""EVIDENCE RUNNER probes for Q8a-1 head fcd77a68. Records only: exception type and message, or what was returned.

Run from the worktree root with the worktree's venv. No database, no network on purpose: every backend that would
contact a service is replaced through the test file's own seam (plant_test_backends). Configs are made with the
helpers of tests/test_q8a_live_overrides.py (live_dir, _demo_app_at, make_cfg + qualify)."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path.cwd()))

from hadavin_sdk import app as app_mod  # noqa: E402
from hadavin_sdk.actions.secrets import FakeSecretProvider  # noqa: E402
from hadavin_sdk.approvals.channel import FakeChannel  # noqa: E402
from hadavin_sdk.config import load_config  # noqa: E402
from hadavin_sdk.models import ToolCallRecord  # noqa: E402
from hadavin_sdk.registry import load_registry  # noqa: E402
from hadavin_sdk.runtime import tick as tick_mod  # noqa: E402
from hadavin_sdk.runtime.tick import TickStep, run_tick  # noqa: E402
from hadavin_sdk.store.memory import MemoryStore  # noqa: E402
from tests import test_q8a_live_overrides as T  # noqa: E402
from tests.conftest import make_cfg, qualify  # noqa: E402
from tests.test_k3_pilot import ScriptedLLM  # noqa: E402
from tests.test_k3_pilot_env import plant_test_backends  # noqa: E402

BASE = Path(tempfile.mkdtemp(prefix="q8a1c-probes-", dir=sys.argv[1]))
N = [0]


def tmp() -> Path:
    N[0] += 1
    p = BASE / f"t{N[0]}"
    p.mkdir()
    return p


def show(text: object, cut: int = 700) -> str:
    return str(text).replace(str(BASE), "<tmp>").replace("\n", "\\n")[:cut]


def rec(label: str, fn, describe=repr) -> object:
    out, err = io.StringIO(), io.StringIO()
    res = None
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            res = fn()
        line = f"no exception; returned {show(describe(res))}"
    except BaseException as exc:  # noqa: BLE001 - recorded verbatim
        line = f"{type(exc).__name__}: {show(exc)}"
    print(f"{label} -> {line}")
    if out.getvalue().strip():
        print(f"    stdout: {show(out.getvalue().strip())}")
    if err.getvalue().strip():
        print(f"    stderr: {show(err.getvalue().strip())}")
    return res


def demo_dir() -> Path:
    d = make_cfg(tmp())
    qualify(load_registry(load_config(d)))
    return d


def demo_app(**kw):
    return app_mod.build(
        demo_dir(), ["test-agent"], secrets=FakeSecretProvider(T.DEMO_SECRETS), **kw
    )


def pilot_app(mp, where="pilot", **kw):
    """A pilot (or prod) app the way test_a_live_build_with_no_test_keyword_is_not_refused builds it."""
    root = T.live_dir(tmp(), mp, where)
    qualify(load_registry(load_config(root)), "ito-agent")
    plant_test_backends(
        mp,
        secrets=FakeSecretProvider(T.PILOT_SECRETS),
        store=MemoryStore,
        channel=FakeChannel(),
        llm=ScriptedLLM(),
    )
    return app_mod.build(root, ["ito-agent"], **kw)


def app_line(app) -> str:
    return (
        f"App(environment={app.config.environment!r}, executor={type(app.executor).__name__}, "
        f"executor.timeout_s={getattr(app.executor, 'timeout_s', 'n/a')!r} "
        f"(type {type(getattr(app.executor, 'timeout_s', None)).__name__}))"
    )


STEP_NAMES = [s.name for s in tick_mod.STEPS]


def states(app) -> str:
    try:
        have = [n for n in [*STEP_NAMES, "recorded"] if app.store.get_tick_state(n) is not None]
        return f"steps with a tick state in the store after the call: {have}"
    except BaseException as exc:  # noqa: BLE001
        return f"tick_state read: {type(exc).__name__}: {show(exc)}"


class FalsySteps:
    """Not a list; falsy; iterating it gives one step."""

    def __init__(self, steps):
        self._steps = steps

    def __bool__(self) -> bool:
        return False

    def __iter__(self):
        return iter(self._steps)


def step_cases(ran: list[str]):
    def one():
        return TickStep("recorded", 0, lambda _ctx: ran.append("recorded"))

    return [
        ("steps=[]", lambda: []),
        ("steps=[one recording step]", lambda: [one()]),
        ("steps=tick.STEPS (the module's own list object)", lambda: tick_mod.STEPS),
        ("steps=() (empty tuple)", lambda: ()),
        ("steps=(one recording step,) (tuple)", lambda: (one(),)),
        ("steps=generator of one recording step", lambda: (s for s in [one()])),
        ("steps=None", lambda: None),
        ("steps=falsy non-list object (class with __bool__ False, iterates to one recording step)", lambda: FalsySteps([one()])),
        ("steps=0 (extra)", lambda: 0),
        ("steps=False (extra)", lambda: False),
        ("steps='' (extra)", lambda: ""),
    ]


def tick_rows(tag: str, make_app) -> None:
    for i in range(len(step_cases([]))):
        ran: list[str] = []
        label, value = step_cases(ran)[i]
        with pytest.MonkeyPatch.context() as mp:
            app = make_app(mp)
            rec(f"(a) {tag}, {label}", lambda: run_tick(app, steps=value()))
            print(f"    recording step ran: {ran}; {states(app)}")


# ---------------------------------------------------------------------------------------------------------------------
print("== (a) run_tick(app, steps=...) ; a new app for every row")
print(f"    tick.STEPS names: {STEP_NAMES}")
tick_rows("demo app (build, stage demo)", lambda mp: demo_app())
tick_rows("pilot app (pilot config, planted backends)", lambda mp: pilot_app(mp))
tick_rows("prod app (pilot config copied with stage prod, planted backends)", lambda mp: pilot_app(mp, "prod"))
tick_rows(
    "extra: pilot the way the run_tick tests build it (_demo_app_at: demo app, config copied with stage pilot)",
    lambda mp: T._demo_app_at(demo_dir(), "pilot"),
)

# ---------------------------------------------------------------------------------------------------------------------
print("== (b) run_tick(app, now=X, steps=Y), both given, pilot app (planted backends)")
FUTURE = datetime.now(UTC) + timedelta(days=500)
for label, kw in [
    ("now=future (today + 500 days), steps=[]", lambda ran: {"now": FUTURE, "steps": []}),
    (
        "now=future, steps=[one recording step]",
        lambda ran: {"now": FUTURE, "steps": [TickStep("recorded", 0, lambda _c: ran.append("recorded"))]},
    ),
    ("now=datetime(2020,1,1,UTC), steps=tick.STEPS", lambda ran: {"now": datetime(2020, 1, 1, tzinfo=UTC), "steps": tick_mod.STEPS}),
    ("now=None, steps=[] (reference: only steps given)", lambda ran: {"now": None, "steps": []}),
    ("now=future, steps=None (reference: only now given)", lambda ran: {"now": FUTURE, "steps": None}),
]:
    ran: list[str] = []
    with pytest.MonkeyPatch.context() as mp:
        app = pilot_app(mp)
        rec(f"(b) pilot, {label}", lambda: run_tick(app, **kw(ran)))
        print(f"    recording step ran: {ran}; {states(app)}")

# ---------------------------------------------------------------------------------------------------------------------
print("== (c) tick.purge_evidence(tick.TickContext(app, <time>)) called by hand on a pilot app (planted backends)")
print("       rows planted by the runner in the app's own in-memory store (made-up run ids ev-run-*):")
print("       tool calls created today, 10 days ago, 100 days ago; one redaction map per run id (put today)")


def plant(store) -> None:
    today = datetime.now(UTC)
    for name, age in (("today", 0), ("10d", 10), ("100d", 100)):
        rid = f"ev-run-{name}"
        store.add_tool_call(
            ToolCallRecord(
                call_id=f"{rid}:1",
                run_id=rid,
                tool="made_up_tool",
                inputs={},
                output="made-up",
                output_sha256="0" * 64,
                created_at=today - timedelta(days=age),
            )
        )
        store.put_redaction_map(rid, {"<P1>": "made-up"})


def left(store) -> str:
    ids = [f"ev-run-{n}" for n in ("today", "10d", "100d")]
    return (
        f"tool calls left: {[r for r in ids if store.list_tool_calls(r)]}; "
        f"redaction maps left: {[r for r in ids if store.get_redaction_map(r) is not None]}"
    )


for label, at in [
    ("time = today + 500 days", lambda: datetime.now(UTC) + timedelta(days=500)),
    ("time = today + 31 days", lambda: datetime.now(UTC) + timedelta(days=31)),
    ("time = today (reference)", lambda: datetime.now(UTC)),
]:
    for where in ("pilot", "prod"):
        with pytest.MonkeyPatch.context() as mp:
            app = pilot_app(mp, where)
            store = app.purge_store or app.store
            print(
                f"    [{where}] app.config.environment={app.config.environment!r}; app.store={type(app.store).__name__}; "
                f"app.purge_store={type(app.purge_store).__name__}; same object as app.store: {app.purge_store is app.store}; "
                f"retention={app.config.retention!r}"
            )
            plant(store)
            print(f"    before: {left(store)}")
            rec(f"(c) {where} app, purge_evidence(TickContext(app, {label}))", lambda: tick_mod.purge_evidence(tick_mod.TickContext(app, at())))
            print(f"    after:  {left(store)}")
with pytest.MonkeyPatch.context() as mp:
    app = pilot_app(mp)
    plant(app.purge_store or app.store)
    rec("(c-reference) pilot app, run_tick(app, now=today + 500 days)", lambda: run_tick(app, now=datetime.now(UTC) + timedelta(days=500)))
    print(f"    after:  {left(app.purge_store or app.store)}")

# ---------------------------------------------------------------------------------------------------------------------
print("== (d1) build(..., timeout_s=x) in demo")
VALUES = [
    ("0", 0, "0"),
    ("-1", -1, "-1"),
    ("True", True, "true"),
    ("1e-9", 1e-9, "1.0e-9"),
    ("5e-324", 5e-324, "5.0e-324"),
    ("0.5", 0.5, "0.5"),
    ("3600", 3600, "3600"),
    ("3600.0000001", 3600.0000001, "3600.0000001"),
    ("3601", 3601, "3601"),
    ("10**400", 10**400, "1" + "0" * 400),
    ("float('inf')", float("inf"), ".inf"),
    ("float('nan')", float("nan"), ".nan"),
    ("Decimal('2.5')", Decimal("2.5"), "2.5"),
    ("Fraction(5, 2)", Fraction(5, 2), "5/2"),
    ("'5'", "5", "'5'"),
]
for text, x, _y in VALUES:
    rec(f"(d1) demo build timeout_s={text}", lambda: demo_app(timeout_s=x), app_line)
rec("(d1-reference) demo build, timeout_s not passed", lambda: demo_app(), app_line)

print("== (d2) the same values written as `executor_timeout_s: <text>` in a demo config.yaml (one line appended by the")
print("       runner to the fixture copy; YAML has no Decimal or Fraction, so those two are written as the plain texts shown);")
print("       then load_config, then build with no timeout_s keyword")
for text, _x, yaml_text in VALUES:
    d = demo_dir()
    path = d / "config.yaml"
    body = path.read_text(encoding="utf-8")
    assert "executor_timeout_s" not in body
    path.write_text(body.rstrip("\n") + f"\nexecutor_timeout_s: {yaml_text}\n", encoding="utf-8")
    shown = yaml_text if len(yaml_text) < 40 else "1 followed by 400 zeros"
    cfg = rec(
        f"(d2) python value {text}; yaml text `executor_timeout_s: {shown}`; load_config",
        lambda: load_config(d),
        lambda c: f"executor_timeout_s={show(repr(c.executor_timeout_s), 60)} (type {type(c.executor_timeout_s).__name__})",
    )
    if cfg is not None:
        rec(
            "     then build(demo, no timeout_s keyword)",
            lambda: app_mod.build(d, ["test-agent"], secrets=FakeSecretProvider(T.DEMO_SECRETS)),
            app_line,
        )
print("== end of probes")
