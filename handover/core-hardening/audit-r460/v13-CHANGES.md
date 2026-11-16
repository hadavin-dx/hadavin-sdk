# v13 changes: each finding of the two v12 reviews and the three citation findings

Written 2026-11-16 (UTC; IST is UTC+5:30). Files: `CORE-PR-HANDOFF-v13.md` ("main"), `CORE-PR-HANDOFF-v13-other-tracks.md` ("other"), raw outputs in `evidence-handoff-v13/`. Section numbers are those of the main file. Nothing here is "verified" except where a raw file is named. Postgres was run on local version 16.15 (the CI version is 17.10, not run). No unit test, `ruff`, `bandit` or `gate4.sh` was run. The EGM skills were not invoked by me.

## Plain statement for the lead (answer Q34, premise is wrong for one write shape)
Q34 says keep the database rule `CHECK (usd >= 0)`. That is right for the rule, but the current write of `add_spend` is `INSERT ... ON CONFLICT DO UPDATE SET usd = spend.usd + EXCLUDED.usd`. Postgres tests a `CHECK` on the proposed new row before it decides there is a conflict. A negative amount (a give-back or a settle below the reserve) therefore fails with error 23514, even though the stored total would stay above 0. Run on 16.15: `raw-pg-b1-v13.txt`. Fix: for a negative amount use `UPDATE ... SET usd = usd + %s ... RETURNING` (the check then sees the resulting total), a missing row raises `LookupError`, a check violation maps to `ValueError`. Test that fails on the old shape: E0-S2-2 and the prototype run `raw-pg-real-code-v13.txt` (47 of 47 pass on the new shape; the old shape fails case B1).

## Security review of v12 (1 blocker, 5 majors, 6 minors)
| Id | What changed | Where | Test that fails on the old design |
|---|---|---|---|
| B1 | Write shape above; Q34 premise stated plainly | 0, 5.4 item 4, 5.6 | E0-S2-2 negative-delta case on Postgres; `raw-pg-b1-v13.txt` (old shape fails 23514) |
| M1 | DB-2 adds a trigger that refuses any change of the key columns (error 42501); lowering is recorded in a log with a `period` column and an index. **Open on purpose:** many small lowerings are not stopped (the runtime role keeps `UPDATE`); L-2 (separate writer role) and L8 say so | 5.6 items 1 and 6, L8 | `raw-pg-m1-v13.txt` (key rewrite without trigger: log rows 0; with trigger: refused) |
| M2 | `qualify` calls the detector with `spend="raise"`, so a refusal cannot count as a pass | 5.5 | a test in 5.5 (qualify with a refusing detector must fail the gate); the E0 row for it was not checked for exact wording |
| M3 | The GRANTS entry is not in DB-1. It goes in the lead's move PR, with the held file. Reason: the alternative (teach `check_grants` about held files) widens a safety check. Held SQL uses `CREATE OR REPLACE FUNCTION` | 5.6 item 1, 7.1 | E0-DB-2: the v12 state (entry merged, SQL held) fails `check_grants`; `raw-pg-m3-v13.txt`, `raw-pg-real-code-v13.txt` |
| M4 | `CallGate(..., window_only=True)` is the only way to have no reserver; any other gate without a reserver is a `ConfigError`; census C7 | 5.3, 6 | E0-S2-8 mutants (`gate` default of `None` again) and census C7 |
| M5 | File 2 split into DB-2 with its own lead yes (L9), not presented as part of Q34; cost measured on 16.15: +0.28 ms per lowering, about 167 bytes per record, a failing log insert fails the UPDATE (closed) | 5.6, 7.1, L9 | `raw-pg-m3-v13.txt`, `pg_experiment_v13.sh` |
| m1 | New code `guardrail_text_too_long` with its own text; S-1 guardrail admits with worst 0 | 5.3, 5.5, 5.7 | E0-S2-4 (the new code) |
| m2 | Per-requester unattributed scope `-unattributed:<requester>` | 5.5 | E0-S2-4 (unattributed scope case) |
| m3 | `studio_daily_usd`, `studio_monthly_usd`, price floor `PRICE_FLOOR_USD_PER_MTOK = 0.01` | 5.1 | E0-S1-2 |
| m4 | Canary list adds `guard/injection.py:92-97` | E0-S2-9 | canary test |
| m5 | `ev is not None and ev.is_set()` with a mutant | 5.3 admit (b), E0-S2-8 | mutant |
| m6 | `status_of` written as PROPOSED; openai_compat second-group refusal stated and tested; Decimal vs "money is integers" stated under D5 | 5.3, 1 | E0-S2-4 |

