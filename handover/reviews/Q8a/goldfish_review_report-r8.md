Status: resolved

# Goldfish Annotated Review Report (Q8a-1, round 8)

**Target:** branch `core/q8a-1-live-override-refusals`, head `a1869655`. Config error text must never quote a configured value: redaction/security path, no round cap. No person was available: recommended option for every item. Reviews: `/home/user/build/reports/q8a1b8-design.md` (0 Blocker, 4 Major, 2 Minor, 2 Nit) and `q8a1b8-codebase.md` (0 Blocker, 3 Major, 2 Minor, 1 Nit); both read-only.
**Evidence (independent, head confirmed):** `handover/evidence/Q8a-1/a1869655/RESULTS.md`. ruff, format, bandit, scan_repo, gitleaks: exit 0. stage_mutants 138/138 alone. **Full pytest FAILS: 12 failed, 10973 passed, 1 skipped.** 11 of the 12 fail again alone: they assert the OLD error wording while the code gives the new wording (7 parametrized cases of `tests/contracts/test_secrets.py::test_a_missing_name_is_a_config_error_at_the_start_up_probe`, `tests/test_k3_pilot_env.py::test_k3_http_refused_in_pilot`, `tests/test_p2_postgres.py::test_cli_limits_without_a_readable_dsn_is_a_config_error`, `tests/test_s3_gate.py::test_bad_unknown_chain`, `tests/warden_port/test_audit_chain.py::test_audit_verify_that_cannot_build_its_store_could_not_verify`). The same six files pass 361 on origin/main. The 12th failure was the runner's own Postgres environment slip (passes on re-run). The builder never ran the whole suite; its "full suite" statement was wrong. Probes: previous 107-probe set 0 readable (was 8); round-8 probes 260, 7 readable, all plain-shaped lower-case ids (agent x2, action x2, chain, principal x2: Issue 6), plus a tool call URL host and tool-author `operation=`/`method=` values echoed. `Decimal(marker)` raises `InvalidOperation` through `load_config` raw (no marker text). A symlink loop used as `config.yaml`/`agents.yaml`/`principals.yaml`/`chains.yaml` is read as an empty file; a no-permission `actions/` folder is read as empty; `tools/<agent>.yaml` as a directory raised nothing. Timing flake (3 runs): head fail, fail, pass; main fail, fail, fail (busy machine). Fail-before: of 461 new test ids, 381 pass on `4ccb4f9a` and 60 pass on origin/main. Not run: Python 3.12 job, perf, Vault-server tests, semgrep/zizmor/pip-audit/trivy, `app.build` endpoint use of the URL fields.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`evidence`, `design` F4, `codebase` R8-1] - Severity: Major (full suite red)
*   **Affected Scope:** the 11 stale tests above; `registry.py:242-244`, `:385-391`; `tests/test_k3_pilot_env.py:108-126`.
*   **Discrepancy Description:** 11 tests assert old wording; `test_k3_http_refused_in_pilot` fails because the new `approver_ids` refusal (`"u"` not in principals) fires before `deferred.check`. The builder claimed a full run that never happened.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** a red suite blocks everything; fixed by reading each new wording deliberately, not by loosening `match=`.
*   ***Proposed Edit:*** update each of the 11 tests to the new wording and state the new wording per test in the builder notes; for k3, add person principal `u`. Decide the channel-native case: `slack_channel._who` parses `slack:U123`, so check `approver_ids` against principals only for chains that name an `approver_of` relation (a person-principal link), otherwise a fixed upgrade note in CHANGELOG ("approver ids must be persons in principals.yaml when ... "). Run the WHOLE suite once at the final head and show the line.

### [Issue 2] [`design` F1] - Severity: Major
*   **Affected Scope:** `app.py:371` (`_tls_context`: only empty PEM `:377` and `ssl.SSLError` `:381` caught), reached from `_build_source` `:420` and `_toolbox` `:547`; test `test_stage_names.py:2472-2480` writes the file first. Other path-like settings: `recorded_dir`, `dir`, `private_key_path`, `ca_cert`, `sslrootcert`, `jwt_path`, `local_dir_audit`.
*   **Discrepancy Description:** a missing, over-long, directory or non-UTF-8 `ca_file` raises a raw `OSError`/`UnicodeDecodeError` that quotes the configured text (a pasted PEM/token).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the exact class the spec forbids; same shape in the other path settings (not read by the reviewer).
*   ***Proposed Edit:*** one wrapper for every file open driven by a configured path: catch `(OSError, UnicodeError, ValueError)` and raise `ConfigError(<fixed sentence> + shown_name + type name) from None`; apply it to all seven path settings listed; load-time check that `ca_file` is a file under the config folder (as `prompt_file` at `registry.py:406`); add missing-file, directory, over-long-name rows to PROBE_ROWS for each setting.

