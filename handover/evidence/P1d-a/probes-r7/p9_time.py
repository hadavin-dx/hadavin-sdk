"""P9: timing shapes the P8 list missed (design N6): `?password=` + `&a` x N, `&amp;` x N, `password=` + `&a=` x N, quoted. 262,144 characters, median of 3.
usage: PYTHONPATH=<tree>/src python p9_time.py"""
import time, statistics
from hadavin_sdk.guard import runmap
N = 262144
SH = {"?password=&a*N": "?password=" + "&a" * N, "&amp;*N": "password=" + "&amp;" * N, "password=&a=*N": "password=" + "&a=" * N,
      "?password=&amp;a=*N": "?password=" + "&amp;a=" * N, "password=\"*N": "password=\"" * N, "password: *N": "password: " * N, "tok.en.*N": "token." * N,
      "a.a.-*N": "a.a.-" * N, "password*N": "password" * N, "pass+spaces": "pass" + " " * N, "keyword at end": "a" * N + "password=x"}
for n, s in SH.items():
    x = s[:N]; ts = []
    for _ in range(3):
        t = time.perf_counter(); runmap.redact_text(x, runmap.RunMap()); ts.append(time.perf_counter() - t)
    print(f"{n:24s} median {statistics.median(ts):6.2f} s  (runs {', '.join(f'{v:.2f}' for v in ts)})")
