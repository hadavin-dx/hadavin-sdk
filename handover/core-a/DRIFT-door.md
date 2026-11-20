# Drift report A7: the DOOR area, docs against code (2026-11-20, core-a)

Method: egm-drift-report (read each document, find the code it names, report only differences), done by hand for the
list of claims because the documents are mostly tables of numbers, status codes, names and `file:line` cites. No git, no
test run (only `pytest --collect-only` to count tests). Nothing in `src/`, `tests/`, `/home/user/wt/*` or another lane was edited.

Code read: `src/hadavin_sdk/triggers/{endpoint,server,worker}.py` (414, 394, 1188 lines), `src/hadavin_sdk/testing/crash.py` (316),
`tests/triggers/*`, `n8n/*.json`, and the files the docs cite in `approvals/`, `runtime/`, `store/`, `models.py`, `identity.py`, `cli.py`.

Documents read: `n8n/README-trigger.md` (the only `n8n/*.md`), `handover/core-a/pr/{CHANGELOG-lines,PR-DESCRIPTION,README-n8n-queue-mode,README-trigger-postmerge,SECURITY-door-section}.md`,
`tickets/D-signed-endpoint.md`, `tickets/E-test-helpers.md`, `CRASH-MATRIX.md`, `REPORT.md`, and the module docstrings of the four source files.

## Counts

| | |
|---|---|
| `file:line` cites checked (script: file exists, range in file; then keyword match of the claim against the cited lines, read by eye where it did not match) | about 645 |
| other claims checked by hand (status codes, limits, exit codes, secrets rules, names, loop numbers in the JSON, arithmetic, test counts, evidence-file lines) | about 140 |
| TRUE | about 760 |
| DRIFT found and FIXED in a doc under `handover/core-a/` or `n8n/` | 11 drifts on 27 lines |
| DRIFT in a file this lane may not edit (tests/) | 1 |
| DRIFT in another lane's file (core-b, core-c) | 0 found |
| Known-stale cites that the document itself already disclaims (not counted above) | about 110 in the D ticket, 8 in the E ticket |

## Drifts

| # | Claim | Where | Truth | Action |
|---|---|---|---|---|
| 1 | `MAX_WAITING, worker.py:110, 329-331` | `n8n/README-trigger.md:680`; `pr/README-trigger-postmerge.md:91, 109` (the OLD and the NEW block of item 4) | `MAX_WAITING` is at worker.py:112; the check that answers 503 at once is `Runner.start`, worker.py:333-335 | fixed (OLD and NEW block still match the README, checked by script) |
| 2 | 503 from the degraded worker is at `worker.py ~1050` | `n8n/README-trigger.md:682` | `_Degraded` is worker.py:966-1038 (`_serve_degraded` 1060) | fixed |
| 3 | "run 20 is not read yet", "see run 20 when it lands" | `pr/PR-DESCRIPTION.md:54, 56, 68`; `pr/SECURITY-door-section.md:41`; `pr/CHANGELOG-lines.md:21` | run 20 landed: `evidence/mutants-run20.md`, 120 of 120, head 05d727afb | fixed (cites run 20, keeps run 19 as the earlier result) |
| 4 | `tests/triggers/crash_launcher.py:60` for `RESERVES` | `pr/CHANGELOG-lines.md:20`, `pr/PR-DESCRIPTION.md:33` | `RESERVES = hasattr(Limits, "reserve")` is line 59 | fixed |
| 5 | first read `_row` worker.py:339; poll read 351; `_submit` 342; poll loop 348-362; 342-351; 351-353; `_decide` 337 | `CRASH-MATRIX.md:32, 71, 72, 73, 74, 85, 182` | `_decide` 341, first `_row` 343, `_submit` 346, first poll read 355, poll loop 352-366, row found 355-357 | fixed (7 lines; note added that they had moved 2 to 4 lines since d-fix21) |
| 6 | "One more case checks the table itself"; log "83 passed" | `CRASH-MATRIX.md:95` (and `:3`) | `test_t5_crash_matrix.py` now collects 84 tests: 43 PG + 39 memory + `test_the_table_covers_every_wrapped_call_once` + `test_reserves_is_what_the_loop_really_does` (added after the raw log; the log still says 83, true for its time) | fixed (second case named, 83 vs 84 said) |
| 7 | `worker.py` is 1178 lines | `tickets/D-signed-endpoint.md:8, 21, 117, 515` | 1188 lines (`endpoint.py` 414, `server.py` 394, `crash.py` 316 are right) | fixed |
| 8 | `test_d_fix13_single_write.py` "(49 tests)" | `tickets/D-signed-endpoint.md:499` | 50 tests collected | fixed ("49 when written, 50 now") |
| 9 | NUL pinned at "ticket D lines 241 and 293"; kill-test paragraph "line 241" | `REPORT.md:68, 69` | the NUL paragraph is D ticket line 312, the kill-test paragraph line 260 | fixed |
| 10 | `crash_launcher.py was de-duplicated (18 lines)` during run 20 | `evidence/mutants-run20.md:2` | one 6-line paragraph (LIMIT of the seeding) is still there twice: `tests/triggers/crash_launcher.py` lines 18-23 and 24-29 (same checksum) | doc note added; the test file is core-a's, not edited here: owner core-a builder, remove lines 24-29 |
| 11 | `WINDOWS-NOTES.md` W02, W03, W07, W09 cites (not in the assigned document list, spotted on the way) | `WINDOWS-NOTES.md:22, 23, 27` | `serve` is worker.py:845-879 (cited 561-595), `LOOPBACK` 117 (cited 99), `check_bind` 630-648 (cited 381-398), SIGBREAK stand-in test at test_worker.py:1167-1168 (cited 1159-1160), IPv6 test at test_worker.py:885 (cited 879) | NOT fixed (outside the list); owner core-a, find by symbol |

