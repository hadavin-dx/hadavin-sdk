# P5b3 round 2, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

TICKET REVIEW ROUND 2, CORRECTNESS: handover/tickets/P5b3.md (revision 2)

Result: no Blocker. Two Majors, then Minors and Nits. Most cites, counts and arithmetic hold, but the sweep count is wrong, one existing test breaks that the ticket does not list, and one lead decision (order 24 item 39) is not applied.

Method: I read all 659 lines of the ticket, the template, orders 6-24 and amendments.md. I read the cited lines in src/ and tests/ on disk. I spot-checked P5a.md:74/:167, P5b4.md:412-419 and P5b2.md:197-204. I did not read reviews/ or evidence/. The tree is not a git repo, so every claim about ce70eb5, cd2243f, 4ec3616 and runmap `:523` is UNVERIFIED.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Major | 292, 214 (Files: `test_k5_round9.py`; Hostile inputs) | The ticket says only the tick driver in `tests/test_k5_round9.py` changes and the key set is unchanged. But `test_every_registry_row_masks_every_spelling_through_its_real_function` (`round9:209-219`) also asserts `PLACEHOLDER.search(out)` for every row and every spelling. The `injection screen log line` driver (`_log_line`, `round9:78`), the `extract validation errors` driver (`_extract`, `round9:91-109`) and the `tick error message` driver all return closed Grammar A or type names. None has a `<NAME_1>`-style placeholder. After P5b3 these three rows fail on the placeholder assertion for every spelling. The builder must either weaken a shared assertion or invent a new one, and the ticket forbids weakening ("no assertion is weakened without a stronger replacement"). This is a decision left to guess. | Name `round9:209-219` in Files. State the replacement for the three diagnostic rows: for example, needle absent AND `grammar_ok(out)` AND the closed-text check, with the placeholder check kept for the other rows. Add this to evidence 1. Also say how `round8` `PRODUCER_CALLS["tick"]` and `["injection log"]` are re-pointed. They only assert `_clean(out)`, so they survive. |
| R2-COR-2 | Major | 234-247 (sweep counts); 568 ("every cite verified"); 563 (STOP at 80) | The scan is described as a floor, but its category counts are false against the disk, and the guard would hit more. Missing from the 47: (a) `cli.py:375-376`, a `print` of `type(exc).__name__` in `_kill_switch_store_down` (print hits are 7, not 6); (b) `runtime/tick.py` `_safe_log(...)` at `:343`, `:345`(`:348`), `:356`, `:363`(`:365`). The ticket lists these in the tick sweep sentence (`:189`) but not in the 47. `_safe_log` is not a logger name, so under the "any call not on SAFE" sink they are other-call hits, not the 2 listed; (c) `sources/__init__.py:73` (`out.append(f"... ({type(exc).__name__})")`); (d) `k1b/replay.py:276` (`atomic_write(..., type(exc).__name__)`); (e) `sources/kubernetes.py:179-181` (`err = SourceError(f"kubernetes: {type(exc).__name__}")` then `raise err`), a raise hit through an assignment, so raises are 25, not 24. That is at least 9 hits not counted, so the floor is about 56. The three new files (`sources/__init__.py`, `sources/kubernetes.py`, `k1b/replay.py`) are not in Files or in the hot-file PENDING LEAD 12, and only the catch-all "any further file the guard names" covers them. | Correct the categories: print 7, raise 25, other-call at least 8, floor at least 56. Add the three files to Files and to PENDING LEAD 12. Keep the base-run STOP at 80 but say the margin is about 24. Add the corrected total to evidence 5 as "builder recounts". Soften "every cite verified" (line 568). |
| R2-COR-3 | Minor | 564 (PENDING LEAD 19); Files | Order 24 item 39 now answers PENDING LEAD 19: option (a), and the limit must also be written in plain words to `handover/owner-visible-limits.md`. The ticket still says "the lead may switch to (b)" and has no step for that file. The file does not exist on disk. | Mark PL19 closed by order 24 item 39. Add a Files entry: create or append `handover/owner-visible-limits.md` (the "ASCII secret in a mislabelled OPERATOR message still prints" limit, plain words). Add it to Done. |
| R2-COR-4 | Minor | 292, 291 (Files: `test_k5_fixes3.py:112-120`) | The ticket calls the replacement "stronger than what it replaces", but the original also asserts `seen and max(seen) <= defaults.MAX_REDACT_CHARS`, which bounds the work done on a 1 MiB message. The new path no longer calls `runmap.redact_text`, so that part has no analogue. Only the length bound `<= 500` becomes `<= DIAG_LINE_CHARS`. | Say the work-bound assertion is dropped on purpose (nothing redacts any more) and give the replacement, for example that `diagnose` is O(1) in the message length. Or drop "stronger" for this row. |
| R2-COR-5 | Minor | 300 (migration table) | The grep (`error_kind=\|refused: \|tick: config error\|last_error`) finds 10 lines in 6 files (I recounted: correct). But other tests pin text P5b3 changes or keeps: `warden_port/test_audit_chain.py:228` and `:258` (`could not verify:`), `:493` and `:497` (`not signed (TimeoutError)`, `not anchored (ConnectionError)`), `test_k1b_cli.py:216` (`error_code == "OSError"`), `test_p2_postgres.py:141` (`kill switch NOT`). All survive because the built-in names stay bare and the own ASCII text is kept. They are absent from "Checked and unchanged" (`:296-299`). | Add these to the "Checked and unchanged" list, with the reason (built-in name bare; own ASCII text kept). Add the builder step "grep tests for any asserted class name and `reason ==`". |
| R2-COR-6 | Minor | 227, 241-245 | `tools.py:994` and `:1012` (`error_reason`) return `type(exc).__name__` text that is sent to the model. A `return` is not a sink in the guard and not a writer in the ticket's definition, so these are neither swept nor stated as out of scope. A run-time-named exception class can reach the model there. | Decide: either add a guard rule or an explicit row for `return` of text from an exception-named function, or add a line saying `error_reason` is outside P5b3 with a v1.1 row. |
| R2-COR-7 | Minor | 169-172, 281 | The generator arithmetic is stated as FOREIGN minus 13 minus 5 minus N. M9 says "the 18 rows lock to FOREIGN". Both are UNVERIFIED until P5b2's table exists. This is correctly marked, but "OPERATOR rises by 18 plus those rows" assumes all 18 rows exist in the CSV now. `tools.py:120` is not one of P5b2's 17 direct places. | Add: "the builder checks that `tools.py:120` is a row at all (it is reached through an assignment) before relying on 18." |
| R2-COR-8 | Nit | 189, 241, 243, 245 | Several cited lines are statement starts, not the line holding `type(exc).__name__`: `tick.py:207` (name on `:209`), `:328` (`:329`), `:345` (`:348`), `:363` (`:365`); `chain.py:331` (`:332`), `:535` (`:536`), `:538` (`:540`); `store/postgres.py:172` (`:173`); `k1b/loop.py:100` (`:101`); `approvals/requests.py:118`, `:187` and `:225` (name on `:121`, `:188`, `:228`). They are valid as statement cites. | Add "(statement start)" or give both lines. |
| R2-COR-9 | Nit | 303-310 | The template asks to list what was checked, including `evals`. The ticket lists seven items and omits `evals`, which it modifies at `:67`. | Add `evals.py` to the checked list. |
| R2-COR-10 | Nit | 196, 357 | After the change, `guard/injection.py` no longer uses `safe_head` (`:96`). The ticket does not say to remove the import, and ruff F401 would fail. The same goes for `extract.py` and `runtime/tick.py` (`_message` and `safe_head`). | Add "remove now-unused `safe_head` imports" to Files. |
| R2-COR-11 | Nit | 356, 203 | FB12 calls `Handler.log_message`, but `Handler` is a local class inside the server factory (`receiver.py:62` is nested). How the test reaches it is not said. The ticket marks FB11 UNVERIFIED but not FB12. | Say: reach it through `make_server(...).RequestHandlerClass`. |
| R2-COR-12 | Nit | 496 | `evidence-r.md` has no path. `plan-v3.md:183` names it without a folder, and no such file exists on disk. | Give the path, or say "the lead appends". |

