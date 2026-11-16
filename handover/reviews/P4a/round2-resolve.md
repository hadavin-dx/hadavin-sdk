Status: resolved (revision 3 applied to the ticket text; not yet re-reviewed)

# P4a BN-17/18/19 revision 2, plan review round 2: resolve

**Target:** `handover/tickets/P4a.md` lines 606-698 (BN-17, BN-18, BN-19) and `handover/tickets/P4b1.md` line 531 (BN-35).
**Findings:** `reviews/P4a/round2-design.md` (0 Blockers, 4 Majors R2-1 to R2-4, R2-5 Major partly open, 6 Nits) and `reviews/P4a/round2-codebase.md` (1 Blocker, 3 Majors, 5 Nits). Round 1 (`bn17-plan-design.md`, `bn17-plan-codebase.md`) re-read for context; both round-2 reviewers mark every round-1 item closed except R2-5 and the k1b answered path (R2-3).
**Lead orders applied:** 178 (BN-18 narrowed to the build site; migrate, audit verify, kill-switch commands and tick keep working in pilot and prod), 173 (no `dev`/`demo` alias), R449 (stage names). Money path: no round cap.
**Resolver:** egm-resolve, headless (the brief said no questions; every PROPOSE FIX below is applied as revision 3). 2026-11-09 07:40 UTC (13:10 IST).
**Code facts:** checked only against `/home/user/build/snap/78-4a0976f` ("78") and `/home/user/build/snap/79-8cc2021` ("79"), read-only. Nothing was run (no tests, no mutants).

## Counts

| | Blocker | Major | Nit | total |
|---|---|---|---|---|
| raw findings (design + codebase) | 1 | 8 (4 + 1 + 3) | 11 (6 + 5) | 20 |
| merged groups | 1 | 7 | 5 | 13 |
| PROPOSE FIX (applied) | 1 | 7 | 5 | 13 |
| CONTEST | 0 | 0 | 0 (one part-contest inside G10, see there) | 0 |
| ESCALATE / NEEDS LEAD | 0 | 0 | 0 | 0 |
| DECLINE | 0 | 0 | 0 | 0 |

## Merged groups

### G1 [codebase B1 + design N5] Blocker: `FakeLLM` facts are wrong in two tickets
- **Finding:** P4a.md:642 and P4b1.md:531 say `FakeLLM` declares no `max_attempts`. In 78 `llm/fake.py` `FakeLLM` declares `REQUESTS_PER_CHAT = 1` and `max_attempts = 1`; in 79 it declares neither (so `request_bound(FakeLLM())` raises `TypeError` there, FB-1).
- **Checked:** confirmed by reading 78 `llm/fake.py:22-25` and grepping 79 `llm/fake.py` (no match).
- **Suggestion:** PROPOSE FIX (decision e).
- **Edit:** state both facts with their snapshot; the merged tree (P4a-2 merges first; the PR78 branch is 78) has count 1 and attempts 1, so a wrapped fake has R = W. FB-T2's "absent gives 10" sub-row uses a test stub that declares only `REQUESTS_PER_CHAT = 2` (no `max_attempts`); FB-T7c's undeclared case uses a bare `object()`. FB-T2 runs on the P4b1-b branch (78 + 79 merged); FB-T7c runs on the P4a-2 branch (78). One new FB-T2 sub-row: the real `FakeLLM` wrapped books exactly 1 x 1 x W. Same correction in P4b1.md BN-35 ("Line 260").

### G2 [design R2-1] Major: the metering wrapper and the BN-18 stand-in contradict each other
- **Suggestion:** PROPOSE FIX (decision a: the build does not wrap a stand-in).
- **Why this choice:** it is the simplest rule and keeps FB-2 free of class sorting (FB-2 must book R for every class once `chat()` is entered). A check inside the wrapper would be a second place that knows about the stand-in.
- **Edit:** the stand-in is a class `RefusedLLM` (P4a-2, `llm/protocol.py`, next to `LLMRefused`). Rule: no code wraps a `RefusedLLM` in the meter; the place that wires the meter around the llm that `app.build` returns (P4c-2, per Answer first 1(d)) skips it. New FB-1 cause "the BN-18 stand-in refused (never wrapped, nothing reserved)". New test SG-T6b (built by the pull request that first wraps the `app.build` llm, P4c-2 today): with the wrapper wiring installed, a refused pilot call leaves 0 open rows and the run, day and month counters unchanged. New mutant SG-M8 "the wiring wraps the stand-in" (FB-2 then books R; killed by SG-T6b).

