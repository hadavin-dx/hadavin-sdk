"""EVIDENCE RUNNER probes (own script, item 6). Records whether a made-up canary reaches any output. No judgment."""
import io, json, logging, os, shutil, subprocess, sys, tempfile, traceback, contextlib
from pathlib import Path
import yaml
from pydantic import ValidationError

# canaries built from parts (not secret-shaped; made-up)
C = "Q" + "Zcanary" + "-" + "7F3a9" + "_" + "Xk"          # capital letters: not word-like
W = "zq" + "wordcanary" + "-" + "lower"                   # word-like, not loaded
LIB = "made-up library says: bad token " + "[" + C + "]"  # made-up library error text
results = []

def surfaces(exc):
    out = {}
    out["str"] = str(exc)
    out["repr"] = repr(exc)
    out["args"] = repr(getattr(exc, "args", ()))
    out["traceback"] = "".join(traceback.format_exception(exc))
    c = exc.__cause__; x = exc.__context__
    out["cause"] = repr(c); out["context"] = repr(x)
    if isinstance(exc, ValidationError):
        for inc in (True, False):
            try: out[f"errors(include_input={inc})"] = repr(exc.errors(include_input=inc, include_context=True, include_url=False))
            except Exception as e: out[f"errors({inc})"] = "EXC " + type(e).__name__
        try: out["json()"] = exc.json(include_input=True)
        except Exception as e: out["json()"] = "EXC " + type(e).__name__
    return out

def rec(name, exc, extra=""):
    s = surfaces(exc) if exc is not None else {}
    hits = [k for k, v in s.items() if (C in v or W in v or "made-up library says" in v)]
    results.append((name, "RAISED " + type(exc).__name__ if exc else "no error", hits, {k: v[:160] for k, v in s.items() if k in hits}))

def attempt(name, fn):
    exc = None
    try:
        r = fn()
        results.append((name, "no error; returned " + type(r).__name__, [], {}))
        return
    except BaseException as e:  # record everything
        exc = e
    rec(name, exc)

from hadavin_sdk.models import AuditEvent
from hadavin_sdk import errors
from hadavin_sdk.audit.local_dir import LocalDirSink

base = dict(run_id="run-" + "0" * 32, domain="d", operation="o", principal="p", source="s")
class StrSub(str):
    def __str__(self): return C
    def __repr__(self): return C
    def __eq__(self, o): return True
    def __hash__(self): return 1
class StrSub2(str):  # text itself is the canary, its __str__ says something else
    def __str__(self): return "harmless"

for label, v in [("canary", C), ("wordlike", W), ("libtext", LIB), ("strsub-__str__=canary", StrSub("abc")), ("strsub-text=canary", StrSub2(C)), ("path-ish", "../" + C), ("long", C * 40), ("nonstr-int", 12345), ("nonstr-bytes", C.encode())]:
    attempt(f"AuditEvent(event_id={label})", lambda v=v: AuditEvent(event_id=v, **base))
    attempt(f"AuditEvent.model_validate(event_id={label})", lambda v=v: AuditEvent.model_validate({"event_id": v, **base}))
attempt("AuditEvent.model_validate_json(event_id=canary)", lambda: AuditEvent.model_validate_json(json.dumps({"event_id": C, **base})))
attempt("AuditEvent.model_validate_strings(event_id=canary)", lambda: AuditEvent.model_validate_strings({"event_id": C, **base}))
attempt("AuditEvent(extra key = canary)", lambda: AuditEvent(**{C: 1}, **base))
attempt("AuditEvent(run_id=canary-wrong-type, ts=canary)", lambda: AuditEvent(run_id=C, domain="d", operation="o", principal="p", source="s", ts=C))
attempt("TypeAdapter(AuditEvent) (documented as NOT covered)", lambda: __import__("pydantic").TypeAdapter(AuditEvent).validate_python({"event_id": C, **base}))

