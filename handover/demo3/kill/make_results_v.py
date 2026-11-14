"""Alert cases on the v3 and v4 flows: one row per run with the counts and the alert times. Own code, no demo numbers. Usage: python make_results_v.py"""
import json
K = "/home/user/work/kill"
rows = []
for x in open(K + "/results.jsonl", encoding="utf-8"):
    r = json.loads(x)
    if str(r.get("label", "")).startswith(("v3", "v4")):
        c = next(iter(r["counts"].values()))
        last = r["timeline"][-1] if r.get("timeline") else None
        rows.append((r["flows"], r["point"], r["label"], r.get("reached"), c["mail_to_intake"], c["alert"], c["crm_rows"], r.get("alert_times_s"), last[1][4] if last else "-"))
print("| flows | case | run | reached | intake mails | alerts | CRM rows | alert times (s) | alert_attempts |")
print("|---|---|---|---|---|---|---|---|---|")
for r in sorted(rows):
    print("| " + " | ".join(str(v) for v in r) + " |")
