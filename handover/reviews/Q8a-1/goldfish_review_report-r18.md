Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8a-1 batch 17, branch `wip/cloud-q8a1-b17`, head `b5b6c9fd` (previous reviewed head `20581c80`), round 18. SECURITY / redaction path: no round cap.
**Inputs:** `handover/reviews/Q8a-1/q8a1b17-design-r18.md` (0 Blocker, 4 Major, 6 Minor, 2 Nit), `handover/reviews/Q8a-1/q8a1b17-codebase-r18.md` (1 Blocker, 3 Major, 4 Minor, 1 Nit), previous report `goldfish_review_report-r17.md`, independent evidence `handover/evidence/Q8a-1/b5b6c9fd/RESULTS.md`.
**Mode:** automated; no person available; the recommended option is taken for every item. No severity is changed. No finding is contested: each is checkable against the snapshot and is valid, or is a stated owner item. Where two reviewers rate one finding differently, both ratings are kept (Group 2).

## Evidence summary (what the runner recorded, not judged)
- `python tests/stage_mutants.py` (the exact CI command) cannot start: exit 1, "the unmutated copy does not pass its tests". `tests/test_changelog_claims.py` reads `CHANGELOG.md` at import, and the mutation runner's temporary copy does not hold it. With `CHANGELOG.md` added by a wrapper the 10 files pass. `tests/migration_numbers_mutants.py` also fails its baseline (its copy holds the known timing test, which fails there). So two CI gates cannot run on this head.
- Full pytest (valid run 2): 3 failed, 11536 passed. One real: `tests/test_lockin_guard.py::test_vendor_sdks_stay_inside_their_kind_modules` says `hadavin_sdk.hidden_input` imports `pydantic_core` outside its allowed modules. The two `demo_askdata` failures are the runner's environment (a fixed file owned by another user, the default socket).
- Supplementary `stage_mutants` through a wrapper: 388 of 405 good, 17 not good. Survived: M18v, Z65, Z152, Z159, Z192, Z193, Z194, Z209, Z223. SNIPPET NOT FOUND: Z21, Z128, Z163, Z190. Wrong reason: Z90, Z154, Z184. Crash: Z221.
- Probes: an unknown key whose NAME is the canary shows the name in `str`, `repr`, traceback, `errors()` and `json()` through `loc`; `shown_name` returns a word-like name that is not a loaded id when no loaded set is given; an `event_id` that is a `str` subclass with its own `__str__` is stored as the plain text.
- Fail-before on `20581c80`: 18 failed, 769 passed with the head CHANGELOG (the builder said 20 and 767); 43 of 61 new tests pass on old code (a written reason each is missing); 4 older ids also fail.
- Clean: ruff, ruff format, bandit, scan_repo, gitleaks, `mutation_runner_mutants` 62 of 62, changelog claims 6 passed. The known timing test fails 3 of 3 on head and on main: not touched.
- Not run (impossible now): Python 3.12, semgrep, zizmor, trivy, pip-audit. The builder's own full pytest and `stage_mutants` never ran on this head.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`evidence stage_mutants`, `evidence migration_numbers_mutants`] - Severity: Blocker
*   **Affected Scope:** `tools/mutation_runner.py` (copy list), `tests/test_changelog_claims.py`, `tests/stage_mutants.py`, `tests/migration_numbers_mutants.py`, `.github/workflows/ci.yml`.
*   **Discrepancy Description:** A gate that cannot run. The exact CI command for the stage mutants exits 1 before any mutant, because a test reads a file the runner's copy does not carry. The migration-number runner also fails its baseline in the copy. Class: a mutation runner whose copy differs from the tree it tests, so a new test input silently breaks the gate (and nothing says so until CI).
*   **Rationale:** Evidence finding by the lead as Blocker: no mutant result can be trusted as a gate while the runner cannot start. This is the second time a gate went unrunnable (batch 14 mutation copy).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Fix at the shared choke point, not per test: the runner copies the root files every test may read (a list in one place, checked by a test that fails when a test reads a repo-root file that the list lacks), or `test_changelog_claims.py` locates its file through the one helper the runner already honours. Run the exact CI command to completion on the final head, and `migration_numbers_mutants` too (the timing test is not to be touched: if the baseline fails only because of it, say so with raw output and fix the baseline choice in the runner, not the test).
*   ***Proposed Edit:***
    *   Location: `tools/mutation_runner.py`, `tests/test_changelog_claims.py`.
    *   Change: one source of truth for files copied; a guard test; a mutant that removes `CHANGELOG.md` from the list and a killer that fails for that reason.

