"""Alert-loss cases for Design A v3 (plan: PLAN-V3-ALERT.md). Usage: python v3.py LABEL CASE   CASE: A | B20 | B90 | C
Uses harness.Run (fresh n8n folder, fresh fakes). Output line goes to results.jsonl. Own code, no demo numbers."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as h  # noqa: E402

ADD = ("ALTER TABLE mf_leads ADD COLUMN IF NOT EXISTS alert_sent boolean NOT NULL DEFAULT false, "
       "ADD COLUMN IF NOT EXISTS alert_token text, ADD COLUMN IF NOT EXISTS alert_until timestamptz, "
       "ADD COLUMN IF NOT EXISTS alert_attempts int NOT NULL DEFAULT 0")
MAX_S = {"A": 900, "B20": 600, "B90": 700, "C": 1100}
AFTER_S = 150  # watch this long after alert_sent turned true, for a second alert


def row(lead):
    out = h.sql("SELECT state,attempts,mail_sent,alert_sent,alert_attempts FROM mf_leads WHERE lead_key='%s'" % lead)
    return out.split("|") if out and not out.startswith("ERR") else None


def main():
    label, case = sys.argv[1], sys.argv[2]
    r = h.Run(label)
    lead = "L-" + label
    out = {"label": label, "point": "v3" + case, "t_start": time.strftime("%H:%M:%SZ", time.gmtime()),
           "flows": os.environ.get("FLOW_COMMIT", "?")}
    timeline = []
    try:
        r.prepare_n8n()
        h.sql(ADD)
        h.sql("TRUNCATE mf_leads")
        r.start_fakes()
        r.start_n8n()
        r.ctl("smtp.ctl", {"drop": 1})  # the lead mail is stored, then the connection is dropped: lead goes unknown
        if case == "A":
            r.ctl("smtp2.ctl", {"alert_refuse": 2})
        elif case == "B20":
            r.ctl("smtp2.ctl", {"alert_hold_s": 20})
        elif case == "B90":
            r.ctl("smtp2.ctl", {"alert_hold_s": 90})
        t0 = time.time()
        out["send"] = r.send(lead)
        if case == "C":
            st = r.wait_event("smtp", "stored", timeout=60)
            out["lead_mail_stored"] = bool(st)
            r.ctl("smtp2.ctl", {"dead_until": time.time() + 600})
            out["dead_from_s"] = round(time.time() - t0)
        sent_true_at = None
        while time.time() - t0 < MAX_S[case]:
            rw = row(lead)
            mails = [json.loads(x) for x in r.lines("mails.jsonl")]
            alerts = [m for m in mails if lead in m.get("subject", "") and "alerts@example.test" in str(m.get("rcpt"))]
            intake = [m for m in mails if lead in m.get("subject", "") and "intake@example.test" in str(m.get("rcpt"))]
            snap = (rw, len(intake), len(alerts))
            if not timeline or timeline[-1][1:] != list(snap):
                timeline.append([round(time.time() - t0), *snap])
            if rw and rw[3] == "t" and sent_true_at is None:
                sent_true_at = time.time()
            if sent_true_at and time.time() - sent_true_at > AFTER_S:
                break
            time.sleep(5)
        out["reached"] = "alert_sent true" if sent_true_at else "alert_sent never true"
        out["timeline"] = timeline  # [seconds since send, [state, attempts, mail_sent, alert_sent, alert_attempts], intake mails, alert mails]
        out["counts"] = r.count([lead])
        ev = [json.loads(x) for x in r.lines("events.jsonl")]
        out["smtp_events"] = {k: sum(1 for e in ev if e["src"] == "smtp" and e["ev"] == k)
                              for k in ("connect", "stored", "alert_rcpt_refused", "refused_dead", "alert_hold_start", "alert_hold_end", "dropped_after_store")}
        out["alert_times_s"] = [round(m["t"] - t0) for m in (json.loads(x) for x in r.lines("mails.jsonl")) if "alerts@example.test" in str(m.get("rcpt"))]
    except Exception as e:  # noqa: BLE001
        out["error"] = "%s: %s" % (type(e).__name__, e)
    finally:
        r.stop_all()
        out["t_end"] = time.strftime("%H:%M:%SZ", time.gmtime())
    with open(os.path.join(h.K, "results.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(out) + "\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
