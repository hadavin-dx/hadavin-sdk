Status: resolved

# Goldfish Annotated Review Report (Q8a-1, round 11)

**Target:** branch `wip/cloud-q8a1-b11`, head `c6028abbe78cbe5d01521242054238aceb9e6961` (delta `f4acee28..c6028abb`, 15 files). SECURITY path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `q8a1b11-design-r11.md` (0 Blocker, 0 Major, 3 Minor, 3 Nit) and `q8a1b11-codebase-r11.md` (0 Blocker, 1 Major, 5 Minor, 2 Nit). Previous round: `goldfish_review_report-r10.md`. Independent evidence: `handover/evidence/Q8a-1/c6028abb/RESULTS.md` and its probe files.

**Evidence status (first).** ruff, format, bandit (rerun with `--with bandit`), `scan_repo`, gitleaks exit 0; `stage_mutants` 184 of 184; full pytest exit 0: 11083 passed, 1 skipped (`test_llm.py ... [bedrock]`, Stubber refuses the shape), 0 failed. Planted-name probe, 718 rows: head 9 rows show the marker (all one case, see Issue 4), `f4acee28` 88 rows; Kubernetes namespace 0 rows on the head. Fail-before on `f4acee28` src: 19 failed, 4283 passed. Widened guard: saw 10 of 25 planted shapes, missed 15 (Issue 2).

**Not run:** the timing test, pip-audit, Semgrep, CI steps beyond `stage_mutants`, botocore error texts (both reviewers worked from memory), installed-extras behaviour of the importorskip tests. The probe scripts of the last evidence run were gone, so the probe rows are not the same rows as last time.

**Both reviewers found:** no readable configured name in any message path of the delta, no regression versus main, every claimed round 10 fix present. The findings below are about a false claim, a guard that is still a list of spellings (fourth return of the class), library text on cause chains, and tests that cannot fail.

## Prioritized Findings & AI Suggestion

### [Issue 1] [`codebase` D1 (Major), `design` D1 (Minor): one finding] - Severity: Major
*   **Scope:** `backends/table.py:149` (AWS secrets region), `:166-167` (S3 bucket and region), `:239` (KMS region), `:127` (Postgres region); allowance reason `_HOST_LIST`; docstring of `tests/test_q8a1_f_string_trace.py` hits 9-11.
*   **Description:** "region and bucket are checked by a pattern" is false for the AWS and S3 settings (plain `str`); only Anthropic, Bedrock, guardrail and the GCS bucket carry a pattern. `_aws_host(f"{s.bucket}.s3", s.region)` puts unchecked text into a host string; the test plants a bad Anthropic region only.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A claim in a security allowance that the code does not keep. Evidence: the planted-name probe found AWS/S3 settings forms clean only because pydantic's own error text did not quote them in the rows tried; the claim itself is unproven. Fix, not defer.
*   ***Proposed Edit:*** Add `pattern=_NAME` (or the existing region pattern) on the four region fields and an S3 bucket pattern (3-63 lowercase letters, digits, dots, hyphens, no leading or trailing dot or hyphen); add bad-bucket and bad-region rows for S3, AWS and KMS to the trace test; correct the `_HOST_LIST` reason and the docstring to say exactly what is checked and "returned only, no caller prints it today" where true.

