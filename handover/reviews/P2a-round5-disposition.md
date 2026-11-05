# P2a round 5 disposition (author of revision 7), 2026-11-05 18:01 UTC = 23:31 IST

Target: `handover/tickets/P2a.md` REVISION 7. Decisions applied exactly as in `reviews/P2a-round5-resolve.md` (33 rows, all PROPOSE FIX). Findings: `P2a-round5-adversarial.md` (ADV-R5-1..17) and `P2a-round5-correctness.md` (COR-R5-C1..C21). "Field N" = the template field in the ticket. Nothing in this file was run; every code cite I kept was read at `ce70eb5` (the `src` tree equals it) or, for PR50, with `git show 748849c:<path>`. All database claims of the new design are UNVERIFIED until the evidence runner adds S29-S39.

Status words: applied / contested / declined. Contested: none. Declined: none. Narrowed (applied in the narrowed form the resolve gave): ADV-R5-9, ADV-R5-16; ADV-R5-2 is applied as a cut.

| id | status | where in the ticket | note |
|---|---|---|---|
| ADV-R5-1 (blocker) | applied | field 7 (Store `set_kill_switch`, short connection); field 11 (Privileges, "Why the runtime has no UPDATE", "The stop function", "Role-level timeouts"); field 12 (real-login tests); field 13 mut-F1..F9, mut-G14, mut-G15, mut-ST13..ST15; PENDING LEAD 11, 27 | runtime SELECT only; SECURITY DEFINER stop function; role timeouts; "delay" wording removed. Disagreement noted below (regex placement) and one residual stated plainly: a compromised runtime can hold the function's row lock until the role timeouts end it; the stop then fails with a busy error, it never succeeds silently. |
| ADV-R5-2 | applied (cut) | v1.1 table row "In-process gate"; field 4 (Problem reworded); field 3 | P2a-1c, `StopOperator`, `StopBackend` code, `Limits.is_stopped()`, `source=` and the gate config go to v1.1; the Problem no longer claims a running program refuses an action. I list the extra items (`StopOperator`, `StopBackend`, `is_stopped`, `source=`) as my consequence of the cut. |
| ADV-R5-3 | applied | field 3 (Depends on P1m); field 5; field 9; v1.1 table row "Mutation runner and judge" | the runner, judge and `testing/__init__.py` are gone from P2a; the 21 runner rows leave. Whether P1m also takes those 21 PR50 rows is UNVERIFIED (P1m decides). |
| ADV-R5-4 | applied (disagreement on wording) | field 11 (Privileges: reset group `UPDATE ("on","by")` only; trigger text; stop function); field 13 mut-G11, mut-G17, mut-G18, mut-F1; field 12 | the resolve puts the regex on "the OFF to ON branch (reset)"; a reset is ON to OFF, where the trigger already overwrites `by` with the registered label (S8). Free text can enter only on OFF to ON (the stop), so the regex is in the stop function and in the trigger's OFF-to-ON branch. The stop function cannot compute the keyed hash, so `Limits` masks first and the function checks the label form. `effective_problems` extension named in field 9. |
| ADV-R5-5 | applied | field 7 (Masking); PENDING LEAD 13 (answer no); field 13 (no allow-list rows exist) | `limits whois NAME` reads an automated label; runbook example `whois meter:estimate_exceeded`. |
| ADV-R5-6 | applied | field 11 (Probe: RECONCILIATION and "PILOT GATE"); PENDING LEAD 10; field 16 | the reconciliation is stated as a convenience; the only authentic reset record is `kill_switch_resets`; the claim that it detects an out-of-band reset under a registered label is withdrawn; a named external reader is a pilot gate. |
| ADV-R5-7 | applied | field 13 mut-G2 (restored) and mut-G3 (kept); field 12 "hand-applied guard file" test | killer applies the guard file by hand with no `migrate`, asserts `tgenabled = 'A'` and that `session_replication_role = replica` does not skip the trigger. |
| ADV-R5-8 + COR-R5-C4 | applied | field 3 (Couplings: P4d rev 8 text, P4b1, P4c, P4b2, P3a, P5c, P0e; reserve-after-stop); field 7 (short connection); field 13 (de-duplication against P4d `w8`); PENDING LEAD 2, 26 | (a) P4d lines 24, 33, 243, 268 are false after this revision (P4d is rev 7 on disk, not rev 6): action for P4d rev 8; (b) P2a does not close the reserve-after-stop window, P4b1 recommended; (c) the short connection is built in P2a-1 and P4d's v1.1 row is withdrawn; (d) P2a keeps no mutant for code that P4d's wrapper owns; (e) sibling cites replaced by item names with the times read (line numbers in sibling tickets moved while I worked). |
| ADV-R5-9 (narrowed) | applied | field 13 (all rows with killers; [catalog] rows mut-G13 and mut-F9 counted separately; counts shown) | dropped rows that cannot fail: `REVOKE ALL FROM PUBLIC` on the trigger function, `kill_switch_resets` primary key; kept it for the stop function (mut-F5, real-login denial). Added the unmapped rows only where a killer exists (mut-G20, G25, G27). No new mutant classes beyond what other findings require (F, K). |
| ADV-R5-10 + COR-R5-C9 | applied (part not mine to edit) | header paragraph; field 11 (negative tests: S9, S20); field 13 | ids are `S<n>` and `mut-<class><n>`; the integer `set_config` case is cited as S20. S9's heading in `evidence/P2a-sql.md` ("update only") is in a file I may not edit: action for the evidence runner. The OFF-to-ON dry run and the model-versus-real differences (append-only error code, TRUNCATE trigger) are marked UNVERIFIED with planned runs S35, S38. |
| ADV-R5-11 | applied | field 11 ("Guard on the log table", Packaging); field 13 mut-G29, mut-G30, mut-P12 | `ENABLE ALWAYS` on the log triggers, a TRUNCATE-raise trigger, `guard_report` reads `tgenabled`. |
| ADV-R5-12 | applied | field 7 (Login label: `label` UNIQUE); field 11 (Probe: breakglass maps to the alarm label); field 13 mut-G31, mut-P13 | |
| ADV-R5-13 + COR-R5-C14 | applied (smaller diff chosen) | field 11 (Packaging, "apply as the migrator role"; `guard_report` owner check; owner-role membership); field 13 mut-P14, mut-G23; PENDING LEAD 2 | the NOINHERIT group login is marked UNVERIFIED (planned S36); the check and its mutant stay. |
| ADV-R5-14 + COR-R5-C10 | applied | field 7 ("Documented behaviour" ON-to-ON merge); field 12 race test (d); v1.1 row "In-process gate" | `restore(True)` on an OFF store goes with the gate to v1.1; the ON-to-ON merge is documented and tested. |
| ADV-R5-15 | applied | field 11 (`migrate(reset_role=...)` refuses `public`, `session_user`, `current_user`, `none`-like); field 13 mut-G32; field 12 | P4b2 keeps its own refusal for other role arguments. |
| ADV-R5-16 (narrowed) | applied (cut) | v1.1 table rows "Row store", "Configuration view"; field 1; PENDING LEAD 3 (re-asked, recommended go) | P2a is P2a-1 only. If the lead keeps them, they return as the revision 6 sub-PRs without the runner files. |
| ADV-R5-17 + COR-R5-C8, C11, C12, C15, C16 | applied | field 14 items 5-6 (rollback executes against `ce70eb5`; text equality is a guard only; "Evidence still to be produced" S29-S39); field 17; "UNVERIFIED" list; field 11 (Probe: every probe call on the short connection); field 13 mut-P15 | OFF to OFF, the upsert refusal, NULL `by`, `ts` clock and `REVOKE` are marked UNVERIFIED and given planned run S38 (smaller diff than writing the SQL myself). C16: tick-step and start-up probes use the separate short connection. |
| COR-R5-C1 | applied | field 7 (stored state: "S3 ... plus S8") | |
| COR-R5-C2 | applied | field 11 (Probe: "A direct SQL reset writes no audit row (S10)" now says the model has no audit tables; UNVERIFIED until the migration run) | the sentence in the ticket says S10 shows the database-side log only. |
| COR-R5-C3 | applied | field 5, header; "UNVERIFIED" list | no "(verified)" on a PR50 half. The gate fail-closed claim left with the gate; the core half (`postgres.py:444-451`) is verified, the PR50 `SwitchChanged` and `_label` cites I did read with `git show 748849c:`. |
| COR-R5-C4 | applied | merged with ADV-R5-8 | |
| COR-R5-C5 | applied | field 9 (ACCEPTED_CHANGES entry); field 13 mut-G33; field 16 | named test: `tests/test_stop_state_rollback.py::test_old_release_fails_loudly_on_a_guarded_database`; the key format of P3a's dictionary is UNVERIFIED. P3a rev 7 stands. |
| COR-R5-C6 | applied | field 7 ("Label key wiring"); field 13 mut-K1, mut-K2, mut-L13 | `limits.label_key_secret_name`, `_restored_key` pattern, start-up and overlap check, required in pilot and prod, dev random key printed, CLI uses the same resolver. |
| COR-R5-C7 | applied | field 7 (CLI: exit 7 and message "stop NOT durable: the store is busy, retry"); field 12; field 13 mut-L30 | one exit-code row, one CLI test, one mutant. The number 7 was a removed draft code that never shipped. |
| COR-R5-C8 | applied | merged with ADV-R5-17 | |
| COR-R5-C9 | applied | merged with ADV-R5-10 | |
| COR-R5-C10 | applied | merged with ADV-R5-14 | |
| COR-R5-C11 | applied | merged with ADV-R5-17 | |
| COR-R5-C12 | applied | merged with ADV-R5-17 | |
| COR-R5-C13 | applied | field 7 (`clear_kill_switch_if` error mapping); field 12; field 13 mut-ST9 | only the fixed trigger messages and 42704 map to `ResetRefused`; any other 42501 is `reset_failed`; test revokes the grant. |
| COR-R5-C14 | applied | merged with ADV-R5-13 | |
| COR-R5-C15 | applied | merged with ADV-R5-17 | |
| COR-R5-C16 | applied | merged with ADV-R5-17 | |
| COR-R5-C17 | applied | field 7 (CLI cite fix), field 9 (`test_repo_rules.py:296-309`; `test_p7_tick.py:79-87`) | |
| COR-R5-C18 | applied | field 3 (P4d cites by item name and time read) | `P4d.md:80` is moot: the sibling lists were replaced. |
| COR-R5-C19 | applied | field 3 (P3a rev 7 cites by item name) | |
| COR-R5-C20 | applied | field 5 (apexc commit `3d78bc7be`, `MANIFEST-SUMMARY.md` line 15; `153d217` is the older PR snapshot) | I read `MANIFEST-SUMMARY.md` and `MANIFEST.csv` for the sha. |
| COR-R5-C21 | applied | field 7 (CLI: `AuditSink.events(run_id=None)`, stop events carry `run_id="-"`); field 5 (`ledger-seed.md` line 133 corroborates only the 262) | |

