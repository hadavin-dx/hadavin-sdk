"""Groups the j-/f- runs by point: one row per distinct outcome with its sample size n. Own code, no demo numbers.
Usage: python make_results.py > RESULTS-table.md"""
import json
import os
import sys

K = "/home/user/work/kill"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load(p):
    try:
        return [json.loads(x) for x in open(p, encoding="utf-8").read().splitlines() if x.strip()]
    except OSError:
        return []


last = {}
for d in load(os.path.join(K, "results.jsonl")):
    last[d["label"]] = d
groups = {}
for label, d in last.items():
    if not (label.startswith("j") or label.startswith("ft14")):
        continue
    wd = os.path.join(K, "runs", label)
    mails = load(os.path.join(wd, "mails.jsonl"))
    ev = load(os.path.join(wd, "events.jsonl"))
    for lead, c in d.get("counts", {}).items():
        st = [r for r in d.get("states", []) if r[0] == lead]
        sig = (st[0][1] if st else "no-row", "attempts=" + (st[0][2] if st else "-"), "intake_mails=%s" % c["mail_to_intake"],
               "lead_alerts=%s" % c["alert"], "crm_rows=%s" % c["crm_rows"], "model_calls=%s" % c["stage_calls"])
        key = (d["point"], sig)
        groups.setdefault(key, []).append(label)
    if d["point"] in ("idle", "t14"):
        sig = ("no lead", "total_stage_requests=%s" % d.get("total_stage_requests"), "total_mails=%s" % d.get("total_mails"),
               "alert_mails=%s" % sum(1 for m in mails if "alerts@example.test" in str(m.get("rcpt"))),
               "crm_upserts=%s" % sum(1 for e in ev if e["src"] == "crm" and e["ev"] == "upsert_start"))
        groups.setdefault((d["point"] + (" FIXED flows" if label.startswith("ft14") else ""), sig), []).append(label)
print("| point | outcome (per lead, counted outside n8n) | n | runs |")
print("|---|---|---|---|")
for (point, sig), labels in sorted(groups.items()):
    print("| %s | %s | %d | %s |" % (point, ", ".join(sig), len(labels), " ".join(sorted(labels))))
