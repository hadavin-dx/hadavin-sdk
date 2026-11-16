"""Evidence probes for 82dd69c1 (record only; loopback, made-up data). Run from the worktree root with PYTHONPATH=<wt>/src:<wt>."""
import copy, gc, tempfile, time, pathlib, weakref, sys
import hadavin_sdk
print("hadavin_sdk file:", hadavin_sdk.__file__)
from pytest import MonkeyPatch
import tests.test_bindguard as T
from hadavin_sdk import standins
from hadavin_sdk.approvals import requests as R
from hadavin_sdk.approvals.requests import make_on_decided
from hadavin_sdk.runtime.agent_loop import Runtime

tmp = pathlib.Path(tempfile.mkdtemp(dir="/home/user/build/er-pdbind11-tmp"))
n = [0]
def fresh():
    n[0] += 1
    return T._built(tmp / f"b{n[0]}")
def refused(app, approvals):
    mp = MonkeyPatch()
    try:
        return "REFUSED" if T._refused_on_public_bind(app, approvals, mp, "") else "SERVED"
    finally:
        mp.undo()
def ask(app, rt=None):
    ap = T._approvals_with(app, make_on_decided({"rt": rt if rt is not None else T._core_runtime(app)}))
    return refused(app, ap)

mode = sys.argv[1]
if mode == "cost":
    print("\n== (6) pre-auth cost per request (ms), store scans, values charged")
    def timed(app, approvals, label):
        scans = []; charged = []
        store = app.approvals.store
        rc, rch = standins._check, standins._Budget.charge
        def chk(o, d, s, b):
            if o is store and d == 0: scans.append(1)
            return rc(o, d, s, b)
        def chg(self, nn): charged.append(nn); return rch(self, nn)
        standins._check = chk; standins._Budget.charge = chg
        try:
            t = time.perf_counter(); res = approvals.real_now(); ms = (time.perf_counter() - t) * 1000
        finally:
            standins._check = rc; standins._Budget.charge = rch
        print(f"{label}: {ms:.1f} ms | store scanned {len(scans)}x | values charged {sum(charged)} | result={res!r}"[:260])
    for rows in (1000, 2400):
        app = fresh(); T._fill_mixed(app.approvals.store, rows)
        ap = T._approvals_with(app, make_on_decided({"rt": T._core_runtime(app)}))
        for i in range(3): timed(app, ap, f"{rows} mixed rows run {i+1}")
        rt = T._core_runtime(app)
        t = time.perf_counter()
        for _ in range(1000): ok = R._runtime_ok(rt)
        print(f"   seal compare alone (_runtime_ok, no scan of rows) x1000 on {rows}-row store: {(time.perf_counter()-t):.3f} s total = {(time.perf_counter()-t):.3f} ms each, result={ok}")
    app = fresh(); ap = T._approvals_with(app, make_on_decided({"rt": T._core_runtime(app)}))
    big = [list(range(1000))] * 150
    app.approvals.store.extra = big; app.approvals.channel.extra = big; T._core_runtime(app).llm.extra = big
    for i in range(3): timed(app, ap, f"store+channel+runtime.llm 150000 values each run {i+1}")
    sys.exit(0)

print("\n== (7) hostile inputs on a sealed core runtime, serve on 0.0.0.0 (REFUSED = good, SERVED = believed)")
app = fresh(); rt = T._core_runtime(app); own = object.__getattribute__(rt, "__dict__"); hooks = own["hooks"]
print("hooks fields:", sorted(vars(hooks)))
print("hooks.tools keys:", list(hooks.tools), "| toolbox:", type(hooks.toolbox).__name__)
print("control (untouched):", ask(app))
# 1 assign into hooks.tools
hooks.tools["probe-tool"] = lambda a: "x"
print("1a hooks.tools['probe-tool'] = fn:", ask(app)); del hooks.tools["probe-tool"]
print("   after removing it again:", ask(app))
for k in list(hooks.tools):
    was = hooks.tools[k]; hooks.tools[k] = lambda a: "x"
    print(f"1b replace existing hooks.tools[{k!r}]:", ask(app)); hooks.tools[k] = was