## Readiness review of v12 (1 blocker, 6 majors, 8 minors)
| Id | What changed | Where |
|---|---|---|
| B1 | Same cause as security M3: no GRANTS entry in DB-1; DB-1 is one file, applied only on the owner's yes | 5.6, 7.1, E0-DB-1 |
| M1 | Main-call handler test uses a clock that flips between the pre-check and the call (two-clock test) and a "handler removed" mutant | 5.2b, E0-S1-3 |
| M2 | Tests that build kinds through `make("llm", ...)` (14 lines in 6 files by my grep G4) use `tests/spend_support.py::test_gate()`, not `unmetered=True` | 5.1 item 7 |
| M3 | G-3 retired; D5 non-blocking; option A assumed; what changes for B and C and for merge order is written | 1, L4, D5 paragraph, 7.1 |
| M4 | E0-S2-4 codes changed to `call_retry_budget`; cases added | 7.2 |
| M5 | Hot-file column complete for H-0 and H-1; `extract.py` correction | 7.1 |
| M6 | Helper signatures block (`estimate_tokens`, `worst_case_usd`, `cost_of`, `clean_tokens`, `definite_client_error`, `SpendWindow(end or None, clock)`, `Limits` methods) | 5.3 |
| m1 | Only files that exist are named; scripts re-run (`raw-counts-v13.txt`: 34 names, 0 missing) | 8 |
| m2 | E0-S1-3 labels (a) to (d) follow the 5.2b table order | 7.2 |
| m3 | Test seam: the gate is required only when the injected object is a `NetworkLLM` | 5.3 |
| m4 | "any environment other than prod and pilot"; the config literal stays `dev` until H-0 (H-0 renames it in the new spend tests) | 1, 5.6, other |
| m5 | Expected result for `tests/test_s5_runtime.py:114-119` with no card hook | 5.3 |
| m6 | The fixture reports usage, so `sum(settles) == Reply.cost_usd` | E0-S2-4 |
| m7 | L4 unbundled; L5 offers "confirm all nine proceed"; L6 states CANNOT-DECIDE handling (earlier probe evidence accepted); L7 silence rule with date 2026-11-30; new L9 | 10 |
| m8 | `held_dir` keyword on `migrate()`; pass rule for the wheel listing | 5.6 |

## Citation check of v12 (`evidence-handoff-v12-independent/00-SUMMARY.md`)
| Id | What changed |
|---|---|
| C1 | Section 8 names only files that exist in `evidence-handoff-v13/`; the scripts were re-run there. Four v9 grep files that v12 named but did not carry were re-run as G12 to G16 in `raw-greps-v13.txt`. Check: `raw-counts-v13.txt`. Section 8 now says what the cite checks show: ranges exist; 70 of 291 rows of my own second program have no anchor match and were not settled by hand (v12's independent check did that by hand) |
| C2 | `status_of` is a proposed hook; `retryable()` reads the code at `llm/bedrock.py:104` and `anthropic.py:67`; no `status_of` in `src` (grep G9) |
| C3 | "38 test hits" withdrawn. Method: G1 and G1b, test lines with `build(` and `llm`: 19 lines, 18 without a `.pyc` match. Whether any passes a `NetworkLLM` was not checked |
| C4 | The planned cycle group of 10 was recomputed with the independent script: today `[9, 4, 3, 3, 2, 2]`, planned `[10, 4, 3, 3, 2, 2]` (`raw-cycles-v13-independent-script.txt`, `raw-merge-probe-v13.txt`). My own `--parents` program says 7; not reconciled |

## Not changed (carried)
The nine other-track PRs (PR-2, R, K1, A1, G-W, G, H-0, H-1, H-2) are carried in content unchanged in the other-tracks file; only evidence names, the merge order (14 ids with the five spend ids), and the planned-names note changed. `run.py` stays out of every PR. No suppressions are planned.
