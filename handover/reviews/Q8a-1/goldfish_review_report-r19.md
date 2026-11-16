Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8a-1 batch 18, branch `wip/cloud-q8a1-b18`, head `51f206bc` (previous reviewed head `b5b6c9fd`), round 19. SECURITY / redaction path: no round cap.
**Inputs:** `q8a1b18-design-r19.md` (0 Blocker, 3 Major D1-D3, 5 Minor D4-D8, 1 Nit D9), `q8a1b18-codebase-r19.md` (1 Blocker B1, 3 Major M1-M3, minors m1-m2), previous report `goldfish_review_report-r18.md`, independent evidence `handover/evidence/Q8a-1/51f206bc/RESULTS.md`, lead probe `lead-probe-b1.py` and `lead-probe-b1.out.txt`.
**Mode:** automated; no person available; the recommended option is taken for every item. No severity is changed. No finding is contested: each is checkable in the snapshot or by the lead probe, or is a stated owner item. Where reviewers rate one finding differently, both ratings are kept.

## Evidence summary (recorded by the independent runner, not judged)
- Every gate exited 0 at the head: full pytest 11574 passed, 1 skipped, 28 deselected; `stage_mutants` 422 of 422 good; `mutation_runner_mutants` 62 of 62; `migration_numbers_mutants` 36 of 36; ruff check and format, bandit, `scan_repo`, gitleaks, `test_changelog_claims` 6 passed. Z256, Z257, Z152, Z190, Z251 each killed alone by its own test.
- The builder's pytest counts (11118 passed, 457 skipped) do not match the runner's (11574 passed, 1 skipped); the runner had a live Postgres 16 and ran as user nobody; the cause of the difference was not looked into. Recorded, not explained.
- Fail-before: `tests/test_q8a1_b18_fixes.py` does not collect on `b5b6c9fd` (ImportError on `code_words`). With an evidence shim outside the repo: 24 failed, 5 passed. The new file has 29 tests, not the 30 the brief and builder say; the builder's "23 failed, 4 passed" was on an earlier 27-test version. The 8 other changed test files: 20 failed, 890 passed.
- Probes (203, runner): the value showed in 4 only, where the caller declares it loaded or it is a valid plain id. **Coverage gap of the runner:** it did not try non-dict input or invalid JSON through `model_validate` and `model_validate_json`; the lead probe did, and confirms B1.
- Not run (impossible now): Python 3.12, semgrep, zizmor, trivy, pip-audit, Vault server tests. The known timing test was not touched.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase B1`, design residuals 2(1),(3), removed mutants Z192-Z194, M16s, M18v] - Severity: Blocker
*   **Affected Scope:** `src/hadavin_sdk/hidden_input.py:152-159`; callers `tools.py:125`, `replay_records.py:66`, `audit/local_dir.py:179,218`, `audit/chain.py:243,286`; `tests/test_q8a1_b18_fixes.py:232-241`.
*   **Discrepancy Description:** Only dict input reaches the custom `__init__`. A string, a list or invalid JSON is validated by pydantic-core directly. The three overrides removed in batch 17 were the only guard for those shapes. The lead probe at `51f206bc` shows `ToolSpec.model_validate(<str>)`, `ToolSpec.model_validate([<str>])` and `ToolSpec.model_validate_json(<str>)` raise errors with the made-up canary absent from `str` and `repr` and PRESENT in `errors()` and `json()`. CHANGELOG batch 18 item 2 and batch 17 item 1 claim none of the refused text is in `errors()`, `json()`, `__cause__`, `__context__`. Z192-Z194 and M16s were declared equivalent only because every test sends a dict. Design residuals: a `ConfigValueError` kept in `ctx["error"]` keeps its own `__context__` (not walked); invalid JSON text from pydantic's own `json_invalid` is believed not to echo input but is not pinned.
*   **Rationale:** Same class as r17 and r18 Issue 2, closed for one entry shape. Confirmed by run (lead), not only by reading. The independent runner's probes missed this shape.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Fix at the one choke point for every entry shape (dict, non-dict, JSON text, strict and strings modes): restore the three class-method overrides or use a wrap `model_validator` plus `__get_pydantic_core_schema__`; do not rely on `__init__` alone. Add tests for string, list, None, number, invalid JSON, JSON of the wrong type through `_everything` plus `errors(include_input=True)`, `include_context=True`, `json()`, `__cause__`, `__context__`, and a walk of `errors()[i]["ctx"]["error"].__cause__`/`__context__`. Restore Z192-Z194 and M16s with killers for those shapes. Sibling check: every `HiddenInputModel` subclass, one canary per class, all shapes.
*   ***Proposed Edit:***
    *   Location: `src/hadavin_sdk/hidden_input.py`, `tests/test_q8a1_b18_fixes.py`, `tests/stage_mutants.py`, CHANGELOG items 2 (batch 17 and 18).
    *   Change: as above; narrow any claim to what is closed.

### [Issue 2] [`codebase M1`] - Severity: Major
*   **Affected Scope:** `hidden_input.py:23-25` (docstring), CHANGELOG batch 18 item 2, `k1b/diagnosis.py:95`.
*   **Discrepancy Description:** The docstring says tests pin custom-init routing (`__pydantic_custom_init__`) and fail when a src or demos call uses `strict=`, `context=` or `from_attributes=`. Grep finds neither test. `Diagnosis.model_validate(value, strict=True)` at `diagnosis.py:95` uses `strict=`; CHANGELOG "no call in src uses them" is false.
*   **Rationale:** A claim about a guard that does not exist.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Add the AST test the docstring promises (scan `src` and `demos` for those keyword arguments on `model_validate*`), with a planted-source control and a mutant; remove the `strict=` call or allow it by name with a written reason (model config already strict); add a custom-init routing test (or, after Issue 1, the test of the replacement guard).
*   ***Proposed Edit:***
    *   Location: `hidden_input.py` docstring, new test, `diagnosis.py:95`, CHANGELOG.
    *   Change: test exists and fails for the named reason; claim matches code.

### [Issue 3] [`design D2`, `codebase M3`] - Severity: Major (both)
*   **Affected Scope:** `tests/_text_guard.py:1072-1090` (`_unknown_receiver`), `R18d`, `Z252`, `Z253`.
*   **Discrepancy Description:** The receiver check for `.count()`, `.index()`, `.find()` treats only a bare `ast.Name` as unknown. `self.client.count(name)`, `get_client().count(name)`, `d["x"].count(name)` stay "proven numbers" and are dropped from a `%d` log call (r18 Issue 6b shape for one receiver form). The plant and the two mutants pin only `client.count(name)`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Any receiver that is not a literal or proven code-owned is unknown; plants for attribute, call and subscript receivers; mutants killed for that reason.
*   ***Proposed Edit:***
    *   Location: `tests/_text_guard.py`, `tests/test_stage_names.py`, `tests/stage_mutants.py`.
    *   Change: as above.

### [Issue 4] [`codebase M2`] - Severity: Major
*   **Affected Scope:** `tests/_text_guard.py:1402-1404, 1607-1623`, pr-notes line 32, `test_stage_names.py:4038-4039`.
*   **Discrepancy Description:** Z163 (strips number-directive arguments in log calls) was removed as "equivalent"; it is an untested branch. No plant passes `log.warning("%d", len(x))` or `x.find(y)` (`number_valued` true, `safe` false). Z190 and Z251 kill only inner parts. CHANGELOG item 5 advertises the rule.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Add a clean-table plant `log.warning("n %d", name.find(","))` and its found-table twin; restore the mutant with its killer. Re-derive Z159 equivalence by a plant or restore it (design: not re-derived).
*   ***Proposed Edit:***
    *   Location: `tests/test_stage_names.py`, `tests/stage_mutants.py`.
    *   Change: as above.

### [Issue 5] [`design D1`] - Severity: Major
*   **Affected Scope:** CHANGELOG batch 18 (5); `tests/_text_guard.py:108-130` (`store_write_methods()`); `test_q8a1_b18_fixes.py:508`.
*   **Discrepancy Description:** The CHANGELOG says a test fails when a protocol method is neither a read nor covered. No such test exists. `store_write_methods()` treats every method not starting `get_`, `list_`, `spend_totals` as covered, so the "uncovered" set is empty by construction. A new write named `get_or_create_run` or `list_and_claim` is classed a read and its stored argument is not scanned (r18 Issue 6a sink).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** List the read methods explicitly; a protocol method in neither list fails a test; plant a write named `get_or_create_x` and a mutant. Or drop the sentence if the test is not built.
*   ***Proposed Edit:***
    *   Location: `tests/_text_guard.py`, `tests/test_q8a1_b18_fixes.py`, CHANGELOG.
    *   Change: as above.

### [Issue 6] [`design D3`, `codebase m1 (config names into store calls)`] - Severity: Major (design) / Minor (codebase)
*   **Affected Scope:** `tests/_text_guard.py:1436-1450` (taint), R18c, CHANGELOG "cannot see" list.
*   **Discrepancy Description:** Taint covers error text only. A configured name flowing into a stored record (`AuditEvent(operation=name)`, `rec["agent"] = cfg_name`, `store.insert_event(detail=agent_cfg_name)`) is unseen; R18c passes only through the general scan. r17 F1(e) and r18 Issue 6a(i) are neither fixed nor named in the CHANGELOG, though the rule says configured names must not reach a stored record.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Taint configured names into store-call arguments, keywords and record subscripts, with plants and a mutant; or, if a shape cannot be seen, name it in the CHANGELOG "cannot see" list with the next step and date (no silent gap).
*   ***Proposed Edit:***
    *   Location: `tests/_text_guard.py`, `tests/test_stage_names.py`, CHANGELOG.
    *   Change: as above.

### [Issue 7] [`design D5`, `codebase m2 (Issue 7 not shown)`] - Severity: Minor
*   **Affected Scope:** `errors.py:57-72, 200-201`, `config.py:662, 674`, `k1b/bundle.py:109`, `registry.py:266-277`, `models.py:65`.
*   **Discrepancy Description:** `<not shown>` is the safe direction. Costs: an operator with 10 systems cannot find the bad one; `bundle.py:109` always prints `bundle <not shown>` though the folder name was typed on the command line; registry parse errors fire before `loaded_ids(...)`; `_no_floats` always `<not shown>`. `error_where(cleaned=True)` shows ANY word-like name and is safe only if the error came through `without_input`; nothing enforces it. The "7 microseconds vs 0.7" claim has no evidence.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Give `bundle.py` a loaded list of the listed folder names; test that `error_where(cleaned=True)` is reached only from `HiddenInputModel` errors (or mark the rebuilt error); measure or drop the microsecond claim. The position hint ("entry 2") stays the owner question E1 (Issue 10).
*   ***Proposed Edit:***
    *   Location: `k1b/bundle.py`, `errors.py`, a test, CHANGELOG.
    *   Change: as above.

### [Issue 8] [`design D4`, `codebase R17t/R17u`] - Severity: Minor
*   **Affected Scope:** `tests/test_stage_names.py:3953-3960, 4047-4048`; `tests/_text_guard.py:168` (`_own` does not descend into lambdas), no `ast.Match` handling.
*   **Discrepancy Description:** R17t and R17u pass only because `name` and `text` are unproven parameters; titles "case pattern" and "lambda" test nothing about match or lambda logic. The real blind spot (match binding shadowing a proven outer name) is disclosed in CHANGELOG item 5 but not planted.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Plant the proven-outer-name versions (`name = 'fixed'; match x: case str(name): raise A(name)` and the lambda form) with a mutant, or rename the rows as controls and list `match` shadowing under "cannot see".
*   ***Proposed Edit:***
    *   Location: `tests/test_stage_names.py`, `tests/stage_mutants.py`, CHANGELOG.
    *   Change: as above.

### [Issue 9] [`design D6, D7, D8, D9`, `codebase m1 (remaining)`] - Severity: Minor (D9 Nit)
*   **Affected Scope:** `tests/test_guard_reasons.py` (`check_literal` ~175-195, `check_rowid` ~361-380, `FIELDS` row for `_place`, CARD docstring 2471-2473); `test_q8a1_b18_fixes.py:413-420, 562`; `test_changelog_claims.py:58`; `_mutant_check.py`; `stage_mutants.py:1209`.
*   **Discrepancy Description:** (a) `check_literal` reads the Literal annotation, not the showing site; `check_rowid` greps two strings and does not check the number comes from `seq`; the `FIELDS` row for `_place` rests on `check_fields`, so removing `and part in words` leaves the row passing (only Z235 pins it). (b) "All 77 model classes" is unpinned (`len(classes) > 40`). (c) ROOT_FILES scan sees only `X / "name"` in `tests/test_*.py`; `Path("x")`, `.joinpath`, `open("pyproject.toml")`, helpers `tests/_*.py`, root folders (`.github`, `migrations`) are invisible; the `ast` limit is in a docstring only. (d) `_tainted` Dict branch (`_text_guard.py:1566-1569`) has no mutant. (e) CARD docstring says "fills EVERY other field"; only 7 are canaried. (f) one-line `except X: pass  # noqa: BLE001` not counted (`test_changelog_claims.py:58`); per-site handler text in CHANGELOG lines 35-36 not checked. (g) Nit: the mutant-list check covers only `stage_mutants.py`, not the other two lists; `expect` and `pinned` ids unchecked; Z257 expect is the bare word "assert", Z254 expect is a pytest artefact string.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Per item: check the showing site and the `seq` source; pin 77 or drop it; widen the scan (all test and helper files, `Path(`, `joinpath`, `open(`, root folders) or state the limit in the CHANGELOG; add the Dict mutant; correct the docstring; count one-line handlers; check handler text or drop the claim; extend the mutant-list check to all three lists with `expect` and `pinned`; strengthen Z257 and Z254 expects.
*   ***Proposed Edit:***
    *   Location: files named above.
    *   Change: as above.