### [Issue 2] [`codebase B1`, `design M2`] - Severity: Blocker (codebase) / Major (design)
*   **Affected Scope:** `src/hadavin_sdk/hidden_input.py` (`without_input` 23-41, `__init__` 49), `src/hadavin_sdk/config.py:124`, `:588`, `:730`, `registry.py:274`, `tools.py:130`; `tests/test_q8a1_b17_fixes.py:23-99`, `:127-146`; CHANGELOG batch 17 item 1.
*   **Discrepancy Description:** `HiddenInputModel` hides only `input`. The claim "a refused value is in no channel of the error" is false. (a) `loc` keeps a pasted unknown key (`extra_forbidden`) and dict-field mapping keys; the probe confirms the name shows in `str`, `repr`, `errors()`, `json()`. (b) `ctx` keeps the typed `tag` for `union_tag_invalid` (reachable at `ExecutorSpec` and the backend `kind`). (c) `ctx["error"]` keeps the original validator exception, and `msg` is "Value error, <text>" when a validator calls `int()`, `Decimal()`, `bytes.fromhex()`. Coverage: tests use one fixed-sentence validator and one type error; no `loc`, no `ctx`, no sibling models (`ToolSpec`, `AgentRecord`, `Chain`, `ActionContract`, executors, `ReplayRecord`, `TickState`, `ToolCall`, `ToolCallRecord`, `Target`, `ChainStep`, design m3). Also: `__init__` puts every `Shape` model on a custom-init path (design m5), and a stored event row with an id outside the pattern fails with `<hidden>` so an operator cannot tell which row (design m6).
*   **Rationale:** Same class as r17 Issue 5, closed for one channel only. The loaders re-raise `from None`, but the ValidationError stays in `__context__`, so a traceback or a logger prints it.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Fix at the one choke point (`without_input`): replace every `loc` element that is a `str` and not a code-owned field name (from `cls.model_fields` or the `error_where` rule, a pattern-shown id passes `shown_name`) by a fixed word; drop or rebuild `ctx` for `union_tag_invalid`, `union_tag_not_found`, `value_error`, `assertion_error` (keep an original exception only when it is a `ConfigValueError`, else a fixed `PydanticCustomError`); the walk includes `msg`. Tests: one per shape over `str`, `repr`, `errors()`, `json()`, `__cause__`, `__context__`, for `extra_forbidden`, dict key, tag, plain `ValueError` validator, int/Decimal/hex validators; sibling models by a test that lists every `Shape` subclass; a mutant per branch with a killer that fails for that reason. Add the row-id operator hint (the row position, not the id) and measure `__init__` cost once (a number in the CHANGELOG, or remove the custom `__init__` if Group 4 shows it is not needed).
*   ***Proposed Edit:***
    *   Location: `src/hadavin_sdk/hidden_input.py`, `tests/test_q8a1_b17_fixes.py`, `tests/stage_mutants.py`, CHANGELOG.
    *   Change: as above; if any channel is deliberately left open, narrow the claim to what is closed.

