"""Mutation pass over live_l2/check_invariants.py. Works on git-free copies of /tmp/dpld-l2e (one per worker); each
mutant is applied, the two live_l2 test files run (-x), then the file is restored in a `finally`. Never touches the
source tree. Usage: python L2e-mutate.py OUT.json"""
import json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SRC = Path("/tmp/dpld-l2e")
TESTS = ["tests/test_live_l2_tools.py", "tests/test_live_l2_e.py"]
M = []  # (name, old, new)
def m(name, old, new): M.append((name, old, new))

# whole check forced green
for n in range(1, 8):
    m(f"check {n} forced ok", "    bad = sorted(set(offenders))\n", f"    bad = sorted(set(offenders))\n    ok = ok or n == {n}\n")
# check 1 terms
for t in ("lost", "mismatch", "short", "stale", "sorted(set(foreign))", "other_run", "by_list", "by_ids"):
    old = "    bad = lost + mismatch + short + stale + sorted(set(foreign)) + other_run + by_list + by_ids\n"
    parts = ["lost", "mismatch", "short", "stale", "sorted(set(foreign))", "other_run", "by_list", "by_ids"]
    new = "    bad = " + " + ".join(p if p != t else "[]" for p in parts) + "\n"
    m(f"c1 drop {t}", old, new)
m("c1 foreign-id off", 'foreign += [f"foreign-id:', 'foreign += [] and [f"foreign-id:')
m("c1 foreign-receipt off", 'foreign += [f"foreign-receipt:', 'foreign += [] and [f"foreign-receipt:')
m("c1 unacked ignored mismatch", 'if acked and key in receipts and r.get("receipt_id") is not None and r["receipt_id"] != receipts[key]:', 'if False:')
# check 2
old = "        total == len(leads)\n        and len(followups) == len(leads)\n        and not open_ids\n        and not no_verdict\n        and not new_no_lead\n        and not count_bad\n        and not in_review\n        and not unexplained\n"
for label, repl in [("sum", "        True\n        and len(followups) == len(leads)\n"), ("rows", "        total == len(leads)\n        and True\n")]:
    tail = "        and not open_ids\n        and not no_verdict\n        and not new_no_lead\n        and not count_bad\n        and not in_review\n        and not unexplained\n"
    m(f"c2 drop {label}", old, repl + tail)
for t in ("open_ids", "no_verdict", "new_no_lead", "count_bad", "in_review", "unexplained"):
    m(f"c2 drop {t}", f"        and not {t}\n", "        and True\n") if False else None
    m(f"c2 drop {t}", f"        and not {t}\n" if t != "unexplained" else "        and not unexplained\n    )\n", "        and True\n" if t != "unexplained" else "        and True\n    )\n")
m("c2 no_row dropped", "no_row + open_ids + no_verdict", "open_ids + no_verdict")
m("c2 foreign-lead off", 'unexplained += [f"foreign-lead:{e}"', 'unexplained += [] and [f"foreign-lead:{e}"')
m("c2 no-lead off", 'unexplained = [f"no-lead:{e}"', 'unexplained = [] and [f"no-lead:{e}"')
# check 3
terms3 = ["doubled", "doubled_to", "stray", "lost_mail", "unexpected", "unattributed", "over", "wrong_to", "no_reason", "not_sent_healthy", "evidence"]
old3 = "    bad = (\n" + "".join(("        " if i == 0 else "        + ") + t + "\n" for i, t in enumerate(terms3)) + "    )\n"
for t in terms3:
    new3 = "    bad = " + " + ".join(p if p != t else "[]" for p in terms3) + "\n"
    m(f"c3 drop {t}", old3, new3)
m("c3 ceiling unknown off", 'over.append("ceiling:unknown")', "pass")
m("c3 ceiling failed off", 'over.append("ceiling:failed")', "pass")
m("c3 catcher evidence off", 'evidence.append("no-catcher-evidence")', "pass")
m("c3 min unknown off", 'evidence.append("too-few-unknown")', "pass")
m("c3 quiet window off", "            evidence += [\n                f\"mail-while-down", "            evidence += [] and [\n                f\"mail-while-down")
m("c3 healthy off", "not_sent_healthy.append(", "(lambda x: None)(")
m("c3 case-sensitive recipient", "[a.lower() for a in str(m.get(\"to\")).split(\",\") if a] != [addresses[str(m.get(\"send_key\"))].lower()]", "[a for a in str(m.get(\"to\")).split(\",\") if a] != [addresses[str(m.get(\"send_key\"))]]")
m("c3 failed reasons any", "if followups[lid][0] == \"failed\" and reasons[lid][0] in MESSAGE_FAILED_ERRORS", "if followups[lid][0] == \"failed\"")
m("c3 unknown reasons any", "unattributed = [lid for lid in unknown_with_mail if reasons[lid][0] not in AMBIGUOUS_ERRORS] + [", "unattributed = [] and [lid for lid in unknown_with_mail if reasons[lid][0] not in AMBIGUOUS_ERRORS] + [")
m("c3 per-recipient count off", "doubled_to = [f\"to:{a}\" for a, n in per_to.items() if n > 1]", "doubled_to = []")
# check 4
terms4 = ["missing", "extra", "twice", "not_leads", '[f"sent-without-crm:{lid}" for lid in sent_no_crm]']
old4 = '    bad = missing + extra + twice + not_leads + [f"sent-without-crm:{lid}" for lid in sent_no_crm]\n'
for t in terms4:
    m(f"c4 drop {t[:12]}", old4, "    bad = " + " + ".join(p if p != t else "[]" for p in terms4) + "\n")
