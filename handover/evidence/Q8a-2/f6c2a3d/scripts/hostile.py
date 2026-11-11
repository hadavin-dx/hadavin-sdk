"""Step 6: hostile inputs against the receiver started in-process on loopback with a fake signer (made-up data).
argv[1] = path of the file that this process's stderr is redirected to (so server stderr lines are counted per request)."""
import hashlib, hmac, json, os, socket, struct, sys, threading, time
from urllib.parse import urlencode
import hadavin_sdk
from hadavin_sdk.approvals import FakeChannel, receiver
from hadavin_sdk.approvals.requests import Approvals
from hadavin_sdk.approvals.slack_channel import SlackChannel

ERR = sys.argv[1]
fd = os.open(ERR, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_APPEND); os.dup2(fd, 2)
def err_lines(): return len(open(ERR, "rb").read().splitlines())
print("hadavin_sdk imported from:", hadavin_sdk.__file__)
SIG = "sig" + "-evq8a2f"; WRONG = "wrong" + "-secret"; TOKEN = "xoxb" + "-evq8a2f-fake"
PREFIX = "X-Hadavin"
PFX = {"fake kind": "X-Hadavin", "slack kind": "X-Slack"}
OUTBOUND = []
_c = socket.socket.connect
def _g(self, a):
    if isinstance(a, tuple) and a[0] not in ("127.0.0.1", "::1", "localhost"):
        OUTBOUND.append(a); raise OSError("probe guard")
    return _c(self, a)
socket.socket.connect = _g

def sign(body, secret):
    PREFIX = CUR[0]
    ts = str(int(time.time()))
    return {f"{PREFIX}-Request-Timestamp": ts, f"{PREFIX}-Signature": "v0=" + hmac.new(secret.encode(), f"v0:{ts}:".encode() + body, hashlib.sha256).hexdigest()}

def raw_headers(d):  # d: list of (bytes|str, bytes|str)
    out = b""
    for k, v in d:
        k = k.encode("latin-1") if isinstance(k, str) else k; v = v.encode("latin-1") if isinstance(v, str) else v
        out += k + b": " + v + b"\r\n"
    return out

def read_status(s, timeout):
    s.settimeout(timeout); data = b""; note = ""
    try:
        while b"\r\n" not in data:
            p = s.recv(4096)
            if not p: break
            data += p
    except OSError as e:
        note = f" [recv {type(e).__name__}]"
    first = data.split(b"\r\n")[0][:60].decode("latin-1") if data else "no status (0 bytes; connection closed)"
    return first + note

def request(port, first_line, hdrs, body=b"", timeout=15, mode="normal", extra=None):
    t0 = time.time(); s = socket.create_connection(("127.0.0.1", port), timeout=timeout); note = ""
    try:
        head = first_line + b"\r\n" + raw_headers([("Host", "127.0.0.1"), ("Connection", "close")] + hdrs) + b"\r\n"
        try:
            if mode == "normal":
                s.sendall(head + body)
            elif mode == "slow_first_line":      # one byte every 0.5 s, no line end
                for b in first_line[:12]: s.sendall(bytes([b])); time.sleep(0.5)
            elif mode == "slow_headers":         # first line fast, then one header byte every 0.5 s
                s.sendall(first_line + b"\r\n")
                for b in (b"X-Slow: " + b"a" * 40): s.sendall(bytes([b])); time.sleep(0.5)
            elif mode == "slow_body":            # headers fast, body one byte every 0.5 s
                s.sendall(head)
                for b in body: s.sendall(bytes([b])); time.sleep(0.5)
            elif mode == "reset_mid_headers":
                s.sendall(first_line + b"\r\nX-Part: abc"); time.sleep(0.2)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)); s.close(); return "client sent RST mid-headers"
            elif mode == "reset_mid_body":
                s.sendall(head + body[:3]); time.sleep(0.2)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)); s.close(); return "client sent RST mid-body"
            elif mode == "reset_before_answer":  # whole request sent, then RST at once
                s.sendall(head + body)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)); s.close(); return "client sent RST right after the whole request"
        except OSError as e:
            note = f" [send stopped: {type(e).__name__}]"
        r = read_status(s, timeout)
        return f"{r}{note} (client waited {time.time()-t0:.2f}s)"
    finally:
        try: s.close()
        except OSError: pass

