"""Hostile probes for Q8a-1 at 464dee1. Records only: exception type and message, or 'no exception'."""
import os, sys, tempfile, traceback
from pathlib import Path
import pytest, yaml
from hadavin_sdk import app as app_mod
from hadavin_sdk.config import load_config
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.guard.injection import RegexDetector
from tests.test_k3_pilot import ScriptedLLM
from tests.test_q8a_live_overrides import live_dir, vault_dir, VAULT, TRANSIT, PILOT_SECRETS, override

def F(base):
    return type("Falsy" + base.__name__, (base,), {"__bool__": lambda self: False})

class FalsyClock:
    def __bool__(self): return False
    def __call__(self):
        from hadavin_sdk.models import now
        return now()

class FalsyFloat(float):
    def __bool__(self): return False

def falsy(name):
    return {
        "secrets": lambda: F(FakeSecretProvider)(PILOT_SECRETS),
        "channel": lambda: F(FakeChannel)(),
        "detector": lambda: F(RegexDetector)(0.5),
        "llm": lambda: F(ScriptedLLM)(),
        "clock": lambda: FalsyClock(),
        "timeout_s": lambda: FalsyFloat(2.5),
    }[name]()

N = [0]
def tmp():
    N[0] += 1
    return Path(tempfile.mkdtemp(prefix=f"probe{N[0]}-", dir=os.environ["PROBE_TMP"]))

def show(label, fn):
    mp = pytest.MonkeyPatch()
    try:
        out = fn(mp)
        print(f"{label} -> no exception (returned {type(out).__name__})")
    except BaseException as exc:  # noqa: BLE001 - recording
        print(f"{label} -> {type(exc).__module__}.{type(exc).__name__}: {" \\n ".join(str(exc)[:700].splitlines())}")
    finally:
        mp.undo()

def build_with(where, **kw):
    def fn(mp):
        root = live_dir(tmp(), mp, where)
        return app_mod.build(root, ["ito-agent"], **kw)
    return fn

print("== (a) each keyword set to an object whose __bool__ returns False")
for where in ("pilot", "prod"):
    for name in ("secrets", "channel", "detector", "llm", "clock", "timeout_s"):
        obj = falsy(name)
        show(f"(a) stage={where} {name}=<{type(obj).__name__}, bool={bool(obj)}>", build_with(where, **{name: obj}))
    show(f"(a) stage={where} timeout_s=0", build_with(where, timeout_s=0))
    show(f"(a) stage={where} timeout_s=0.0", build_with(where, timeout_s=0.0))
    show(f"(a) stage={where} timeout_s=False", build_with(where, timeout_s=False))

print("== (b) two keywords at once")
import itertools
for where in ("pilot", "prod"):
    for a, b in itertools.permutations(("secrets", "channel", "detector", "llm", "clock", "timeout_s"), 2):
        show(f"(b) stage={where} given in call order {a}=, {b}=", build_with(where, **{a: override(a, PILOT_SECRETS), b: override(b, PILOT_SECRETS)}))

print("== (c) clock= set to the module's own now function")
from hadavin_sdk import models
print(f"(c) app_mod.now is models.now: {app_mod.now is models.now}")
for where in ("pilot", "prod"):
    show(f"(c) stage={where} clock=hadavin_sdk.app.now", build_with(where, clock=app_mod.now))
    show(f"(c) stage={where} clock=hadavin_sdk.models.now", build_with(where, clock=models.now))

print("== (d) stage value with other letter case / surrounding spaces")
STAGES = ["Pilot", "PROD", "PILOT", "Prod", " pilot", "pilot ", " prod ", " demo", "demo ", "Demo", "DEMO", "\tdemo\n"]
print("-- (d1) stage put on the loaded pilot config with model_copy (the way live_dir does it); build(channel=FakeChannel())")
for st in STAGES:
    show(f"(d1) stage={st!r} channel=FakeChannel()", build_with(st, channel=FakeChannel()))
print("-- (d2) stage written in config.yaml of the pilot config; load_config(root)")
from tests.test_k3_pilot_env import pilot_cfg
for st in STAGES:
    def fn(mp, st=st):
        root = pilot_cfg(tmp())
        (root / "secrets").mkdir()
        p = root / "config.yaml"
        d = yaml.safe_load(p.read_text(encoding="utf-8")); d["environment"] = st
        p.write_text(yaml.safe_dump(d), encoding="utf-8")
        cfg = load_config(root)
        return cfg.environment
    show(f"(d2) config.yaml environment={st!r} load_config", fn)
