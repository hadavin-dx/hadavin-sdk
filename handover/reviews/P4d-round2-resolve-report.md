# Goldfish Annotated Review Report (resolve, round 2)

Status: findings categorised; the author applies them (ticket revision 4)

**Target:** `handover/tickets/P4d.md` (revision 3). Findings: `handover/reviews/P4d-round2-adversarial.md`, `handover/reviews/P4d-round2-correctness.md`. Counts: 34 findings, all PROPOSE FIX (none contested, none escalated: the lead answered the open questions in `LEAD-ORDERS.md` order 5 / amendment A14).

## Lead decisions that apply (order 5)
Order 5 (f): add the terminal status `expired` and `list_open_reservations` NOW, while the Protocol is open. (b) / A14: P4d-c is the lock-in guard. (g): fix every blocker and major, or contest with evidence in the disposition file. A11 stands: money SQL in P4d.

Note on the gate (skill Step 4): the owner told the cloud session to follow `LEAD-ORDERS.md` (allowed actions only) and to run the resolve step; the auto-accept path is taken for every PROPOSE FIX, as in round 1.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`egm-design`] - Severity: Blocker (finding id A1, adversarial)
*   **Affected Scope:** P4d-b "Money SQL rules" 1 vs 2 and the GLOBAL LOCK ORDER sentence of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The ticket contradicts itself. The stated order is reservation, run, day, month. Rule 1 (reserve) lists the counters as day, month, then run: "per counter ... `spend` ... `spend_month` ... and, if `run_id`, `UPDATE runs`". It also runs the "ensure counter rows exist" inserts before the run update. Rule 2 (settle) uses run, day, month. A builder following the recipe text builds an inverted lock order.
*   **Rationale:** evidence: `postgres.py:416-431` `add_spend` locks day then month. The ticket text for reserve (day, month, run) differs from its text for settle (run, day, month).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b "Money SQL rules" 1 vs 2 and the GLOBAL LOCK ORDER sentence
    *   Change: Rewrite rule 1 as: insert the reservation, `UPDATE runs` (when `run_id` is given), ensure the day and month rows exist, `UPDATE spend` (day), `UPDATE spend_month`. State one total order for all five methods plus `add_spend`/`add_cost`. Add a deadlock stress row with `run_id` set (B4 v currently uses "same agent and cap" only).

### [Issue 2] [`egm-design`] - Severity: Major (finding id A2, adversarial)
*   **Affected Scope:** P4d-a `check_usd`, `max_decimals` of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `x.normalize()` rounds to the context precision (28 digits) before stripping zeros. I reasoned this from CPython's `_fix`; I did not run it. A value such as `Decimal("1.0000000000000000000000000000001")` (31 decimals) normalizes to `1`, so exponent 0 passes `max_decimals=6` (and 8). The edge table has no input longer than 28 digits.
*   **Rationale:** evidence: The ticket's own verified facts: "`Decimal("1E+22") + Decimal("0.000001")` is silently rounded at default precision".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a `check_usd`, `max_decimals`
    *   Change: Check scale without context rounding, for example `x == x.quantize(Decimal(1).scaleb(-n), context=Context(prec=60))`, or inspect `as_tuple()` digits and strip trailing zeros by hand. Run the arithmetic in a local high-precision context. Add 29-, 40- and 1000-digit rows to the edge table and a mutant "validator uses default-context `normalize`".

### [Issue 3] [`egm-design`] - Severity: Major (finding id A3, adversarial)
*   **Affected Scope:** Error rule, `@_writes`, money SQL of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Nothing sets `lock_timeout` or `statement_timeout`. Every call holds the process-wide `self._lock` for its whole duration, on one connection.
*   **Rationale:** evidence: `postgres.py:197`, `postgres.py:359`; `postgres.py:146` sets only `connect_timeout`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Error rule, `@_writes`, money SQL
    *   Change: `SET LOCAL lock_timeout` (a few seconds) in every money transaction. Map `LockNotAvailable` (55P03) to `StoreBusy`. Test it with an admin lock that is never released. Also decide how `is_connectivity_error` classifies 55P03 and 57014: both are `OperationalError`, so they currently count as "unreachable".

