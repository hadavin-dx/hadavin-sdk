"""Continuous-arrival scenarios for the lead desk (ORDER 212). Evidence only: prints numbers, never judges.
Reuses the helpers of load.py (same environment variables: LOAD_ROOT LOAD_DATA LOAD_PY LOAD_DESK_PORT LOAD_FAKES_PORT).
usage: arrival.py MODE SCENARIO     MODE = keyed|blind     SCENARIO = burst10|burst50|burst200|mixed50|rate5x60
 burst N   : N different leads at the same instant (all web form)
 mixed50   : 50 leads, half through the web form and half through the email door (webhook); every request id sent twice
             at the same instant (100 requests, 50 distinct request ids)
 rate5x60  : one new lead every 200 ms for 60 s (300 requests, 5 per second), alternating the two doors"""
import sys, threading, time
from collections import Counter
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import load


def body(ref, email, door):
    return {"source": door, "source_ref": ref, "payload": {"name": "Ada Example", "email": email, "phone": "555 0100", "message": "Please call me."}}


def fire(items, pace=None):
    """items: list of (door, ref, email). pace=None: all at once behind a barrier; else seconds between starts."""
    res, lock = [], threading.Lock()
    barrier = threading.Barrier(len(items)) if pace is None else None

    def one(door, ref, email):
        if barrier: barrier.wait()
        t0 = time.time(); st, js = load.post(load.DESK + "/leads", body(ref, email, door))
        with lock: res.append((st, time.time() - t0, js.get("receipt_id"), ref, email, 1))
    th = []
    for i, (door, ref, email) in enumerate(items):
        t = threading.Thread(target=one, args=(door, ref, email)); th.append(t)
        if pace is None: t.start()
    if pace is not None:
        t0 = time.time()
        for i, t in enumerate(th):
            time.sleep(max(0, t0 + i * pace - time.time())); t.start()
    [t.join() for t in th]
    return res


def main(mode, scen):
    load.start(mode)
    try:
        if scen.startswith("burst"):
            n = int(scen[5:]); items = [("form", f"{scen}-{i}", f"a{i}@example.test") for i in range(n)]
            res = fire(items); expect = n; reqs = n
        elif scen == "mixed50":
            base = [("form" if i % 2 == 0 else "webhook", f"mx-{i}", f"m{i}@example.test") for i in range(50)]
            res = fire(base + base); expect = 50; reqs = 100
        elif scen == "rate5x60":
            items = [("form" if i % 2 == 0 else "webhook", f"r5-{i}", f"r{i}@example.test") for i in range(300)]
            t0 = time.time(); res = fire(items, pace=0.2); print(f"   wall_seconds={time.time()-t0:.1f}"); expect = 300; reqs = 300
        else: raise SystemExit("unknown scenario")
        print(f"   status_by_request_id: {dict(Counter(r[0] for r in res))}; distinct_request_ids={len({r[3] for r in res})}")
        load.report(f"[{mode}] {scen} requests={reqs}", reqs, res, expect, wait=5.0)
    finally: load.stop()


if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
