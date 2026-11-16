Status: resolved

# Goldfish Annotated Review Report (Q8a-1, round 8)

**Target:** branch `core/q8a-1-live-override-refusals`, head `18741c8c`. Live-override refusals and error-text hiding (security path, no round cap). No person was available: recommended option for every item. Reviews (both read-only, nothing run): `/home/user/build/reports/q8a1b8-design-r8.md` (2 Major, 3 Minor, 1 Nit) and `q8a1b8-codebase-r8.md` (2 Major, 3 Minor, 2 Nit). Neither found a readable secret or a regression against main. Evidence (independent, head confirmed, tree clean): `handover/evidence/Q8a-1/18741c8c/RESULTS.md`: full pytest 11024 passed, 1 skipped (Stubber), 28 deselected; `stage_mutants` 160 of 160 good; ruff, format, scan_repo, gitleaks exit 0; bandit exit 0 (one existing nosec warning); fail-before `a1869655` 51 failed, `origin/main` 283 failed; ticket probes 60 of 60 overrides refused, falsy overrides refused, static Vault token refused at build. Not run: timing test, perf, pip-audit, semgrep, zizmor, trivy.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` F1] - Severity: Major
*   **Affected Scope:** `tools.py:119-121` (`error_where`), `errors.py:123-137` (`shown_name`).
*   **Discrepancy Description:** Tool-manifest field names such as `max_output_bytes` now print as `<not shown>`, because `error_where` runs the membership test inside `load_registry`'s loaded-ids context, which does not hold field names. `max_output_bytes: 0` gives "invalid tool entry (<not shown>)". This is a regression against main and contradicts the CHANGELOG ("names of fields and kinds" are not covered). No test asserts the field name is visible.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A field name is code-owned text, not a configured value; hiding it removes the only useful part of the message and no secret is protected.
*   ***Proposed Edit:*** `error_where` shows field names by the word-like test only (a helper without the membership test). Add a test that the field name is visible in the message.

### [Issue 2] [`design` F2] - Severity: Major (owner question, two parts)
*   **Affected Scope:** `backends/platform_secrets.py`, `actions/secrets_{aws,azure,gcp,file,env,cache,vault}.py`, `app.py` (`_own_secrets`), `tools.py` (`secret()`); `tests/test_stage_names.py:3103-3111`; CHANGELOG.
*   **Discrepancy Description:** Secret-name fields get only the word-like test; the membership test is vacuous there (the loaded set is built from the same names or is empty). A password pasted into `private_key_secret_name` such as `hunter2` appears in "secret hunter2 not found ...". `audit/signer.py` already uses fixed labels. The CHANGELOG is silent about the secret providers and the tests try only shapes that fail the word-like test.
*   ***AI Suggestion:*** PROPOSE FIX (the recommended default is "hide"; the two-part owner question below still stands)
*   ***Justification:*** Safe direction follows least privilege and masking-by-default. Owner question to record in `questions-for-lead.md` with default hide: (1) plain-shaped defining ids of agent, action, chain and principal stay printed (already disclosed in the CHANGELOG); (2) secret-name and other reference fields are hidden. Part 2 follows the safe default now; part 1 stays as is until the owner answers.
*   ***Proposed Edit:*** Secret-reference sites name the field or position ("the `private_key_secret_name` secret", "secret 2 of settings.secrets") instead of the value. Plant a lower-case plain word as a secret-name field in each provider and assert it is absent from the message. State the decision in the CHANGELOG. Mutant for one provider.

### [Issue 3] [`codebase` F1] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/actions/secrets_file.py:71-73` (`build`).
*   **Discrepancy Description:** `ConfigError(f"secrets mounted_file: {root} is not a folder")` quotes a configured path (same class as `jwt_path` and `ca_cert`, fixed in this delta). The module is in `GUARDED_MODULES`, but `root` is not in `CONFIG_DERIVED`, so the guard passes. Input: `backends.secrets: {kind: mounted_file, dir: <pasted text>}`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same class as earlier rounds; the guard's spelling list is the reason it was missed (Issue 6).
*   ***Proposed Edit:*** Fixed sentence ("secrets mounted_file: the configured dir is not a folder"). Add a test with a pasted-text `dir`, and a mutant.

### [Issue 4] [`codebase` F2, `design` F3] - Severity: Major (design rated Minor; the larger rating is kept)
*   **Affected Scope:** `src/hadavin_sdk/evals.py:72-75`.
*   **Discrepancy Description:** The golden-case gate quotes the case id and `input_ref` with `!r` from a file in `golden_dir`. `evals.py` is not in `GUARDED_MODULES` and subscripts are invisible to the guard.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** File content is configured data; the quoted `input_ref` can carry pasted text.
*   ***Proposed Edit:*** Name the case by its position ("golden case 3") and leave the values out; add `evals.py` to `GUARDED_MODULES`; test with a secret-shaped id and `input_ref`.

