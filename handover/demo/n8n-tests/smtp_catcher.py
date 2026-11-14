"""Stand-in mail catcher for the error notifier (made-up, loopback only). Accepts any message on a plain SMTP port, writes one JSON line per message
(envelope recipients, subject, text body) to the file given. Nothing is relayed anywhere. python smtp_catcher.py PORT FILE"""
import socketserver, sys, json, base64, time, email
PORT, FILE = int(sys.argv[1]), sys.argv[2]
class H(socketserver.StreamRequestHandler):
    def w(self, s): self.wfile.write((s + "\r\n").encode()); self.wfile.flush()
    def handle(self):
        rcpt, frm, data = [], "", None
        with open(FILE + ".conn", "a") as f: f.write(json.dumps({"t": time.time()}) + "\n")          # one line per connection (counts SMTP node executions)
        try: pre = float(open(FILE + ".pre").read().strip() or 0)                                  # optional: seconds to wait BEFORE the greeting (D-N2a)
        except (OSError, ValueError): pre = 0
        if pre > 0: time.sleep(pre)
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
            elif u.startswith("RCPT TO"):
                r = cmd[8:].strip().strip("<>")
                try: nf, sub = open(FILE + ".rcptfail").read().strip().split("|", 1); nf = int(nf)                # fault mode (AF1): "N|text": answer 451 (try later) to the next N recipients whose address contains text, nothing stored
                except (OSError, ValueError): nf, sub = 0, None
                if nf > 0 and sub in r: open(FILE + ".rcptfail", "w").write("%d|%s" % (nf - 1, sub)); self.w("451 try later"); continue
                rcpt.append(r); self.w("250 ok")
            elif u == "DATA":
                self.w("354 go"); buf = []
                while True:
                    l = self.rfile.readline()
                    if not l or l in (b".\r\n", b".\n"): break
                    buf.append(l)
                m = email.message_from_bytes(b"".join(buf)); body = m.get_payload(decode=True) if not m.is_multipart() else b""
                with open(FILE, "a") as f: f.write(json.dumps({"t": time.time(), "to": rcpt, "subject": str(m.get("Subject")), "body": (body or b"").decode(errors="replace"), "headers": [k for k in m.keys()]}) + "\n")
                try: d = float(open(FILE + ".delay").read().strip() or 0)   # optional: seconds to wait AFTER storing, BEFORE the acknowledgement (D-N2 kill tests)
                except (OSError, ValueError): d = 0
                if d > 0: time.sleep(d)
                try: drop = int(open(FILE + ".drop").read().strip() or 0)                          # fault mode: accept the mail (stored above), then drop the connection without the acknowledgement; the number = messages still to drop
                except (OSError, ValueError): drop = 0
                if drop > 0:
                    open(FILE + ".drop", "w").write(str(drop - 1)); return
                self.w("250 queued"); rcpt = []
            elif u == "QUIT": self.w("221 bye"); return
            elif u == "RSET": rcpt = []; self.w("250 ok")
            else: self.w("250 ok")
class S(socketserver.ThreadingTCPServer): allow_reuse_address = True; daemon_threads = True
S(("127.0.0.1", PORT), H).serve_forever()