### G3 [design R2-2 + codebase M1 + codebase N3] Major: "before any secret read" is false at two build sites
- **Checked:** 78 `cli.py` `_k1b` calls `make("secrets")` (:290) and `build_audit` (:291) before `make("llm")` (:296); the `gate` branch (:173-180) builds secrets inside the `evals.gate(...)` argument list; 78 `app.py` `build` reads every backend secret, the llm's included, through `platform_secrets.check` (:125; `backends/platform_secrets.py:58-63` calls `provider.get(name)`).
- **Suggestion:** PROPOSE FIX (decision b).
- **Edit:** `replay`: the check is the first statement of `_k1b` for `args.cmd == "replay"`, before `make("secrets")` (78 :290); `score` is untouched. `gate`: the check is the first statement of the `gate` branch. `app.build`: the rule sentence now says plainly that the llm secret is still read at start-up by `platform_secrets.check` (unchanged, so the shared-name checks there keep working and a pilot without that secret still fails start-up as today); only `make("llm")` and `make("detector")` for refused kinds are skipped. Reason for not excluding the llm entry from that check: the check also refuses a secret shared between a backend and an executor or a read tool (least privilege); dropping the entry would drop that check for the llm secret. SG-T4 keeps the spy on both `make("secrets")` and `make("llm")` and asserts 0 calls of each for `gate` and `replay`; the `replay` half is reachable only through that spy (codebase N3: replay already refuses every non-fake kind later, 78 `k1b/replay.py:129-134`). New mutant SG-M11 "the replay check sits after `make("secrets")`" (killed by SG-T4).

### G4 [design R2-3 + codebase N1 + codebase N2] Major: the k1b answered-call path is outside the table
- **Checked:** 78 `k1b/loop.py:215` `budget.charge(reply.cost_usd)` on an answered reply; 78 `k1b/replay.py:129-134` refuses a non-fake kind and a `NetworkLLM` object; 78 `llm/fake.py` declares `max_attempts = 1`, so the fake's answered call has nothing hidden.
- **Suggestion:** PROPOSE FIX (decision c: fake-only pin with a test, not a new booking branch).
- **Why:** no real kind can reach the k1b answered path today; a pin that fails when the fence is removed is the smaller, testable change, and it forces FB-9 to be applied before the fence is lifted.
- **Edit:** FB-7 gains "answered path": fake kind only; FB-9 applies to k1b before any real kind is allowed there. New test FB-T7d: `replay` with a non-fake kind, and with a `NetworkLLM` object under a `fake` label, raises `ConfigError` (pin); new mutant FB-M7c: the `NetworkLLM` refusal in `replay` removed (killed by FB-T7d). Codebase N1: P4a-2 updates the `run_case` docstring ("Never raises for a model or provider problem") to say that a non-provider exception is booked and re-raised, and that the caller `replay` writes `FAILED.txt` and re-raises (78 `k1b/replay.py:285-296`). Codebase N2: stated plainly that the k1b charge lives only in the run's in-memory `Budget`; the run ends on the re-raise; no money exposure because the kind is fake (FB-T7d).

### G5 [design R2-4] Major: `bedrock_guardrail` is a paid, unmetered call that BN-18 does not refuse
- **Checked:** 78 `backends/table.py:556-563` (`bedrock_guardrail`, cloud `aws`, reads its filters at start-up); 78 `app.py:168` and `cli.py:297` are the only `make("detector")` sites (79: `app.py:165`, `cli.py:222`).
- **Suggestion:** PROPOSE FIX (decision d: build the refusal now, fail closed).
- **Edit:** `live_llm_refusal(cfg, capability, kind)` also covers detectors: outside the demo stage every detector kind other than `regex` and `llm_judge` is refused (an allowlist, so a new paid detector kind is refused by default; `llm_judge` already goes through the llm stand-in). In `app.build` a refused detector is replaced by a `RefusedDetector` whose `check` raises `LLMRefused`; `injection_check` (78 `guard/injection.py:85-101`) turns that into `flagged`, reason `guard_unavailable`, so a person must look (fail closed). The approval summary screen keeps that member and so also flags (fail closed; stated). The `_k1b` site is already covered by the replay check (G3). FB-8 and P4b1.md:397 wording: "no paid model or detector call is built in pilot or prod". New test SG-T9, mutant SG-M9. PENDING LEAD 71 is closed by this.