Template fields: all 17 are present, in the template's order. The "Problem in plain words" has 4 sentences (limit 3-5), plus one sub-bullet. Details under "Verified" below.

Verified (read on disk, true as cited):
- `cli.py`: `:72-83` (except order; hint text at `:79`; `HADAVIN_DEBUG` at `:81`; `traceback` only at `:32` and `:82`; `os` still used at `:133` and `:322`), `:191-206`, `:267-271`, `:300-308`, `:354`.
- `tick.py`: `:73`, `:284-292`, `:310`, `:316-317`, `:324`; `_safe_log` exists at `:273`; step names are checked to `[a-z_]` at `:60`.
- `extract.py:57-64`; `injection.py:92-96`.
- `producers.py:30-37`: the three rows exist; `_message` is column 3 of the tick row and changes to `_run_step`.
- `receiver.py:62-63`.
- `config.py`: `:43`, `:52` (only `hide_input_in_errors` in config), `:120`, `:413`, `:436`, `:453-454`.
- `registry.py`: `:33`, `:39`, `:58`, `:179`, `:214-227` (the 5 places), `:314-330`.
- `identity.py:10`, `contract.py:47` (no `hide_input_in_errors`).
- `anthropic.py:55-56`; `evals.py:67-69`; `runmap.py:476` on disk (other `RedactionError` raises carry fixed words only).
- `tools.py:118-120`, `:397`, `:617-620`; `chain.py:213`, `:316`, `:331`, `:343-358`, `:535-540`; `local_dir.py:108`.
- `app.py:192`, `slack_channel.py:177`, `agent_loop.py:567`; `retry.py:79`, `:99`, `:101-103`.
- `store/protocol.py:29`, `:41` (`StoreUnavailable` is a `ConfigError`); `BundleError` is a `ConfigError`.
- Class-name places: 2+1+1+1+2+2+1+1+1+1 = 13, plus 5 = 18.
- Category sum: 24+11+6+3+1+2 = 47. The 11 log hits are all correct (3 in requests, 2 in chain, 1 injection, 1 k1b loop, 4 tick). The 24 raises assume `retry.py` counts as 2.
- Tests: `test_k1b_cli.py:140`, `:144`, `:188-195`; `test_k5_round7.py:41-42`; `test_k5_fixes3.py:112-120`; `test_k5_round8.py:73`; `test_k5_round9.py:196`, `:204`; `test_k5_round12_fuzz.py:132`; `test_k5_round5.py:589`; `test_p7_tick.py:110`, `:112`, `:424-425`; `test_k5_producers.py:47-53`. Exactly 5 test files call `tick_mod._message`.
- `class_name_of(URLError)` prints `urllib.error.URLError`, per `P5a.md:74`.
- Arithmetic:
  - 31 finding ids + 6 RES = 37 items, 1 contest, so 36 fixes.
  - AUTH-1 to AUTH-9 is 9 items.
  - FB1-FB13 is 13 rows; the mutant table has 31 rows; v1.1 rows V1-V14 is 14; PENDING LEAD items 1-20 is 20.
  - Cut mutants M10-M13, M16, M17, M22, M24 is 8, so 27-8+12 = 31.
  - New test files: 4.
