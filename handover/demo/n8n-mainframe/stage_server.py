"""The desk STAGE the n8n main frame calls (D-N2, part C). A thin wrapper around the desk's OWN code: it imports lead_desk.live_claude (LiveQualifier, SpendLedger: reserve before the call,
settle after, caps) and exposes it over HTTP. NEW code here (the desk has no stage endpoint for this): about 45 lines, in this file only; the desk's source is not touched.
  POST /qualify {lead_key, email} -> {label, cached}    per-lead journal so a re-run never calls the model twice: 'started' is written BEFORE the call; a lead with 'started' but no label
                                                        (killed mid-call) is NOT called again: answer {label:"unknown", unknown_model:true} (money-safe, a person decides)
  GET  /mail_count?key=K -> {count} from the mail stand-in file (the second count, from the receiving side)
Run from the desk checkout with the desk's live-model settings in the environment (as dn1_common.denv()).  python stage_server.py PORT JOURNAL_FILE MAIL_FILE"""
import json, sys, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from lead_desk import config
from lead_desk.live_claude import LiveQualifier
import time
PORT, JOURNAL, MAILF = int(sys.argv[1]), sys.argv[2], sys.argv[3]
CTL = {"mode": "ok", "sleep": 40}
Q = LiveQualifier(config._live_from_env(os.environ)); LK = threading.Lock()
def journal():
    d = {}
    try:
        for l in open(JOURNAL):
            r = json.loads(l); d.setdefault(r["lead_key"], {}).update(r)
    except OSError: pass
    return d
def jw(**r):
    with open(JOURNAL, "a") as f: f.write(json.dumps(r) + "\n"); f.flush(); os.fsync(f.fileno())
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _j(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urlsplit(self.path)
        if u.path == "/mail_count":
            k = parse_qs(u.query).get("key", [""])[0]
            try: n = sum(1 for l in open(MAILF) if l.strip() and k in json.loads(l).get("subject", ""))
            except OSError: n = 0
            return self._j(200, {"count": n})
        self._j(404, {})
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); o = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/control": CTL.update(o); return self._j(200, CTL)
        if self.path != "/qualify": return self._j(404, {})
        k = o["lead_key"]
        if CTL["mode"] == "refuse": return self._j(403, {"error": "refused"})                  # fault mode (D-N2a): the cap stage refuses / errors / does not answer in time
        if CTL["mode"] == "error": return self._j(500, {"error": "stage_error"})
        if CTL["mode"] == "timeout": time.sleep(float(CTL.get("sleep", 40))); return self._j(200, {"label": "warm", "late": True})
        with LK:
            j = journal().get(k, {})
            if j.get("label"): return self._j(200, {"label": j["label"], "cached": True})
            if j.get("started"): return self._j(200, {"label": "unknown", "unknown_model": True, "cached": True})
            jw(lead_key=k, started=True)
        c0 = Q.calls
        try: lab = Q.qualify(k, o.get("email", ""))
        except Exception as e:
            if Q.calls == c0: jw(lead_key=k, started=False)      # failed before the network step (cap, ledger): nothing was sent, a re-run may try again
            return self._j(502, {"error": type(e).__name__})
        jw(lead_key=k, label=lab); self._j(200, {"label": lab, "cached": False})
ThreadingHTTPServer.allow_reuse_address = True
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
