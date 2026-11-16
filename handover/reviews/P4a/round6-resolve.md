Status: resolved (fixes applied to the ticket text as revision 7; not yet re-reviewed)

# P4a BN-17 to BN-19, plan review round 6: resolve (egm-resolve, headless, ordered mode)

Written 2026-11-09 08:51 UTC (14:21 IST) by the resolver (Opus 5.5). Money path: no round cap.
Targets: `handover/tickets/P4a.md` (revision 6 -> 7: build notes BN-17 to BN-19, lines 606 onward, plus the revision log on line 3) and `handover/tickets/P4b1.md` (BN-35 on line 531 only, as a supersede list).
Findings: `reviews/P4a/round6-design.md` (0 Blockers, 4 Majors M1-M4, 8 Nits N1-N8) and `reviews/P4a/round6-readiness.md` (0 Blockers, 1 Major M1, 5 Nits N1-N5). Below, design findings are `D-`, readiness findings `R-`.
Lead answers applied as binding: LEAD ORDER 189 (q404): N-1 one pull request PR78, N-2 a refusal in both config-read loaders, N-3 the new migration file goes on P3a-2's trigger allow list; merge order PR75, PR76, PR78, PR79, P4b1-b confirmed. LEAD ORDER 186 G73-2(c) (P3a-2 refuses a changed trigger-function body unless allow-listed).

**Nothing was built, run or tested.** I ran only read-only commands: `sed`, `grep`, `awk`, `git log`, `git ls-tree`, `git show` and `git branch -r` against `origin/*` refs, `date -u`, and one read-only `python3 -I` script that parses the two snapshots' `src/hadavin_sdk/` with `ast` (it writes nothing). No commit, no push. Ticket edits were applied by one `python3 -I` script of exact-string replacements, each asserted to match exactly once.

## Facts I checked for this resolve (read, not run)

