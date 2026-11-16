# fix-patchcopies10 (tenth fixer pass, security path) for patch-copies README.md and DEAD-MAN-CHECK.md
Static only. Not run: every recipe line changed here (checked with `bash -n` only: 4 README blocks and the password block, all "syntax ok"), every new SQL query, the pg_hba / no-password test, the verdict script change. Reviewer words were checked against the files; none was wrong. The .patch files were not touched; `git apply --check` on a fresh `git archive b4cce5b` extract: C-01 rc=0, C-01-price-only rc=0, A-01 rc=0.

| Finding | Result |
|---|---|
| B1 (failed cd applies in current folder) | fixed: README recipe is now function `setup`, every failure `return 1`, `cd` guarded, `git rev-parse --show-toplevel` must equal `$W/patched` before any `git apply`; last line prints STOP. not run (bash -n only) |
| M1 verdict clause (e) | fixed: PASSED needs (a),(b),(c),(e); ADDS NO NEW FAILURE says (a) to (e) |
| M2 "Apply" definition | fixed: line 3 defines apply as a folder you keep; recipe's clone is "run the recipe" |
| M3 row 7 vs Decision 23a/23b | fixed: row 7 and the numbering-scheme row say it has no Decision of its own; 23a and 23b named as other questions |
| M4 overclaims | fixed: "verdict EXPECTED today, derived by hand, script never run on real logs"; fifth-pass verdict marked derived by hand; exit-code table says which were seen (unpatched extract only for exact lines); script prints "non-database verdict ..." after PASSED; DEAD-MAN line 5 and negative-test "seen once" reworded (only exit 3 seen, no alert channel) |
| M5 shred / CHANGE THIS | fixed: CHANGE THIS marker, shred commented out until the storage place exists, recovery = repeat with a new secret |
| code M1 proof exit=1 | fixed: output to proof.log, proof needs exit=1 AND last line `12 failed, 18 passed` (`13 failed, 19 passed`); 99/98 for failed cd / git add. not run |
| code M2 pg_hba, no-password, VALID UNTIL | fixed: new section "Checks on a real store", items 1 and 2. not run |
| code M3 catalog queries | fixed: queries a to f (relations incl. PUBLIC, columns, functions with prosecdef, pg_default_acl, membership and attributes, schemas, TEMPORARY); cites `effective_problems` `store/migrate.py:192`. not run |
| N4 STOP must stop | fixed (function `setup`) |
| N5 failed cd rc | fixed: `run` writes rc 99; verdict (c) then FAILED |
| N6 exit status, variable list | fixed: last script line prints exit status; variable and function list extended |
| N7 env -i, proxy CA | fixed: Who-runs table and proxy note (SSL_CERT_FILE) |
| N8 ci.yml re-cite | fixed from `git show` at both commits: install :77/:78, ruff :79,:81 / :80,:82 |
| N9 role attributes, soft limits, stdout | fixed: NOINHERIT NOREPLICATION NOBYPASSRLS; statement_timeout soft, CONNECTION LIMIT enforced; alert on stdout lines or exit code only |
| N10 password block | fixed: subshell umask+pipefail, `-s` check, clipboard always cleared, shred caveat, PGSSLMODE verify-full on admin psql |
| citation M1 Decision line numbers | fixed: cited by name, no line numbers (REVIEW.md Decision 18/19/21/23a/23b are now at 397/398/400/402/403, would drift again) |
| citation M2 ci.yml :80/:82 | fixed |
| citation M3/M4 3.12 job, scan_repo | fixed: README lines 90, 120, 207 say 3.13 only at b4cce5b (:73,:109); tests-py312 (:105), scan_repo (:84), stage mutants (:94) only at bbfbeee19; b4cce5b extras listed with lines |
| citation M5 row 7 | fixed (see M3) |
| DEAD-MAN:49 weak cite | fixed: creation cited to `0003_approvals_tick.sql:29` (unqualified CREATE TABLE); `migrate.py:172-173` described as the grant only; creation in `public` marked inference, UNVERIFIED |

Not fixed (below threshold, reader list): DEAD-MAN line 139 variables list omits SHA; README "bandit with tools added" wording; "2 kinds" unnamed. Needs lead: none. Reader's "org handle in repo address": `git remote -v` shows the same org address as the file (confirmed studio repository; it is an organisation name).

## Raw outputs (from handover/flows-audit)
python3 -I tools/check_refs.py : PASS 5176 references
tools/check_names.py : PASS 655 rows
tools/check_secrets.py : PASS 0 hits in 2646 files
ruff format --check . : 794 files already formatted
git apply --check on fresh git archive b4cce5b: C-01 rc=0; C-01-price-only rc=0; A-01 rc=0
Note: git status shows README.md as unmodified (another session already committed it, last commit 2d19c8cc4); my edits are in the file. Nothing committed by this pass.
