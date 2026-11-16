import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
p = ROOT / "CORE-PR-HANDOFF-v16.md"
s = p.read_text(encoding="utf-8")
def R(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: print(f"MISMATCH expected {n} got {c}: {old[:80]!r}"); sys.exit(1)
    s = s.replace(old, new)
def edit_line(prefix, fn):
    global s
    L = s.split("\n"); h = [i for i, l in enumerate(L) if l.startswith(prefix)]
    if len(h) != 1: print(f"LINE MISMATCH {len(h)}: {prefix[:60]!r}"); sys.exit(1)
    L[h[0]] = fn(L[h[0]]); s = "\n".join(L)
def before_line(prefix, text):
    edit_line(prefix, lambda l: text + "\n" + l)
# table continuity: remove the blank line between E0-DB-2 and E0-DB-3
L = s.split("\n"); i = [k for k, l in enumerate(L) if l.startswith("| E0-DB-3 |")][0]
assert L[i-1] == ""; del L[i-1]; s = "\n".join(L)
# hot files (7.1 merge table)
edit_line("| 2 | S-2a | spend |", lambda l: l.rstrip().rstrip("|").rstrip() + ", `llm/anthropic.py` and `llm/gemini.py` (the kinds' `status_of`, `extra` statuses), `config.py` (`SpendSettings` breaker fields, with S-1), `limits.py` (`clock`), `llm/retry.py` (also S-1) |")
edit_line("| 3 | S-2b | spend |", lambda l: l.rstrip().rstrip("|").rstrip() + ", `PostgresSettings` fields `audit_reader_role` and `audit_reader_dsn_secret` (`backends/table.py`, also DB-2 reads them) |")
edit_line("| 4 | DB-1 | spend, held |", lambda l: l.rstrip().rstrip("|").rstrip() + ", `tests/test_lockin_guard.py` (the new SQL-file guard is registered there), `tests/test_secdef_guard.py` (new), `cli.py` (`migrate` messages) |")
edit_line("| 5 | DB-2 | spend, held |", lambda l: l.rstrip().rstrip("|").rstrip() + ", `cli.py` (`limits status` audit-reader line, with S-2b) |")
# G-4(i) real node ids
R("a Postgres test named `store emits UPDATE for negative deltas`", "the Postgres test `tests/test_spend_store_pg.py::test_store_emits_update_for_negative_deltas`")
R("`store emits UPDATE for negative deltas`", "`tests/test_spend_store_pg.py::test_store_emits_update_for_negative_deltas`")
# section 8
R("## 8. Evidence saved this pass (`evidence-handoff-v15/`; v14 files that were not re-run stay in `evidence-handoff-v14/` and are named as carried)",
  "## 8. Evidence saved this pass (`evidence-handoff-v16/`; v15 and v14 files that were not re-run stay in `evidence-handoff-v15/` and `evidence-handoff-v14/` and are named as carried)\n\n**New in v16.** `pg_v16.py` and `pg_run_v16.sh` (174 of 174 checks in each of two runs on 16.15 with password logins; `raw-pg-v16-run1.txt`, `raw-pg-v16-run2.txt`, `raw-pg-version-v16.txt`), `secdef_guard_v16.py`, the four held files (`held-sql/`; `sha256-v16.txt` has the hashes; the first two are byte-copies of v15's), `gate4_v16.sh` and `raw-gate4-base-*.txt` (the baseline on the unchanged tree: two failing repository guard tests, L20), and `INVENTORY.md`. **Not re-run in v16:** the citation programs, the planned-name list and the import-graph run of v15 and v14 (their results are carried; the v16 text changes only the names in 8.1 and adds no import edge except `llm/spend.py` `Gate`, which imports only `models` and `errors`); a builder re-runs them at the S-1 head (E0-S1-5).")
# section 10 questions
before_line("- **O1** (owner, needs a yes, default NO)",
"""- **L18** (needs-lead, new in v16) **The lowest Postgres version the studio supports.** Nothing I read states it. The held default works on any version; the upgrade file (5.6 k) needs 14 or later. Only 16.15 exists on this machine, so 14 and 17.10 are NOT run. Ask: name the lowest version, and let an independent runner repeat `bash pg_run_v16.sh` on 14 and on 17.
- **L19** (needs-lead, new in v16) **`REVOKE TEMPORARY ON DATABASE <db> FROM PUBLIC` is an operator step before the audit reader exists** (5.6 g2, G-4(v)). It changes what every other role may do; I tested the effect on a throwaway cluster only (P1 to P7, M7). Ask: who runs it, and on which databases.
- **L20** (needs-lead, new in v16) **The unchanged tree already fails two repository guard tests**, outside this folder: `tests/test_no_reference_material.py` (two files under `handover/core-hardening/lead-repin/evidence-repin4-independent/` are not UTF-8 text) and `tests/test_repo_rules.py::test_licences_are_proprietary` (10 licence files under `handover/promotion-inputs/`). I did not touch them (rule: no edits outside this folder). Ask: who fixes them, because every PR gate (CLAUDE.md) needs a green `pytest`.
- **Unverified items and how each is settled (v16).** Postgres 14 and 17.10: L18 and an independent run. The product tests and code: not written. Vendor facts of 5.9: invoice comparison (7.3). The breaker numbers (3, 60 s, 900 s) and the 30-day credential life are my choices, settled by a review answer. The reason codes of every detector for the `qualify` allowlist (`v.reason_code in {None, "injection_suspected"}` replaces the blacklist `!= "guard_unavailable"` at `guard/judge.py:108`): the S-2a builder reads all detectors first; I read only `guard/injection.py`.""")
edit_line("- **L9** (**OWNER-OPEN**", lambda l: l + " **Measured in v16 (16.15, two runs):** the decrease trigger costs +0.062 ms and +0.047 ms per lowering; one record is about 110.6 bytes (2,211,840 bytes for 20,000 rows). Unchanged: still an owner yes, not assumed.")
edit_line("- **L16** (**OWNER-OPEN**", lambda l: l + " **v16:** both records are append-only (an accidental delete is refused even for the owner, H1 to H5); the owner can still disable the trigger and a superuser bypasses it (H4). The deliberate delete path, if any, is still the owner's decision; nothing is assumed.")
edit_line("- **L13** (needs-lead)", lambda l: l + " **Added in v16:** also who runs `limits status --check` on a schedule and who is told when it exits non-zero (5.6 g2); nobody is named.")
p.write_text(s, encoding="utf-8"); print("part C ok")
