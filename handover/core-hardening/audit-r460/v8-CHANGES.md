# v8 changes: finding -> change -> where in `CORE-PR-HANDOFF-v8.md` (2026-11-16 UTC)

Inputs: `review-handoff-v7-security.md` (M-A to M-I, nits 1 to 8), `review-handoff-v7-readiness.md` (majors 1 to 9, ordering note, nits), `evidence-handoff-v7/citation-check-v7.md` (2 wrong, 4 partly right). Nothing below was run: the status of every change is "specified, unverified" until its E0 item runs (section 7). "Wrong or partly right review claim" rows come first.

## A. Where a review claim was wrong or only partly right (and what I kept)

| Review claim | What the code says | What v8 does |
|---|---|---|
| Security M-G: "do not hold the Python lock across the wait" | `PostgresStore` has one connection behind one `threading.Lock` (`store/postgres.py:191-197`), `autocommit=True` (`:146`), `add_spend` uses `with self._lock, self._db.transaction()` (~`:416-431`). A second thread's statement on that connection would join the first thread's open transaction. | **Not done as worded.** The Python lock stays; the wait is bounded by `lock_timeout` (default 2000 ms) mapped to `meter_unavailable`; a dedicated second connection is a named trigger (4.1, F25, D27). The rest of M-G (timeout, explicit READ COMMITTED, second-connection test) is done. |
| Security nit 3 / readiness major 1 are right, and also show my own v7 error | v7 line 309 told the builder to rename each kind's `chat` to `_chat`; `NetworkLLM.chat` (`llm/common.py:208-220`) and `_chat` (`:222-231`) exist and all four kinds define `_chat`. | M2b wraps the existing `chat`, no rename (4.2, F24). |
| Readiness major 3: "the builder is told to copy the purge handling (`migrate.py:304-360`) which the author never read" | Correct for v7. | I read `store/migrate.py` in full this pass (F26) and wrote the adjust handling from it (4.1 Grants). |
| Security M-F: "true lower-bound floor, or split totals" | A true lower bound cannot be computed: the 3-characters-per-token estimator is high for English and low for text with few characters per token. | The floor is renamed a **sanity floor**, stated not to be a bound, and the totals are **split by `basis`** (4.1; section 0 item 5b). |
| Security M-E: "consider per-agent roles or row security" | A per-agent role map is a real cost (one role per agent). | Shipped as an optional table, **off by default** (D29), with tests for both states (section 5 items 14, 15); the default setup states the gap. |
| Readiness major 9 (E0-12 "named file written in M2-0") | Right. | `tests/test_import_graph.py` in M2-0; the pass rule is stated trivially true today (citation row 6). |
| My earlier plan of a new `SpendBookkeepingError` | With `finish` catching every `Exception`, pricing wrapped, and `reserve` raising only `SpendRefused`, nothing can leave the closure. | Dropped (4.2); the test proves it instead. |

## B. Security review (v7)