### [Issue 3] [`evidence lockin`, `design m4 (evidence)`] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/hidden_input.py` (imports `pydantic_core`), `tests/test_lockin_guard.py`.
*   **Discrepancy Description:** The repo lock-in guard fails: `hadavin_sdk.hidden_input` imports `pydantic_core` outside its allowed modules. A full-suite failure on the head; the builder never ran the full suite.
*   **Rationale:** Core rule: vendor imports only in their kind module. Red gate.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Import only from `pydantic` (`pydantic.errors.PydanticCustomError`, `pydantic_core.ErrorDetails` typed via `pydantic`'s re-exports, or a local type) so no allowed-list change is needed; if a second import cannot be avoided, add the module to the guard's allowed list with a written reason and a negative test. Run the full suite on the final head.
*   ***Proposed Edit:***
    *   Location: `src/hadavin_sdk/hidden_input.py`.
    *   Change: remove the `pydantic_core` import.

### [Issue 4] [`codebase M1`, `design M1`, `evidence Z21 Z128 Z163`] - Severity: Major
*   **Affected Scope:** `tests/stage_mutants.py` (Z190 1098-1099, Z21, Z128, Z163), `tests/_text_guard.py:1555-1556`, `tools/mutation_runner.py:538-539`.
*   **Discrepancy Description:** Four mutants cannot apply (SNIPPET NOT FOUND): the text they replace is not in the head. Z190 was the only mutant for the `%d` proof rule (and removes the old restriction, not the new `number_valued` proof, so the rule has no mutant); Z21, Z128, Z163 the same class.
*   **Rationale:** A mutant that cannot apply proves nothing; a bad row fails the gate once Issue 1 lets it run.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Re-anchor each on text that exists (Z190: `old` = `and self.number_valued(rest[j], env)`, `new` empty, pinned to the planted `%d` argument that is a text parameter). Add at the shared choke point a pre-check that fails at import when a mutant's snippet is absent, so a drift shows in the unit tests and not only in the slow run. Run all 405+ mutants.
*   ***Proposed Edit:***
    *   Location: `tests/stage_mutants.py`, `tools/mutation_runner.py` (or its test).
    *   Change: as above.

### [Issue 5] [`evidence survivors`, `codebase M2`, `design m4`] - Severity: Major
*   **Affected Scope:** `tests/stage_mutants.py` (M18v, Z65, Z152, Z159, Z192, Z193, Z194, Z209, Z223, Z90, Z154, Z184, Z221), `tests/test_stage_names.py`, `tests/test_q8a1_b17_fixes.py`, `src/hadavin_sdk/hidden_input.py`.
*   **Discrepancy Description:** Nine mutants survive, three are killed for the wrong reason, one crashes (event_id not a plain file name). Z192-Z194 are probably equivalent: `HiddenInputModel` defines `__init__`, so `model_validate`, `model_validate_json`, `model_validate_strings` route through the hiding `__init__` and the `hidden = exc` mutants survive; only Z191 is a real kill. R17t and R17u have no mutant and no guard change (controls passing on old code); the notes say "Z202-Z218" but Z218 does not exist; Z171 proves the flag, not the value; Z152 survives and Z154 is killed by another test (not shown to die for its named reason).
*   **Rationale:** Same class as r17 Issue 3: a mutant counted as good that does not prove its fix.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Per survivor: write the killer that fails for the named reason, or prove the mutant equivalent in the notes with the code reason and remove it (never leave a survivor in the set). For Z192-Z194: delete the redundant overrides or make the test bypass `__init__` (and state that `strict=` and `context=` of `model_validate` are ignored on a custom-init model; no src call uses them today). Z221: find why the plant raises (an invalid event id in the fixture) and fix the plant. Re-point Z154 and Z184 and Z90 so each dies for its named reason. Final head: whole set to `problems: []` with the exact CI command.
*   ***Proposed Edit:***
    *   Location: `tests/stage_mutants.py` and the tests named.
    *   Change: as above; correct the notes numbering.

### [Issue 6] [`codebase M3`, `design M3`, `design M4`, `codebase m4`] - Severity: Major
*   **Affected Scope:** `tests/_text_guard.py:486`, `:562-572`, `:1246-1251`, `:1381-1385`, `:1501-1504`; `tests/test_stage_names.py:3869-3888` (R17a, R17c, R17h-k, R17t, R17u); `tests/test_guard_reasons.py:1135-1137`, `:1217-1227`; `src/hadavin_sdk/store/protocol.py:58-149`; CHANGELOG items 4 and 7.
*   **Discrepancy Description:** (a) The stored-record sink prefixes (update, insert, write, execute, append, put) do not match the real store API (`create_run`, `transition`, `add_cost`, `touch`, `save_*`, `record_decision`, `add_dead_letter`, `add_spend`, `set_kill_switch`, `save_tick_state`, `add_tool_call`); `store.add_dead_letter(DeadLetter(reason=exc.args))` is unseen; plants Z206-Z210 use names real code does not call. Keywords of the store-call family are not scanned; the `Dict` branch of `_tainted` has no mutant; r17 F1(e) (`AuditEvent(operation=name)`, `rec["agent"] = cfg_name`, `store.insert_event(detail=agent_cfg_name)`) is still invisible. (b) The `-> int` proof is matched by bare function name (`_declared_number_function`), so `log.warning("bad %d", client.count(name))` drops its argument for a library receiver returning text; the `fsafe` branch resolves by the definition reached, this one does not. Also `_numeric` trusts any call named `index` or `count`; `_proc_carriers` leaves out `*args` and `**kwargs`; two REDACTED rows keyed by module and text; message sinks still unseen: `sys.stderr.buffer.write`, `os.write(2, ...)`, `f = sys.stderr.write` aliases, `Thread.name = x`, `match` shadowing.
*   **Rationale:** Same guard class as r17 Issue 1, closed one more step; FOUND is 0 on today's `src/`, so these concern the next edit.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Derive the store prefixes from `store/protocol.py` (the method names are the single source: a test fails when a protocol method is not covered by a prefix family); scan keywords and dict/attribute sinks of stored model classes (`AuditEvent`, `Run`, `DeadLetter`, `ToolCallRecord`, `TickState`); resolve `-> int` through `self.resolve(call)` like `fsafe`; plant each shape with a real method name and add a mutant per branch (including `Dict`); add the sinks listed (or name the exact residual shapes in the CHANGELOG with a ticket and date if one cannot be seen by a static guard). 
*   ***Proposed Edit:***
    *   Location: `tests/_text_guard.py`, `tests/test_stage_names.py`, `tests/stage_mutants.py`, CHANGELOG.
    *   Change: as above.

### [Issue 7] [`evidence probes`, `evidence fail-before`] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/errors.py` (`shown_name`, `shown_id`, `word_like`), `src/hadavin_sdk/audit/models.py:33-52`, `src/hadavin_sdk/audit/local_dir.py`, `tests/test_q8a1_b17_fixes.py`.
*   **Discrepancy Description:** `shown_name` returns a word-like name with no loaded set (it should return the fixed placeholder unless the name is in a loaded set); an `event_id` that is a `str` subclass with its own `__str__` is stored as the plain text (`plain_event_name` uses `isinstance`, `_write` formats with an f-string: a `model_construct` event passes the regex on content and builds the path from the subclass text); the YAML-library probe from r17 is still not shown to reach the patched name. Fail-before: 18 failed / 769 passed (builder said 20 / 767); 43 of 61 new tests pass on old code with no written reason; 4 older test ids also fail on the old code.
*   **Rationale:** Evidence contradicts a builder claim and shows two leak shapes.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** `shown_name` and `plain_event_name` use `type(x) is str` and `str.__str__` as `shown_id` already does; a test and a mutant each; the YAML test patches the name `_read_yaml` actually calls (assert the patch was hit). Write the pass-on-old-code table per test (the reason: control, new guard path, or already-fixed shape) and explain the 4 older failing ids; give the measured fail-before numbers, not remembered ones.
*   ***Proposed Edit:***
    *   Location: files named; `handover/evidence` notes of the builder.
    *   Change: as above.

### [Issue 8] [`codebase m1`, `codebase m2`, `codebase m3`, `design m1`, `design m2`, `codebase n1`] - Severity: Minor
*   **Affected Scope:** CHANGELOG batch 17 (items 7 and the handler list), `tests/_guard_allowances.py:884-891`, `tests/test_guard_reasons.py` (`check_literal` 175-187, `check_rowid` 361-367, `check_card` 2465-2475, 2533-2543), `tests/test_changelog_claims.py:49-105`, `src/hadavin_sdk/audit/local_dir.py:91`, `:119-121`, `:150-160`, `src/hadavin_sdk/audit/models.py:49`, ticket `Q8a1-card-demo-fixture.md`.
*   **Discrepancy Description:** New LITERAL rows (`deferred.py` `a.data_class`, `llm/anthropic.py` `settings.platform`) are "checked" by a check that does not read them; ROWID only greps for "seq INTEGER PRIMARY KEY"; "18 became rows with a checked reason" is false for at least 3. CHANGELOG item 7 CARD is wrong both ways (`check_card` does canary `chain_id` and `requested_by`; "half checked" against "54 of them checked"); the docstring names `Q8a1-CARD-FIXTURE`, the ticket is `Q8a1-card-demo-fixture`, and it still says "every other field". The handler list says none prints error text yet lists `_run_tool` and `invoke` (which show `error_reason(exc)`; owner E1). `test_changelog_claims.py` checks (file, function, count) only; a one-line `except X: pass  # noqa` is not counted. `write_intent` wraps all of `_write` in `except ValueError`, so a serialisation error or the `ConfigError` of an unreadable index is reported as "event id is not a plain file name"; poison events stay in `_pending` forever (disclosed, tested).
*   **Rationale:** Prose and checks that say more than the code keeps; same class as r17 Issue 2.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Make each check read the row it names; fix the counts and the handler sentence; test `plain_event_name` before the `try`; correct the ticket name. Cheap; files are open anyway.
*   ***Proposed Edit:***
    *   Location: files named.
    *   Change: as above.

### [Issue 9] [`design m3`, `design m5 (rest)`, `design nit`, `codebase nit`] - Severity: Nit
*   **Affected Scope:** `tests/test_q8a1_b17_fixes.py:127-137`, `tests/_text_guard.py`, HTTPCODE check (accepts any handler type ending in `HTTPError` without checking the import), scoped rows keyed by bare function name (fails safe), the two Nit entries of the design persona.
*   **Discrepancy Description:** Small trust widenings and wording; all fail safe.
*   **Rationale:** Nits.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Fix where the builder is already in the file, no new review for these.
*   ***Proposed Edit:***
    *   Location: files named.
    *   Change: tighten the HTTPCODE check to the import; list sibling-model coverage with Issue 2; others by the builder's judgment, listed in the ledger.

### [Issue 10] [`design owner items`, `codebase judged`] - Severity: Major
*   **Affected Scope:** E1 `q-q8a1-hide-ids`, E2 `ConfigName`, the `error_reason` owner question (5 REDACTED rows pinned), CARD demo-fixture ticket due 2026-11-19.
*   **Discrepancy Description:** The owner items are disclosed and not built; `_run_tool` and `invoke` still show `error_reason(exc)` text.
*   **Rationale:** They need the owner's decision; the reviewers state them as such.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** The evidence (the owner's decisions on id display and the config name type) is outside every file a reviewer could read. Do not fix, do not report as closed.
*   ***Proposed Edit:***
    *   Location: none.
    *   Change: none. The builder keeps the 5 REDACTED rows pinned in number and keeps the reason text linking the owner question.

