Status: resolved

# Goldfish Annotated Review Report (Q8a-1, round 7)

**Target:** `core/q8a-1-live-override-refusals` head `4ccb4f9a`, snapshot `/home/user/build/snap/q8a1b6-4ccb4f9a`. Redaction and security path (secret values in error text): no round cap. No person was available: recommended option for every item. Nothing is DECLINEd where a secret stays readable.

Sources: `/home/user/build/reports/q8a1b6-design-r7.md` (0 Blocker, 4 Major, 2 Nit) and `q8a1b6-codebase-r7.md` (0 Blocker, 4 Major, 4 Nit); both read-only, nothing run. Evidence: `handover/evidence/Q8a-1/4ccb4f9a/RESULTS.md` (full suite 10807 passed, 1 skipped; 110 of 110 mutants; 8 of 107 probes show the made-up marker; 29 hold it only in `__context__`). Reviewer pydantic-message claims were from memory; the evidence probes confirm them (the executor kind tag message quotes the value).

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` F1, `codebase` F1, `evidence` item 1] - Severity: Major (readable value)
*   **Affected Scope:** `config.py:520-525` (`_what`), `contract.py:44`, `registry.py:240-241`, and the registry "unknown name" messages the probes found: agents `model_route`, `scope_allowed` name, actions `target_system`, `chain_id`, `verify_check`, executor `kind` tag, `tools/<name>.yaml` with no agent (marker twice), tool `operations` entry.
*   **Discrepancy Description:** `_what` returns pydantic's message for every error type except `value_error`; for a bad discriminator (`union_tag_invalid`) that message quotes the typed tag. The registry cross-checks print the offending identifier back (8 of 107 probe results readable).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A value typed into a config file reaches the error text on a redaction path; same class as rounds 1-6. A one-by-one patch is not enough; the choke point is how every file-derived name reaches an error.
*   ***Proposed Edit:*** (a) `_what`: allow-list of pydantic error types whose message is a fixed sentence; `union_tag_invalid` and `union_tag_not_found` get a fixed sentence; any other type becomes "a value was refused (<type>)". (b) Every registry message that quotes a file-derived name goes through `shown_name` (or one helper `named()` used by all of them); grep `registry.py`, `deferred.py`, `contract.py`, `config.py`, `app.py`, `sources/__init__.py` for f-strings with names from files. (c) One table test that feeds the marker into every field the probes list (all 8 plus the 29 hidden ones) and asserts 0 occurrences in `str`, `repr` and the printed traceback; fixture proves the probe finds the 8 on the old head. Mutants: widen the allow-list; remove the helper at one site.

### [Issue 2] [`design` F2, `codebase` F2] - Severity: Major
*   **Affected Scope:** `deferred.py:46-101` (lines 52, 55, 59, 63, 65, 69, 72, 77, 83, 87, 89, 91, 98), reached from `registry.py:247-248`.
*   **Discrepancy Description:** Raw `a.id`, `c.id`, the `levels` key and the action name are printed; ids are free strings (`registry.py:43,54`, `contract.py:50`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Wrap every printed name with `shown_name` (one wrapper, not 13 edits). Test: marker as a `levels` key, an agent id and a chain id; mutant: remove the wrapper at one site.

### [Issue 3] [`design` F3, F6, `codebase` F8] - Severity: Major (app and source names), Nit (rest)
*   **Affected Scope:** `app.py:478-481` (`_unprobed_tools`, raised `:213`), `sources/__init__.py:73,78,81`; also `tools.py:232` (`cluster_suffixes`), `tools.py:312,316,345,375,383,433,441,449`, `tools.py:416` (`from exc`), `app.py:377,382` (`ca_file`, `ca_secret_name`), `backends/platform_secrets.py:29,49,54,63`.
*   **Discrepancy Description:** Raw names reach error text on build paths; the CHANGELOG says `app.build` follows the rules. `app.py:479-481` is pattern-bound (safe) per the codebase reviewer.
*   ***AI Suggestion:*** PROPOSE FIX (all sites; the safe one gets a comment and a test pinning the pattern)
*   ***Proposed Edit:*** `shown_name` at every site above, drop `from exc` where the cause carries the typed value (or suppress context as elsewhere). Test per site with the marker. CHANGELOG lists exactly the paths covered.

### [Issue 4] [`design` F4, `codebase` F4] - Severity: Major (latent)
*   **Affected Scope:** `config.py:505-517` (`_own_error`); `tests/test_stage_names.py:1552-1569` (Probe class lives in the tests module); mutants M16l, M16m; docstring and CHANGELOG (3 places).
*   **Discrepancy Description:** A ValueError counts as "own" if the last traceback frame is in `hadavin_sdk`. A C builtin (`int()`, `float()`, `Decimal()`, `bytes.fromhex`) called from a validator leaves no own frame, or leaves one and quotes the value; the test passes only because its probe sits in the tests module.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A frame heuristic is a guess; the message text of a ValueError is only safe to show if we wrote it.
*   ***Proposed Edit:*** A dedicated `ConfigValueError` class: `value_error` messages are shown only when the cause is that class; every other ValueError gets the fixed sentence. Convert the existing own validators to raise it. Test with validators defined inside a `hadavin_sdk` module that call `int(marker)`, `float(marker)`, `Decimal(marker)`, `bytes.fromhex(marker)` and raise a plain ValueError with the marker. Re-point M16l and M16m to kill by that test. Fix docstring and CHANGELOG.

### [Issue 5] [`codebase` F3] - Severity: Major (behaviour change, untested)
*   **Affected Scope:** `tools.py:573`, `:574-597`, `:536-537` (`_port`'s dead `except ValueError`).
*   **Discrepancy Description:** `safe_urlsplit` now raises `InvalidUrl` (a ValueError) for `https://host:abc/x` and `:99999`; main raised `ToolRefused("the URL's port is not valid")`. The runtime path now raises a different exception class.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** In `fetch`, catch `InvalidUrl` and raise `ToolRefused("the URL is not valid")`; delete the dead branch; tests for `:abc`, `:99999`, bracket and login shapes assert `ToolRefused` and no value in the text.

