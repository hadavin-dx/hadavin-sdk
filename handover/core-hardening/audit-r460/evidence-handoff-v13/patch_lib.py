"""Tiny patch helper: every replacement must match exactly once, or the whole script stops (nothing half-applied)."""
import sys

DOC = "/home/user/hadavin-sdk/handover/core-hardening/audit-r460/"


class Doc:
    def __init__(self, name):
        self.path = DOC + name
        self.t = open(self.path, encoding="utf-8").read()
        self.n = 0

    def rep(self, old, new, count=1):
        c = self.t.count(old)
        if c != count:
            print(f"PATCH FAIL (found {c}, wanted {count}): {old[:90]!r}")
            sys.exit(1)
        self.t = self.t.replace(old, new)
        self.n += 1

    def line(self, prefix, new):
        """Replace the whole line that starts with prefix (must be unique)."""
        lines = self.t.split("\n")
        hit = [i for i, x in enumerate(lines) if x.startswith(prefix)]
        if len(hit) != 1:
            print(f"LINE FAIL ({len(hit)} hits): {prefix[:80]!r}")
            sys.exit(1)
        lines[hit[0]] = new
        self.t = "\n".join(lines)
        self.n += 1

    def after_line(self, prefix, new):
        lines = self.t.split("\n")
        hit = [i for i, x in enumerate(lines) if x.startswith(prefix)]
        if len(hit) != 1:
            print(f"AFTER FAIL ({len(hit)} hits): {prefix[:80]!r}")
            sys.exit(1)
        lines.insert(hit[0] + 1, new)
        self.t = "\n".join(lines)
        self.n += 1

    def save(self):
        open(self.path, "w", encoding="utf-8").write(self.t)
        print("saved", self.path.split("/")[-1], "edits:", self.n)