- Orders cited: 7(1), 7(3), 8(5), 14/15 wording, 16, 20 items 4/5/6, 21 item 17, 22 item 29 all match LEAD-ORDERS.md.
- Cross-ticket cites: `P5a.md:167` ("non-revertible" claim), `P5b4.md:414-419`, `P5b2.md:199-204`.
- `HADAVIN_DEBUG` appears in `src/` only at `cli.py:79` and `:81`.
- Rollback claim: `last_error` is read only as `is None` (`tick.py:310`).

Not checked / UNVERIFIED:
- Git facts: `ce70eb5`, `cd2243f`, `4ec3616`, `runmap` `:523`, "5 files differ" (no git on this tree).
- P5a and P5b2 merged names and behaviour: `validation_text`, `Where`, `StepToken`, the identity rule, `tainted_names`, corpus row ids. These files do not exist on disk, and `test_diagnostics_*`, `test_llm_text_channels.py`, `guard/diagnostic.py` and `tools/` are absent.
- Golden lines: the fact keys `type=` and `count=`, and the `at=` values.
- Whether `errors.py` can import `guard/diagnostic.py` at module level without a cycle (the ticket marks this UNVERIFIED). I did not check `runmap` importing `class_name_of` for a cycle either.
- P4c's tick step and alert writer (`P4c.md:41`, `:196`, `:201`, `:221`) and `P5b4.md:154` and `:319`: not read.
- Feasibility of the `round12_fuzz` driver calling `_run_step` per case (a store per case is heavy).
- The 90 percent reverse-check threshold, the STOP value of 80, `REFUSAL_CHARS` 2000, and the agent-hour estimate.
- Mutant ids "12 added" (only the totals add up).
- Whether `evals.py:67`'s `RedactionError` text is operator-safe after the `runmap` fix, beyond the `:476` raise.
