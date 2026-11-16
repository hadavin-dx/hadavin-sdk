# v6-CHANGES: finding id | fixed where in CORE-PR-HANDOFF-v6.md | or why not

Nothing was run (design only; the only commands were file reads and one banned-word count). "Fixed" means the design now specifies it; it is verified only when the E0 evidence batch and the lead's EGM review exist. Section numbers are v6's. Every row is fixed; none is deferred, except where the Note says "not fixed" with the reason.

## Security review of v5 (`review-handoff-v5-security.md`)
| Id | Fixed where | Note |
|---|---|---|
| 1 blocker: release after a possibly billed attempt | 4.1 per-attempt reservation, booking table; D23; 4.2 `_retry` closure and `CallBook` | test 1 and 2 of 4.2; bound is N attempts in flight |
| 2 gate checks only that a scope exists | 4.2: reservation made inside `NetworkLLM._retry`, no gate means `unmetered` refusal | test 3 of 4.2; negative tests 5.6 |
| 3 finish_spend and add_cost separate writes | 4.1 `finish_spend` updates `runs.cost_usd` in the same transaction; `add_cost` call removed | test 7 of 4.2 |
| 4 run cap ignores open reservations | 4.1 run total is the sum over `spend_op` for the run, inside the reserve transaction; D14 | test 6 of 4.2, E0-3 |
| 5 under-reported cost booked as truth; settle could raise | 4.1 `settle` floor, cost 0 means keep, clamp at `MAX_SPEND_OP_USD`, never raises the four listed errors | test 5 of 4.2 |
| 6 runtime could lower a total through UPDATE grants | 4.1 totals from append-only `spend_op`; `spend`, `spend_month` shrunk to SELECT; trigger; section 5 table and "what the runtime can still do" | second-role test in E0-3. Not fully closed: the runtime can undo its own reservation once (stated; option and trigger in 4.1) |
| 7 D5 not non-blocking | Section 0, D5 (needed before M2a, OWNER-OPEN, safe default), section 6 row 3; sNaN order in 4.1 `spend_amount` | owner answer still open |
| 8 orphan handling thin; res_id; repeated id | 4.1 orphan view, `correct`, bulk `--older-than`, index, `res_id` rule, repeated-id compare; D15 availability bound | CLI spec in 4.3 |
| 9 redaction contract | 4.7 private `_Mapping` holder, `__reduce__` raises, copy returns empty, `Valid.restore`, schema guard, echo-canary test | |
| 10 over-claims | 4.6 `anchor_retention_probed`, "configured" key location; 4.1 caught-exception list; 4.4 notice claim reworded (delivery, per-process set); section 0 item 7 wording; `window_owner` validator in 4.5 and 5.8 | |
| 11 UTC midnight is 05:30 IST | D1 and 4.5 (last allowed moment 05:29:59 IST next day) | |
| 12 spend_op retention and index | 4.1 indexes, D24 | |
| 13 G4 "withheld" wording | 4.9 "not shown", display-filter note | |
| U1 Bedrock status | 4.1 `refused(exc)` kind hook, Bedrock reads `ResponseMetadata` | other kinds' constructors not read (section 9) |
| U2 cache, thinking pricing | F19 (no kind sends them; grep) | grep only |
| U3 migration number | F21 (0006 checked against the file list) | |
| Missing negative tests (9) | Section 5 negative tests; 4.2 tests 1 to 9; 4.5 tests; E0-3, E0-11 | transient+refused, raw client, add_cost failure, parallel run cap, cost 0, second role, repeated id, midnight, thread, e-mail owner |

## Readiness review of v5 (`review-handoff-v5-readiness.md`)
| Id | Fixed where | Note |
|---|---|---|
| B1 interfaces unspecified | 4.1 and 4.2: signatures, home files, `Deps.gate`, `ALLOWED`, `build_llm`, closure in `_retry` | gemini and openai-compatible constructors not read (section 9) |
| M1 Postgres plumbing | 4.1 `GRANTS` entry, `_APPEND`, file `0006_spend_op.sql`, guard forms | check_grants run is E0-1 |
| M2 spend_op shape | 4.1 DDL with `how`, `run_id`, `actual_usd`, meaning of `usd` on a final row | |
| M3 M2b depends on M2a | Section 6 | |
| M4 silent stop at the cap | 4.4 `_limits_stop` goes through `_wall_stop`; end states table | |
| M5 handler placement | 4.4 `handle` split, one handler for three sites | |
| M6 k1b double booking | D25, 4.2 table, k1b untouched | |
| M7 CLI | 4.3 choices, `--by` rule, options, exit codes, memory-store text | |
| M8 Limits signature, clock | 4.5 | |
| M9 Store protocol break | 4.1 (protocol), section 6 row 3, E0-1 | |
| M10 E0-8 scope | 4.5 and section 7 | |
| N1 YAML | 4.5 `date | Literal["none"] | None`, E0-11 | |
| N2 name clash, import direction | 4.1 `reserve_estimate`; `llm` never imports `k1b` | |
| N3 POLICY_STOP_REASONS owner | 4.4, section 8: M2c | |

## Citation check of v5 (`evidence-handoff-v5/citation-check-v5.md`)
| Row | Fixed where | Note |
|---|---|---|
| 1 `config.py:393-394` (wrong; real lines 395-396) | 4.8 now cites `config.py:395-396` | read in source this pass |
| 2 "37 probes" (wrong; 36) | 4.9: 36 probes | per the check's own count |
| 3 `migrations/0001_core.sql:87-92` (partly: `store/` missing) | F4 and 4.1 cite `src/hadavin_sdk/store/migrations/0001_core.sql` | path only |
| 4 `migrations/0003_approvals_tick.sql:15-20` (partly) | F4 cites `src/hadavin_sdk/store/migrations/0003_approvals_tick.sql` | path only |
| 5 `common.py:195` (partly: docstring) | F6 and 4.2 cite the class and docstring as `common.py:193-196` (opened: lines 193-196 are the `NetworkLLM` docstring) | parse code itself cited at `_retry` `:233-241` |
| 6 `fake.py:29` (partly: method not class) | F10: class `FakeLLM` at `fake.py:21`, `chat` at `:29` | |
| 7 `common.py:86-100` decode (partly) | 4.1 now says `turns` is `common.py:86-100` and the `decode("utf-8", "replace")` is at line 92 (opened); `evals.py:63` cited separately | |
