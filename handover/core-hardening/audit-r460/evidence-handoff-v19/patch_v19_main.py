"""Builds CORE-PR-HANDOFF-v19.md from CORE-PR-HANDOFF-v18.md (improve, do not replace). Every replacement asserts that its old text occurs exactly
once, so a v18 text that moved makes the script stop instead of silently doing nothing. Also writes the three history blocks it removes
(0a, 0b, 0 of v18) to history-blocks-from-v18.md in the scratch folder given as argv[1]; v19-CHANGES.md carries them.
usage: python -I patch_v19_main.py <audit-r460 folder> <scratch folder>"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
scratch = Path(sys.argv[2])
t = (root / "CORE-PR-HANDOFF-v18.md").read_text(encoding="utf-8")


def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f"expected {count} of, found {n}: {old[:90]!r}"
    t = t.replace(old, new)


def cut(start, end, new):
    """replace the text from `start` up to (not including) `end` by `new`; both must be unique"""
    global t
    assert t.count(start) == 1, f"start not unique: {start[:80]!r} ({t.count(start)})"
    i = t.index(start)
    j = t.index(end, i)
    old = t[i:j]
    t = t[:i] + new + t[j:]
    return old


# ---------------------------------------------------------------- header
rep("# Core hardening hand-off v18: spend track only", "# Core hardening hand-off v19: spend track only")
old3 = cut("Replaces v17 for everything about spend.", "\n\n**Core is paused", (
    "Replaces v18 for everything about spend. v18, v17, v16, v15, v14, v13, v12, v11, v10 and v4 to v9 stay as they are. Everything that is not spend is in "
    "`CORE-PR-HANDOFF-v19-other-tracks.md`. What changed from v18, finding by finding, with the test that fails on the old design: `v19-CHANGES.md` and "
    "`resolve-handoff-v19.md`. Raw output of every check I ran: `evidence-handoff-v19/` (older folders such as `evidence-handoff-v16/` stay and are named "
    "where a file is carried). **This text is one layer: v14 added its corrections as a section that overrode others; v15 to v18 moved each correction into "
    "the place it belongs; v19 does the same for the findings of the two v18 reviews and of the independent evidence run of v18, and moves the three "
    "history blocks that v18 kept at the top (0a, 0b, 0) into `v19-CHANGES.md` (readiness minor 1 of the v18 review). A sentence that contradicts another "
    "one is a defect: report it.**"))
rep("Round: 9 of the spend track after v13 (money path, no round cap)", "Round: 5 of the current review loop of the spend track (money, secret and audit path, no round cap)")

# ---------------------------------------------------------------- section 0 (replaced; history goes to v19-CHANGES.md)
i0 = t.index("## 0. What failed")
i1 = t.index("## 1. Words used")
sec0 = t[i0:i1]
# carry three standing items unchanged: item 1 (migration 0006), item 4 (vendor facts), item 5 (what this design does not protect against)
lines0 = sec0.split("\n")
item = {}
for ln in lines0:
    m = re.match(r"^(\d)\. \*\*", ln)
    if m:
        item[int(m.group(1))] = ln
hist = [ln for ln in lines0 if ln.startswith(("0a. ", "0b. ", "0. "))]
assert len(hist) == 3 and all(k in item for k in (1, 4, 5)), (len(hist), sorted(item))
(scratch / "history-blocks-from-v18.md").write_text("\n\n".join(hist) + "\n", encoding="utf-8")
words = [ln for ln in lines0 if ln.startswith("Words such as reservation")][0]
new0 = f"""## 0. What failed, what is uncertain, what was not run (read first)

{words}

