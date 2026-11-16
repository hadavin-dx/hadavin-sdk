"""EVIDENCE probe (own script, outside the repo). For each channel, record whether a canary value reaches any output."""
import io, json, os, sys, shutil, subprocess, tempfile, logging, traceback, pickle, copy
from pathlib import Path

WT = Path(sys.argv[1]); OUT = Path(sys.argv[2])
FIX = WT / "tests" / "fixtures"
# canaries built from parts
CAN = "zq" + "canary" + "7" + "x" + "kw"          # word-like lower-case
CAP = "Zq" + "Canary" + "9" + "Kw"                 # capital letter
LIB = "Input should be " + "'" + "zqlib" + "text" + "'" + " [type=literal_error, input_value='" + CAN + "', input_type=str]"
PATHLIKE = "/etc/" + CAN + "/x"
HEX = "a1b2c3d4" * 6
VALUES = {"canary": CAN, "capital": CAP, "libtext": LIB, "pathlike": PATHLIKE, "hex48": HEX, "long5120": CAN * 800, "newline": CAN + "\nx"}
NEEDLES = [CAN, CAP.lower(), "zqlib" + "text"]
class S1(str):
    def __str__(self): return "SUBCLASS-STR-" + CAN
    def __repr__(self): return "SUBCLASS-REPR-" + CAN
class S2(str):
    def __eq__(self, o): return True
    __hash__ = str.__hash__
SUBS = {"S1_str_override": S1(CAN), "S2_eq_override": S2(CAN)}
res = []
def rec(chan, name, text):
    t = text if isinstance(text, str) else repr(text)
    hit = [n for n in NEEDLES if n in t.lower() or n in t] + (["S1MARK"] if "SUBCLASS-" in t else [])
    res.append({"channel": chan, "value": name, "reaches_output": bool(hit), "needles": hit, "sample": t[:160].replace(CAN, "<canary>")})

from hadavin_sdk import errors
from hadavin_sdk.models import AuditEvent
allv = dict(VALUES); allv.update(SUBS)
for n, v in allv.items():
    rec("errors.shown_id", n, errors.shown_id(v))
    rec("errors.shown_name(no loaded)", n, errors.shown_name(v))
    rec("errors.shown_name(loaded=[v])", n, errors.shown_name(v, [v]))
    try:
        with errors.loaded_ids([v]):
            rec("errors.shown_name(loaded_ids ctx)", n, errors.shown_name(v))
    except Exception as e:
        rec("errors.shown_name(loaded_ids ctx) EXC", n, type(e).__name__ + str(e))
    # AuditEvent event_id via ctor, model_validate, model_validate_json
    base = dict(run_id="run-" + "0"*32, domain="d", operation="o", principal="p", source="s")
    def chk(label, fn):
        try:
            fn(); res.append({"channel": label, "value": n, "reaches_output": False, "needles": [], "sample": "accepted (no error)"})
        except BaseException as e:
            blob = []
            blob.append(str(e)); blob.append(repr(e)); blob.append("".join(traceback.format_exception(e)))
            if hasattr(e, "errors"):
                try:
                    blob.append(repr(e.errors()))
                    blob.append(repr(e.errors(include_input=True)))
                    blob.append(repr(e.errors(include_url=False, include_context=True)))
                    blob.append(e.json())
                except BaseException as e2: blob.append("errors()/json() raised " + type(e2).__name__)
            blob.append(repr(getattr(e, "args", ""))); blob.append(repr(getattr(e, "__cause__", ""))); blob.append(repr(getattr(e, "__context__", "")))
            blob.append(repr(e.__dict__))
            rec(label, n, " || ".join(blob))
    chk("AuditEvent(event_id=) ctor", lambda: AuditEvent(event_id=v, **base))
    chk("AuditEvent.model_validate", lambda: AuditEvent.model_validate({"event_id": v, **base}))
    if isinstance(v, str) and type(v) is str:
        chk("AuditEvent.model_validate_json", lambda: AuditEvent.model_validate_json(json.dumps({"event_id": v, **base})))
        chk("AuditEvent.model_validate_strings", lambda: AuditEvent.model_validate_strings({"event_id": v, **base}))
    # local_dir
    from hadavin_sdk.audit.local_dir import LocalDirSink
    d = Path(tempfile.mkdtemp(prefix="pb-", dir=os.environ.get("TMPDIR")))
    sink = LocalDirSink(d)
    ev = AuditEvent(**base)
    try:
        object.__setattr__(ev, "event_id", v)  # an event built without the model check
    except BaseException as e: rec("setattr event_id", n, str(e))
    for meth in ("write_intent", "write_outcome"):
        logs = io.StringIO(); h = logging.StreamHandler(logs); logging.getLogger().addHandler(h); logging.getLogger().setLevel(logging.DEBUG)
        try:
            r = getattr(sink, meth)(ev); out = "returned " + repr(r)
        except BaseException as e:
            out = "".join(traceback.format_exception(e)) + repr(e) + str(e)
        logging.getLogger().removeHandler(h)
        rec("LocalDirSink." + meth + " (+log)", n, out + logs.getvalue())
    try: r = sink.reconcile(); out = "reconcile returned " + repr(r)
    except BaseException as e: out = "".join(traceback.format_exception(e))
    rec("LocalDirSink.reconcile", n, out)
    # root below a file whose name holds the value
    if type(v) is str and "/" not in v and "\n" not in v and len(v) < 200:
        f = d / v; f.write_text("x")
        s2 = LocalDirSink(f / "sub")
        try: s2.write_intent(AuditEvent(**base)); out = "ok"
        except BaseException as e: out = "".join(traceback.format_exception(e)) + str(e)
        rec("LocalDirSink root-under-file name", n, out)
    shutil.rmtree(d, ignore_errors=True)

