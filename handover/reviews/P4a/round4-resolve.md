Status: resolved (revision 5 applied to the ticket text; not yet re-reviewed)

# P4a BN-17/18/19 revision 4, plan review round 4: resolve

**Target:** `handover/tickets/P4a.md` build notes BN-17, BN-18, BN-19 (lines 606-718 after the edit) and the revision log on line 3; `handover/tickets/P4b1.md` line 397 (item 5 bracket) and line 531 (BN-35).
**Findings:** `reviews/P4a/round4-design.md` (egm-design, money path: 0 Blockers, 5 Majors M1-M5, 7 Nits N1-N7, 1 open question) and `reviews/P4a/round4-codebase.md` (egm-codebase-details: 0 Blockers, 2 Majors M1-M2, 5 Nits N1-N5).
**Resolver:** egm-resolve method, headless (brief: no questions; every PROPOSE FIX is applied as revision 5). Written 2026-11-09 08:21 UTC (13:51 IST), from `date -u`. Money path: no round cap.
**Code facts:** checked only by reading `/home/user/build/snap/78-4a0976f` ("78"), `/home/user/build/snap/79-8cc2021` ("79") and `origin/main` (`0dabf1f`) for the migration files and `store/migration_numbers.py`. Nothing was run: no tests, no mutants, no guard, no import-cycle check.
**Slip to report:** the revision 4 entry was missing from the line 3 revision log; revision 5 adds it, marked as added late.
**Commit note:** I did not commit. The lead session's own automatic commits picked up my edits while I worked (`a5fb15e` holds the first P4a.md edit batch, `1698f31` the P4b1.md edits). The later P4a.md edits (codebase N2 and N5, plus one count phrase) were picked up by `e74b43e`. Only this resolve file is uncommitted.

## Counts

| | Blocker | Major | Nit | Open question | total |
|---|---|---|---|---|---|
| raw findings (design + codebase) | 0 | 7 (5 + 2) | 12 (7 + 5) | 1 | 20 |
| merged groups (design N3 merged into codebase M2) | 0 | 7 | 11 | 1 | 19 |
| PROPOSE FIX (applied) | 0 | 7 | 8 | 1 | 16 |
| CONTEST | 0 | 0 | 3 (design N2, N6, N7) | 0 | 3 |
| NEEDS LEAD (in addition to the applied default) | 0 | 4 (76, 78, 79; 77 is a lead action) | 0 | 1 (75 updated) | 5 |

New totals after revision 5 (counted by hand from the ticket text; the builder recounts by script):
- BN-17 test row ids: 17 (was 16; + FB-T9b). New sub-rows: FB-T2 alert, FB-T6b upgrade, FB-T7 booking-raises, FB-T7b look-alike, FB-T9 real-counter and field proven 0, FB-T1e (only if P4b1-b keeps its own W formula).
- BN-17 mutants: 32 ids (was 27), 30 new (was 25): P4b1-b 19 (17 new, + FB-M2h), P4b1-a 7 (+ FB-M6d), P4a-2 6 (+ FB-M7d, FB-M9e, FB-M9f).
- BN-18: 15 test rows (was 14; + SG-T12), 16 mutants (was 14; + SG-M15, SG-M16; SG-M5 and SG-M12 redefined). 13 rows and 14 mutants are built in P4a-2.
- P4a-2 test rows from BN-17 and BN-18: 6 + 13 = 19 (codebase N3 asked for this total; it said 17 before revision 5 added FB-T9b and SG-T12).
- P4a-1/P4a-2 body mutant count: 86 becomes 92, plus BN-18's 14.
- `P4b1.md` BN-35 new mutants: 18 in -b + 7 in -a = 25 (was 23).
- Unchanged: W = 27,360 and R = 164,160 micro-dollars (the codebase reviewer re-derived both).

## Merged groups