### [Issue 2] [`design` D2, `codebase` D3, evidence probe 7] - Severity: Minor (the class has now come back four times)
*   **Scope:** `tests/test_stage_names.py:3566-3738` (`_bound_names`, `_config_derived`, `_message_nodes`, `TEXT_METHODS`, `SETTINGS_LIKE`); the evidence: 15 of 25 planted shapes not seen: renamed variable, `self._cfg.api_url`, `f"{exc}"` pass-through, `label = name` then f-string, value through a helper, `%(a)s % {...}`, `string.Template`, `print`, `sys.stderr.write`, `extra={...}`, `exc.add_note`, `m = str(exc)` then raise, `format_map`, an f-string of an unlisted variable name, `json.dumps({...})`. Reviewers add: `f"{root / name}"`, `.split/.partition/.rsplit/.zfill/.ljust/.rjust`, nested tuple targets, `with ... as`, `except ... as`, `:=`, `.append/.extend/.add` arguments, empty-separator `join`, `_settings`/`_cfg` attribute names, function parameters.
*   ***AI Suggestion:*** PROPOSE FIX (the stronger option, not a longer list)
*   ***Justification:*** Three reviews have found a new spelling each time; adding the 15 names would repeat that. The class is "a configured or library-quoted value reaches text that a person or a log can read". The choke-point fix is to invert the guard: at every message site (raise argument, `warnings.warn`, log call positional and keyword, `print`, `sys.stderr.write`, `add_note`, `.append/.extend` into a problem list, f-string, `%`, `.format`, `.format_map`, `Template`, `join`, `+`, `+=`, `json.dumps`) flag any interpolated expression that is not a literal, a written number, a loop index, or an expression the allowance table names with a reason. Names are then not what decides; only the allowance table does. State plainly in the CHANGELOG what an AST scan cannot see (a value that passes through a call into another module) and keep the probe-7 table as 25 planted-fault rows.
*   ***Proposed Edit:*** Rewrite `_config_derived` as "not proven code-owned" instead of "in CONFIG_DERIVED"; remove the name lists as the decider; add all 25 probe-7 shapes plus the reviewers' extras as planted faults (one fault per row, each must give exactly one site) and clean forms for the carve-outs; recurse into nested tuple targets, `with`, `except`, `:=`; extend the allowance table only with a true per-site reason. Run the widened guard over all real `src/` before the builder reports; every new site gets a fix or a true reason. Mutants in `stage_mutants.py` for each new rule branch.

### [Issue 3] [`design` D3] - Severity: Minor
*   **Scope:** `audit/signer.py:87` (`raise ConfigError(...) from exc`, KMS error text quotes key ARN or id); `audit/local_dir.py:112` (`AuditUnavailable from exc`, OS error with the configured path). Both exist on main; `cli.main` prints only `str(exc)` (`cli.py:75`) but the chain shows when uncaught or `HADAVIN_DEBUG=1`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Library text quoting a configured value is where this round's real leaks were; `from exc` carries it. Same class as the round 11 wrappers.
*   ***Proposed Edit:*** `from None` in both; add both to the trace table with a test that a raised library error quoting a made-up marker leaves no marker in `__cause__`, `__context__` or the traceback. Grep for other `from exc` / `from e` sites in `src/` that wrap a library error and fix each the same way, or list why the library text is code-owned.

### [Issue 4] [evidence probe 5] - Severity: Minor
*   **Scope:** settings forms with an unknown key whose name is the marker (`AwsSecretsManagerSettings(**{<marker>: 1})`): pydantic's "extra forbidden" error names the key. 9 of 718 rows on the head, the same 9 on `f4acee28`; same on main (not a regression).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A person can type a secret into the key position (a misplaced paste). The class is one message path: the place where the config loader turns a `ValidationError` into text. Fixing it there covers every settings model.
*   ***Proposed Edit:*** At the loader's one choke point, replace the text for errors of type `extra_forbidden` by "unknown setting at position N (name not shown)" and list the allowed names of that model (code-owned); add a row per settings model with a marker key; check `loc` as well as `msg`. If the loader already prints the key on purpose for diagnosis, the same rule that governs ids applies: this is question `q-q8a1-hide-ids` and its default (do not show) stays.

### [Issue 5] [`codebase` D2, `design` D4] - Severity: Minor (D2), Nit (D4)
*   **Scope:** `tests/test_stage_names.py:3838` (no inner function; `scope` already in CONFIG_DERIVED, so `bound_of` is not exercised; deleting the outer-scope merge `:3672-3677` would not fail), `:3845` (ends in a fixed sentence); planted-fault dict has 18 faults and 8 clean forms while the brief says 16; the carve-out "a sum is a message unless one side is a written number" (`:3694-3697`) has no self-test either way.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Evidence: the 18 planted-fault rows, 8 clean-form rows and 5 control tests pass on `f4acee28` src (they scan synthetic text), so only a mutant can show they can fail. Not yet shown for these two rows.
*   ***Proposed Edit:*** Row 3838: an inner `def g(other): raise A(f"{other}")` with `other` bound in the outer function, expected clean, and a variant expected flagged; row 3845 ends in a derived name in `g`. Add `name + 1` clean form and `name + "x"` faulty form. Correct the count in the CHANGELOG and docstrings. Once Issue 2 is done these rows are rewritten anyway; keep the principle: each row has a mutant of the guard that makes it fail.