- F1. 78 `tests/contracts/kinds/store_postgres.py` line 26: `pg_schema(migrated=True, runtime=False)`; with `migrated=True` it calls `migrate(scoped, reset_role=RESET_GROUP)` (line 43), so a default `pg_schema()` already applies every file. 78 `store/migrate.py` `migrate` raises `ConfigError` when `reset_role` is None. `RESET_GROUP = "hadavin_test_reset"` is in 78 `tests/stop_state_helpers.py` line 34. `pg_schema(migrated=False)` is already used by 78 `tests/test_k5_fixes2.py:303`, `test_p2_postgres.py:152`, `test_p7_store.py:125`. Readiness M1 is correct.
- F2. 79 `store/migrate.py` line 55 grants the runtime role read and write on `spend_reservations` (no DELETE). 79 `0006_spend_reservations.sql` lines 40-67: the update trigger allows open to expired (with `settled_usd = reserved_usd`, `closed_at`, `expired_at` set) and expired to settled or released.
- F3. 78 `store/migrate.py` lines 548-551: `migrate` refuses with "applied migrations have no file in this release: ..." when the ledger holds a stem with no file. Design N4's cite (320-326) points at other text; the behaviour it names is real at 548-551.
- F4. Migration files on every `origin/*` ref (2026-11-09 08:50 UTC): `origin/main` holds 0001 to 0005; `0006_spend_reservations.sql` is on `core/P4d-a2`, `core/P4b1`, `core/P2a-1`, `core/P4a`, `core/P6b1`; `0007_kill_switch_guard.sql` on `core/P2a-1`, `core/P4a`, `core/P6b1`; no ref holds any other file numbered 0006 or above. `core/P3a-2` holds none above 0005. `P3a.md` line 26: "no migration of any kind in P3a". P1m and P4d-c have no branch with migrations today, so 0008 cannot be proven free for them.
- F5. `P2a.md` line 23 (Depends-on): P1m, P3a and all five P4d pull requests merge before P2a-1. LEAD ORDER 186 says "P2a's CREATE OR REPLACE TRIGGER file gets its own allow-list entry when P2a lands", so P3a-2 lands before P2a-1. Hence P3a-2 merges before P4b1-a, and the revision 6 branch "if P4b1-a merges first" cannot happen under the confirmed list (design M4 is right). ORDER 189 N-3's rule "whichever merges second" gives P4b1-a.
- F6. `_DEMO_STAGES` is in 78 `limits.py` line 32 and on `origin/core/P4a`, but not on `origin/core/P2a-1`, `origin/main` or `origin/core/P4b1`; `git log -S_DEMO_STAGES` finds it only in commit 77ace26 ("WIP P2a-1 ..."), which the current `core/P2a-1` no longer holds. `P2a.md` line 27: "P2a-1b" now says "P2a-1".
- F7. Code loaders in 78 and 79 `src/hadavin_sdk/`: `importlib.import_module` only in `backends/factory.py:39`, `actions/executor.py:37`, `tools.py:365`; `exec(compile(...))` only in `tools.py:389`. 78 `tools.py` lines 276-292 already define `_LOADERS` (13 loader names) and `_reach_problems` walks names, attributes, aliases, `ImportFrom` and `getattr` strings against it. My `ast` script applied that walk to every module of both snapshots except the three loader files: 0 hits; the attribute `.factory` is read only in `backends/factory.py:37`. So rule (c') is clean on today's code.
- F8. The factory `make` is bound in 78 and 79 `src/` only by the exact statement `from hadavin_sdk.backends.factory import make` (`cli.py:39`, `app.py:28`, `k1b/audit_sink.py:15`); nothing imports the factory module as an object. `cfg` is bound by `cfg = load_config()` (78 `cli.py:156`), `cfg = load_config(config_dir)` (78 `app.py:79`), or is a parameter (`_k1b(cfg, reg, args)`, `cli.py:287`).
- F9. 78 `scrub_settings.py` docstring: `tools.py` must not import `config.py` ("which pulls in the backends table ...: a repo test pins that"). So `tools.py` cannot import a list derived from `backends/table.py` at run time; the paid-module list it uses must sit in a light module (I chose `defaults.py`) and be kept equal to the derived set by a test.
- F10. Existing callers of `app.build(..., llm=...)` in 78 `tests/` and `demos/` pass `ScriptLLM` or `ScriptedLLM` objects only (`test_k5_tools.py:848`, `test_k3_pilot.py:643`); none passes a `NetworkLLM`. 78 `k1b/replay.py` lines 131-134 refuse a `NetworkLLM` object in every stage.
- F11. 79 `meter.py` lines 300-305: after an unknown reserve failure the meter calls `store.release_spend(rid)`; if that raises, it logs `"meter release after an unknown reserve failed: %s"` with the class name (readiness N5 is right: the ticket cited a prefix).
- F12. 78 `llm/fake.py`: `FakeLLM.chat` raises `UnknownRecording` (a `KeyError` subclass) when no recording file exists for the prompt; `REQUESTS_PER_CHAT = 1`, `max_attempts = 1`.
- F13. 78 `llm/protocol.py`: `USAGE_REASONS = ("absent", "invalid", "implausible_zero", "unpriced_class")`, `USAGE_FIELDS` starts with `"usage"`, `"input_tokens"`, `"output_tokens"`; `UsageMissing(ProviderError)`; `checked_count(value, field)`. 78 `models.py` `Reply.usage` builds `Usage(...)`, whose `__post_init__` raises `ValueError` on a non-int, negative or too-large count. So a B4 form can reach the wrapper only through a reply that skipped validation (`model_construct`, a stub, a kind outside the core).
- F14. 79 `store/memory.py` `reserve_spend` raises `NotFound` for an unknown run id and `ValueError` for another agent's run; on `origin/core/P2a-1` `set_kill_switch` refuses a label it does not accept (`LabelRefused`) and refuses a reset. 79 `tests/test_meter_unit.py:635` turns the switch on with `store.set_kill_switch(KillSwitch(on=True, by="t"))`.
- F15. 78 `llm/anthropic.py:37` `max_retries: 0`; `llm/bedrock.py:51` `total_max_attempts: 1` (design N3's pin values are right).
- F16. 78 `k1b/loop.py` `worst_case_usd` (lines 115-132) measures `len((system + _dumps(messages) + _dumps(tools)).encode("utf-8", "surrogatepass"))` and rounds once with `round_cost_up`.

## Findings, in severity order

### D-M1 [egm-design] Major: row FB-4 has no exception, yet the alert names `type(exc).__name__` and FB-T4 asserts an alert
- AI Suggestion: **PROPOSE FIX**, choosing a third option over the two the reviewer offered.
- The three options: (a) FB-4 sends no alert (like FB-1d) and returns the reply; (b) FB-4 alerts with a closed class name such as "UnusableUsage" and returns the reply; (c) the wrapper books R, raises `UsageMissing(reason, field)` (P4a-1's own class, closed reasons and fields, F13), alerts like FB-2 and does NOT return the reply.
- Chosen: (c). Why it is the safe one on the money path: (1) P4a-1's rule for the whole core is "a reply without usable counts is refused, never priced by a guess"; (c) keeps that one rule at both layers, (a) and (b) would let the meter layer accept what the kind layer refuses. (2) By F13, an FB-4 reply can only come from an object whose output skipped validation, so its content should not drive the next step of a run. (3) (a) books R silently, and the lock-out by repeated R bookings ("What this costs") would then reach an agent with no alert, against bible R215 (fail loudly). (4) (c) gives FB-2, FB-3 and FB-4 one path (book R, alert once, raise), so no booking at R from a failure lacks an alert, and the revision 6 sentence "re-raises the same exception" becomes true for FB-4 (the exception is the one the wrapper raised inside the hold). Cost: a provider answer is discarded and R stays booked; with the core kinds this never happens (they raise inside `chat()`, row FB-2).
- Edit applied: row FB-4 rewritten (refuse, alert, reasons and fields named, the four reasons stated); FB-T4 asserts `UsageMissing`, no returned reply, one alert with `error_class == "UsageMissing"` and `booked == R`; new mutant FB-M4b (the wrapper returns the reply). FB-2's alert sentence and "The failure alert" say how FB-4 gets its exception. `P4b1.md` BN-35: line 267 and B4 (line 287) gain the refusal.

### D-M2 [egm-design] Major: garbage `unknown_attempts` still books the maximum extra in `P4b1.md` lines 268 and 282
- AI Suggestion: **PROPOSE FIX** (verified by reading `P4b1.md` lines 268, 282 and 531).
- Edit applied (BN-35 only): line 268's private helper `_unknown_attempts(reply, count, attempts)` (garbage gives `count x (attempts - 1)`) is named superseded and not built; line 282's garbage clause is named superseded and removed from R4d-2; garbage is "not proven" and books `max(R, answered)` (row FB-9, FB-T9 garbage sub-row). The revision 6 BN-35 sentence "R4d-2's garbage and answered-part sub-rows ... run only with a proven count" is corrected to "answered-part sub-rows".

### D-M3 [egm-design] Major: SG-T11 rules (a') and (b') can still be bypassed
- AI Suggestion: **PROPOSE FIX** (F7, F8 verified every bypass form named; LEAD ORDER 189 N-2 adds the loader refusal).
- Edit applied: (b') is rewritten: the factory `make` is bound outside `backends/factory.py` only by the exact `from hadavin_sdk.backends.factory import make` (no `as`), the factory module is never bound as an object, `getattr(..., "make")` is reported, and `stage=` is exactly `cfg.environment` where `cfg` is a parameter or bound only from `load_config(...)` (this also closes design N2's `.environment` on a fake). New rule (c'): outside `backends/factory.py`, `actions/executor.py` and `tools.py`, no module names any loader in 78 `tools.py` `_LOADERS`, checked by the SAME walk as `tools.py` `_reach_problems` (moved into one shared function; reuse, not a second list); `.factory` is read only in `backends/factory.py`. That refuses `importlib.import_module` with a built string, an f-string or a variable. New row SG-T13 (ORDER 189 N-2): `actions/executor.py` `resolve` and `tools.py` `load_tool_module` refuse a paid kind module (or a submodule) as their first statement, and `_reach_problems` reports a pinned tool module that imports one. Because `tools.py` may not import the kind table (F9), the list is one constant `defaults.PAID_KIND_MODULES`, kept equal to the derived set by an SG-T13 sub-row. SG-T11 self-tests grow from 6 to 18 plants (design N2 included). New mutants SG-M20 to SG-M23, SG-M25, SG-M26.
- Interpretation of ORDER 189 N-2 (stated, default applied): the lead's words "must not be imported unless it is on the existing allow list / inside the package namespace" are read as "refuse a paid kind module name even when it is on the allow list". A reading "only names inside the `hadavin_sdk` namespace may load" would refuse every operator tool module, which lives outside the package (78 `tests/test_k5_tools.py:1236` loads `tests.fixtures.k5_tools`); the allow-list half is already true today (`resolve` refuses a name outside `check_modules`, `load_tool_module` is reached only for names on `tool_modules`). Listed as NEEDS LEAD N7-1 for confirmation only; the ticket is buildable as written.

### D-M4 [egm-design] Major: the "ONE list" omits line 213's prerequisites; dead branch; "0008 is fixed" not proven; FB-T6b hard-codes 0008
- AI Suggestion: **PROPOSE FIX** (F4, F5).
- Edit applied: the merge-order paragraph gains item (0) (P1m; P3a with P3a-2, PR73; P4d-a1, PR66; P4d-c), PR78 is one pull request per ORDER 189 N-1 with the item-to-commit mapping in body and CHANGELOG, and PR78's `_DEMO_STAGES` removal is placed (F6). A new "Migration file name" part: the file is `NNNN_spend_reservations_expired_guard.sql`, expected 0008 with today's facts (F4), number taken at the PR79 rebase; NO test hard-codes the number: tests find the file by its name ending and assert exactly one match. Row FB-6: the "if P4b1-a merges first" branch is removed; the P3a-2 allow-list entry is REQUIRED, added by P4b1-a under ORDER 189 N-3 (F5), with its one-line reason written; the allow-list sub-row of FB-T6b is required.

### R-M1 [egm-implementation-readiness] Major: the FB-T6b upgrade recipe cannot give its stated result
- AI Suggestion: **PROPOSE FIX** (F1, F2).
- Edit applied: the recipe is rewritten step by step: `pg_schema(migrated=False)` with `next(gen)` and `gen.close()`; the new file found by name ending; `_migration_files` patched to the list without it; `mig.migrate(dsn, reset_role=RESET_GROUP)` (required argument, constant from `tests/stop_state_helpers.py`); one reservation made by `reserve_spend` and turned `expired` by a direct UPDATE on the owner connection (the open-to-expired change 0006 allows), not by the sweep (its minimum age would make the test wait); the real list restored and `migrate` again returning exactly the new stem. Identity: the refusal UPDATEs run twice, on the test's owner connection and as the runtime role (`pg_schema(runtime=True)`, F2), each after asserting `session_replication_role = 'origin'` on that same connection (also answers design N8).

### D-N1 [egm-design] Nit: no assertion that refusals send no alert; wrapper shape; `KeyboardInterrupt` during reserve
- AI Suggestion: **PROPOSE FIX**. Every FB-T1 cause sub-row asserts the `on_failure_booked` spy saw 0 calls; "The failure alert" states the wrapper's shape (reserve outside the booking `try`, so a reserve failure, `KeyboardInterrupt` and `SystemExit` included, never builds an event; the alert in an outer `finally`, guarded so the original exception always propagates); new mutant FB-M1f (alert on a reserve failure).

### D-N2 [egm-design] Nit: SG-M17 wording; six plants; missing self-tests
- AI Suggestion: **PROPOSE FIX**. SG-M17 reworded to rule (a') ("reports only `import x` and misses `from x import Name`"); SG-T11 self-tests listed 1 to 18 (relative import, `from pkg import module`, `__import__`, `":make"` suffix string and `.environment` on a fake all included). The round 5 resolve's "five" is historical text and is not edited.

### D-N3 [egm-design] Nit: SDK-retry-off pin belongs with the counter
- AI Suggestion: **PROPOSE FIX** (F15). Pin moved from FB-T2 (P4b1-b) to FB-T9b (P4a-2); FB-T2 points to it.

### D-N4 [egm-design] Nit: rollback of the new migration
- AI Suggestion: **PROPOSE FIX** (F3). Row FB-6 states the file is not revertible by a code rollback, what older code does on a migrated database (refuses at `migrate`; an older `_close` gets the trigger's database error), and that undoing it needs a new forward migration. FB-T6b gains an old-code sub-row (a pin of 78 behaviour, no mutant).

### D-N5 [egm-design] Nit: `P4b1.md:106` lets a real settle correct an expired row "in either direction"
- AI Suggestion: **PROPOSE FIX**. BN-35 names line 106's last clause superseded by row FB-6.

### D-N6 [egm-design] Nit: a healthy slow call can be expired by P4b2-a's sweep
- AI Suggestion: **PROPOSE FIX**. New "What this costs" bullet with the numbers (orphan age at least 600 s; 2 x 10 x 60 s = 1,200 s; booked R, the safe side; P4b2-a sizes its sweep age).

### D-N7 [egm-design] Nit: SG-T7 and BN-18 item 3 silent on the demo stage
- AI Suggestion: **PROPOSE FIX**, choosing "refuse in every stage" (F10): a real kind then reaches `app.build` only through `make`, so the stage check and the SG-T3 start-up WARNING always apply, matching `_replay`; no existing test passes a `NetworkLLM`. SG-T7 gains a demo-stage sub-row; new mutant SG-M24 (the check runs only outside the demo stage).

### D-N8 [egm-design] Nit: FB-T6b must say it asserts `session_replication_role = 'origin'`
- AI Suggestion: **CONTEST** (partly). Revision 6 already says "after asserting `current_setting('session_replication_role') = 'origin'`". The wording is tightened under R-M1 so the assertion is made on each connection that runs an UPDATE; no other change.

### R-N1 [egm-implementation-readiness] Nit: `limits.py` hot-file order incomplete
- AI Suggestion: **PROPOSE FIX** (F6). Order is now `limits.py`: PR76 (P2a-1; "P2a-1b" is its old name), PR78 (removes `_DEMO_STAGES` only), P4b1-a, P4b1-b, P4c; same text in BN-35.

### R-N2 [egm-implementation-readiness] Nit: FB-T1e orphaned, no mutant, rounding unstated
- AI Suggestion: **PROPOSE FIX** (F16). FB-T1e moved into row FB-1's test column with N built by k1b's own measure and the exact rounding expression; one route with fractional micro-dollar prices; new mutant FB-M1g (`worst_case_micro` rounds down). The W definition keeps a pointer.

### R-N3 [egm-implementation-readiness] Nit: unwritten fixtures
- AI Suggestion: **PROPOSE FIX** (F12, F14). "Kill switch and stop state" gains the stub fixture (run row via `create_run`, kill switch via `set_kill_switch` with an accepted label after PR76); FB-T9 gains the usage numbers for the `measured` and answered-above-R sub-rows (W 27,360, R 164,160: answered 177,000 or 150,000; booked 204,360, 177,360, 177,000; overshoot 40,200, 13,200, 12,840; arithmetic: 4,000 x 3 + 11,000 x 15 = 177,000; 4,000 x 3 + 9,200 x 15 = 150,000); FB-T2's real-fake sub-row fails through `UnknownRecording` (empty recording folder).

### R-N4 [egm-implementation-readiness] Nit: FB-M9g is two mutants; "field reads 0" is wrong
- AI Suggestion: **PROPOSE FIX**. Split into FB-M9g (skip counting instead of raising: the plain-thread sub-row gets a reply with field `None` instead of `RuntimeError`) and FB-M9j (a plain integer in the `ContextVar`: the `copy_context` sub-row gets `None` instead of 1).

### R-N5 [egm-implementation-readiness] Nit: "13 causes" in the round 5 resolve; WARNING text is a prefix
- AI Suggestion: **PROPOSE FIX** for the WARNING text (F11): FB-T1d cites the full logged form. **DECLINE** editing the round 5 resolve (a closed historical report; the ticket's 15 is right, and this note records it).

## Tally
PROPOSE FIX 17 (5 Majors, 12 Nits; D-N8 and R-N5 partly), CONTEST 1 part (D-N8), DECLINE 1 part (R-N5, the historical report), ESCALATE 0. Remaining unaddressed: 0.

## Counts after editing (to be recounted by the builder by script)
- BN-17 test row ids: 17, unchanged (revision 7 adds sub-rows only).
- BN-17 mutant ids: 35 + FB-M1f, FB-M1g, FB-M4b, FB-M9j = 39; renamed 2, so 37 new. P4b1-b 24 (22 new), P4b1-a 7, P4a-2 8. 24 + 7 + 8 = 39.
- BN-18: 16 test rows (SG-T13 added; P4a-2 holds 14), 26 mutants (SG-M20 to SG-M26 added; P4a-2 holds 24, P4c-2 SG-M8, P4b1-b SG-M13).
- P4a-2 test rows from BN-17 and BN-18: 6 + 14 = 20. P4a-1/P4a-2 body mutant count 86 becomes 94, plus 24 BN-18 mutants built in P4a-2.
- `P4b1.md` BN-35 "new in this ticket": -b 23 (revision 6's 20 + FB-M1f, FB-M1g, FB-M4b) + -a 7 = 30.

## NEEDS LEAD (new)
- N7-1. Confirm the reading of ORDER 189 N-2: both loaders refuse a PAID KIND module name (and its submodules) even when it is on the operator's allow list; they do NOT refuse every name outside the `hadavin_sdk` namespace, because operator tool modules live outside it (78 `tests/test_k5_tools.py:1236`, `tests.fixtures.k5_tools`). Default written into the ticket: the paid-kind refusal. Recommended: confirm.