# shown_id / shown_name
for label, v in [("canary", C), ("wordlike", W), ("libtext", LIB), ("strsub-__str__=canary", StrSub("evt-" + "a" * 32)), ("strsub-text=canary", StrSub2(C))]:
    r = errors.shown_id(v); results.append((f"shown_id({label})", "returned " + repr(r), [k for k in ["ret"] if C in r or W in r], {"ret": r}))
    r = errors.shown_name(v); results.append((f"shown_name({label})", "returned " + repr(r), [k for k in ["ret"] if C in r or W in r], {"ret": r}))
    r = errors.shown_name(v, loaded=[v, str(v) if type(v) is str else "x"]); results.append((f"shown_name({label}, loaded=[itself])", "returned " + repr(r), [k for k in ["ret"] if C in r or W in r], {"ret": r}))

# local_dir
tmp = Path(tempfile.mkdtemp(prefix="ev-probe-"))
try:
    sink = LocalDirSink(tmp / "audit")
    ev = AuditEvent.model_construct(event_id=C, **base)
    logs = io.StringIO(); h = logging.StreamHandler(logs); logging.getLogger().addHandler(h); logging.getLogger().setLevel(logging.DEBUG)
    attempt("LocalDirSink.write_intent(model_construct event_id=canary)", lambda: sink.write_intent(ev))
    r = sink.write_outcome(ev); results.append(("LocalDirSink.write_outcome(model_construct event_id=canary)", "returned " + repr(r), [], {}))
    try: sink.reconcile()
    except BaseException as e: rec("reconcile raised", e)
    for label, v in [("path-ish", "../" + C), ("strsub", StrSub("abc"))]:
        e2 = AuditEvent.model_construct(event_id=v, **base)
        attempt(f"LocalDirSink.write_intent(event_id={label})", lambda e2=e2: sink.write_intent(e2))
        sink.write_outcome(e2)
    try: sink.reconcile()
    except BaseException as e: rec("reconcile2 raised", e)
    # OSError that quotes a configured path holding the canary
    bad = tmp / ("file-" + C)
    bad.write_text("x")
    sink2 = LocalDirSink(bad / "audit")
    good = AuditEvent(**base)
    attempt("LocalDirSink(root under a FILE named canary).write_intent(valid event)", lambda: sink2.write_intent(good))
    logtext = logs.getvalue()
    results.append(("log output of local_dir probes (root logger, DEBUG)", "captured %d chars" % len(logtext), ["log"] if (C in logtext or W in logtext) else [], {"log": logtext[:200]} if (C in logtext) else {}))
    logging.getLogger().removeHandler(h)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# check-config via the CLI, one config folder per probe
src_cfg = Path(sys.argv[1]) / "tests/fixtures/config"
def check_config(name, mutate):
    d = Path(tempfile.mkdtemp(prefix="ev-cfg-"))
    try:
        shutil.copytree(src_cfg, d / "c")
        _cf = d / "c" / "config.yaml"; _cf.write_text(_cf.read_text().replace("{port}", "8080"))
        mutate(d / "c")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("AWS_", "VAULT_", "ANTHROPIC_"))}
        env["HADAVIN_CONFIG_DIR"] = str(d / "c")
        p = subprocess.run([sys.executable, "-m", "hadavin_sdk.cli", "check-config"], capture_output=True, text=True, env=env, cwd=sys.argv[1])
        out = p.stdout + p.stderr
        # the config dir itself must not hold the canary in its path, so any hit is from the content
        results.append((f"check-config: {name}", f"exit {p.returncode} first-line: {out.strip().splitlines()[0][:90] if out.strip() else ''}", ["stdout+stderr"] if (C in out or W in out or "made-up library says" in out) else [], {"out": out[-300:]} if (C in out or W in out) else {}))
    finally:
        shutil.rmtree(d, ignore_errors=True)

def setyaml(fname, fn):
    def m(c):
        p = c / fname; data = yaml.safe_load(p.read_text()); data = fn(data); p.write_text(yaml.safe_dump(data))
    return m