### [Issue 6] [`codebase` D4, `design` D6] - Severity: Minor (D4), Nit (D6)
*   **Scope:** false or too-wide allowance reasons: `actions/contract.py` `unexpected {k}` (`_FIELD_NAMES` wrong: k is a key of the supplied input); `backends/platform_secrets.py` `f'{type(s).__name__}.{k}'` labelled `_POSITION`; `audit/chain.py` CREATE TABLE labelled `_GENERATED_ID` (fits `_SQL`); `models.py` `f'{path}.{k}'` labelled `_NOT_TEXT` but path is printed at `models.py:34`; `audit/signer.py` `f'{source} is not an Ed25519 private key'` (`load_private_key` passes `str(path)`, `signer.py:199`); `cli.py` lines where `audit.verify` includes `anchor object {names[i]!r}` (`chain.py:502`, a raw listed object name); `guard/judge.py` `_ASK.format(source=source)` (source can be `tool:{call.name}`, `agent_loop.py:570`); `store/migrate.py` `_ROLE_CLI` (true for current callers only); `_URL_BUILD` on `executor.py` and `kubernetes.py` ("region or resource a pattern checked": base is `systems[...].base_url`, path a contract template); `_FIELD_NAMES` on `contract.py`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A guard whose reasons are untrue gives false comfort and hides real sites (chain.py:502 prints a raw listed object name; models.py:34 prints a path of a caller-supplied key).
*   ***Proposed Edit:*** Go through every allowance reason against its site (about 112; the two reviewers read about 70 and 15): fix the nine named above; for the real prints (`chain.py:502`, `models.py:34`, `signer.py:199`, `judge.py`) either show a position or a class, or state that the value is code-owned and why. Add a test that reads each reason's category and checks the category's predicate where it can be checked by AST (the category `_POSITION` is an int, `_SQL` is a constant).

### [Issue 7] [`codebase` D5] - Severity: Minor
*   **Scope:** `GUARD_EXEMPT_MODULES` entry `k1b/` ("never the client configuration") false: `k1b/audit_sink.py:59-71` reads `cfg.backends`; `k1b/replay.py:86,111,118` reads `registry.config`. `k1b/replay.py:117` prints raw `unknown agent {agent_id!r}`, contradicting the CHANGELOG sentence "an unknown agent id handed in by a caller is <not shown>".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Use the existing shown-name helper (or `<not shown>`) at `replay.py:117`; narrow the exemption to the files that really read no configuration (list them), scan the rest; add a row to the trace test.

### [Issue 8] [`codebase` D6, `design` D5] - Severity: Minor (D6), Nit (D5)
*   **Scope:** `actions/secrets_cache.py:33-43`: `from None` is right, but `__context__` still holds the library text (the CHANGELOG "Not covered" line says so, "drops the library's text and cause" is stronger). The same base serves `VaultProvider` and `MountedFileProvider`: a Vault `URLError`/`TimeoutError`/`SSLCertVerificationError` now reads "secrets: reading a secret failed (URLError)" (`secrets_vault.py:82` catches only `HTTPError`); AWS/Azure/GCP lose the error code. The three tests of the new branch use `pytest.importorskip`, so mutant M21a is not killed without the extras.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Suppress the context too (`raise ... from None` inside a block that does not leave the library error in `__context__`, e.g. build the new error after leaving the `except`); say in the CHANGELOG exactly what is dropped; name Vault and mounted_file; add a fixed-vocabulary hint for the class (timeout, TLS, access denied, not found) taken from the exception class only; an extras-free test with a `CachedSecrets` subclass raising `RuntimeError` and point M21a at it.

### [Issue 9] [`codebase` D7] - Severity: Nit
*   **Scope:** `tests/contracts/test_sources.py:228` (the round-11 note said `:285`; the line is the assertion message that still calls `rules_problems("prod", rules)`; it raises `TypeError` on failure and hides the real failure).
*   ***AI Suggestion:*** PROPOSE FIX (one line)
*   ***Proposed Edit:*** Message uses a position (`rules_problems(0, rules)`) or no call; grep the tests for other assertion messages that call the changed function.

