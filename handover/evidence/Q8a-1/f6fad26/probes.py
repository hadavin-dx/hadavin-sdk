"""EVIDENCE RUNNER probes for Q8a-1 head f6fad26f. Records only: exception type and message, or what was returned.

Run from the worktree root with the worktree's venv. No database, no network on purpose: every backend that would
contact a service is replaced through the test file's own seam (plant_test_backends). Configs are made with the
helpers of tests/test_q8a_live_overrides.py (live_dir, vault_dir, make_cfg + qualify)."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path.cwd()))

from hadavin_sdk import app as app_mod  # noqa: E402
from hadavin_sdk import cli as cli_mod  # noqa: E402
from hadavin_sdk.actions.secrets import FakeSecretProvider  # noqa: E402
from hadavin_sdk.approvals.channel import FakeChannel  # noqa: E402
from hadavin_sdk.config import load_config  # noqa: E402
from hadavin_sdk.k1b import audit_sink as sink_mod  # noqa: E402
from hadavin_sdk.registry import load_registry  # noqa: E402
from hadavin_sdk.runtime import tick as tick_mod  # noqa: E402
from hadavin_sdk.runtime.tick import run_tick  # noqa: E402
from hadavin_sdk.store.memory import MemoryStore  # noqa: E402
from tests import test_q8a_live_overrides as T  # noqa: E402
from tests.conftest import make_cfg, qualify  # noqa: E402
from tests.test_k3_pilot import ScriptedLLM  # noqa: E402
from tests.test_k3_pilot_env import plant_test_backends  # noqa: E402

BASE = Path(tempfile.mkdtemp(prefix="q8a1b-probes-", dir=sys.argv[1]))
N = [0]


def tmp() -> Path:
    N[0] += 1
    p = BASE / f"t{N[0]}"
    p.mkdir()
    return p


def show(text: object, cut: int = 700) -> str:
    return str(text).replace("\n", "\\n")[:cut]


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


def cfg_line(cfg) -> str:
    return f"Config(environment={cfg.environment!r}, backends.secrets={cfg.backends.secrets!r}, backends.signer.kind={cfg.backends.signer.kind!r})"


def app_line(app) -> str:
    return (
        f"App(environment={app.config.environment!r}, executor={type(app.executor).__name__}, "
        f"executor.timeout_s={getattr(app.executor, 'timeout_s', 'n/a')!r}, "
        f"sources={sorted(app.sources)!r}, hooks.tools={getattr(app.runtime.hooks, 'tools', 'n/a')!r})"
    )


# ---------------------------------------------------------------------------------------------------------------------
print("== (a) pilot and prod, backends.secrets = {kind: vault, address: https://vault.example}, auth left out")
for where in ("pilot", "prod"):
    root = T.vault_dir(tmp(), where, "secrets", T.VAULT)
    rec(f"(a) {where} secrets=vault auth-left-out load_config", lambda: load_config(root), cfg_line)
    rec(f"(a) {where} secrets=vault auth-left-out build", lambda: app_mod.build(root, ["ito-agent"]), app_line)
print("== (a-extra, not in the brief) the same with backends.signer = vault_transit, auth left out")
for where in ("pilot", "prod"):
    root = T.vault_dir(tmp(), where, "signer", T.TRANSIT)
    rec(f"(a-extra) {where} signer=vault_transit auth-left-out load_config", lambda: load_config(root), cfg_line)
    rec(f"(a-extra) {where} signer=vault_transit auth-left-out build", lambda: app_mod.build(root, ["ito-agent"]), app_line)

# ---------------------------------------------------------------------------------------------------------------------
print("== (b) command-line functions with that same config (cli._main; backends planted through the test seam:")
print("       secrets=FakeSecretProvider(PILOT_SECRETS), store=MemoryStore, signer=None, anchor=None, llm=ScriptedLLM();")
print("       for replay and score the same objects are also planted in hadavin_sdk.k1b.audit_sink, which has its own `make`)")


def cli_call(where: str, argv: list[str], env: dict[str, str] | None = None, label: str | None = None):
    with pytest.MonkeyPatch.context() as mp:
        root = T.vault_dir(tmp(), where, "secrets", T.VAULT)
        mp.setenv("HADAVIN_CONFIG_DIR", str(root))
        mp.delenv("HADAVIN_MIGRATE_DSN", raising=False)
        for k, v in (env or {}).items():
            mp.setenv(k, v)
        store, secrets = MemoryStore(), FakeSecretProvider(T.PILOT_SECRETS)
        calls = []
        for module in (cli_mod, sink_mod):
            calls.append(
                plant_test_backends(
                    mp, module=module, secrets=secrets, store=lambda: store, signer=None, anchor=None, llm=ScriptedLLM()
                )
            )
        work = tmp()
        argv = [a.replace("{work}", str(work)) for a in argv]
        for sub in ("bundles", "causes", "outputs", "out"):
            (work / sub).mkdir()
        (work / "answers.yaml").write_text("", encoding="utf-8")
        rec(f"(b) {where} {label or ' '.join(argv).replace(str(work), '<work>')}", lambda: cli_mod._main(argv))
        asked = [(c, k) for lst in calls for (c, k, _p) in lst]
        print(f"    factory calls seen (capability, kind): {asked}")
        print(f"    kill switch state in the planted store after the call: {store.get_kill_switch()!r}" if hasattr(store, "get_kill_switch") else "    (planted store has no get_kill_switch)")


for where in ("pilot", "prod"):
    cli_call(where, ["limits", "stop", "--by", "ops"])
    cli_call(where, ["limits", "reset", "--by", "ops"])
    cli_call(where, ["audit", "verify"])
    cli_call(where, ["gate", "ito-agent"])
    cli_call(where, ["migrate"], label="migrate (HADAVIN_MIGRATE_DSN not set)")
    cli_call(
        where,
        ["replay", "ito-agent", "--bundles", "{work}/bundles", "--cause-list", "{work}/causes", "--max-usd", "1", "--out", "{work}/out"],
    )
    cli_call(
        where,
        ["score", "--outputs", "{work}/outputs", "--answers", "{work}/answers.yaml", "--cause-list", "{work}/causes", "--bundles", "{work}/bundles"],
    )

# ---------------------------------------------------------------------------------------------------------------------
print("== (c) run_tick(app, now=...) on a demo app and on a pilot app (a new app for every row)")


class FalsyTime(datetime):
    def __bool__(self) -> bool:
        return False


PAST = datetime(2020, 1, 1, tzinfo=UTC)
FUTURE = datetime.now(UTC) + timedelta(days=500)
FALSY_TIME = FalsyTime(2020, 1, 1, tzinfo=UTC)
NOWS = [
    ("fixed past datetime(2020,1,1,UTC)", PAST),
    ("future (today + 500 days)", FUTURE),
    ("None", None),
    ("falsy datetime subclass (2020-01-01, __bool__ False)", FALSY_TIME),
    ("0", 0),
    ("False", False),
    ("''", ""),
]


def tick_row(label, app, **kw):
    rec(label, lambda: run_tick(app, **kw))
    try:
        states = {s.name: app.store.get_tick_state(s.name) for s in tick_mod.STEPS}
        print(
            "    tick_state after: "
            + show({n: (None if st is None else (getattr(st, "last_status", "?"), str(getattr(st, "last_run_at", "?")))) for n, st in states.items()}, 900)
        )
    except BaseException as exc:  # noqa: BLE001
        print(f"    tick_state read: {type(exc).__name__}: {show(exc)}")


for name, value in NOWS:
    tick_row(f"(c) demo app, now={name}", demo_app(), now=value)
for name, value in NOWS:
    with pytest.MonkeyPatch.context() as mp:
        tick_row(f"(c) pilot app, now={name}", pilot_app(mp), now=value)
with pytest.MonkeyPatch.context() as mp:
    tick_row("(c) pilot app, now not passed at all", pilot_app(mp))
with pytest.MonkeyPatch.context() as mp:
    tick_row("(c-extra) prod app (pilot config copied with stage prod), now=future", pilot_app(mp, "prod"), now=FUTURE)

# ---------------------------------------------------------------------------------------------------------------------
print("== (d) build(..., timeout_s=x) in demo")
for text, x in [
    ("0", 0), ("0.0", 0.0), ("-1", -1), ("True", True), ("False", False), ("float('nan')", float("nan")),
    ("float('inf')", float("inf")), ("'5'", "5"), ("1e-9", 1e-9), ("5", 5),
]:
    rec(f"(d) demo timeout_s={text}", lambda: demo_app(timeout_s=x), app_line)

# ---------------------------------------------------------------------------------------------------------------------
print("== (e) build(..., sources=/tools=) in demo and pilot")
CASES = [("sources={}", {"sources": {}}), ("tools={}", {"tools": {}}), ("sources=None", {"sources": None}), ("tools=None", {"tools": None})]
for text, kw in CASES:
    rec(f"(e) demo {text}", lambda: demo_app(**kw), app_line)
for text, kw in CASES:
    with pytest.MonkeyPatch.context() as mp:
        rec(f"(e) pilot {text}", lambda: pilot_app(mp, **kw), app_line)

# ---------------------------------------------------------------------------------------------------------------------
print("== (f) run_tick(app, steps=...) on a pilot app")
print(f"    default STEPS names: {[s.name for s in tick_mod.STEPS]}")
with pytest.MonkeyPatch.context() as mp:
    tick_row("(f) pilot steps=[]", pilot_app(mp), steps=[])
for left_out in [s.name for s in tick_mod.STEPS]:
    with pytest.MonkeyPatch.context() as mp:
        tick_row(
            f"(f) pilot steps=STEPS without {left_out!r}",
            pilot_app(mp),
            steps=[s for s in tick_mod.STEPS if s.name != left_out],
        )
with pytest.MonkeyPatch.context() as mp:
    tick_row("(f) pilot steps=None (reference)", pilot_app(mp), steps=None)
print("== end of probes")