### [Issue 5] [`codebase` F4] - Severity: Minor
*   **Affected Scope:** `runtime/agent_loop.py:227-230` (also `:171`, `:151`).
*   **Discrepancy Description:** `Runtime.__init__` prints raw loaded ids that did not pass the word-like test (a 40+ character id or one with a hex run prints whole); CHANGELOG says the agent id is shown only with a plain shape.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** `shown_name(agent_id, registry.agents)` and `shown_name(action, registry.contracts)`; same for `Unqualified(agent_id)` and `path.name`; test with a 40-character id.

### [Issue 6] [`design` F4, `codebase` F3] - Severity: Minor
*   **Affected Scope:** `tests/test_stage_names.py:3116-3248` (guard, `CONFIG_DERIVED`, `GUARD_ALLOWED`, `test_the_guard_sees_a_name_printed_outside_the_filter`), CHANGELOG line 13.
*   **Discrepancy Description:** The guard is a spelling list over f-strings and log arguments in 18 modules; it misses `{root}`, subscripts, `%`, `.format`, `str()`, concatenation and `raise X(name)`, unlisted modules, and cannot report a stale `GUARD_ALLOWED` entry. The test that claims to cover a name printed outside the filter never calls `_guard_violations` (evidence also shows it passing on old code).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Overclaim in the CHANGELOG; the guard is the only thing that would have caught Issues 3 and 4.
*   ***Proposed Edit:*** Reword the CHANGELOG to "known spellings"; add `root`, `case` and subscripts to the list; add all message-printing modules found by walking `src`; fail on a `GUARD_ALLOWED` key that no longer matches a node; make the self-test run `_guard_violations` on a synthetic module (fails on the old guard).

### [Issue 7] [`design` F5, `codebase` F5] - Severity: Minor
*   **Affected Scope:** `audit/local_dir.py:73-75,99,143-147,163,177`; `tools.py:365` (`module_sha256`); `evals.py:140`; `secrets_vault.py` (~175-192, ca_cert); CHANGELOG lines 13 and 17.
*   **Discrepancy Description:** "One reader for every configured path" is overclaimed: only `local_dir._entries` moved; `module_sha256` and the run-time reads bypass it; the loaded set is set only by `registry.py:273` and `:329`, so other sites apply the word-like test alone; `ca_cert` goes through a fixed value-free wrapper, not the reader.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Route `module_sha256` through `read_configured`; convert the `local_dir` start-up reads (or narrow the text to "the audit index read at start-up"); add the no-loaded-set exception to the CHANGELOG, delete "and the other loaders", name `ca_cert` as an exception.

### [Issue 8] [`design` F6] - Severity: Nit
*   **Affected Scope:** `registry.py:433`, `:448-451`; CHANGELOG.
*   **Discrepancy Description:** Docstring stale after the `approver_ids` relaxation; decision path authorises by membership only (`approvals/requests.py:159`); no widening.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One sentence in each place.
*   ***Proposed Edit:*** Update the docstring; add to the CHANGELOG that the person check is advisory and the decision path authorises by membership.

### [Issue 9] [`codebase` F6] - Severity: Nit (mutant strength)
*   **Affected Scope:** `tests/stage_mutants.py` M18g, M18n, M18o, M18r, M18v (`expect="assert"`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Use the fragments "the pin says", "is not set", "model_id", "entry 1", "login" so only the intended assertion satisfies `expect`.

### [Issue 10] [`codebase` F7] - Severity: Nit
*   **Affected Scope:** `secrets_vault.py:142`, `tests/test_p4b_secrets.py`.
*   **Discrepancy Description:** The sign-in failure text no longer says which method; a trade-off, not a leak.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One fixed word from a Literal (`settings.auth` kind), no configured value.
*   ***Proposed Edit:*** "the configured auth mount (approle): sign-in refused (400)" with the kind from the validated field.

### [Issue 11] [`evidence`] - Severity: Nit (recorded)
*   **Discrepancy Description:** On old code `test_the_guard_sees_a_name_printed_outside_the_filter`, the `[hex64]` and `[upper]` id tests and the empty-manifest test pass (controls or vacuous); 14 older tests also fail on `a1869655` src with the new test files.
*   ***AI Suggestion:*** PROPOSE FIX for the first (Issue 6); DECLINE the rest as controls for earlier classes, with one line each in the next evidence table.

## Handoff counts
Accepted (PROPOSE FIX): 11 (Issues 1-11; Issue 11 only for the guard self-test). Contested: 0. Escalated: 0 (one owner question recorded with the safe default hide for secret-name and reference fields, plain-shaped defining ids unchanged). Declined: 0 apart from the controls in Issue 11. No unaddressed Blocker. Majors (Issues 1-4) need a fix builder (b9) and a round 9 review (security path, no round cap); fixes by class: every message site that prints a configured value, plus the guard that must find such sites.
