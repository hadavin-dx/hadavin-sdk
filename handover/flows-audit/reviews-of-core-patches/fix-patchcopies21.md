# Fix report, round 21 (fixer session; files: patch-copies/README.md and patch-copies/DEAD-MAN-CHECK.md only)
Time: 2026-11-16, 19:12 to about 19:30 UTC by the sandbox clock = 00:42 to about 01:00 IST on 2026-11-17.

## Failures, gaps and contested items first
- NOT run: the changed recipe functions of README.md as a whole (`setup`, `verdict_run`, `proof`, `final`, `keep_logs`, `cleanup`); they were checked only with `bash -n` (13 of 13 fenced blocks ok). The README changes are therefore untested as running code.
- NOT run: any of the new SQL (DMC checks 1c, 1d, 5), the job against a real store, scheduler or alert channel, macOS, bash other than 5.2.21. The job script WAS run with fake programs as root (cases in DMC item 2f); the refusals that depend on file owner and mode were not shown with an ordinary user.
- NOT shown against old code: that closing descriptors above 9 matters (the test only shows the new script does not pass descriptor 7 on).
- Still open (not impossible, not deferred by choice of rule: time box): re-reading the other `file:line` cites of both files against `git show b4cce5b:<path>`. Four were read and agree (`tick.py:319`, `migrate.py:172-173`, `migrate.py:193`, `0003_approvals_tick.sql:30-35`). Next step: one session reads the rest.
- Contested: DMC nit (S5 grants `last_run_at`, unused) is wrong: the query selects `last_run_at`; unchanged. DMC m7 `PUBLIC` part was already covered by check 3 query a; only `pg_db_role_setting`, row security and SCRAM were added.
- Exceptions that stay (need a frozen patch edit, owner/lead): the missing self-hosted price test and the wording RV-A1, both marked EXCEPTION with the next step in README.md.
- Correction of an earlier claim: README and DMC said the tree of `b4cce5b` is missing. In this checkout it is readable (`git show b4cce5b:<path>`; `git archive`; a fresh clone then `git fetch origin <sha>` reaches it). The text now says so.
- Unverified inputs: the saved reader reports; each item was checked against the file before editing.

## Verification output (from handover/flows-audit)
- `ruff format --check .`: 1010 files already formatted
- check_refs.py: PASS 5193 references; check_names.py: PASS 655 rows; check_secrets.py: PASS 0 hits in 2885 files; check_counts.py: PASS 52 files / 655 nodes
- sha256sum prefixes: A-01.patch 64fdf315, C-01-price-only.patch e7ff677e, C-01.patch ca4982eb (unchanged)
- `bash -n`: README 13 of 13 ok; DMC 8 of 12 ok, the 3 failing blocks are SQL/sample output (same 3 failed before my edits; checked against the backup)

## Table: finding to change
| Finding | Change |
|---|---|
| README M1 (setup/verdict read the patch files again from `$P`) | `setup` copies the three patches into `$W/patches`; check, apply and patch-id all read the copy |
| README m1 (bash only) | words and START HERE: bash-only warning, version check, only 5.2.21 tried |
| README m2 (stamp too narrow) | `sg` stamp covers clone, gates, exit codes, logs, failed-test lists |
| README m3 (ALL_PROXY) | added to removed variables and to scrub text |
| README m4 (proof overclaim) | worded as counts, 12 of 30 (13 of 32) fail, rest are controls |
| README m5 (old PROOF OK / final.txt) | `proof` removes them before any guard |
| README m6 (keep_logs partial copy) | removes partials, unsets K, stops |
| README m7 (cleanup after good run lost result) | cleanup needs keep_logs unless DISCARD_LOGS=yes |
| README m8/m9 (undefined words, headings, stale "tree missing", clause (e) test) | words box row, headings, corrected, patch-id run on real patches reported |
| DMC M1 (column type) | stated TIMESTAMPTZ, check 1d, timezone=UTC |
| DMC M2 (check 1c) | `*` pgpass file, pass only on pg_hba text |
| DMC M3 (signal) | run_at and STORE_LABEL in signal; receiver rules |
| DMC M4 (env backend) | backend removed; secret-like variables unset for psql |
| DMC m1-m10 | see DMC history, twenty-first pass |
| r20b M1-M3, r20c M2 | already fixed in pass 20 (checked in text); r20c m9 exceptions stay |