### G6 [design R2-5] Major: an `expired` row accepts a lower settle or a release (PL73)
- **Checked:** 79 `store/memory.py` `_close` refuses only settled/released (:331); 79 `store/postgres.py` `_close` claims `status IN ('open', 'expired')` (:619-621); 79 migration `0006_spend_reservations.sql` trigger allows `expired` to `settled`/`released` (:56); the sweep sets `settled_usd = reserved_usd` without lowering counters, so a later lower settle lowers them.
- **Suggestion:** PROPOSE FIX (decision f: build-time default). No concrete reason against was found: nothing calls the sweep before P4b2-a, so no existing flow needs to lower an `expired` row; P4b2-a's reconciler, when it comes, adds its own path as a new row of this table.
- **Edit:** P4b1-a makes both stores refuse a release of an `expired` row and a settle of an `expired` row below its reserved amount: memory `_close` and postgres `_close` return `applied=False` with the stored row unchanged and log one WARNING naming the reservation id; the postgres trigger refuses `expired` to `released` and `expired` to `settled` with `settled_usd < reserved_usd` (in 0006 if it is not yet in `migrations_released.json` when P4b1-a is built, else a new migration; 79 has no released manifest entry for 0006). FB-T6b changes from a pin to a test (both stores, plus a direct UPDATE as the store's own role against the trigger); new mutants FB-M6b (memory accepts the lower settle) and FB-M6c (the trigger allows it). PENDING LEAD 73 is closed by this.

### G7 [codebase M3 + design N1] Major: FB-5 and FB-9 disagree on `SettleFailure.planned`
- **Checked:** 79 `meter.py` `_failed` (:418-421): `planned = None if h._release else h._actual`, logged amount `planned or reserved`; `Meter.settle(id, None)` books the stored reserved amount; `_exit` retries the same settle before `_failed`.
- **Suggestion:** PROPOSE FIX (decision g).
- **Edit:** each row names its `record(...)` call. FB-2, FB-3, FB-4: `h.record(None, measured=False)`. FB-9: field absent or not proven and answered <= R: `h.record(None, measured=False)` (books R, `planned is None`); answered > R: `h.record(answered, measured=True)` (`planned == answered`); field proven: `h.record(answered + u x W)`; attempts == 1: `h.record(answered)`. FB-5: `planned is None` after FB-2/3/4 and after FB-9 with answered <= R; after FB-9 with answered > R, `planned == answered` and the logged amount is `answered`; the row stays open at R, which is below the measured cost by `answered - R` until repair. Repair rule: a repair settles at the logged planned amount when it is not None, else at R (`Meter.settle(id, None)`); before P4b2-a only the hold's own exit retry exists, and it retries the same planned amount. New test sub-row FB-T5c (answered > R plus `CounterDamaged`: `planned == answered`, logged amount `answered`, row open at R).

### G8 [codebase M2 + design N3] Major: the judge path under the stand-in is unspecified
- **Checked:** 79 `runtime/agent_loop.py` `Runtime.handle` screens the document (:387-390, `injection_check`) BEFORE the run-path `self.llm.chat` (:425). 78 `guard/judge.py:72` calls `self.llm.chat`; `injection_check` catches any `Exception` and returns `flagged=True, reason_code="guard_unavailable"` with one WARNING per check.
- **Suggestion:** PROPOSE FIX (decision i: fail closed, a person must look).
- **Edit:** with `llm_judge` in the detector list, a pilot run ends at the document screen as "a person must look" with reason `guard_unavailable`, before the run-path model call; 0 booked; one WARNING per check. SG-T6 now says its detector list is `regex` only (then the reason is `provider_error`). New row SG-T6c (with `llm_judge`). `extract.py` and `evals.py`: no pilot or prod caller builds an llm for them other than the `gate` command (refused by G3); stated.

### G9 [design N4] Nit: the gate fails open for a future fourth stage
- **Suggestion:** PROPOSE FIX (decision h).
- **Edit:** `live_llm_refusal` refuses unless `cfg.environment` equals the demo stage. The demo stage's spelling lives in one new constant `deferred.DEMO_STAGE` next to `LIVE`; today it holds the `Config.environment` value that R449 reads as "demo" (spelled `dev` in 78 and 79 `config.py`; the rename PR of PENDING LEAD 68 changes only this value). Test SG-T10 is parametrised over `typing.get_args` of the `Config.environment` Literal plus one value outside it built with `model_construct` (for example `"staging"`): every value other than `DEMO_STAGE` is refused. Mutant SG-M10: the check is "in `deferred.LIVE`" (fails open; killed by the out-of-Literal value).

### G10 [design N6] Nit: constants `METER_MIN_MICRO` and `METER_ABSURD_TOKENS`
- **Checked:** neither exists in 78 or 79 src. `P4b1.md` BN-9 (line 480) CUTS `METER_ABSURD_TOKENS` and replaces it with `MAX_USAGE_TOKENS_PER_CLASS`, which exists in 78 `defaults.py:157` (P4a-1). `METER_MIN_MICRO = 1` is one of P4b1-b's four constants (P4b1.md:50 as amended by BN-9).
- **Suggestion:** PROPOSE FIX, with a part-contest: the brief and the reviewer ask to list `METER_ABSURD_TOKENS` as a P4b1-b constant; that would undo P4b1 BN-9. It is not added.
- **Edit:** FB-9 says `METER_MIN_MICRO` is created by P4b1-b (one of its four constants, P4b1 BN-9); FB-4 says the B4 forms are those of `P4b1.md` as amended by BN-9 (a count above `MAX_USAGE_TOKENS_PER_CLASS`, 78 `defaults.py`, P4a-1), so `METER_ABSURD_TOKENS` is not created.

### G11 [design N2] Nit: missing mutants for FB-9 garbage forms and the lost reserve reply
- **Suggestion:** PROPOSE FIX.
- **Edit:** FB-M9c (a `bool` or out-of-range field is accepted as proven; killed by FB-T9 garbage sub-rows); FB-M1e (the best-effort release after a lost reserve reply removed; killed by FB-T1c).

### G12 [codebase N4] Nit: long refusal-text parenthetical
- **Suggestion:** PROPOSE FIX. **Edit:** text becomes f"environment {env}: refused: {capability}: {kind} (paid calls run only in the demo stage for now; see CHANGELOG)".

### G13 [codebase N5] Nit: the 10,189-pass figure is a sketch run; `ScriptedLLM`/`ScriptLLM` unconfirmed
- **Checked:** the four test classes (78 `tests/k1b_support.py:17`, `test_k1a_pass_k.py:23`, `test_k3_pilot.py:52`, `k5_support.py:124`) are plain classes, not `NetworkLLM` subclasses (78 `llm/common.py:212`).
- **Suggestion:** PROPOSE FIX. **Edit:** the evidence paragraph says the builder re-runs the full suite on the real P4a-2 head and the evidence runner records it; the plain-class fact is stated with its cites.

## NOT CHECKED (by this resolve)
- Nothing was run. The new rows SG-T6b to SG-T10, FB-T5c, FB-T6b (now a test), FB-T7d and the five new FB mutants and four new SG mutants are specified, not built.
- Possible double booking once the wrapper is wired: 79 `runtime/agent_loop.py:440-441` still calls `limits.charge` and `store.add_cost` after an answered call (P4c-2 territory; not changed here).
- Whether `openai_compat` sums usage across its two requests; gemini/openai_compat SDK retry settings (taken from the ticket).
- `P4c.md` is not edited: SG-T6b and SG-M8 bind P4c-2 through BN-17's "wins over every other ticket" clause; the lead relays it.

## Ledger
Rows BL-core-p4a-bn17-r2-01 to -08 (the Blocker and seven Majors) appended to `handover/ledger.md` as FIXED-UNVERIFIED (text fix; verified only by the round-3 plan review).
