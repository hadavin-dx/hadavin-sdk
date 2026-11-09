# P4a rev 5 plan review round 5, implementation readiness (0B/5M/6N). Saved by cloud session.

IMPLEMENTATION READINESS, plan review round 5, P4a.md revision 5 (BN-17/18/19) and P4b1.md BN-35. Mode: REVIEW. Money path, no round cap.

VERDICT: not ready to build. 0 Blockers, 5 Majors, 6 Nits. The test tables are mostly precise, and the counts match their tables. The gaps are in the merge order, one unspecified callback interface, the upgrade-test fixture, and the thin setups for FB-T1 and FB-T3. A builder would have to decide each of these themselves.

WHAT I DID NOT CHECK (read this first)
- I read P4a.md lines 600-718 only: BN-15, BN-16, BN-17, BN-18 and BN-19. I did not read P4a.md lines 1-599. That covers the line 3 revision log, the body mutant count "86 becomes 92", the "Answer first" sections, and what P4a-1 and P4a-2 each contain. The statement "line 3 now has revisions 4 and 5" is unchecked.
- I read P4b1.md lines 1-128, 255-286 and 520-531 only. I did not read BN-2, BN-3, BN-4, BN-9 or BN-10 (lines 467-482), or BN-30. So I did not check "-b test rows stay 28" or "four constants" against BN-9.
- I did not read `origin/main`. This sandbox has no git, and I read no main tree. I did not verify P3a's `late_files` rule, `store/migration_numbers.py`, or the claim that main has only migrations 0001-0005. I only saw the snapshots: 78 has 0001-0007 and 79 has 0001-0006.
- I ran no code, no tests and no mutants.
- I did not read snapshot 78 `registry.py`, `config.py` `_cross_checks` or `app.py` bodies beyond the grep hits. I did not check PL67 to PL79 arithmetic beyond what is listed below.

VERIFIED
- Test rows in BN-17: FB-T1 to FB-T10 (10) plus T5b, T5c, T6b, T7b, T7c, T7d, T9b (7) is 17. By package: P4b1-a has 6 (T5, T5b, T5c, T6, T6b, T10), P4b1-b has 5 (T1-T4, T9), P4a-2 has 6 (T7, T7b, T7c, T7d, T8, T9b). 6+5+6 = 17.
- Mutants in BN-17: P4b1-b has 19 (M1a-e = 5, M2a-h = 8, M3, M4, M9a-d = 4). P4b1-a has 7. P4a-2 has 6 (M7a-d, M9e, M9f). Total 32, with 2 renamed, so 30 new.
- BN-18: 15 SG-T ids (T1-T12 plus T6b, T6c, T6d) and 16 SG-M ids. The P4a-2 split of 13 rows and 14 mutants is correct. The P4a-2 total of 6+13 = 19 is correct.
- BN-35 "25 new" is correct: 18 in -b (FB-M1a-e, M2c-h, M3, M4, M9a-d = 17, plus SG-M13) and 7 in -a.
- Arithmetic checks out: W = 4000x3 + 1024x15 = 27,360. R = 2x3xW = 164,160. A US$5 day cap gives 30 failures. A US$50 month cap gives 304. US$189 gives 1,151. A US$0.50 run cap gives 3.
- FB-T7c: 2 x 10 = 20 = CHARGE_FALLBACK_REQUESTS (2) x CHARGE_FALLBACK_ATTEMPTS (10).
- Symbols found in the snapshots:
  - 78: `k1b/loop.py` `_charge_factor` (139), `_count_or` (135), `worst_case_usd` (115), `_worst_case_of_call` (147).
  - 78: `llm/common.py` `request_bound` (157), `NetworkLLM._chat` (241), `_retry` (252), `chat` (227).
  - 78: `llm/retry.py` `with_retry` (83); `llm/fake.py` `REQUESTS_PER_CHAT = 1` and `max_attempts = 1`.
  - 78: `defaults.py` `CHARGE_FALLBACK_REQUESTS`, `CHARGE_FALLBACK_ATTEMPTS`, `MAX_USAGE_TOKENS_PER_CLASS`; `errors.py` `ConfigError`; `deferred.py` `LIVE`.
  - 78: `tests/conftest.py` `qualify`; `tests/test_k3_pilot_env.py` `pilot_cfg`; the `test_c13b/c/d/d2/f/j` tests in `tests/test_usage_classes.py`.
  - 78: `guard/http.py` `_STUCK` (97); the `make()` call sites at `cli.py` 177, 296, 297 and `app.py` 165, 168.
  - 79: `meter.py` `_reserve_failure` (275), `Hold.record` (156), `_exit` (379), `_failed` (418).
  - 79: `limits.py` callbacks; `store/memory.py` `_close` (326); `store/postgres.py` `_LOG = "hadavin_sdk.store"`; migration 0006 trigger function.
  - 79: `llm/fake.py` declares neither `REQUESTS_PER_CHAT` nor `max_attempts`.
