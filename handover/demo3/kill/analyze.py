"""Builds the per-run table from the raw run folders (events.jsonl, mails.jsonl, results.jsonl). Own code; no demo numbers.
Usage: python analyze.py [LABEL_PREFIX ...]   Per lead: mails to intake, alert mails naming the lead, CRM rows,
model calls and requests at the stage. Phantom = idle-recovery noise (lead None / null / 'undefined'), reported apart.
noise_changed_count = YES only if a phantom event touched a lead-specific count (it never can by key, so it is checked
by comparing totals with the sum of per-lead counts plus phantom)."""
import json
import os
import sys

K = "/home/user/work/kill"


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return [json.loads(x) for x in f.read().splitlines() if x.strip()]
    except OSError:
        return []


def main():
    prefixes = sys.argv[1:] or [""]
    res = {}
    for d in load(os.path.join(K, "results.jsonl")):
        res[d["label"]] = d  # last record wins for a label
    print("label | point | kill seen | restart s | final state(s) | intake mails | lead alerts | crm rows | model calls | stage reqs | phantom stage | phantom crm | phantom alerts | noise changed a lead count | seconds")
    for label in sorted(res):
        if not any(label.startswith(p) for p in prefixes):
            continue
        d = res[label]
        wd = os.path.join(K, "runs", label)
        ev = load(os.path.join(wd, "events.jsonl"))
        mails = load(os.path.join(wd, "mails.jsonl"))
        leads = list(d.get("counts", {}).keys())
        ph_stage = sum(1 for e in ev if e["src"] == "stage" and e["ev"] in ("qualify_start", "qualify_repeat") and e.get("lead") in ("None", None))
        ph_crm = sum(1 for e in ev if e["src"] == "crm" and e["ev"] == "upsert_start" and e.get("lead") is None)
        ph_alert = sum(1 for m in mails if "undefined" in m.get("subject", ""))
        tot_alert = sum(1 for m in mails if "alerts@example.test" in str(m.get("rcpt")))
        lead_alert = sum(c["alert"] for c in d.get("counts", {}).values())
        noise = "NO" if tot_alert == lead_alert + ph_alert else "CHECK"
        states = ";".join("%s=%s/a%s/m%s" % (r[0], r[1], r[2], r[3]) for r in d.get("states", []))
        c = d.get("counts", {})
        calls = ",".join(str(v.get("stage_calls")) for v in c.values())
        reqs = ",".join(str(v.get("stage_requests")) for v in c.values())
        crm = ",".join(str(v.get("crm_rows")) for v in c.values())
        im = ",".join(str(v.get("mail_to_intake")) for v in c.values())
        la = ",".join(str(v.get("alert")) for v in c.values())
        secs = ""
        if d.get("t_start") and d.get("t_end"):
            h = lambda s: int(s[0:2]) * 3600 + int(s[3:5]) * 60 + int(s[6:8])  # noqa: E731
            secs = h(d["t_end"]) - h(d["t_start"])
        print(" | ".join(str(x) for x in (label, d["point"], d.get("event_seen", ""), d.get("restart_s", ""), states or d.get("error", ""),
                                        im, la, crm, calls, reqs, ph_stage, ph_crm, ph_alert, noise, secs)))


main()
