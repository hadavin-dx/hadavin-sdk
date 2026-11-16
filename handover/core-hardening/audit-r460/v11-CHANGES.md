# v11 changes: every v10 finding -> fix -> test -> does it fail on the old design (2026-11-16 UTC, 20:xx IST)

## Failures and gaps first
- **Nothing was run except read-only programs** (cite checker, import-graph programs, snippet parser, banned-string counter, the gate-script comparison). No pytest, ruff, bandit, Postgres, vendor call or spend. "Test that fails on the old design" therefore means: the test is SPECIFIED in `CORE-PR-HANDOFF-v11.md` section 7.2, and the old design is v10 (or today's tree where the new function does not exist). For new functions (`CallGate`, `owner_gates`, `ScopedDetector`) a test cannot "fail on old code" by assertion: it fails because the name is missing, which proves nothing; the proof there is the hand-made mutants of E0-S2-8 (`mutants.py`, written by S-2a, not run).
- **`gate4.sh` has never run.** It is syntax-checked (`raw-gate4-syntax.txt`) and compared with `ci.yml` (`raw-gate4-vs-ci.txt`, 5 of 5 commands match). CI also sets the Postgres and vault test settings; the script does not, so database tests skip on a laptop. The lead's CI run is the real gate.
- **Import-graph counts disagree between programs.** Counting B for the group around package `llm`: my program says 7, the independent script says 9 today and 10 planned. I used the independent numbers in section 8.1 and did not reconcile mine. Counting A: 0 new cycles in both.
- **"Seven PRs" cannot be reproduced**; there are nine ids. Not resolved by me (needs-lead, question L5). Nothing dropped.
- **No EGM skill was run by me** (not invokable from this session); the lead runs the EGM reviews. No commit exists.
- Postgres 14 for `'Infinity'::numeric`, the vendor error shapes, the guardrail client's retry layer, `ScopedDetector` and `reconnect` on a real drop: all UNVERIFIED (section 10).
- Checker results on the v11 files: cites 174 (spend) and 79 (other-tracks), 0 missing or out of range (`raw-cite-check-v11.txt`, `raw-cite-check-v11-other.txt`; the CHECK lines are the anchor-word heuristic, not failures, and the checker does not check meaning); Python fences 1, syntax errors 0 (`raw-snippets-v11.txt`); banned strings 0 (`raw-banned-v11.txt`); new import cycles 0 under counting A, and under B the llm group grows from 9 to 10 (`raw-cycles-v11-independent-script.txt`, `raw-merge-probe-v11.txt`).

## A. Security review of v10 (5 majors, 8 minors)

| Finding | Fix in v11 (section of `CORE-PR-HANDOFF-v11.md`) | Test (7.2) | Fails on old design? |
|---|---|---|---|
| M1 guardrail metered as one request, client can send two (`guard/bedrock_guardrail.py:36`) | The guardrail check is one request per check: the client's own retries are set to one and the gate's retry owns repeats; each attempt reserved (5.7) | E0-S2-4 (guardrail attempts) | Yes on v10 (one reservation, two requests); mutant removing the retry setting |
| M2 missing gate fails open | Paid kinds' constructors require a gate or an explicit `unmetered` flag (fake and test kinds only); `make()` with no gate raises `ConfigError` (5.3 constructor rule) | E0-S1-7 | Yes: v10 default `gate=None` runs unmetered |
| M3 `SpendRefused` unhandled in the approval-summary path | `injection_check(spend="flag"/"raise")`; summary path turns the refusal into a flagged verdict; `SpendRefused` moved to leaf `errors.py`, not a `ProviderError` (5.5, 9) | E0-S2-7, E0-S2-4 | Yes on v10 (raises into approval path) |
| M4 429 storm books 3x worst case; wrong key empties the day | Release on definite client errors (400, 401, 403, 404, 422) and on gate refusal; keep after failures a vendor may bill; marked UNVERIFIED (5.3 outcome table) | E0-S2-4 (retry cases) | Yes: v10 keeps every sent request |
| M5 runtime role UPDATE grant; 0006 handling | 0006 kept (Q34), own negative test run as the runtime role, held outside `store/migrations/` plus runner gate `owner_gates.py` (`HELD`, `OWNER_YES`); lead's-confirmation gate and L1 removed; DB-1 scheduled as order 4 (5.6, 7.1) | E0-DB-1 | Yes: v10 left DB-1 unscheduled and the runner would apply a file in the folder |
| N1 `MAX_PLAUSIBLE_TOKENS` undefined | `max_plausible_tokens` setting; `clean_tokens` returns ok, missing or high; high books the worse of worst case and estimate and alerts (5.1, 5.3) | E0-S2-4 | Yes (name undefined in v10) |
| N2 vendor row 2 wrong; 5.9 closing sentence unsupported | 5.9 table says which safety property rests on which vendor fact; closing paragraph rewritten; invoice comparison named as the only catch for rows 1-2 | E0-S2-6 | n/a (text); statement narrowed |
| N3 settle failure only logged | Audit row `spend_settle_failed` and alert path (5.3) | E0-S2-4 | Yes |
| N4 NaN in settings reaches `admit` | Finite rule on every spend setting, not only Route and Budget (5.1, 5.4) | E0-S1-2 | Yes |
| N5 `-cli` / `-unattributed` collide with agent ids; cron loops | Ids starting with `-` refused for real agents; `-cli` daily and monthly caps; `ProcessCap` shared total (5.1, 5.8) | E0-S1-6, E0-S2-1 | Yes |
| N6 `spend_totals` read outside a transaction; no reconnect | Read inside a transaction with local timeouts; reconnect rule (5.5b, 5.6) | E0-S2-3 (Postgres, not run) | UNVERIFIED |
| N7 lost settle acknowledgement can over-count | Stated: over-count is the safe direction; kept (5.3) | E0-S2-4 | n/a (statement) |
| N8 D5 default self-granted | Default removed; options A, B, C with plain prices; S-1 waits for the owner's answer (section 1, 7.1, 10) | none (owner decision) | Yes (v10 text shipped nano-dollars silently) |

## B. Readiness review of v10 (6 majors, 6 minors)

| Finding | Fix in v11 | Test | Fails on old? |
|---|---|---|---|
| 1 E0-S2-7 needs `POLICY_STOP_REASONS` not yet built | Constant moved to S-2a (5.5) | E0-S2-7 | Yes (could not pass at the S-2a head) |
| 2 `default_scope` vs `scope_missing` contradict | `unattributed_scope` is separate from `default_scope`; a scopeless paid call is refused `scope_missing`; `unattributed_max_call_usd` defined (5.1, 5.3, 5.5) | E0-S2-4 | Yes |
| 3 0006 treated as conflict | Settled by Q34; scheduled (see M5) | E0-DB-1 | Yes |
| 4 "Seven PRs" vs nine | Counted: nine ids; question L5 to the lead; nothing dropped (9, other-tracks O-0) | none | n/a |
| 5 NEEDED-CHECK has no owner or format | Design added (other-tracks O-6): checker (L6 to the lead), per-PR file, `NEEDED-CHECK v1`, verdicts, pass rule | none (document) | n/a |
| 6 S-1 passes a reserver S-1 lacks | S-1 omits the reserver; S-2a changes the argument (5.3) | E0-S1-6 | Yes |
| 7 `CallCtx` defaults undefined | Defaults written; `booked` rule (5.3) | E0-S2-4 | Yes |
| 8 end-state naming | Table of paths P1, P2, P3 with end states (5.5) | E0-S2-7 | Yes |
| 9 retry-storm wording | Exact outcome lists (fail, fail, success and others) (E0-S2-4) | E0-S2-4 | n/a |
| 10 S-1 split left to builder | Split into two sessions with named content (7.1) | none | n/a |
| 11 gate4.sh "written, not run" | Marked UNTESTED in E0-S1-1 and E0-S2-1 | none | n/a |
| 12 D5 review date | Kept 2026-12-31 | none | n/a |

## C. Independent re-check of v10 (`evidence-handoff-v10-independent/00-TABLE.md`, 10 rows)

| Row | Fix in v11 | Evidence |
|---|---|---|
| 1 gate4.sh not the `ci.yml` commands | Rewritten to the five commands (`ci.yml:79,81,88,94,119`); E0-S1-1 row and other-tracks E0-O1 fixed; CI environment difference stated | `raw-gate4-vs-ci.txt` (5 of 5), `raw-gate4-syntax.txt` |
| 2 and 3 counting-B claim understated (9 today, 16 planned) | 8.1 rewritten with the measured numbers; cause named (`SpendRefused` as `ProviderError` pulled the guard group in); fixed by `errors.py`; result 10, guard group separate | `raw-cycles-v11-independent-script.txt`, `raw-merge-probe-v11.txt` |
| 4 `retry.py` 20-110 | Ranges within 108 lines (`retry.py:83-108` and others) | cite check, 0 out of range |
| 5, 6 resolver artefacts (`agent_loop.py` continuations, `:513`) | Explicit paths added (`runtime/agent_loop.py:318-322`; `guard/redact.py:513`, pattern at 513-519) | `raw-cite-check-v11*.txt` |
| 7 `app.py:160` | `app.py:161` | grep |
| 8 F16 fifth site | `tests/test_p6_detectors.py:186` added | grep |
| 9 `_limits_stop` call at `agent_loop.py:460` | Added (5.5: called at 359, 421, 460) | grep |
| 10 seven vs nine | See B4 | n/a |

## D. Lead's correction Q34 (migration 0006)
Kept; own negative test as the runtime role; applied only on an owner yes; made enforceable (`owner_gates.py`, file held outside the folder the runner globs, `migrate.py:93-94`); lead's-confirmation gate and L1 removed; the extra `usd < 'Infinity'` clause shown to the lead as L7 and in 5.6.

## E. Not changed on purpose
D5 stays OWNER-OPEN. v10 files are untouched. `src/`, `tests/`, `inputs/` untouched.
