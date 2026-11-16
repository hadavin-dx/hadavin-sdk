"""Copy hostile_run.py into the unpacked tree and point it at this gate's python and free ports. Fails loudly if a
line to replace is not found exactly once. usage: prep_hostile.py SRC_hostile_run.py TREE PYTHON DESK_PORT FAKES_PORT"""
import re, sys
src, tree, py, dp, fp = sys.argv[1:6]
s = open(src).read()
def sub(pat, new):
    global s
    s, n = re.subn(pat, lambda m: new, s, flags=re.M)
    if n != 1: sys.exit(f"prep_hostile FAILED: pattern {pat!r} matched {n} times (need 1)")
sub(r'^PY = .*$', f'PY = {py!r}')
sub(r'^DP, FP = .*$', f'DP, FP = {int(dp)}, {int(fp)}')
open(tree + "/hostile_run.py", "w").write(s)
print("hostile_run.py prepared with python", py, "ports", dp, fp)