CUR = ["X-Hadavin"]
def run(read_timeout, label, make_channel):
    CUR[0] = PFX[label]
    ch = make_channel()
    ap = Approvals(None, None, None, ch, lambda *a: None)
    srv = receiver.serve(ap, port=0, read_timeout_s=read_timeout)
    th = threading.Thread(target=srv.serve_forever, daemon=True); th.start(); port = srv.server_address[1]
    P = ch.callback_path; p = P.encode()
    print(f"\n==== {label}: channel {type(ch).__name__}, path {P!r}, read_timeout_s={read_timeout}, 127.0.0.1:{port}")
    BODY = b"payload=x"
    def hd(body=BODY, cl=None, secret=WRONG):
        h = [(k, v) for k, v in sign(body, secret).items()] + [("Content-Type", "application/x-www-form-urlencoded")]
        if cl is not False: h.append(("Content-Length", str(len(body)) if cl is None else cl))
        return h
    def case(name, *a, **k):
        b = err_lines(); r = request(port, *a, **k); time.sleep(0.4); n = err_lines() - b
        print(f"  {name} -> {r} | server stderr lines: {n}"); sys.stdout.flush()
    POST = b"POST " + p + b" HTTP/1.1"
    print(" -- Content-Length forms (bad signature, 9-byte body sent; first at the right path)")
    forms = [("empty value", [b""]), ("header twice (9 and 9)", [b"9", b"9"]), ("header twice (9 and 5)", [b"9", b"5"]), ("12 digits (999999999999)", [b"9" * 12]),
             ("13 digits", [b"9" * 13]), ("4000 digits", [b"9" * 4000]), ("4301 digits", [b"9" * 4301]), ("10000 digits", [b"9" * 10000]),
             ("minus 5", [b"-5"]), ("plus 5", [b"+5"]), ("plus 9", [b"+9"]), ("Arabic-Indic digit U+0665 as UTF-8 bytes", ["٥".encode()]), ("fullwidth digit U+FF15 as UTF-8 bytes", ["５".encode()]),
             ("superscript two U+00B2 latin-1 byte", [b"\xb2"]), ("hex 0x10", [b"0x10"]), ("hex 0x9", [b"0x9"]), ("underscore 1_0", [b"1_0"]), ("float 9.0", [b"9.0"]), ("1e1", [b"1e1"]),
             ("trailing space (9 )", [b"9 "]), ("leading space ( 9)", [b" 9"]), ("zero", [b"0"]), ("leading zeros 0009", [b"0009"]), ("65536 (limit) but 9 bytes sent", [b"65536"]),
             ("65537", [b"65537"]), ("no Content-Length header", None)]
    for name, vals in forms:
        if vals is None: hs = [(k, v) for k, v in sign(BODY, WRONG).items()]
        else: hs = [(k, v) for k, v in sign(BODY, WRONG).items()] + [("Content-Length", v) for v in vals]
        case(f"CL {name}", POST, hs, BODY, timeout=(read_timeout + 4 if name.startswith("65536") else 15))
    print(" -- same Content-Length forms at a WRONG path (expect 404 whatever the header)")
    for name, vals in forms[:13]:
        hs = [(k, v) for k, v in sign(BODY, WRONG).items()] + ([("Content-Length", v) for v in vals] if vals else [])
        case(f"wrong path, CL {name}", b"POST /nope HTTP/1.1", hs, BODY)
    print(" -- slow and short requests")
    case("slow first line (1 byte / 0.5 s, never ends)", POST, hd(), BODY, mode="slow_first_line", timeout=read_timeout + 6)
    case("slow headers (1 byte / 0.5 s)", POST, hd(), BODY, mode="slow_headers", timeout=read_timeout + 6)
    case("slow body (CL 30, 1 byte / 0.5 s, 30 bytes)", POST, hd(b"x" * 30), b"x" * 30, mode="slow_body", timeout=read_timeout + 6)
    case("short body (CL 100, 9 sent, connection kept open)", POST, hd(BODY, cl="100"), BODY, timeout=read_timeout + 6)
    case("nothing sent after connect", b"", [], b"", mode="slow_first_line", timeout=read_timeout + 6) if False else None
    s = socket.create_connection(("127.0.0.1", port)); b = err_lines(); t0 = time.time(); r = read_status(s, read_timeout + 6); s.close(); time.sleep(0.4)
    print(f"  connect and send nothing -> {r} (waited {time.time()-t0:.2f}s) | server stderr lines: {err_lines()-b}")
    print(" -- connection reset")
    case("RST mid-headers", POST, hd(), BODY, mode="reset_mid_headers")
    case("RST mid-body (CL 30, 3 sent)", POST, hd(b"x" * 30), b"x" * 30, mode="reset_mid_body")
    case("RST right after the whole bad-signature request", POST, hd(), BODY, mode="reset_before_answer")
    sb = urlencode({"payload": json.dumps({"user": {"id": "U1"}, "actions": [{"value": "ap-evq8a2f|" + "0" * 64 + "|0|approve"}]})}).encode()
    case("RST right after a correctly signed request (handler fails: store is None)", POST, hd(sb, secret=SIG), sb, mode="reset_before_answer")
    print(" -- header count and size")
    for n in (99, 100, 101, 200, 5000):
        hs = hd() + [(f"X-H{i}", "v") for i in range(n)]
        case(f"{n} extra headers (+ {len(hd())+2} normal)", POST, hs, BODY)
    case("one header value of 70000 bytes", POST, hd() + [("X-Big", b"a" * 70000)], BODY)
    case("request line of 70000 bytes", b"POST /" + b"a" * 70000 + b" HTTP/1.1", hd(), BODY)
    print(" -- request line forms (bad signature; right path unless said)")
    forms2 = [("tab between words", b"POST\t" + p + b"\tHTTP/1.1"), ("vertical tab", b"POST\x0b" + p + b"\x0bHTTP/1.1"), ("0x1C", b"POST\x1c" + p + b"\x1cHTTP/1.1"),
              ("two spaces", b"POST  " + p + b"  HTTP/1.1"), ("doubled slash path", b"POST /" + p + b" HTTP/1.1"), ("tripled slash path", b"POST //" + p + b" HTTP/1.1"),
              ("percent-encoded first letter", b"POST /%" + (hex(ord(P[1]))[2:]).encode() + P[2:].encode() + b" HTTP/1.1"), ("percent-encoded slash", b"POST /" + P[1:].replace("/", "%2F").encode() + b" HTTP/1.1"),
              ("query on right path", b"POST " + p + b"?a=1 HTTP/1.1"), ("trailing slash", b"POST " + p + b"/ HTTP/1.1"), ("no version (HTTP/0.9 style)", b"POST " + p),
              ("lowercase method", b"post " + p + b" HTTP/1.1"), ("absolute form", b"POST http://127.0.0.1" + p + b" HTTP/1.1"), ("path then extra word", b"POST " + p + b" x HTTP/1.1"),
              ("no-break space (latin-1 0xA0) between words", b"POST\xa0" + p + b"\xa0HTTP/1.1")]
    for name, line in forms2:
        case(name, line, hd(), BODY)
    print(" -- failure inside the handler")
    case("correctly signed click, store None (handler raises AttributeError)", POST, hd(sb, secret=SIG), sb)
    case("correctly signed click, store None, second time", POST, hd(sb, secret=SIG), sb)
    case("right path, correct signature, 70000-byte body", POST, hd(b"a" * 70000, secret=SIG), b"a" * 70000)
    case("GET on the right path", b"GET " + p + b" HTTP/1.1", [], b"")
    case("PUT on the right path", b"PUT " + p + b" HTTP/1.1", hd(), BODY)
    time.sleep(0.5); srv.shutdown(); srv.server_close(); th.join(5); print(f"  server closed; thread alive: {th.is_alive()}")