### [Issue 6] [`evidence` item 1 and probe notes] - Severity: Major (accepted shapes), to be classified per case
*   **Affected Scope:** `openai_compat` `base_url` and Vault `address` accept an ASCII `user:<marker>@host` login (`systems.base_url` refuses it); fullwidth brackets and fullwidth percent accepted in all three URL fields; `egress.yaml` with an extra key raises nothing; unknown values raise nothing at `load_registry`: `tools_allowed`, `principals approver_of` and `rights`, `chains approver_ids`, egress host, route key.
*   ***AI Suggestion:*** PROPOSE FIX for the login in the two URL fields (a secret typed into a URL is exactly what `url_has_login` exists for; fail closed) and for fullwidth bracket and percent (normalise or refuse as for the other fullwidth shapes). For the others, the builder checks each: if a typo can silently disable a check (an unknown right or approver id that is ignored), it must be refused with a fixed sentence; if it is already caught later, say where, with the line.
*   ***Proposed Edit:*** Route both fields through the same URL check as `systems.base_url`; add the 16-shape table to those fields; `egress.yaml` extra key refused. Report per-case classification in the notes.

### [Issue 7] [`evidence` fail-before] - Severity: Minor
*   **Affected Scope:** 250 of 285 new tests pass on the previous head `3f3d4b6c` and 47 on main (217 in `test_q8a_live_overrides.py`, 33 in `test_stage_names.py`; list in `new-pass-on-3f3d4b6c-by-function.txt`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Builder gives a one-line reason per test function (73 functions) why it passes on the old code (a control or table row extending a class already fixed) or makes it fail on the old code. Tests that are neither controls nor failing get a mutant.

### [Issue 8] [`codebase` F5, F6, F7, `design` F5] - Severity: Nit (PROPOSE FIX, cheap)
*   **Proposed Edit:** F5: `runtime/tick.py:76-78` docstring reworded; the test asserts the sentence, not just "replace()". F6: `test_stage_names.py:1588` assert behaviour not the constant; `:1355` drop the "a value was refused" alternative; `:1387` regex covers `parse.urlsplit`, `up.urlsplit`, import-as; add a 64-character name case (kills the `{1,63}` mutant), a Cyrillic look-alike, positives other than "PW"; a mutant removing `registry._yaml`'s OSError branch. F7: wrap `OSError` in `config._read_yaml` and `load_config`; catch `TypeError` for unhashable YAML keys in `_UniqueKeyLoader`, `registry._yaml` and `_load_tools`. Design F5: test `SourceConfig._kind_checks` with a secret as `api_url` plus an extra key (nested `KubernetesSettings` error).

## Handoff counts
Accepted (PROPOSE FIX): 8 issues (Issues 1-5 and 6 Major). Contested: 0. Escalated: 0. Declined: 0. Not run by anyone: Python 3.12 CI job, perf step, Vault server tests, app-build probe. Round 8 review needed after the fix batch (redaction path, no round cap); evidence for round 8 must include the app-build probe and the marker table across all 8 readable shapes.