### [Issue 4] [`egm-design`] - Severity: Major (finding id A4, adversarial)
*   **Affected Scope:** `reserve_spend` step 1, kill switch with `FOR SHARE` of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The share lock on the kill-switch row is held until the reservation commits. `set_kill_switch` is an UPDATE and conflicts with `FOR SHARE`. The safety control therefore waits behind every in-flight reserve, including one blocked on a counter lock (A3).
*   **Rationale:** evidence: `postgres.py:457` (upsert of the kill switch); ticket rule 1.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: `reserve_spend` step 1, kill switch with `FOR SHARE`
    *   Change: Use `FOR KEY SHARE`, which does not conflict with a non-key update, or read the switch without a lock and accept the documented race. Add a test that `set_kill_switch` completes while a reserve is blocked.

### [Issue 5] [`egm-design`] - Severity: Major (finding id A5, adversarial)
*   **Affected Scope:** `sweep_spend_reservations`, `settle_spend`, `release_spend`, rollback procedure of `handover/tickets/P4d.md`
*   **Discrepancy Description:** (a) The sweep can only settle at the reserved worst case. A crashed call that never reached the model keeps its reserved amount in the day, month and run counters until nothing can reduce it. Nothing releases it. (b) The reservation id is random and lost in the crash, and there is no lookup by `run_id` or `agent_id`, so the caller cannot find the id to release it. (c) A swept row is `settled` with `settled_usd = reserved_usd`. P4b2 cannot tell a measured settlement from a guess. (d) A late real `settle_spend` after a sweep (or a late `release_spend`) silently returns the sweep's result, so the actual usage is discarded and the caller gets no signal.
*   **Rationale:** evidence: Ticket: `older_than_s` int >= 1, "settles each at its reserved amount". Memo-2 line 30 requires a floor of "2x call deadline + 5", but the store takes any value >= 1. Memo-2 gap 10 asks for the release/settle distinction.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: `sweep_spend_reservations`, `settle_spend`, `release_spend`, rollback procedure
    *   Change: Add a terminal status `expired` (status CHECK, trigger and model change now, while the Protocol is still open). Add `list_open_reservations(agent_id=None, run_id=None, limit)` so a run's cleanup can release. Decide whether a late `settle_spend` on an `expired` row may correct downward once. Return or flag "this call was not the first".

### [Issue 6] [`egm-design`] - Severity: Major (finding id A6, adversarial)
*   **Affected Scope:** P4d-a `require_backend` and the session-end check vs A4 "Memory: skip" of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Three contradictions. (1) The check "fails the run when any `tests/contracts` test was skipped" covers the whole directory, but that directory also holds the anchor, llm, secrets, signer, sources and capabilities contracts. `skip` or `importorskip` appears in `test_llm.py`, `test_secrets.py`, `llm_wire.py` and `detectors.py`. Under `CI=true` this red-lights unrelated optional kinds. (2) A4 memory is "skip with reason not applicable", yet any skip fails the run. (3) Postgres-only rows (privilege, process, B8 schema) mean "fewer `[postgres]` than `[memory]` store tests" can be true or false for the wrong reasons.
*   **Rationale:** evidence: `tests/contracts/kinds/store_postgres.py:22-25`; grep count: skips in 5 files under `tests/contracts`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a `require_backend` and the session-end check vs A4 "Memory: skip"
    *   Change: Scope the check to the `store` and `store_pair` fixtures. Use an explicit marker or registry for "backend-specific by design" tests, and count per row (the same row id must appear for both backends or be on a named exception list). Drop skips on memory in favour of not parametrising.

### [Issue 7] [`egm-design`] - Severity: Major (finding id A7, adversarial)
*   **Affected Scope:** Order of work: "c may run in parallel with a (different files)" of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Both sub-tickets change `tests/contracts/kinds/store_postgres.py`: a for `require_backend`, the pair and the "behind schema" builder, c for `pg_driver`. c also calls a's `require_backend`. c also touches six test files that P4d-a rows and P3b share. It is not parallel-safe, and it is not independent of a.
*   **Rationale:** evidence: Ticket header "Order inside P4d"; P4d-c "Files".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Order of work: "c may run in parallel with a (different files)"
    *   Change: Make c depend on a, or move `pg_driver` and `require_backend` into a separate new module (`kinds/pg_driver.py`) owned by c.

