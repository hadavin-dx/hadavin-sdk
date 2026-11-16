Status: resolved (revision 4 applied to the ticket text; not yet re-reviewed)

# P4a BN-17/18/19 revision 3, plan review round 3: resolve

**Target:** `handover/tickets/P4a.md` lines 606-710 after the edit (BN-17, BN-18, BN-19; were 606-702) and `handover/tickets/P4b1.md` lines 397 and 531 (BN-35).
**Findings:** `reviews/P4a/round3-design.md` (egm-design, 0 Blockers, 4 Majors N-1 to N-4, 7 Nits N-5 to N-11) and `reviews/P4a/round3-codebase.md` (egm-codebase-details, 0 Blockers, 2 Majors M1 and M2, 5 Nits N1 to N5). Round 2 resolve (`round2-resolve.md`) re-read for context.
**Lead orders applied:** 178 (BN-18 narrowed to the place where the llm backend is built; migrate, audit verify, the kill-switch commands and tick keep working in pilot and prod), 181 item 2 (`forbid_skips` keyword named for FB-T6b's Postgres half), R449 (stage names). Money path: no round cap.
**Resolver:** egm-resolve method, headless (the brief said no questions; every PROPOSE FIX is applied as revision 4). 2026-11-09 07:54 UTC (13:24 IST, from `date -u`).
**Code facts:** checked only by reading the snapshots `/home/user/build/snap/78-4a0976f` ("78"), `/home/user/build/snap/79-8cc2021` ("79") and, for the manifest only, `/home/user/build/snap/P3a-2-2b0941b`. Nothing was run: no tests, no mutants, no guard.

## Counts

| | Blocker | Major | Nit | total |
|---|---|---|---|---|
| raw findings (design + codebase) | 0 | 6 (4 + 2) | 12 (7 + 5) | 18 |
| merged groups | 0 | 6 | 7 | 13 |
| PROPOSE FIX (applied) | 0 | 6 | 7 | 13 |
| CONTEST | 0 | 0 | 0 | 0 |
| ESCALATE / NEEDS LEAD | 0 | 0 (M2 is fixed in text; whether its consequence is intended is NEEDS LEAD 75) | 0 | 0 |
| DECLINE | 0 | 0 | 0 | 0 |

New totals after revision 4 (re-derived by hand from the ticket text; the builder recounts by script):
- BN-17 test row ids: 16 (unchanged); new sub-rows only: FB-T1d, FB-T9 answered-above-R, FB-T5c second variant, FB-T7b explicit `None`.
- BN-17 mutants: 27 ids (was 25), 25 new (was 23): P4b1-b 18 (16 new, + FB-M9d), P4b1-a 6 (+ FB-M5c), P4a-2 3.
- BN-18 test rows: 14 (was 12): P4a-2 12 (+ SG-T11), P4c-2 1 (SG-T6b), P4b1-b 1 (SG-T6d, new).
- BN-18 mutants: 14 (was 11): P4a-2 12 (+ SG-M12, SG-M14), P4c-2 1 (SG-M8), P4b1-b 1 (SG-M13, new).
- P4a-1/P4a-2 body count: 89 plus BN-18's 12 built in P4a-2 (was "plus 10").
- `P4b1.md` BN-35: new mutants in P4b1 = 17 in -b (incl. SG-M13) + 6 in -a = 23 (was 20).
- Unchanged arithmetic: W = 27,360, R = 164,160 micro-dollars (both reviewers re-derived it).

## Merged groups

### G1 [design N-1] Major: the refusal sits at several call sites, not one choke point
- **Checked:** 78 `cli.py` lines 177, 296, 297 and `app.py` 165, 168; 79 `cli.py` 150, 221, 222 and `app.py` 162, 165 are the only `make("llm"/"detector")` sites. `backends/factory.py` loads kind modules by name with `importlib`; kind modules with their own `make`: `llm/anthropic.py`, `bedrock.py`, `gemini.py`, `openai_compat.py`, `guard/bedrock_guardrail.py`, `guard/judge.py`. `registry.py` imports `PROMPT_SHA256` from `guard/judge.py` (so "no import from a kind module" would be too broad).
- **Suggestion:** PROPOSE FIX.
- **Edit:** new paragraph "One choke point for the build sites" in BN-18 and test SG-T11 (AST guard): (a) a factory `make` call with a non-literal first argument fails; (b) `make("llm"/"detector")` outside `cli._main`, `cli._k1b`, `app.build` fails; (c) inside them, it must come after a `live_llm_refusal` call in source order; (d) importing the name `make` from, or calling `<module>.make` on, a paid kind module outside `backends/factory.py` fails. Self-test with a made-up module. Mutant SG-M12 (a new `make("llm")` in `extract.py`). Stated what the guard cannot see: modules loaded by a name read from configuration at run time (78 `actions/executor.py`, `tools.py` do this for action and tool modules, not model kinds).

### G2 [design N-2] Major: "never wrap the stand-in" is a cross-ticket duty with no loud backstop
- **Suggestion:** PROPOSE FIX.
- **Edit:** the P4b1-b wrapper's constructor raises `ConfigError` (78 `errors.py`) when the inner llm is a `RefusedLLM` or a subclass, before any reserve. Test SG-T6d and mutant SG-M13, both built by P4b1-b. The check is in the constructor, not in `chat()`, so FB-2 still books R for every class with no class sorting (round 2 G2's reason holds). FB-1, Who builds what, and `P4b1.md` 397 and 531 updated. The relay into `P4c.md` is now numbered LEAD ACTION 74 in BN-19, with the effect if it is not copied (the constructor refusal makes `app.build` fail loudly in pilot and prod).

