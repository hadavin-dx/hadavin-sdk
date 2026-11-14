"""Stand-in mail catcher for the error notifier (made-up, loopback only). Accepts any message on a plain SMTP port, writes one JSON line per message
(envelope recipients, subject, text body) to the file given. Nothing is relayed anywhere. python smtp_catcher.py PORT FILE"""
import socketserver, sys, json, base64, time, email
PORT, FILE = int(sys.argv[1]), sys.argv[2]
class H(socketserver.StreamRequestHandler):
    def w(self, s): self.wfile.write((s + "\r\n").encode()); self.wfile.flush()
    def handle(self):
        rcpt, frm, data = [], "", None
        self.w("220 catcher ready")
        while True:
            line = self.rfile.readline()
            if not line: return
            cmd = line.decode(errors="replace").strip(); u = cmd.upper()
            if u.startswith("EHLO"): self.w("250-catcher"); self.w("250 AUTH PLAIN LOGIN")
            elif u.startswith("HELO"): self.w("250 catcher")
            elif u.startswith("AUTH PLAIN"): self.w("235 ok")
            elif u.startswith("AUTH LOGIN"):
                self.w("334 VXNlcm5hbWU6"); self.rfile.readline(); self.w("334 UGFzc3dvcmQ6"); self.rfile.readline(); self.w("235 ok")
            elif u.startswith("MAIL FROM"): frm = cmd[10:].strip(); self.w("250 ok")
            elif u.startswith("RCPT TO"): rcpt.append(cmd[8:].strip().strip("<>")); self.w("250 ok")
            elif u == "DATA":
                self.w("354 go"); buf = []
                while True:
                    l = self.rfile.readline()
                    if not l or l in (b".\r\n", b".\n"): break
                    buf.append(l)
                m = email.message_from_bytes(b"".join(buf)); body = m.get_payload(decode=True) if not m.is_multipart() else b""
                with open(FILE, "a") as f: f.write(json.dumps({"t": time.time(), "to": rcpt, "subject": str(m.get("Subject")), "body": (body or b"").decode(errors="replace"), "headers": [k for k in m.keys()]}) + "\n")
                self.w("250 queued"); rcpt = []
            elif u == "QUIT": self.w("221 bye"); return
            elif u == "RSET": rcpt = []; self.w("250 ok")
            else: self.w("250 ok")
class S(socketserver.ThreadingTCPServer): allow_reuse_address = True; daemon_threads = True
S(("127.0.0.1", PORT), H).serve_forever()
