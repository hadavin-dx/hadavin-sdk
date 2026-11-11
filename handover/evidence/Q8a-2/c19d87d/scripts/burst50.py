"""EV c19d87dc: the CHANGELOG measurement: 50 silent connections opened at once (barrier), read bound 2 s, loopback.
Reports how many are still open 0.5 s after the bound and the longest life. Uses _served/FakeChannel/SIG of tests/test_q8a2_callback.py."""
import socket, threading, time, sys
from tests.test_q8a2_callback import _served, FakeChannel, SIG
import hadavin_sdk
N, BOUND = 50, 2.0
lives = []; lock = threading.Lock(); bar = threading.Barrier(N)
def one(port):
    bar.wait(); t0 = time.perf_counter()
    c = socket.create_connection(("127.0.0.1", port), timeout=40); c.settimeout(40)
    try: c.recv(10)
    except OSError: pass
    c.close()
    with lock: lives.append(time.perf_counter() - t0)
with _served(FakeChannel(SIG), read_timeout_s=BOUND) as port:
    ts = [threading.Thread(target=one, args=(port,)) for _ in range(N)]
    [t.start() for t in ts]; [t.join(60) for t in ts]
lives.sort()
print(f"{hadavin_sdk.__file__.split('/')[-4]} n={len(lives)} still open at bound+0.5s: {sum(1 for x in lives if x > BOUND + 0.5)} of {N}; longest life {lives[-1]:.1f}s; median {lives[len(lives)//2]:.2f}s")
