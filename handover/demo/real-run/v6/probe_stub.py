"""Loopback-only stand-in for the HubSpot calls of scripts/hubspot_probe.py (made-up data, no network beyond 127.0.0.1).

usage: probe_stub.py MODE PORTFILE [TOKEN_TO_ECHO]
 MODE happy      every step passes (404 for the tag property, 1 owner, create 201, patch 200, read-back equal, gdpr 204)
 MODE owners403  the owner list is refused with 403
 MODE echo       the create call is refused with 400 and the message holds TOKEN_TO_ECHO (the probe must mask it)
 MODE createlost the create answer is 500 (the probe must fall back to delete-by-email)
Writes the chosen port to PORTFILE, logs each step name to PORTFILE.log, serves until it is killed."""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

mode, portfile = sys.argv[1], sys.argv[2]
echo = sys.argv[3] if len(sys.argv) > 3 else ""
OWNER = "90001234"
OK = {"properties": {"hs_lead_status": "OPEN", "hubspot_owner_id": OWNER}}


class H(BaseHTTPRequestHandler):
    def _go(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)
        p, m = self.path, self.command
        if "/properties/" in p:
            step, st, body = "tag", 404, {}
        elif "/owners" in p:
            step, st, body = "owners", (403 if mode == "owners403" else 200), (
                {"message": "missing scopes"} if mode == "owners403" else {"results": [{"id": OWNER}]})
        elif p.endswith("gdpr-delete"):
            step, st, body = "gdpr", 204, {}
        elif m == "POST":
            step = "create"
            if mode == "echo":
                st, body = 400, {"category": "VALIDATION_ERROR", "message": "bad " + echo}
            elif mode == "createlost":
                st, body = 500, {}
            else:
                st, body = 201, {"id": "5550001"}
        elif m == "PATCH":
            step, st, body = "patch", 200, {}
        elif m == "DELETE":
            step, st, body = "delete", 204, {}
        else:
            step, st, body = "readback", 200, OK
        with open(portfile + ".log", "a") as f:
            f.write(step + "\n")
        raw = json.dumps(body).encode()
        self.send_response(st)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    do_GET = do_POST = do_PATCH = do_DELETE = _go

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 0), H)
open(portfile, "w").write(str(srv.server_port))
srv.serve_forever()