0. **What v19 changes, what failed, what is uncertain (read first; failures and gaps first).** v18 failed two independent reviews (security: 0 blockers, 3 majors MA1 to MA3, 9 minors m1 to m9; readiness: 0 blockers, 4 majors Ma1 to Ma4, 8 minors) and the independent evidence run of v18 found one more hole the review had not named: a plain `CREATE VIEW` passed the v18 guard (1 of 30 spellings). Every finding, its fix, its place and its test: `v19-CHANGES.md` and `resolve-handoff-v19.md`; every question that is yours: `v19-OPEN-FOR-LEAD.md`.
   - **(1) The v18 guard was not deny by default although the text said so (MA1).** A statement that matched none of its deny branches passed. I proved the security review's bypasses myself on a real 16.15 server, not only by reading: `SET "role"`, `SET session_authorization`, `SELECT set_config('role', ...)` change who the session is, a body calling `query_to_xml` runs a caller-chosen query as the function owner, and a `REVOKE`, `DROP FUNCTION`, `CREATE OR REPLACE FUNCTION` sequence leaves PUBLIC with `EXECUTE` (3 stated exploits and 20 identity or privilege checks in `pg_v19.py`, `raw/raw-pg-v19-run1.txt`). The v19 guard is a real allow-list (5.6 item 1(j)): 152 checks, 0 failed; of the 51 mutants new in v19 the v18 guard misses 49 and flags 2 (N35 and N49, flagged by v18 for a weaker reason: they differ in problem count, 3 against 1 and 2 against 1); the independent runner's 30 spellings are flagged 30 of 30 (the v18 guard misses the `CREATE VIEW`).
   - **(2) Schema and case aliasing (MA2)** fixed in the same guard (N1) and in the start-up query (it now reads `proname`, not text parsed from `regprocedure`).
   - **(3) The secret-check claims were overstated (MA3).** M3g, M3i and M3l pass because the agent's operating-system user READS the secret; nothing detects it today. Item 1(g2) now says so: the real protection is the operator keeping the agent on another OS user or container and setting the modes by hand; the planned detectors (a mode check on the file kind and an operator-side probe for the others) are text, and v18's plan that the agent asks for the secret once and discards it is withdrawn.
   - **(4) Behaviour the runner observed, fixed in the held files (new hashes):** day `infinity`, `-infinity`, 1999-01-01 and 0001-01-01 were accepted (now a day window 2020-01-01 to 2099-12-31, `23514`); an amount of 0 created a 0 / 0 row (a reserve of 0 now writes nothing); agent names that differ by NFC or NFD form, leading or trailing blanks, a newline or tab were separate budgets (now refused); the DB-2 record missed the INSERT of a missing switch row (m1); a settle for a day that had no row lowered the month row (m2); `statement_timeout` was missing for the scan of the new checks (m7).
   - **(5) Stated, not closed, with the reason (nothing here is a "known limitation" I chose to leave if I could fix it; each needs a design decision, the owner, or a person who runs something):** (a) the single runtime login can still settle a reservation under ANY agent name (cross-agent settle) and can reserve any amount below the 1,000,000,000,000 ceiling under any name and settle it back, so it can under-report; one login per agent (L-4) and the invoice comparison (7.3) are the controls; (b) agent ids that differ only in letter case or by an inner blank are separate budgets, and a hostile login can choose any name; (c) a settle with `actual` above `worst` (even `worst` 0, `actual` 5) raises a total: it can only over-report spend, and refusing it would lose a true cost; (d) row spam inside the day window: unlimited rows by name and day; (e) a DELETE of the switch row is not recorded: a missing row reads as ON, the safe direction; (f) the 60 s `statement_timeout` of the DB-3 file overrides a stricter value of the caller for that transaction; (g) the start-up query does not pin the function bodies (a hash of `prosrc` or `prosqlbody` would pin Postgres's own text, whose stability across 14, 16 and 17 I could not test: UNVERIFIED), and does not check that the runtime role is a member of any role other than the operator role beyond the rules in `secdef_audit_v19.py`; (h) the store must treat an empty result of `spend_reserve` or `spend_settle` as an error (T, L-2).
   - **(6) Still NOT run:** any unit test of the product change (none is written), `bandit` of the change, CodeQL, Postgres 14 and 17.10 (only 16.15 exists here, L18), a Windows checkout, `gate4_v19.sh` (only its comparator `compare_gate4.py` ran, on four cases, `raw/raw-gate4-compare-v19.txt`), and the EGM skills (I cannot invoke them from the place I run; the lead runs the EGM steps).
   - **(7) Every v19 check was run by the author (me).** No independent evidence runner has re-run v19; v18's independent run found the `CREATE VIEW` hole, so expect another hole until one has. The guard, the start-up query and the grants prototype are reference code in `evidence-handoff-v19/`, not product code.
   - **(8) What is text only (T, product code not written):** the `function` kind of `GRANTS` and `PostgresStore.startup_checks` (the prototype `secdef_audit_v19.py` is tested, the product code is not), the store code L-2, the file-kind mode check `mode & 0o077` (prototype in `agent_probe_v19.py`; the product file kind `secrets_file.py` accepts mode 0440 by design), the pre-flight query of 5.6 item 1(e2) (SQL written, not run).
   - **(9) Measured here, one machine, Postgres 16.15 only (all through `scram-sha-256` logins on a unix socket, made-up data, one scratch cluster at a time, removed afterwards):** `pg_v19.py` 120 safety checks, 24 controls (each fails on the old file) and 3 stated exploits, run twice with the same output apart from the timing line; the 175 v16 checks against the v19 files, run twice, 175 of 175 (one `ALLOWED` set edited for the new function, line 522 of the copy); `secdef_mutants_v19.py` 152 checks; `spell30_guard_v19.py` 30 of 30; `run_secrets_v19.sh` 12 of 12 plus a one-line pre-check when the OS user `nobody` cannot enter the folder (exit 3, `raw/raw-secrets-precheck-v19.txt`; the run before that pre-check wasted the runner's time). The cost of the DB-2 decrease trigger (not DB-1) was measured in v18: +0.05 to +0.08 ms per lowering of a total; not re-measured in v19 (the trigger text did not change).
{item[1]}
2. **What was run in v19, and what was not:** see item 0 (6) to (9) above and section 8; the older run lists (v16 item 2, v18 item 6) are history in `v19-CHANGES.md`.
3. **Postgres behaviour: what is run and what is not (all 16.15).** Run: the held files apply through the real `store/migrate.py` as a non-superuser migration role; the runtime role is refused (`42501`) any direct write to the three tables once DB-3 is in; the functions behave as in 5.6 item 1(o); the lock, timeout and trigger behaviour of 5.6 items (i), (m), (n). Not run: Postgres 14 and 17.10, parallel load beyond the 400-call fuzz, a Windows checkout, the product tests. Details and raw files: section 8.
{item[4]}
{item[5]}
6. **Why v12 to v18 failed:** history, moved to `v19-CHANGES.md` and the older `v1x-CHANGES.md` files (v19 removes it from this text so that no stale sentence can contradict a live one).
7. **Code I read this pass** (opened by me unless marked "carried"): the five held files and the five product migrations of `store/migrations/` (guard input), `store/migrate.py` (grants), `app.py` lines 155 to 170 (the two `make(` calls: line 162 `make("llm"`, line 165 `make("detector"`; v18 gave three different ranges for them, readiness minor 3), `tests/test_no_reference_material.py` (the `BANNED` list, read at run time, never copied). **Carried, not re-opened in v19:** every other cite in this text is carried from v16 to v18 (the S-1 builder re-reads them, E0-S1-5).

"""
t = t[:i0] + new0 + t[i1:]

# ---------------------------------------------------------------- global renames of the current evidence files
for a, b in (
    ("CORE-PR-HANDOFF-v18-other-tracks.md", "CORE-PR-HANDOFF-v19-other-tracks.md"),
    ("v18-CHANGES.md", "v19-CHANGES.md"), ("resolve-handoff-v18.md", "resolve-handoff-v19.md"), ("v18-OPEN-FOR-LEAD.md", "v19-OPEN-FOR-LEAD.md"),
    ("evidence-handoff-v18/", "evidence-handoff-v19/"),
    ("secdef_guard_v18.py", "secdef_guard_v19.py"), ("allow_v18.py", "allow_v19.py"), ("secdef_mutants_v18.py", "secdef_mutants_v19.py"),
    ("secdef_audit_v18.py", "secdef_audit_v19.py"), ("run_pg_v18.sh", "run_pg_v19.sh"), ("run_secrets_v18.sh", "run_secrets_v19.sh"),
    ("agent_probe_v18.py", "agent_probe_v19.py"), ("pg_v18.py", "pg_v19.py"), ("gate4_v18.sh", "gate4_v19.sh"), ("patch_v18_main.py", "patch_v19_main.py"),
    ("raw-pg-v18-run", "raw-pg-v19-run"), ("raw-secdef-mutants-v18.txt", "raw-secdef-mutants-v19.txt"), ("raw-secrets-v18.txt", "raw-secrets-v19.txt"),
    ("raw-pg-v16-regress-on-v18-run", "raw-pg-v16-regress-on-v19-run"), ("sha256-v18.txt", "sha256-v19.txt"), ("raw-banned-count-v18.txt", "raw-banned-count-v19.txt"),
    ("evidence-handoff-v16/held-sql/", "evidence-handoff-v19/held-sql/"),
    ("sha256-v16.txt", "sha256-v19.txt"),
):
    t = t.replace(a, b)
# the section 8 of v16 (kept as it was) names its own sha256-v16.txt and held-sql: restore those two inside the "8-v16" block only
i8 = t.index("## 8-v16.")
j8 = t.index("## 8.1 ", i8) if "## 8.1 " in t[i8:] else t.index("### 8.1 ", i8)
blk = t[i8:j8].replace("evidence-handoff-v19/held-sql/", "evidence-handoff-v16/held-sql/").replace("sha256-v19.txt", "sha256-v16.txt")
t = t[:i8] + blk + t[j8:]

# ---------------------------------------------------------------- minors: app.py ranges, punctuation, G-5, stale labels
rep("(was `app.py:162-166`)", "(was `app.py:162`)")
rep("(was `app.py:162-165`)", "(was `app.py:165`)")
rep("`app.py:162-167,165`", "`app.py:162` and `app.py:165`")
rep("(readiness minor 3: v12 said \"not a `FakeLLM`\", which contradicted the last sentence of this paragraph; the last sentence wins)",
    "(readiness minor 3: v12 said \"not a `FakeLLM`\", which contradicted the last sentence of this paragraph; v19 removed the contradiction: the paragraph now says what its last sentence says.)")
rep("start gate (vi) below", "start gate G-5 below")
old_g4 = cut("**G-4** (DB-1 and DB-2, at the **move**", "**NC-1** (each of the nine", (
    "**G-4** (DB-1 and DB-2, at the **move**, not at the merge): (i) S-2a is merged and running, so the UPDATE shape of 5.4 item 4 is in place (v13 review finding B1 of v12), "
    "**shown by the Postgres test `tests/test_spend_store_pg.py::test_store_emits_update_for_negative_deltas` green in the move PR (5.6 item 1(c))**; (ii) the owner's yes to apply "
    "the file, with its sha256 in the PR description; (iii) **NOT a gate by default**: v13 made the owner's answer on D5 a condition, but your answer Q28 says D5 is non-blocking; "
    "the held tables keep dollars as today and D5 gates only a NEW spend table; **you decide in L11, and until you answer, (iii) is not applied**; for DB-2 also (iv) the lead's yes, L9, "
    "and (v) the operator step `REVOKE TEMPORARY ON DATABASE ... FROM PUBLIC` done and the start-up check green (5.6 item 1(h), 5.5b item 3). "
    "**G-5** (DB-3, at the **move**; readiness minor 7 of the v18 review: v18 appended this as item (vi) of G-4; G-4 (i) and (ii) apply to DB-3 as well, (iii) to (v) do not): "
    "(a) the owner's yes naming the sha256 of the file (L22); (b) L23 answered (the operator role is named); (c) the change of `GRANTS` and the function-grant step of 5.6 item 1(o) "
    "in the same PR, with the migrate-four-times test green (G1, G4 and G9 repeated, plus DELETE and TRUNCATE); (d) the start-up query of 5.6 item 1(o2) running; "
    "(e) the S-2a and L-2 store code running, because the functions replace the statements of 5.4 item 4 and the store must treat an empty result as an error. "))
rep("(start gate G-4(v), question L19)", "(start gate G-4(v), question L19)") if False else None
t = t.replace("G-4(vi)", "G-5")

# DB-1 item (a): unclosed bold and path; (k) stale hash name already renamed above
n_open = t.split("\n")[302].count("**")
if n_open % 2:
    lines = t.split("\n")
    lines[302] = lines[302] + "**"
    t = "\n".join(lines)

# ---------------------------------------------------------------- 5.6 (b) DB-2
rep("`evidence-handoff-v19/held-sql/spend_decrease_log.sql` (sha256 `e3111401ec65caed136d8c7ff56b4e7374677a3126f7bb42549bb41f759c2ce9`; v17 was",
    "`evidence-handoff-v19/held-sql/spend_decrease_log.sql` (sha256 `c0c4913eede84ead97a33b1e1d2c3f055987f7e12854936ba27ef0b3585cdaf2`; **v19 adds** the function `kill_switch_log_insert()` and an `AFTER INSERT` trigger on `kill_switch` (security minor m1 of the v18 review: a switch row that was missing and was made by `kill_switch_engage()` or by hand left no record; the state before is written as ON and no earlier author, a missing row reads as stopped; same failure rule as the UPDATE record: a failing write never stops a switch ON, a switch OFF without a record is refused; a DELETE of the switch row stays unrecorded, stated in 0 (5)); v18 was `e3111401ec65caed136d8c7ff56b4e7374677a3126f7bb42549bb41f759c2ce9`; v17 was")
rep("DB-2 adds one table, one index, two functions and four triggers, **no grant to the runtime role**",
    "DB-2 adds two tables (`spend_decrease_log`, `kill_switch_log`), two indexes, five functions (three `SECURITY DEFINER`: `spend_log_decrease`, `kill_switch_log_change`, `kill_switch_log_insert`; two invoker: `spend_keep_keys`, `audit_log_append_only`) and ten triggers (v19 count; v18 said two functions and four triggers, which was stale since v16), **no grant to the runtime role**")
rep("fired `AFTER UPDATE ON kill_switch ... WHEN (NEW.\"on\" IS DISTINCT FROM OLD.\"on\")`; the row is seeded by migration `0003` and `set_kill_switch` is `INSERT ... ON CONFLICT DO UPDATE`, so the trigger fires.",
    "fired `AFTER UPDATE ON kill_switch ... WHEN (NEW.\"on\" IS DISTINCT FROM OLD.\"on\")`; the row is seeded by migration `0003` and `set_kill_switch` is `INSERT ... ON CONFLICT DO UPDATE`, so the trigger fires. **v19 (security minor m1): a second trigger function `kill_switch_log_insert()` fires `AFTER INSERT ON kill_switch` and writes the record `old_on = true` (a missing row reads as stopped), `new_on`, `old_by` NULL; run (`pg_v19.py` G9 m1 and K m1): the INSERT of a missing row is recorded, with the record unwritable an INSERT of a switch that is ON works and an INSERT that is OFF is refused and leaves no row; the v18 file writes no record (control).**")

# ---------------------------------------------------------------- 5.6 (e2) pre-flight for DB-3 (security minor m7), after item (e)
ie = t.index("   **(e) Repair path for the pre-flight")
je = t.index("\n", ie)
t = t[:je] + (
    "\n   **(e2) Pre-flight for DB-3 (security minor m7 of the v18 review: item (e) covers DB-1 only; UNVERIFIED text, not run).** DB-3's `usd` and `open_usd` checks are added without `NOT VALID`, so the file scans each table under an exclusive lock and one bad row aborts the whole file. Before the move the operator, as the migration role, reads: `SELECT agent_id, day, usd FROM spend WHERE usd < 0 OR usd >= 1000000000000 OR NOT (day >= DATE '2020-01-01' AND day < DATE '2100-01-01')` and the same on `spend_month` with `month`; a row it returns is repaired or reported by a person before the file is applied (the file itself never repairs a row). Two limits bound the file: `lock_timeout = 5s` bounds the wait for the lock; v19 adds `SET LOCAL statement_timeout = '60s'` (my number; the owner may change it) so that the scan cannot hold the lock for ever; the file then fails and rolls back." + t[je:])

# ---------------------------------------------------------------- 5.6 (g2): secret claims (MA3)
rep("one shared user makes the secret readable by the agent and is refused by the start-up check below.",
    "one shared user makes the secret readable by the agent, and **nothing detects that today** (security major MA3 of the v18 review: v18 said a start-up check refuses it; that check is not written and the file kind accepts mode 0440 by design).")
rep("**mutant M3g: the same file made group-readable by the agent's group is READ by the agent, and the check reports it** (this is the bad configuration the review described).",
    "**mutant M3g: the same file made group-readable by the agent's group is READ by the agent** (this is the bad configuration the review described; **M3g, M3i and M3l PASS because the agent READS the secret, they show the leak works and nothing reports it**: v18 wrote \"the check reports it\", which overstated).")
cut("(3) **Start-up probe (S-2b, `PostgresStore.startup_checks`):**", "**So log detection by the agent runs only on its own connection**", (
    "(3) **Detection, stated as it is (security major MA3 of the v18 review): no detector exists today.** The planned detectors are (a) for the `mounted_file` kind a `stat` check that refuses a secret file or its folder when any group or other bit is set (`mode & 0o077`; the prototype is in `agent_probe_v19.py` and tested in `run_secrets_v19.sh` M3j and M3k; the product file kind `actions/secrets_file.py` refuses only a file readable by every user (the `S_IROTH` check) and accepts 0440 by design, so the product change is T), and (b) for the other kinds a probe made from the OPERATOR side (the operator asks the secrets manager or the shell whether the agent's identity can read that name). **v18's plan, in which the agent process asks its own secrets kind for the audit-reader name once and throws the value away, is withdrawn:** where the secret is readable the fetch puts it into the agent's memory and, in a cloud secrets manager, writes an access log entry; the spy test then allows no request for that name at all. **The real protection is the operator's:** the agent runs as another OS user or in another container, and the modes are set by hand as in (1). "))
rep("`raw/raw-secrets-v19.txt` M3a to M3l (v18 adds the folder-mode test M3h",
    "`raw/raw-secrets-v19.txt` M3a to M3l (12 of 12; v19 adds a pre-check line (exit 3) when `nobody` cannot enter the folder, `raw/raw-secrets-precheck-v19.txt`; v18 added the folder-mode test M3h")

# ---------------------------------------------------------------- 5.6 (j): the guard, rewritten as the allow-list it is now
oldj = cut("   **(j) A guard test over every SQL file", "\n   **(k) The default-to-variant upgrade", (
    "   **(j) A guard test over every SQL file (security major 6 of v15; M2 of v16; MA1 of v17; MA1 and MA2 of v18: the v18 guard said \"deny by default\" and was not, because a statement that matched none of its deny branches passed, and only `CREATE FUNCTION` was checked for what it is).** *Class:* a check that lists the bad shapes passes every shape not on the list. *Fix at the one choke point (`evidence-handoff-v19/secdef_guard_v19.py`, `allow_v19.py`; port to `tests/test_secdef_guard.py`, and to nowhere else):* **a real allow-list: every statement of a `.sql` file must match one of the shapes below, otherwise it is a problem, so a new SQL keyword is refused until someone adds a shape and a mutant.** One tokenizer reads nested comments, single-quoted strings (also `E'...'`), double-quoted names (case kept unless the name is plain lower case), dollar quotes, words, numbers and punctuation; statements are split once, with `BEGIN ATOMIC ... END` counted with a `CASE ... END` depth. Allowed shapes: **S1** `SET LOCAL lock_timeout` or `statement_timeout` (`=` or `TO`, one string or number; every other `SET`, `RESET`, `SET ROLE`, `SET SESSION AUTHORIZATION` in any spelling is a problem); **S2** `ALTER TABLE [IF EXISTS] [ONLY] name ADD ...` where every top-level action starts with `ADD` (`DISABLE TRIGGER`, `DROP CONSTRAINT`, `OWNER TO`, `SET` are problems); **S3** `CREATE TABLE`, `CREATE [UNIQUE] INDEX`, `CREATE TRIGGER` that executes a function listed for THIS file, `COMMENT ON`; **S4** `DROP TRIGGER IF EXISTS name ON name`; **S5** `REVOKE ALL|EXECUTE ON FUNCTION signature FROM PUBLIC` for a signature listed for this file; **S6** `CREATE OR REPLACE FUNCTION` of an unqualified name whose signature is on the **per-file list** (`ALLOWED_BY_FILE`: file name, function name with types, definer or invoker); **S7** a statement whose fingerprint (the first 16 hex digits of the sha256 of its tokens, comments removed) is pinned for this file (`EXTRA_BY_FILE`: the duplicate-decision `DELETE`, the month backfill `INSERT` and the switch-row `INSERT` of migration `0003`, and the two `DROP CONSTRAINT`, `ADD CONSTRAINT` statements of the upgrade file): a pin, not a shape. Everything else is a problem, including `SELECT`, `DROP`, `LOCK`, `CALL`, `PREPARE`, `REASSIGN OWNED`, `CREATE VIEW`, `CREATE POLICY`, `COPY`, `GRANT` (all forms, including `ALTER DEFAULT PRIVILEGES` and `TO PUBLIC`), `DO`, `CREATE PROCEDURE` and any statement at file level that writes rows. **Rules inside a function, kept from v18:** the name and the normalised argument types are on the list; a definer function has `SET search_path = pg_catalog, pg_temp` exactly and no other `SET`; `EXECUTE` is `format(` with `%I.` for every relation and no `%s` or `%L` in a relation position. **New in v19 (MA1 and MA2 of the v18 review):** **N1** a function name or a type with a schema in front of it is a problem (`other.spend_reserve(...)` can no longer stand for the listed `spend_reserve(...)`), a quoted name or type keeps its case (`\"Spend_Reserve\"` and `\"Date\"` are not `spend_reserve` and `date`), and the `REVOKE` must name the same unqualified signature; **N2** the `REVOKE` of a signature must come AFTER the last `CREATE` of that signature in the file (a `REVOKE`, then `DROP FUNCTION`, then `CREATE OR REPLACE` re-opens PUBLIC `EXECUTE`), `DROP FUNCTION` is refused, a signature created twice is refused; **N3** a `BEGIN ATOMIC` body is scanned (v18 never scanned it): only the relations pinned for that file (`ATOMIC_TABLES_BY_FILE`: `spend`, `spend_month`, `kill_switch` for DB-3), no `ALTER`, `GRANT`, `CREATE`, `DROP`, `RESET`, `CALL`, `DO`, `EXECUTE`, a `SET` only as part of an `UPDATE`, and in EVERY definer body (atomic, plpgsql or sql) a called function must be on a short list (`CALLS_OK`): `set_config`, `query_to_xml` and its relatives, `dblink`, `pg_read_file` and every other name are refused because they are not listed. **A file name that is not a key of `allow_v19.py` gets nothing allowed (fails closed; security minor m4): the move PR that renames a held file renames its key in the same commit, and the guard test names the file in every problem.** **Run on 16.15 (`evidence-handoff-v19/raw/raw-secdef-mutants-v19.txt`): `python secdef_mutants_v19.py held-sql <migrations folder>`: 152 checks, 0 failed.** They are: the 20 mutants S01 to S20 of v17, one mutant per spelling A to F of v18 (3, 5, 3, 5, 6 and 11), 9 controls K (clean text that must NOT be flagged, so the guard is not \"flag everything\"), the independent runner's 27 hostile spellings of v18 (`spellings.json`, `spellings2.json`, each run through v16, v17, v18 and v19; 27 R checks), 2 parser tests, **51 new mutants N01 to N51 (the order of `REVOKE`, `DROP FUNCTION` and `CREATE OR REPLACE`; `SET \"role\"`, `SET session_authorization`, `RESET`, `SET LOCAL \"role\"` in quoted and underscore spellings and `set_config`; file-level `SET search_path`; top-level `CALL`, `PREPARE`, `REASSIGN OWNED`, `CREATE VIEW`, `CREATE POLICY`, `COPY`, `COMMIT`, `SELECT`, `DROP`, `LOCK`, `INSERT`, `UPDATE`, `DELETE`; `ALTER TABLE` with `DISABLE TRIGGER` or `DROP CONSTRAINT`; calls of `query_to_xml`, `set_config`, `pg_read_file` in definer bodies in five spellings; unpinned or schema-qualified relations and `SET ROLE` in `BEGIN ATOMIC` bodies; schema and case aliasing of function names and of types; a file name that is not on the list)** and the 5 real held files and 5 real migrations (no problem). **The v18 guard misses 49 of the 51 new mutants (the other two, N35 and N49, are flagged by v18 for a weaker reason and by v19 for the new rule: 3 problems against 1 and 2 against 1); the v17 guard misses 89 of all 152 and the v16 guard 117.** The independent runner's 30 spellings of the v18 evidence run, copied into `spell30_runner_v18_copy.py`: **all 30 are flagged by v19; v18 misses one (`CREATE VIEW`)** (`raw/raw-spell30-guard-v19.txt`). The script needs both folder arguments and exits 2 with a usage line without them. The guard is run over the five held files and the five product migrations with no problem (`raw/raw-chk-v19.txt`). Not covered, stated: the guard is a text check on `.sql` files; a function made in a console is seen only by the start-up query of item 1(o2); a SQL spelling nobody has tried can still exist, which is why the list is of allowed shapes and not of bad ones, why every shape has a mutant and why the start-up query checks the real catalogue as well; **there is still no independent run of v19: v17 had 8 and v18 had 1 spelling that the author did not think of, so expect more until a runner finds none.** A file that adds such a function without being on the list fails the guard in CI."))

# ---------------------------------------------------------------- 5.6 (o) DB-3
rep("(sha256 `244d2a06c7565ee4b23c466e38da57c8d34b7f2fe47f05c655d78edd9895c230`; v17 was `03380075e512c1e2218c0da4fbae078f6542bae1f61a67a8c499eaceb9b9ed6e`)",
    "(sha256 `40d8b345a0a807cb38d168b18779c88c281be61914b42e4181861a8fc48eaaa3`; v18 was `244d2a06c7565ee4b23c466e38da57c8d34b7f2fe47f05c655d78edd9895c230`; v17 was `03380075e512c1e2218c0da4fbae078f6542bae1f61a67a8c499eaceb9b9ed6e`)")
rep("*How the roles are used (the file names no role; `GRANTS` and the move PR do):*",
    "**v19 adds (the independent run of v18, security minors m2, m3 and m7):** (a) a day window: `spend.day` and `spend_month.month` must lie in 2020-01-01 to 2099-12-31 (checks `spend_day_window` and `spend_month_window`, `NOT VALID`; `infinity`, `-infinity`, 1999-01-01 and 0001-01-01 are refused `23514`; the window is my number and the owner may change it); (b) an agent id may not have leading or trailing blanks, a control character (newline, tab) or a form that is not NFC (the two spellings of one accented name were two budgets; `NOT VALID`, so rows that exist are not rescanned); (c) a reserve of 0 or less writes no row (an amount of 0 made a 0 / 0 row); (d) `spend_settle` changes the month row only when the DAY row exists, so a settle for a day with no row changes nothing and returns no row (v18 lowered the month row by up to the open amount: m2); the store (L-2) must treat an empty result of `spend_reserve` or `spend_settle` as an error (T); (e) `SET LOCAL statement_timeout = '60s'` after the `lock_timeout` line, because the checks that scan the tables take an exclusive lock and `lock_timeout` bounds only the wait for it (m7; it overrides a stricter value of the caller for that transaction, stated). **Stated, not closed:** names that differ only in letter case or by an inner blank are separate budgets; row spam inside the window (any agent name, any day, unlimited rows) stays possible for the holder of the runtime login (m3); a settle with `actual` above `worst` can raise a total. The money columns `usd` and `open_usd` of DB-3 are numeric dollars, so D5 (the money unit, OWNER-OPEN) would change them later (security minor m8); the 1,000,000,000,000 ceiling is my number, not a rule from any source. *How the roles are used (the file names no role; `GRANTS` and the move PR do):*")
rep("and **fails 23514 when `worst` is larger than the open reservation**", "and **fails 23514 when `worst` is larger than the open reservation (and, v19, changes nothing when the day row is missing)**")
cut("*Run on 16.15 (`raw/raw-pg-v19-run1.txt` and `-run2.txt`, `pg_v19.py`: 114 of 114 checks", "MA3 the control and the four `migrate()` runs", (
    "*Run on 16.15 (`raw/raw-pg-v19-run1.txt` and `-run2.txt`, `pg_v19.py`: 120 safety checks, 24 controls (each fails on the old design or file) and 3 stated exploits, reported as three separate counts since v19, security minor m6 of the v18 review: v18 counted \"stated, not closed\" exploits as passes; the G, MA, m, K, L and H series are the ones about these files): "))
rep("G12 (unbounded inputs): a reserve of 1,000,000,000,000 is refused 23514 and 999,999,999,999 accepted, an agent name of 0 or 201 characters is refused, and the cross-agent settle is shown to work (stated above, not closed);",
    "G12 (unbounded inputs): a reserve of 1,000,000,000,000 is refused 23514 and 999,999,999,999 accepted, an agent name of 0 or 201 characters is refused, **v19: the five day values above are refused, a reserve of 0 writes no row, five agent-name spellings (NFD, blanks only, leading blank, newline, tab and quote) are refused and the NFC spelling is one budget; m2: a settle for another day of the same month without a day row returns no row and leaves the month row alone and the honest settle still works afterwards; three stated exploits are shown to work and counted apart: the cross-agent settle, names that differ only in case, and a settle of 5 against a worst of 0**;")
rep("**Controls (the same assertions fail on the old design):**", "**Controls (the same assertions fail on the old design; v19 adds the v18 files as the old design: a settle for a day without a row lowers the month row, the INSERT of a missing switch row writes no record, `CREATE VIEW` passes the v18 guard):**")

# ---------------------------------------------------------------- 5.6 (o2), (p)
rep("the MA2 and m7 series of `pg_v19.py` as product tests).", "the MA2 and m7 series of `pg_v19.py` as product tests; v19: names come from `p.proname` (the v18 text parse read `x.spend_settle` as `spend_settle`) and a grantable column is reported (security minor m5 of the v18 review). **Not done in v19 and why: body content is not pinned (item 0 (5g)); membership is checked for the runtime role and the operator role only.**)")
cut("   **(p) What was run in v17", "\n\n", (
    "   **(p) What was run in v19 (all on 16.15, throwaway clusters with password logins, made-up data; raw files in section 8).** (1) The 175 v16 checks against the v19 files, one `ALLOWED` set edited: 175 of 175 in two runs. (2) `pg_v19.py`: 120 safety checks, 24 controls, 3 stated exploits, two runs. (3) 152 guard checks, 30 runner spellings, the guard over the real files. (4) The secrets isolation test with a second operating-system user: 12 of 12, plus the pre-check. (5) `compare_gate4.py` on four cases. **Not run:** Postgres 14 and 17.10, parallel load, a Windows checkout, the product tests (not written), `gate4_v19.sh` itself, `ruff`, `pytest`, `bandit`, the cite programs (carried)."))

# ---------------------------------------------------------------- 7.2: gate4 (Ma1) and the conditional table (Ma2, Ma3)
cut("**`gate4.sh` is carried from v14 and its output folder is hard-coded", "), pass rule, author PR.", (
    "**one command in every row (readiness major Ma1 of the v18 review: v18 named `evidence-handoff-v14/gate4.sh`, `gate4.sh` and `gate4_v18.sh` and two output folders in four places): `sh evidence-handoff-v19/gate4_v19.sh <row id>`; the five outputs of every evidence row land in `evidence-handoff-v19/`; the script ends by running `python -I evidence-handoff-v19/compare_gate4.py <row id>`, whose exit code is the verdict; the baseline is `evidence-handoff-v19/baseline/` (byte copies of the v16 `raw-gate4-base-*.txt`)**; `E0-*.txt` and `E0-*-failing-on-old.txt` names in this table are **PLANNED outputs: they do not exist until a runner writes them**"))
rep("`sh evidence-handoff-v14/gate4.sh E0-S1-1`", "`sh evidence-handoff-v19/gate4_v19.sh E0-S1-1`")
rep("`sh gate4.sh E0-S2-1`", "`sh evidence-handoff-v19/gate4_v19.sh E0-S2-1`")
rep("`sh gate4.sh E0-S2b-1`", "`sh evidence-handoff-v19/gate4_v19.sh E0-S2b-1`")
rep("and the failing test ids AND their failure messages (printed by `-rfs`; compare the lines, not only the count) equal the recorded baseline: a new failure that hides behind one of the two old ids is a failure**",
    "and the script `compare_gate4.py` (five lines of logic, written in v19, tested on four cases in `raw/raw-gate4-compare-v19.txt`: the baseline against itself exits 0; a new failing name, a `perf` rc of 1 and a larger failed count each exit 1) finds no failing test name outside the two of the baseline, no more failed tests than the baseline, and no error count in the pytest summary line. The names are the `____ name ____` headings of the FAILURES section: this repository's pytest prints no `FAILED` lines under `-rfs` (found while writing the script; v18 said `-rfs` prints the ids). **The script does not compare failure message text** (the baseline message lists files under `handover/`, which change when files are added), so a new failure that hides behind one of the two old names is not caught by it: the reviewer reads the two messages once at the head**")
rep("`gate4.sh` ran once in v16 (`evidence-handoff-v16/gate4_v16.sh`, a copy) on the UNCHANGED tree", "`gate4.sh` ran once in v16 (`evidence-handoff-v16/gate4_v16.sh`, a copy; v19 has `gate4_v19.sh`, not run) on the UNCHANGED tree")
rep("(raw files `raw-gate4-base-*.txt`).**", "(raw files `evidence-handoff-v19/baseline/raw-gate4-base-*.txt`, copies of `evidence-handoff-v16/raw-gate4-base-*.txt`).**")
rep("and writes every output file into `evidence-handoff-v14/` whatever folder it is started from.", "and writes every output file into `evidence-handoff-v19/` whatever folder it is started from.")
rep("it was only syntax-checked with `bash -n` and compared line by line with `ci.yml` (`evidence-handoff-v14/raw-gate4-vs-ci.txt`); its first run is its first test;",
    "it was syntax-checked with `sh -n` (v19) and its five commands are the five of v14, compared line by line with `ci.yml` in v14 (`evidence-handoff-v14/raw-gate4-vs-ci.txt`; not re-compared in v19); `gate4_v19.sh` itself has NOT been run; its first run is its first test;")
# conditional table
rep("| L18: Postgres versions | tests run on 16.15 only (author); CI uses 17.10 | an independent runner repeats `run_pg_v19.sh` and `run_secrets_v19.sh` on 14 and 17 |",
    "| L18: Postgres versions | floor 14 for the upgrade file, DB-2 and DB-3 (the one default, stated in section 10 L18); my tests ran on 16.15 only; CI uses 17.10 | an independent runner repeats `run_pg_v19.sh` and `run_secrets_v19.sh` on 14 and 17, or the lead names another floor |")
rep("| L21: the move PR | the lead adds `GRANTS` entries and numbers when it moves the held files | as default | the E1 to E4 rows of the move PR carry the tests; nothing else changes. |",
    "| L21: S-1 split (readiness major Ma2 of the v18 review: v18 labelled this row \"the move PR\", which is not L21) | not split: S-1 is one PR and the merge order of 7.1 has 14 ids | accepted: S-1a (config, `errors.py`, `SpendWindow`, `Gate`, `llm/spend.py` helpers, `clean_tokens`) and S-1b (`WindowOnlyGate`, `NetworkLLM` wiring, `chain_status`, `status_of`, the `k1b` handler); 15 ids | proposed division of the S-1 rows, the lead may change it: E0-S1-2, E0-S1-3 and E0-S1-4 (config, window, formula) belong to S-1a; E0-S1-6 and E0-S1-7 (census, construct) to S-1b; E0-S1-1 and E0-S1-5 (gate4, import graph) run at each of the two heads; no test text changes. |\n"
    "| (not a numbered question) the move PR | the lead adds `GRANTS` entries and numbers when it moves the held files | as default | the E1 to E4 rows of the move PR carry the tests; nothing else changes. |")
rep("| L22: DB-3 | not built, not applied; runtime role keeps `_RW` on the three tables | yes (names the new sha256) |",
    "| L22: DB-3 (needs L23 as well) | not built, not applied; runtime role keeps `_RW` on the three tables | yes (names the new sha256) AND L23 answered (both are start gate G-5) |")
t = t.replace("\n| L22: DB-3 (needs L23 as well)", "\n| L23: the operator role | DB-3 is not applied (nobody is named) | the lead names the human login or separate service identity that holds `kill_switch_release` | E0-DB-4 gate G9 runs with that login as the operator role; the function-grant step names it; the operator role gets `EXECUTE` on `kill_switch_release` only and no table right (checked by MA4); the start-up query's role list gains the name; the secret of that login follows 5.6 item 1(g2) (stored where the agent's identity cannot read it). |\n| L22: DB-3 (needs L23 as well)", 1)

# ---------------------------------------------------------------- section 8
i8a = t.index("## 8. Evidence saved this pass")
j8a = t.index("**v16 evidence (kept as it was):**")
t = t[:i8a] + (
    "## 8. Evidence saved this pass (`evidence-handoff-v19/`; `evidence-handoff-v16/` and the older folders stay and are named where carried)\n\n"
    "**New in v19.** `sha256-v19.txt` hashes every file of the folder except itself (it cannot hash itself) and includes `INVENTORY.md`, which names `sha256-v19.txt` (readiness minor 6 of the v18 review: v18 did not say this). Run `sha256sum -c sha256-v19.txt` in `evidence-handoff-v19/`; not run on a Windows checkout.\n\n"
    "| Held file (`evidence-handoff-v19/held-sql/`) | sha256 | Same as v18? |\n|---|---|---|\n"
    "| `spend_nonneg.sql` (DB-1 default) | `5d765255bd1c7477d0bab11c281171b2bb331f0ac4dd08c2151403ba47cc1093` | yes |\n"
    "| `spend_nonneg_finite.sql` (DB-1 variant) | `bd0409c9bde0ef91dc71f1b28eb960caad4818e01312a669b12e260949d9fe84` | yes |\n"
    "| `spend_nonneg_upgrade.sql` (DB-1 upgrade) | `fafa71faa08df60423276e4235714e9772f47256d64321f7e7f189691bbf041f` | yes |\n"
    "| `spend_decrease_log.sql` (DB-2) | `c0c4913eede84ead97a33b1e1d2c3f055987f7e12854936ba27ef0b3585cdaf2` | **no** (v18: `e3111401ec65caed136d8c7ff56b4e7374677a3126f7bb42549bb41f759c2ce9`; v17: `b4dfdf3a62d390951b3c9c3df2275103645983a7fe5e73477611dc25238e1ec9`) |\n"
    "| `spend_guarded_writes.sql` (DB-3) | `40d8b345a0a807cb38d168b18779c88c281be61914b42e4181861a8fc48eaaa3` | **no** (v18: `244d2a06c7565ee4b23c466e38da57c8d34b7f2fe47f05c655d78edd9895c230`; v17: `03380075e512c1e2218c0da4fbae078f6542bae1f61a67a8c499eaceb9b9ed6e`) |\n\n"
    "Files: `run_pg_v19.sh` (private throwaway cluster, password logins only, one cluster at a time), `pg_v19.py` (120 safety checks, 24 controls, 3 stated exploits), `pg_v16_regress.py` (the 175 v16 checks against the v19 files; one `ALLOWED` set edited), `secdef_guard_v19.py`, `allow_v19.py`, `chk.py`, `secdef_mutants_v19.py` (152 checks; needs two folder arguments), `spell30_guard_v19.py` and `spell30_runner_v18_copy.py` (the independent runner's 30 spellings), `spellings.json` and `spellings2.json`, `secdef_guard_v16.py`, `secdef_guard_v17.py` and `secdef_guard_v18.py` (kept only for comparison), `secdef_audit_v19.py` (the start-up query and the function-grant prototype), `run_secrets_v19.sh` (12 checks and the pre-check) and `agent_probe_v19.py`, `gate4_v19.sh` (NOT run), `compare_gate4.py` and `baseline/` (the comparator and its baseline), `banned_count_v19.py` (reads `BANNED` from `tests/test_no_reference_material.py` at run time), `patch_v19_main.py` (builds this text from v18), `INVENTORY.md`, `sha256-v19.txt`, and the raw files in `raw/`: `raw-pg-v19-run1.txt` and `-run2.txt`, `raw-pg-v16-regress-on-v19-run1.txt` and `-run2.txt` (175 of 175), `raw-secdef-mutants-v19.txt` (152 checks), `raw-spell30-guard-v19.txt`, `raw-chk-v19.txt`, `raw-secrets-v19.txt` (12 of 12), `raw-secrets-precheck-v19.txt`, `raw-gate4-compare-v19.txt`, PG version lines, and the banned-string count `raw-banned-count-v19.txt` (written at the end).\n\n"
) + t[j8a:]

# ---------------------------------------------------------------- section 10
cut("**Postgres:** what I ran is listed in 8", "**Not run:** Postgres 17.10", (
    "**Postgres:** what I ran is listed in 8 (local version 16.15, scratch cluster, stopped and deleted afterwards): `raw/raw-pg-v19-run1.txt` and `-run2.txt` (120 safety checks, 24 controls, 3 stated exploits) and `raw/raw-pg-v16-regress-on-v19-run1.txt` and `-run2.txt` (175 of 175 checks each), including the migration step as a non-superuser role. "))
cut("- **L18** (needs-lead, new in v16)", "\n- **L19**", (
    "- **L18** (needs-lead, new in v16) **The lowest Postgres version the studio supports.** Nothing I read states it. **Default, stated once (readiness major Ma3 of the v18 review: v18 stated it three ways):** 14 or newer for the upgrade file, DB-2 and DB-3, because `'Infinity'::numeric` and `BEGIN ATOMIC` do not exist before 14; the default DB-1 file has no version-dependent syntax and works on any version; CI uses 17.10; my own tests ran on 16.15 only, so 14 and 17.10 are NOT run. Ask: confirm or change the floor, and let an independent runner repeat `bash run_pg_v19.sh` (in `evidence-handoff-v19/`) and `bash pg_run_v16.sh` (in `evidence-handoff-v16/`) on 14 and on 17."))
rep("- **Unverified items and how each is settled (v16).**", "- **Unverified items and how each is settled (v19).**")
rep("`sha256sum -c sha256-v19.txt` on one,", "`sha256sum -c sha256-v19.txt` on one,", 1) if "`sha256sum -c sha256-v19.txt` on one," in t else None
rep("*Owner decides (nothing built or applied without a yes; the default is shown):*", "*(one list of defaults for L2 to L23; `v19-OPEN-FOR-LEAD.md` repeats it and nothing else; readiness minor 8) Owner decides (nothing built or applied without a yes; the default is shown):*")
# L23: say what the default holds
rep("Default: DB-3 is not applied.\n", "Default: DB-3 is not applied. (v19: start gate G-5(b).)\n") if t.count("Default: DB-3 is not applied.\n") == 1 else None

(root / "CORE-PR-HANDOFF-v19.md").write_text(t, encoding="utf-8")
print("written", len(t), "bytes;", t.count("\n"), "lines")
