"""Own derivation of the lease-45 crash figures from raw-lane3/results.jsonl (not void-check.py, not recompute.py)."""
import json, statistics
rows = [json.loads(x) for x in open("/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/raw-lane3/results.jsonl", encoding="utf-8") if x.strip()]
print("total rows", len(rows), "keys of first", sorted(rows[0].keys()))
fl = sorted({r.get("flows") for r in rows}, key=str); print("distinct flows values:", fl)
l45 = [r for r in rows if "lease45" in str(r.get("flows"))]
print("lease45 rows", len(l45))
for r in l45: print(" ", r.get("label"), r.get("point"), "term=%r" % r.get("reached_terminal"), "state=%r" % r.get("final_state", r.get("state")), "k2f=%r rec=%r err=%r" % (r.get("kill_to_final_s"), r.get("recovery_s"), r.get("error")))
crash = [r for r in l45 if r.get("point") in ("K1", "K2", "K3", "K6")]
void = [r for r in crash if str(r["label"]).startswith("VOID")]
kept = [r for r in crash if r not in void]
print("crash runs", len(crash), "void", [r["label"] for r in void], "kept", len(kept))
import collections
print("kept per point", dict(collections.Counter(r["point"] for r in kept)))
print("kept reached_terminal all true:", all(r.get("reached_terminal") is True for r in kept))
a = [r["kill_to_final_s"] for r in kept]; b = [r["recovery_s"] for r in kept]
print("kill_to_final_s: n=%d min=%.1f max=%.1f" % (len(a), min(a), max(a)))
print("recovery_s     : n=%d min=%.1f max=%.1f" % (len(b), min(b), max(b)))
print("DERIVED RANGES: %.1f to %.1f s and %.1f to %.1f s" % (min(a), max(a), min(b), max(b)))
print("including void rows would give kill_to_final range:", min(a + [r["kill_to_final_s"] for r in void if r.get("kill_to_final_s") is not None]), max(a + [r["kill_to_final_s"] for r in void if r.get("kill_to_final_s") is not None]))
for k in ("done", "unknown"):
    pass
print("end states of kept:", collections.Counter((r["point"], str(r.get("end_state", r.get("final", r.get("result"))))) for r in kept))
