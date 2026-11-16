"""Patch helper for the v15 hand-off (replays every edit from the v14 text). Exact-match replace, fails loudly."""
import sys
F = "CORE-PR-HANDOFF-v15.md"
def load(f=F): return open(f, encoding="utf-8").read()
def save(t, f=F): open(f, "w", encoding="utf-8").write(t)
def rep(t, old, new, n=1):
    c = t.count(old)
    if c != n: sys.exit(f"PATCH FAIL: expected {n} got {c} for: {old[:90]!r}")
    return t.replace(old, new)
def repline(t, prefix, new):
    ls = t.split("\n"); idx = [i for i, l in enumerate(ls) if l.startswith(prefix)]
    if len(idx) != 1: sys.exit(f"PATCH FAIL: {len(idx)} lines start with {prefix[:60]!r}")
    ls[idx[0]] = new; return "\n".join(ls)
def delline(t, prefix):
    ls = t.split("\n"); idx = [i for i, l in enumerate(ls) if l.startswith(prefix)]
    if len(idx) != 1: sys.exit(f"PATCH FAIL: {len(idx)} lines start with {prefix[:60]!r}")
    del ls[idx[0]]; return "\n".join(ls)