### [Issue 8] [`egm-design`] - Severity: Major (finding id A8, adversarial)
*   **Affected Scope:** P4d-b Security, negative tests; P4d-c `pg_driver` of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `pg_driver` offers only `connect_admin`. The negative-privilege tests need a runtime-role raw connection, and the ticket does not say how a test gets one. The CI DSN is a superuser or an owner (it migrates the schema). A "DELETE fails with `InsufficientPrivilege`" test run on the wrong connection raises nothing and the test fails, or a test that expects only "some error" passes for another reason. The mutant "grant removed" is not in the plan.
*   **Rationale:** evidence: Ticket: "runtime role, real statements"; `pg_schema(runtime=True)` yields the runtime DSN only inside fixtures.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b Security, negative tests; P4d-c `pg_driver`
    *   Change: Provide `connect_runtime(...)`. In every negative test assert `current_user`, `rolsuper = false` and `rolinherit`/membership of the owner first. Expect the exact SQLSTATE or exception class. For the trigger, assert the RAISE message separately from the CHECK errors. Add the mutant "`GRANT DELETE` given".

### [Issue 9] [`egm-design`] - Severity: Major (finding id A9, adversarial)
*   **Affected Scope:** P4d-a scope, "no new money SQL" of `handover/tickets/P4d.md`
*   **Discrepancy Description:** P4d-a is labelled "no new money SQL" but changes `add_spend`/`add_cost` (rejects values, so legitimate callers could now fail), puts a retry-on-class-40 wrapper over EVERY write, validators on 18 write paths and an id grammar on every key. It also adds harness machinery.
*   **Rationale:** evidence: `models.py:23`, `agent_loop.py:466` (conforming); the ticket's own "UNVERIFIED" on agent ids.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a scope, "no new money SQL"
    *   Change: Split P4d-a into a1 (harness: pair, `require_backend`, session check, recording proxy) and a2 (validators, `@_writes`, existing-method fixes, which count as a money pull request). Restrict retry to 40001/40P01 and never retry add-style writes without a key.

### [Issue 10] [`egm-codebase-details`] - Severity: Major (finding id C1, correctness)
*   **Affected Scope:** P4d-b "Money SQL rules" 1 vs 2 and the GLOBAL LOCK ORDER sentence of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The ticket contradicts itself on lock order. The header says reservation, then run, then day, then month, and the settle rule (2) follows it. But `reserve_spend` (rule 1) is written as day UPDATE, then month UPDATE, then run UPDATE. Reserve and settle on a reservation with a `run_id` can therefore deadlock. Reserve holds day and waits for run. Settle holds run and waits for day. Mutant b15 and test B4(v) only catch this by luck, and retries hide it as `StoreBusy`. The error precedence for `SpendCapExceeded.which` when several caps fail is also unstated.
*   **Rationale:** evidence: Ticket rule 1 order is day, month, run. Rule 2 says "run, day, month in that order". memo-3-store.md line 19 says "one lock order (run counter first, then agent)".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b "Money SQL rules" 1 vs 2 and the GLOBAL LOCK ORDER sentence
    *   Change: Reorder rule 1 to reservation row, then the "ensure counter rows" inserts, then run UPDATE, then day, then month. Keep the ensure-rows step before the run lock. If it moved after the run lock it could wait on another transaction's uncommitted counter insert while that transaction waits on the run row, which is a new deadlock. Write the ensure-rows step into the lock-order sentence. State the order in which `which` is reported.

### [Issue 11] [`egm-codebase-details`] - Severity: Major (finding id C2, correctness)
*   **Affected Scope:** P4d-a Interface, `require_backend` and session-end check of `handover/tickets/P4d.md`
*   **Discrepancy Description:** As specified, the session-end check fails green runs. (a) It fails on "any `tests/contracts` test skipped", but contracts hold a legitimate skip: `tests/contracts/test_llm.py:95` skips for bedrock. The ticket's own A4 memory row also says "skip, not applicable". (b) "A registered store kind never ran any test" and "fewer postgres than memory tests" would fire in the CI step `pytest -m perf` (`ci.yml:94`) and in any `-k` or partial run. That run loads `tests/contracts/conftest.py` but runs no store test.
*   **Rationale:** evidence: `test_llm.py:93-95`; `ci.yml:84-94`; `tests/contracts/conftest.py` is loaded at collection.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a Interface, `require_backend` and session-end check
    *   Change: Scope the check to skips that come from `require_backend` (a marker or a reason prefix). Run it only when at least one `store` or `store_pair` test was selected. Do not use `pytest.skip` for the memory-variant of A4. Either leave the memory variant out of the run, or use a skip reason that the check ignores.

