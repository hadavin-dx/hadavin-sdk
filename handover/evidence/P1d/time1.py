import sys, time; sys.path.insert(0, sys.argv[1])
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
E = "user%d" + "@" + "example.org"
for n in (3000, 30000, 120000):
    unit = "Approve **step** for `svc-a` by " + E + ". \x1b[1mbold\x1b[0m &amp; more.\n"
    t = "".join(unit % i for i in range(n // len(unit) + 1))[:n]
    t0 = time.thread_time()
    try: clean(t); r = "ok"
    except runmap.RedactionError as e: r = type(e).__name__
    print(n, f"{time.thread_time()-t0:.2f}s", r)