### [Issue 3] [`design` F2] - Severity: Major
*   **Affected Scope:** `registry.py:362`, `tools.py:379` (`pin[:12]`), `config.py:391` (`tool_module_hashes: dict[str, str]`).
*   **Discrepancy Description:** a credential pasted in the pin position leaks its first 12 characters.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** validate values as `[0-9a-f]{64}` at load with a `ConfigValueError` fixed sentence; print a digest prefix only when `_DIGEST.fullmatch(pin)`, else `<not shown>`. Test and mutant.

### [Issue 4] [`design` F3, `codebase` R8-4] - Severity: Major
*   **Affected Scope:** `app.py:424`, `:507` (source name to the model via `error_reason` `tools.py:1026`, `:1203`), `:215` (log of the `scope_inventory` key), `:541` (log `agent_id`, `action`); `secrets_vault.py:113,117,119,122,125,141,148,181` (secret name, field, `auth_mount`, env var name, `jwt_path`); `llm/common.py:53` (`route {name}`), `_LATEST` `:32`; `table.py:267,269` (`token_env`, `secret_id_env` plain `str`).
*   **Discrepancy Description:** unfiltered file-derived names beside `shown_name` calls on the same values; pasting a token into `token_env` prints it (later reads, TTL refresh and the Vault transit signer's login, are unwrapped and reach tick logs).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the unlisted siblings of the sites already fixed; per the lead decision (Issue 6) the fix is at the one shared filter, with a repo test that fails when any f-string/format in the listed modules interpolates a config-derived name outside `shown_name`.
*   ***Proposed Edit:*** route every site through the shared filter or say "the configured environment variable"; pattern-validate `token_env`, `secret_id_env`, `field`, `role_id` at load (`_NAME`); logs use the filter too. Add the AST/grep guard test (listed sites by module name), plus a mutant.

### [Issue 5] [`codebase` R8-2, R8-3] - Severity: Major (mutant strength)
*   **Affected Scope:** `tests/stage_mutants.py:458-460` (M17zb) with killer `test_stage_names.py:2354-2360`; M17r with `config.py:510-511`, `:699-705`.
*   **Discrepancy Description:** M17zb does a real DNS lookup; the lookup error arrives as `URLError` (`guard/http.py:130-146`, `tools.py:636-639`), not the `gaierror` it declares, so the verdict depends on the network. M17r is killed only because the assert message contains the class name; `load_config` catches the same `OSError` again.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** M17zb: stub opener, no network, crash type that the stub raises. M17r: `expect="cannot be read"` and ordinary mutant status; remove the redundant `OSError` catch at `config.py:703` so the guard at `:510` is the only one, and say so in a comment. Re-run `stage_mutants` alone.

### [Issue 6] [`design` F6, `evidence` plain-id probes] - Severity: Minor (design) / evidence: 7 readable results
*   **Affected Scope:** `errors.py:21` (`[a-z0-9_.-]{1,64}`), `errors.py:30`; ids of agent, action, chain, principal, tool, route, system, source and `scope_inventory` key; tool call URL host and tool-author `operation=`/`method=` echoes.
*   **Discrepancy Description:** plain-shaped ids pass the shape filter, so a lower-case plain secret typed as an id is shown; fixture ids such as `svc:test-agent` contain `:` and always print `<not shown>` (too strict).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** DECISION made by the lead (reversible, recorded in `handover/DECISIONS.md`): a file-derived name appears in error text only if it is the id of an object that was loaded (a member of the registry's own id sets) AND word-like (letter first, at most 40 characters, no run of 20 or more hex/digit characters); everything else is shown by position ("entry N"). Fix at the one shared filter (`shown_name` / `error_where`), not per site. A load-time id grammar is added only if it does not break existing fixture ids; `:` is allowed so real ids can show. Tool call URL host and tool-author `operation=`/`method=` echoes use the same filter.
*   ***Proposed Edit:*** implement the rule in `errors.py`; probe set of 7 lower-case markers must read 0; fixture ids print as themselves; counter-test: a hex-like or 64-char id prints by position.

### [Issue 7] [`evidence` facts] - Severity: Major
*   **Affected Scope:** `load_config` (`config.py:699-705`): `Decimal(marker)` raising `decimal.InvalidOperation` escapes raw; a symlink loop as `config.yaml`/`agents.yaml`/`principals.yaml`/`chains.yaml` is read as empty; a no-permission `actions/` folder and `tools/<agent>.yaml` as a directory are read as empty or raise nothing.
*   **Discrepancy Description:** a non-`ConfigError` escapes `load_config`; an unreadable config file silently becomes an empty config (more permissive than refusing).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** a configuration that cannot be read must stop start-up with a fixed sentence; reading it as empty can drop restrictions.
*   ***Proposed Edit:*** catch `ArithmeticError`/`decimal.DecimalException` (and `ValueError`/`TypeError` generally from validators) at the load choke point and raise a fixed-sentence `ConfigError`; every config file read distinguishes "does not exist" (as before, allowed where optional) from "exists but cannot be read" (symlink loop, directory, permission) which is a fixed-sentence `ConfigError` with the file name via the filter. Tests per file and mutants.

### [Issue 8] [`design` F5] - Severity: Minor
*   **Affected Scope:** `registry.py:278-282` (`found[agent_id] = {}` for an empty manifest); `config_hash` `:161-165`, toolbox `app.py:530`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** check `tools_allowed` only `if specs`; test an empty manifest plus callables from `app.build(tools=)`.

### [Issue 9] [`design` F7, `design` F8, `codebase` R8-5] - Severity: Nit
*   **Affected Scope:** `tools.py:117` (`ToolSpec(**entry)` TypeError for non-string keys; `parse_manifest` `registry.py:272` outside the `_yaml` try); `tools.py:245` (`ports {bad}`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** catch `(TypeError, ValueError)` in `parse_manifest`; print "N entries" instead of the port numbers.

### [Issue 10] [`codebase` R8-6] - Severity: Nit
*   **Affected Scope:** `test_stage_names.py:1903` ("107 results, 8 readable"; real 126 = 68 URL + 58 others), `:2533-2535` (first disjunct never true), `config.py:189-194` (`url_has_login` unused by production), `registry.py:191` (`TypeError` with no source), CHANGELOG "review rounds 1 to 7"; `_FIXED_SENTENCE_TYPES` test only checks names exist (several types never produced), `test_the_marker...` checks `__cause__` not `__suppress_context__`; `ConfigUrl` field-type test covers `TABLE`/`KINDS` only, not `System.base_url`.
*   ***AI Suggestion:*** PROPOSE FIX (cheap)
*   ***Proposed Edit:*** fix the stale numbers and wording; remove or use `url_has_login`; add the `__suppress_context__` assertion; extend the field-type test to `System.base_url`; for the never-produced allow-listed types add one produced-case test each or drop the type from the list if it cannot occur.

### Items recorded, no change
*   Pre-existing and out of this change: Slack `api_base` (`table.py:336`) has no scheme check (`http://other-host/` accepted for a bot token); a query string passes `config_urlsplit` (never printed); tool run-time `ToolRefused` texts quote operation/host from code (outside scope; the host and `operation=`/`method=` echoes of Issue 6 are now in scope). Timing-harness flake: separate ticket `core/fix-timing-harness-flake`. ConfigUrl additive; ACCEPTED_ROWS disable no check; `_what`/`_FIXED_SENTENCE_TYPES`, `error_where`, `_UniqueKeyLoader`, `_read_yaml`, `tools.fetch` InvalidUrl all checked fine by the reviewers.

## Handoff counts
Accepted (PROPOSE FIX): 10 (Issues 1-10). Contested: 0. Escalated: 0. Declined: 0. Round 9 review needed after the fix batch (security path, no round cap) with independent evidence at the fixed head, including the whole suite and the 3.12 CI job variant where possible.