### [Issue 12] [`egm-codebase-details`] - Severity: Major (finding id C3, correctness)
*   **Affected Scope:** Header "Order inside P4d"; P4d-c of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The claim "c may run in parallel with a (different files)" is false. P4d-a and P4d-c both change `tests/contracts/kinds/store_postgres.py`. P4d-c's `pg_driver` calls P4d-a's `require_backend`, so c depends on a. P4d-c also changes `tests/test_p2_postgres.py` and `tests/test_k2_migrations.py`, and P4d-b edits `test_p2_postgres.py:290` and possibly the `TABLES` entry. STUDIO-RULES and plan rule 10 forbid two packages on one file at once.
*   **Rationale:** evidence: Ticket P4d-a "CHANGE kinds/store_postgres.py"; P4d-c "pg_driver in kinds/store_postgres.py"; `test_p2_postgres.py:290` is cited by P4d-b.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Header "Order inside P4d"; P4d-c
    *   Change: State the order as a, then b, then c (or a, c, b), and add a Depends-on line to P4d-c. Drop the "parallel" claim.

### [Issue 13] [`egm-codebase-details`] - Severity: Major (finding id C4, correctness)
*   **Affected Scope:** P4d-a, P4d-b "Tests" and "Security" vs P4d-c guard rule 3 of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The new a and b tests need raw driver access. Examples: an admin connection holding `FOR UPDATE`, runtime-role `UPDATE`/`DELETE` that must fail with `InsufficientPrivilege`, and 8 `multiprocessing` workers. They are `test_store_atomic.py`, `test_store_hostile.py` and `test_store_reserve.py`. `pg_driver()` only arrives in P4d-c. Guard rule 3 then bans psycopg in every test file except `kinds/store_postgres.py`, and P4d-c's conversion list covers only the six old files. Either a and b import psycopg directly (the P4d-c guard then fails) or the ticket needs helpers earlier.
*   **Rationale:** evidence: P4d-c "Guard rules (3)" and "CHANGE the six test files"; P4d-a/b Tests rows A2, A5, B4.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a, P4d-b "Tests" and "Security" vs P4d-c guard rule 3
    *   Change: Put the admin/runtime connection helpers and the `errors` namespace in `kinds/store_postgres.py` in P4d-a, so a and b never import psycopg. Alternatively list the new a/b files in P4d-c's conversion scope. Either way, say which.

### [Issue 14] [`egm-codebase-details`] - Severity: Major (finding id C5, correctness)
*   **Affected Scope:** P4d-b "Tests" FAIL-BEFORE; P4d-a FAIL-BEFORE of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The template asks for fail-before on an assertion. Every B row fails on ce70eb5 with `AttributeError` (and with `NotImplementedError` in the stub commit). That is an error, not an assertion. The ticket admits it is weak. The real assertion-level fail-before is B8(d): `missing_methods` of an old custom store would return `[]` on ce70eb5. Several P4d-a fail-before items also cannot fail on an assertion. The CI-without-DSN item would show as SKIPPED, because `pg_schema` raises `Skipped`. The `check_usd`, `check_step_name` and `require_backend` items raise `ImportError`.
*   **Rationale:** evidence: `store_postgres.py:23-24`; `protocol.py:151-160`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b "Tests" FAIL-BEFORE; P4d-a FAIL-BEFORE
    *   Change: Write each test against the existing ce70eb5 API. For the CI case, catch `Skipped` and assert on it. Label every B row "new feature; killed by mutants". Name B8(d) as the real assertion fail-before.

### [Issue 15] [`egm-design`] - Severity: Nit (finding id A10, adversarial)
*   **Affected Scope:** `sweep_spend_reservations`, `limit` and `older_than_s` of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `limit` has no validation. Memory slices `[:limit]`, so a negative `limit` returns "all but the last" silently, while Postgres errors (`LIMIT must not be negative`). `limit=0` and a huge `limit` also differ. `older_than_s` must be "an int", but `True` is an int; a huge int overflows `make_interval`.
*   **Rationale:** evidence: Ticket interface only states `older_than_s` int >= 1.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: `sweep_spend_reservations`, `limit` and `older_than_s`
    *   Change: `check_int(x, lo, hi)` with `type(x) is int`, `limit` in 1..1000; add them to the edge table.