- Behaviour claims confirmed in 79:
  - `_reserve_failure` follows the release table: StoreBusy and unknown errors release, other codes do not.
  - `_exit` retries only on `store_busy`.
  - `memory._close` refuses only settled and released rows, so an expired row is still accepted today (FB-6's premise).
  - `store/memory.py` has no logger today.
- Symbols that do not exist yet, as the ticket says: `reserved_factor`, `Limits.on_failure_booked`, `PaidKindRefused`, `RefusedLLM`, `LLMRefused`, `DEMO_STAGE`, `Reply.unknown_attempts`, `with_retry(on_retry=)`, `make(stage=)`, `METER_MIN_MICRO`.

FINDINGS

**1. MAJOR. Merge order among PR78, PR79, P4a-1, P4a-2, P4b1-a and P4b1-b is not unambiguous.**
Scope: P4a.md:213 (Depends-on), :608 (BN-17 header), :633 (FB-6), :642, :661, :672. P4b1.md:531 (BN-35).
- Four different statements exist. Line 213 says "P4a-1, P4a-2, P4b1-a, P4b1-b, nothing between", with P2a-1 before P4a-1. Line 608 says "P2a -> P4a-2 -> P4b1-a -> P4b1-b is load-bearing". Line 633 says "0008 if PR78 merged first". Line 661 says P4a-2 builds the gate "on the PR78 branch".
- Nowhere is it stated what PR78 and PR79 are. Is PR78 = P4a-1 plus P4a-2 already built? Is PR79 = P4b1-a already built? Do P4a-2 and P4b1-a add commits on top of those branches, or rebuild from main?
- Snapshot 78 already holds P4a-1 content (`MAX_USAGE_TOKENS_PER_CLASS`, `build_usage`) and 0007. Snapshot 79 holds P4b1-a content (`meter.py`) and no 0007. So the two trees diverge from P4d, not from each other.
- `limits.py` is edited by both: 78 has stop-state (`_DEMO_STAGES`), 79 has hold and callbacks. Who rebases onto whom is not stated.
- Failure scenario: a builder starts P4b1-a on 79. It lacks 0007, so the "highest on merge base" rule gives 0007_x. PR78 then merges with its own 0007_kill_switch_guard. Two files are numbered 0007 and P3a's check refuses the ledger. The ticket says "0008 if PR78 merged first" but never says PR78 must merge first.
- Fix: one ordered list with an explicit branch-to-package mapping. For example: "P2a-1, then PR78 (= P4a-1 + P4a-2), then PR79 rebased on it (= P4b1-a), then P4b1-b". It should also state that the file number is fixed at 0008 and that 0007 is PR78's.

**2. MAJOR. The `Limits.on_failure_booked` interface is undefined.**
Scope: FB-2 (P4a.md:628), BN-17 "Who builds what" (:651), P4b1.md:531, BN-19 item 74.
- FB-2 says "with the agent id, run id, reservation id, R and the error class name". It gives no parameter names, order, or types.
- It does not say whether R is a `SpendMicro` or an int, whether the callback takes one object or five arguments, or whether `run_id` may be None.
- The test asserts "called exactly once with R and the error class name". Item 74 makes P4c-2 write a callback against this interface.
- Failure scenario: P4b1-b picks `cb(agent, run, rid, SpendMicro, "KeyError")`. P4c-2 later wraps it with another shape. FB-T2's spy cannot pin the shape.
- Also, `limits.py` is a hot file ordered P2a-1b, P4b1-a, P4c (P4b1.md:52). P4b1-b now edits it too, and neither the P4b1 files list (:273, "NOT changed...") nor BN-35 updates the file list or the hot-file order.
- Fix: give a frozen dataclass or exact signature, and add `limits.py` to -b's CHANGE list with its place in the order.

**3. MAJOR. FB-T1 and FB-T3 lack a precise setup for several sub-rows.**
Scope: FB-1 (:627), FB-3 (:629).
- FB-T1 says "one sub-row per cause with a counting stub ... the named error raised". FB-1 lists about 11 causes separated by semicolons. The exact error class is not given for each. "Route name missing" is only in P4b1:270 (ValueError). "No scope" is MeterError.
- Several causes have no construction recipe or numbers. A price not whole in micro-dollars (config already refuses more than 6 decimals, so how is a Route built?). A prompt over the tier bound (the constant name is not given; P4b1 says `METER_MAX_PROMPT_TOKENS` 100,000). R above MAX_USD x 10^6 (which price and bytes?). KeyboardInterrupt/SystemExit during reserve, and `request_bound` TypeError vs ValueError (one sub-row or two?).
- FB-T3 says "a monkeypatched cost helper raises ValueError". The target symbol is not named. Is it `round_cost_up`, `SpendMicro.ceil_cost`, or a private `_cost` in the not-yet-written `llm/metered.py`? The builder invents the seam, and the mutant FB-M3 depends on it.
- FB-T1b gives no synchronisation spec: the barrier or event, and how "exactly 3 enter" is asserted.
- FB-T2 uses the W example "hand-computed" but does not say the fixture is the 4,000-byte, prices 3 and 15, max_tokens 1,024 case. It also does not say how the 4,000 bytes are built, given P4b1 framing (16) and document factor (3) rules. The conversion from bytes to tokens (PROMPT_BYTES_PER_TOKEN, assumed 1) is not stated. 27,360 therefore holds only if there is no framing. The builder must decide.
- Fix: a table of cause, how to trigger it, expected exception class, and expected counters, plus the exact fixture for W.

**4. MAJOR. The new-migration test and fixture are under-specified.**
Scope: FB-6 (:633), FB-T6b, FB-M6d, BN-35.
- The file name suffix is "0008_..." with no name. The builder decides.
- The upgrade sub-row says "a database migrated with the 79 text of 0006 and recorded in `schema_migrations`". It does not say where the old text comes from: a literal copy in the test, or `git show`? Is 78's 0006 byte-identical to 79's? Not stated.
- The sub-row also does not say how the test populates the `schema_migrations` row, whether 0007 must be applied in between, or which role performs the "direct UPDATE as the store's own role".
- Existing tests that mention migrations (`tests/test_k2_migrations.py`, `test_p2_postgres.py`, `test_k5_fixes2.py`, `test_k5_round10_postgres.py`, plus `store/migrate.py`) were not assessed for breakage when a new file is added. `check_grants` and `check_ledger` apply (`test_k2_migrations.py` lines 33-53). "Passes P3a's file and statement rules" is unverified; I could not read P3a's rules.
- Fix: name the file, state the source of the old 0006 text, and list which migration tests must be re-run.
- The Postgres half skips without `HADAVIN_TEST_PG_DSN`. That is flagged correctly, but nothing says what the evidence runner must check to show the sub-row ran.

**5. MAJOR. The P4b1 body and BN-35 still leave contradictions the builder must resolve.**
Scope: P4b1.md:266, :267, :268, :270, :273, :283; BN-35.
- Line 267 says garbage usage is `h.record(None)`. FB-4 requires `h.record(None, measured=False)`. BN-35 does not list line 267 as superseded.
- FB-9's "field proven" branch says `h.record(answered + u x W)` and does not say what `measured` is. The `measured=(answered > reserved)` rule is in line 266, which BN-35 supersedes. Failure scenario: a proven count with answered above the sizing triggers `on_overshoot` or not, depending on the builder's guess. No FB-T9 sub-row asserts `on_overshoot` in the proven branch, so a mutant here has nothing to kill it.
- BN-35 says line 273 stays as written. It still says "five constants" and CHANGELOG sentences that predate R = count x attempts x W. I could not confirm the BN-9 "four constants" statement against the body.
- BN-35 still cites "PENDING LEAD 69 (fresh plan review round 4 of P4a BN-17 revision 4)". It should say round 5 of revision 5.

**6. NIT. Choices left to the builder.**
- FB-T1e depends on "either computes `worst_case_micro` by calling `worst_case_usd`, or keeps its own formula and adds FB-T1e". Pick one.
- The retry-count carrier is "for example a contextvars.ContextVar ... the builder picks the form". FB-T9b would catch a wrong choice, but the form is still left open.
- The new migration name is left open (finding 4).

**7. NIT. Mutants are described as behaviours, not as patches.**
- FB-M2d, FB-M3, FB-M4, FB-M9b and the like have no location, because `llm/metered.py` does not exist yet. Each is killable by its named test row, but the builder writes the planted diff. That is acceptable only if the evidence file lists each planted diff.
- FB-M5b ("a new caller of `Meter.settle` in `runtime/`") needs the builder to choose a file.

**8. NIT. Wording and loose ends.**
- FB-1's books cell says "0" with one named exception (FB-T1d). FB-T1d says the best-effort release fails with `StoreBusy`, so `MeterUnavailable` carries `store_busy`. The expected code string is not stated.
- The logger name `hadavin_sdk.meter` for the WARNING in FB-2 is unverified; I did not find the logger definition in 79 `meter.py`.
- FB-10 and FB-T10 are "regression pin of P4d" and need the builder to name the P4d row, as stated.

**9. NIT. FB-7 changes `run_case` to a required `route_prices` keyword.**
- The 78 test `_drive` and `_booked` helpers default `route_prices=ROUTE` and pass `None` explicitly in the two named c13f tests. Other callers of `run_case(...)` in tests and demos were not grepped.
- Ask the builder to list them by script, as the ticket does for `make`.

**10. NIT. Counts in the prose.**
- Everything above matches. The only mismatch is the stale reference to PL69 (finding 5). BN-17's "FB-T6b is no longer a pin" and "FB-T1 sub-rows a to d" are consistent.

Files read: /home/user/hadavin-sdk/handover/tickets/P4a.md (lines 66-68, 211-213, 567-569, 600-718), /home/user/hadavin-sdk/handover/tickets/P4b1.md (1-128, 255-286, 520-531), /home/user/hadavin-sdk/handover/TICKET-TEMPLATE.md, /home/user/hadavin-sdk/handover/reviews/P4a/round4-resolve.md, and snapshots /home/user/build/snap/78-4a0976f and /home/user/build/snap/79-8cc2021 (greps, `meter.py` 225-435, `store/memory.py` 320-400).