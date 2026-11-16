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

## Round 9 fix (FIXER, 2026-11-16; sources reviews/findings-r9-readiness.md and reviews/findings-r9-codebase.md; each claim read against the files first; nothing ran in n8n, Postgres or HubSpot; backups in the scratchpad as bak-f9-*.md)
Both FINDINGS.md and LEDGER-ROWS.md edited with the same text in every fix cell (old-vs-new compare: only F-001 and F-013 differ, as before). No rating changed; counts kept (45 rows, Blocker 5, Major 5, Nit 35, BEFORE 11, AFTER 34).
- F-002 (fix cell): T19 command and what to read from it; mailbox count method LEAD FILLS with needed-by time; IST added (07:00Z = 12:30 IST); log path needed-by time; flows must be imported and ACTIVATED (production /webhook/ address); T20 extra case with no key field; T21: PGPASSWORD for step 3, terminate count meaning and pg_signal_backend; F-002b proposed time; order and time of applying F-002 and F-008.
- F-007: naming table text written into the fix cell (from L3-5), lane3 mapping LEAD FILLS; cite check 13 corrected to line 257; pass part 2b checks table content; allowed-hit list LEAD FILLS with time; order against F-004 stated (F-004 patch first; verified from the patch context).
- F-004, F-028: order (F-003, F-004, F-007 table, F-028); F-028 pass line added (count of numbered statements equals the Total line).
- F-031: choice made (sentence in the run sheet; alert is the AFTER flow change); placement LEAD FILLS; order after F-003; IST; part 2 key list and time.
- F-011: setup commands, start line (LEAD FILLS), expected output (LEAD FILLS), negative test, slot, downgrade check (b) tightened, role count wording aligned with F-010.
- F-018: HubSpot contact count method, wait value source, DESK_ALERT_TO owner and time, probe time.
- F-029: grep -rlF over $FILLED and $EXPORT; contradiction (fails loudly vs silent trace) removed (UNVERIFIED stated).
- F-037: rating untouched; grep form changed to list form; worst case stated; filled copy status clarified.
- F-041: cites fixed (row 7 line 145, Block R7 226-236; "marked LEAD FILLS" claim removed; REPORT.md:622 described correctly); role count wording; Part A pattern mismatch noted.
- F-001: psql command, owner, time. NOT COVERED 1: stale T17-T21/M0/M1/K1 laptop line replaced. 'BEFORE n' defined in the header. F-009, F-015, F-017, F-021, F-032, F-035: decision proposed in words (lead confirms). F-027, F-039, F-046: pointers named.
## For other files (not edited by this fixer)
- TAKE-CHECKLIST.md:246 (check 3b): still says T21 uses revoke CONNECT and T19 "under 10 s (fixed bound)". Point it to the F-002 T21 METHOD (ALTER ROLE NOLOGIN plus pg_terminate_backend) and say N is PROVISIONAL (lead sets it, Q24-2).
- TAKE-CHECKLIST.md Block R7 Part A: grep pattern `one database` only; F-041 downgrade check (a) uses `one database|single database`; align with -E.
- TAKE-CHECKLIST.md check 7: needs the F-004 Blocker-if-said grep and the order note; row 13 / check 13 allowed-hit list and the K3/K3B wording are LEAD FILLS.
- FIX-PLAN.md: item 3 step 7 needs the DESK_ALERT_TO check owner/time (lead, at re-pin, before first lead); item 8b grep must read as in F-041.
- QUESTIONS.md / ORDERS.md: ORDERS.md:32 still says T1; F-002 lift question (T21), F-037 rating, F-031 Blocker question stay as listed above.
## Checks (exit codes read directly)
count_findings 0 (45 rows, 5/5/35, BEFORE 11, AFTER 34); check_secrets 0 (0 hits, 1813 files); check_refs 0 (5162 references); ruff check 0; ruff format --check 0.
