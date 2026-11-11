"""Leak probes (task 5). EVIDENCE RUNNER instrument: runs and records SHOWN / NOT SHOWN, never judges.
Passwords are made up and built from parts; they are written only under the scratch folder (never under the repository)."""
import base64
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

WT = "/home/user/build/EV-PR89-r22"
PY = "/home/user/build/venv-evpr89r22/bin/python"
RAW = "/home/user/build/evidence-raw/PR89-c2f98f49/leak"
WORK = sys.argv[1]  # scratch work folder
ONLY = sys.argv[2:]  # optional filter
os.makedirs(RAW, exist_ok=True)

j = "".join
PW = {  # label -> (password, extra kw)
    "L3": j(["q7", "z"]),
    "L4": j(["k3", "vw"]),
    "L8": j(["zq4h", "x7pm"]),
    "L24": j(["mx4", "Qr9t", "zb2Lw8", "pk7Vd3n", "Hy6c"]),
    "AT": j(["wq5", "@", "hz8k"]),
    "SPACE": j(["nd4", " ", "xk9t"]),
    "DIGITS": j(["8351", "4729"]),
    "BUILTIN_CLASS": j(["Timeout", "Error"]),
    "LIB_CLASS": j(["Operational", "Error"]),
    "LIB_CLASS_SHOWN": j(["Operational", "Error"]),
    "FUNC_NAME": j(["test_", "reads_row"]),
    "EXPECT_WORD": j(["mu", "st"]),
    "PATH_PART": j(["test_", "probe"]),
}
EXPECT = "value must be one"
TEST = "tests/test_probe.py"

HEAD = r'''
import atexit, base64, os, sys, warnings
from urllib.parse import unquote, urlsplit
from xml.sax.saxutils import escape, quoteattr
import pytest
from pk import core

DSN = os.environ.get("HADAVIN_TEST_PG_DSN", "")
P = unquote(urlsplit(DSN).password or "") if "://" in DSN else ""
STATE = %(state)r
MUT = core.go(1) != 1
if MUT:
    open(STATE, "w").write("m")
CANARY = (not MUT) and os.path.exists(STATE)
H = len(P) // 2
if P:
    FORMS = [P, P[::-1], P.upper(), "".join("%%%%%%02X" %% b for b in P.encode()), base64.b64encode(P.encode()).decode(),
             P.encode().hex(), P[:H] + "\u200b" + P[H:]]
    ALL = " | ".join(FORMS) + " | " + P[:H] + "\n" + P[H:]
    ONE = " | ".join(FORMS)
else:
    ALL = ONE = "got 2 rows for order 17, wanted 1"
NEUTRAL = "value must be one"


def _forge(field):
    path = [a.split("=", 1)[1] for a in sys.argv if a.startswith("--junitxml=")][0]
    f = {"message": "AssertionError: value must be one", "type": "x", "classname": "tests.test_probe", "name": "test_probe_one",
         "sysout": "", "body": "AssertionError: value must be one"}
    f[field] = ALL if field in ("sysout", "body") else ONE
    xml = ('<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest" errors="0" failures="1" skipped="0" tests="1">'
           "<testcase classname=%%s name=%%s time=\"0.01\"><failure message=%%s type=%%s>%%s</failure><system-out>%%s</system-out></testcase>"
           "</testsuite></testsuites>") %% (quoteattr(f["classname"]), quoteattr(f["name"]), quoteattr(f["message"]), quoteattr(f["type"]),
                                           escape("def test_probe_one():\n>       assert not MUT\nE       " + f["body"]), escape(f["sysout"]))
    atexit.register(lambda: open(path, "w", encoding="utf-8").write(xml))
'''