print("-- (d3) same config.yaml, then build(channel=FakeChannel())")
for st in STAGES:
    def fn(mp, st=st):
        root = pilot_cfg(tmp())
        (root / "secrets").mkdir()
        p = root / "config.yaml"
        d = yaml.safe_load(p.read_text(encoding="utf-8")); d["environment"] = st
        p.write_text(yaml.safe_dump(d), encoding="utf-8")
        return app_mod.build(root, ["ito-agent"], channel=FakeChannel())
    show(f"(d3) config.yaml environment={st!r} build(channel=FakeChannel())", fn)

print("== (e) Vault secrets / signer config, auth in other letter case, and auth through an environment variable")
def vload(where, cap, settings, env=None):
    def fn(mp):
        for k, v in (env or {}).items():
            mp.setenv(k, v)
        root = vault_dir(tmp(), where, cap, settings)
        cfg = load_config(root)
        s = getattr(cfg.backends, cap)
        return type("auth_is_" + repr(s.auth), (), {})()
    return fn
for where in ("pilot", "prod"):
    for cap, base in (("secrets", VAULT), ("signer", TRANSIT)):
        for auth in ("TOKEN", "Token", " token", "token ", "token"):
            show(f"(e1) stage={where} backends.{cap} kind={base['kind']} auth={auth!r}", vload(where, cap, base | {"auth": auth}))
        show(f"(e1) stage={where} backends.{cap} kind={base['kind']} auth left out", vload(where, cap, base))
        show(f"(e1) stage={where} backends.{cap} kind={base['kind']} auth=None (yaml null)", vload(where, cap, base | {"auth": None}))
        for kind in (base["kind"].upper(), base["kind"].title(), base["kind"] + " "):
            show(f"(e1) stage={where} backends.{cap} kind={kind!r} auth left out", vload(where, cap, base | {"kind": kind}))
print("-- (e2) environment-variable override attempts (config.py reads only HADAVIN_CONFIG_DIR through Settings(env_prefix='HADAVIN_'); these variables are tried anyway)")
ENVS = [
    {"HADAVIN_BACKENDS__SECRETS__AUTH": "kubernetes"},
    {"HADAVIN_BACKENDS_SECRETS_AUTH": "kubernetes"},
    {"HADAVIN_AUTH": "kubernetes"},
    {"HADAVIN_ENVIRONMENT": "demo"},
    {"VAULT_AUTH": "kubernetes"},
]
for where in ("pilot", "prod"):
    for env in ENVS:
        show(f"(e2) stage={where} backends.secrets kind=vault auth left out in file, env {env}", vload(where, "secrets", VAULT, env))
    for env in ({"HADAVIN_BACKENDS__SECRETS__AUTH": "token"}, {"HADAVIN_BACKENDS__SECRETS__AUTH": "TOKEN"}, {"HADAVIN_AUTH": "token"}):
        show(f"(e2) stage={where} backends.secrets kind=vault auth=kubernetes role=hadavin in file, env {env}", vload(where, "secrets", VAULT | {"auth": "kubernetes", "role": "hadavin"}, env))
print("-- (e3) HADAVIN_CONFIG_DIR names the folder (config_dir=None), env HADAVIN_ENVIRONMENT=demo, file says pilot + vault token")
def fn(mp):
    root = vault_dir(tmp(), "pilot", "secrets", VAULT)
    mp.setenv("HADAVIN_CONFIG_DIR", str(root)); mp.setenv("HADAVIN_ENVIRONMENT", "demo"); mp.setenv("HADAVIN_BACKENDS__SECRETS__AUTH", "kubernetes")
    return type("env_is_" + load_config(None).environment, (), {})()
show("(e3)", fn)
print("== reference rows (not hostile): demo with a falsy channel; pilot with no keyword and hold_run_ids only is not run here (needs every backend)")
def demo(mp):
    from tests.conftest import make_cfg
    root = make_cfg(tmp())
    return app_mod.build(root, ["ito-agent"], channel=F(FakeChannel)())
show("(ref) demo make_cfg channel=<falsy FakeChannel>", demo)
