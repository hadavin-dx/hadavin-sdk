Status: resolved

# Goldfish Annotated Review Report (Q8a-1, round 6)

**Target:** branch head `3f3d4b6c`, snapshot `/home/user/build/snap/q8a1b5-3f3d4b6c/files`. Security path, no round cap. No person was available: the recommended option was taken for every item. Reviews: `/home/user/build/reports/q8a1-design.md`, `q8a1-codebase.md`; evidence `q8a1-EV.md`. Nothing was run by the reviewers; the evidence runner's results are partial (no RESULTS.md, fail-before has no result).

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design`] D1 - Severity: Major
*   **Affected Scope:** `config.py:180-193` (`url_has_login`, `url_allowed`), `config.py:414-421`, `backends/table.py:79` and `:317`; text reaches the user via `config.py:499-506`.
*   **Discrepancy Description:** `url_has_login` swallows `ValueError` from `urlsplit` and returns False. `url_allowed` then calls `urlsplit` again; for a netloc that changes under NFKC into one containing `/ ? # @ :`, the standard library raises a `ValueError` whose text holds the whole netloc, login included. Pydantic wraps it as `Value error, netloc '...'`, and `_value_free_text` keeps `msg`.
*   **Rationale:** the promise "never the value that was refused" is false for this path; no test has a non-ASCII netloc.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Class: a library error message copied into our error text. The choke point is `_value_free_text` / `config_error_text`, plus the three `urlsplit` callers.
*   ***Proposed Edit:*** (a) one helper `safe_urlsplit(value)` that turns any `ValueError` into a fixed refusal sentence ("not a valid URL"), used in `url_has_login`, `url_allowed` and `table.py:79`, `:317`; no other direct `urlsplit` of a configured value (grep for siblings in `src/`). (b) At the choke point: for `value_error` entries that did not come from our own validators, keep the type name only. (c) Tests for fullwidth `@` and `:` in the netloc for `systems`, the OpenAICompat `base_url` and the Vault `address`; they must fail on 3f3d4b6c. Add a mutant.

### [Issue 2] [`design` D2 Major, `codebase` D1 Minor - same finding]
*   **Affected Scope:** `registry.py:261` (`parse_manifest(_yaml(path), where)` in `_load_tools`), called at `registry.py:234` outside any `try`; `cli.py:304`.
*   **Discrepancy Description:** A malformed `tools/<agent>.yaml` raises a raw `yaml.YAMLError` whose text quotes the source line; it bypasses `config_error_text` and `from None`. The CHANGELOG sentence "a YAML error with its line and column only" is false for this file.
*   ***AI Suggestion:*** PROPOSE FIX (severity kept at Major, the higher of the two reports)
*   ***Justification:*** Verified by both reviewers at the same lines; the cause is a read site outside the choke point.
*   ***Proposed Edit:*** Wrap `_yaml` itself (so every present and future read goes through `except yaml.YAMLError as exc: raise ConfigError(config_error_text(exc)) from None`), not only line 261. Grep every `load_yaml` / `_yaml` caller for siblings. Test: a made-up credential on a broken YAML line in `tools/<agent>.yaml`, for `load_registry` and for `load_config`; add a mutant.

### [Issue 3] [`design`] D3 - Severity: Minor (a pasted secret as a key name stays visible)
*   **Affected Scope:** `config.py:505` (`".".join(str(p) for p in e["loc"])`), `config.py:60` comment, `config.py:409`, `:416`, `:419`; `registry.py:348-349`, `:380`, `:384`, `:386`.
*   **Discrepancy Description:** Unknown mapping keys appear through `loc`; values such as an unknown `model_route` and an unknown scope name appear in registry cross-check messages. The docstring and CHANGELOG say a value is never shown.
*   ***AI Suggestion:*** PROPOSE FIX (also covers the codebase Nit D2 and the evidence rows: 5 key rows and 2 value rows)
*   ***Justification:*** A pasted credential can be the key or the unknown name. Dropping the text costs the user little (the file and the item position remain). On a security path the honest option is to fix, not to document.
*   ***Proposed Edit:*** For `extra_forbidden` entries replace the key in `loc` with `<unknown key>` and keep the parent path. For the registry cross-check messages, say which field and which file ("model_route is not defined", the position or count), never the value. Where a name is needed to help the user, show it only if it passes the identifier check (`[a-z0-9_-]{1,64}`, no look-alike characters) and otherwise show `<not shown>`. Fix the docstring and CHANGELOG to match what the code does. Tests with a marker as key and as value for each row in the evidence probe (the 7 rows); mutants.

### [Issue 4] [`codebase`] D3 - Severity: Nit
*   **Affected Scope:** `tick.py:57-60`, `:97` (the copy sentence is attached to every given-time refusal).
*   ***AI Suggestion:*** PROPOSE FIX (the builder reads the review text; if the sentence is not wrong for any path, it is kept and the reason is written down)
*   ***Proposed Edit:*** Attach the "not copied by replace()" sentence only to the refusal it explains.

### [Issue 5] [`evidence`] E-1 - Severity: Major (process)
*   **Affected Scope:** fail-before for item 7 and the full evidence.
*   **Discrepancy Description:** The head test file `tests/test_q8a_live_overrides.py` imports `VaultConnection`, which origin/main lacks, so collection aborts on main; no fail-before result exists. The runner also left no RESULTS.md.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Move the import into the test where it is needed (a guarded import or `pytest.importorskip`-free helper in a shared test module that exists on main) so the new tests collect on the old code and fail there. A new evidence runner then records fail-before for all new tests (Issues 1-3 included), the 7 probe rows, the burst test, and a full run at the final head.

## Handoff counts
Accepted (PROPOSE FIX): 5. Contested: 0. Escalated: 0. Declined: 0. Remaining unaddressed: 0 until the fix batch. Round 7 review needed after the fix (no round cap).
