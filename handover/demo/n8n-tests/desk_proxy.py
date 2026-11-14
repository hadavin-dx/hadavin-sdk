"""Test instrument, loopback, made-up data: a pass-through between n8n and the desk that logs one JSON line per request it forwards
(time, source_ref, the desk's status or the error). It lets a test count how many times n8n really called the desk (retries included).
When the desk cannot be reached or drops the connection, it drops the caller's connection without any answer (what n8n would see from the desk itself).
python desk_proxy.py LISTEN_PORT DESK_PORT LOGFILE"""
import json, sys, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
LP, DP, LOG = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
def log(d):
    with open(LOG, "a") as f: f.write(json.dumps(d) + "\n")
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n); t0 = time.time()
        try: ref = json.loads(body).get("source_ref")
        except Exception: ref = None
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (DP, self.path), body, {"Content-Type": self.headers.get("Content-Type", "application/json")}, method="POST")
        try:
            try:
                with urllib.request.urlopen(req, timeout=60) as r: st, data = r.status, r.read()
            except urllib.error.HTTPError as e: st, data = e.code, e.read()
        except Exception as e:
            log({"t": t0, "ref": ref, "error": type(e).__name__, "secs": round(time.time() - t0, 2)}); self.close_connection = True
            try: self.connection.shutdown(2)
            except OSError: pass
            return
        log({"t": t0, "ref": ref, "status": st, "secs": round(time.time() - t0, 2)})
        try:
            self.send_response(st); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        except OSError: pass
class S(ThreadingHTTPServer): allow_reuse_address = True; daemon_threads = True
S(("127.0.0.1", LP), H).serve_forever()
