# CROSS-LANE: mismatches between core-a, core-b and core-c before integration
Written by a read-only lookup agent of core-c, 2026-11-20 06:15 to 06:20 UTC (STANDING ORDER 016 item 4c; queue item CROSS-CHECK). Nothing was run: every row is from reading.
Refs read: A = refs/inputs/cloud-core-a at 0e7d539; B = refs/inputs/cloud-core-b at 576f292; M = refs/inputs/main at 51c9fc4 (merge base of both); C = core-c HEAD (7b58e21 at 06:15, 93f7f24 at 06:18).
The gate was read in the working tree at 06:15:50 UTC: src/hadavin_sdk/guard/model_gate.py, 346 lines, equal to HEAD. Its behaviour is the same as commit 619a3e5 (only comments, AUDIT_CODES and formatting changed since), which is the copy core-a tested and core-b reviewed.

## 1. What the other two have pushed
core-b (B), last 20 commits: mostly board commits; code commits are 8db9c29 "code F-store" (migration 0007, store reserve/settle/expire/purge, Limits.reserve and settle, tick step), 95a9d28 "code C" changelog, 9d72569 and 0b0b150 "code A" tests, f5dc81e mutant scripts, cf2d7d0 "code F: producers text".
- Diff M...B, src and tests: 35 files, +4369 -82. Built: step A audit drain (audit/chain.py), step B stop state (migration 0006, reset role in store/migrate.py), step C price constraint (config.py, models.py), F-store (limits.py, store/*, runtime/tick.py). Also Config.triggers and App.secrets for core-a (B:src/hadavin_sdk/app.py:56-58, 171-176).
- NOT built on B: the install. No file under B:src or B:tests names ModelGate, GateRefused or UnmaskedInput; the only gate lines are the two producers rows (B:src/hadavin_sdk/guard/producers.py:61, 69). Limits.charge is still there (B:src/hadavin_sdk/limits.py:45) and the loop still charges (B:src/hadavin_sdk/runtime/agent_loop.py:488-489). Budget is not in limits.py yet.
- Handover: tickets A, B, C, F-store, F-install (+ reviews); interfaces/README.md, i_store_spend.py, ii_meter.py, ii-meter.md ("FINAL", ten points); notes/core-c-model_gate-copy.md (the gate at 619a3e5); requests/core-c-1.answer.md.
core-a (A), last 20 commits: board commits, two "code D+E: WIP snapshot" (66348ed, 3251de4: "builders running, not the tested state"), lead orders 014 to 016.
- Diff M...A, src and tests: 21 files, +9758, all NEW files: triggers/endpoint.py, server.py, worker.py, testing/crash.py, 16 test files. No existing file is changed.
- It wrote tests for the other two sessions: tests/contracts/test_model_gate_contract.py (1377 lines, for core-c's gate), test_store_spend_reservations.py and test_t1_reserve_cap.py (for core-b's store), tests/test_trigger_config.py (for core-b's config).
- core-a is running a TRIAL INTEGRATION of all three branches now (A:handover/core-a/STATUS-BOARD.md:49, row O14-1, "RUNNING 5"): its findings will overlap this file.

## 2. The gate contract: what core-c built against what core-b expects
What matches (checked on both sides, no action):
- Constructor and bind: `ModelGate(llm, *, meter, audit, worst_case, enforce=...)` and `bind(agent_id, run_id, *, mapping=None, principal=None, source=...)` (C:model_gate.py:176-198) = B:handover/core-b/tickets/F-install.md:14 (U1) and :33 (V7).
- Meter shape: C:model_gate.py:76-79 = B:src/hadavin_sdk/limits.py:26-35, same names, order and keywords. The gate calls `reserve(agent_id, worst, run_id=run_id)` (C:model_gate.py:240) and `settle(reservation, usd)` (:283).
- worst_case: six positional arguments, route as a name (C:model_gate.py:82-92, 239) = F-install.md:27 (V1).
- Settle rule (a)/(b)/(c) (C:model_gate.py:61-70, 255-275) = F-install.md:17 (U4) and B:handover/core-b/interfaces/ii-meter.md:21-22.
- A meter refusal passes through unchanged (C:model_gate.py:241-245) = F-install.md:32 (V6). A client that is already a gate is a TypeError (C:model_gate.py:185-186) = F-install.md:33.
- The five reasons (C:model_gate.py:117-119) = the five raised by B:limits.py:68, 72, 87, 90. Audit codes provider_error and provider_exhausted (C:model_gate.py:108-109) are the strings the loop writes today (B:agent_loop.py:483-486) and tests read (B:tests/test_p1a_fixes.py:38, tests/test_p5_llm.py:59).
- Every message content at the five call sites is a str (B:agent_loop.py:465, 580, 583; guard/judge.py:73; evals.py:74; k1b/loop.py:147, 212, 214), so the gate's "content that is not str is refused" (C:model_gate.py:300-302) refuses nothing there.
- Producers row: MODEL_CALLERS and OUTSIDE_THE_CHOKE_POINT hold guard/model_gate.py on B (producers.py:61, 69) and not on C. No PRODUCERS row, as planned.

Mismatches (C = src/hadavin_sdk/guard/model_gate.py in the working tree; FI = B:handover/core-b/tickets/F-install.md):
| # | what core-c built | what core-b expects or built | file:line core-c | file:line core-b | who should change | severity |
|---|---|---|---|---|---|---|
| 1 | rule (b) needs a mark `refused_before_response` on ProviderError; nothing sets it, so every failed call keeps its worst case booked | FI V5 counts on "the mark from ORDER 013"; no line in B:src sets or names it; request 2 is not answered in B:handover/core-b/requests/ | C:134-140; handover/core-c/requests/2-refused-before-response.md:1-12 | FI:31; B:handover/core-b/ORDERS.md:111-112 | core-b (owner of llm/retry.py, llm/protocol.py): build the mark and publish its name | HIGH: until then a bad key or throttling eats a small daily budget for at least 3600 s |
| 2 | the client gets a NEW list on every call (`sent`), never the caller's list | FakeLLM keeps the list it is given by reference (M:src/hadavin_sdk/llm/fake.py:44); today that is the loop's growing list, behind the gate it is a per-call copy. Tests that read `rt.llm.calls[i]["messages"]` may see other content | C:298, 309 | FI:59 (tests read `rt.llm.calls`: test_s5_runtime.py:64, 98, 119; test_peel_run_id.py) | core-b at install: run those files first; not a gate change | MEDIUM (unverified: no test was run) |
| 3 | only the five published reasons are copied into an audit row; any other `.reason` becomes `reserve_refused` | Budget will raise `SpendRefused("usd_cap")`, a sixth reason, "when the lead agrees" | C:117-119, 242-244 | FI:28 (V2); B:src/hadavin_sdk/k1b/loop.py:155 | core-c adds "usd_cap" to SPEND_REASONS in the same change in which core-b updates ii_meter.py; nothing breaks before | LOW (eval and replay bind with audit=None, FI:29) |
| 4 | a local copy of the Meter Protocol; the comment says SpendRefused "is not in limits.py yet" | both are in limits.py since 8db9c29 | C:49-55, 76-79 | B:limits.py:17-35 | core-c after core-b's F-store is merged: import both from hadavin_sdk.limits, delete the copy, fix the comment | LOW (duplicate, same shape) |
| 5 | comment: "the sweep closes the row after 3600 seconds" | expiry age is the LARGER of 3600 s and the stuck-run age | C:70 | B:src/hadavin_sdk/runtime/tick.py:264-267; ii-meter.md:26 | core-c: comment only | LOW |
| 6 | the gate writes the `llm chat failed` row itself, with principal = agent id unless `principal=` is passed, source "gate" | the loop's own row uses the run's event shape (`self._event(run, ...)`); FI V7 leaves principal and source at the gate's defaults; FI U9 says audit-shape pins are "read at build" | C:202, 328-346 | B:agent_loop.py:240-241, 486; FI:22, 33 | core-b decides at install: pass `principal=` of the run, or accept agent id; state it in the ticket | LOW to MEDIUM (a test that pins principal or source on that row would fail; not searched) |
| 7 | any `usable_cost` (finite Decimal, 0 or more) is sent to settle | settle refuses an amount of 1000000000 or more with ValueError; the gate then writes `ok` / `settle_failed` and returns the reply | C:143-148, 278-286 | ii-meter.md:18, 20 | nobody: behaviour is safe (worst case stays booked); listed so the code `settle_failed` is expected | INFO |
| 8 | an unknown agent (KeyError from reserve) is audited `reserve_refused` and re-raised as KeyError, not as GateRefused | FI V6: "any other exception ... before provider contact -> NEEDS_PERSON gate_error" | C:241-245 | B:limits.py:69; FI:32 | nobody; core-b's `except` must be wider than (SpendRefused, GateRefused), as V6 already says | INFO |
| 9 | Limits.settle writes its own row on an overshoot (domain limits, operation overshoot, source meter) besides the gate's `llm chat ok` row | two audit rows for one call | C:275, 286 | B:limits.py:98-109 | nobody; tests that count rows per call must expect it | INFO |
| 10 | AS BUILT item 5 says a row has "no agent id" | the default principal IS the agent id | handover/core-c/tickets/F-gate-wrapper-body.md:146; C:202 | n/a | core-c: one line in the ticket | INFO |
Stale text on core-b's side (core-b should fix, no code effect): the lead's draft below the line still says `mask_check=MASK_CHECK`, `bind(agent_id, run_id)`, "the gate only checks" and "H2 ... is refused" (FI:45, 69, 83, 188); B:handover/core-b/interfaces/README.md contract 10 still shows the helper without `output_schema`; B:limits.py:27 says the Meter is implemented by Limits only.

## 3. Files more than one session edits
core-a changes no existing file, so every overlap is core-b against core-c. "Planned" = core-b's install list FI:37 (V11), not pushed yet.
| file | core-b | core-c | kind |
|---|---|---|---|
| src/hadavin_sdk/defaults.py | appends 20 lines after line 131 | appends 80 lines after line 131 (HEAD); wip-g3-p2d also changes 45-48; planned WORST_CASE_OVERHEAD_BYTES | SAME LINES: both append at the end of file. Git conflict for certain; keep both blocks |
| CHANGELOG.md | inserts 75 lines after line 5, edits 22, 49, 56, 63, adds after 221 | HEAD adds after 267 and 404; wip-g3-p2d and wip-g2-p1d-a insert after line 5 | SAME LINES at line 5 for the wip branches (conflict); HEAD itself is in other regions |
| src/hadavin_sdk/app.py | 56-58, 171-176, 304 | 30 (import), 132-134 | different regions; clean |
| README.md | line 33, after 57 | after line 14 | different regions; clean. Planned: both add the security sentences (handover/core-c/SECURITY-WORDING-draft.md against FI V11) |
| src/hadavin_sdk/guard/injection.py | planned: `injection_check` re-raises SpendRefused and GateRefused (FI:33) | 134 lines changed above it; `injection_check` moved from M:85 to C:211, body not changed | different regions; the new import of model_gate and limits into injection.py makes no cycle (model_gate imports runmap, audit.protocol, llm.protocol, models only: C:43-46) |
| src/hadavin_sdk/runtime/agent_loop.py | 251-254, 788-797 pushed; install planned | not touched | core-b only |
| src/hadavin_sdk/runtime/evidence.py | not touched | 56-66, 96-97, 160-161 | core-c only |
| pyproject.toml | not touched | 6-10, 80-89 (banned-api for textnorm.fold, squeeze, identity_key) | core-c only. No new file of A or B imports textnorm, so the ban hits nothing of theirs |
| tests/test_k5_round9.py | planned: `_extract` (91-109) and the DRIVERS row (195) removed | line 239 only | different regions |
| src/hadavin_sdk/guard/producers.py | lines 61, 69 pushed; extract rows planned | not touched | core-b only; C:tests/test_k5_producers.py stays red on core-c alone until B is merged (ticket F AS BUILT, "Verified") |
| src/hadavin_sdk/guard/redact.py | not touched | HEAD, wip-g2-p1d-a and wip-g3-p2d all change it (wip-g3: about 40 hunks) | inside core-c only: the three core-c branches overlap around lines 880-960 |

## 4. Duplicated work
| subject | where | note |
|---|---|---|
| grants negative tests for the stop state | C:tests/test_grants_negative_roles.py (566 lines) against B:tests/test_stop_state_roles.py (991 lines) | NOT just a duplicate: core-c's file pins the OLD grant map and BREAKS on merge. `WRITES` holds `"kill_switch": {"INSERT", "UPDATE"}` (C:97) but B gives the runtime role SELECT only (B:src/hadavin_sdk/store/migrate.py, `"kill_switch": Grant("table", "SELECT", reset="SELECT, UPDATE")`); two `xfail(strict=True)` tests (C:539-545) turn red by design once step B is in; `test_pg_the_runtime_role_can_switch_the_stop_on` (C:510-515) does an UPDATE the runtime role no longer may do; the reset role, kill_switch_stops, kill_switch_clears and spend_reservations are in none of its lists (pin tests C:131, 154). core-c must rework it against B's map (its own docstring lists the cases, C:22-48) |
| gate tests | C:tests/test_model_gate.py (1468 lines) and A:tests/contracts/test_model_gate_contract.py (1377 lines; 201 passed, 1 skipped on 619a3e5, A:handover/core-a/raw/gate-contract-tests-on-core-c.log) | on purpose (builder against non-builder); keep both. The one skip is contract point 10: no worst-case formula exists on any branch yet |
| fake meters | C:tests/test_model_gate.py:58 `Meter`; A:test_model_gate_contract.py:120, 169, 184 (`_MeterDouble`, `StoreStyleMeter`, `MemoryStyleMeter`); core-b plans tests/contracts/test_meter.py (FI:23) | three doubles for one Protocol; after the install the real Limits and Budget can replace two of them |
| fake model clients | C:tests/test_model_gate.py:37 `Client`, :898 `Blocked`; A:tests/triggers/test_worker.py:42 `GateLLM`, crash_launcher.py:53 `CountingLLM`; M:src/hadavin_sdk/llm/fake.py | small, no action |
| T1 cap test (50 connections) | only A:tests/contracts/test_t1_reserve_cap.py; core-b pushed none | no duplicate; it skipped when written (store not built then) and has not been shown to run on B's 8db9c29 |
| store reservation tests | only A:tests/contracts/test_store_spend_reservations.py; B changed tests/test_p7_store.py by 67 lines | no duplicate found by name; B's F-store tests C1 to C5 were not found on B |
| crash hooks | only A:src/hadavin_sdk/testing/crash.py (+ tests/triggers/crash_launcher.py) | no second copy; core-b's crash cases can use it. It is a new module under src: guard tests that scan src (tests/test_k5_producers.py, test_no_hardcoded_values.py) were run by core-a on its own branch only |
| mutant scripts | C:tests/gate_mutants.py, textnorm_mutants.py; B:audit_drain_mutants.py, price_mutants.py, stop_state_mutants.py; A:endpoint_mutants.py; planned B:gate_install_mutants.py | different targets, same runner format; no overlap |

## 5. core-a's door (triggers/endpoint.py, server.py, worker.py)
- No model call: no `.chat(` in A:src/hadavin_sdk/triggers/. The document goes to the model only through `runtime.handle(agent_id, principal_id, document, trigger_kind=, trigger_ref=, run_id=)` (A:triggers/worker.py:185-192), the signature main already has (M:src/hadavin_sdk/runtime/agent_loop.py:352-361). So the gate covers it once core-b installs it in `handle`; the door needs no bind of its own.
- No use of redact, runmap or textnorm in the three files (imports: A:triggers/endpoint.py:17-26, server.py:17-23, worker.py:40-58). So neither the fold, nor G7, nor keyword-only `scan_holds` (C:src/hadavin_sdk/guard/textnorm.py:1446), nor `canonical` (C:runmap.py:283) touches the door. The only `canonical` callers outside guard/ are in runtime/evidence.py (M lines 57, 87, 88, 151), which only core-c edits.
- Logs: status, sender id, run id, counts and exception CLASS names only (A:endpoint.py:289, 299, 311; server.py:55, 76, 88, 114, 125; worker.py:151, 194, 204, 257, 339, 354). No document text, no key, no secret value, no exception text.
- Two places print exception TEXT to stderr: A:worker.py:424 `config error: {exc}` for the ConfigError written in that file (its texts hold sender id, agent id, principal id: A:worker.py:235-246, 263-265), and endpoint.py:186 puts `{sender!r}` in a ValueError. Ids from config, not document text; not routed through runmap. Low risk; core-a's call.
- `trigger_ref` = `sender/key#sha256(document)` (A:endpoint.py:113-115) is stored on the run. `key` is caller text but must match KEY_RE (A:endpoint.py:138). Whether trigger_ref later reaches a prompt or a card was not followed.

## 6. NOT CHECKED
- Nothing was run: no test, no merge, no trial tree. "Conflict" in section 3 is read from hunk positions, not from a real merge.
- The body of B:handover/core-b/tickets/F-store.md, B's A, B and C tickets and both F-store reviews; B:handover/core-b/DECISIONS.md and ESCALATIONS.md (so "request 2 is not answered" means: no answer file and no line in ORDERS, QUEUE, DECISIONS or STATUS-BOARD that names the mark beyond ORDERS.md:111-112).
- Row 2 (list copy against FakeLLM) and row 6 (principal on the audit row): the tests were not opened one by one.
- Whether `system` at B:agent_loop.py:463 can ever hold run data (the gate does not touch `system`); the cost of enforcing the document again on every step of the loop.
- core-a's test files beyond their headers; n8n files; A:tests/test_trigger_config.py against B's config.py.
- core-c's wip-g1-fold beyond its diffstat; the content of the wip branches' CHANGELOG and redact.py hunks (positions only).
- tools/ and .github of A and B (their diffstat for src and tests shows none; .github is changed by core-c only: ci.yml +6).
- The refs move every minute: A and B were read once, at the commits named at the top.