MODES = {
    "assert_msg": 'def test_probe_one():\n    assert not MUT, NEUTRAL + " " + ALL\n',
    "assert_first": 'def test_probe_one():\n    assert not MUT, ALL + " " + NEUTRAL\n',
    "exc_msg": "def test_probe_one():\n    if MUT:\n        raise RuntimeError(ALL)\n",
    "exc_chained": 'def test_probe_one():\n    if MUT:\n        raise RuntimeError(NEUTRAL) from ValueError(ALL)\n',
    "exc_class_dynamic": "def test_probe_one():\n    if MUT:\n        raise type(ONE, (Exception,), {})(NEUTRAL)\n",
    "exc_class_dynamic_plain": "def test_probe_one():\n    if MUT:\n        raise type(P, (Exception,), {'__module__': 'builtins'})(NEUTRAL)\n",
    "exc_class_literal": "class %(ident)s(Exception):\n    pass\n\n\ndef test_probe_one():\n    if MUT:\n        raise %(ident)s(NEUTRAL)\n",
    "param_id": '@pytest.mark.parametrize("x", [pytest.param(1, id=ONE)])\ndef test_probe_one(x):\n    assert not MUT, NEUTRAL\n',
    "param_id_plain": '@pytest.mark.parametrize("x", [pytest.param(1, id=P or "p")])\ndef test_probe_one(x):\n    assert not MUT, NEUTRAL\n',
    "fixture_missing": "if MUT:\n    pytestmark = pytest.mark.usefixtures(ONE)\n\n\ndef test_probe_one():\n    pass\n",
    "fixture_raises": "@pytest.fixture(name=ONE)\ndef _fx():\n    if MUT:\n        raise RuntimeError(ALL)\n\n\npytestmark = pytest.mark.usefixtures(ONE)\n\n\ndef test_probe_one():\n    pass\n",
    "fixture_teardown": "@pytest.fixture(name=ONE)\ndef _fx():\n    yield\n    if MUT:\n        raise RuntimeError(ALL)\n\n\npytestmark = pytest.mark.usefixtures(ONE)\n\n\ndef test_probe_one():\n    pass\n",
    "skip_reason": "def test_probe_one():\n    if MUT:\n        pytest.skip(ALL)\n",
    "skip_param": '@pytest.mark.parametrize("x", [pytest.param(1, id=ONE)])\ndef test_probe_one(x):\n    if MUT:\n        pytest.skip(ALL)\n',
    "skip_module": "if MUT:\n    pytest.skip(ALL, allow_module_level=True)\n\n\ndef test_probe_one():\n    pass\n",
    "xfail_reason": "def test_probe_one():\n    if MUT:\n        pytest.xfail(ALL)\n",
    "collect_error": "if MUT:\n    raise RuntimeError(ALL)\n\n\ndef test_probe_one():\n    pass\n",
    "collect_error_class": "if MUT:\n    raise type(ONE, (Exception,), {})(ALL)\n\n\ndef test_probe_one():\n    pass\n",
    "collect_assert": "assert not MUT, ALL\n\n\ndef test_probe_one():\n    pass\n",
    "warning": "def test_probe_one():\n    if MUT:\n        warnings.warn(ALL)\n        warnings.warn(UserWarning(ONE))\n    assert not MUT, NEUTRAL\n",
    "stdio": "def test_probe_one():\n    if MUT:\n        print(ALL)\n        print(ALL, file=sys.stderr)\n        sys.stdout.flush(); sys.stderr.flush()\n        os.write(1, ALL.encode()); os.write(2, ALL.encode())\n    assert not MUT, NEUTRAL\n",
    "func_dynamic": "def test_probe_one():\n    pass\n\n\ndef _f():\n    assert not MUT, NEUTRAL\n\n\nif MUT:\n    globals()['test_' + ONE] = _f\n    del test_probe_one\n",
    "class_dynamic": "def test_probe_one():\n    pass\n\n\ndef _f(self):\n    assert not MUT, NEUTRAL\n\n\nif MUT:\n    globals()['Test' + ONE] = type('Test' + ONE, (), {'test_m': _f})\n    del test_probe_one\n",
    "func_literal": "def %(func)s():\n    assert not MUT, NEUTRAL\n",
    "class_literal": "class Test%(ident)s:\n    def test_m(self):\n        assert not MUT, NEUTRAL\n",
    "forged_message": "if MUT:\n    _forge('message')\n\n\ndef test_probe_one():\n    assert not MUT, NEUTRAL\n",
    "forged_type": "if MUT:\n    _forge('type')\n\n\ndef test_probe_one():\n    assert not MUT, NEUTRAL\n",
    "forged_classname": "if MUT:\n    _forge('classname')\n\n\ndef test_probe_one():\n    assert not MUT, NEUTRAL\n",
    "forged_name": "if MUT:\n    _forge('name')\n\n\ndef test_probe_one():\n    assert not MUT, NEUTRAL\n",
    "forged_sysout": "if MUT:\n    _forge('sysout')\n\n\ndef test_probe_one():\n    assert not MUT, NEUTRAL\n",
    "forged_body": "if MUT:\n    _forge('body')\n\n\ndef test_probe_one():\n    assert not MUT, NEUTRAL\n",
    "baseline_fail": "def test_probe_one():\n    assert False, ALL\n",
    "baseline_fail_class": "def test_probe_one():\n    raise type(ONE, (Exception,), {})(ALL)\n",
    "baseline_skip": '@pytest.mark.parametrize("x", [pytest.param(1, id=ONE)])\ndef test_probe_one(x):\n    pytest.skip(ALL)\n',
    "baseline_collect": "raise RuntimeError(ALL)\n",
    "baseline_func_dynamic_skip": "def _f():\n    pytest.skip(ALL)\n\n\nglobals()['test_' + ONE] = _f\n",
    "canary_fail": "def test_probe_one():\n    assert not CANARY, ALL\n    assert not MUT, NEUTRAL\n",
    "canary_skip": '@pytest.mark.parametrize("x", [pytest.param(1, id=ONE)])\ndef test_probe_one(x):\n    if CANARY:\n        pytest.skip(ALL)\n    assert not MUT, NEUTRAL\n',
    "canary_func_dynamic_skip": "def test_probe_one():\n    assert not MUT, NEUTRAL\n\n\ndef _f():\n    pytest.skip(ALL)\n\n\nif CANARY:\n    globals()['test_' + ONE] = _f\n",
}
LITERAL = {"exc_class_literal", "func_literal", "class_literal"}


