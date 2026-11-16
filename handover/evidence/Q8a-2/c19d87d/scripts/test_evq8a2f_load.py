"""EV c19d87dc copy of the 3210f93 script (only change: the closed-check records every outcome and looks again at +6 s).
Step 8: 50 parallel slow connections held open against the receiver (default read timeout), while fast requests are timed.
Uses the `app` fixture, `_callback` and `_waiting` of tests/test_p7_tick.py (real store, fake channel kind). Prints raw numbers. Variant B: the held connections are opened by parallel client threads."""
import http.client, socket, threading, time, statistics
from hadavin_sdk.approvals import receiver
from hadavin_sdk.defaults import RECEIVER_READ_TIMEOUT_S
from tests.test_p7_tick import app, _callback, _waiting, SIG  # noqa: F401
pytest_plugins = ["tests.conftest"]

def post(port, path, headers, body):
    t0 = time.perf_counter(); c = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
    try:
        c.request("POST", path, body=body, headers=headers); st = c.getresponse().status
    except Exception as e:
        st = type(e).__name__
    finally:
        c.close()
    return st, (time.perf_counter() - t0) * 1000

def fast_batch(port, path, req, now, n=20):
    res = []
    for i in range(n):
        h, b = _callback(req, "U1", now) if i % 2 == 0 else _callback(req, "U1", now, secret=SIG[::-1])
        res.append((("signed" if i % 2 == 0 else "bad-sig"),) + post(port, path, h, b))
    return res

def summ(label, res):
    for kind in ("signed", "bad-sig"):
        xs = [ms for k, st, ms in res if k == kind]; sts = sorted({st for k, st, ms in res if k == kind}, key=str)
        xs.sort()
        print(f"    {label} {kind}: n={len(xs)} statuses={sts} min={xs[0]:.1f} median={statistics.median(xs):.1f} p90={xs[int(len(xs)*0.9)-1]:.1f} max={xs[-1]:.1f} ms")

def hold(port, path, pattern, n):
    socks = [None] * n
    def one(i):
        s = socket.create_connection(("127.0.0.1", port), timeout=30)
        if pattern == "short_body":
            s.sendall(f"POST {path} HTTP/1.1\r\nHost: x\r\nContent-Length: 100\r\n\r\n".encode() + b"payload=x")
        elif pattern == "partial_first_line":
            s.sendall(b"POST " + path.encode()[:5])
        socks[i] = s
    ts = [threading.Thread(target=one, args=(i,)) for i in range(n)]
    [x.start() for x in ts]; [x.join() for x in ts]
    return socks

def test_load(app):
    import hadavin_sdk
    print("\nEVLOAD hadavin_sdk:", hadavin_sdk.__file__, "| default read timeout:", RECEIVER_READ_TIMEOUT_S, "s")
    run, req = _waiting(app); now = int(app.approvals.clock().timestamp())
    path = app.approvals.channel.callback_path
    server = receiver.serve(app.approvals, port=0)
    t = threading.Thread(target=server.serve_forever, daemon=True); t.start(); port = server.server_address[1]
    try:
        print(f"EVLOAD path {path!r} port {port}; load average at start: {open('/proc/loadavg').read().split()[:3]}; threads alive: {threading.active_count()}")
        summ("baseline, no slow connections:", fast_batch(port, path, req, now))
        for pattern in ("silent", "short_body", "partial_first_line"):
            t0 = time.perf_counter(); socks = hold(port, path, pattern, 50)
            print(f"  -- {pattern}: 50 connections opened in {(time.perf_counter()-t0)*1000:.0f} ms; threads alive now {threading.active_count()}")
            # time fast requests at several moments after the opening
            for at in (0.2, 3.0, 8.0):
                while time.perf_counter() - t0 < at: time.sleep(0.05)
                summ(f"at +{time.perf_counter()-t0:.1f}s with 50 held:", fast_batch(port, path, req, now, 10))
            while time.perf_counter() - t0 < RECEIVER_READ_TIMEOUT_S + 2.0: time.sleep(0.1)
            closed = 0; kinds = {}
            for s in socks:
                s.settimeout(0.5)
                try:
                    d = s.recv(10)
                    k = "closed(b'')" if d == b"" else "data"
                    if d == b"": closed += 1
                except socket.timeout: k = "still-open(timeout)"
                except OSError as e: k = type(e).__name__
                kinds[k] = kinds.get(k, 0) + 1
            # second look 4 s later at the ones that were not closed
            time.sleep(4.0)
            late = {}
            for s in socks:
                s.settimeout(0.5)
                try:
                    d = s.recv(10); k = "closed(b'')" if d == b"" else "data"
                except socket.timeout: k = "still-open(timeout)"
                except OSError as e: k = type(e).__name__
                late[k] = late.get(k, 0) + 1
            for s in socks: s.close()
            print(f"  after the {RECEIVER_READ_TIMEOUT_S}s bound (+2s): {closed} of 50 connections closed by the server; outcomes {kinds}; again at +6s: {late}; threads alive now {threading.active_count()}")
            summ("  after release:", fast_batch(port, path, req, now, 10))
        # a second round: 200 held connections (beyond the brief's 50) for the same pattern 'silent'
        t0 = time.perf_counter(); socks = hold(port, path, "silent", 200)
        print(f"  -- extra: silent x200 opened in {(time.perf_counter()-t0)*1000:.0f} ms; threads alive {threading.active_count()}")
        summ("  with 200 held:", fast_batch(port, path, req, now, 10))
        for s in socks: s.close()
        time.sleep(0.5)
    finally:
        server.shutdown(); server.server_close(); t.join(5)
    print("EVLOAD done; threads alive:", threading.active_count())
