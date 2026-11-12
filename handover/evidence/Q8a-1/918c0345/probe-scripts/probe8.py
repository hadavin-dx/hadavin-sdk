"""EVIDENCE probe (brief item 8, extra): where a planted marker appears for (a) signer_vault status, (b) tick step failures
(message holds a marker; step, save and probe failures; _each and purge hook), (c) the injection detector log line.
Records, never judges. Usage: python probe8.py <src-dir> <out.json>"""
import sys, json, logging, traceback
from datetime import UTC, datetime
from types import SimpleNamespace
M = "zq" + "-probe-" + "mk4417"; S = "Zq9x" + "-Pw-" + "4417"; H = "9f" * 16
MARKS = (M, S, H)
class Hd(logging.Handler):
    def __init__(s): super().__init__(); s.buf = []
    def emit(s, r): s.buf.append(r.getMessage())
rows = []
def where(group, label, fn):
    h = Hd(); lg = logging.getLogger(); lg.addHandler(h); old = lg.level; lg.setLevel(logging.DEBUG)
    ret = None; exc_txt = ""; kind = "returned"
    try: ret = fn()
    except BaseException as e:
        kind = "raised " + type(e).__name__
        seen=set(); stack=[e]; parts=[]
        while stack:
            x=stack.pop()
            if x is None or id(x) in seen: continue
            seen.add(id(x)); parts += [str(x), repr(x), str(x.args)]; stack += [x.__cause__] + ([] if x.__suppress_context__ else [x.__context__])
        parts.append("".join(traceback.format_exception(e))); exc_txt = "\n".join(parts)
    lg.removeHandler(h); lg.setLevel(old)
    log = "\n".join(h.buf); rt = json.dumps(ret, default=str) if ret is not None else ""
    for i, m in enumerate(MARKS):
        rows.append(dict(group=group, label=label, marker=i, outcome=kind, in_exc=m in exc_txt, in_log=m in log, in_returned=m in rt))
    return ret
# (a) signer_vault status
from hadavin_sdk.audit.signer_vault import VaultTransitSigner
class V:
    def __init__(s, st): s.st = st
    def authed(s, *a, **k): return s.st, {}
for i, m in enumerate(MARKS):
    for st_label, st in (("text status", m), ("bytes", m.encode()), ("float", 503.5), ("bool", True), ("int 503", 503)):
        sg = VaultTransitSigner(V(m if st_label == "text status" else st), "transit", "key-name", 1)
        where("signer_vault._call", f"status={st_label} (marker idx {i} when text)", lambda sg=sg: sg._call("GET", "keys/key-name"))
# (b) tick
from hadavin_sdk.runtime import tick
tick._now = lambda ctx: datetime(2030, 1, 1, tzinfo=UTC)
class St:
    def __init__(s, fail_get=None, fail_save=None): s.saved=[]; s.fg=fail_get; s.fs=fail_save
    def get_tick_state(s, n):
        if s.fg: raise s.fg
    def save_tick_state(s, st):
        if s.fs: raise s.fs
        s.saved.append(st)
def ctx(st): return SimpleNamespace(app=SimpleNamespace(store=st), now=lambda: datetime(2030,1,1,tzinfo=UTC))
for i, m in enumerate(MARKS):
    for ename, ex in (("ValueError", ValueError(m)), ("RuntimeError chained from marker error", None), ("OSError", OSError(m)), ("KeyError", KeyError(m))):
        def step_fn(c, ex=ex, ename=ename, m=m):
            if ex is None:
                try: raise ValueError(m)
                except ValueError as inner: raise RuntimeError("outer") from inner
            raise ex
        st = St()
        r = where("tick._run_step step raises", f"{ename} marker={i}", lambda st=st: tick._run_step(ctx(st), tick.TickStep("s", 0, step_fn)))
        rows.append(dict(group="tick._run_step step raises", label=f"{ename} marker={i} -> stored last_error", marker=i, outcome=str(r), in_exc=False, in_log=False, in_returned=m in (st.saved[0].last_error or "") if st.saved else False))
    st = St(fail_save=ValueError(m)); where("tick._run_step save raises", f"marker={i}", lambda st=st: tick._run_step(ctx(st), tick.TickStep("s", 0, lambda c: None)))
    st = St(fail_get=ValueError(m)); where("tick._run_step get_tick_state raises", f"marker={i}", lambda st=st: tick._run_step(ctx(st), tick.TickStep("s", 0, lambda c: None)))
    def each_fn(item, m=m): raise ValueError(m)
    where("tick._each item raises", f"marker={i}", lambda each_fn=each_fn: tick._each([1, 2], each_fn, "what"))
    def raiser(item, m=m): raise tick.StaleState(m)
    where("tick._each CAS loser", f"marker={i}", lambda raiser=raiser: tick._each([1], raiser, "what"))
    # purge hold hook
    keep = SimpleNamespace(held_tool_calls_max_days=1, hold_labelled=True, tool_calls_days=1)
# (c) injection detector log line
from hadavin_sdk.guard.injection import injection_check
for i, m in enumerate(MARKS):
    class Broken:
        backend = "broken"
        def check(s, text, source): raise ValueError(m)
    where("injection_check detector raises", f"exc text marker={i}", lambda Broken=Broken: injection_check(Broken(), "plain text", "src"))
    class Broken2:
        backend = m
        def check(s, text, source): raise ValueError("x")
    where("injection_check detector.backend=marker", f"marker={i}", lambda Broken2=Broken2: injection_check(Broken2(), "plain text", "src"))
import collections
print("module:", tick.__file__)
for r in rows:
    if r["in_exc"] or r["in_log"] or r["in_returned"]: print("SHOWS", r["group"], "|", r["label"], "| marker", r["marker"], "|", r["outcome"], "| exc/tb", r["in_exc"], "log", r["in_log"], "returned", r["in_returned"])
c = collections.Counter((r["group"], r["in_exc"] or r["in_log"] or r["in_returned"]) for r in rows)
print("rows", len(rows)); [print(" ", g, "shows=" + str(s), n) for (g, s), n in sorted(c.items())]
json.dump(rows, open(sys.argv[1], "w"), indent=0)