m("c4 unknown allowance off", "unknown = {lid for lid, (s, d, _) in followups.items() if d == CRM_INTENT_MARK or s == \"unknown\"} - done", "unknown = set()")
# check 5
m("c5 over off", "not over and not faults", "not faults")
m("c5 faults off", "not over and not faults", "not over")
for f_old in ['faults.append("no-model-calls")', 'faults += [f"never-asked:{lid}"', 'faults.append("model-fault-not-seen")', 'faults.append("too-few-non-200-results")', 'faults += [f"asked-twice:{lid}"', 'faults += [f"asked-after-answer:{lid}"', 'f"too-many-failed-calls:{lid}"']:
    if f_old.startswith("faults.append"):
        m(f"c5 off {f_old[15:35]}", f_old, "pass")
    elif f_old.startswith("faults +="):
        m(f"c5 off {f_old[10:30]}", f_old, f_old.replace("faults += [", "faults += [] and ["))
    else:
        m("c5 off too-many-failed", "            f\"too-many-failed-calls:{lid}\" for lid, n in down_per_lead.items() if n > expect.max_down_calls_per_lead", "            f\"x{lid}\" for lid, n in down_per_lead.items() if False")
m("c5 down modes incomplete", 'MODEL_DOWN_MODES = frozenset({"timeout", "rate_limit", "malformed_json", "malformed_label", "refusal", "server_error"})', 'MODEL_DOWN_MODES = frozenset({"timeout", "rate_limit", "malformed_json", "refusal", "server_error"})')
m("c5 arrivals not preferred", "return arrivals or [r for r in model_rows if \"event\" not in r]", "return [r for r in model_rows if \"event\" not in r]")
m("c5 again ignores arrival", 'if event in ("arrival", None) and lead in answered:', 'if event is None and lead in answered:')
# check 6
m("c6 ceiling off", "ok = ceiling is None or rate <= ceiling", "ok = True")
m("c6 ceiling strict", "ok = ceiling is None or rate <= ceiling", "ok = ceiling is None or rate < ceiling")
# check 7
m("c7 ceiling off", "ok = seconds <= ceiling and left == 0", "ok = left == 0")
m("c7 open work off", "ok = seconds <= ceiling and left == 0", "ok = seconds <= ceiling")
m("c7 timed_out off", "    if timed_out:\n", "    if False:\n")
m("c7 never-drained ok", 'return _result(7, False, "no intended send time or no drain moment"', 'return _result(7, True, "no intended send time or no drain moment"')
# run_checks glue
m("run ok any", '"ok": all(c["ok"] for c in checks)', '"ok": any(c["ok"] for c in checks)')

def run_one(idx, workdir):
    name, old, new = M[idx]
    f = workdir / "live_l2/check_invariants.py"
    orig = f.read_text(encoding="utf-8")
    try:
        if orig.count(old) != 1:
            return idx, "NOT-APPLIED", f"pattern count {orig.count(old)}"
        f.write_text(orig.replace(old, new), encoding="utf-8")
        env = dict(os.environ, PYTHONPATH="src:tests:.", PYTHONDONTWRITEBYTECODE="1")
        p = subprocess.run(["/root/.local/bin/pytest", "-x", "-q", "-p", "no:cacheprovider", *TESTS], cwd=workdir, env=env, capture_output=True, text=True, timeout=300)
        tail = (p.stdout.strip().splitlines() or [""])[-1]
        return idx, "KILLED" if p.returncode != 0 else "SURVIVED", tail
    finally:
        f.write_text(orig, encoding="utf-8")

def main():
    out = Path(sys.argv[1])
    workers = 4
    dirs = []
    for k in range(workers):
        d = Path(f"/tmp/dpld-l2e-mut{k}")
        if d.exists(): shutil.rmtree(d)
        shutil.copytree(SRC, d, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"))
        dirs.append(d)
    results = {}
    import queue, threading
    q = queue.Queue()
    for i in range(len(M)): q.put(i)
    def work(k):
        while True:
            try: i = q.get_nowait()
            except queue.Empty: return
            idx, status, tail = run_one(i, dirs[k])
            results[idx] = {"name": M[idx][0], "status": status, "tail": tail}
            print(idx, M[idx][0], status, flush=True)
    ts = [threading.Thread(target=work, args=(k,)) for k in range(workers)]
    [t.start() for t in ts]; [t.join() for t in ts]
    ordered = [results[i] for i in sorted(results)]
    out.write_text(json.dumps(ordered, indent=1), encoding="utf-8")
    from collections import Counter
    print(Counter(r["status"] for r in ordered))
    for d in dirs: shutil.rmtree(d, ignore_errors=True)

main()
