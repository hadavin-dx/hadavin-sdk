"""lane3 kill script driver. Made-up data, loopback only. Own code.
Usage: python harness.py RUNLABEL POINT [N]   POINT: control1 | control2same | control2par | controlbad | K1 | K2 | K3 | K6 | Fa | Fb | Fc
Each run: fresh n8n user folder (import creds + 4 flows with the n8n CLI), fresh fakes, empty table.
Kill = SIGKILL of the n8n process the moment a fake logs the named event; then restart and wait for recovery.
Counting is done outside n8n: mail file, CRM rows, stage journal, table.
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
K = "/home/user/work/kill"
N8N_DIR = "/home/user/work/kill-n8n"
NODE_BIN = "/home/user/work/node24/node_modules/node/bin"
PROBE = os.environ.get("FLOW_PROBE", os.path.join(K, "probe"))
PSQL = ["psql", "-h", "127.0.0.1", "-p", "55432", "-U", "postgres", "-d", "kill_t", "-At", "-F", "|"]
PORT = {"crm": 18101, "stage": 18102, "smtp": 2525, "n8n": 5690}
FLOWS = ["mf-sub-crm-mail", "mf-form", "mf-hook", "mf-recovery"]
PUBLISH_IDS = ["subflow0000000001", "form000000000001", "hook000000000001", "recov00000000001"]
TERMINAL = ("done", "unknown", "failed", "review")


def env_n8n(home):
    e = dict(os.environ)
    e["PATH"] = NODE_BIN + ":" + e["PATH"]
    e.update(N8N_USER_FOLDER=home, N8N_DIAGNOSTICS_ENABLED="false", N8N_PORT=str(PORT["n8n"]),
             N8N_BLOCK_ENV_ACCESS_IN_NODE="false", N8N_HOST="127.0.0.1", N8N_LISTEN_ADDRESS="127.0.0.1",
             MF_CRM_URL="http://127.0.0.1:%d" % PORT["crm"], MF_STAGE_URL="http://127.0.0.1:%d" % PORT["stage"],
             N8N_VERSION_NOTIFICATIONS_ENABLED="false", N8N_TEMPLATES_ENABLED="false")
    return e


def sql(q):
    r = subprocess.run(PSQL + ["-c", q], capture_output=True, text=True, timeout=30)
    return r.stdout.strip() if r.returncode == 0 else "ERR " + r.stderr.strip()[:200]


def http(method, url, body=None, timeout=20):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:  # noqa: BLE001 - driver reports the cause by name
        return 0, "%s: %s" % (type(e).__name__, e)


class Run:
    def __init__(self, label):
        self.label = label
        self.wd = os.path.join(K, "runs", label)
        shutil.rmtree(self.wd, ignore_errors=True)
        os.makedirs(self.wd)
        self.home = os.path.join(self.wd, "n8nhome")
        self.procs = {}
        self.n8n = None
        self.n8n_log = os.path.join(self.wd, "n8n.log")

    # ---- fakes
    def start_fakes(self):
        for kind in ("crm", "stage", "smtp"):
            lg = open(os.path.join(self.wd, kind + ".log"), "a")
            self.procs[kind] = subprocess.Popen([sys.executable, os.path.join(HERE, "fakes.py"), kind,
                                                 str(PORT[kind]), self.wd], stdout=lg, stderr=lg)
        end = time.time() + 20
        while time.time() < end:
            ups = [json.loads(x).get("src") for x in self.lines("events.jsonl") if '"ev": "up"' in x]
            if len(set(ups)) == 3:
                return
            time.sleep(0.3)
        raise RuntimeError("fakes_not_up")

    def lines(self, name):
        try:
            with open(os.path.join(self.wd, name), encoding="utf-8") as f:
                return [x for x in f.read().splitlines() if x.strip()]
        except OSError:
            return []

    def ctl(self, name, d):
        with open(os.path.join(self.wd, name), "w", encoding="utf-8") as f:
            json.dump(d, f)

    def clear_ctl(self):
        for n in ("crm.ctl", "stage.ctl", "smtp.ctl"):
            try:
                os.remove(os.path.join(self.wd, n))
            except OSError:
                pass

    # ---- n8n
    def cli(self, *args):
        r = subprocess.run([os.path.join(N8N_DIR, "node_modules/.bin/n8n"), *args], cwd=N8N_DIR,
                           env=env_n8n(self.home), capture_output=True, text=True, timeout=180)
        return r.returncode, (r.stdout + r.stderr)

    def prepare_n8n(self):
        os.makedirs(self.home)
        rc, out = self.cli("import:credentials", "--input=" + os.path.join(PROBE, "creds.json"))
        assert rc == 0, "import creds: " + out[-300:]
        for w in FLOWS:
            rc, out = self.cli("import:workflow", "--input=" + os.path.join(PROBE, w + ".json"))
            assert rc == 0, "import %s: %s" % (w, out[-300:])
        for i in PUBLISH_IDS:
            rc, out = self.cli("publish:workflow", "--id=" + i)
            assert rc == 0, "publish %s: %s" % (i, out[-300:])

    def start_n8n(self):
        lg = open(self.n8n_log, "ab")
        self.n8n = subprocess.Popen([os.path.join(N8N_DIR, "node_modules/.bin/n8n"), "start"], cwd=N8N_DIR,
                                    env=env_n8n(self.home), stdout=lg, stderr=lg, start_new_session=True)
        end = time.time() + 90
        while time.time() < end:
            if self.n8n.poll() is not None:
                raise RuntimeError("n8n_exited rc=%s" % self.n8n.returncode)
            if http("GET", "http://127.0.0.1:%d/healthz" % PORT["n8n"], timeout=3)[0] == 200:
                while time.time() < end:  # a GET tells a registered POST-only webhook from an unregistered one
                    code, body = http("GET", "http://127.0.0.1:%d/webhook/mf-form" % PORT["n8n"], timeout=3)
                    if "not registered for GET" in body or "Did you mean" in body:
                        return time.time()
                    time.sleep(0.5)
                raise RuntimeError("webhook_not_registered")
            time.sleep(0.5)
        raise RuntimeError("n8n_not_healthy")

    def kill_n8n(self):
        t = time.time()
        try:
            os.killpg(self.n8n.pid, signal.SIGKILL)
        except (ProcessLookupError, AttributeError):
            pass
        self.n8n.wait()
        return t

    def stop_all(self):
        if self.n8n and self.n8n.poll() is None:
            self.kill_n8n()
        for p in self.procs.values():
            p.terminate()
        for p in self.procs.values():
            try:
                p.wait(8)
            except subprocess.TimeoutExpired:
                p.kill()

    # ---- lead + waiting
    def send(self, lead, email=None, path="mf-form", extra=None, name="Test Person"):
        email = email or (lead.lower() + "@example.test")  # one e-mail per lead: the CRM upsert also matches on e-mail
        body = {"submission_id": lead, "email": email, "name": name}
        body.update(extra or {})
        return http("POST", "http://127.0.0.1:%d/webhook/%s" % (PORT["n8n"], path), body, timeout=60)

    def grep_canaries(self, canary):
        """Search n8n's own folder (database file and logs), n8n.log and an export of every workflow for each planted
        value. The Postgres table is checked apart (it holds e-mail and name by design)."""
        exp = os.path.join(self.wd, "export.json")
        rc, _ = self.cli("export:workflow", "--all", "--output=" + exp)
        hits = {"export_rc": rc}
        targets = {"n8n_folder": self.home, "n8n_log": self.n8n_log, "export_json": exp}
        for tname, path in targets.items():
            for cname, val in canary.items():
                r = subprocess.run(["grep", "-rlaF", "--", val, path], capture_output=True, text=True)
                hits["%s:%s" % (tname, cname)] = [os.path.relpath(x, self.wd) for x in r.stdout.split()]
        for cname, val in canary.items():
            hits["postgres_row:%s" % cname] = sql("SELECT count(*) FROM mf_leads WHERE concat_ws(' ',lead_key,email,name,crm_id) LIKE '%%" + val + "%%'")
        return hits

    def wait_event(self, src, ev, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            for x in self.lines("events.jsonl"):
                d = json.loads(x)
                if d["src"] == src and d["ev"] == ev:
                    return d
            time.sleep(0.05)
        return None

    def states(self):
        out = sql("SELECT lead_key,state,attempts,mail_sent,coalesce(crm_id,'') FROM mf_leads ORDER BY lead_key")
        return [r.split("|") for r in out.splitlines() if r and not r.startswith("ERR")]

    def wait_terminal(self, leads, timeout=330):
        end = time.time() + timeout
        while time.time() < end:
            st = {r[0]: r[1] for r in self.states()}
            if all(st.get(l) in TERMINAL for l in leads):
                return True
            time.sleep(2)
        return False

    def count(self, leads):
        mails = [json.loads(x) for x in self.lines("mails.jsonl")]
        _, crm = http("GET", "http://127.0.0.1:%d/rows" % PORT["crm"])
        _, calls = http("GET", "http://127.0.0.1:%d/calls" % PORT["stage"])
        try:
            crm_rows = json.loads(crm)
        except ValueError:
            crm_rows = {"parse_error": crm[:80]}
        try:
            stage_calls = json.loads(calls)
        except ValueError:
            stage_calls = {"parse_error": calls[:80]}
        res = {}
        for l in leads:
            lm = [m for m in mails if l in m.get("subject", "")]
            res[l] = {
                "stage_requests": _calls_for({"calls": stage_calls.get("requests", {})}, l) if isinstance(stage_calls, dict) else -1,
                "mail_to_intake": sum(1 for m in lm if "intake@example.test" in str(m.get("rcpt"))),
                "alert": sum(1 for m in lm if "alerts@example.test" in str(m.get("rcpt"))),
                "crm_rows": _rows_for(crm_rows, l),
                "stage_calls": _calls_for(stage_calls, l),
            }
        return res


def _rows_for(rows, lead):
    if isinstance(rows, dict):
        rows = rows.get("rows", rows)
    if isinstance(rows, dict):
        return sum(1 for k, v in rows.items() if lead in k or lead in json.dumps(v))
    return sum(1 for v in rows if lead in json.dumps(v))


def _calls_for(calls, lead):
    if isinstance(calls, dict):
        c = calls.get("calls", calls)
        if isinstance(c, dict):
            return c.get(lead, 0) if not isinstance(c.get(lead), (list, dict)) else len(c[lead])
    return sum(1 for v in calls if lead in json.dumps(v)) if isinstance(calls, list) else -1


KILL_AT = {  # point -> (fake, event, ctl file, ctl content)
    "K1": ("stage", "qualify_start", "stage.ctl", {"delay_ms": 6000}),
    "K2": ("crm", "upsert_stored", "crm.ctl", {"upsert_ack_delay_ms": 6000}),
    "K3": ("smtp", "connect", "smtp.ctl", {"pre_s": 6}),
    "K6": ("smtp", "stored", "smtp.ctl", {"delay_s": 6}),
}


def main():
    label, point = sys.argv[1], sys.argv[2]
    r = Run(label)
    out = {"label": label, "point": point, "t_start": time.strftime("%H:%M:%SZ", time.gmtime())}
    out["flows"] = os.environ.get("FLOW_COMMIT", "11:05Z set (59202078)")
    leads = ["L-" + label]
    try:
        r.prepare_n8n()
        sql("TRUNCATE mf_leads")
        r.start_fakes()
        r.start_n8n()
        if point in KILL_AT:
            fake, ev, cf, cc = KILL_AT[point]
            r.ctl(cf, cc)
            import threading
            th = threading.Thread(target=r.send, args=(leads[0],), daemon=True)
            th.start()
            d = r.wait_event(fake, ev)
            out["event_seen"] = bool(d)
            tk = r.kill_n8n()
            r.clear_ctl()
            out["rows_at_kill"] = r.states()
            time.sleep(1)
            t_up = r.start_n8n()
            out["restart_s"] = round(t_up - tk, 1)
        elif point == "control1":
            out["send"] = r.send(leads[0])
        elif point == "control2same":
            out["send1"] = r.send(leads[0])
            out["send2"] = r.send(leads[0])
        elif point == "control2par":
            import concurrent.futures as cf2
            leads = [leads[0] + "-a", leads[0] + "-b"]
            with cf2.ThreadPoolExecutor(2) as ex:
                futs = [ex.submit(r.send, l) for l in leads]
                out["sends"] = [f.result() for f in futs]
        elif point == "control1long":
            out["send"] = r.send(leads[0])
            r.wait_terminal(leads)
            time.sleep(100)  # recovery ticks on a table whose only row is done
        elif point == "burst":
            import concurrent.futures as cf3
            with cf3.ThreadPoolExecutor(10) as ex:
                futs = [ex.submit(r.send, leads[0]) for _ in range(10)]
                rs = [f.result() for f in futs]
            tally = {}
            for code, body in rs:
                try:
                    j = json.loads(body)
                    key = "%s/%s/repeat=%s" % (code, j.get("verdict"), j.get("repeat"))
                except ValueError:
                    key = "%s/%s" % (code, body[:50])
                tally[key] = tally.get(key, 0) + 1
            out["burst_answers"] = tally
        elif point == "error":
            r.ctl("crm.ctl", {"upsert_status": 500})  # the CRM refuses every call: three attempts, then failed + 1 alert
            out["send"] = r.send(leads[0])
        elif point == "grep":
            canary = {"name": "Zelda" + " Quasar-Canary", "email": "zq" + ".canary@example.test",
                      "key": "CANARY" + "KEY" + "-" + "7f3a9c2e"}
            out["send"] = r.send(leads[0], email=canary["email"], name=canary["name"], extra={"api_key": canary["key"]})
            r.wait_terminal(leads)
            time.sleep(35)  # one recovery tick and one error-handler pass
            r.kill_n8n()
            out["grep"] = r.grep_canaries(canary)
        elif point in ("idle", "t14"):
            time.sleep(120 if point == "t14" else 100)  # no lead at all: recovery ticks every 30 s on an empty table
            leads = []
        elif point == "controlbad":
            out["send"] = r.send(leads[0], email="not-an-email")
        elif point == "Fa":
            r.ctl("crm.ctl", {"search_blind_s": 90})
            out["send"] = r.send(leads[0])
        elif point == "Fb":
            r.ctl("smtp.ctl", {"drop": 1})
            out["send"] = r.send(leads[0])
        elif point == "Fc":
            r.ctl("smtp.ctl", {"pre_s": 40})
            out["send"] = r.send(leads[0])
        out["reached_terminal"] = r.wait_terminal(leads, 700 if point == "error" else 330) if leads else True
        time.sleep(20 if leads else 0)  # settle: a late double would show here
        out["states"] = r.states()
        out["counts"] = r.count(leads)
        out["events"] = len(r.lines("events.jsonl"))
        out["all_mails"] = [json.loads(x).get("subject") for x in r.lines("mails.jsonl")]
        out["total_stage_requests"] = sum(1 for x in r.lines("events.jsonl") if "qualify_start" in x or "qualify_repeat" in x)
        out["total_mails"] = len(r.lines("mails.jsonl"))
        out["stage_qualify_events"] = sum(1 for x in r.lines("events.jsonl") if "qualify_start" in x)
        out["crm_upsert_events"] = sum(1 for x in r.lines("events.jsonl") if "upsert_start" in x)
    except Exception as e:  # noqa: BLE001
        out["error"] = "%s: %s" % (type(e).__name__, e)
    finally:
        r.stop_all()
        out["t_end"] = time.strftime("%H:%M:%SZ", time.gmtime())
    line = json.dumps(out)
    with open(os.path.join(K, "results.jsonl"), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


if __name__ == "__main__":
    main()