## Handoff
- Accepted fixes (PROPOSE FIX): 9 groups (Issues 1 to 9; Issue 9 holds the Nits, fixed because the files are open anyway).
- Contested: 0. Escalated: 1 (Issue 10, owner items E1, E2 and the error_reason question). Declined: 0.
- Remaining unaddressed: 0 of the reviewers' findings (each is in a group above). Severity counts kept as reported: design 0 Blocker 4 Major 6 Minor 2 Nit; codebase 1 Blocker 3 Major 4 Minor 1 Nit. The evidence adds one Blocker group (Issue 1, a gate that cannot run), one Major group (Issue 3, lock-in guard) and the mutant and probe groups (Issues 5 and 7).
- Gate state at `b5b6c9fd`: red (stage_mutants and migration_numbers_mutants cannot start; one real full-suite failure; 17 of 405 mutants not good). Not mergeable on this head.

## Who fixes it
One batch-18 builder (Sonnet 5.5) on a new branch `core/q8a1-b18` from `b5b6c9fd`, pushing to `wip/cloud-q8a1-b18`. Order: Issue 1 (the gate that cannot run), Issue 2 (HiddenInputModel channels), Issue 3 (lock-in), Issue 4, Issue 5, Issue 6, Issue 7, Issue 8, Issue 9. Method per bug: name the class, fix at the shared choke point, grep for siblings, show each new test failing on `b5b6c9fd`, one mutant per fix with a killer that fails for the named reason; a written reason for every test that passes on old code; CHANGELOG corrections. Final head: the full suite, the exact CI `stage_mutants` command and `migration_numbers_mutants` each run to completion with `problems: []` (raw output kept; the known timing test is not touched). Security path: no round cap; another independent evidence run and two reviewers follow the batch-18 push. Owner items E1, E2 and the error_reason question stay OWNER-ONLY.
