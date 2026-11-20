"""Which step of _build holds the peak: python m_parts.py STEP L  (STEP: trie | regex | compile | prefixes). One value."""
import random
import resource
import string
import sys
import time

step, length = sys.argv[1], int(sys.argv[2])
v = "".join(random.Random(7).choices(string.ascii_letters + string.digits, k=length))
import importlib

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]
base = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
t0 = time.thread_time()
t = R._trie([v])
if step in ("regex", "compile"):
    s = R._trie_regex(t)
    if step == "compile":
        del t
        p = R._compile_uncached("(?=(" + s + "))")
if step == "prefixes":
    pr = R._prefixes(t, v)
cpu = time.thread_time() - t0
print(f"{step} L={length} peak_MB={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 - base:.0f} cpu_s={cpu:.2f}")
