"""M2 measure: one growing RunMap, CALLS redact_untrusted calls, each adding one value of 30-60 KB (tracemalloc OFF).
usage: python m_seq.py SHAPE CALLS   SHAPE: plain (password=<random alnum>) | b64 (a base64 run of random bytes, G4 ENCODED)
After every call: map chars, call CPU, peak RSS so far over the baseline, and an enforce_map of a short text over the map (the gate's
build, once per model call). Stops at the first refusal and says which."""
import base64
import random
import resource
import string
import sys
import time

shape, calls = sys.argv[1], int(sys.argv[2])
rng = random.Random(11)
alpha = string.ascii_letters + string.digits
import importlib

importlib.import_module("hadavin_sdk.guard.redact")
from hadavin_sdk.guard import runmap

runmap.redact_untrusted("warm password=abcdefgh1234", runmap.RunMap())
base = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
m = runmap.RunMap()
for i in range(calls):
    size = rng.randint(30_000, 60_000)
    if shape == "plain":
        text = f"line {i} password={''.join(rng.choices(alpha, k=size))} end"
    else:
        raw = rng.randbytes(size * 3 // 4)
        text = f"blob {i}: {base64.b64encode(raw).decode()} end"
    t = time.thread_time()
    try:
        runmap.redact_untrusted(text, m)
    except runmap.RedactionError as exc:
        print(f"call {i + 1}: REFUSED {type(exc).__name__}({exc}) after {time.thread_time() - t:.2f} s", flush=True)
        break
    c = time.thread_time() - t
    t = time.thread_time()
    try:
        runmap.enforce_map(f"reply {i} mentions nothing", m)
        g = f"{time.thread_time() - t:.2f}"
    except runmap.RedactionError as exc:
        g = f"REFUSED {type(exc).__name__}({exc}) {time.thread_time() - t:.2f}"
    chars = sum(map(len, m.values()))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 - base
    print(f"call {i + 1}: entries={len(m)} map_chars={chars} call_cpu_s={c:.2f} enforce_s={g} peak_MB={peak:.0f}", flush=True)
