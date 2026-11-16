"""Independent recount of the lane3 lease-45 crash runs from raw-lane3/results.jsonl (own code, not recompute.py).
Prints: kept runs per case, min/max/median of kill_to_final_s and of recovery start, the voided rows, and which KEPT runs overlap in time
with each voided run. Reads only; writes nothing."""
import json, statistics, collections, sys
SRC = sys.argv[1]
rows = [json.loads(l) for l in open(SRC, encoding="utf-8")]
L45 = "873a908a-film-v4-lease45"
r45 = [r for r in rows if r.get("flows") == L45]
void = [r for r in rows if str(r.get("label", "")).startswith("VOID")]
kept = [r for r in r45 if r["point"] in ("K1", "K2", "K3", "K6") and not r["label"].startswith("VOID")]
other = [r for r in r45 if r not in kept and r not in void]
print("rows in file:", len(rows), "| lease-45 rows:", len(r45))
print("KEPT crash runs:", len(kept), dict(collections.Counter(r["point"] for r in kept)))
print("KEPT with reached_terminal true:", sum(1 for r in kept if r.get("reached_terminal")))
v = [r["kill_to_final_s"] for r in kept]
print("kill_to_final_s min %.1f max %.1f median %.2f" % (min(v), max(v), statistics.median(v)))
w = [r["recovery_s"] for r in kept]
print("recovery_s (seconds from n8n coming back up) min %.1f max %.1f" % (min(w), max(w)))
r_ = [r["restart_s"] for r in kept]
print("restart_s min %.1f max %.1f" % (min(r_), max(r_)))
print("lease-45 rows that are neither kept crash runs nor void (the CRM-refuses case):", [(r["label"], r["point"]) for r in other])
print("VOID rows in the whole file:", len(void))
def sec(t):
    h, m, x = t[:-1].split(":"); return int(h) * 3600 + int(m) * 60 + int(x)
for x in void:
    print(" VOID", x["label"], x["point"], x["t_start"], x["t_end"], "error=%r" % x.get("error"), "reached_terminal=%r" % x.get("reached_terminal"), "kill_to_final_s=%r" % x.get("kill_to_final_s"), "flows=%s" % x.get("flows"))
    a, b = sec(x["t_start"]), sec(x["t_end"])
    ov = [r["label"] for r in kept if sec(r["t_start"]) < b and sec(r["t_end"]) > a]
    print("   kept runs overlapping its time window:", len(ov), ov)
