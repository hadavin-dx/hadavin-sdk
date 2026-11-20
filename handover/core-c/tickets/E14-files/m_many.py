"""E14 measure: real peak RSS (ru_maxrss, tracemalloc OFF) and thread CPU of building N plain values of length L.
usage: python m_many.py MODE N L
MODE: many   -> redact_many([f"password={v_i}"]) (no deadline)
      build  -> _Redactor({"<SECRET_i>": v_i})._build() only (finder memory alone)
      runmap -> one RunMap, redact_untrusted(f"password={v_i}") per value (the bundle / run path, with the 6 s deadline)
Prints one line: mode N L chars peak_MB_over_base retained_MB cpu_s result."""
import random
import resource
import string
import sys
import time


def rss_now_mb() -> float:
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * 4096 / 2**20


def main() -> None:
    mode, n, length = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    rng = random.Random(7)
    alpha = string.ascii_letters + string.digits
    vals = ["".join(rng.choices(alpha, k=length)) for _ in range(n)]
    import importlib

    importlib.import_module("hadavin_sdk.guard.redact")
    R = sys.modules["hadavin_sdk.guard.redact"]
    from hadavin_sdk.guard import runmap

    R.redact_many(["warm password=abcdefgh1234"])  # imports and compiles done before the baseline
    base = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    base_now = rss_now_mb()
    t0 = time.thread_time()
    result = "ok"
    m = {}
    try:
        if mode == "many":
            out, m = R.redact_many([f"password={v}" for v in vals])
            result = f"ok entries={len(m)} maxlen={max(map(len, m.values()))}"
        elif mode == "build":
            r = R._Redactor({f"<SECRET_{i + 1}>": v for i, v in enumerate(vals)})
            r._build()
            result = f"ok finders={len(r._finders)} slow={len(r._slow)}"
        elif mode == "runmap":
            m = runmap.RunMap()
            per = []
            for v in vals:
                t = time.thread_time()
                runmap.redact_untrusted(f"password={v}", m)
                per.append(time.thread_time() - t)
            result = f"ok entries={len(m)} max_call_s={max(per):.2f} last_call_s={per[-1]:.2f}"
    except runmap.RedactionError as exc:
        result = f"refused {type(exc).__name__}({exc}) entries={len(m)}"
    cpu = time.thread_time() - t0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 - base
    print(
        f"{mode} N={n} L={length} chars={n * length} peak_MB={peak:.0f} retained_MB={rss_now_mb() - base_now:.0f} "
        f"cpu_s={cpu:.2f} {result}",
        flush=True,
    )


main()