## Counts

- Findings: 17 adversarial + 21 correctness = 38 ids. Applied 38 (ADV-R5-9 and ADV-R5-16 narrowed as the resolve says; ADV-R5-2 as a cut). Contested 0. Declined 0. Escalated: the written escalation text stays in `reviews/P2a-round5-resolve.md` for the lead to append to `questions-for-lead.md`.
- Mutants: revision 6 total 190 = 41 + 14 + 82 + 53. Revision 7 total 105, all in P2a-1: G 33, F 9, ST 16, P 15, L 30, K 2 (2 are [catalog] rows, 103 have a behaviour killer). Arithmetic: 190 - 41 (row store 20 + runner/judge 21) - 14 (view) - 53 (gate) = 82; 82 - 8 (REVOKE-on-guard-function, resets primary key, cache ceiling, dry-run first UPDATE, two timeout rows de-duplicated against P4d, two merged re-pointed rows) = 74; 74 + 31 new = 105. The 53, 20 and 14 gate, row-store and view rows travel with their v1.1 rows; they are not deleted. The 21 runner/judge rows go to P1m's decision (UNVERIFIED).
- Pull requests: 4 (P2a-2, P2a-3, P2a-1, P2a-1c) become 1 (P2a-1).
- PENDING LEAD: 11 and 13 answers proposed (yes, no); 3 re-asked (go to v1.1); 10 restated (named external reader as a pilot gate); 26 new (reserve-after-stop owner, P4b1 recommended); 27 new, mine (role-timeout defaults and the migrator's `ALTER ROLE` right); 1, 5, 7 closed or moot by the cuts; others carried.

## Disagreements and things the lead should know

1. ADV-R5-4 wording: the regex belongs on the OFF-to-ON path (stop), not on "reset" (ON to OFF). Applied that way.
2. Consequence of the cut that the resolve did not list: `StopOperator`, `StopBackend` code, `Limits.is_stopped()` and the `source=` argument leave with the gate. `Limits.blocked()` keeps its core shape.
3. The five revision 6 "re-pointed" PR50 rows are no longer re-pointed (their targets are cut or rewritten): 3 are written new, 2 merge into new rows.
4. The probe's dry run changed: the runtime has no `UPDATE`, so the old two-step dry run (S17, S18) no longer applies; the runtime-handle dry run now expects 42501 "permission denied". My design, UNVERIFIED (planned S38).
5. P4d on disk is rev 7 and still says P2a keeps `SELECT, UPDATE`; it needs a text-only rev 8 (field 3). P3a, P4b1, P4c, P4b2 carry stale names or cites (field 3).
6. Existing tests that fail after this revision and revision 6 missed: `tests/test_p7_store.py:153-154`, `tests/contracts/test_store.py:196-203` (field 9 (j), (k)).
7. Residual stated plainly: the role timeouts bound a lock hold by a compromised runtime, they do not remove it.
