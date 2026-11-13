#!/usr/bin/env python3
"""Q3c probe: ONE lead per run, blind mail fake, one named crash point, restart, resend. Shows what a single follow-up does at each point
(docs/tests.md:98-110 table), without other follow-ups in flight. Imports the q3c harness classes; made-up data, loopback only."""
import argparse, importlib.util, json, sqlite3, sys, time
from pathlib import Path

spec = importlib.util.spec_from_file_location("q3c", "/home/user/hadavin-sdk/handover/demo3/tools/q3c-soak.py")
m = importlib.util.module_from_spec(spec); sys.modules["q3c"] = m; spec.loader.exec_module(m)
ns = argparse.Namespace(base="/home/user/work/q3c-base", python="/home/user/work/final-venv/bin/python",
                        logs="/home/user/work/q3c-logs/probe", outbox="blind", master_seed=1, legacy=True)
Path(ns.logs).mkdir(parents=True, exist_ok=True)
m.PID_FILE = Path(ns.logs) / "pids.txt"
res = []
n = 0
for point in ["A", "A2", "B", "L", "C0", "C1", "D1", "D1b", "D2", "D3"]:
    for trial in range(10):
        n += 1
        r = m.Round(ns, 5000 + n)
        try:
            r.start_fakes(); r.start_desk()
            r.flag.write_text(point, encoding="utf-8")
            pl = {"name": "Solo", "email": f"solo{n}@example.com", "company": "Co", "message": "made-up"}
            r.post("form", f"s{n}", pl, False)
            for _ in range(60):
                if r.desk.poll() is not None: break
                time.sleep(0.1)
            fired = r.desk.poll() is not None and r.desk.returncode == 137
            if r.desk.poll() is None: r.kill9(r.desk)
            m.MY_PIDS.discard(r.desk.pid)
            r.start_desk()
            r.post("form", f"s{n}", pl, True)
            idle = r.wait_idle()["idle"]
            r.collect_fakes()
            c = sqlite3.connect(f"file:{r.book}?mode=ro", uri=True)
            fu = c.execute("select state,last_error from followups").fetchall()
            nl = c.execute("select count(*) from leads").fetchone()[0]
            c.close()
            res.append({"point": point, "trial": trial, "fired": fired, "idle": idle, "leads": nl, "followups": fu, "mails": len(r.outbox.get("messages", []))})
        finally:
            r.stop_all()
print(json.dumps(res))