Drifts in other lanes' files: none found. The cites that point into core-b and core-c files (`agent_loop.py:208-213, 335-349, 388-393, 396-398`,
`store/memory.py:31, 52, 58, 64`, `audit/local_dir.py:30, 82`, `llm/fake.py:27`, `limits.py:17-30`, `tick.py:38, 100-109, 112-119`, `models.py:60-99`,
`identity.py:13`, `hmac_v0.py:19, 47`, `backends/table.py:40`) were opened and are current.

Disclaimed, not rewritten (the document already says its numbers are old and tells the reader to find by name):
- `tickets/D-signed-endpoint.md`: the cites into worker.py, server.py, endpoint.py and crash.py in sections 2 and 5 to 10b (header WARNING, R2-2); section 3 is frozen at main 51c9fc4fb by its own text.
- `tickets/E-test-helpers.md`: the numeric cites into crash.py (for example `crash.py:75-76` is now 77-78), note at line 215 (R2-17).
- `REPORT.md` is a dated log, newest first: its counts are those of the hour they were written. Differences to today: n8n template tests 92 (now 93), d-fix13 49 tests (now 50), d-fix14 "8 more cases" (now 6 collected). Not edited.

## Claims checked and TRUE (the ones that matter)

Status codes 200, 202, 400, 401, 404, 405, 409, 413, 414, 431, 503 and their bodies, headers (`Allow`, `Retry-After: 1`), the check order; secret rules (32 characters, at most 2 per sender, at most 8 senders, whitespace, zero-width, control, lone surrogate, shared value);
300 second window and 12-digit timestamp; key rule (1 to 128, `A-Za-z0-9._:-`); run id (`run-` + 32 hex of tenant NUL sender NUL key); 64 KiB request line, 16384 / 16382 header cap, 256 connections, 30 second deadline, 128 waiting, `ack_wait_s` 5 and 30, `max_running` 64, `max_body_bytes` 2097152 ceiling;
exit codes 0, 2, 3; port 8081; loopback and `--allow-non-loopback`; IPv6 refused; memory store refused outside demo (exit 2, message text); SIGTERM and SIGBREAK; 600 second tick check; health body and 503;
the 14 `RunState` values, `OPEN_STATES`, the tick `STUCK` reasons incl. `approval_missing`; `stuck_after_s` formula and the defaults 60 and 3 (`backends/table.py:40`); arithmetic of the loop (3150 s, 52 min, 87 min, 6300 s, 105 min, 2220 / 2280 s, 17 / 32 / 53 checks);
n8n JSON: wait 70 s, 45 rounds, 45 checks, timeout 45000, Set nodes 3.4, Crypto 2, header names, node names; `CrashPoints` rules (137, marker, gate, 20 tries at 20 ms, nth limits); crash matrix numbers (43, 39, 171, 346; raw log tails 83 and 346; 4 + 33 + 5 + r4); fuzz 4 x 300; 26 drifts in DRIFT-REPORT.md; WINDOWS-NOTES 16 rows;
n8n evidence-4 lines 46 to 51, 58 to 60, 66, 78, 91, 93, 105, 124, and the timings 0.18 s, 0.047 s, 73.7 and 75.6 s; the OLD blocks of README-trigger-postmerge items 1 to 4 against the README (lines 51, 671, 673, 803).

## Could not verify

- Every `integ:` cite (core-b and the merged tree `/home/user/wt/integ`, which this task forbids touching): `defaults.py:278-290`, `config.py:395-425, 709-717`, `agent_loop.py:388-392, 396-404, 567`, `CHANGELOG.md:8, 13`; also "default 4 / 10 / 1 to 1000" of `TriggerSettings`. Owner core-b.
- This branch has no `Config.triggers` and no `App.trigger_secret` (true, checked), so everything about the merged tree is read from the docs only.
- n8n behaviour: lines of `lead-evidence-n8n-1.md`, `evidence-n8n-2.md`, `evidence-n8n-3.md` (only record 4 was spot-checked); queue mode, Cloud, 520 to 524, redirects, TLS, a real proxy, a real Windows run.
- "A second Ctrl-C aborts the wait" (README stated limit 11) and the other signal behaviour: code read, not run.
- Pass and skip counts (1374 passed, 12366 passed, 1399 passed and so on), the 120 of 120 mutants, and the BATCH logs: read from their summary files only; nothing re-run. Commit hashes (5a8c83fd3, 05d727afb, 02226ce0, 6e61005db): no git.
- The D ticket's frozen section 3 cites into other lanes' files at main 51c9fc4fb: five spot-checked (STUCK table 112-119, identity 10-15, hmac_v0 19, `models.py:99`, `identity.py:13`), the rest not.
