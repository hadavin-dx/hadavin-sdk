"""Writes ../v22-CHANGES.md, ../v22-OPEN-FOR-LEAD.md and INVENTORY.md (round 9). Usage: python3 -I -B docs_v22.py <pg run file> <regress run file>"""
import re, hashlib, sys
def rd(p): return open(p, encoding="utf-8", errors="replace").read()
m = re.search(r"SUMMARY safety checks (\d+) of (\d+) passed; controls (\d+) of (\d+) showed the old behaviour; stated exploits shown (\d+) of (\d+)", rd(sys.argv[1])); SF, ST, CF, CT, XF, XT = m.groups()
rg = [l for l in rd(sys.argv[2]).splitlines() if l.startswith("SUMMARY")][-1]; RG = re.search(r"(\d+) of (\d+)", rg); RG = f"{RG.group(1)} of {RG.group(2)}"
SHA = hashlib.sha256(open("held-sql/spend_guarded_writes.sql", "rb").read()).hexdigest()
CNT = f"{SF} of {ST} safety checks, {CF} of {CT} controls, {XF} of {XT} stated exploits"
ch = f"""# v22 changes (round 9): finding, fix, place, test

Sources: `review-handoff-v21-readiness.md` (B1, M1-M8, m1-m8), `review-handoff-v21-security.md` (MJ1-MJ5, m1-m8). The independent evidence of v21 was NOT relayed when this was written (`v22-OPEN-FOR-LEAD.md` item 1). Everything below was run by the author on Postgres 16.15 only; no count was re-run by anyone else. "Place" is a section of `CORE-PR-HANDOFF-v22.md`; "test" is a check in `evidence-handoff-v22/`. Final Postgres run: `raw/raw-pg-v22-run2.txt`: {CNT}. DB-3 sha256: `{SHA}`.

## Readiness (v21 verdict NOT READY)
- **B1** DB-3 header contradicted the grant table and cited items that do not exist: header rewritten (runtime role: reserve and settle; operator role: engage and release; pseudo ids: Option A or B of 5.6c item 8, no claim that the store skips the functions; ten ALTER lines; item numbers fixed). The sha256 changed (section 8). Test: `sha256sum -c sha256-v22.txt`; `chk.py` clean.
- **M1** one signature, and the owner: 5.5b item (3b) now names `secdef_problems(db, *, roles, policy=None, owner=None)`; 5.6c item 4 says the migration role must BE the database owner for the default to pass, and the error message names what the owner was compared with. Test: `pg_v22.py` MJ4 series.
- **M2** L19 stated once: record OR role, function `l19_check_applies`; 5.5b item 3, 5.6 item 1(h) and 5.6c item 4 point to it; E0-L19 gains the case "record without role". Test: `pg_v22.py` M2.
- **M3** S-2b split: S-2b-1 owns every new settings field and the base `limits status` line; S-2b-2 owns `startup_checks`, the secdef module, `limits status --check` and the secdef test file; hot files named per half; E0-F5 moves to the DB-3 move PR. "seven sessions" in the merge-order text is carried from an older count and was not re-derived (stated in `v22-OPEN-FOR-LEAD.md`).
- **M4** `startup_checks(self, environment, *, spend, postgres)`; `inputs_from_config` turns the two settings objects into the arguments. Test: `pg_v22.py` M4.
- **M5** `limits status --check`: an empty operator role is `WARN` before DB-3 and `FAIL` after; `limits reset` is never a reason; E0-L13 has fixtures for on-too-long, released-by-other, row-count warning and the audit-reader write probe; the weekly hand run is replaced by "nobody runs it until named" with a named default owner (the studio owner).
- **M6** E0-F5 tested code that does not exist at S-2b-2: it moves to row 5b (the DB-3 move PR) and runs on an agent-day with rows.
- **M7** other-tracks E0-O1: now `gate4_v22.sh`, pass rule = `compare_gate4.py` rc 0, folder and the PLANNED sentence corrected (`tests/test_g4_parity.py` exists: checked with `ls`).
- **M8** the L23 row says engage and release; the L22 row's pointer now says "5.6 item 1, sub-item (o)" (the sub-item exists at the line starting `(o) DB-3`; I could not reproduce "no longer exists", stated).
- **m1** cross-reference fixed to item 7. **m2** stale names: the blanket rename of every file name and raw cite to v22, with the comparison copies listed as v16 to v21; every raw file the text cites is checked to exist in `raw/` or in an older evidence folder by `raw-cite-check-v22.txt`. **m3** guard names. **m4** L26 says four functions. **m5** section 10 first paragraph: run counts and raw file names replaced; the rest is a list of what is not run, re-read and still true. **m6** done (other-tracks). **m7** the S-2b builder still reads the constructor signatures (UNVERIFIED, stated). **m8** this file lists only what the text now carries.

## Security (v21 verdict NOT CLEAN)
- **MJ1** reserve final SELECT unguarded: `AND p_worst > 0` added (DB-3 file); text 5.6(o), 5.6c item 3; tests `pg_v22.py` G7 (reserve of -1 returns no row), F5 (0, -0.01, -1e30, -Infinity, NULL on an agent-day with rows, tables unchanged), control: the v21 file returns the totals.
- **MJ2** `None` pins now means every ADD is a problem; mutant X05 (renamed DB-3 file); DDL pins for CREATE TABLE, CREATE INDEX, COMMENT ON as well (46 pins, product migrations included). Test: `secdef_mutants_v22.py` ({MC if False else ''}262 of 262).
- **MJ3** catalog checks (constraints, triggers, table rights, runtime role, dedicated owner): `catalog_problems` in `secdef_audit_v22.py`; each shown by a real change in `pg_v22.py` (MJ3 series).
- **MJ4** the default owner on a superuser-owned or managed database can never pass: stated, shown; the dedicated-owner path runs end to end (own22, NOLOGIN, schema CREATE granted then revoked, reserve and settle work); L26 text corrected (four functions, CREATE on schema, no ALTER DEFAULT PRIVILEGES needed).
- **MJ5** header and stale cross-references: header rewritten; every "5.6 item 1(o)" kept (it exists); other stale numbers listed above.
- **m1** zero and refused amounts stated in the header and 5.6c item 3. **m2** timeouts: positive whole number, units ms/s/min/h, at most one hour, timeouts before the first ALTER, required in held files (DB-3 both). Mutants X-series. **m3** ten ALTER lines, worst case about 10 minutes, drained cutover (5.6c item 9). **m4** guard version names; mutant variables renamed g22/A22/p22. **m5** pseudo id: Option A regex run on the server (11 cases), length rule (182+ characters have no pseudo id). **m6** guard accepts no unpinned CREATE TABLE, CREATE INDEX or COMMENT ON; timeouts required. **m7** L13 alert has a named default owner (the studio owner; the lead may change it). **m8** said plainly: counts were not re-run independently.

## What was not done and why
- DB-1 and DB-2 have no `statement_timeout` (L27: adding it changes two lead-approved hashes).
- `run_secrets_v22.sh` and `gate4_v22.sh` not re-run (slots busy; gate4 source tree unchanged: `raw/raw-gate-carry-check-v22.txt`).
- Postgres 14 and 17.10 not available. Stored constraint text not compared (needs 14 and 17).
"""
ch = ch.replace("({MC if False else ''}262 of 262)", "(262 of 262)")
open("../v22-CHANGES.md", "w").write(ch)
op = f"""# Hand-off v22: what only the lead or the owner can decide (one line each)

Format: id | default if unanswered | why | who decides. Silence never counts as a yes on a money, delete or secret rule. Full text: `CORE-PR-HANDOFF-v22.md` section 10 and section 0. This file repeats that list and adds L27 only.

## Do first (lead)
1. **Relay the findings of the independent evidence runner of v21.** Nothing of it reached me; it is not folded in.
2. **Run the EGM review of v22** (a builder cannot call the skills).
3. **Postgres 14 and 17.10** are not run (L18): an independent runner repeats `run_pg_v22.sh` there. **Independent re-runs of all counts** are not done.
4. Run `run_secrets_v22.sh` and `gate4_v22.sh` once (both carried from v21, not re-run in v22).

## OWNER-OPEN
- **L22** | DB-3 `spend_guarded_writes.sql` (sha256 `{SHA}`, changed in v22: header, and the final SELECT of `spend_reserve` is guarded) is NOT built or applied | runtime role SELECT on three tables and EXECUTE on reserve and settle; operator role EXECUTE on engage and release; needs the `GRANTS` change and the function-grant step in one PR | owner.
- **L7** | Infinity clause not applied. **L9** | DB-2 not applied. **L16, L17, D5, O1** | as in section 10 | owner.

## Lead's choices (not decided by me; each default is stated)
- **L22b** engage by the operator role only (default) or also the runtime role. **L23** who holds the operator role. DB-3 stays unapplied until named.
- **L26** dedicated NOLOGIN owner role for the four DB-3 functions. Default: not built. **New fact:** on a database owned by a superuser, or a managed database where the migration role is not the database owner, the default owner can never pass; there L26 is the only way to run DB-3 (shown in `pg_v22.py`).
- **L26b** pseudo agent ids `-cli` and `-unattributed:<agent>`: Option A (widen the rule; the pattern now ran on the server; agent names of 182 or more characters have no pseudo id) or B (a second table). Until you choose, DB-3 stays unapplied.
- **L27 (new)** | `statement_timeout` is required in DB-3 only. DB-1 and DB-2 have `lock_timeout` only; adding `statement_timeout` changes two hashes you approved. Default: leave as is | lead.
- **L13** the alert has a default named owner (the studio owner); change it if you want someone else.

## NEEDS-LEAD (defaults in section 10)
- **L18**, **L20**, **L21** (S-2b split in two sessions), **L19**, **L24**, **L25** as in v21. The merge-order sentence that says "seven builder sessions" was not re-counted: please confirm the count (eight with the S-2b split) before the first builder starts.
- My own numbers, yours to change: `spend.kill_switch_alert_minutes` 60, the day window 2020-01-01 to 2099-12-31, the 60 s `statement_timeout` of DB-3 (per statement), the 1,000,000,000,000 ceiling, the one-hour bound of a guard timeout.
"""
open("../v22-OPEN-FOR-LEAD.md", "w").write(op)
inv = rd("INVENTORY.md").replace("v21", "v22")
inv = inv.replace("Current layer (v22):", "Current layer (v22; round 9):").replace("(DB-3 changed in v22; the other four are byte copies of v20)", "(DB-3 changed in v22; the other four are byte copies of v21)")
inv += f"\nRound 9 additions: `patch_audit_v22.py`, `patch_pg_v22.py`, `patch_v22_main.py`, `patch_v22_other.py`, `finish_v22.py`, `docs_v22.py` (they build the v22 files from v21; run in that order), `raw/raw-pg-v22-run1-first-owner-bug.txt`, `raw/raw-pg-v22-run2.txt`, `raw/raw-gate-carry-check-v22.txt`. Not re-run in v22: `run_secrets_v22.sh`, `gate4_v22.sh` (v21 results in `../evidence-handoff-v21/raw/`).\n"
open("INVENTORY.md", "w").write(inv); print("docs ok")
