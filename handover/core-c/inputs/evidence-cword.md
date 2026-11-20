# evidence-cword: proof for SECURITY-README-v6.md and CHANGELOG-lines-v6.md

Written 2026-11-20 by the lead's laptop job "wording" (job 3 of handover/core-c/requests/lead-build-1.md). Docs only; no src or tests edited; nothing pushed; US$0.

## Head

- Worktree: `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\lead-cword` (detached at origin/cloud/core-c after `git fetch origin cloud/core-c`).
- **Head sha: `a60da33944f772faf99ebee34a997c6933b98bb4`** (a60da3394). The request named base 7c31dbc97; the fetched head is later: it holds 7c31dbc97 plus notes commits and the E15 pin tests (d399ac5f3, a2dd036c1). v6 is written against a60da3394.
- Python for the probes: 3.13.3 (laptop), run from the worktree with `sys.path` = `src`; no dependency needed; no live call; US$0.

## How to read the proof column

- file:line = I read those lines at the head above. T:: names are tests; the number after a test name is its `def` line.
- Code R = I read the cited code or test lines. E = a recorded evidence or ticket file line that I read (a builder's result, not re-run by me). P = my own probe at this head (section Probes). U = the statement itself is worded UNVERIFIED (a reading, not a run).
- TESTED in v6 means: the test exists at the cited line and a recorded batch (evidence/INT-merged-batch-1.md to -5.md, or the builder's file) says it passed. I did NOT run the suite; that is laptop job 1 (NOT RUN here).

## Probes (MEASURED by me, head a60da3394, Python 3.13.3, `redact` = `guard/redact.py` `redact()`; `redact_text` = `guard/runmap.py`)

probe.py (redact):
```
'x10.20.30.40' -> 'x<IPV4_1>'
'10.20.30.40x' -> '<IPV4_1>x'
'10.20.30.40_x' -> '<IPV4_1>_x'
'DE89370400440532013000_x' -> '<IBAN_1>_x'
'xDE89370400440532013000' -> 'xDE89370400440532013000'
'iban_DE89370400440532013000' -> 'iban_<IBAN_1>'
'acct_iban_DE89370400440532013000' -> 'acct_iban_DE89370400440532013000'
'+14155550132_x' -> '<PHONE_1>_x'
'123e4567-e89b-12d3-a456-426614174000x' -> '<UUID_1>x'
'ref 55556666 paid' -> 'ref 55556666 paid'
'db01.acme.example' -> 'db01.acme.example'
'telephone4155550132' -> 'telephone4155550132'
'card_4242424242424242' -> 'card_<PHONE_1>'
'x4242424242424242' -> 'x4242424242424242'
'&lt;TENANT_4155550132&gt;' -> '&lt;TENANT_<PHONE_1>&gt;'
'call +44 20 5550 1234.' -> 'call <PHONE_1> 1234.'
'password=<SEC' -> 'password=<SEC'
'password=<EMA' -> 'password=<SECRET_1>'
'password=\u2039JWT_1\u203a' -> 'password=<SECRET_1>'
'password=<S' -> 'password=<S'
```
probe2.py (redact and redact_text):
```
(text: 'str', mapping: 'dict[str, str]', neutralise: 'Callable[[str], str] | None' = None) -> 'str'
'python3.11.4.1' | redact -> 'python<IPV4_1>' | redact_text -> 'python<IPV4_1>'
'order_1234567890' | redact -> 'order_<PHONE_1>' | redact_text -> 'order_<PHONE_1>'
'tok_4155550132_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef' | redact -> 'tok_<PHONE_1>_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef' | redact_text -> 'tok_<PHONE_1>_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef'
'&lt;TENANT_1&gt;' | redact -> '&lt;TENANT_1&gt;' | redact_text -> '<TENANT_1>'
'%3CTENANT_1%3E' | redact -> '%3CTENANT_1%3E' | redact_text -> '<TENANT_1>'
'&#60;IPV4_1&#62;' | redact -> '&#60;IPV4_1&#62;' | redact_text -> '<IPV4_1>'
'&lt;TENANT_4155550132&gt;' | redact -> '&lt;TENANT_<PHONE_1>&gt;' | redact_text -> '&lt;TENANT_<PHONE_1>&gt;'
```
probe3: `python -c "import unicodedata; print(unicodedata.unidata_version)"` printed `15.1.0` on Python 3.13.3.

## Commands run

- `git log --oneline 6b990d9..HEAD` filtered to code commits: 22 code commits (b83accc65 gate round 4; da0f71fbe, 678353539, d1384342e, 9d8bc580a, bff88a7a1 G7 rounds 3 to 7; e8ff6de2b, c4d68c6ef, aa3b7ffdf E9; 4fb0b5154, 1bf4f11ba, 944d143db Q9; 6a852c7d3, 9c83340d1, 0b6f4e1ef G8; a6484cc7c, 0e3da02cf G10; d399ac5f3 E15; a2dea639f, 61ff6e7c8, a4b2ce230 approvals and docs; 833a86b60 flaky gate test). Filtered on G4 or G9 without "notes" or "board": empty.
- `git diff --stat 6b990d9..HEAD -- src`: 7 files (approvals/gate.py, defaults.py, guard/injection.py, guard/model_gate.py, guard/redact.py, guard/runmap.py, guard/textnorm.py). store, llm, runtime and models.py: unchanged.
- `grep -rn "ModelGate(" src` outside guard/model_gate.py: empty (the gate is not installed). `grep -rn reserve_spend src`: empty.
- check_v6.py: status of every K1 to K76 equal in part 2 and 4.2 (0 mismatches); part 1 holds no K numbers; no project words in parts 2 and 3 outside [INTERNAL] lines except the common word "ticket" (two shipped lines carried from v5 and a new K74 line); every cited test name has a `def` at head (see tables); cites_v6.py: 145 file:line cites in v6 edited lines, 0 beyond the end of their file.

## Counts

- Statement rows with a file:line or evidence proof: **170** (table A). Of these, 40 are worded UNVERIFIED in v6 itself (a reading, proof is the cite).
- Statements struck from v6 and listed here (table D): **32**.
- K rows carried unchanged from v5 (table C): 40; their cited tests exist at head (def line shown); that they pass is NOT RUN here.

## Table A: statements changed or new in v6, with proof

| id | statement (shortened) | proof | code |
|---|---|---|---|
| K3.1 | TESTED: for a known value that is not plain ASCII, the gate also masks its folded spellings. A known full-width name and its plain Latin spelling are both masked. | guard/model_gate.py:15-19; tests/test_model_gate.py:2639; tests: test_r3_c_m2_stated_rule_the_sweep_also_replaces_the_folded_spelling_of_a_non_ascii_value (tests/test_model_gate.py:2639) | R E |
| K10.1 | **K10. Fixed:** the audit row said "map in use" when the map was empty. It also said so when the calling code had supplied its own masking function (allowed for tests). The row now says which. | guard/model_gate.py:244-248; tests: test_r2_m5_the_audit_decision_says_what_was_really_enforced (tests/test_model_gate.py:2318), test_d1_every_audit_row_says_whether_the_map_was_enforced (tests/test_model_gate.py:1693) | R E |
| K10.2 | Example: a run with an empty map now writes "map empty", not the same row as one with 50 values. | guard/model_gate.py:244-248; tests: test_r2_m5_the_audit_decision_says_what_was_really_enforced (tests/test_model_gate.py:2318), test_d1_every_audit_row_says_whether_the_map_was_enforced (tests/test_model_gate.py:1693) | R E |
| K10.3 | Status: FIXED. Evidence: TESTED. Who acts: nobody. | guard/model_gate.py:244-248; tests: test_r2_m5_the_audit_decision_says_what_was_really_enforced (tests/test_model_gate.py:2318), test_d1_every_audit_row_says_whether_the_map_was_enforced (tests/test_model_gate.py:1693) | R E |
| K11.1 | **K11. Fixed:** a known secret inside a forged marker went out unmasked. Now the gate keeps only the marker's fixed words and masks the rest. | guard/model_gate.py:744-800; tests/test_model_gate.py:2025; tests: test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client (tests/test_model_gate.py:2025) | R E |
| K11.2 | Example: a document holds a forged marker whose call number contains the known `S3cr3tPw`. Before this fix, `S3cr3tPw` went out. | guard/model_gate.py:744-800; tests/test_model_gate.py:2025; tests: test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client (tests/test_model_gate.py:2025) | R E |
| K11.3 | Status: FIXED. Evidence: TESTED. Who acts: nobody. | guard/model_gate.py:744-800; tests/test_model_gate.py:2025; tests: test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client (tests/test_model_gate.py:2025) | R E |
| K12.1 | **K12. Reported, not reproduced:** a secret at a held-back value's edge may leak its tail. | guard/runmap.py:936-949; guard/runmap.py:678-682; tests: test_r2_m2_ (tests/test_model_gate.py:1997) | R |
| K12.2 | Example: known `S3cr3t` and `>abcdef`. A reviewer read that `S3cr3t>abcdef` becomes `<SECRET_1>abcdef`. A builder ran it and got `<SECRET_1><SECRET_2>`, with no leak. | guard/runmap.py:936-949; guard/runmap.py:678-682; tests: test_r2_m2_ (tests/test_model_gate.py:1997) | R |
| K12.3 | Status: OPEN. Evidence: NOT REPRODUCED. Who acts: the text and masking team (a fresh reviewer checks the builder's run). | guard/runmap.py:936-949; guard/runmap.py:678-682; tests: test_r2_m2_ (tests/test_model_gate.py:1997) | R |
| K12.4 | TESTED: the safety net that refuses a call when a known secret stays readable is in the code and in the batches (see K65). | guard/runmap.py:936-949; guard/runmap.py:678-682; tests: test_r2_m2_ (tests/test_model_gate.py:1997) | R |
| K13.1 | **K13. Not fully limited:** the time the gate spends on one model call. One budget per call now covers the characters, the steps and the time, and the time is read inside the masking step. One scan of one stretch of text inside th | guard/runmap.py:625-640; guard/model_gate.py:59-66; tests/test_model_gate.py:2493; tests: test_r3_m2_a_deadline_inside_the_sweep_is_a_budget_refusal_with_its_own_code (tests/test_model_gate.py:2493) | R E U |
| K13.2 | Example: UNVERIFIED (a figure in the gate's own source notes, not re-measured here). A text of 262,144 characters of `a` with 500 planted values of `aaa...` takes about 7 seconds before the deadline is read. A call past its budget | guard/runmap.py:625-640; guard/model_gate.py:59-66; tests/test_model_gate.py:2493; tests: test_r3_m2_a_deadline_inside_the_sweep_is_a_budget_refusal_with_its_own_code (tests/test_model_gate.py:2493) | R E U |
| K13.3 | MEASURED earlier: 100 messages against a run map of 2,000 entries took 0.018 seconds. | guard/runmap.py:625-640; guard/model_gate.py:59-66; tests/test_model_gate.py:2493; tests: test_r3_m2_a_deadline_inside_the_sweep_is_a_budget_refusal_with_its_own_code (tests/test_model_gate.py:2493) | R E U |
| K13.4 | Status: OPEN. Evidence: MEASURED (the 0.018 s case); UNVERIFIED (the 7 s). Who acts: the text and masking team. | guard/runmap.py:625-640; guard/model_gate.py:59-66; tests/test_model_gate.py:2493; tests: test_r3_m2_a_deadline_inside_the_sweep_is_a_budget_refusal_with_its_own_code (tests/test_model_gate.py:2493) | R E U |
| K14.1 | **K14. Not protected:** a run's later tool-using calls. A planted secret of 4 or more characters makes each of them refuse. It does so when it equals a tool's name or a call number, or is a piece of a name in the tool list. | guard/model_gate.py:368-396; tests/test_model_gate.py:1897; tests: test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker (tests/test_model_gate.py:1897), test_r3_c_m1_a_secret_that_is_part_of_a_listed_tool_name_refuses_the_call (tests/test_model_gate.py:2624) | R E |
| K14.2 | Example: a tool result contains `password=search_web`, where `search_web` is a tool's name. Later calls in that run refuse. | guard/model_gate.py:368-396; tests/test_model_gate.py:1897; tests: test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker (tests/test_model_gate.py:1897), test_r3_c_m1_a_secret_that_is_part_of_a_listed_tool_name_refuses_the_call (tests/test_model_gate.py:2624) | R E |
| K14.3 | Status: OPEN. Evidence: TESTED (the rule as built). Who acts: the owner decides which rule. If no answer arrives by 2026-11-23 12:00 UTC, the rule as built stays. | guard/model_gate.py:368-396; tests/test_model_gate.py:1897; tests: test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker (tests/test_model_gate.py:1897), test_r3_c_m1_a_secret_that_is_part_of_a_listed_tool_name_refuses_the_call (tests/test_model_gate.py:2624) | R E |
| K15.1 | **K15. Fixed:** planted text could rewrite part of a tool's name in the line where the model asked for that tool. | guard/model_gate.py:744-800; tests/test_model_gate.py:2598; tests: test_r3_c_m1_a_tool_name_in_the_tools_list_stays_exact_when_a_known_value_lies_inside_it (tests/test_model_gate.py:2598) | R E |
| K15.2 | Example: a document planted `password=logs`; the model then saw two names for one tool call. | guard/model_gate.py:744-800; tests/test_model_gate.py:2598; tests: test_r3_c_m1_a_tool_name_in_the_tools_list_stays_exact_when_a_known_value_lies_inside_it (tests/test_model_gate.py:2598) | R E |
| K15.3 | Status: FIXED. Evidence: TESTED. Who acts: nobody. See K66 for the tool list. | guard/model_gate.py:744-800; tests/test_model_gate.py:2598; tests: test_r3_c_m1_a_tool_name_in_the_tools_list_stays_exact_when_a_known_value_lies_inside_it (tests/test_model_gate.py:2598) | R E |
| K16.1 | **K16. Fixed:** stopping the program by hand while the gate masked, worked out the worst case, asked for a reservation, or in the instant after it, left no audit row. Now a row is written. | guard/model_gate.py:570-575, :610, :616; tests/test_model_gate.py:2340; tests: test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on (tests/test_model_gate.py:2340), test_r3_n4_a_keyboard_interrupt_in_the_enforce_step_writes_a_row_and_passes_on (tests/test_model_gate.py:2705), test_r3_n4_an_interrupt_between_reserve_and_the_call_writes_a_row_and_passes_on (tests/test_model_gate.py:2726) | R E |
| K16.2 | Example: the program is stopped by hand while the gate waits for its reservation. The record now holds a row that says "reservation interrupted". | guard/model_gate.py:570-575, :610, :616; tests/test_model_gate.py:2340; tests: test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on (tests/test_model_gate.py:2340), test_r3_n4_a_keyboard_interrupt_in_the_enforce_step_writes_a_row_and_passes_on (tests/test_model_gate.py:2705), test_r3_n4_an_interrupt_between_reserve_and_the_call_writes_a_row_and_passes_on (tests/test_model_gate.py:2726) | R E |
| K16.3 | The reservation stays booked, on purpose: the worst case stays booked, not the real cost. | guard/model_gate.py:570-575, :610, :616; tests/test_model_gate.py:2340; tests: test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on (tests/test_model_gate.py:2340), test_r3_n4_a_keyboard_interrupt_in_the_enforce_step_writes_a_row_and_passes_on (tests/test_model_gate.py:2705), test_r3_n4_an_interrupt_between_reserve_and_the_call_writes_a_row_and_passes_on (tests/test_model_gate.py:2726) | R E |
| K16.4 | Status: FIXED. Evidence: TESTED. Who acts: nobody. | guard/model_gate.py:570-575, :610, :616; tests/test_model_gate.py:2340; tests: test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on (tests/test_model_gate.py:2340), test_r3_n4_a_keyboard_interrupt_in_the_enforce_step_writes_a_row_and_passes_on (tests/test_model_gate.py:2705), test_r3_n4_an_interrupt_between_reserve_and_the_call_writes_a_row_and_passes_on (tests/test_model_gate.py:2726) | R E |
| K17.1 | **K17. Not safe:** two threads writing one run map at the same time can give one placeholder number to two values. | guard/runmap.py:603-606; guard/model_gate.py:119-121 | R U |
| K17.2 | Example: two tools finish together and both values become `<SECRET_3>`. | guard/runmap.py:603-606; guard/model_gate.py:119-121 | R U |
| K17.3 | Status: OPEN. Evidence: UNVERIFIED (stated in the code comments, not run). | guard/runmap.py:603-606; guard/model_gate.py:119-121 | R U |
| K17.4 | Who acts: the text and masking team adds "one writer per run map" to its install request to the connector and store team. | guard/runmap.py:603-606; guard/model_gate.py:119-121 | R U |
| K20.1 | **K20. Not released:** the worst case of a failed call. The model connectors cannot yet say "refused before any answer", so the gate does not settle a failed call. | tests/test_model_gate.py:1205; tests/contracts/test_t1_reserve_cap.py:41; tests: test_pin_an_unmarked_provider_error_is_not_settled (tests/test_model_gate.py:1205), test_pin_no_settle_on_keyboard_interrupt (tests/test_model_gate.py:1197) | R E |
| K20.2 | Example: the gate side is TESTED: a failed call is not settled. What the store keeps booked after that is the store's behaviour. The store's reservation code is the connector and store team's and is not on this branch (NOT PROVABL | tests/test_model_gate.py:1205; tests/contracts/test_t1_reserve_cap.py:41; tests: test_pin_an_unmarked_provider_error_is_not_settled (tests/test_model_gate.py:1205), test_pin_no_settle_on_keyboard_interrupt (tests/test_model_gate.py:1197) | R E |
| K20.3 | Status: WAITING. Evidence: TESTED (a failed call is not settled). Who acts: the connector and store team (written request). | tests/test_model_gate.py:1205; tests/contracts/test_t1_reserve_cap.py:41; tests: test_pin_an_unmarked_provider_error_is_not_settled (tests/test_model_gate.py:1205), test_pin_no_settle_on_keyboard_interrupt (tests/test_model_gate.py:1197) | R E |
| K24.1 | **K24. The gate passes a higher real cost to settle:** a call that costs more than its worst case is passed to settle at the real cost, on purpose. How the store books it is the store's code (not on this branch). | tests/test_model_gate.py:283; tests: test_a_settle_above_the_reservation_is_passed_through (tests/test_model_gate.py:283) | R E |
| K24.2 | Example: the gate side is TESTED. The store side (booked money passing the cap once) is NOT PROVABLE here. | tests/test_model_gate.py:283; tests: test_a_settle_above_the_reservation_is_passed_through (tests/test_model_gate.py:283) | R E |
| K24.3 | Status: PINNED (the gate's side). Evidence: TESTED. Who acts: nobody (by design). How often this happens depends on the worst-case formula, which does not exist yet (K25). | tests/test_model_gate.py:283; tests: test_a_settle_above_the_reservation_is_passed_through (tests/test_model_gate.py:283) | R E |
| K25.1 | **K25. Not written:** the worst-case formula for the gate. The gate takes the function from the installer. It must cover the system prompt, the messages, the tool schemas and the documents, and the attempts. No function in this tr | guard/model_gate.py:187-190; k1b/loop.py:115 | R U |
| K25.2 | Example: the one worst-case function in the tree prices only the system prompt and the messages, and only the replay command line uses it. Until the connector and store team writes the gate's function, no installed gate has a real | guard/model_gate.py:187-190; k1b/loop.py:115 | R U |
| K25.3 | Status: WAITING. Evidence: UNVERIFIED (read from the code; nothing to test). Who acts: the connector and store team (written order). | guard/model_gate.py:187-190; k1b/loop.py:115 | R U |
| K26.1 | **K26. Not enforced by the database:** the runtime login can rewrite the spend counters. On this branch it holds SELECT, INSERT and UPDATE on the tables `spend` and `spend_month`. | src/hadavin_sdk/store/migrate.py:40; evidence/B-grants-rework.md:60-61 | R U |
| K26.2 | Example: faulty code could lower the booked amount. | src/hadavin_sdk/store/migrate.py:40; evidence/B-grants-rework.md:60-61 | R U |
| K26.3 | Status: OPEN. Evidence: UNVERIFIED (read from the grant map; no database test was run here). | src/hadavin_sdk/store/migrate.py:40; evidence/B-grants-rework.md:60-61 | R U |
| K26.4 | Who acts: the owner decides whether to tighten these rights. If no answer arrives by 2026-11-23 12:00 UTC, they are tightened. Then the connector and store team changes them. | src/hadavin_sdk/store/migrate.py:40; evidence/B-grants-rework.md:60-61 | R U |
| K29.1 | **K29. Not narrowed by the database:** the runtime login can change the stop switch and sign a stop record with any name. On this branch it holds SELECT, INSERT and UPDATE on the table `kill_switch`, and the migrations add no trig | src/hadavin_sdk/store/migrate.py:55; store/migrations/0001_core.sql:94; 0002_audit_chain.sql:25-34 | R U |
| K29.2 | Example: a stop record says "by: operator" when the runtime wrote it. The runtime can also set the flag back to off. | src/hadavin_sdk/store/migrate.py:55; store/migrations/0001_core.sql:94; 0002_audit_chain.sql:25-34 | R U |
| K29.3 | Status: OPEN. Evidence: UNVERIFIED (read from the grant map and the migrations; no database test was run here). | src/hadavin_sdk/store/migrate.py:55; store/migrations/0001_core.sql:94; 0002_audit_chain.sql:25-34 | R U |
| K29.4 | Who acts: the owner decides whether to tighten these rights. If no answer arrives by 2026-11-23 12:00 UTC, they are tightened. Then the connector and store team changes them. | src/hadavin_sdk/store/migrate.py:55; store/migrations/0001_core.sql:94; 0002_audit_chain.sql:25-34 | R U |
| K31.1 | **K31. Not recorded:** whether anything was masked, and the route. | guard/model_gate.py:244-248 | R |
| K32.1 | **K32. Struck in v6:** v5 said the reset login can add any audit row. The reset login belongs to the connector and store team's code and is not on this branch (NOT PROVABLE here). On this branch the audit tables are append-only fo | src/hadavin_sdk/store/migrate.py:42-45; store/migrations/0002_audit_chain.sql:25-34; migrate.py:65 | R U |
| K32.2 | Status: STRUCK. Evidence: UNVERIFIED (read from the migrations). Who acts: nobody until that code is merged; the claim is restored then. | src/hadavin_sdk/store/migrate.py:42-45; store/migrations/0002_audit_chain.sql:25-34; migrate.py:65 | R U |
| K38.1 | **K38. Fixed:** a letter or `_x` glued behind an IPv4 address, a UUID, a phone number written with `+` or an IBAN beside `_` kept it unmasked. Now each is masked, and the glued text stays outside the placeholder. | guard/redact.py:77-89; evidence/G8-build-notes.md:38 | R E P |
| K38.2 | Example: `10.20.30.40_x` now becomes `<IPV4_1>_x`; `DE89..._x` becomes `<IBAN_1>_x`. Shapes that are still not masked are in K70 and K71. | guard/redact.py:77-89; evidence/G8-build-notes.md:38 | R E P |
| K38.3 | Status: FIXED. Evidence: TESTED; MEASURED (a probe on the merged head, `10.20.30.40_x`, `10.20.30.40x`, `x10.20.30.40`, `+14155550132_x`, a UUID with `x` behind it). | guard/redact.py:77-89; evidence/G8-build-notes.md:38 | R E P |
| K38.4 | Who acts: nobody. | guard/redact.py:77-89; evidence/G8-build-notes.md:38 | R E P |
| K39.1 | **K39. Not proven:** that the repeated search finds every value. Each call repeats the patterns and the masking until a round changes no text, at most 5 rounds. A call still changing after round 5 is refused. | guard/redact.py:1238-1262; guard/redact.py:1283-1318 | R E |
| K39.2 | Example: planted text glues a bank code to a secret, then puts the account after that code elsewhere. This needed a third round and is masked. | guard/redact.py:1238-1262; guard/redact.py:1283-1318 | R E |
| K39.3 | Status: OPEN. Evidence: TESTED (the chain; the loop to a fixed point). Who acts: the text and masking team. Two limits that stay are in K72. | guard/redact.py:1238-1262; guard/redact.py:1283-1318 | R E |
| K40.1 | **K40. Fixed:** the last part, up to 7 characters, of a longer token stayed readable in its other copies. This happened when the token was found only after a shorter known secret inside it. | evidence/G7-1.md:290 | R E |
| K40.2 | Example: `password=ab9x`, then `Bearer ab9xqrstu`. The line `note ab9xqrstuvw end` used to show `note <SECRET_1>qrstuvw end`. It now shows `note <BEARER_1>vw end`. | evidence/G7-1.md:290 | R E |
| K40.3 | Status: FIXED. Evidence: TESTED (the tail tests are in tests/test_redact_settle_loop.py, which every merged-tree batch lists). | evidence/G7-1.md:290 | R E |
| K40.4 | Who acts: nobody. See K68. | evidence/G7-1.md:290 | R E |
| K41.1 | **K41. Not fully limited:** how long one call of the secret finder takes. Its time budget (6 seconds of processor time per call) is read before each search round and inside each masking step, the finder build and the written-forms | evidence/G7-1.md:318; guard/redact.py:1238-1319; defaults.py:88; defaults.py:35-45; evidence/G7-1.md:314, :353 | R E |
| K41.2 | Example (MEASURED, processor time, on the test machine): the text `curl -u ` repeated up to the size cap took 4.5 to 5.4 seconds against the 6.0-second budget. A machine about 25 percent slower refuses that text, and a real docume | evidence/G7-1.md:318; guard/redact.py:1238-1319; defaults.py:88; defaults.py:35-45; evidence/G7-1.md:314, :353 | R E |
| K41.3 | Status: OPEN. Evidence: MEASURED. Who acts: the text and masking team. | evidence/G7-1.md:318; guard/redact.py:1238-1319; defaults.py:88; defaults.py:35-45; evidence/G7-1.md:314, :353 | R E |
| K43.1 | **K43. Not masked:** a secret spelled exactly like the redactor's own escaped placeholder (`‹SECRET_1›`, with angle quotes), a run of such spellings, or the cut-off start of one (`<S`, `<SEC`, `<SECRET_`). | guard/redact.py:928-952; tests/test_redact_context_after_sweep.py:498; tests: test_only_the_exact_escaped_shape_is_left_alone (tests/test_redact_own_output.py:170) | R E P |
| K43.2 | Example: `password=‹SECRET_1›` stays as written, on purpose. A tool's error text is read twice, and the first read wrote that placeholder. A real password `<S` or `<SEC` stays readable and gets no map entry. | guard/redact.py:928-952; tests/test_redact_context_after_sweep.py:498; tests: test_only_the_exact_escaped_shape_is_left_alone (tests/test_redact_own_output.py:170) | R E P |
| K43.3 | Status: PINNED. Evidence: TESTED; MEASURED (a probe on the merged head: `password=‹SECRET_1›` unchanged, `password=<S` and `password=<SEC` unchanged). Who acts: nobody. | guard/redact.py:928-952; tests/test_redact_context_after_sweep.py:498; tests: test_only_the_exact_escaped_shape_is_left_alone (tests/test_redact_own_output.py:170) | R E P |
| K50.1 | **K50. Over-matching, measured:** the text-folding scan finds a known name inside a longer word or across a space. No masking path uses this scan yet. | evidence/G1-false-hits-and-cost.md:106-130; defaults.py:257-264 | R E |
| K50.2 | Example: known `mary` found in `summary`. | evidence/G1-false-hits-and-cost.md:106-130; defaults.py:257-264 | R E |
| K50.3 | MEASURED 2026-11-20 per scan of one 10,000-character chunk of ordinary Latin text (repository prose and code, library docstrings, generated text). The value was drawn at random. Rates: 4 letters 5.3 %; 5 letters 1.0 %; 6 letters 0 | evidence/G1-false-hits-and-cost.md:106-130; defaults.py:257-264 | R E |
| K50.4 | The rate is a hit rate on this corpus with random values. It is an upper bound only in that a value that is a whole word counts as a hit. It is NOT a bound for tickets, e-mail, chat or real values. | evidence/G1-false-hits-and-cost.md:106-130; defaults.py:257-264 | R E |
| K50.5 | The share of hits that cut a word: 94 % for 4 letters, 63.4 % for 5 letters, 99 % for short ids, 9 % for 6-letter names. Real Russian interface text 7.6 % and real Chinese interface text 5.2 % for short values; Arabic and Devanaga | evidence/G1-false-hits-and-cost.md:106-130; defaults.py:257-264 | R E |
| K50.6 | Status: STATED. Evidence: MEASURED. Who acts: nobody (the first user of this scan measures again). | evidence/G1-false-hits-and-cost.md:106-130; defaults.py:257-264 | R E |
| K51.1 | **K51. Limited by a CPU budget:** the planted-instruction check stops at 30 seconds of processor time per check and then flags the run as "guard unavailable". The time is that of the thread that runs the check. It fails closed. On | defaults.py:296-302; guard/injection.py:66-77, :94, :149, :166, :257; guard/textnorm.py:250-262, :397-400; tests/test_textnorm_deadline.py:266; evidence/G10-build-notes.md:12-14; textnorm.py:608, :614; injection.py:77, :83; tests: test_the_injection_check_flags_a_run_past_its_budget (tests/test_textnorm_deadline.py:266) | R E P |
| K51.2 | Example: a constructed text of 2,000,000 characters took 185 seconds of processor time without the budget and was flagged at 30.1 seconds with it (MEASURED on the build machine; maxima of named texts, not a bound for every text). | defaults.py:296-302; guard/injection.py:66-77, :94, :149, :166, :257; guard/textnorm.py:250-262, :397-400; tests/test_textnorm_deadline.py:266; evidence/G10-build-notes.md:12-14; textnorm.py:608, :614; injection.py:77, :83; tests: test_the_injection_check_flags_a_run_past_its_budget (tests/test_textnorm_deadline.py:266) | R E P |
| K51.3 | A machine about 1.9 times slower than the build machine flags the slowest ordinary 2,000,000-character text measured (16.0 s) on every run. | defaults.py:296-302; guard/injection.py:66-77, :94, :149, :166, :257; guard/textnorm.py:250-262, :397-400; tests/test_textnorm_deadline.py:266; evidence/G10-build-notes.md:12-14; textnorm.py:608, :614; injection.py:77, :83; tests: test_the_injection_check_flags_a_run_past_its_budget (tests/test_textnorm_deadline.py:266) | R E P |
| K51.4 | The work on a protected value inside one scan has no reading inside it (7.2 to 7.5 s measured for a value of 236,879 distinct letters). | defaults.py:296-302; guard/injection.py:66-77, :94, :149, :166, :257; guard/textnorm.py:250-262, :397-400; tests/test_textnorm_deadline.py:266; evidence/G10-build-notes.md:12-14; textnorm.py:608, :614; injection.py:77, :83; tests: test_the_injection_check_flags_a_run_past_its_budget (tests/test_textnorm_deadline.py:266) | R E P |
| K51.5 | Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The 30-second limit and its scope (per check) are the defaults as built. | defaults.py:296-302; guard/injection.py:66-77, :94, :149, :166, :257; guard/textnorm.py:250-262, :397-400; tests/test_textnorm_deadline.py:266; evidence/G10-build-notes.md:12-14; textnorm.py:608, :614; injection.py:77, :83; tests: test_the_injection_check_flags_a_run_past_its_budget (tests/test_textnorm_deadline.py:266) | R E P |
| K53.1 | **K53. Chosen in a written order:** dashes and curly quotes are ordinary punctuation. Three slash look-alikes make the line withheld. | guard/redact.py:1049-1073; tests/redact_mutants.py:230-260; evidence/G1-mutants-run.md:154-186; evidence/G1-mutants-run.md:194; handover/core-c/ESCALATIONS.md:107 | R E |
| K53.2 | Example: a value right after an em dash (—) is masked in place. | guard/redact.py:1049-1073; tests/redact_mutants.py:230-260; evidence/G1-mutants-run.md:154-186; evidence/G1-mutants-run.md:194; handover/core-c/ESCALATIONS.md:107 | R E |
| K53.3 | A line holding DIVISION SLASH (∕), BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT (╱) or BIG SOLIDUS (⧸) plus a look-alike value is withheld. | guard/redact.py:1049-1073; tests/redact_mutants.py:230-260; evidence/G1-mutants-run.md:154-186; evidence/G1-mutants-run.md:194; handover/core-c/ESCALATIONS.md:107 | R E |
| K53.4 | This choice changed the class of 30 code points. They are 20 dashes and the minus sign, 6 quotes, 3 slash look-alikes and the replacement character U+FFFD, which the fold now drops. Each of the 30 has a test and a deliberate code  | guard/redact.py:1049-1073; tests/redact_mutants.py:230-260; evidence/G1-mutants-run.md:154-186; evidence/G1-mutants-run.md:194; handover/core-c/ESCALATIONS.md:107 | R E |
| K53.5 | Status: PINNED (chosen in the project's written order of 2026-11-20 06:15 UTC). Evidence: TESTED. Who acts: nobody. | guard/redact.py:1049-1073; tests/redact_mutants.py:230-260; evidence/G1-mutants-run.md:154-186; evidence/G1-mutants-run.md:194; handover/core-c/ESCALATIONS.md:107 | R E |
| K60.1 | **K60. Not proven:** that no clickable link remains. The old test used the same patterns as the code it tested. A new test now uses its own patterns and also checks against a link-finding library. | tests/test_p1d_link_oracle.py:1-9; pyproject.toml:52-53; evidence/INT-merged-batch-5.md:5; tests: test_oracle_agrees_with_linkify_it_py (tests/test_p1d_link_oracle.py:218) | R E U |
| K60.2 | Example (UNVERIFIED): a link whose end is not in the test's own, finite list of web-address endings could still slip past both. | tests/test_p1d_link_oracle.py:1-9; pyproject.toml:52-53; evidence/INT-merged-batch-5.md:5; tests: test_oracle_agrees_with_linkify_it_py (tests/test_p1d_link_oracle.py:218) | R E U |
| K60.3 | Status: OPEN. Evidence: TESTED (the independent test); UNVERIFIED (the missed link). Who acts: the text and masking team. | tests/test_p1d_link_oracle.py:1-9; pyproject.toml:52-53; evidence/INT-merged-batch-5.md:5; tests: test_oracle_agrees_with_linkify_it_py (tests/test_p1d_link_oracle.py:218) | R E U |
| K64.1 | **K64. Not protected:** a run's later calls, when planted text holds more than 4,096 values at a placeholder's edge (such as `password=>aaaa1`), or more than 20,480 values in all. The gate then refuses every later call of that run | guard/runmap.py:629-640; tests/test_model_gate.py:2432; guard/runmap.py:599; tests: test_r3_m1b_planted_held_values_past_the_old_cap_of_256_do_not_brick_the_run (tests/test_model_gate.py:2432) | R E U |
| K64.2 | Example: one planted document with 4,097 such lines stops the run. | guard/runmap.py:629-640; tests/test_model_gate.py:2432; guard/runmap.py:599; tests: test_r3_m1b_planted_held_values_past_the_old_cap_of_256_do_not_brick_the_run (tests/test_model_gate.py:2432) | R E U |
| K64.3 | Status: OPEN. Evidence: TESTED (the old cap of 256 is gone; a run is no longer stopped by 257 values). UNVERIFIED: that the run map only grows. Who acts: the text and masking team. | guard/runmap.py:629-640; tests/test_model_gate.py:2432; guard/runmap.py:599; tests: test_r3_m1b_planted_held_values_past_the_old_cap_of_256_do_not_brick_the_run (tests/test_model_gate.py:2432) | R E U |
| K65.1 | **K65. Not refused:** a known secret that spans a fixed framing word. The safety net checks each stretch of text between fixed framing words on its own. | guard/runmap.py:936-949; guard/model_gate.py:51-58; tests/test_model_gate.py:2568; tests: test_r3_m3_the_net_covers_every_secret_value_not_only_the_held_back_ones (tests/test_model_gate.py:2568), test_r3_m3_a_secret_hidden_in_a_placeholder_shaped_token_that_is_not_a_key_refuses_the_call (tests/test_model_gate.py:2535), test_r3_n2_stated_limit_a_value_spanning_a_fixed_framing_word_is_not_replaced (tests/test_model_gate.py:2585) | R E |
| K65.2 | Example: a known secret written as `tool read_logs` inside `password="tool read_logs"` is cut by the fixed word `tool ` and goes out as written. | guard/runmap.py:936-949; guard/model_gate.py:51-58; tests/test_model_gate.py:2568; tests: test_r3_m3_the_net_covers_every_secret_value_not_only_the_held_back_ones (tests/test_model_gate.py:2568), test_r3_m3_a_secret_hidden_in_a_placeholder_shaped_token_that_is_not_a_key_refuses_the_call (tests/test_model_gate.py:2535), test_r3_n2_stated_limit_a_value_spanning_a_fixed_framing_word_is_not_replaced (tests/test_model_gate.py:2585) | R E |
| K65.3 | TESTED: the safety net now covers every known secret of 4 or more characters, not only held-back ones. A secret hidden in a made-up placeholder-shaped token that is not a key of the map refuses the call. | guard/runmap.py:936-949; guard/model_gate.py:51-58; tests/test_model_gate.py:2568; tests: test_r3_m3_the_net_covers_every_secret_value_not_only_the_held_back_ones (tests/test_model_gate.py:2568), test_r3_m3_a_secret_hidden_in_a_placeholder_shaped_token_that_is_not_a_key_refuses_the_call (tests/test_model_gate.py:2535), test_r3_n2_stated_limit_a_value_spanning_a_fixed_framing_word_is_not_replaced (tests/test_model_gate.py:2585) | R E |
| K65.4 | Status: PINNED. Evidence: TESTED. Who acts: nobody. | guard/runmap.py:936-949; guard/model_gate.py:51-58; tests/test_model_gate.py:2568; tests: test_r3_m3_the_net_covers_every_secret_value_not_only_the_held_back_ones (tests/test_model_gate.py:2568), test_r3_m3_a_secret_hidden_in_a_placeholder_shaped_token_that_is_not_a_key_refuses_the_call (tests/test_model_gate.py:2535), test_r3_n2_stated_limit_a_value_spanning_a_fixed_framing_word_is_not_replaced (tests/test_model_gate.py:2585) | R E |
| K66.1 | **K66. Fixed:** a known value inside a tool's name. The gate masked it in the line where the model asked for the tool, but the tool list went out as written, so the model saw two names. | guard/model_gate.py:368-396, :398-404, :744-800; tests/test_model_gate.py:2598 | R E |
| K66.2 | Now a name that is in the tool list stays exact in the line and in the marker. A secret that equals a listed name, or is a piece of one, refuses the call (see K14). | guard/model_gate.py:368-396, :398-404, :744-800; tests/test_model_gate.py:2598 | R E |
| K66.3 | Example: the run map holds `<TENANT_1>` for `billing`. The tool `get_billing_info` is no longer rewritten to `get_<TENANT_1>_info`. | guard/model_gate.py:368-396, :398-404, :744-800; tests/test_model_gate.py:2598 | R E |
| K66.4 | Status: FIXED. Evidence: TESTED. Who acts: nobody. | guard/model_gate.py:368-396, :398-404, :744-800; tests/test_model_gate.py:2598 | R E |
| K67.1 | **K67. Fixed (the list); the install is still waiting:** the install hand-over list and the install test now name the judge's call points. They are the agent loop, the approval cards, the approval summaries and the replay loop. A  | tests/test_gate_install_callers.py:56-63; tests: test_the_judge_call_sites_in_src_are_all_in_the_table (tests/test_gate_install_callers.py:296), test_install_behavioural_the_judge_is_built_on_a_bound_gate (tests/test_gate_install_callers.py:354) | R E |
| K67.2 | Example: the approval summary reaches the judge from a place the old list did not name. | tests/test_gate_install_callers.py:56-63; tests: test_the_judge_call_sites_in_src_are_all_in_the_table (tests/test_gate_install_callers.py:296), test_install_behavioural_the_judge_is_built_on_a_bound_gate (tests/test_gate_install_callers.py:354) | R E |
| K67.3 | Status: FIXED. Evidence: TESTED. Who acts: nobody for the list; the connector and store team installs the gate (K18). | tests/test_gate_install_callers.py:56-63; tests: test_the_judge_call_sites_in_src_are_all_in_the_table (tests/test_gate_install_callers.py:296), test_install_behavioural_the_judge_is_built_on_a_bound_gate (tests/test_gate_install_callers.py:354) | R E |
| K68.1 | **K68. Fixed:** after the secret finder undid a half-made entry, an old record could survive, so a later placeholder with the same number could be restored to the wrong value. | guard/redact.py:1665-1676; tests/test_redact_settle_loop.py:250; tests: test_a_rolled_back_compound_entry_leaves_no_ghost_spelling (tests/test_redact_settle_loop.py:250), test_a_number_reissued_after_a_rollback_does_not_revive_the_ghost_spelling (tests/test_redact_settle_loop.py:261) | R E |
| K68.2 | The text stayed masked; nothing raw went to the model. A tool could have got the wrong account or credential. | guard/redact.py:1665-1676; tests/test_redact_settle_loop.py:250; tests: test_a_rolled_back_compound_entry_leaves_no_ghost_spelling (tests/test_redact_settle_loop.py:250), test_a_number_reissued_after_a_rollback_does_not_revive_the_ghost_spelling (tests/test_redact_settle_loop.py:261) | R E |
| K68.3 | Example: a token found and then undone left a record for `<BEARER_1>`. A new `<BEARER_1>` for another value was later restored as the old one. | guard/redact.py:1665-1676; tests/test_redact_settle_loop.py:250; tests: test_a_rolled_back_compound_entry_leaves_no_ghost_spelling (tests/test_redact_settle_loop.py:250), test_a_number_reissued_after_a_rollback_does_not_revive_the_ghost_spelling (tests/test_redact_settle_loop.py:261) | R E |
| K68.4 | Status: FIXED. Evidence: TESTED. Who acts: nobody. | guard/redact.py:1665-1676; tests/test_redact_settle_loop.py:250; tests: test_a_rolled_back_compound_entry_leaves_no_ghost_spelling (tests/test_redact_settle_loop.py:250), test_a_number_reissued_after_a_rollback_does_not_revive_the_ghost_spelling (tests/test_redact_settle_loop.py:261) | R E |
| K69.1 | **K69. Not checked:** that the run map given to the gate is the run's own, current map. The gate now refuses a plain dict and a `dict(run_map)` copy. It cannot tell the run's own map from another run's map, or from a `RunMap` buil | guard/model_gate.py:528-529; tests/test_model_gate.py:1635; tests/test_gate_install_callers.py:186; tests: test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping (tests/test_model_gate.py:1635), test_r3_m4_an_enforce_function_other_than_the_default_is_marked_and_documented_as_test_only (tests/test_model_gate.py:2739) | R E U |
| K69.2 | Example: the calling code passes yesterday's run map object. Values found today are not masked, and the row says the map was used. | guard/model_gate.py:528-529; tests/test_model_gate.py:1635; tests/test_gate_install_callers.py:186; tests: test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping (tests/test_model_gate.py:1635), test_r3_m4_an_enforce_function_other_than_the_default_is_marked_and_documented_as_test_only (tests/test_model_gate.py:2739) | R E U |
| K69.3 | Status: OPEN. Evidence: TESTED (the dict refusal and the empty-map row); UNVERIFIED (the stale-map case, stated in the code). | guard/model_gate.py:528-529; tests/test_model_gate.py:1635; tests/test_gate_install_callers.py:186; tests: test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping (tests/test_model_gate.py:1635), test_r3_m4_an_enforce_function_other_than_the_default_is_marked_and_documented_as_test_only (tests/test_model_gate.py:2739) | R E U |
| K69.4 | Who acts: the owner decides it together with one question: whether the gate refuses a call when the run map is empty. | guard/model_gate.py:528-529; tests/test_model_gate.py:1635; tests/test_gate_install_callers.py:186; tests: test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping (tests/test_model_gate.py:1635), test_r3_m4_an_enforce_function_other_than_the_default_is_marked_and_documented_as_test_only (tests/test_model_gate.py:2739) | R E U |
| K69.5 | If no answer arrives by 2026-11-23 12:00 UTC, the default applies: the gate refuses an empty map. Then the text and masking team changes the code. | guard/model_gate.py:528-529; tests/test_model_gate.py:1635; tests/test_gate_install_callers.py:186; tests: test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping (tests/test_model_gate.py:1635), test_r3_m4_an_enforce_function_other_than_the_default_is_marked_and_documented_as_test_only (tests/test_model_gate.py:2739) | R E U |
| K70.1 | **K70. Not masked, by design:** glued shapes the glued-text change leaves readable. A phone number or card number written as one run of digits with a letter right before or after it (`x4155550132`, `telephone4155550132`, `x4242424 | tests/test_redact_glued_rest.py:104; tests/g8_cases.py:54; evidence/G8-build-notes.md:19-23; tests: test_limit_rows_are_pinned (tests/test_redact_glued_rest.py:104), test_phone_before_a_full_stop_is_a_stated_limit (tests/test_redact_glued_rest.py:137) | R E P |
| K70.2 | Example: `x4155550132` and `acct_iban_DE89370400440532013000` go out as written (MEASURED on the merged head). A card number written as one run beside `_` (`card_4242424242424242`) is masked as a phone number and kept in the run's | tests/test_redact_glued_rest.py:104; tests/g8_cases.py:54; evidence/G8-build-notes.md:19-23; tests: test_limit_rows_are_pinned (tests/test_redact_glued_rest.py:104), test_phone_before_a_full_stop_is_a_stated_limit (tests/test_redact_glued_rest.py:137) | R E P |
| K70.3 | Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The defaults are as built. A phone directly before a full stop is not masked. An IBAN beside `_` is masked only after a short word at the start of a name or before a sh | tests/test_redact_glued_rest.py:104; tests/g8_cases.py:54; evidence/G8-build-notes.md:19-23; tests: test_limit_rows_are_pinned (tests/test_redact_glued_rest.py:104), test_phone_before_a_full_stop_is_a_stated_limit (tests/test_redact_glued_rest.py:137) | R E P |
| K71.1 | **K71. Readable remainder of a long token:** a UUID or a number of 10 or 11 digits, set off by `_`, is now cut out of a long token. The rest of the token stays readable when it is under 40 characters. Before the change, the whole  | tests/g8_cases.py:247-309; tests/test_redact_glued_rest.py:263; guard/redact.py:30-31; evidence/G8-build-notes.md:30-34; tests: test_a_value_inside_an_opaque_token_is_a_stated_limit (tests/test_redact_glued_rest.py:263) | R E P |
| K71.2 | Example (MEASURED on the merged head): `tok_<uuid>_` followed by 32 characters becomes `tok_<UUID_1>_` and the same 32 characters, readable. With a remainder of 40 characters or more the remainder is masked too. | tests/g8_cases.py:247-309; tests/test_redact_glued_rest.py:263; guard/redact.py:30-31; evidence/G8-build-notes.md:30-34; tests: test_a_value_inside_an_opaque_token_is_a_stated_limit (tests/test_redact_glued_rest.py:263) | R E P |
| K71.3 | Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. This is the limit as built. A follow-up change that keeps the token whole was measured on scratch copies; nothing of it is built. | tests/g8_cases.py:247-309; tests/test_redact_glued_rest.py:263; guard/redact.py:30-31; evidence/G8-build-notes.md:30-34; tests: test_a_value_inside_an_opaque_token_is_a_stated_limit (tests/test_redact_glued_rest.py:263) | R E P |
| K72.1 | **K72. Not masked whole:** overlapping values. Two overlaps leave a readable part of a value the map holds. (1) A written form that is completed only in a later round cannot recover text an earlier round already masked, so its lit | tests/test_redact_settle_loop.py:607; defaults.py:112-114; tests: test_an_overlap_completed_only_in_a_later_round_leaves_the_swallowed_part_readable_a_stated_limit (tests/test_redact_settle_loop.py:607), test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit (tests/test_redact_settle_loop.py:1376) | R E |
| K72.2 | Example: plain values `abcdefgh` and `efghijkl` in `abcdefghijkl` become `<S1>ijkl`. A log author who controls the order of lines can cause both cases and needs no secret knowledge. | tests/test_redact_settle_loop.py:607; defaults.py:112-114; tests: test_an_overlap_completed_only_in_a_later_round_leaves_the_swallowed_part_readable_a_stated_limit (tests/test_redact_settle_loop.py:607), test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit (tests/test_redact_settle_loop.py:1376) | R E |
| K72.3 | Status: PINNED. Evidence: TESTED. Who acts: the text and masking team (a planned change, not merged). | tests/test_redact_settle_loop.py:607; defaults.py:112-114; tests: test_an_overlap_completed_only_in_a_later_round_leaves_the_swallowed_part_readable_a_stated_limit (tests/test_redact_settle_loop.py:607), test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit (tests/test_redact_settle_loop.py:1376) | R E |
| K73.1 | **K73. Refused, not read:** a hostile text can make the secret finder refuse a whole document. The refusals fail closed: nothing is shown, and a real document in the same text is lost. | guard/redact.py:1793; defaults.py:98-125 | R E |
| K73.2 | The refusal words are: `SpelledWorkTooMuch`, past 4,000,000 units of work in the written-forms scan; `SpelledMemoryTooMuch`, past 1,000,000 characters of written forms in one call; `InputTooLarge`, the time or size limit; `NotSett | guard/redact.py:1793; defaults.py:98-125 | R E |
| K73.3 | Example (MEASURED): a text of 2,800 written forms in 213,000 characters, then 262,000 characters of copies, needs 6.3 million units and is refused after 0.49 seconds of processor time. | guard/redact.py:1793; defaults.py:98-125 | R E |
| K73.4 | Status: STATED (written in the code's own notes). Evidence: MEASURED. Who acts: nobody. | guard/redact.py:1793; defaults.py:98-125 | R E |
| K74.1 | **K74. Not limited:** the memory the secret finder holds for a very large plain value. A hostile document can force about 1 GB of finder memory in one call. | defaults.py:119-120 | E U |
| K74.2 | Example (MEASURED earlier): eight distinct plain values of 260,000 characters each, through one bundle call, peaked at 956 MB (tracemalloc). | defaults.py:119-120 | E U |
| K74.3 | Status: OPEN. Evidence: MEASURED. Who acts: the text and masking team (a ticket and a plan review come first). The caller's own memory guard is the connector and store team's. | defaults.py:119-120 | E U |
| K75.1 | **K75. Extra map entry, accepted:** a tool's error text read twice can make one extra map entry for each distinct token of another kind written after a key. The model sees a secret placeholder instead of the kind. Nothing real is  | guard/redact.py:936-948; tests/test_redact_own_output_hardening.py:202; evidence/E9-own-output.md:6 | R E P |
| K75.2 | Example: `token=<JWT_1>` becomes `token=<SECRET_1>`, and `<SECRET_1>` stands for `‹JWT_1›`. Also `password=‹EMAIL_1› host` becomes `password=<SECRET_1> host` (MEASURED on the merged head). | guard/redact.py:936-948; tests/test_redact_own_output_hardening.py:202; evidence/E9-own-output.md:6 | R E P |
| K75.3 | Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The alternative (exempt the escaped tokens of other kinds on the tool-error path only) is not built. | guard/redact.py:936-948; tests/test_redact_own_output_hardening.py:202; evidence/E9-own-output.md:6 | R E P |
| K76.1 | **K76. Fail-safe, accepted:** a placeholder written in a spelled form (`&lt;TENANT_1&gt;`, `%3CTENANT_1%3E`, `&#60;IPV4_1&#62;`) can come back from the secret finder as the decoded placeholder shape, when its digits are not masked | - | R E P |
| K76.2 | Example: `&lt;TENANT_4155550132&gt;` becomes `&lt;TENANT_<PHONE_1>&gt;`, as typed with the digits masked (MEASURED on the merged head). | - | R E P |
| K76.3 | Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. | - | R E P |
| item 2 | merged-tree batches of 15 test files passed; last result 2,687 passed, 1 skipped, 5 xfailed; the 5 xfails are the install tests | evidence/INT-merged-batch-5.md:4; tests/test_gate_install_callers.py:233, 243, 280, 327, 353 (5 `@_xfail`) | E R |
| item 4 | three gate reviews on file; none for round 4 | ls handover/core-c/tickets: F-result-review-1.md, -2.md, -3.md only (3 files); git log: b83accc65 is gate round 4 | R |
| item 6 | no code commit for G4 or G9 on this branch | git log --oneline 6b990d9..HEAD, filtered on code commits and on G4/G9: no G4/G9 code commit (output in section "Commands run") | R |
| item 7 | summary names 32 of 76 gaps | build.py PART1_GAPS list (32 distinct); 4.3 of v6 lists them | R |
| item 9 | NOT RUN list; the test service uses database 17.10 | .github/workflows/ci.yml:41 (`postgres:17.10`); evidence/INT-merged-batch-5.md line 6 ("NOT RUN here: the whole suite, perf tests ..."); STATUS-BOARD.md line 15 | R E |
| item 12 | no written confirmation of the 2026-11-23 date | grep "11-23" in handover/core-c/ORDERS.md and DECISIONS.md: no match | R |
| item 21 (4th bullet) | glued IPv4, `+` phone, UUID, IBAN are masked now | probe (this file, section Probes): `10.20.30.40_x` -> `<IPV4_1>_x`; evidence/G8-build-notes.md:38 | P E |
| item 23 | three v5 leak paths closed; one limit remains | see K65.1-K67.x rows | R E |
| item 24 | the gate worst-case function is not written; the one function in the tree serves the replay command line | model_gate.py:187-190; k1b/loop.py:115, :170; llm/common.py has no worst_case_usd (grep) | R U |
| items 26-28, 44, 45 | STRUCK (store code not on branch) | tests/contracts/test_t1_reserve_cap.py:16, :41, :50; grep reserve_spend src: empty; store/migrations ends 0005 | R |
| item 31 | runtime login holds SELECT, INSERT, UPDATE on spend, spend_month | src/hadavin_sdk/store/migrate.py:40, :53-54 | R U |
| item 32-33 | K68 fixed | see K68 rows | R E |
| item 34 | runtime login can change the stop switch; no trigger | store/migrate.py:55; store/migrations/0001_core.sql:94; triggers only on audit tables (0002_audit_chain.sql:25-34) | R U |
| items 35-38 | K14, K64, K13, K41 as in part 2 | see those rows | R E U |
| items 47-48 | K39 | see K39 rows | R E |
| items 49-54 | K70 to K75 | see those rows | R E P |
| decision 1 row | narrower rule built and tested; also refuses a piece of a listed name | model_gate.py:368-396; tests/test_model_gate.py:2624 | R E |
| decision 3 row | the plan has 8 versions and 8 review rounds; not built | handover/core-c/tickets/G4-P1c-redactor-gaps-v8.md, G4-review-8-design.md, G4-review-8-readiness.md exist; git log: no G4 code commit | R |
| decision 5 row | runtime login rights; purge and reset rights struck | store/migrate.py:40, :53-55; no `reset` in store/migrate.py | R U |
| decision 6 row | the gate refuses a dict or a copy; accepts an empty RunMap | model_gate.py:528-529, :245, :731 | R |
| 1b L-D13 | default: not masked | tickets/G8-glued-rest-gap-v6.md:1022-1060 (row L-D13); tests/test_redact_glued_rest.py:137; probe `call 415-555-0132.` unchanged | R E P |
| 1b L-D15 | default: short-word IBAN rule; 16 of 24 shapes leave the whole IBAN readable (base 24, option (b) 13) | tickets/G8-glued-rest-gap-v6.md section 6.1 table (line "whole IBAN readable, of 24"); evidence/G8-build-notes.md:19-23; redact.py:77-89 | R E |
| 1b L-D17 | default: no card check; rows 97-99 strict xfails | tickets/G8-glued-rest-gap-v6.md L-D17 row; probe `x4242424242424242` unchanged, `card_4242424242424242` -> `card_<PHONE_1>` | R E P |
| 1b E16 | default: accept L15 as merged | handover/core-c/ESCALATIONS.md E16 and "E16 update"; tests/g8_cases.py:247-309 | R E |
| 1b G10 D4 | 30 CPU s per check | defaults.py:296-302; tickets/G10-textfold-deadline-v4.md section 10 (D4 row) | R E |
| 1b E9 | option (a) as built | redact.py:936-948; E9-own-output.md:47-54 | R E |
| part 3 | refusal order, pins, 15.1.0, tag with the Unicode edition | defaults.py:214, :217; textnorm.py:1720-1735, :460; app.py:128-134; pyproject.toml:8; python 3.13.3 prints unidata 15.1.0 (probe3 below) | R P |
| C1 | bind accepts only a RunMap or NO_MAP; empty RunMap accepted, row `map_enforced_empty` | model_gate.py:528-529, :245, :731 | R |
| C2 | one budget per call: 32,768 steps, CPU deadline 6.0 s into the sweep, monotonic-clock deadline between values, code `mask_budget_exceeded`, 7 s note, 4,096 held / 20,480 entries | runmap.py:625-640 (8 x 4096 = 32,768 steps; 5 x 4096 = 20,480), :643-675 (`EnforceBudget.check` reads `time.monotonic` and `time.thread_time`), :689-777; defaults.py:88; model_gate.py:221, :430-434, :59-66 | R |
| C3 | net checks every known secret of 4+ characters per chunk; spanning limit | runmap.py:936-949; model_gate.py:51-58 | R E |
| C4 | framing_refused on a piece of a listed tool name; listed names stay exact | model_gate.py:368-396, :744-800, :80-86 | R E |
| C5 | interrupt rows; cost_unknown for -0, absurd exponent, raising property; install test: 4 judge sites, 5 strict xfails | model_gate.py:570-575, :610, :616, :327-340 (`usable_amount`), :343-352 (`usable_cost`); tests/test_gate_install_callers.py:56-63, :233-353 | R |
| C6 | settle to a fixed point, 4 rounds after the first pass, NotSettled; deadline places | redact.py:1238-1319, :2145, :1358-1364 | R |
| C7 | refusal words and limits | redact.py:1793, :1996, :1364; defaults.py:98-125 | R E |
| C8 | E10 limits and E14 | tests/test_redact_settle_loop.py:607, :1376; ESCALATIONS.md E10, E14; defaults.py:112-120 | R E |
| C9 | glued masks incl. version numbers and `order_1234567890`, `card_...` as phone | probe2 (this file): `python3.11.4.1` -> `python<IPV4_1>`; `order_1234567890` -> `order_<PHONE_1>`; probe: `card_4242424242424242` -> `card_<PHONE_1>`; G8 ticket L-D8, L-D10 rows | P E |
| C10 | not masked by design: list | probe: `x4155550132`, `telephone4155550132`, `x4242424242424242`, `call 415-555-0132.`, `call +44 20 5550 1234.` -> `call <PHONE_1> 1234.`, `acct_iban_DE89...`, `xDE89...` | P E |
| C11 | UUID / 10-11 digit number inside a long token cut out; remainder under 40 readable | probe: UUID token; probe2: phone token; tests/g8_cases.py:247-309; evidence/G8-build-notes.md:30-34 | P E |
| C12 | spelled placeholder decoded by redact_text; 15 pin cases | probe2: `&lt;TENANT_1&gt;` -> `<TENANT_1>` via redact_text; tests/test_runmap_e15_placeholder_spellings.py; ESCALATIONS.md E15 update | P E |
| C13 | 30 code points: 20 + 6 + 3 + 1; each has a Q9 mutant and a killer | redact.py:1049-1073; tests/redact_mutants.py:230-260; evidence/G1-mutants-run.md:154-186 (30 rows KILLED), :194 | R E |

## Table C: gaps carried unchanged from v5 (statements not re-proved beyond test and file existence)

| gap | check made at head |
|---|---|
| K1 | test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job -> tests/test_model_gate.py:361 |
| K2 | test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept -> tests/test_runmap_enforce_map.py:235; test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept -> tests/test_runmap_enforce_map.py:263 |
| K3 | test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate -> tests/test_model_gate.py:403; test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced -> tests/test_runmap_enforce_map.py:103; test_stated_limit_a_copy_split_by_nul_characters_is_not_found -> tests/test_runmap_enforce_map.py:422; test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced -> tests/test_model_gate.py:1753 |
| K4 | test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced -> tests/test_model_gate.py:1742 |
| K5 | test_stated_limit_partial_overlap_leaves_a_tail -> tests/test_runmap_enforce_map.py:179; test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent -> tests/test_model_gate.py:566 |
| K6 | test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched -> tests/test_model_gate.py:2278 |
| K7 | test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced -> tests/test_runmap_enforce_map.py:405; test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder -> tests/test_runmap_enforce_map.py:413; test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass -> tests/test_runmap_enforce_map.py:435 |
| K8 | test_t20_system_and_tools_are_not_touched -> tests/test_model_gate.py:1683; test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched -> tests/test_model_gate.py:1773 |
| K9 | test_no_map_means_no_enforce_step_at_all -> tests/test_model_gate.py:631; tests/test_gate_install_callers.py exists |
| K18 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K19 | tests/test_gate_install_callers.py exists |
| K21 | test_m5_a_zero_cost_reply_is_settled_at_zero -> tests/test_model_gate.py:1070 |
| K22 | test_pin_a_reply_with_no_usable_cost_is_not_settled -> tests/test_model_gate.py:1228; test_o17_2_ -> tests/test_model_gate.py:2142 |
| K23 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K27 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K28 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K30 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K31 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K33 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K34 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K35 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K36 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K37 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K42 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K44 | test_a_secret_wrapped_in_lookalike_brackets_is_masked -> tests/test_redact_own_output_hardening.py:46; tests/test_redact_own_output_hardening.py exists |
| K45 | test_the_tool_error_path_adds_no_map_entry_and_keeps_the_escaped_text -> tests/test_redact_own_output.py:51; tests/test_redact_own_output.py exists |
| K46 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K47 | tests/test_redact_g3_port.py exists |
| K48 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K49 | test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed -> tests/test_textnorm_mixed_script_micro.py:115; tests/test_textnorm_mixed_script_micro.py exists |
| K52 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K54 | test_known_difference_from_main_an_invisible_character_between_a_letter_and_its_accent_now_joins_them -> tests/test_evidence_decomposed.py:157; tests/test_evidence_decomposed.py exists |
| K55 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K56 | tests/test_undo_composes.py exists |
| K57 | tests/test_injection_chunk_boundary.py exists |
| K58 | test_a_wrong_unicode_version_refuses_a_pilot_build_before_any_backend_is_made -> tests/test_app_unicode_check_order.py:18; tests/test_app_unicode_check_order.py exists |
| K59 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K61 | test_glued_email_regression_digit_or_underscore_behind_the_address -> tests/test_text_parts_together.py:213; test_glued_addresses_are_masked_whole_in_one_pass -> tests/test_p1d_a_paths.py:377; tests/test_text_parts_together.py exists; tests/test_p1d_a_paths.py exists |
| K62 | no test or file cited (source is a document or a code reading; see 4.2 row) |
| K63 | no test or file cited (source is a document or a code reading; see 4.2 row) |

Not re-read in this pass (carried): approvals/gate.py changes of the P1d-a review rounds 2 and 3 beyond what K60 names (the diff is 44 lines); K42, K59 and K18 examples; the claims in v5 part 1 items 13 to 20, 22, 24, 25, 29, 30, 39 to 43 and 46. They are as v5 worded them.

## Table D: statements struck from v6 (NOT PROVABLE at this head, or no longer true)

| id | v5 statement | reason |
|---|---|---|
| S1 | K32: the reset login can add any audit row | reset login not in this tree (grep reset in store/migrate.py empty); source was core-b ref 576f292 |
| S2 | K26: the purge login can delete an open reservation | table spend_reservations not in this tree; v5 cited evidence/B-grants-rework.md on core-b ref |
| S3 | K29: the reset login can change any stop-switch row | no reset login in this tree |
| S4 | K24: booked money can pass the cap once (1.00 + 1.00 + 2.50 = 4.50 USD), PostgreSQL 16.15 test | tests/contracts/test_t1_reserve_cap.py skips (reserve_spend missing) |
| S5 | K20: three failed calls book 3.00 USD for the day and the month | needs the store; not on branch |
| S6 | item 26: "worked out from the store rules" (three failed calls stop an agent) | same |
| S7 | items 27-28: TESTED that booked money passes the cap; 4.50 USD example | same as S4 |
| S8 | item 44 and 2.2 bullets: 50 connections, 47 refused, five other pairs, two agents, month cap | same; tests skip |
| S9 | 2.2: "These tests show reservations stop at the cap ... K24 shows it can pass, K26 not tested" | same |
| S10 | item 45: booked money can still pass the cap (items 27, 31) | same |
| S11 | K13: reviewer estimate of 128 million steps for 262,144 characters with 500 planted values | superseded: the budget is built; the gate note gives about 7 s (model_gate.py:63) |
| S12 | K13: before the change 100 messages at 6 s each could take 600 s (worked out, not run) | no longer describes the code |
| S13 | K13: the final masking step gets no time limit; two parts use different clocks | code at head passes a CPU deadline into the sweep (runmap.py:744-777) |
| S14 | K41: 6-second budget checked before each round, not inside one; 0.167 s to 0.395 s; 4.00 s | round 2 code; the deadline is now read inside sweeps, builds and scans (redact.py:1238-1319) |
| S15 | K41/item 38: "one call can take its budget plus one whole search round" (reviewer reading) | replaced by the settle docstring statement of what is not checked |
| S16 | K39: line changed by the patterns but not the masking step is not searched again | settle re-reads the union of both (redact.py:1245-1250) |
| S17 | K40: 20 of 28 new tests failed before the change | withdrawn by evidence/G7-1.md:290 |
| S18 | K64: more than 256 values at a placeholder edge | cap is 4,096 (runmap.py:636) |
| S19 | K65 (v5): the safety net checks held-back values only | net covers every secret value (runmap.py:936-949) |
| S20 | K66 (v5): tool list goes out as written while the line is rewritten | names in `tools` stay exact (model_gate.py:744-800) |
| S21 | 2.1: tests caught each of 66 deliberate code breaks; 81 of 81 | no run at this head; the list is larger (105 per requests/3) |
| S22 | 2.5: one text can go through up to 7 calls of the secret finder (reviewer reading) | not shown by the code |
| S23 | 2.9 and item 9: 238 of the 240 text-folding breaks not run; 2 ran (spacing-mark rule) | list is 256 now; builder ran 25 (evidence/G10-build-notes.md:14, :29) |
| S24 | item 4 / 2.0: third review found 9 major faults; gate fix round 4 running; secret finder fix round 3 running | both merged; process state of head 6b990d9 |
| S25 | item 6 (v5): the team must finish gate fix round 4 and secret finder fix round 3 | both merged |
| S26 | item 3 / 2.0 INTERNAL: 12,392-test pick batch, 135 files, c9478a9 / a2b6311 / 0fcc5e1 commit story | process history of head 6b990d9; not needed |
| S27 | 2.7 INTERNAL: 27 test functions in tests/test_p1d_a_paths.py (counted at HEAD) | process count of head 6b990d9; not recounted |
| S28 | K19 line cite "line 41" | the row is at line 44 (tests/test_gate_install_callers.py:44) |
| S29 | part 3 and K63 sentence "Python 3.12 carries 15.0.0" as a flat fact | kept only as the code note textnorm.py:143, NOT RUN on a real 3.12 |
| S30 | K10, K11, K15, K16 evidence "NOT RUN (no recorded batch)" | now in batches 1-5 |
| S31 | item 3/K39/K40/item 47 caveat "which saved version of the code the batch ran on" | closed by batches 1-5 |
| S32 | K12 line "a safety net ... saved on the shared branch, in no recorded batch" | net is in the code and in the batches |

## Statements kept but worded UNVERIFIED (a reading, not a run)

- K17 (race: two writers) - wording says UNVERIFIED; proof is the code comments runmap.py:603-606, model_gate.py:119-121, not a run
- K64 "the run map only grows" - UNVERIFIED; comment runmap.py:599, requests/3 section 7
- K13 "about 7 seconds" - UNVERIFIED; the gate's own note model_gate.py:63
- K69 stale-map case - UNVERIFIED; model_gate.py:100-106 docstring
- K26, K29 - read from the grant map; no database test run here
- K60 missed link - UNVERIFIED
- K45 "no other place does this" (carried), K42, K59 example, K18 example (carried readings from v5)
- v5 part 1 items 13-20, 22, 24, 25, 29, 30, 39-43, 46, carried unchanged (their K rows are in table C)

## Open questions for the lead

1. **The store code is not on cloud/core-c.** v5 stated tested cap behaviour (50 connections, booked money past the cap, purge and reset rights) from core-b's tree. At a60da3394 `reserve_spend` does not exist in src, migrations stop at 0005, and the T1 tests skip. v6 struck those statements (table D S1 to S10) and says so. Decision 5 now rests on the runtime rights in store/migrate.py:40, :53-55 only. Restore the struck statements when core-b's store is merged, or tell core-c which tree to prove them on.
2. **Wall clock.** The gate's `EnforceBudget.check` also reads `time.monotonic` (runmap.py:659-661) and the CHANGELOG line C2 says so. No other part of v6 claims a wall-clock guard: G10 (K51) is CPU only; the redactor (K41) is CPU only. If the rule "no claim of a wall-clock guard" was meant to cover the gate too, strike the monotonic sentence in C2 and K13's INTERNAL line.
3. **L-D13, L-D15, L-D17, E16, G10 D4, E9** are written with the default the code has and marked LEAD DECISION (part 1b; marks in [INTERNAL] lines and in the CHANGELOG lines).
4. **Head.** The request named 7c31dbc97; the latest fetched head is a60da3394. If the lead wants v6 pinned to 7c31dbc97, K76 (E15) and the d399ac5f3 pins must come out.
5. **Evidence-level tally** of v5 (4.3, second table) was dropped, not recounted (v6 4.3 says so).
6. **No fresh style review** was run from the laptop, as ordered. Sentences over 30 words remain only in the owner decision table (part 1a rows 3, 5, 6), as in v5.

