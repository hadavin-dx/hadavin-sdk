"""Worker: one run_mutants call; writes everything the tool returned/raised to a JSON file. EVIDENCE RUNNER instrument (records only)."""
import json
import os
import shutil
import sys
import traceback

cfg = json.load(open(sys.argv[1], encoding="utf-8"))
WT = cfg["wt"]
sys.path.insert(0, WT)
sys.path.insert(0, WT + "/src")
import tools.mutation_runner as mr  # noqa: E402

calls = {"n": 0}
cap = cfg.get("capture")
_orig = mr._pytest


def _spy(cwd, tests, junit, timeout, **kw):
    rc = _orig(cwd, tests, junit, timeout, **kw)
    calls["n"] += 1
    if cap:
        try:
            shutil.copy(junit, os.path.join(cap, f"junit-{calls['n']}.xml"))
        except OSError:
            pass
    return rc


mr._pytest = _spy

if cfg.get("fake_environ") is not None:  # simulate values the OS cannot hold (NUL, bytes, None)
    fe = dict(os.environ)
    for k, v in cfg["fake_environ"].items():
        fe[k] = v["bytes"].encode("latin-1") if isinstance(v, dict) and "bytes" in v else v
    mr.os.environ = fe  # the tool reads os.environ through its own ``os`` name (same module object: restored by process exit)


def conv(spec):
    if isinstance(spec, dict) and "__bytes__" in spec:
        return spec["__bytes__"].encode("latin-1")
    if isinstance(spec, dict) and "__tuple__" in spec:
        return tuple(conv(x) for x in spec["__tuple__"])
    if isinstance(spec, dict) and "__set__" in spec:
        return set(conv(x) for x in spec["__set__"])
    if isinstance(spec, dict) and "__int__" in spec:
        return spec["__int__"]
    if isinstance(spec, list):
        return [conv(x) for x in spec]
    return spec


out = {"rows": None, "on_result": [], "first_lines": None, "exc": None}
first_lines = {}
mutants = [mr.Mutant(**m) for m in cfg.get("mutants", [])]
kw = {k: conv(v) for k, v in cfg.get("kw", {}).items()}


def chain(exc, depth=0):
    if exc is None or depth > 5:
        return None
    d = {
        "type": type(exc).__name__,
        "str": str(exc),
        "repr": repr(exc),
        "args": [repr(a) for a in exc.args],
        "rows": [[str(x) for x in r] + [repr(r)] for r in getattr(exc, "rows", ())],
        "notes": list(getattr(exc, "__notes__", [])),
        "cause": chain(exc.__cause__, depth + 1),
        "context": chain(exc.__context__, depth + 1),
        "suppress_context": exc.__suppress_context__,
    }
    return d


try:
    rows = mr.run_mutants(
        cfg["root"], mutants, cfg["tests"], extra_dirs=(), timeout=120,
        on_result=lambda r: out["on_result"].append([str(x) for x in r] + [repr(r)]),
        first_lines=first_lines, **kw,
    )
    out["rows"] = [[str(x) for x in r] + [repr(r)] for r in rows]
except BaseException as exc:  # noqa: BLE001 - record everything
    out["exc"] = chain(exc)
    out["traceback"] = "".join(traceback.format_exception(exc, chain=True))
out["first_lines"] = dict(first_lines)
out["pytest_calls"] = calls["n"]
json.dump(out, open(cfg["result"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