### [Issue 10] [`codebase` D8] - Severity: Nit
*   **Scope:** `stage_mutants` Y5 `expect="Vault"` also matches the class name; `anthropic.py:60` "usual cause" hint names `ANTHROPIC_FOUNDRY_RESOURCE`/`ANTHROPIC_BASE_URL` for every platform including vertex; `migrate.py` message names `runtime_role` while the flag is `--runtime-role` (`cli.py:98-104`); `config.py:399` "tool_module_hashes: entries N" counts positions among mapping values; CHANGELOG Kubernetes bullet "a pasted credential included, is refused" is false for a lower-case token of at most 63 characters (the test itself uses `SECRET_SHAPES["hex32"]` as a legal namespace, `test_stage_names.py:3141`); `rules_problems` accepts 0 and negatives.
*   ***AI Suggestion:*** PROPOSE FIX (each is small; all in this batch)
*   ***Proposed Edit:*** Y5 `expect="looked at no Vault kind"`; hint chosen by platform; the flag spelling in the message; "entry N of tool_module_hashes (counted from 1)"; reword the CHANGELOG bullet to what the pattern refuses ("a value that is not a valid DNS name; a lower-case token of up to 63 characters is a valid name and is accepted"); `rules_problems` refuses `< 1` as the other labels count from 1.

### [Issue 11] [evidence item 4 and the r10 repeat] - Severity: Minor
*   **Scope:** fail-before on `f4acee28` src: 19 failed, 4283 passed; of the 33 changed or new test functions, the 18 planted-fault rows, 8 clean-form rows, 5 control tests and about 9 more pass on old code; on main src 287 failed.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The proof that a new test can fail is its killing mutant or a stated control reason. For this round the guard tests pass on old code by construction (they scan synthetic text), so the mutants of the guard are the proof.
*   ***Proposed Edit:*** The builder writes, in the PR notes, one line per new or changed test function since `f4acee28`: fails on old head (command and first output line), or control with the reason, or the killing mutant id from `stage_mutants.py`. The next evidence runner repeats the classification on the final head.

### [Issue 12] [`design` item 8, owner question `q-q8a1-hide-ids`] - Severity: n/a (record)
*   **Scope:** a `ConfigName` type that carries "not shown" through every use.
*   ***AI Suggestion:*** ESCALATE (stays open, safe default: no type)
*   ***Justification:*** The design reviewer recommends no type now: it would not close the library-quoted-text hole (the value goes to the library as plain text), and it would change every settings field and validator. The cheaper controls (Issues 2, 3, 4, 8) are in this batch. The question needs the owner because it changes how every setting is typed. Safe default: no type; keep the question in `questions-for-lead.md`.

## Handoff counts
Accepted (PROPOSE FIX): 10 findings (Issues 1 to 11 except 12; Issue 1 counts the two duplicated reviewer entries once). Escalated: 1 (Issue 12, stays open, default stated). Declined: 0. Contested: 0. Remaining unaddressed: none. Severity unchanged from the reviews (Issue 1 Major, the rest Minor or Nit). Because the path is security with no cap: one batch-12 builder fixes Issues 1 to 11 and reports once; then one independent evidence run (full pytest with the database, the 25-shape probe 7 on the new guard, the 718-row probe 5 including a marker as an unknown key, the per-test fail-before classification) and two `egm:*` reviewers read the new head.

## Who fixes it
One batch-12 builder on a new branch `core/q8a1-b12` from `c6028abb`, plain push to `wip/cloud-q8a1-b12`. Files (the builder checks that no other open package edits the same lines, and says so): `src/hadavin_sdk/backends/table.py`, `backends/platform_secrets.py`, `actions/secrets_cache.py`, `actions/contract.py`, `audit/signer.py`, `audit/local_dir.py`, `audit/chain.py`, `k1b/replay.py`, `models.py`, `cli.py`, `guard/judge.py`, `store/migrate.py`, `config.py`, the loader that renders `ValidationError`, `llm/anthropic.py` (path as found), `sources/kubernetes.py`; tests `tests/test_stage_names.py`, `tests/test_q8a1_f_string_trace.py`, `tests/stage_mutants.py`, `tests/contracts/test_sources.py`; `CHANGELOG.md`. Evidence `RESULTS.md` is the verifying artifact for the ledger rows; they stay FIXED-UNVERIFIED until then.
