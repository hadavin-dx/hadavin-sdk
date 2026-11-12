Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8a-1 batch 16, branch `wip/cloud-q8a1-b16`, head `20581c80` (round 17, SECURITY / redaction path: configured names and library error text must not reach a message, log, tick or stored record; no round cap).
**Inputs:** `handover/reviews/Q8a-1/q8a1b16-design-r17.md` (0 Blocker, 3 Major, 4 Minor, 2 Nit), `handover/reviews/Q8a-1/q8a1b16-codebase-r17.md` (0 Blocker, 4 Major, 1 Minor, 2 Nit), previous report `goldfish_review_report-r15.md`, independent evidence `handover/evidence/Q8a-1/20581c80/RESULTS.md`.
**Mode:** automated; no person available; the recommended option is taken for every item. No severity is changed. No finding is contested: each is checkable against the snapshot and is valid, or is a stated owner item.

## Evidence summary (what the runner recorded, not judged)
- Full pytest: 11480 passed, 1 skipped, 28 deselected, exit 0 (own Postgres 16.15).
- `stage_mutants.py`: **362 of 363 good, exit 1.** The bad row is Z150, WRONG_REASON: caught by `test_the_guard_finds_each_planted_fault_alone[R15c ...]` (assertion shows an empty list), not by its pinned R16a. This confirms both reviewers (design F7, codebase F4).
- `mutation_runner_mutants.py` 62 of 62, `migration_numbers_mutants.py` 36 of 36. ruff, ruff format, bandit -ll, `scan_repo`, gitleaks: exit 0.
- Fail-before on `c098aacf`: 27 failed, 591 passed. 20 of the 27 are in `test_q8a1_b16_fixes.py`; 5 tests of that file pass on old code (each needs a written reason).
- Hostile probes (39 rows): the `AuditEvent.event_id` refusal keeps the rejected value out of `str`, `repr` and `args` but **`exc.errors()` and `exc.json()` still carry it** (11 rows; `errors(include_input=False)` has none). `shown_id` returns the real id text for a `str` subclass with its own `__str__`. A planted YAML-library error did not cause a refusal in check-config (accepted, exit 0, marker not printed). Nothing else leaked.
- Not run (impossible now): Python 3.12, semgrep, zizmor, trivy, pip-audit. Timing test not touched.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design F1`, `design F2`, `design F3`, `codebase F1`, `codebase F2`] - Severity: Major
*   **Affected Scope:** `tests/_text_guard.py` (`_attr_read_ok` 491-504, `safe()` Attribute branch ~1066-1071, `sites()` ~1194-1362, `_tainted` ~1393-1413, `_without_number_directives` 1431-1443, keyword/attribute/dict sinks 1301-1328); `tests/test_stage_names.py` R16k, R16o; `tests/stage_mutants.py` Z163; CHANGELOG batch 16 items 4 and 7.
*   **Discrepancy Description:** Guard blind spots, one class (a path the guard cannot see, so it reports a leak-free tree by silence): (a) an attribute read is trusted for any receiver that is not library-rooted if the attribute is only written with safe values somewhere (a library exception's `.reason`); (b) taint is not followed through Tuple, List, Set, Dict wrappers or positional arguments of `update*`, `insert*`, `write*`, `execute*`, `append*`, `put*` calls; (c) message sinks without a branch: `assert ok, name`, `writelines`, `exit`/`quit`, `getLogger`, `Thread(name=)`, aliases of `stderr`/`stdout`, `match` and lambda bindings shadowing a proven name; (d) every argument at a `%d` directive of a log call is dropped without proof it is a number (a logging format failure goes to `Handler.handleError`, printing `Message:` and `Arguments:`); (e) a configured name placed directly in a stored record (`Row(detail=cfg_name)`, `rec["agent"] = cfg_name`, `AuditEvent(operation=name)`) passes because those sinks fire only on error-derived text.
*   **Rationale:** same class as r15 Issue 2, closed one more step. FOUND is 0 on today's `src/`, so these concern the next edit, not a live leak. Evidence adds no contradiction.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each shape follows from a straight reading of the cited lines; the builder must run each as a planted fault, so any shape already flagged shows up at once. Security path, no cap.
*   ***Proposed Edit:***
    *   Location: `tests/_text_guard.py`, `tests/test_stage_names.py`, `tests/stage_mutants.py`, CHANGELOG limits.
    *   Change: (a) trust an attribute only for `self` of the writing class or a name bound to a constructor call of that class, else tainted or allowed by row; (b) recurse into Tuple, List, Set, Dict and treat positional arguments of the named call families as sinks; (c) add the missing sinks, resolve `stderr`/`stdout` aliases, handle `match` and lambda bindings; (d) drop a `%d` argument only when `number_valued` proves it, else keep it as a site; (e) make keyword, dict and attribute sinks of stored model classes use `safe`, or name the limit in the CHANGELOG with the exact shapes (list derived from the planted-fault table). One planted fault, one clean form and one mutant per shape, each mutant pinned to its own test; show each new test failing on `20581c80`.

### [Issue 2] [`codebase F3`, `design F8`, `codebase F5`, `design F6`] - Severity: Major
*   **Affected Scope:** CHANGELOG batch 16 items 1, 5 and the CARD sentences; `src/hadavin_sdk/registry.py:310-312, 411-430`; `tests/_text_guard.py:88` (`NUMBER_ANNOTATIONS`); `tests/test_changelog_claims.py:71-86`; `tests/test_guard_reasons.py` `check_card` ~2339-2480; `tests/_guard_allowances.py:10`.
*   **Discrepancy Description:** Sentences the code does not keep: (a) item 1 says check-config does not check that a tool module matches its pinned hash; `registry._load_tools` runs `_module_pin_problems` first and unconditionally, so the hash match is checked and only loading and operation binding are skipped; (b) item 5 says a `Decimal` field is proven a number by its declaration; `NUMBER_ANNOTATIONS` is {int, float, bool, Literal}, and the `Decimal` declarations in `k1b/loop.py:45` and `replay.py:147` still need NUMFIELD rows; (c) the "per-site list of 54 handlers is in the batch 16 notes" but those notes are not in the code branch; (d) the claims test checks one "Counts at this head" sentence only, older numbers ("50 of 52", "547 rows", "445 rows") and the batch-15 text are stale, handlers are counted by `noqa: BLE001` lines and mutants by `len()` of a dict literal (undercounts duplicate keys); (e) the CARD canary covers 7 of 15 fields (shadow, abstain, one summary, one send or update); "every other field" and "53 of 54 checked by code" overstate it; free text shown on purpose has no canary.
*   **Rationale:** the owner rule on honest claims: a number or sentence in a CHANGELOG must be what a test or command shows. The CARD deferral itself is honest (ticket `Q8a1-card-demo-fixture`, due 2026-11-19).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each is checkable against the cited lines; none is a code defect, so the fix is the sentence or the test that derives the number.
*   ***Proposed Edit:***
    *   Location: CHANGELOG batch 16; `tests/test_changelog_claims.py`; `tests/test_guard_reasons.py` CARD reason.
    *   Change: correct (a), (b), (c) (put the handler list under `handover/` or in the CHANGELOG and name where); derive every count in the batch 15 and 16 text from the code in the claims test (count handlers with `ast`, mutants with `ast` keys, reject duplicate keys, cover the older numbers); in the CARD reason and CHANGELOG say "the listed canaried fields" and count CARD as half checked, or canary every `ApprovalRequest` field and drive the "Would be refused", "too large" and free-text paths. Prove the claims test fails on a deliberately wrong sentence.

### [Issue 3] [`design F7`, `codebase F4`, `evidence stage_mutants`] - Severity: Major
*   **Affected Scope:** `tests/stage_mutants.py` Z150 (1016-1017), Z152, Z153, Z154, Z158, Z162, Z176-Z179, R16j, R16o; `tests/test_stage_names.py` R16a, R16c, R16d, R16e, R16i, R16n (3723-3828); b16 notes table rows R16a, R16e, R16i, R16j.
*   **Discrepancy Description:** Mutant and planted-fault attribution is weaker than claimed, and the independent run confirms it: **Z150 is BAD WRONG_REASON** (it edits the same expression as the older Z102, pinned to R15c, which fails first; it adds nothing beyond Z102). Z152, Z153, Z162 die only because a site count drops from 2 to 1 (a sibling rule finds the same fault), so "isolates one rule" is false for them. Z154 is double-pinned to R16a, Z176-Z179 are pinned only by module-name fragments, R16j has only Z100 and is unpinned, R16o's planted form has no mutant, no mutant touches `taint_of` propagation, many clean-form rows rest on "Z1 and others", and the notes table says R16i is killed by Z158 and R16e by Z154, which the code does not support.
*   **Rationale:** a mutant that dies for the wrong reason proves nothing about the rule it names; the runner already exits 1 on it, so this blocks the gate.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The runner output and both reviewers agree; Z150 is the only red row in the gate.
*   ***Proposed Edit:***
    *   Location: `tests/stage_mutants.py`, `tests/test_stage_names.py`, notes table.
    *   Change: move Z150's edit to a distinct line or drop it (name the choice); give each planted fault a count or marker that only its own rule can produce, so no sibling rule satisfies it; pin Z176-Z179 to the full site text; add a mutant that breaks `taint_of` propagation and mutants for R16j and R16o; correct the notes table rows; run the full 363+ set until `problems: []`.

### [Issue 4] [`design F4`, `design F5`, `codebase F5 (allowance part)`] - Severity: Minor
*   **Affected Scope:** `tests/_guard_allowances.py:845-890` (31 new rows); `tests/test_guard_reasons.py` `check_proc` ~1642-1665, `check_handoff` ~2205-2260, UNCHECKED test ~2540-2547; `src/hadavin_sdk/tools.py:411-417, 1027-1052, 1140-1174`; `k1b/loop.py:84-112`.
*   **Discrepancy Description:** The new rows are standing allowances for every occurrence of the same text in a module (keyed by module plus unparsed text): `return message[:200]`, `str(exc)` (REDACTED), `str(path)`, `str(raw)`, `str(key)`. A new site with the same short text is silently allowed; `check_proc` follows only names the function stores and cannot fail for a parameter-borne value; `str(path)` is passed to `compile()` as a filename. The HANDOFF reason is circular: re-raising keeps the text and safety rests on `error_reason` returning `message[:200]` or `f"{type(exc).__name__}: {message[:160]}"`, neither redacted (the REDACTED question is owner-only).
*   **Rationale:** weak allowances erode the guard one row at a time.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Checkable by reading; the redaction question itself is owner item E1 (Issue 7), so only the guard-side keying is fixed.
*   ***Proposed Edit:***
    *   Location: `_guard_allowances.py`, `test_guard_reasons.py`.
    *   Change: key rows by enclosing function plus occurrence count; pin the number of REDACTED rows in the UNCHECKED test; state in the HANDOFF reason that safety rests on `error_reason` and link `q-q8a1-hide-ids`; make `check_proc` fail for a parameter-borne value or say it does not.

### [Issue 5] [`evidence probes`, `evidence fail-before`] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/audit/models.py:197-248` (`AuditEvent.event_id`, `hide_input_in_errors`); `src/hadavin_sdk/errors.py:131-142` (`shown_id`), `:70` (`shown_name`); `src/hadavin_sdk/cli.py:307-321` (`_check_config`); `tests/test_q8a1_b16_fixes.py`.
*   **Discrepancy Description:** Independent probes found (a) `exc.errors()` and `exc.json()` of a refused `AuditEvent` still carry the rejected `event_id` (pydantic's default `input` field), in 11 rows; the fix hid it from `str`, `repr` and `args` only, and the standing invariant covers a message, log, tick or stored record, which a caller that logs `exc.errors()` produces; (b) `shown_id` returns the real id text for a `str` subclass that overrides `__str__`, so the closed shape check is not closed; (c) a planted library error text in the YAML reader did not cause a refusal (the probe did not reach it as a failure), so the claim that check-config shows no library text is shown only for the OSError case; (d) 5 tests of `test_q8a1_b16_fixes.py` pass on old code with no written reason.
*   **Rationale:** (a) is a live channel of the exact class the batch closes, found only by the independent run; (d) is the standing rule that a test passing on old code needs its reason.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Evidence lines in `RESULTS.md` and `probes.log.txt`, `probe2.log.txt`; no reviewer read these, so no contest is possible.
*   ***Proposed Edit:***
    *   Location: `audit/models.py`, `errors.py`, `cli.py`, `tests/test_q8a1_b16_fixes.py`, CHANGELOG.
    *   Change: (a) drop the input from every error channel at the choke point (validator raises a fresh error with no input, or a model-level handler that strips `input` from `errors()` and `json()`), grep every other model with `hide_input_in_errors` or a custom validator for siblings, add a test over `str`, `repr`, `args`, `errors()` and `json()`; (b) return `str.__str__(value)` after the closed check and the exact type check (`type(x) is str`); also make `shown_name` use the same primitive and add `shown_name` to `_filter_behaviour`; (c) add a probe that makes the YAML reader raise a planted text at the call check-config does reach, assert exit 2 and no text; (d) write one reason per passing-on-old-code test (already-correct behaviour, control, or guard copy) or add the failing form. Show each new test failing on `20581c80`; one mutant per fix.

### [Issue 6] [`codebase F6`, `codebase F7`, `design F9`] - Severity: Nit
*   **Affected Scope:** `src/hadavin_sdk/audit/local_dir.py:82-85, 126-190`; `src/hadavin_sdk/models.py:198-206`; `src/hadavin_sdk/errors.py:70`; `tests/test_guard_reasons.py:2263-2301`; `tests/_text_guard.py:867-873`; b16 62-row table.
*   **Discrepancy Description:** A poison event built with `model_construct` stays in `_pending` and is retried each tick, swallowed by design, never logged or removed; `write_intent` raises a bare `ValueError`, not `AuditUnavailable`; read paths still join `self.objects / <key>` without the recheck (same as main); an outbox file under an old id outside the new pattern now moves to `outbox/corrupt/` and the CHANGELOG does not say so; `_RESERVED_NAMES` omits `com0` and `lpt0`; `_scope_env` trusts an `int`-annotated parameter of a function with no caller in the tree and the CHANGELOG list does not name it; about 12 clean-form rows in the 62-row table say "killed by Z1 and others"; the 27 failed / 591 passed fail-before is now independently confirmed.
*   **Rationale:** small gaps in disclosure or coverage.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Cheap, in the same files being edited, and the owner rule is to fix, not defer; local_dir poison event gets one test.
*   ***Proposed Edit:***
    *   Location: files above.
    *   Change: add `com0`, `lpt0`; raise `AuditUnavailable` from `write_intent` or document and test the `ValueError`; add the recheck to read paths or state it; add the corrupt-move sentence to the CHANGELOG; name the `_scope_env` rule; give each clean-form row its own pinned mutant or a named "control" label.

### [Issue 7] [`design/codebase owner items`] - Severity: Major
*   **Affected Scope:** E1 `q-q8a1-hide-ids` (the two REDACTED allowance rows at `tools.py:1036` and `:1051`, `error_reason` returning an unredacted slice), E2 `ConfigName`.
*   **Discrepancy Description:** Disclosed and not built; both reviewers mark them as agreed owner questions.
*   **Rationale:** need the owner's decision.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** The deciding fact (the owner's answer on hiding ids and on the `ConfigName` type) is outside every file a reviewer can read. Not fixed here. Ledger status OWNER-ONLY; do not report batch 16 or 17 as closing them.
*   ***Proposed Edit:***
    *   Location: none.
    *   Change: none. The batch-17 builder keeps the REDACTED rows pinned in number (Issue 4) and links the owner question in the reason text.