| Id | Change | Where in v8 |
|---|---|---|
| M-A finish against relief race | Both triggers take `pg_advisory_xact_lock(spend_lock_key('agent:'\|\|agent_id))` first and refuse non-READ-COMMITTED; `finish_spend` and `adjust_spend` take the same lock and re-read after taking it; two-connection tests | 4.1 (triggers, locking, `finish_spend`, `adjust_spend`); section 7 E0-3 (a) to (f); section 5 item 16, 17 |
| M-B flat prices, no tier, no cache price | `Route` tier fields, `max_input_tokens`, `cache_read_usd_per_mtok`; one `cost_of`; guard test for cache words; tier numbers marked UNVERIFIED | 4.1 "Prices"; D26; 4.3 M1 content item 4; E0-15 |
| M-C bookkeeping inside the retry classifier | `finish` catches every `Exception`; pricing wrapped; `reserve` raises only `SpendRefused`; `with_retry` passes `SpendRefused`; `ConnectionResetError` tests, one HTTP request | 4.1 "Settle details"; 4.2 "The `_retry` closure"; E0-13; section 5 item 19 |
| M-D demo stage weak rules | `classify_llm`: network (`type(llm).chat is NetworkLLM.chat`, own gate) or named double wrapped by `MeteredLLM`, doubles refused in live stages, everything else refused in every stage | 4.2 "What can spend money"; D28; E0-14 |
| M-E over-claims about a hostile runtime | Reworded; the cap-filling insert for another `agent_id` stated; "never exceeds a cap" restated as a lock property; per-agent role option; negative tests 14, 15 | section 0 item 8; 4.1 "Admission rule"; section 5; D29 |
| M-F floor not a bound; invoice rule fires every month | `basis` column; sanity floor; seven-part report; revised invoice rule | 4.1 (schema, booking table, "Unknown usage"); section 0 item 5b; `limits report` in 4.3; E0-15 |
| M-G lock timeout, Python lock, READ COMMITTED | `lock_timeout`, explicit isolation, mapping to `meter_unavailable`; Python lock kept with the reason | 4.1 "Serialising writers"; D27; E0-3 (d) |
| M-H self-hosted unusable in live stages | `Route.self_hosted`, loopback-only zero price, unknown usage priced at floor on such routes; trigger for private hosts | 4.1 "Self-hosted models"; D11; E0-15 |
| M-I host clock | `max_skew_s` against `transaction_timestamp()`; window check repeated inside `reserve_spend`; codes `clock_skew`, `window_ended` | 4.1 `reserve_spend`; 4.4 table; D27; E0-3 |
| Nit 1 trigger lookup no kind filter | `PRIMARY KEY (kind, res_id)`; every lookup names the kind | 4.1 schema and triggers |
| Nit 2 `ON CONFLICT (res_id) WHERE ...` may hit the wrong key | untargeted `DO NOTHING`; 23505 maps to `late=True` | 4.1 `finish_spend` |
| Nit 3 stale line 309 | see A | 4.2, F24 |
| Nit 4 `by` free text; `window_owner` self-asserted | `by_label` with a check pattern; both stated to be labels, not identities | 4.1 schema note; D1 |
| Nit 5 `usage_estimated` "exactly when unknown" | now "estimator fired in `reply()` or `unknown_seen`" with the reason | 4.1 "Unknown usage" |
| Nit 6 `_Mapping.__deepcopy__` empty holder | copy marked `copied=True`; `restore` on it raises | 4.7 |
| Nit 7 month sum not covered by an index; 50 ms cap on reserves per second | covering indexes with `INCLUDE`; the per-second figure stated in D24 | 4.1 schema; D24 |
| Nit 8 memory store lacks trigger equivalents; shrinking `spend` breaks old replicas | `spend_rules.check_final` and `check_adjust` used by the memory store; shrink moved to PR M2d | 4.1 store methods; D30; section 6 row 7b; E0-16 |
| v6 closure remarks (M-B, M-F remaining; demo and subclass open) | covered by M-B, M-F, M-D rows | as above |

## C. Readiness review (v7)