### G3 [design N-3] Major: FB-9 has no row or mutant for answered > R; FB-T5c has no mutant
- **Checked:** 79 `meter.py` `Meter._signal_overshoot` calls `on_overshoot` only when the settle is applied, the overshoot is above 0 and the hold is `measured`.
- **Suggestion:** PROPOSE FIX.
- **Edit:** FB-T9 answered-above-R sub-row (books exactly `answered`, `measured=True`, `on_overshoot` once with `answered - R`); mutant FB-M9d (records `None`, books R). FB-T5c second variant (`StoreBusy` once, then success: settled at `answered`); mutant FB-M5c (exit retry settles at the stored R).

### G4 [design N-4] Major: SG-T6c's "run-path spy saw 0 calls" cannot be asserted
- **Checked:** 78 `app.py` `build` passes the same `llm` object to `make("detector", ..., llm=llm)`, so the judge and the run path share the stand-in.
- **Suggestion:** PROPOSE FIX.
- **Edit:** SG-T6c asserts: reason `guard_unavailable` (not `provider_error`); stand-in `chat()` count equals the number of `JudgeDetector.check` calls (spy); no model step of the run's own; cost and day counter 0.

### G5 [codebase M1] Major: two existing tests pin the `route_prices=None` hole
- **Checked:** 78 `tests/test_usage_classes.py` lines 594-595 (`test_c13f_no_prices_books_nothing_and_raises_nothing`, via `_booked`) and 599-606 (`test_c13f_an_abandoned_call_without_prices_books_nothing`, via `_drive`); 78 `k1b/loop.py` `run_case` signature `route_prices: Route | None = None`, three `if route_prices is not None` branches; `Route` is 78 `config.py` `Route`.
- **Suggestion:** PROPOSE FIX.
- **Edit:** FB-7: `route_prices: Route`, required, and an `isinstance(route_prices, Route)` check as the first statement raising `TypeError` (a type hint alone does not refuse `None`). Both C13f tests named as changed on purpose, with new names and replacement assertions (`TypeError`, stub entered 0 times, no worker thread, spent exactly 0). FB-T7b explicit-`None` sub-row; FB-M7b covers the default restored and the explicit `None` accepted.

### G6 [codebase M2] Major: BN-18 leaves pilot and prod agents permanently unqualified
- **Checked:** 78 `runtime/agent_loop.py` `assert_qualified` and `Runtime.__init__` (start-up refuses an unqualified agent); 78 `app.py` `build` constructs `Runtime` with the listed agents; 78 `registry.py` `config_hash` includes `llm_backend` and has no stage key in lines 105-160; 78 `evals.py` is the only product writer of `qualified.jsonl`; 79 `cli.py` `_tick` drops unqualified agents with a "not qualified" line and still builds; 78 `tests/conftest.py` `qualify(...)` writes a green record for tests.
- **Suggestion:** PROPOSE FIX (state the consequence and the fixture) plus NEEDS LEAD 75 (is it intended?).
- **Edit:** new BN-18 paragraph "What this means for qualifying an agent in pilot and prod": (1) `app.build` with an unqualified agent raises `Unqualified`; (2) tick still runs; (3) no new agent can be qualified in pilot or prod while the gate stands; a demo-stage record of an identical configuration would match by reading (not run; no product step copies it). Fixture named: `tests/conftest.py` `qualify(registry, agent_id)` before `app.build` in SG-T1, T2, T6, T6b, T6c, T7, T9; SG-T5's tick runs with and without a record.

### G7 [design N-5 + codebase N3] Nit: FB-T5b as a text search matches the semaphore `.release(`
- **Checked:** 79 `guard/http.py` lines 134 and 140 `_STUCK.release()`.
- **Suggestion:** PROPOSE FIX. **Edit:** FB-T5b is an AST guard: attribute calls `settle_spend`, `release_spend`, `settle` fail outside `meter.py`, `store/`, `llm/metered.py`; `release` fails unless the (file, receiver) pair is on an allowlist holding only `guard/http.py` `_STUCK`.

