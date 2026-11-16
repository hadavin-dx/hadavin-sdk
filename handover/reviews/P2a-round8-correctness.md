# P2a round 8, correctness review (ticket revision 9)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-codebase-details`, read-only, no SQL or tests run, did not open `reviews/`. Every trace UNVERIFIED unless marked read.

Verdict: CLEAN under the old rule: 0 Blocker, 0 Major, 13 Nit. (The adversarial round 8 found Major M1, so the ticket is not clean overall.)

## NIT

- N1: round-cap text (lines 3, 18, 385, 389) contradicts order 16: say max 3 rounds then freeze; two-clean-rounds stays for result review only.
- N2: `lock_timeout` set before the advisory lock (lines 162, 234); core's first statement is `pg_advisory_xact_lock` (migrate.py:314); lock_timeout likely also bounds advisory waits (UNVERIFIED), so a concurrent `migrate` would fail with 55P03 after 2 s; existing `test_two_concurrent_migrate_runs_apply_once` (test_p2_postgres.py:157-170) is not in field 9. Set it after the advisory lock or say intended; add the test.
- N3: "no stop is lost" has an exception at the cap (lines 55, 88, 163): a stop made after the operator's read at N open requests leaves no trace; add one sentence.
- N4: `clear_kill_switch_if` cited as if it exists (lines 92, 420); it is in neither core nor the snapshot.
- N5: ACCEPTED_CHANGES relay (line 115; P3a.md:96): P3a keys by `(object_name, package_id)`; state entries per object, drop UNVERIFIED; comparer only fails differences on OLD relations.
- N6: stale relay cites (lines 25, 28, 30): P4d v1.1 row at P4d.md:301 (WITHDRAWN); P4d is rev 9; P2d mentions at 30, 33, 71, 73, 101, 102, 213; `docs/promoted-controls.md` relay open; P2d.md:213 mentions a "P2a-0 evidence file" P2a no longer has.
- N7: hot-file order incomplete vs P4a, P4d and order 16(3) (line 32): config.py (P4a.md wants P4d-a2-i, P2a-1, P4a-2, P4b1-a), defaults.py (three tickets disagree); P2a-1 merges before P4a-1 (order 16(3)) not stated.
- N8: cites `P1.md` by line number (114, 139); P1.md:23 wants item name "P1m create".
- N9: home of `StopNotPermitted`, `SwitchChanged`, `StopNotConfirmed`, `ProbeInconclusive` not stated; `errors.py` would be a hot file missing from field 9.
- N10: S31 case i cannot show what it claims (after step g the state is OFF with 0 open; line 201 raises HD003); needs another committed open stop first.
- N11: `migrate(` count 26 correct only at ce70eb5; say "re-grep at build".
- N12: field 9 (d) mentions only the exit code of test_review_pr3_round2.py:278-290; line 289 also asserts "stays ON" in stderr; that changes too.
- N13: "seven new v1.1 rows" (line 455) vs 6 new rows in the table plus withdrawn and dropped rows; ambiguous.

## Verified

Mutant classes G 44, F 16, R 19, ST 22, P 21, L 45, K 7 = 174; 159 - 8 + 23 = 174; conditional 171/167; 6 equivalent rows; S29-S42 = 14 steps; 26 `migrate(` call sites; 9 `Limits(` sites; `pilot_cfg` 11 uses. SQL claims against migrate.py, 0001-0003; function and trigger text reads without compile or logic errors; S31 a-k consistent. Code cites in limits.py, models.py, protocol.py, postgres.py, memory.py, app.py, cli.py, agent_loop.py, tick.py, table.py, config.py, tests all matched. Cross-ticket relays by grep (P4d, P4b1, P4c, P4b2, P6b1, P0c, P1).

## Not checked

No SQL run; PostgreSQL 17 and psycopg int typing; whether lock_timeout covers advisory waits; full bodies of P4b1, P4b2, P4c, P6b1, P0c, P2d, P4a, P3a; several test cites; pytest ids in field 13; evidence files beyond headings.
