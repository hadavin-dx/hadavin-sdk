"""Made-up CRM stand-in for the D-N2 tests (loopback only). Like HubSpot, it has NO unique constraint on the lead id property: search-then-create can double if two runs race.
  POST /search {lead_key} -> {results:[...]}      POST /create {lead_key,...} -> 201      GET /rows      POST /control {search_delay_ms, create_ack_delay_ms, upsert_delay_ms, upsert_ack_delay_ms, search_blind_s}
  POST /upsert {hadavin_lead_id, email, label} -> 200 {id, created}: create-or-update keyed on the lead id property AND on the e-mail (Design A, v2). Fault modes (D-N2a): search_blind_s = search answers EMPTY for N s after a row was written (like a slow index);
  upsert_delay_ms = hold the request BEFORE it is stored (one-shot); upsert_ack_delay_ms = store FIRST, answer late (one-shot).
A search delay holds the answer back; a create ack delay stores the row FIRST and answers late (a test kills n8n inside that gap). Every request is logged to FILE."""
import json, sys, time, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
PORT, FILE = int(sys.argv[1]), sys.argv[2]
ROWS, CTL, LK = [], {"search_delay_ms": 0, "create_ack_delay_ms": 0, "upsert_delay_ms": 0, "upsert_ack_delay_ms": 0, "search_blind_s": 0}, threading.Lock()
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
            hits = [r for r in ROWS if r["lead_key"] == o.get("lead_key") and time.time() - r.get("t", 0) >= CTL["search_blind_s"]]
            if d: CTL["search_delay_ms"] = 0; time.sleep(d)          # one-shot
            return self._j(200, {"results": hits})
        if self.path == "/create":
            ROWS.append({"lead_key": o.get("lead_key"), "email": o.get("email"), "label": o.get("label"), "t": time.time()}); log(op="create", lead_key=o.get("lead_key"))
            d = CTL["create_ack_delay_ms"] / 1000
            if d: CTL["create_ack_delay_ms"] = 0; time.sleep(d)    # one-shot
            return self._j(201, {"id": len(ROWS)})
        if self.path == "/upsert":
            k = o.get("hadavin_lead_id"); log(op="upsert_start", lead_key=k); d = CTL["upsert_delay_ms"] / 1000
            if d: CTL["upsert_delay_ms"] = 0; time.sleep(d)
            with LK:
                hit = [r for r in ROWS if r["lead_key"] == k or (o.get("email") and r.get("email") == o.get("email"))]
                if hit: hit[0].update(label=o.get("label")); rid, created = ROWS.index(hit[0]) + 1, False
                else: ROWS.append({"lead_key": k, "email": o.get("email"), "label": o.get("label"), "t": time.time()}); rid, created = len(ROWS), True
            log(op="upsert", lead_key=k, created=created); d = CTL["upsert_ack_delay_ms"] / 1000
            if d: CTL["upsert_ack_delay_ms"] = 0; time.sleep(d)
            return self._j(200, {"id": rid, "created": created})
        self._j(404, {})
ThreadingHTTPServer.allow_reuse_address = True
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