check_config("baseline (no change)", lambda c: None)
check_config("unknown top-level key = canary", setyaml("config.yaml", lambda d: {**d, C: 1}))
check_config("unknown top-level key = wordlike", setyaml("config.yaml", lambda d: {**d, W: 1}))
check_config("environment = canary", setyaml("config.yaml", lambda d: {**d, "environment": C}))
check_config("environment = libtext", setyaml("config.yaml", lambda d: {**d, "environment": LIB}))
check_config("route max_tokens = canary", setyaml("config.yaml", lambda d: {**d, "routes": {"default": {**d["routes"]["default"], "max_tokens": C}}}))
check_config("route price = libtext", setyaml("config.yaml", lambda d: {**d, "routes": {"default": {**d["routes"]["default"], "input_usd_per_mtok": LIB}}}))
check_config("route name = canary (route key)", setyaml("config.yaml", lambda d: {**d, "routes": {C: d["routes"]["default"]}}))
check_config("route name = wordlike", setyaml("config.yaml", lambda d: {**d, "routes": {W: d["routes"]["default"]}}))
check_config("systems base_url = libtext", setyaml("config.yaml", lambda d: {**d, "systems": {"fixture-records": {"base_url": LIB}}}))
check_config("backends.audit.dir = canary type error", setyaml("config.yaml", lambda d: {**d, "backends": {**d["backends"], "audit": {"kind": C, "dir": "audit"}}}))
check_config("agents: id = canary", setyaml("agents.yaml", lambda a: [{**a[0], "id": C}] + a[1:]))
check_config("agents: model_route = canary (matches nothing)", setyaml("agents.yaml", lambda a: [{**a[0], "model_route": C}] + a[1:]))
check_config("agents: model_route = wordlike (matches nothing)", setyaml("agents.yaml", lambda a: [{**a[0], "model_route": W}] + a[1:]))
check_config("agents: scope_allowed has canary", setyaml("agents.yaml", lambda a: [{**a[0], "scope_allowed": [C]}] + a[1:]))
check_config("agents: budget daily = libtext", setyaml("agents.yaml", lambda a: [{**a[0], "budget_usd": {"daily": LIB, "monthly": "10.00"}}] + a[1:]))
check_config("agents: unknown key = canary", setyaml("agents.yaml", lambda a: [{**a[0], C: 1}] + a[1:]))
check_config("principals file: canary key", setyaml("principals.yaml", lambda d: {**d, C: 1} if isinstance(d, dict) else d + [{"id": C}]))
def badyaml(c): (c / "chains.yaml").write_text("a: [" + C + "\n  : : {")
check_config("chains.yaml malformed YAML containing canary", badyaml)
def badutf(c): (c / "agents.yaml").write_bytes(b"- id: " + C.encode() + b"\xff\xfe\n")
check_config("agents.yaml bytes not UTF-8 with canary", badutf)
def promptpath(c):
    p = c / "agents.yaml"; a = yaml.safe_load(p.read_text()); a[0]["prompt_file"] = C + "/nope.md"; p.write_text(yaml.safe_dump(a))
check_config("agents prompt_file path = canary", promptpath)
def actionname(c):
    (c / "actions" / (C.lower() + ".yaml")).write_text("id: " + C + "\nbad: [")
check_config("actions/<canary>.yaml malformed", actionname)

width = 0
leaks = [r for r in results if r[2]]
print("TOTAL probes:", len(results), " canary-visible:", len(leaks))
print("\n== PROBES WHERE THE CANARY OR MADE-UP LIBRARY TEXT APPEARED ==")
for n, st, hits, ex in leaks:
    print(f"- {n} | {st} | surfaces: {hits}")
    for k, v in ex.items(): print(f"    {k}: {v!r}")
print("\n== ALL PROBES ==")
for n, st, hits, ex in results:
    print(f"{'SHOWN ' if hits else 'hidden'} | {n} | {st}")
