# fix-findings8 (section H of reviews/round-16z-findings.md; fixer, static only; EGM skipped: fixer role)

Files changed: FINDINGS.md, LEDGER-ROWS.md (this log is new). Backups: scratchpad bak-fl8-FINDINGS.md, bak-fl8-LEDGER-ROWS.md. Nothing committed. No severity changed.

## What I verified first (reviewer claims against the files)
- M2 true: FINDINGS lines 21 and 65 said "Postgres down gives 503".
- M3 true: row says T19 and T20; Q27 item 9 says T19-T21; Q29-3 names T19/T20 only; only T21 exercises ReplyStoreFail.
- M5 true: `grep -c -E "60\.1|61\.9|25 to 30"` on the run sheet prints 7 today; after applying F-003 patch to a scratchpad copy it prints 0 (apply exit 0). Real repo `git apply --check` exit 0. All 8 save settings in real-v5 read "none" today.
- M7 true: ORDER 007 item 2 does not name F-037 (it is in item 5, as a new finding); no ORDERS line gives it a rating.
- F-007 nit true: mf.py:153-164 K3B = mail NOT delivered; PAGE-STATEMENTS:150/:153 and run sheet :90 say "killed after the mail left"; run sheet :24 agrees with mf.py.
- M1: the lead's earlier method was WRONG. Tested on a throw-away Postgres 16 (made-up db and role, removed afterwards): `REVOKE CONNECT ... FROM role` changed nothing (new session still worked, because CONNECT is granted to PUBLIC). `ALTER ROLE .. NOLOGIN` blocks new sessions ("not permitted to log in") but leaves open sessions running; `pg_terminate_backend` ends them (1 session before, 0 after). Restore with `ALTER ROLE .. LOGIN` worked.

## Fixes (both files unless marked)
- M1: T21 METHOD written as 6 steps with commands (NOLOGIN, terminate sessions, proof of cut, send, restore, resend, mailbox and row check), T21 INVALID if first reply is not 503, recorder = lead at the practice run, log path LEAD FILLS.
- M2: lines 21 and 65 now say "take database made unreachable for the flows' role", server not stopped.
- M3: lift condition paragraph in F-002 fix cell (reading plus question); pointer in the "Scenes" paragraph. Severity cell untouched.
- M4: 10 s marked PROVISIONAL (Q24-2); wait = LEAD FILLS, written before T19 starts; T19 reply time = flow health, not the processed-once proof; T20 command (200 junk keys, form and hook path) plus before/after row count; T21 commands; recorder named.
- M5: F-003 pass line (apply check plus grep prints 0); F-008 pass line (grep -H -o over the four files plus ACCEPTED line); F-007 and F-041 allowed-hit lists pointed to TAKE-CHECKLIST.md check 13 (line 108) and GO row 7 (line 88), marked proposal until the lead writes them.
- M6: F-031 pass line split: part 1 closes the Blocker (Wed 06:00Z), part 2 is take-day proof only.
- M7: FINDINGS F-037 evidence cell now describes the fill_flows route (0 $env reads in filled copy, 3 in unfilled: Qualify 2, AlertSend 1) and states the rating source; rating note also in the fix cell of both files. Rating unchanged.
- Nits: F-005/F-006/F-023 take cell "take (file); scene out" and ledger area text; short answer item 4 carries "only after fix A of F-011 is tested"; F-011 sizing (fix A not in Tuesday's 1 hour re-smoke) and who writes downgrade evidence; F-007 evidence "opposite" narrowed; T19 reply-time wording; ledger header (summary cell is first sentence only, fix cell identical except F-001/F-013, row order is the ledger's own).

## Tests (what was and was not run)
- Commands extracted FROM the edited FINDINGS.md text and run: T20 loop against a made-up stand-in server (prints `done`, exit 0; a deliberately weakened copy printed `NOT 422` lines); T21 curl prints body and status (200, and 503 when the stand-in was set to fail). NOT run against n8n or the real flows.
- psql queries (count, state, F-031 select, terminate) run on the throw-away Postgres 16. Server stopped, /tmp/fl8-pg and /tmp/fl8-x removed. The throw-away server lived under /tmp (not the scratchpad) because the scratchpad parents are mode 700 and the postgres user cannot enter them.

## Checks (real exit codes, from flows-audit)
- `python3 -I tools/count_findings.py FINDINGS.md`: 45 rows, Blocker 5, Major 5, Nit 35, BEFORE 11, AFTER 34.
- Own script: 45 ids equal in both files, severities identical, LEDGER 9 columns on all 45 rows, fix cells identical except F-001 and F-013 (pre-existing).
- check_secrets.py exit 0 (0 hits, 1801 files); check_refs.py exit 0 (5160 references); check_counts.py exit 0 (52 files / 655 nodes); ruff check exit 0; ruff format --check exit 0.

## Questions for the lead (QUESTIONS.md is another fixer's file; not edited)
1. F-002: is T21 part of the lift condition? If T19 and T20 pass and T21 fails, is the take NO-GO or is the 503 path left out?
2. F-037: confirm Blocker (audit's own rating, no ORDER names it) or re-rate Major (pass is a grep like F-029).
3. F-031: confirm part 1 alone closes the Blocker and part 2 is take-day evidence only.
4. F-002 T21: confirm the lead accepts ALTER ROLE NOLOGIN plus pg_terminate_backend (not REVOKE CONNECT) as the method, and names the test log path.
5. T19 wait in seconds and N (replacing 10 s): lead fills after the rehearsal (already Q24-2).