old_tools = hooks.tools; hooks.tools = dict(old_tools)
print("1c hooks.tools field replaced by a copy dict:", ask(app)); hooks.tools = old_tools
# 2 toolbox member
tb = hooks.toolbox
if tb is None:
    print("2 toolbox is None in this fixture: member replacement not applicable; instead set hooks.toolbox to a new object:")
    hooks.toolbox = object(); print("2' hooks.toolbox = object():", ask(app)); hooks.toolbox = None
else:
    for f in sorted(vars(tb)):
        was = getattr(tb, f)
        try:
            setattr(tb, f, copy.copy(was) if was is not None else object())
            print(f"2 toolbox.{f} replaced by a copy/object:", ask(app))
        except Exception as e: print(f"2 toolbox.{f}: setup error {type(e).__name__}")
        finally:
            setattr(tb, f, was)
    print("2 control after restoring toolbox:", ask(app))
# 3 closure cells
for fname in ("post_card", "request_approval", "execute", "verify", "rollback", "hold_run_ids", "level_override"):
    fn = getattr(hooks, fname)
    cells = getattr(fn, "__closure__", None) or ()
    if not cells: print(f"3 hooks.{fname}: no closure cells ({type(fn).__name__})"); continue
    for i, c in enumerate(cells):
        try: was = c.cell_contents
        except ValueError: print(f"3 hooks.{fname} cell {i}: empty"); continue
        try:
            c.cell_contents = object() if not isinstance(was, (dict, list, set)) else type(was)()
            print(f"3 hooks.{fname} cell {i} ({type(was).__name__}) rewritten:", ask(app))
        except Exception as e: print(f"3 hooks.{fname} cell {i}: {type(e).__name__}")
        finally: c.cell_contents = was
print("3 control after restoring cells:", ask(app))
# 3b: the on_decided holder cell of the approvals object
# 4 _kinds
was = own["_kinds"]
own["_kinds"] = frozenset({"evil-kind"}); print("4a own['_kinds'] = other frozenset:", ask(app))
own["_kinds"] = frozenset(was) | {"extra"}; print("4b own['_kinds'] = was + one name:", ask(app))
own["_kinds"] = set(was); print("4c own['_kinds'] = a plain set with the same names:", ask(app))
class FS(frozenset):
    def __contains__(self, x): return True
own["_kinds"] = FS(was); print("4d own['_kinds'] = frozenset subclass, same names, own __contains__:", ask(app))
own["_kinds"] = was; print("4e restored:", ask(app))
Runtime._kinds = frozenset({"evil"})
print("4f class attribute Runtime._kinds put on the pinned class:", ask(app)); del Runtime._kinds
print("4g after deleting it:", ask(app))
rt_new = object.__new__(Runtime); object.__getattribute__(rt_new, "__dict__").update(own)
print("4h hand-built Runtime (object.__new__) with the same dict incl. _kinds:", ask(app, rt_new))
# 5 drop a sealed runtime, gc
print("5 seals now:", len(R._RUNTIME_SEALS))
app2 = fresh(); rt2 = T._core_runtime(app2); print("   after building a second app:", len(R._RUNTIME_SEALS))
ref = weakref.ref(rt2); h2 = ask(app2, rt2)
print("   second app asked while alive:", h2)
del rt2; app2.app.runtime = None if hasattr(app2.app, "runtime") and False else app2.app.runtime
import types
objs_before = len(R._RUNTIME_SEALS)
app3 = fresh(); r3 = T._core_runtime(app3); w3 = weakref.ref(r3); ap3 = T._approvals_with(app3, make_on_decided({"rt": r3}))
print("   third app, seals:", len(R._RUNTIME_SEALS))
del r3, ap3
try:
    del app3.app.runtime
except Exception as e:
    try: object.__delattr__(app3.app, "runtime")
    except Exception as e2: print("   could not delete app.runtime:", type(e2).__name__)
del app3
for _ in range(3): gc.collect()
print("   after dropping the third app and gc x3: runtime alive:", w3() is not None, "| seals:", len(R._RUNTIME_SEALS))
for _ in range(3): gc.collect()
print("   seals left (every other live app still holds its own):", len(R._RUNTIME_SEALS))
# id reuse: a hand-built runtime created after a collection must not be believed
hand = object.__new__(Runtime); object.__getattribute__(hand, "__dict__").update(own)
print("   hand-built runtime made after gc:", ask(app, hand))
print("   control, the real runtime still:", ask(app))
