# v10 changes: every v9 finding -> fix -> test that fails on the old design (2026-11-16 UTC)

Failures and gaps first:
- **Nothing was run except read-only programs** (cite checker, import graph, snippet parser, banned-string counter). No pytest, ruff, bandit, Postgres, vendor call or spend. "Test that fails on the old design" means the test is SPECIFIED in `CORE-PR-HANDOFF-v10.md` section 7.2 and would fail on the v9 design or the current tree; none of them exists yet, so none has been shown to fail.
- **Instruction conflict (0006).** My brief says the lead vetoed migration 0006; `ORDERS.md` Q34 says "no veto, keep it, applied only on an owner yes". v10 puts no migration in S-2a or S-2b and keeps the check as stand-alone unscheduled PR DB-1 (section 5.6). Open question L1 for the lead. Exposure without DB-1: a holder of the runtime database role can write a negative or not-a-number total directly.
- Postgres timeouts, the NaN check in DB-1 and all vendor billing facts are UNVERIFIED (section 5.9 and E0-DB-1 / E0-S2-3 name the test that settles each).
- The over-breadth of the runtime role (SELECT, INSERT, UPDATE on the spend tables, `migrate.py:53-54`) is real and is not removed in this step. v9's "none" is corrected; the partial fix is the DB-1 check plus the code-level refusal.
- This file's check counts: cites 155 (spend file) and 76 (other-tracks file), 0 missing or out of range (`raw-cite-check-v10*.txt`); 25 and 11 lines marked CHECK are the anchor-word heuristic, not failures. Python fences 1, syntax errors 0. Banned strings 0. Import cycles today 1 (run time) and 3 (with type-checking imports) under counting A, 0 new from the planned table; under counting B (parent packages, `--parents`) the existing llm cycle grows by `llm`, `llm.fake`, `guard.judge`, still 0 new from the planned table (raw files `raw-import-graph-v10*.txt`).

## A. Readiness review of v9 (2 blockers, 9 majors, 10 minors)

| Finding | Fix in v10 (section) | Test that fails on the old design (section 7.2) |
|---|---|---|
| B1 edited test runs on the fake kind, never reaches the new code | A named `NetworkStub` and fixture; the edited test changes to use it (5.3) | E0-S2-4: one request per attempt, retry storm books 3x worst; fails on v9 and on today's tree, which have no gate |
| B2 inputs for E0-S2-7 / E0-S2-3 do not exist; "old" undefined | Synthetic set written by the S-2a builder, with "old" defined per row (7.2) | E0-S2-7, E0-S2-3 |
| M1 build order | window, then limits, then gate, then llm and detectors; signatures given (5.3) | E0-S2-1 (app and CLI build tests) |
| M2 injected `llm=` skips the gate | Fail closed with a stated rule (5.3, 5.5) | E0-S2-4 |
| M3 undefined `spend` parameter | Fields split between S-1 and S-2 (5.1, 5.3) | E0-S1-2, E0-S2-1 |
| M4 S-1 versus S-2 gate contract | Reserver protocol; no-op rule stated per PR (5.3) | E0-S1-6, E0-S2-4 |
| M5 no card at run start | Run-start refusal goes through `_wall_stop` (5.5) | E0-S2-7 |
| M6 answer shape | `Answer.tokens` shape pinned (5.3, 5.4) | E0-S2-4 |
| M7 table in a folder deleted at hand-over | Planned-edge table moved into the document (8.1) | E0-S1-5 |
| M8 no owners or briefs | Owners and 60-minute briefs per PR (7.1) | n/a (document content) |
| M9 other-tracks evidence gaps | New rows E0-O2, E0-O3, E0-O12; missing files and owners named (other-tracks file) | E0-O* rows |
| Minors 1-10 | Rounding rule, `Config.spend` default, route price basis, other `except ProviderError` sites, complete commands via `gate4.sh`, datetime rule, test named E0-S2-4, "no migration" wording, money-type owner and review date (lead/D5, 2026-12-31), census function names (6) | E0-S1-3, E0-S1-4, E0-S1-6, E0-S2-8 |