| Id | Change | Where in v8 |
|---|---|---|
| 1 stale line 309; `Reply` is pydantic | wrap existing `chat`; `model_copy(update=...)` | 4.2 "What `chat` becomes"; F24 |
| 2 refusal code `run_budget` vs `run_budget_reserve` | `SpendMeter.reserve` maps `which == "run_budget"` to `run_budget_reserve`; K6 note kept | 4.1 `SpendMeter`; 4.4 |
| 3 adjust-role grants | `Grant.adjust`; spend_op `SELECT`, spend_adjust `SELECT, INSERT`; `_apply_grants` and `effective_problems` copied from the purge handling (read) | 4.1 Grants; section 5 table |
| 4 `Limits.correct` path | `Limits(..., adjust_store=)`, `adjust_dsn_secret_name`, `model_copy` build (`app.py:152-160`), refusal in live stages without it; `_SplitStore` forwards `adjust_spend`; F20 corrected | 4.1 Orphans and relief; 4.5; 4.3; F20 |
| 5 finish race; duplicate final 23505 | as M-A; 23505 maps to `late=True` | 4.1 |
| 6 `add_spend` ts and id | `ts = models.now()`, `res_id = new_id("dir")`, `run_id` NULL, `day` as given; callers listed; no DB-day check | 4.1 store methods |
| 7 judge and fake path; `test_k5_fixes1:73`; full pass of `Runtime(`, `Limits(`, `.detector =` | judge test change; checks after the `validate_proposal` loop; `llm` property; app wraps once; callers listed | 4.2 "What can spend money"; F27 |
| 8 M1 content unspecified | six-part M1 content (Money, Budget, Reply, Route, window_end validator, zero-price function, constants) | 4.3 "M1 content" |
| 9 E0 items not runnable | table with command, output file, pass rule, author PR; import-graph test file named; lead inputs named | section 7 |
| Ordering: `window_ended` in `Limits.blocked` and `spend_totals` rewrite unassigned; one train vs CI per PR | assigned to M2a; stacked branches, CI per PR head, one full run at the train head | 4.5; section 6 |
| Nit: caps round down; over 1,000,000 USD raises | `cap_to_nano` (floor); more than 9 decimals refused at config load | 4.1 Money unit |
| Nit: `cli.py:195-199` messages | per-command wording | 4.3 |
| Nit: `SpendScope` types for window-only | `Decimal \| None`; `meter=None` | 4.2 table |
| Nit: `floor_usd` no home or signature | `floor_for(est, ans)` in `llm/common.py`; `Estimate` fields | 4.1 |
| Nit: `_handle_body` parameters | `(run, agent, document, mapping, cited)`, with the unread range stated | 4.2 edits table; 4.4 |
| Nit: `max_call_usd=None` meaning | allowed only for a window-only scope | 4.2 table |
| Nit: `signer.py:197,209` | S1 siblings | 4.8 |
| Nit: `utc_day` with `astimezone(UTC)` | specified; naive time refused | 4.1 `SpendMeter`; 4.2 table |
| Nit: `refused` hook as `staticmethod` | stated, with the two cites | 4.1 status hook |
| v6 closure gaps: `build_gate(spend: SpendSettings)` import; `MAX_SPEND_OP_USD` not in the spend.py row | `build_gate(window_end, clock, margin)` takes plain values; `MAX_SPEND_OP_USD` listed in the `llm/spend.py` row | 4.2 table |
| v6 closure: line 276 `usage_estimated` claim | see nit 5 | 4.1 |

## D. Citation check of v7

| Row | Fix | Where |
|---|---|---|
| 1 purge connection `app.py:131-139` | `app.py:152-160` | 4.1 Grants, 4.1 Orphans and relief, 4.2 edits table |
| 2 `Money` is not a class | type alias `config.py:45`, validator `_money` `:38-42` | F15, 4.3 |
| 3 `test_providers.py` list one site short | `:65,123,148,172,198` | 4.2 tests |
| 4 `test_p6_detectors.py:351` is the import line | `make("detector"` call at `:355` | 4.2 tests |
| 5 `runmap.py:275-304` | `escape_placeholders` `:275`, `redact_untrusted` `:298`, `redact_text` `:417` | F16 |
| 6 cycle counting | both counts stated; the rule uses run-time imports; the two extra sets exist only under `TYPE_CHECKING` | 4.2; section 0 item 2(l); E0-12 (pass rule trivially true today) |

## E. Verification of v8 itself

- Read-only AST import-graph program saved at `evidence-handoff-v8/import_graph_v8.py`, output `evidence-handoff-v8/raw-import-graph-v8.txt` (one cycle today, none new in the v8 shape, the v6 shape shows `llm.common <-> llm.gate`).
- Banned-string count in my three files: 0 (counted with strings built from parts). Final numbers (sha256, line count) are in the report to the lead.
- Not run: tests, `ruff`, `bandit`, Postgres. No independent review has happened; the lead runs the EGM reviewers next.
- The citation file `evidence-handoff-v7/citation-check-v7.md` existed when I read it this pass (it was missing earlier); I re-checked for a newer copy just before reporting (see the report).
