#!/usr/bin/env python3
"""Q3c (copy of Q3 soak, BLIND mail mode default, classification A/B/C, reachable crash points). Q3 crash soak: real desk process + demo fakes (loopback only), killed at documented crash points or at random times.

Usage: q3-soak.py run --base DIR --python PY --logs DIR --evidence-raw DIR --rounds 300 --master-seed 20261113
                      [--deadline-utc HH:MM] [--start-round 1]
       q3-soak.py report --logs DIR --out FILE
Evidence runner only: it never edits the product code. Made-up data, 127.0.0.1 only, one core, own PIDs only.
Per round: fresh fakes (keyed mail) + fresh book; k kills (1, or 2 with 30%), each by a documented crash point
(flag file, scripts/crash_desk.py) or a SIGKILL at a random time; restart on the SAME book; resend ALL leads and
replays; wait idle; assert the three invariants; run load_tools/check_invariants.py on the book.
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.client
import json
import os
import random
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

POINTS = ["A", "A2", "B", "L", "C0", "C1", "D1", "D1b", "D2", "D3"]  # ALL_HOOK_POINTS minus N1 (reminders are off)
ROUND_LIMIT_S = 120.0
MY_PIDS: set[int] = set()
PID_FILE: Path | None = None


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_ist() -> str:
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+0530")


def free_port(p: int) -> bool:
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", p))
        return True
    except OSError:
        return False
    finally:
        s.close()


def http_json(port: int, method: str, path: str, body: object | None = None, timeout: float = 10.0):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        data = None if body is None else json.dumps(body).encode()
        c.request(method, path, body=data, headers={"Content-Type": "application/json"} if data else {})
        r = c.getresponse()
        raw = r.read()
        try:
            return r.status, json.loads(raw.decode() or "null")
        except ValueError:
            return r.status, None
    finally:
        c.close()


class Round:
    def __init__(self, a: argparse.Namespace, n: int) -> None:
        self.a, self.n = a, n
        self.seed = f"{a.master_seed}-{n}"
        self.rng = random.Random(self.seed)
        self.dir = Path(a.logs) / f"round-{n:03d}"
        shutil.rmtree(self.dir, ignore_errors=True)
        self.dir.mkdir(parents=True)
        off = n % 400
        while not (free_port(27000 + off) and free_port(27500 + off)):
            off = (off + 1) % 400
        self.desk_port, self.fakes_port = 27000 + off, 27500 + off
        self.rng2 = random.Random(self.seed + "-x")  # extra draws, so the legacy draw order of self.rng is unchanged
        self.extra_n = 0
        self.book = self.dir / "data" / "desk.sqlite3"
        self.flag = self.book.parent / "crash.flag"
        self.book.parent.mkdir()
        self.desk: subprocess.Popen | None = None
        self.fakes: subprocess.Popen | None = None
        self.hung = threading.Event()
        self.t0 = time.monotonic()
        self.reqlog: list[dict] = []
        self.lock = threading.Lock()
        self.events: list[str] = []
        self.restarts = 0
        self.kills: list[dict] = []

    # ---- processes
    def env(self) -> dict[str, str]:
        e = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR")}
        e.update(
            PYTHONPATH="src:.",
            DESK_DB_PATH=str(self.book),
            DESK_PORT=str(self.desk_port),
            DESK_FAKES_PORT=str(self.fakes_port),
        )
        return e

    def spawn(self, argv: list[str], logname: str) -> subprocess.Popen:
        out = open(self.dir / logname, "ab")  # noqa: SIM115
        p = subprocess.Popen(  # noqa: S603
            argv, cwd=self.a.base, env=self.env(), stdout=out, stderr=subprocess.STDOUT, start_new_session=True
        )
        MY_PIDS.add(p.pid)
        if PID_FILE:
            with open(PID_FILE, "a") as f:
                f.write(f"{p.pid} round {self.n} {' '.join(argv[-3:])}\n")
        return p

    def start_fakes(self) -> None:
        self.fakes = self.spawn(
            [self.a.python, "-m", "demo_only.fakes_server", "--outbox", self.a.outbox, "--port", str(self.fakes_port)],
            "fakes.log",
        )
        for _ in range(100):
            try:
                if http_json(self.fakes_port, "GET", "/fake/info", timeout=2)[0] == 200:
                    return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("fakes did not start")

    def start_desk(self) -> None:
        self.desk = self.spawn([self.a.python, "scripts/crash_desk.py"], "desk.log")
        self.events.append(f"desk start #{self.restarts} pid {self.desk.pid}")
        for _ in range(300):
            if self.desk.poll() is not None:
                raise RuntimeError(f"desk exited at start with {self.desk.returncode}")
            try:
                if http_json(self.desk_port, "GET", "/counts", timeout=2)[0] == 200:
                    return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("desk did not become ready")

    def kill9(self, p: subprocess.Popen | None) -> None:
        if p is not None and p.pid in MY_PIDS and p.poll() is None:
            try:
                os.kill(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass

    def stop_all(self) -> None:
        if self.desk is not None and self.desk.poll() is None:
            try:
                os.kill(self.desk.pid, signal.SIGTERM)
                self.desk.wait(timeout=12)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                self.kill9(self.desk)
        if self.fakes is not None and self.fakes.poll() is None:
            try:
                os.kill(self.fakes.pid, signal.SIGTERM)
                self.fakes.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                self.kill9(self.fakes)
        for p in (self.desk, self.fakes):
            if p is not None:
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.kill9(p)
                MY_PIDS.discard(p.pid)

    # ---- sending
    def post(self, door: str, rid: str, payload: dict, retry: bool) -> None:
        first = time.time()
        attempts: list[dict] = []
        final: object = None
        receipt = None
        verdict = None
        delay = 0.1
        while True:
            if self.hung.is_set():
                break
            t = time.time()
            code, err, body = None, None, None
            try:
                code, body = http_json(
                    self.desk_port, "POST", "/leads", {"source": door, "source_ref": rid, "payload": payload}, 10
                )
            except Exception as e:  # noqa: BLE001
                err = type(e).__name__
            attempts.append({"ts": t, "code": code, "error": err, "latency_s": round(time.time() - t, 4)})
            final = code if code is not None else err
            if isinstance(body, dict):
                receipt, verdict = body.get("receipt_id"), body.get("verdict")
            if not retry or code in (200, 201, 202) or (code is not None and code != 503):
                break
            if time.time() - first > 30:
                break
            time.sleep(delay)
            delay = min(delay * 2, 1.0)
        with self.lock:
            self.reqlog.append(
                {
                    "request_id": rid,
                    "door": door,
                    "intended_ts": first,
                    "sent_ts": first,
                    "done_ts": time.time(),
                    "attempts": attempts,
                    "codes": [a["code"] if a["code"] is not None else a["error"] for a in attempts],
                    "final_status": final,
                    "receipt_id": receipt,
                    "verdict": verdict,
                    "accepted": final in (200, 201, 202),
                }
            )

    def send_all(self, plan: list[tuple[str, str, dict]], retry: bool, stop_when_dead: bool) -> int:
        sent = 0

        def one(item: tuple[str, str, dict]) -> None:
            nonlocal sent
            if stop_when_dead and self.desk is not None and self.desk.poll() is not None:
                return
            self.post(*item, retry)
            sent += 1

        with ThreadPoolExecutor(max_workers=6) as ex:
            list(ex.map(one, plan))
        return sent

    # ---- one round
    def run(self) -> dict:
        r = self.rng
        n_leads = r.randint(5, 40)
        persons = []
        for i in range(1, n_leads + 1):
            persons.append(
                {
                    "rid": f"r{self.n}-{i}",
                    "payload": {
                        "name": f"Person{self.n}x{i}",
                        "email": f"p{self.n}x{i}@example.com",
                        "company": f"Co {i}",
                        "message": f"made-up message {i}",
                    },
                }
            )
        plan: list[tuple[str, str, dict]] = []
        n_two_doors = n_replays = 0
        for p in persons:
            door = r.choice(["form", "webhook"])
            plan.append((door, p["rid"], p["payload"]))
            if r.random() < 0.3:
                plan.append(("webhook" if door == "form" else "form", p["rid"], p["payload"]))
                n_two_doors += 1
            if r.random() < 0.3:
                plan.append((door, p["rid"], p["payload"]))
                n_replays += 1
        k = 2 if r.random() < 0.3 else 1
        rec: dict = {
            "round": self.n,
            "seed": self.seed,
            "n_leads": n_leads,
            "two_door_dups": n_two_doors,
            "replays": n_replays,
            "planned_sends": len(plan),
            "kills_planned": k,
            "desk_port": self.desk_port,
            "fakes_port": self.fakes_port,
            "start_utc": now_utc(),
        }

        def watchdog() -> None:
            self.hung.set()
            for p in (self.desk, self.fakes):
                self.kill9(p)

        timer = threading.Timer(ROUND_LIMIT_S, watchdog)
        timer.start()
        try:
            self.start_fakes()
            self.start_desk()
            for ki in range(k):
                kind = "point" if r.random() < 0.6 else "time"
                point = r.choice(POINTS) if kind == "point" else None
                delay = r.uniform(0.02, 0.5 + 0.03 * n_leads) if kind == "time" else None
                order = plan[:]
                r.shuffle(order)
                kinfo = {"kill": ki + 1, "type": kind, "point": point, "delay_s": round(delay, 3) if delay else None}
                attempts_info: list[dict] = []
                max_att = 1 if self.a.legacy else 3
                for att in range(max_att):
                    extras: list[tuple[str, str, dict]] = []
                    if not self.a.legacy:
                        # fresh leads in every kill phase: A/A2/B need a NEW request id, L/C0/C1/D* need new follow-up work
                        for _ in range(self.rng2.randint(3, 8)):
                            self.extra_n += 1
                            j = self.extra_n
                            pl = {
                                "name": f"Person{self.n}y{j}",
                                "email": f"p{self.n}y{j}@example.com",
                                "company": f"Co y{j}",
                                "message": f"made-up extra message {j}",
                            }
                            persons.append({"rid": f"r{self.n}-y{j}", "payload": pl})
                            extras.append((self.rng2.choice(["form", "webhook"]), f"r{self.n}-y{j}", pl))
                        plan.extend(extras)
                    if point:
                        self.flag.write_text(point, encoding="utf-8")
                    killer = None
                    if kind == "time" and att == 0:
                        desk = self.desk

                        def late(d=desk, s=delay) -> None:
                            time.sleep(s)
                            self.kill9(d)

                        killer = threading.Thread(target=late, daemon=True)
                        killer.start()
                    batch = extras + (order if att == 0 else [])
                    sends = self.send_all(batch, retry=False, stop_when_dead=True)
                    kinfo["sends_made"] = kinfo.get("sends_made", 0) + sends
                    for _ in range(80 if self.a.legacy else 50):
                        if self.desk.poll() is not None:
                            break
                        time.sleep(0.1)
                    attempts_info.append({"attempt": att + 1, "point": point, "extras": len(extras), "ended": self.desk.poll() is not None})
                    if killer:
                        killer.join(timeout=5)
                    if self.desk.poll() is not None or kind != "point":
                        break
                kinfo["attempts"] = attempts_info
                if self.desk.poll() is None:
                    kinfo["outcome"] = "not-fired-then-sigkill" if kind == "point" else "late-sigkill"
                    self.kill9(self.desk)
                else:
                    kinfo["outcome"] = "fired" if self.desk.returncode in (137, -9) else f"exit-{self.desk.returncode}"
                kinfo["exit_code"] = self.desk.returncode
                try:
                    self.flag.unlink()
                except FileNotFoundError:
                    pass
                MY_PIDS.discard(self.desk.pid)
                self.kills.append(kinfo)
                self.restarts += 1
                self.start_desk()
            # resend ALL leads and replays, in a new random order, patiently
            order = plan[:]
            r.shuffle(order)
            self.send_all(order, retry=True, stop_when_dead=False)
            idle = self.wait_idle()
            rec["idle"] = idle
            self.collect_desk_views()
        except Exception as e:  # noqa: BLE001
            rec["harness_error"] = f"{type(e).__name__}: {e}"
        finally:
            timer.cancel()
        rec["hang"] = self.hung.is_set()
        rec["kills"] = self.kills
        rec["restarts"] = self.restarts
        rec["events"] = self.events
        rec["elapsed_s"] = round(time.monotonic() - self.t0, 2)
        if rec["hang"] or "harness_error" in rec:
            self.collect_fakes()
            self.stop_all()
            self.finish_files(rec, persons, assertions=False)
            return rec
        self.collect_fakes()
        self.counts = None
        try:
            self.counts = http_json(self.desk_port, "GET", "/counts", timeout=5)[1]
        except Exception:  # noqa: BLE001
            pass
        self.stop_all()
        self.finish_files(rec, persons, assertions=True)
        return rec

    def wait_idle(self) -> dict:
        t_end = self.t0 + ROUND_LIMIT_S - 5
        last = None
        stable = 0
        while time.monotonic() < t_end and not self.hung.is_set():
            try:
                c = http_json(self.desk_port, "GET", "/counts", timeout=5)[1]
            except Exception:  # noqa: BLE001
                time.sleep(0.3)
                continue
            busy = int(c.get("open", 0)) + int(c.get("pending_followups", 0))
            try:
                o = http_json(self.fakes_port, "GET", "/fake/outbox", timeout=5)[1]["count"]
            except Exception:  # noqa: BLE001
                o = -1
            snap = (busy, o, c.get("received"), c.get("sending_followups"))
            if busy == 0:
                stable = stable + 1 if snap == last else 1
                if stable >= 3:
                    return {"idle": True, "counts": c}
            else:
                stable = 0
            last = snap
            time.sleep(0.3)
        return {"idle": False, "counts": None}

    def collect_desk_views(self) -> None:
        self.review, self.ui_review = None, None
        try:
            self.review = http_json(self.desk_port, "GET", "/review", timeout=10)[1]
            self.ui_review = http_json(self.desk_port, "GET", "/api/ui/review", timeout=10)[1]
        except Exception as e:  # noqa: BLE001
            self.review = {"error": str(e)}

    def collect_fakes(self) -> None:
        try:
            self.outbox = http_json(self.fakes_port, "GET", "/fake/outbox", timeout=5)[1]
            self.crm = http_json(self.fakes_port, "GET", "/fake/crm", timeout=5)[1]
        except Exception as e:  # noqa: BLE001
            self.outbox, self.crm = {"messages": [], "error": str(e)}, {"rows": [], "error": str(e)}

    # ---- assertions
    def finish_files(self, rec: dict, persons: list[dict], assertions: bool) -> None:
        d = self.dir
        with open(d / "requests.jsonl", "w") as f:
            for line in sorted(self.reqlog, key=lambda x: x["intended_ts"]):
                f.write(json.dumps(line) + "\n")
        (d / "requests.jsonl.facts.json").write_text(
            json.dumps({"intended_requests": len(self.reqlog), "qualifier": "recorded", "harness": "q3-soak"})
        )
        (d / "outbox.json").write_text(json.dumps(self.outbox))
        (d / "crm.json").write_text(json.dumps(self.crm))
        (d / "model.jsonl").write_text("")
        with open(d / "mail.jsonl", "w") as f:
            for m in self.outbox.get("messages", []):
                f.write(json.dumps({"ts": 0, "send_key": m["key"], "to": m["to"], "subject": m["subject"]}) + "\n")
        if not assertions:
            rec["assert"] = None
            return
        rec["assert"] = self.assert_all(rec, persons)
        rec["classes"] = self.classify(rec, persons)
        rec["checker"] = self.run_checker()
        rec["checker_allow_unknown"] = self.run_checker(extra=["--max-unknown", "100000"], tag="allow")

    def assert_all(self, rec: dict, persons: list[dict]) -> dict:
        res: dict = {"a1_no_double": None, "a2_mail_le_1": None, "a3_no_lost": None, "notes": []}
        try:
            conn = sqlite3.connect(f"file:{self.book}?mode=ro", uri=True)
            receipts = conn.execute("SELECT source, source_ref, outcome, outcome_lead_id FROM receipts").fetchall()
            leads = conn.execute("SELECT lead_id, email_key FROM leads").fetchall()
            fus = {lid: (st, err) for lid, st, err in conn.execute("SELECT lead_id, state, last_error FROM followups")}
            conn.close()
        except sqlite3.Error as e:
            res["notes"].append(f"book unreadable: {e}")
            res["a1_no_double"] = res["a2_mail_le_1"] = res["a3_no_lost"] = False
            return res
        rids = {p["rid"] for p in persons}
        by_email = Counter(e for _, e in leads)
        lead_email = dict(leads)
        crm_rows = self.crm.get("rows", [])
        crm_per_lead = Counter(str(x["lead_id"]) for x in crm_rows)
        news = Counter(ref for _, ref, o, _ in receipts if o == "new")
        a1_bad: list[str] = []
        for p in persons:
            em = p["payload"]["email"].lower()
            if by_email.get(em, 0) > 1:
                a1_bad.append(f"{p['rid']}: {by_email[em]} leads for one person")
            if news.get(p["rid"], 0) > 1:
                a1_bad.append(f"{p['rid']}: {news[p['rid']]} 'new' verdict rows")
        for lid, n in crm_per_lead.items():
            if n > 1:
                a1_bad.append(f"lead {lid}: {n} CRM rows")
            if lid not in lead_email:
                a1_bad.append(f"CRM row for unknown lead {lid}")
        if len(leads) > len(persons):
            a1_bad.append(f"{len(leads)} leads for {len(persons)} people")
        res["a1_no_double"] = not a1_bad
        res["a1_bad"] = a1_bad
        msgs = self.outbox.get("messages", [])
        per_key = Counter(m["key"] for m in msgs)
        per_to = Counter(m["to"].strip().lower() for m in msgs)
        a2_bad = [f"key {k}: {n} mails" for k, n in per_key.items() if n > 1]
        a2_bad += [f"address {t}: {n} mails" for t, n in per_to.items() if n > 1]
        res["a2_mail_le_1"] = not a2_bad
        res["a2_bad"] = a2_bad
        # no lead lost: every sent person has a decided receipt, a lead, and a follow-up out of pending/sending
        decided = {ref for _, ref, o, _ in receipts if o in ("new", "duplicate", "review")}
        undecided = [ref for _, ref, o, _ in receipts if o is None]
        a3_bad = []
        email_to_lead = {e: lid for lid, e in leads}
        states = Counter()
        for p in persons:
            rid = p["rid"]
            if rid not in decided:
                a3_bad.append(f"{rid}: no decided receipt")
                continue
            lid = email_to_lead.get(p["payload"]["email"].lower())
            if lid is None:
                a3_bad.append(f"{rid}: decided but no lead row")
                continue
            st = fus.get(lid, (None, None))[0]
            states[st] += 1
            if st in (None, "pending", "sending"):
                a3_bad.append(f"{rid}/{lid}: follow-up not terminal ({st})")
        if undecided:
            a3_bad.append(f"open receipts: {undecided}")
        res["a3_no_lost"] = not a3_bad
        res["a3_bad"] = a3_bad
        res["followup_states"] = dict(states)
        res["mail_count"] = len(msgs)
        res["crm_count"] = len(crm_rows)
        res["lead_count"] = len(leads)
        res["receipt_count"] = len(receipts)
        res["idle"] = bool(rec.get("idle", {}).get("idle"))
        if not res["idle"]:
            res["notes"].append("desk never became idle inside the round budget")
        return res

    def classify(self, rec: dict, persons: list[dict]) -> dict:
        """A = promise of the documents broken, B = documented non-guarantee of blind mode, C = undocumented."""
        out: dict = {"A": [], "B": [], "C": [], "unknown_n": 0, "unknown_visible": 0, "mails_per_lead": {}}
        try:
            conn = sqlite3.connect(f"file:{self.book}?mode=ro", uri=True)
            leads = conn.execute("SELECT lead_id, email_key FROM leads").fetchall()
            fus = {lid: (st, err) for lid, st, err in conn.execute("SELECT lead_id, state, last_error FROM followups")}
            conn.close()
        except sqlite3.Error as e:
            out["A"].append(f"book unreadable: {e}")
            return out
        email_of = dict(leads)
        mails = Counter(m["to"].strip().lower() for m in self.outbox.get("messages", []))
        shown = set()
        for it in (self.review if isinstance(self.review, list) else []):
            if it.get("kind") == "unknown":
                shown.add(str(it.get("lead_id")))
        ui_txt = json.dumps(self.ui_review) if self.ui_review is not None else ""
        if not isinstance(self.review, list):
            out["A"].append(f"/review not readable: {str(self.review)[:200]}")
        out["mails_per_lead"] = dict(Counter(mails.get(e, 0) for e in email_of.values()))
        for lid, em in email_of.items():
            st, err = fus.get(lid, (None, None))
            m = mails.get(em, 0)
            if m > 1:
                out["A"].append(f"{lid} ({em}): {m} mails from the desk alone (state {st}/{err})")
            if st == "unknown":
                out["unknown_n"] += 1
                vis = lid in shown
                vis_ui = lid in ui_txt
                out["unknown_visible"] += 1 if vis else 0
                if not vis:
                    out["A"].append(f"{lid}: unknown follow-up NOT listed in GET /review (ui lists it: {vis_ui})")
                if err in ("ambiguous_prior", "ambiguous") and m <= 1:
                    out["B"].append(f"{lid}: unknown/{err}, {m} mail(s)")
                else:
                    out["C"].append(f"{lid}: unknown/{err}, {m} mail(s)")
            elif st == "sent":
                if m == 0:
                    out["A"].append(f"{lid}: state sent but 0 mails in the fake outbox")
            elif st == "failed":
                out["C"].append(f"{lid}: failed/{err}, {m} mail(s)")
            else:
                out["A"].append(f"{lid}: follow-up ended {st} ({err}) after idle; {m} mail(s)")
        return out

    def run_checker(self, extra: list[str] | None = None, tag: str = "main") -> dict:
        d = self.dir
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG")}
        env["PYTHONPATH"] = "src:."
        env["LEAD_DESK_PATH_ROOTS"] = str(d)
        cmd = [
            self.a.python,
            "load_tools/check_invariants.py",
            "--requests",
            str(d / "requests.jsonl"),
            "--book",
            str(self.book),
            "--catcher",
            str(d / "mail.jsonl"),
            "--crm",
            str(d / "crm.json"),
            "--model-log",
            str(d / "model.jsonl"),
            "--no-require-comparable",
            "--json",
            str(d / ("checker.json" if tag == "main" else f"checker-{tag}.json")),
            *(extra or []),
        ]
        try:
            p = subprocess.run(cmd, cwd=self.a.base, env=env, capture_output=True, text=True, timeout=60)  # noqa: S603
        except subprocess.TimeoutExpired:
            return {"exit": "timeout"}
        (d / ("checker.txt" if tag == "main" else f"checker-{tag}.txt")).write_text(p.stdout + "\n--stderr--\n" + p.stderr)
        failed: list[str] = []
        try:
            js = json.loads((d / ("checker.json" if tag == "main" else f"checker-{tag}.json")).read_text())
            failed = [f"{c['id']}:{c['name']} -> {c['detail']} :: {c['offenders']}" for c in js["checks"] if not c["ok"]]
        except (OSError, ValueError, KeyError):
            pass
        return {"exit": p.returncode, "failed": failed}


def run(a: argparse.Namespace) -> None:
    global PID_FILE
    logs = Path(a.logs)
    logs.mkdir(parents=True, exist_ok=True)
    raw = Path(a.evidence_raw)
    raw.mkdir(parents=True, exist_ok=True)
    PID_FILE = logs / "pids.txt"
    tag = "q3c" + ("-legacy" if a.legacy else "")
    out = logs / "rounds.jsonl"
    progress = raw / "progress-Q3c.txt"
    deadline = None
    if a.deadline_utc:
        hh, mm = map(int, a.deadline_utc.split(":"))
        deadline = dt.datetime.now(dt.timezone.utc).replace(hour=hh, minute=mm, second=0, microsecond=0)
    viol = hangs = done = 0
    last_snap = time.monotonic()
    with open(progress, "a") as f:
        f.write(f"Q3c soak start UTC {now_utc()} IST {now_ist()} rounds={a.rounds} master_seed={a.master_seed} outbox={a.outbox} legacy={a.legacy}\n")
    for n in range(a.start_round, a.start_round + a.rounds):
        if deadline and dt.datetime.now(dt.timezone.utc) >= deadline:
            with open(progress, "a") as f:
                f.write(f"deadline {a.deadline_utc}Z reached before round {n}: stopping UTC {now_utc()}\n")
            break
        rnd = Round(a, n)
        try:
            rec = rnd.run()
        except Exception as e:  # noqa: BLE001
            rec = {"round": n, "seed": rnd.seed, "harness_error": f"{type(e).__name__}: {e}"}
            rnd.stop_all()
        asr = rec.get("assert") or {}
        cl = rec.get("classes") or {}
        bad = bool(cl.get("A") or cl.get("C")) or (
            asr and not (asr.get("a1_no_double") and asr.get("a2_mail_le_1") and asr.get("a3_no_lost"))
        ) or (rec.get("checker_allow_unknown", {}).get("exit") not in (0, None))
        rec["violation"] = bool(bad)
        rec["end_utc"] = now_utc()
        with open(out, "a") as f:
            f.write(json.dumps(rec) + "\n")
        done += 1
        viol += 1 if bad else 0
        hangs += 1 if rec.get("hang") else 0
        if not bad and not rec.get("hang") and "harness_error" not in rec:
            shutil.rmtree(rnd.dir / "data", ignore_errors=True)  # keep only logs of clean rounds
        if done % 25 == 0:
            with open(progress, "a") as f:
                f.write(f"UTC {now_utc()} IST {now_ist()} rounds_done={done} (last {n}) violations={viol} hangs={hangs}\n")
        if time.monotonic() - last_snap >= 600:
            shutil.copy(out, raw / f"q3c-{tag}-rounds-partial-{dt.datetime.now(dt.timezone.utc):%H%M}.jsonl")
            last_snap = time.monotonic()
    shutil.copy(out, raw / f"{tag}-rounds.jsonl")
    with open(progress, "a") as f:
        f.write(f"Q3c soak end UTC {now_utc()} IST {now_ist()} rounds_done={done} violations={viol} hangs={hangs}\n")


def report(a: argparse.Namespace) -> None:
    rows = [json.loads(line) for line in (Path(a.logs) / "rounds.jsonl").read_text().splitlines() if line.strip()]
    lines = ["| round | seed | N | planned sends | kills (type/point/outcome) | restarts | A1 | A2 | A3 | checker | s |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        asr = r.get("assert") or {}
        ks = "; ".join(f"{k['type']}/{k.get('point') or k.get('delay_s')}/{k['outcome']}" for k in r.get("kills", []))
        lines.append(
            f"| {r['round']} | {r['seed']} | {r.get('n_leads')} | {r.get('planned_sends')} | {ks} | {r.get('restarts')} | "
            f"{asr.get('a1_no_double')} | {asr.get('a2_mail_le_1')} | {asr.get('a3_no_lost')} | "
            f"{(r.get('checker') or {}).get('exit')} | {r.get('elapsed_s')} |"
        )
    Path(a.out).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--base", required=True)
    r.add_argument("--python", required=True)
    r.add_argument("--logs", required=True)
    r.add_argument("--evidence-raw", required=True)
    r.add_argument("--rounds", type=int, default=300)
    r.add_argument("--start-round", type=int, default=1)
    r.add_argument("--master-seed", type=int, default=20261115)
    r.add_argument("--deadline-utc", default=None)
    r.add_argument("--outbox", choices=["keyed", "blind"], default="blind")
    r.add_argument("--legacy", action="store_true", help="Q3 kill plan: no extra leads, no re-arm (same seeds as Q3)")
    p = sub.add_parser("report")
    p.add_argument("--logs", required=True)
    p.add_argument("--out", required=True)
    args = ap.parse_args()
    run(args) if args.cmd == "run" else report(args)