## Handoff
- Accepted fixes (PROPOSE FIX): 6 groups (Issues 1 to 6; Issue 6 holds Nits fixed because the files are open anyway).
- Contested: 0. Escalated: 1 (Issue 7, owner items E1 and E2). Declined: 0.
- Remaining unaddressed: 0 of the reviewers' findings (every one is in a group above). Severity counts kept as reported: design 0 Blocker 3 Major 4 Minor 2 Nit; codebase 0 Blocker 4 Major 1 Minor 2 Nit. The evidence adds one Major group (Issue 5) and confirms the Z150 red row.
- Gate state at `20581c80`: red until Z150 is fixed (362 of 363); everything else green. Not mergeable on this head.

## Who fixes it
One batch-17 builder (Sonnet 5.5) on a new branch `core/q8a1-b17` from `20581c80`, pushing to `wip/cloud-q8a1-b17`. Order: Issue 3 (the red gate row), Issue 5, Issue 1, Issue 2, Issue 4, Issue 6. Method per bug: name the class, fix at the shared choke point, grep for siblings, show each new test failing on `20581c80`, one mutant per fix with a killer that fails for the named reason (run the whole mutant set to `problems: []`), final-head full suite once, a written reason for every test that passes on old code, CHANGELOG corrections. Security path: no round cap; another independent evidence run and two reviewers follow the batch-17 push. Owner items E1 and E2 stay OWNER-ONLY.
