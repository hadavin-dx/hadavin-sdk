"""Made-up CRM stand-in for the D-N2 tests (loopback only). Like HubSpot, it has NO unique constraint on the lead id property: search-then-create can double if two runs race.
  POST /search {lead_key} -> {results:[...]}      POST /create {lead_key,...} -> 201      GET /rows      POST /control {search_delay_ms, create_ack_delay_ms}
A search delay holds the answer back; a create ack delay stores the row FIRST and answers late (a test kills n8n inside that gap). Every request is logged to FILE."""
import json, sys, time, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
PORT, FILE = int(sys.argv[1]), sys.argv[2]
ROWS, CTL, LK = [], {"search_delay_ms": 0, "create_ack_delay_ms": 0}, threading.Lock()
def log(**k):
    with LK, open(FILE, "a") as f: f.write(json.dumps(dict(t=time.time(), **k)) + "\n")
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _j(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.startswith("/rows"): return self._j(200, {"rows": ROWS})
        self._j(404, {})
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); o = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/control": CTL.update({k: o[k] for k in CTL if k in o}); return self._j(200, CTL)
        if self.path == "/search":
            log(op="search", lead_key=o.get("lead_key")); d = CTL["search_delay_ms"] / 1000
            hits = [r for r in ROWS if r["lead_key"] == o.get("lead_key")]
            if d: CTL["search_delay_ms"] = 0; time.sleep(d)          # one-shot
            return self._j(200, {"results": hits})
        if self.path == "/create":
            ROWS.append({"lead_key": o.get("lead_key"), "email": o.get("email"), "label": o.get("label")}); log(op="create", lead_key=o.get("lead_key"))
            d = CTL["create_ack_delay_ms"] / 1000
            if d: CTL["create_ack_delay_ms"] = 0; time.sleep(d)    # one-shot
            return self._j(201, {"id": len(ROWS)})
        self._j(404, {})
ThreadingHTTPServer.allow_reuse_address = True
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