# config models: pydantic errors()/json() with configured name in various fields
from hadavin_sdk import config as C
import yaml
for n, v in allv.items():
    if not isinstance(v, str): continue
    for fname, kwargs in (("Route.model_id", dict(model_id=v, input_usd_per_mtok="1", output_usd_per_mtok="1", max_tokens=5)),
                          ("Route.max_tokens", dict(model_id="m", input_usd_per_mtok="1", output_usd_per_mtok="1", max_tokens=v)),
                          ("Route.unknown_key", {v: 1, "model_id": "m", "input_usd_per_mtok": "1", "output_usd_per_mtok": "1", "max_tokens": 5}),
                          ("System.base_url", None)):
        try:
            if fname == "System.base_url": C.System(base_url=v)
            else: C.Route(**kwargs)
            res.append({"channel": "config." + fname, "value": n, "reaches_output": False, "needles": [], "sample": "accepted"})
        except BaseException as e:
            blob = [str(e), repr(e), "".join(traceback.format_exception(e))]
            if hasattr(e, "errors"):
                try: blob += [repr(e.errors()), repr(e.errors(include_input=True)), e.json()]
                except BaseException as e2: blob.append("errors()/json() raised " + type(e2).__name__)
            rec("config." + fname + " (str/errors()/json())", n, " || ".join(blob))

# check-config on a copy of the fixture with the canary in places
def cc(label, mutate):
    d = Path(tempfile.mkdtemp(prefix="cc-", dir=os.environ.get("TMPDIR")))
    shutil.copytree(FIX / "config", d / "config")
    cfgp = d / "config" / "config.yaml"
    cfgp.write_text(cfgp.read_text().replace("{port}", "1"))
    try: mutate(d / "config")
    except BaseException as e: res.append({"channel": "check-config:" + label, "value": "SETUP", "reaches_output": False, "needles": [], "sample": "setup failed " + type(e).__name__}); return
    p = subprocess.run([os.environ["VIRTUAL_ENV"] + "/bin/hadavin-sdk", "--config", str(d / "config"), "check-config"], capture_output=True, text=True, env={**os.environ, "HADAVIN_DEBUG": "0"})
    rec("check-config:" + label + f" (rc={p.returncode})", "stdout+stderr", p.stdout + p.stderr)
    p = subprocess.run([os.environ["VIRTUAL_ENV"] + "/bin/hadavin-sdk", "--config", str(d / "config"), "check-config"], capture_output=True, text=True, env={**os.environ, "HADAVIN_DEBUG": "1"})
    rec("check-config:" + label + f" DEBUG=1 (rc={p.returncode})", "stdout+stderr", p.stdout + p.stderr)
    shutil.rmtree(d, ignore_errors=True)
def sub_in(fn, old, new):
    def m(cd):
        t = (cd / fn).read_text(); assert old in t, (fn, old); (cd / fn).write_text(t.replace(old, new, 1))
    return m
for vn in ("canary", "capital", "libtext", "pathlike", "hex48"):
    v = VALUES[vn].replace('"', "").replace("\n", " ")
    cc(f"{vn}: agent id in agents.yaml", sub_in("agents.yaml", "id: test-agent", f'id: "{v}"'))
    cc(f"{vn}: model_route name", sub_in("agents.yaml", "model_route: default", f'model_route: "{v}"'))
    cc(f"{vn}: unknown top-level key", lambda cd, v=v: (cd / "config.yaml").write_text((cd / "config.yaml").read_text() + f'\n"{v}": 1\n'))
    cc(f"{vn}: tool name in scope_allowed", sub_in("agents.yaml", "scope_allowed: [lookup_record,", f'scope_allowed: ["{v}", lookup_record,'))
    cc(f"{vn}: prompt_file path", sub_in("agents.yaml", "prompt_file: prompts/test-agent.md", f'prompt_file: "prompts/{v}.md"'))
    cc(f"{vn}: non-int max_steps", sub_in("agents.yaml", "max_steps: 4", f'max_steps: "{v}"'))
cc("malformed yaml with canary", lambda cd: (cd / "agents.yaml").write_text("- id: [" + CAN + "\n  : : {\n"))
cc("non-utf8 bytes + canary", lambda cd: (cd / "agents.yaml").write_bytes(b"- id: " + CAN.encode() + b"\xff\xfe\n"))
# an action file name
def act(cd):
    (cd / "actions" / (CAN + ".yaml")).write_text("not: [valid")
cc("action file name holds canary", act)
cc("baseline (no change)", lambda cd: None)
Path(OUT).write_text(json.dumps(res, indent=1))
bad = [r for r in res if r["reaches_output"]]
print("probes:", len(res), "reaching output:", len(bad))
for r in bad: print("REACHES", r["channel"], r["value"], "|", r["sample"][:100])