### [Issue 10] [`design owner items`, `codebase Issue 10`] - Severity: Major (owner question)
*   **Affected Scope:** `q-q8a1-hide-ids` E1 (position hint instead of `<not shown>`), E2, and the `error_reason(exc)` question (`_run_tool`, `invoke`).
*   **Discrepancy Description:** Owner decisions, not judged by either reviewer.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** The evidence is the owner's decision, outside every file the reviewers could read. Stay OWNER-ONLY and unbuilt; do not report closed.
*   ***Proposed Edit:***
    *   Location: `handover/questions-for-lead.md`.
    *   Change: none by the builder.

### [Issue 11] [`evidence`, `design Fail-before`, `codebase Fail-before`] - Severity: Major
*   **Affected Scope:** `handover/evidence/Q8a-1/b18/`, `tests/test_q8a1_b18_fixes.py`, CHANGELOG counts.
*   **Discrepancy Description:** The final test file cannot be imported on `b5b6c9fd`; the builder's fail-before was on an earlier 27-test file. The runner measured 24 failed, 5 passed with a shim (29 tests, not 30); the 5 passes on old code have no written reason in the builder table beyond the early four. The independent runner did not cover non-dict shapes. The builder's pytest counts differ from the runner's and the cause is unexplained.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Batch 19 measures fail-before on `51f206bc` for every new test with the import shimmed outside the repo, writes a reason per test that passes on old code, recomputes the CHANGELOG counts, and states the pytest environment (Postgres, user, skips). A full independent evidence run on the batch-19 head is a gate; its probe list must include non-dict, list, None and invalid-JSON entry shapes for every `HiddenInputModel` subclass.
*   ***Proposed Edit:***
    *   Location: `handover/evidence/Q8a-1/b19/`, CHANGELOG.
    *   Change: as above.