### [Issue 16] [`egm-design`] - Severity: Nit (finding id A11, adversarial)
*   **Affected Scope:** `check_text` of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Scope is "JSON-bound fields". Plain TEXT columns (reasons, tool names, messages, `reason_code`) are not covered. NUL in a TEXT column: Postgres refuses it (DataError, mapped to `ValueError`), memory accepts it. A lone surrogate in TEXT gives a client-side `UnicodeEncodeError` that is not caught by `@_writes`.
*   **Rationale:** evidence: Ticket hostile-values paragraph says "in a text value" without naming the fields.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: `check_text`
    *   Change: Run `check_text` over `model_dump()` of every model, all str fields, in both stores.

### [Issue 17] [`egm-design`] - Severity: Nit (finding id A12, adversarial)
*   **Affected Scope:** 0006 DDL of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `agent_id` and `run_id` have no CHECK, while the PK has one. Python-side only, so a direct runtime-role INSERT can store anything. No FK from `run_id` to `runs`. `day` is unbounded (the caller can book against year 0001 or 9999 and create rows in `spend`, which the runtime cannot delete). A bad `run_id` row makes settle's run UPDATE find 0 rows and roll back, so the reservation stays open until swept.
*   **Rationale:** evidence: Ticket DDL; GRANTS has no DELETE for `spend`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: 0006 DDL
    *   Change: Add the same grammar CHECKs and `day` bounds; consider `REFERENCES runs`.