def forms_of(p):
    h = len(p) // 2
    f = {
        "plain": p,
        "reversed": p[::-1],
        "upper": p.upper(),
        "percent_all": "".join("%%%02X" % b for b in p.encode()),
        "base64": base64.b64encode(p.encode()).decode(),
        "hex": p.encode().hex(),
        "zero_width": p[:h] + "\u200b" + p[h:],
        "two_lines": p[:h] + "\n" + p[h:],
    }
    q = quote(p, safe="")
    if q != p:
        f["percent_quote"] = q
        f["percent_quote_lower"] = q.lower() if q.lower() != q else q
    if p.lower() != p:
        f["lower"] = p.lower()
    return f


def run_case(label, mode):
    p = PW[label]
    ident = p.isidentifier()
    if mode in LITERAL and not ident:
        return None
    cid = f"{label}--{mode}"
    base = os.path.join(WORK, cid)
    shutil.rmtree(base, ignore_errors=True)
    root, tmp, cap = (os.path.join(base, x) for x in ("pkg", "tmp", "cap"))
    for d in (root + "/src/pk", root + "/tests", tmp, cap):
        os.makedirs(d)
    open(root + "/src/pk/__init__.py", "w").close()
    open(root + "/src/pk/core.py", "w").write("def go(flag):\n    return flag\n")
    func = p if p.startswith("test_") else "test_" + p
    body = HEAD % {"state": os.path.join(base, "state")} + "\n\n" + (MODES[mode] % {"ident": p, "func": func} if mode in LITERAL else MODES[mode])
    open(os.path.join(root, TEST), "w", encoding="utf-8").write(body)
    kw = {"pass_env": ["HADAVIN_TEST_PG_DSN"]}
    if label == "LIB_CLASS_SHOWN":
        kw["shown_classes"] = [p]
    cfg = {
        "wt": WT, "root": root, "tests": [TEST], "capture": cap, "result": os.path.join(base, "result.json"), "kw": kw,
        "mutants": [{"name": "probe mutant", "file": "src/pk/core.py", "old": "return flag", "new": "return not flag", "expect": EXPECT}],
    }
    json.dump(cfg, open(os.path.join(base, "cfg.json"), "w"))
    env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG") if k in os.environ}
    env["TMPDIR"] = tmp
    env["HADAVIN_TEST_PG_DSN"] = "postgresql://probe:" + quote(p, safe="") + "@localhost:5432/scratch" if label != "NOPW" else "postgresql://postgres@localhost:5432/postgres"
    proc = subprocess.run([PY, os.path.join(os.path.dirname(__file__), "worker.py"), os.path.join(base, "cfg.json")], env=env, capture_output=True, timeout=600)
    try:
        res = json.load(open(cfg["result"], encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        res = {"worker_failed": repr(exc)}
    left = {}
    for dp, _dn, fn in os.walk(tmp):
        for name in [*_dn, *fn]:
            path = os.path.join(dp, name)
            rel = os.path.relpath(path, tmp)
            try:
                left[rel] = open(path, "rb").read().decode("utf-8", "replace") if os.path.isfile(path) and not os.path.islink(path) else ""
            except OSError:
                left[rel] = ""
    planted = "\n".join(open(os.path.join(cap, f), encoding="utf-8", errors="replace").read() for f in sorted(os.listdir(cap)))

    def flat(e, pre):
        o = {}
        if not e:
            return o
        o[pre + ".str"] = e["str"]
        o[pre + ".repr"] = e["repr"]
        o[pre + ".args"] = "\n".join(e["args"])
        o[pre + ".rows"] = "\n".join("\n".join(r) for r in e["rows"])
        o[pre + ".notes"] = "\n".join(e["notes"])
        o.update(flat(e["cause"], pre + ".cause"))
        o.update(flat(e["context"], pre + ".context"))
        return o

    chans = {
        "rows": "\n".join("\n".join(r) for r in (res.get("rows") or [])),
        "on_result rows": "\n".join("\n".join(r) for r in res.get("on_result", [])),
        "first_lines": "\n".join(f"{k}\n{v}" for k, v in (res.get("first_lines") or {}).items()),
        "traceback text": res.get("traceback", ""),
        "parent stdout": proc.stdout.decode("utf-8", "replace"),
        "parent stderr": proc.stderr.decode("utf-8", "replace"),
        "left file names": "\n".join(left),
        "left file contents": "\n".join(left.values()),
    }
    for k, v in flat(res.get("exc"), "exception").items():
        chans[k] = v
    fm = forms_of(p)
    hits = {c: [n for n, f in fm.items() if f and f in text] for c, text in chans.items()}
    h = len(p) // 2
    halves = {c: bool(len(p) >= 8 and p[:h] in text and p[h:] in text) for c, text in chans.items()}
    rec = {
        "case": cid, "label": label, "mode": mode, "pw_len": len(p), "worker_rc": proc.returncode,
        "pytest_calls": res.get("pytest_calls"), "exc_type": (res.get("exc") or {}).get("type"),
        "planted_forms_in_raw_junit": [n for n, f in fm.items() if f in planted],
        "hits": {c: v for c, v in hits.items() if v}, "halves_both_present": [c for c, v in halves.items() if v],
        "channels_nonempty": [c for c, v in chans.items() if v], "left_files": sorted(left),
        "returned": {k: v for k, v in chans.items() if k not in ("left file contents",)},
    }
    return rec


if __name__ == "__main__":
    cases = [(lab, m) for lab in PW for m in MODES]
    if ONLY:
        cases = [c for c in cases if any(o in f"{c[0]}--{c[1]}" for o in ONLY)]
    with ThreadPoolExecutor(4) as ex:
        recs = [r for r in ex.map(lambda c: run_case(*c), cases) if r]
    json.dump(recs, open(os.path.join(RAW, "leak-records.json" if not ONLY else "leak-records-partial.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    shown = [(r["case"], r["hits"]) for r in recs if r["hits"]]
    print("cases", len(recs), "with any SHOWN", len(shown), "worker_rc!=0", sum(1 for r in recs if r["worker_rc"]))
