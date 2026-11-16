"""List every mutant whose planted `old` text overlaps a line range that ticket rev 3 plans to edit (rev 3, R2 readiness M7).
Reads the mutant lists of a source snapshot; changes nothing. Usage: python -I affected_mutants.py <snapshot root>
Line ranges are 4d328e3d line numbers taken from ticket rev 3 sections 3.1, 5.2, 5.3, 6.1-6.2, 9.3 (commit number in brackets)."""
import importlib.util, sys, re
from pathlib import Path
ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "src"), str(ROOT)] + sys.argv[2:3]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / f"{name}.py"); m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m
MIG, MN, CL, CLI = "src/hadavin_sdk/store/migrate.py", "src/hadavin_sdk/store/migration_numbers.py", "CHANGELOG.md", "src/hadavin_sdk/cli.py"
PLAN = {  # file -> list of (first, last, commit, why)
    MIG: [(1, 78, 6, "module docstring"), (260, 264, 3, "_apply_grants gets schema"), (283, 372, 3, "deleted: _TABLE_PRIVS.. effective_problems"),
          (476, 476, 3, "_READBACK_TRIGGERS_SQL current_schema -> parameter"), (671, 671, 3, "_FOREIGN_OWNED_SQL current_schema"),
          (680, 680, 3, "_FOREIGN_OWNED_SQL current_schema"), (694, 694, 3, "_SCHEMA_USAGE_SQL deleted"), (770, 770, 3, "_refuse_foreign_owned current_schema"),
          (821, 824, 3, "REVIEWED_DEFINER_FUNCTIONS key"), (826, 1018, 3, "deleted comparison + constants moved"), (1024, 1254, 3, "deleted comparison, _refuse_unlisted_grantees"),
          (1257, 1325, 4, "lock message, prepared join, unreadable view"), (1364, 1366, 1, "_label moves to migration_numbers"),
          (1512, 1677, 3, "migrate() new order (docstring 1524-1554 in commit 6)")],
    MN: [(677, 679, 6, "comment above _GRANT_TARGET"), (722, 723, 6, "refused_statements docstring")],
    CL: [(6, 34, 6, "Migrations bullet rewritten")],
    CLI: [(1, 20, 3, "module docstring exit-code line"), (320, 360, 3, "_migrate catches AppliedNotVerifiedError")],
}
def span(m):
    text = (ROOT / m.file).read_text(encoding="utf-8"); n = text.count(m.old)
    if n != 1: return None, None, n
    i = text.index(m.old); a = text.count("\n", 0, i) + 1; return a, a + m.old.count("\n") - (1 if m.old.endswith("\n") else 0), n
rows = []
for modname, lst in (("migrate_mutants", "M"), ("migration_numbers_mutants", None)):
    mod = load(modname)
    muts = getattr(mod, lst) if lst else next(v for k, v in vars(mod).items() if isinstance(v, list) and v and hasattr(v[0], "old") and k.isupper())
    for m in muts:
        a, b, n = span(m)
        hits = [(c, w) for (f0, f1, c, w) in PLAN.get(m.file, []) if a is not None and not (b < f0 or a > f1)]
        rows.append((modname, m.name, m.file, a, b, n, hits))
print(f"mutants read: {len(rows)} ({sum(1 for r in rows if r[0]=='migrate_mutants')} migrate, {sum(1 for r in rows if r[0]!='migrate_mutants')} migration_numbers)")
bad = [r for r in rows if r[5] != 1]
print(f"old text not exactly once at the snapshot: {len(bad)} {[r[1] for r in bad]}")
aff = [r for r in rows if r[6]]
print(f"affected by a planned edit: {len(aff)}")
for r in sorted(aff, key=lambda r: (r[6][0][0], r[2], r[3])):
    print(f"  commit {r[6][0][0]}  {r[1]:<6} {r[2]}:{r[3]}-{r[4]}  ({r[6][0][1]})")
cl = [r for r in rows if r[2] == CL and not r[6]]
print(f"planted in CHANGELOG outside the rewritten lines (re-checked at commit 6 by rule R3-M7b): {[r[1] for r in cl]}")