run(2.0, "fake kind", lambda: FakeChannel(SIG))
run(2.0, "slack kind", lambda: SlackChannel("C1", TOKEN, SIG))

print("\n==== str-subclass path")
class P(str):
    def __eq__(self, o): return True
    __hash__ = str.__hash__
class Ch(FakeChannel):
    pass
ch = FakeChannel(SIG); ch.callback_path = P("/fake/actions") if False else P("/x/y")
b = err_lines()
try:
    srv = receiver.serve(Approvals(None, None, None, ch, lambda *a: None), port=0)
    print("  serve() with a str-subclass path (__eq__ always True) returned a server (NOT refused)")
    srv.server_close()
except Exception as e:
    print(f"  serve() with a str-subclass path (__eq__ always True) raised {type(e).__name__}: {str(e)[:200]}")
class P2(str): pass
ch2 = FakeChannel(SIG); ch2.callback_path = P2("/x/y")
try:
    srv = receiver.serve(Approvals(None, None, None, ch2, lambda *a: None), port=0); print("  serve() with a plain str subclass (no override) returned a server (NOT refused)"); srv.server_close()
except Exception as e:
    print(f"  serve() with a plain str subclass raised {type(e).__name__}: {str(e)[:200]}")
print(f"\nnon-loopback connections attempted: {len(OUTBOUND)}; threads alive: {[t.name for t in threading.enumerate()]}")
