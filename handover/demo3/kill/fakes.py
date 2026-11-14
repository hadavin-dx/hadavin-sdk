"""lane3 kill script: loopback stand-ins (CRM, stage, SMTP catcher). Made-up data only. Own code, written from the
flow JSON and the Design A README. Usage: python fakes.py crm|stage|smtp PORT WORKDIR
Every fake appends one JSON line per event to WORKDIR/events.jsonl (flushed and fsynced) so a driver can react to an event."""
import base64
import json
import os
import socketserver
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_EV_LOCK = threading.Lock()


def event(workdir, src, ev, **kw):
    line = json.dumps({"t": round(time.time(), 3), "src": src, "ev": ev, **kw})
    with _EV_LOCK, open(os.path.join(workdir, "events.jsonl"), "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_ctl(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_ctl(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def make_http(src, workdir, handle):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            return

        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            try:
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                event(workdir, src, "peer_closed_before_answer", path=self.path)

        def do_GET(self):
            code, obj = handle("GET", self.path, {})
            self._send(code, obj)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b""
            try:
                body = json.loads(raw or b"{}")
            except ValueError:
                body = {}
            code, obj = handle("POST", self.path, body)
            self._send(code, obj)

    return H


def crm(port, workdir):
    rows, lock, ctl_path = {}, threading.Lock(), os.path.join(workdir, "crm.ctl")
    state = {"blind_until": 0.0}

    def take(key):
        ctl = read_ctl(ctl_path)
        v = ctl.pop(key, 0)
        if v:
            write_ctl(ctl_path, ctl)
        return v

    def handle(method, path, body):
        if method == "GET" and path == "/rows":
            with lock:
                return 200, {"rows": list(rows.values())}
        if path == "/control":
            write_ctl(ctl_path, body)
            return 200, {"ok": True}
        if path == "/upsert":
            lead, email = body.get("hadavin_lead_id"), body.get("email")
            event(workdir, "crm", "upsert_start", lead=lead)
            d = take("upsert_delay_ms")
            if d:
                time.sleep(d / 1000)
            refuse = read_ctl(ctl_path).get("upsert_status")  # persistent fault: the CRM answers an error for every call
            if refuse:
                event(workdir, "crm", "upsert_refused", lead=lead, status=int(refuse))
                return int(refuse), {"error": "refused"}
            with lock:
                hit = next((r for r in rows.values() if r["lead"] == lead or r["email"] == email), None)
                created = hit is None
                if created:
                    hit = {"id": "crm-%d" % (len(rows) + 1), "lead": lead, "email": email, "label": body.get("label")}
                    rows[hit["id"]] = hit
                state["blind_until"] = time.time() + (take("search_blind_s") or 0)
            event(workdir, "crm", "upsert_stored", lead=lead, created=created)
            a = take("upsert_ack_delay_ms")
            if a:
                time.sleep(a / 1000)
            return 200, {"id": hit["id"], "created": created}
        if path == "/search":
            event(workdir, "crm", "search", lead=body.get("lead_key"))
            if time.time() < state["blind_until"]:
                return 200, {"results": []}
            with lock:
                return 200, {"results": [r for r in rows.values() if r["lead"] == body.get("lead_key")]}
        if path == "/create":
            lead = body.get("hadavin_lead_id") or body.get("lead_key")
            with lock:
                rid = "crm-%d" % (len(rows) + 1)
                rows[rid] = {"id": rid, "lead": lead, "email": body.get("email"), "label": body.get("label")}
            event(workdir, "crm", "create", lead=lead)
            return 200, {"id": rid, "created": True}
        return 404, {"error": "no such path"}

    return ThreadingHTTPServer(("127.0.0.1", port), make_http("crm", workdir, handle))


def stage(port, workdir):
    """Stage stand-in following the README rule: a per-lead journal. First request = one model call (journal
    'started', then 'answered' when the simulated call ends, even if the caller has died). A repeat after the answer
    returns the same label with NO new model call; a repeat while the call is still open returns label 'unknown'
    with NO new model call. requests counts HTTP requests; model_calls counts simulated paid calls."""
    requests, model_calls, journal, lock = {}, {}, {}, threading.Lock()
    ctl_path = os.path.join(workdir, "stage.ctl")

    def handle(method, path, body):
        if path == "/control":
            write_ctl(ctl_path, body)
            return 200, {"ok": True}
        if method == "GET" and path == "/calls":
            with lock:
                return 200, {"calls": dict(model_calls), "requests": dict(requests)}
        if path == "/qualify":
            lead = str(body.get("lead_key"))
            with lock:
                requests[lead] = requests.get(lead, 0) + 1
                j = journal.get(lead)
                if j is None:
                    journal[lead] = {"state": "started"}
                    model_calls[lead] = model_calls.get(lead, 0) + 1
                    first = True
                else:
                    first = False
            if not first:
                with lock:
                    j = journal[lead]
                    label = j.get("label", "unknown") if j["state"] == "answered" else "unknown"
                event(workdir, "stage", "qualify_repeat", lead=lead, answered=j["state"] == "answered", label=label)
                return 200, {"label": label, "lead_key": lead}
            event(workdir, "stage", "qualify_start", lead=lead, n=requests[lead])
            d = read_ctl(ctl_path).get("delay_ms", 0)
            if d:
                time.sleep(d / 1000)
            label = ("hot", "warm", "cold")[sum(map(ord, lead)) % 3]
            with lock:
                journal[lead] = {"state": "answered", "label": label}
            return 200, {"label": label, "lead_key": lead}
        return 404, {"error": "no such path"}

    return ThreadingHTTPServer(("127.0.0.1", port), make_http("stage", workdir, handle))


class SmtpHandler(socketserver.StreamRequestHandler):
    workdir = "."

    def reply(self, text):
        self.wfile.write((text + "\r\n").encode())
        self.wfile.flush()

    def handle(self):
        wd, ctl_path = self.workdir, os.path.join(self.workdir, "smtp.ctl")
        ctl = read_ctl(ctl_path)
        event(wd, "smtp", "connect")
        if ctl.get("pre_s"):
            time.sleep(ctl["pre_s"])
        self.reply("220 stand-in ESMTP")
        rcpts, subject, body_lines = [], "", []
        while True:
            line = self.rfile.readline()
            if not line:
                return
            cmd = line.decode("latin-1").strip()
            up = cmd.upper()
            if up.startswith("EHLO") or up.startswith("HELO"):
                self.wfile.write(b"250-stand-in\r\n250-AUTH PLAIN LOGIN\r\n250 8BITMIME\r\n")
                self.wfile.flush()
            elif up.startswith("AUTH PLAIN"):
                self.reply("235 ok")
            elif up == "AUTH LOGIN":
                self.reply("334 VXNlcm5hbWU6")
                self.rfile.readline()
                self.reply("334 UGFzc3dvcmQ6")
                self.rfile.readline()
                self.reply("235 ok")
            elif up.startswith("MAIL FROM"):
                self.reply("250 ok")
            elif up.startswith("RCPT TO"):
                rcpts.append(cmd.split(":", 1)[1].strip().strip("<>"))
                self.reply("250 ok")
            elif up == "DATA":
                self.reply("354 go")
                body_lines = []
                while True:
                    ln = self.rfile.readline()
                    if not ln:
                        return
                    t = ln.decode("latin-1").rstrip("\r\n")
                    if t == ".":
                        break
                    body_lines.append(t)
                for t in body_lines:
                    if t.lower().startswith("subject:"):
                        subject = t.split(":", 1)[1].strip()
                        if subject.startswith("=?"):
                            try:
                                import email.header as eh
                                subject = str(eh.make_header(eh.decode_header(subject)))
                            except Exception:
                                pass
                        break
                with open(os.path.join(wd, "mails.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps({"t": round(time.time(), 3), "rcpt": rcpts, "subject": subject}) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                event(wd, "smtp", "stored", subject=subject, rcpt=rcpts)
                ctl = read_ctl(ctl_path)
                if ctl.get("drop", 0) > 0:
                    ctl["drop"] -= 1
                    write_ctl(ctl_path, ctl)
                    event(wd, "smtp", "dropped_after_store")
                    return
                if ctl.get("delay_s"):
                    time.sleep(ctl["delay_s"])
                self.reply("250 queued")
            elif up == "QUIT":
                self.reply("221 bye")
                return
            elif up == "RSET":
                self.reply("250 ok")
            else:
                self.reply("250 ok")


class ThreadedSmtp(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def smtp(port, workdir):
    SmtpHandler.workdir = workdir
    return ThreadedSmtp(("127.0.0.1", port), SmtpHandler)


if __name__ == "__main__":
    kind, port, workdir = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    os.makedirs(workdir, exist_ok=True)
    srv = {"crm": crm, "stage": stage, "smtp": smtp}[kind](port, workdir)
    event(workdir, kind, "up", port=port)
    srv.serve_forever()