### [Issue 18] [`egm-design`] - Severity: Nit (finding id A13, adversarial)
*   **Affected Scope:** P4d-b Security: "a compromised runtime cannot rewrite `reserved_usd` ..." of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Overstated. The runtime role has `UPDATE` on `spend`, `spend_month` and `runs`, so it can zero the counters directly. The trigger protects the ledger rows, not the caps. The ticket gives the trigger no honest scope statement.
*   **Rationale:** evidence: `migrate.py:53-54` (`spend`, `spend_month` are `_RW`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b Security: "a compromised runtime cannot rewrite `reserved_usd` ..."
    *   Change: State the limit plainly in the ticket. Say where the caps live (P4b1), and list the counters as the trust boundary. Test only what the trigger really guarantees.

### [Issue 19] [`egm-design`] - Severity: Nit (finding id A14, adversarial)
*   **Affected Scope:** Trigger definition of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `BEFORE UPDATE` only. A role with INSERT can insert a row directly as `status='settled'` (CHECKs allow it). The trigger does not fire on a `session_replication_role = replica` session by a superuser; that is out of scope but is not stated.
*   **Rationale:** evidence: Ticket DDL.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Trigger definition
    *   Change: Add `CREATE TRIGGER ... BEFORE INSERT` forcing `status='open'`, `settled_*` NULL, or document the choice. State that the owner/superuser are outside the model.

### [Issue 20] [`egm-design`] - Severity: Nit (finding id A15, adversarial)
*   **Affected Scope:** P4d-c guard of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `pg_driver()` returns `sql`, `errors` and the live admin connection, so the test files can reach psycopg through them. c5 only checks that the namespace has no `connect`, `Connection` or `Error` attribute. The planned detections are AST-based on `import`, `importorskip`, `import_module`/`__import__` and an attribute named `psycopg`. A string key `sys.modules["psycopg"]`, `from tests.contracts.kinds.store_postgres import psycopg`, or `getattr(mod, "psycopg")` is not covered. The guard's own plant strings must stay AST-safe.
*   **Rationale:** evidence: Ticket P4d-c rule 3.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-c guard
    *   Change: Also flag string constants `"psycopg"` and `ImportFrom` alias names in `tests/` outside the allow-list. State in the guard that it is a lint, not a boundary.

### [Issue 21] [`egm-design`] - Severity: Nit (finding id A16, adversarial)
*   **Affected Scope:** P4d-a tests of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The "recording proxy" counts a call anywhere (fixtures, setup) as coverage, so a method can be "called on every backend" without any assertion. The closed-port test accepts `OperationalError` "from either state", which is nearly vacuous. The contract rows are written by the same author for both stores from the same spec, so "both wrong the same way" is the main residual risk.
*   **Rationale:** evidence: Ticket A7/A4 text.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a tests
    *   Change: Count only calls made inside a test body. Add one model-based property test (hypothesis, random sequences of reserve/settle/release/sweep) that checks both stores against a plain-Python reference ledger and checks `counter == sum(open reserved) + sum(settled)` as an invariant.

### [Issue 22] [`egm-design`] - Severity: Nit (finding id A17, adversarial)
*   **Affected Scope:** B7 and process rows of `handover/tickets/P4d.md`
*   **Discrepancy Description:** B7 uses `sleep 2s` with `older_than_s=1`, which is slow and flaky on a loaded machine (the shared laptop has had load problems). The SIGKILL test depends on timing: a backend blocked on a lock does not notice a dead client until it wakes (reasoned about Postgres, not run), so the test must release the admin lock and then wait before asserting.
*   **Rationale:** evidence: Ticket B4/B7.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: B7 and process rows
    *   Change: Assert after release plus a poll on `pg_stat_activity` with a bounded timeout. Use an injected clock offset (`created_at` set by an owner-only fixture connection, not the runtime role) so the sweep test does not sleep.

### [Issue 23] [`egm-codebase-details`] - Severity: Nit (finding id C10, correctness)
*   **Affected Scope:** P4d-a Security of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The claim "the only DSN text in the repo is CI's password-less URL (`ci.yml:86`)" is false. `ci.yml:93` repeats it, and about ten tests hold DSN literals.
*   **Rationale:** evidence: `ci.yml:93`; `test_p2_postgres.py:78,137`; `test_k2_migrations.py:115,120`; `test_p7_tick.py:389,504`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a Security
    *   Change: Reword: "no password-bearing DSN; new fixtures build from parts".

### [Issue 24] [`egm-codebase-details`] - Severity: Nit (finding id C11, correctness)
*   **Affected Scope:** P4d-a FAIL-BEFORE and regression pins of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Several rows already pass on ce70eb5 and are not labelled as pins. They are the 1 MB, Unicode and SQL-text round trips (parametrized, so they pass). Also the duplicate `save_gate_decision`, `add_tool_call` and `save_approval_decision` rows, A3 atomicity, and the A2 races for `create_run`, `transition`, `record_decision` and `add_spend`. The Postgres side of the `list_approvals` order rows also already passes.
*   **Rationale:** evidence: `test_store.py:139,206,227,264`; `test_p2_postgres.py:246`; `test_p7_store.py:174`; `postgres.py:399-406`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a FAIL-BEFORE and regression pins
    *   Change: Add these to the regression-pin list.

### [Issue 25] [`egm-codebase-details`] - Severity: Nit (finding id C12, correctness)
*   **Affected Scope:** P4d-b, `@_writes` list of `handover/tickets/P4d.md`
*   **Discrepancy Description:** "Five methods, all `@_writes`" includes `get_spend_reservation`, which is a read. The AST sibling check is for write methods.
*   **Rationale:** evidence: Ticket P4d-b Interface and Files.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b, `@_writes` list
    *   Change: Four writes, one read.

### [Issue 26] [`egm-codebase-details`] - Severity: Nit (finding id C13, correctness)
*   **Affected Scope:** P4d-b, `is_connectivity_error` change of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The ticket does not list the other callers or add tests for them. They are `audit/chain.py:531-541` (an unreachable store becomes `StoreUnavailable`), `cli.py:368` and `tick.py:342,362`. After the change, a class-40 error at these call sites reads as "answers but not ready: run migrate".
*   **Rationale:** evidence: Cited files.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b, `is_connectivity_error` change
    *   Change: Add one test per caller.

### [Issue 27] [`egm-codebase-details`] - Severity: Nit (finding id C14, correctness)
*   **Affected Scope:** P4d-b, row B8(c) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Two points. (1) "How existing tests build an old release is UNVERIFIED" is verifiable: `test_k2_migrations.py:387-394` monkeypatches `_migration_files` to `files[:-1]` and stubs `check_grants`. `test_k5_fixes2.py:260-309` builds renamed folders. (2) "Run the ce70eb5 contract rows against a database that has the new table" needs a mechanism. The P3a ticket says an old tree refuses a new table via the catalog test (`test_k2_migrations.py:357-371`), and its layer 2 works only for ALTER-only migrations.
*   **Rationale:** evidence: P3a ticket line 64.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b, row B8(c)
    *   Change: Name the mechanism (old `migrate` wrapped, then apply the new SQL by hand) and note the limit.

### [Issue 28] [`egm-codebase-details`] - Severity: Nit (finding id C15, correctness)
*   **Affected Scope:** P4d-b `settle_spend` of `handover/tickets/P4d.md`
*   **Discrepancy Description:** "A later call, whatever its amount (even an invalid-looking one that is a valid Decimal)" conflicts with "validate before any SQL". A NaN second call would raise `ValueError`, not return the first result.
*   **Rationale:** evidence: Ticket rule 1 and the settle interface.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b `settle_spend`
    *   Change: State that validation runs first on every call, or exempt closed reservations.

### [Issue 29] [`egm-codebase-details`] - Severity: Nit (finding id C16, correctness)
*   **Affected Scope:** Template order and fields of `handover/tickets/P4d.md`
*   **Discrepancy Description:** All 17 template fields are present and "Extended review: yes" is set. The order is not the template's. The header places Neutral default and Existing code reused before each sub-ticket's Interface and Files. Sub-tickets have no Depends-on of their own (P4d-c has none) and no own Done or Reviewers. A13(1) calls P4d-c "its adversarial review A12 defines", but A12 on disk defines no such thing. The ticket's P4d-c is the lock-in guard.
*   **Rationale:** evidence: `amendments.md:31,33`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Template order and fields
    *   Change: Add per-sub-ticket Depends-on lines. Ask the lead to correct the A13 wording.

### [Issue 30] [`egm-codebase-details`] - Severity: Nit (finding id C17, correctness)
*   **Affected Scope:** P4d-b, kill switch of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Not stated whether `settle_spend`, `release_spend` and sweep ignore the kill switch. They should, so that stopping does not strand reservations.
*   **Rationale:** evidence: Ticket interface.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-b, kill switch
    *   Change: One line.

### [Issue 31] [`egm-codebase-details`] - Severity: Nit (finding id C6, correctness)
*   **Affected Scope:** P4d-a, `@_writes` retry of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The retry fires on "sqlstate class 40". That includes 40003 `StatementCompletionUnknown`, where a write may have been applied, so a blind retry of `add_spend` or `reserve_spend` is unsafe.
*   **Rationale:** evidence: `psycopg/errors.py:1292`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a, `@_writes` retry
    *   Change: Retry only on 40001 and 40P01. Other class-40 errors map to `StoreBusy` or pass through.

### [Issue 32] [`egm-codebase-details`] - Severity: Nit (finding id C7, correctness)
*   **Affected Scope:** P4d-a, `check_text` scope vs hostile rows of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `check_text` is defined for "JSON-bound fields". The hostile row demands that NUL in a plain text value be a `ValueError` on both stores. MemoryStore would accept NUL in TEXT fields.
*   **Rationale:** evidence: Ticket text; `memory.py` stores any value.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P4d-a, `check_text` scope vs hostile rows
    *   Change: Apply `check_text` to every string field of the row model.

### [Issue 33] [`egm-codebase-details`] - Severity: Nit (finding id C8, correctness)
*   **Affected Scope:** Evidence commands, P4d-a and P4d-b of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `uv run --group test bandit` fails. bandit is in the `scan` group, not `test`. P3a uses `--group scan`.
*   **Rationale:** evidence: `pyproject.toml:52,54`; P3a ticket line 74.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Evidence commands, P4d-a and P4d-b
    *   Change: Use `uv run --group scan bandit -q -r src demos -ll`.

### [Issue 34] [`egm-codebase-details`] - Severity: Nit (finding id C9, correctness)
*   **Affected Scope:** Verified facts, psycopg counts of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `test_p7_store.py` has 1 `importorskip` (line 11), not "+2". All other per-file counts are correct.
*   **Rationale:** evidence: `tests/test_p7_store.py:11,13,137,140,144,156`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Verified facts, psycopg counts
    *   Change: Correct to 1.