## Handoff
- PROPOSE FIX: 10 groups (Issues 1-9 and 11), 0 contested, 0 declined as Nit-only (the Nit D9 is folded into Issue 9 as a fix).
- ESCALATE: 1 (Issue 10, owner items E1, E2, `error_reason`).
- Contested: 0. Declined: 0.
- Remaining unaddressed: all fixes are unbuilt until batch 19. Blockers: 1 (Issue 1, confirmed by lead run). Majors: 5 (Issues 2-6 by reviewer severity; Issue 11 evidence).
- Gate: the independent full evidence run on the batch-19 head, with the non-dict shapes in the probes. No claim of "done" before it.

## Who fixes it
One batch-19 builder on `core/q8a1-b19` from `51f206bc`, pushing to `wip/cloud-q8a1-b19`. Order: Issue 1 first (the Blocker), then Issues 2, 3, 4, 5, 6 and 11, then 7, 8, 9. Method per bug: name the class, cite the standard, fix at the shared choke point (all pydantic models that hold hidden input, all entry shapes), grep siblings, new tests shown failing on `51f206bc` with measured counts, one mutant per fix killed for the named reason, full suite and all mutant sets (`stage_mutants`, `mutation_runner_mutants`, `migration_numbers_mutants`) on the final head, a written reason for every test that passes on old code, CHANGELOG counts recomputed. Never touch the known timing test. Then: snapshot, independent evidence runner, two `egm:*` reviewers, `egm:egm-resolve`. Security path: no round cap.
