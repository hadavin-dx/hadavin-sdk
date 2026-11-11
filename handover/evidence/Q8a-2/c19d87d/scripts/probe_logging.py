"""EV own probes (typed from the Q8a-2 ticket path table and the batch-4 fix list; not the builder's tests).
Own approvals stub, raw sockets, a log handler on logger hadavin_sdk.receiver. Prints one line per probe."""
import logging, socket, threading, time, sys
from hadavin_sdk.approvals import receiver
import hadavin_sdk
print("SRC", hadavin_sdk.__file__)
class Chan:
    name = "stub"; callback_path = "/channel/actions"
class Stub:
    channel = Chan()
    def __init__(s): s.mode = None; s.delay = 0
    def receive(s, headers, body, record_only=False):
        time.sleep(s.delay)
        if s.mode is not None: raise s.mode
        return True, "recorded"
class Cap(logging.Handler):
    def __init__(s): super().__init__(logging.DEBUG); s.recs = []
    def emit(s, r): s.recs.append((r.levelname, r.getMessage()))
cap = Cap(); lg = logging.getLogger("hadavin_sdk.receiver"); lg.addHandler(cap); lg.setLevel(logging.DEBUG); lg.propagate = False
def start(stub, bound=3.0):
    srv = receiver.serve(stub, port=0, read_timeout_s=bound)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    return srv, t, srv.server_address[1]
def stop(srv, t): srv.shutdown(); srv.server_close(); t.join(5)
def raw(port, data, read=True, wait=1.0):
    c = socket.create_connection(("127.0.0.1", port), timeout=5); c.sendall(data)
    out = b""
    if read:
        c.settimeout(wait)
        try:
            while True:
                d = c.recv(4096)
                if not d: break
                out += d
        except OSError: pass
    c.close(); return out
def status(b): return b.split(b" ")[1].decode() if b.startswith(b"HTTP") else repr(b[:20])
def post(path, body=b"x=1", extra=b""): return b"POST " + path.encode() + b" HTTP/1.1\r\nHost: x\r\nContent-Length: " + str(len(body)).encode() + b"\r\n" + extra + b"\r\n" + body
def levels(since=0): return [(l, m) for l, m in cap.recs[since:] if l != "DEBUG" or "request ended" in m]
stub = Stub(); srv, t, port = start(stub)
try:
    # path table: configured path handled, anything else 404, the vendor path 404, // prefix 404
    for p in ["/channel/actions", "/slack/actions", "/other", "//channel/actions", "/channel/actions/", "/channel/actions?x=1", "/CHANNEL/actions", "/"]:
        print(f"PATH {p!r}: status {status(raw(port, post(p)))}")
    # handler failures of every kind: expect 500 and exactly one ERROR line, kind only
    for exc in [RuntimeError("secret text"), ConnectionRefusedError("secret text"), ConnectionResetError("secret text"), BrokenPipeError("secret text"), TimeoutError("secret text"), OSError("secret text"), ConnectionAbortedError("secret text")]:
        stub.mode = exc; n = len(cap.recs); o = raw(port, post("/channel/actions")); time.sleep(0.3)
        ls = levels(n); errs = [m for l, m in ls if l == "ERROR"]
        print(f"HANDLER {type(exc).__name__}: status {status(o)}; ERROR lines {len(errs)} {errs}; DEBUG error lines {[m for l,m in ls if l=='DEBUG']}; secret in log: {any('secret' in m for l,m in cap.recs[n:])}")
    # handler fails and the caller leaves before the answer is written
    for exc in [RuntimeError("secret text"), ConnectionRefusedError("secret text")]:
        stub.mode = exc; stub.delay = 0.4; n = len(cap.recs)
        c = socket.create_connection(("127.0.0.1", port), timeout=5); c.sendall(post("/channel/actions")); time.sleep(0.1)
        c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b"\x01\x00\x00\x00\x00\x00\x00\x00"); c.close(); time.sleep(1.0)
        ls = levels(n); print(f"FAIL+LEAVE {type(exc).__name__}: ERROR lines {[m for l,m in ls if l=='ERROR']}; DEBUG {[m for l,m in ls if l=='DEBUG']}")
    # handler fine, the caller leaves before the answer is written: expect no ERROR
    stub.mode = None; stub.delay = 0.4; n = len(cap.recs)
    c = socket.create_connection(("127.0.0.1", port), timeout=5); c.sendall(post("/channel/actions")); time.sleep(0.1)
    c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b"\x01\x00\x00\x00\x00\x00\x00\x00"); c.close(); time.sleep(1.0)
    ls = levels(n); print(f"OK+LEAVE: ERROR lines {[m for l,m in ls if l=='ERROR']}; DEBUG {[m for l,m in ls if l=='DEBUG']}")
    stub.delay = 0
    # caller resets while the server waits for the body
    n = len(cap.recs)
    c = socket.create_connection(("127.0.0.1", port), timeout=5); c.sendall(b"POST /channel/actions HTTP/1.1\r\nHost: x\r\nContent-Length: 100\r\n\r\nab"); time.sleep(0.1)
    c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b"\x01\x00\x00\x00\x00\x00\x00\x00"); c.close(); time.sleep(0.6)
    ls = levels(n); print(f"RESET-IN-BODY: ERROR lines {[m for l,m in ls if l=='ERROR']}; DEBUG {[m for l,m in ls if l=='DEBUG']}")
    # sequential: a failed request then a good one (the per-request flag must not carry over)
    stub.mode = RuntimeError("secret text"); raw(port, post("/channel/actions")); time.sleep(0.2); stub.mode = None
    n = len(cap.recs)
    c = socket.create_connection(("127.0.0.1", port), timeout=5); c.sendall(b"POST /channel/actions HTTP/1.1\r\nHost: x\r\nContent-Length: 100\r\n\r\nab"); time.sleep(0.1)
    c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b"\x01\x00\x00\x00\x00\x00\x00\x00"); c.close(); time.sleep(0.6)
    print(f"AFTER-FAILURE reset-in-body: {levels(n)}")
    # hostile request line in the log
    n = len(cap.recs); raw(port, b"POST /x\x1b[31m\r\x00evil HTTP/1.1\r\nHost: x\r\n\r\n"); time.sleep(0.2)
    print("LOGGED-LINES with hostile first line:", [(l, m[:120]) for l, m in cap.recs[n:]])
    # Content-Length forms
    for cl in [b"Content-Length: 99999999999999\r\n", b"Content-Length: -1\r\n", b"Content-Length: \r\n", b"Content-Length: 1\r\nContent-Length: 1\r\n", b"Content-Length: 9" * 1 + b"\r\n", b"Content-Length: 65537\r\n", b"Content-Length: 5555555555555555555555\r\n"]:
        o = raw(port, b"POST /channel/actions HTTP/1.1\r\nHost: x\r\n" + cl + b"\r\nabc"); print(f"CL {cl[:40]!r}: {status(o)}")
finally:
    stop(srv, t)
# slow caller bound (1.5 s)
srv, t, port = start(Stub(), bound=1.5)
try:
    c = socket.create_connection(("127.0.0.1", port), timeout=10); c.sendall(b"POST /channel/actions HTTP/1.1\r\nHost: x\r\nContent-Length: 50\r\n\r\nabc"); t0 = time.perf_counter()
    c.settimeout(8)
    try: d = c.recv(100)
    except OSError as e: d = repr(e)
    print(f"SLOW BODY: closed after {time.perf_counter()-t0:.2f}s, data {d!r} (bound 1.5 s)"); c.close()
finally: stop(srv, t)
print("threads alive at end:", threading.active_count())