### G8 [design N-6 + codebase N5] Nit: `migrations_released.json` cannot be checked
- **Checked:** absent in 78 and 79 (`find`); present in snapshot `P3a-2-2b0941b` at `src/hadavin_sdk/store/migrations_released.json`, keys `0001_core` to `0005_evidence` only (other snapshots have a `tests/fixtures/` copy, not the product file).
- **Suggestion:** PROPOSE FIX. **Edit:** FB-6 names the path; rule: change 0006 in place if the file on P4b1-a's base is absent or has no `0006_spend_reservations` key, else a new migration; the builder pastes `git show <base>:src/hadavin_sdk/store/migrations_released.json` output into the evidence.

### G9 [design N-7] Nit: FB-T6b needs a real Postgres; WARNING source unnamed
- **Checked:** 79 `store/postgres.py` `_LOG = logging.getLogger("hadavin_sdk.store")`; `store/memory.py` has no logger.
- **Suggestion:** PROPOSE FIX. **Edit:** WARNING from logger `hadavin_sdk.store` (memory gets one with the same name); the Postgres half needs `HADAVIN_TEST_PG_DSN` and the evidence must show it ran, not skipped (CI Postgres job, or `forbid_skips` of lead order 181).

### G10 [design N-8 + codebase N4] Nit: FB-T7d path and `replay` vs `_replay`
- **Checked:** 78 `k1b/replay.py` `_replay` (line 100) holds the refusals (lines 129-134); `replay` (line 284) is the wrapper.
- **Suggestion:** PROPOSE FIX. **Edit:** FB-T7d calls `k1b.replay.replay(...)` directly with a demo-stage config (the CLI's BN-18 check would hide the fence in pilot); cites in FB-7 and BN-18 items 2 and 3 now say `_replay`; FB-M7c names `_replay`.

### G11 [design N-9] Nit: `RefusedLLM` is not a model kind; release-fails sub-row missing
- **Suggestion:** PROPOSE FIX. **Edit:** FB-1 says plainly that `RefusedLLM` is not a kind, its own `chat()` raises `LLMRefused` before any byte (books 0 with no meter), asserted by SG-T1 and SG-T6, not by FB-T1. New sub-row FB-T1d: lost reserve reply and the best-effort release also fails: `MeterUnavailable`, `chat()` 0 calls, row open at R, counters up by exactly R (the safe side, FB-10); a pin of the safe side with no mutant of its own.

### G12 [design N-10 + N-11] Nit: approval flag only warns; FB-8 mutant list; RefusedDetector clean-verdict mutant
- **Checked:** 78 `approvals/requests.py` `summary`: a flagged check only prefixes a warning to the card.
- **Suggestion:** PROPOSE FIX. **Edit:** BN-18 item 3 says the flag only adds a warning and does not block the approval (and a pilot run with a refused detector ends before any plan). FB-8 mutant column: SG-M1 to SG-M6, SG-M9, SG-M12, SG-M14. New mutant SG-M14 (`RefusedDetector.check` returns a clean verdict), killed by SG-T9 (run and a direct-call assertion added).

### G13 [codebase N1 + N2] Nit: `meter.py` wording; `_exit` retry wording
- **Checked:** 79 `meter.py` `Meter._exit`: retries only `store_busy`; any other `MeterUnavailable` code or exception breaks to `_failed`.
- **Suggestion:** PROPOSE FIX. **Edit:** header says "no `src/hadavin_sdk/meter.py`" and names the unrelated demo file; FB-5 says the exit retry repeats the same settle only after `StoreBusy`, and `CounterDamaged` and every other error stop at once.

## NOT CHECKED (by this resolve)
- Nothing was run: SG-T11's guard, SG-T6d, FB-T1d, FB-T5c's variant, FB-T7b's sub-row, the two changed C13f tests and the new mutants are specified, not built or proven to fail on the old code.
- `config_hash` beyond line 160 of 78 `registry.py` was not read to its end; "no stage key" is from lines 105-160 only.
- Import cycles in `llm/metered.py`: 78 `errors.py` has no import lines at all (grep), so `ConfigError` is safe; `RefusedLLM` lives in `llm/protocol.py`, whose imports (78) are `defaults` and `models` only; `llm/metered.py` does not exist in either snapshot, so its own imports are not checked.
- `P4c.md` is not edited (LEAD ACTION 74). `handover/ledger.md` is not edited (the brief limited the files): the six Majors of round 3 need ledger rows BL-core-p4a-bn17-r3-01 to -06 as FIXED-UNVERIFIED, added by the lead.
- Still open from round 2: possible double booking at 79 `runtime/agent_loop.py` lines 440-441 once the wrapper is wired (P4c-2 territory).

## Open for the lead
- NEEDS LEAD 75: is it intended that, while BN-18 stands, a pilot or prod deployment cannot qualify any agent (so no agent runs there until the gate lifts)? Recommended: yes.
- LEAD ACTION 74: copy the P4c-2 duty (skip `RefusedLLM` when wiring; SG-T6b, SG-M8) into `P4c.md`.
- PENDING LEAD 69: plan review round 4 of revision 4 (egm-design and egm-codebase-details, uncapped) before any builder codes against BN-17 or BN-18.