## B. Security review of v9 (9 majors, 8 minors)

| Finding | Fix in v10 | Test that fails on the old design |
|---|---|---|
| M1 hostile numbers lower totals | Prices and tokens must be finite and not below zero; implausible counts are kept at the worst case; store refuses non-finite and totals below zero (5.4) | E0-S2-2, E0-S2-4 |
| M2 zero usage becomes a small booking | Zero or missing usage means keep (5.4) | E0-S2-4 |
| M3 failed settle triggers a second paid request | `settle` never raises; errors logged and the worst case kept (5.3 pseudocode) | E0-S2-4 (settle raises `OSError`: exactly one request) |
| M4 false timeout claim | True bound stated (about 4T per add_spend, about 8T per refused reserve); `statement_timeout`, `lock_timeout`, `tcp_user_timeout` specified, UNVERIFIED (5.5b, 5.6) | E0-S2-3, E0-S2b-1 |
| M5 missing scope does nothing | Fail closed: `scope_missing`, `call_context_missing`; ProcessCap for CLI paths (5.3, 5.8) | E0-S2-4, E0-S2-8 |
| M6 false "no property depends on vendor facts" | Dependency table, one property per vendor fact with the largest error (5.9) | E0-S2-6 (guard stays UNVERIFIED) |
| M7 guardrail skips the window check | Guardrail metered as a paid kind, not keyed on the llm kind (5.7) | E0-S2-4, census C3 |
| M8 abandoned replay thread keeps paying | Abandoned flag and budget multiplied by attempts (5.8) | E0-S2-4 |
| M9 runtime role over-breadth | Corrected text; DB-1 check; repair path (5.6) | E0-DB-1 |
| N1 non-UTC clock shifts window | Converted to UTC once in `build_window` (5.2) | E0-S1-3 |
| N2 reserve at the limit (> versus >=) | One comparison rule (5.3) | E0-S2-3 |
| N3 kill switch not consulted per attempt | Consulted per attempt (5.3) | E0-S2-4 |
| N4 start-up check not for all kinds | Census C1 asserts it (6) | E0-S1-6 |
| N5 `limits_unavailable` relies on best-effort card | Stated plainly (5.5) | E0-S2-7 |
| N6 memory store parity for NaN | Same refusal in both stores (5.4) | E0-S2-2 |
| N7 lost ack after commit | Stated: safe over-count (5.3) | E0-S2-3 |
| N8 inputs missing, "0 new abstains" conflicts with call_too_large | Synthetic set; ceiling both rates (7.2) | E0-S2-7 |

Note: N2 to N8 are mapped from my condensed copy of the review, which truncates some N lines; if a mapping is wrong the lead should say so.

## C. Citation review of v9

| Finding | Fix | Check |
|---|---|---|
| C1 `chain.py:171` | Worded as "planned change"; `:171` (value stored) and `:360` (real call) cited | cite checker, 0 missing |
| C2 "nine places" for `Limits(` | 7 test sites listed (F16) | cite checker |
| C3 104 versus 113 count | Count now produced by script (155 and 76) | `raw-cite-check-v10*.txt` |
| C4 import counting not stated | Counting A and B stated and both run (8.1) | `raw-import-graph-v10*.txt` |
| 4 loose ranges | `registry.py:33-36`, `postgres.py:192-197`, `migrate.py:87-90`, bare file names given paths | cite checker |
| Four cites I found wrong myself | `retry.py:23`, `common.py:184-189`, `app.py:166-169`, `agent_loop.py:432-433` | opened by hand, then the checker |

## D. Lead answers Q33 and Q34

- All 7 other-track PRs carried unchanged (except the corrections above). PR-2 NEEDED-CHECK = UNVERIFIED; the row "needs an independent per-PR NEEDED-CHECK (dated evidence) before build" added (O-6). No verdicts guessed.
