# EGM review round 1 of 1: tickets/B-stop-state.md, compared with the BUILT code (egm:egm-review-loop through the Skill tool; direct dispatch; model fable)
When: 2026-11-20 05:43 to 05:50 UTC. Target: full file (191 lines). Reading list: src/hadavin_sdk, tests, notes/builder-B-report.md.
Reviewers: egm:egm-implementation-readiness = completed; egm:egm-codebase-details = completed. Not run: none. Neither reviewer ran anything (reading only; PostgreSQL behaviour is from knowledge).
Round result: NOT CLEAN. Blockers 1, Majors 18, Nits 15. Both say the built source matches the ticket almost word for word; the gaps are in what the ticket GUARANTEES (it claims more than the database enforces) and in its test plan.
Timing note: both reviewers read the tree before the role tests landed (commit 7afdab2), so "no role tests exist" (cb-M9, ir-D2) is already answered by evidence/B-tests-after-fix.txt (218 passed with real logins).
Resolution: ticket section "RESOLUTION of review round 1" (S1 to S12) and code fix round 3 (the LAST allowed try for step B). No round 2.

| id | severity | finding (short) | answer |
|---|---|---|---|
| cb-B1 | Blocker | invariant 1 is false as written: the runtime login can create TEMPORARY tables named kill_switch, kill_switch_stops, kill_switch_clears; its own connection then reads OFF (names are unqualified, pg_temp is searched first) | S1: code fix (schema-qualified reads and writes) plus a stated limit |
| cb-M1 | Major | a runtime role that is a NOINHERIT member of another role holding the old rights can SET ROLE and clear; migrate does not see it | S2: code fix (database-wide "who else can clear" check) |
| cb-M2 / ir-8 | Major | role difference and membership are only checked inside one migrate call; --reset-role naming the old runtime role passes; a role never named again keeps UPDATE on kill_switch | S2 |
| cb-M3 | Major | "audit row first" is enforced by the command, not by the database: the reset login can clear by hand with no audit row | S3: stated limit in ticket, SECURITY, runbook |
| cb-M4 / ir-10 | Major | "the reset role cannot stop" is wrong: it holds UPDATE on kill_switch and can set the old flag ON | S4: wording; harmless direction |
| cb-M5 | Major | "a stop committed during the reset stays ON" is false between the audit intent and the clear statement's snapshot | S5: wording in code comments, protocol docstring, runbook, ticket |
| cb-M6 / ir-5 | Major | two mutants have no test that can kill them (ON CONFLICT removed; not one transaction) | S6 |
| cb-M7 | Major | a reset with the kill_switch row missing reports success (exit 0, audit "off") while the state still reads ON | S7: code fix |
| cb-M8 / ir-2 | Major | owner TRUNCATE fails on the foreign key before the trigger; owner UPDATE and DELETE need existing rows | S8: ticket text; the landed tests already use TRUNCATE ... CASCADE |
| cb-M9 / ir-D2 | Major | role tests, unit tests, mutants and evidence were not in the tree | landed since (7afdab2); tests/test_stop_state_unit.py still missing: S9 |
| cb-M10 / ir-D3 | Major | CHANGELOG lacked "stop all runtime processes first" and "in ONE command"; rollback steps nowhere | first two fixed in 7cdecb9; rollback: S10 |
| ir-1 | Major | the mutation runner gives its child no database DSN, so the ordered evidence command cannot kill the PostgreSQL mutants | S6: the mutants run with --hand (already built that way) |
| ir-3 | Major | case E7 (apply 0001 to 0005, set the flag, apply 0006) cannot be done through migrate() | S8 |
| ir-4 | Major | config set-up for N3, E10 and the runtime-DSN reset is left to the test writer | S8: the landed tests show the set-up; named in the ticket |
| ir-6 | Major | six items are specified only as "from the branch" | S11 |
| ir-7 | Major | no phases, no owner for edits to existing tests | S11 |
| cb-N1 | Nit | stop rows carry client-chosen ts and by: a backdated or infinite ts mislabels or breaks the read (fails closed) | S12: code fix (database clock, finite check) |
| cb-N2 to N9, ir-9 to ir-14 | Nit | stale line numbers, stale builder note, pinned SECURITY sentence differs, open questions read as undecided, placeholder in the rollback text, MAINTAIN right on PostgreSQL 17 not checked, misleading message for an ungranted reset login | S12 |