### G1 [design M1] Major: the refusal sits at several call sites, so it is not one choke point
- **Checked:** 78 `backends/factory.py` `make(capability, settings, provider=None, **available)` reads `TABLE[capability][settings.kind]`, then `importlib.import_module`, then calls the factory. Every llm and detector build goes through it: 78 `cli.py` 177, 296, 297 and `app.py` 165, 168 (25 `make(` calls in product code in all). `make` has no stage today. `config.py` imports `deferred` and `backends/table.py`; `factory.py` imports neither `config` nor `deferred`.
- **Suggestion:** PROPOSE FIX (the reviewer's main recommendation, without the `TABLE` flag).
- **Edit:** `make` gains a keyword-only `stage: str | None = None`. For capability `llm` or `detector`, its FIRST step calls `live_llm_refusal(stage, capability, kind)`, which now takes the stage value and not the config. A refusal raises `PaidKindRefused`, a new `ConfigError` subclass, before the module import. A missing stage refuses a paid kind (fail closed). `app.build` catches exactly that class and installs `RefusedLLM` or `RefusedDetector`. The early CLI checks for `gate` and `replay` stay, because lead order 178 also wants those commands to stop before `make("secrets")`. SG-T11 shrinks to two rules: only the factory reaches a paid kind module's `make`, and `stage=` is never a constant. Round 3's rules (a) to (c) are dropped. New: SG-T12 (factory unit row), SG-M15 (a missing stage is read as demo) and SG-M16 (`build` lets the refusal propagate). SG-M5 and SG-M12 are redefined. Paragraph "The choke point is `make` itself" replaces "One choke point for the build sites".
- **Not taken:** the reviewer's `paid` flag on `backends/table.py` entries. It would be a second source next to `live_llm_refusal`'s allowlist, which already fails closed.
- **Uncertain:** whether `factory.py` can import `deferred.py` or `config.py` without an import cycle (not run). The ticket says the function moves to `deferred.py` if needed and stays one function. The number of existing tests that call `make("llm"|"detector", <paid kind>)` without a stage is not counted. The builder lists them by script.

### G2 [design M2] Major: FB-9 waits for a P4b2-a field that the retry loop could already supply
- **Checked:** 79 `llm/retry.py` `with_retry` (identical in 78) loops `for attempt in range(1, max_attempts + 1)` and keeps no count. A non-transient error raises at once, and an exhausted retry raises `ProviderExhausted`. 78 `llm/common.py` `NetworkLLM._retry` is the only caller, and all four kinds call `self._retry`. `P4b2.md:105` plans `Reply.unknown_attempts: int = 0`, written only by `NetworkLLM.chat`. With the default `max_attempts: 3` and count 2, R = 6W, so every answered call books about 6 times its cost: the reviewer's figure, confirmed by arithmetic.
- **Suggestion:** PROPOSE FIX, plus LEAD ACTION 77.
- **Edit:** P4a-2 builds the counter now. It adds `with_retry(..., on_retry=None)`, called once per retried failed attempt. `NetworkLLM.chat` keeps a per-call count that is not shared between threads and sets the new field `Reply.unknown_attempts: int | None = None` (`None` means not counted). FB-9's existing "field proven" branch then applies: answered + u x W, which is exactly the answered cost when no attempt was retried. New: unit row FB-T9b, FB-T9 real-counter and proven-0 sub-rows, and mutants FB-M9e and FB-M9f. The "Requirement on P4b2-a" paragraph is rewritten, and so is the cost paragraph. PENDING LEAD 72 now recommends keeping the default of 3 attempts. Hot-file order does not change: P4a-2 is already listed for `llm/common.py`, `llm/retry.py` and `models.py`.
- **Why this stays inside the lead's rule (3):** the table already approved the "field proven" branch. This fix only builds the proof earlier. It does not lower a booking below R for any call whose hidden attempts are uncounted. The reviewer's looser bound, `(attempts - 1) x W` for an uncounted call, was not applied.

### G3 [design M3] Major: an outage or a wrong key books R per failure and can lock agents out
- **Checked:** 79 `meter.py` has `on_overshoot` and `on_settle_failed` callbacks only, wired through 79 `limits.py`. `P4c.md` lines 112-113 wire those two to "a person must look". Nothing in 78 or 79 sends an alert on a failure booking. Counters are per agent: 79 `store/memory.py` keys the day by `(agent_id, day)` and sums the month per agent. A 4xx is a `ProviderError` at the first attempt. A refused connection is an `OSError` and is retried.
- **Suggestion:** PROPOSE FIX for the alert and for the plainly stated consequence; NEEDS LEAD 78 for the "provably unsent" class.
- **Edit:** FB-2, FB-3 and FB-4 call a new `Limits.on_failure_booked` and log one WARNING, with an alert sub-row and mutant FB-M2h. A "Lock-out after an outage or a wrong key" bullet gives numbers. With R = US$0.164160, a US$5 day cap is used up after 30 failures and a US$50 month cap after about 304. LEAD ACTION 74 now also tells P4c-2 to wire the new callback to a person.

### G4 [design M4] Major: two sources compute R
- **Checked:** 78 `k1b/loop.py` `_charge_factor` (lenient, `_count_or` with the fallbacks 2 and 10) and 78 `llm/common.py` `request_bound` (strict). Their attempts rule is the same (an int of at least 1, a bool refused).
- **Suggestion:** PROPOSE FIX.
- **Edit:** one function, `reserved_factor(llm, *, strict)` in 78 `llm/common.py`, built by P4a-2. k1b uses `strict=False` and the P4b1-b meter uses `strict=True`. FB-T7c is rewritten to test it.

### G5 [design M5] Major: the gate trusts an operator-written stage value
- **Checked:** 78 `config.py` `Config.environment: Literal["dev", "pilot", "prod"]`. `_cross_checks` and `_anchor_refusals` refuse kinds by stage only. Nothing ties `dev` to a real demo environment.
- **Suggestion:** PROPOSE FIX (state it plainly, and add a start-up WARNING with an SG-T3 assertion) plus NEEDS LEAD 79 (whether a stronger tie is wanted).
- **Edit:** new paragraph "What the stage value rests on".

### G6 [codebase M1] Major: P4b1.md lines 27, 52 and 76 still say "no store file, no migration"
- **Checked:** the three lines in `P4b1.md` say exactly that.
- **Suggestion:** PROPOSE FIX.
- **Edit:** BN-35 now lists the three lines as superseded for exactly `store/memory.py`, `store/postgres.py` and the one new migration. It names P4d as the owner that is overridden (amendment A11), only for the `expired`-row guard, and gives the hot-file order P4d, then P4b1-a.

### G7 [codebase M2 + design N3] Major: an edit to 0006 in place does not reach databases that already applied it
- **Checked:** 78 `store/migrate.py` `migrate` skips applied files by name (`if path.stem in done`) and keeps no checksum. `origin/main` has only 0001 to 0005 and no `migrations_released.json`. Snapshots 76, 78 and P6b1 have `0007_kill_switch_guard.sql`, and 79 and P4da2 end at 0006. Main's `store/migration_numbers.py` `late_files` refuses a file numbered at or below the highest applied one; P3a-2 is what puts that rule in force. In 79, 0006 defines `hadavin_spend_reservations_update()` with `CREATE OR REPLACE FUNCTION` and binds the trigger to it by name.
- **Suggestion:** PROPOSE FIX (the new migration becomes the only path) plus NEEDS LEAD 76 (in place only if the lead states that no database applied 0006).
- **Edit:** FB-6 now requires a new file numbered after the last one on P4b1-a's merge base (`0008_...` if PR78 merged first). It holds only `CREATE OR REPLACE FUNCTION` and does not re-create the trigger. The Python `_close` guards change in place. FB-T6b gains an upgrade sub-row (an old 0006 is applied first), and FB-M6d is added. The revision 4 manifest rule is removed.

### G8 [design open question] Pilot and prod cannot qualify any agent while the gate stands
- **Suggestion:** PROPOSE FIX (the reviewer's conditions are written in) and PENDING LEAD 75 is updated.
- **Edit:** "Lifting the gate" now names one pull request (proposed `core/P4-lift-stage-gate`) and its checklist: the meter on every path; the stage carried in the gate record or added to `config_hash` (78 `registry.py` has no stage key); SG-T1, SG-T2 and SG-T4 flipped and FB-8 closed; the owner told before any pilot date is promised. A fake-kind smoke run is added only if a test needs it.

### G9 [design N1] Nit: FB-1 says "books 0" while FB-T1d leaves R open
- **Suggestion:** PROPOSE FIX. **Edit:** the books cell now says "0", with one named exception: FB-T1d, where R stays open.

### G10 [design N2] Nit: the stand-in ends as `provider_error`, which looks like an outage
- **Checked:** 79 `runtime/agent_loop.py` records only `error_code` (`provider_error` or `provider_exhausted`) in `_note`.
- **Suggestion:** CONTEST. Tagging `LLMRefused` in the run's audit text requires editing `runtime/agent_loop.py`, which lead order 175 item 5 forbids. The refusal also covers the whole deployment, not one run, and is named in the start-up WARNING. In addition, while the gate stands, pilot and prod agents cannot be qualified (PENDING LEAD 75), so such runs are reachable only in tests. No edit.

### G11 [design N4] Nit: keep a test that refuses a mock `Route`
- **Suggestion:** PROPOSE FIX. **Edit:** FB-T7b gains a look-alike sub-row (a `SimpleNamespace` with `Route`'s field names is refused). The ticket also notes that `Mock(spec=Route)` passes `isinstance`.

### G12 [design N5] Nit: tie FB-T7c's "20" to `Field(le=10)`
- **Suggestion:** PROPOSE FIX. **Edit:** FB-T7c reads the `le` bound from the settings model's field metadata and multiplies it by the largest declared `REQUESTS_PER_CHAT`.

### G13 [design N6] Nit: the P4c.md duty relies on the lead; the backstop SG-T6d is good
- **Suggestion:** CONTEST (no change). The reviewer rates the backstop as sufficient, and LEAD ACTION 74 stays.

### G14 [design N7] Nit: send the build WARNING to the operator alert path
- **Checked:** neither 78 nor 79 has an operator alert path. The person-facing paths are the meter callbacks that P4c-2 wires.
- **Suggestion:** CONTEST. There is no path to send it to. The money-relevant alert (`on_failure_booked`) is added under G3 and routed through P4c-2. The build refusal is a deployment-wide state shown in the start-up log. No edit.

### G15 [codebase N1] Nit: FB-T7 duplicates the existing C13 tests
- **Checked:** 78 `tests/test_usage_classes.py` `test_c13b`, `c13c`, `c13d`, `c13d2` and `c13j` exist and assert exact equality.
- **Suggestion:** PROPOSE FIX. **Edit:** FB-T7 names those tests and adds only `KeyError` and `KeyboardInterrupt`.

### G16 [codebase N2] Nit: two copies of the worst case W
- **Checked:** 78 `k1b/loop.py` `worst_case_usd` (byte bound, rounded up once). `worst_case_micro` does not exist yet; P4b1-b builds it.
- **Suggestion:** PROPOSE FIX. **Edit:** the definition of W says P4b1-b either reuses `worst_case_usd(..., requests=1)` or adds relating sub-row FB-T1e.

### G17 [codebase N3] Nit: no P4a-2 test-row total
- **Suggestion:** PROPOSE FIX. **Edit:** the counts paragraph gives P4a-2 19 rows (6 + 13).

### G18 [codebase N4] Nit: the booking in `except BaseException` may itself raise
- **Checked:** 78 `k1b/loop.py` `_worst_case_of_call` calls `worst_case_usd`, which can raise. `Budget.charge` only adds.
- **Suggestion:** PROPOSE FIX. **Edit:** FB-7 runs the booking in its own `try`, and the original exception wins. FB-T7 gains a sub-row, and FB-M7d is added. The cost is stated: a failed booking is not booked, and the in-memory budget ends with the run.

### G19 [codebase N5] Nit: the second 78-only file is unnamed
- **Checked:** 78 `tests/test_stop_state_memory.py` lines 121 and 123 contain `environment="pilot"` and no `pilot_cfg`. 79 has no `test_stop_state_*` files.
- **Suggestion:** PROPOSE FIX. **Edit:** the evidence paragraph names the file and says it needs no change.

## Files changed
- `handover/tickets/P4a.md`: revision log line 3 (revision 4 added late, revision 5 added); BN-17, BN-18 and BN-19 as listed above. 718 lines (was 710). No line added or removed above the build notes.
- `handover/tickets/P4b1.md`: line 397 bracket and line 531 BN-35 (revision 5 header, lines 27/52/76 superseded with P4d named as the overridden owner, FB-M2h, FB-M6d, new migration, `on_failure_booked`, `reserved_factor`, field built by P4a-2, counts 25 new, lead items 76-79). 531 lines (unchanged).

## NEEDS LEAD
- **76.** Migration 0006: the default written in is a NEW migration file. Change 0006 in place only if the lead states in writing that no database (CI, laptop, demo) applied 0006 from the PR79 or P4d branches.
- **77 (LEAD ACTION).** Copy into `P4b2.md` before P4b2-a's plan review: P4a-2 builds `Reply.unknown_attempts: int | None = None` and the retry counter. P4b2-a keeps them and adds only failure stamps. `P4b2.md:105` is superseded.
- **74 (LEAD ACTION, extended).** P4c-2 also wires `Limits.on_failure_booked` to a person, the same way as `on_overshoot` and `on_settle_failed`.
- **78.** Should a failure that provably sent nothing (a DNS failure or a refused connection on every attempt) book 0 through a new table row? Recommended: no for now (lead order 175 rule (2); a proxy hides where the bytes stopped; vendor SDKs wrap these errors differently). Revisit with P4b2-a's reconciler.
- **79.** The stage value is written by the operator. Recommended: accept it, with the start-up WARNING and the provider-side spending limit (PENDING LEAD 67), and tell the owner plainly. Alternative: a demo-stage configuration with a real llm kind must name its demo budget, or start-up refuses it.
- **75 (updated).** Is "pilot and prod cannot qualify any agent until the gate lifts" intended? The reviewer accepts it only with the owner told before any pilot date is promised and the gate-lifting pull request named. Both are now in the ticket; the lead confirms the name `core/P4-lift-stage-gate`.
- **69 (updated).** One fresh plan review round 5 of revision 5 (egm-design and egm-codebase-details, money path, uncapped) before any builder codes against BN-17 or BN-18.
