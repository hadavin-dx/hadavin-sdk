Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8a-1 batch 13, head 918c0345 (branch wip/cloud-q8a1-b13), full diff against origin/main. Security path (configured names and library text must not reach a message), no round cap. Round 13.
**Inputs read:** `handover/reviews/Q8a-1/q8a1b13-design-r13.md`, `q8a1b13-codebase-r13.md`, previous report `goldfish_review_report-r11.md`, independent evidence `handover/evidence/Q8a-1/918c0345/RESULTS.md`.
**Mode:** automated, no person available; the recommended option is taken for every item. No severity was changed. Duplicates across the two reviews are merged by root cause.

## Evidence in one paragraph (what it confirms, what it did not run)
Full pytest: 1 failed, 11259 passed, 1 skipped. The one failure is an environment slip of the runner's own Postgres (no PGHOST/PGPORT in the server environment); that file alone passed (253) after the restart; the other tests were not re-run after the restart. stage_mutants 246 of 246 good. Probe 7: 25 of 25 planted guard faults found (10 of 25 on the previous head). Probe 5: 0 marker rows on both trees. Fail-before: 15 of 538 tests of the 4 changed files fail on the old source, 523 pass on it. Hostile inputs on the head: a tick step failure message still shows in the log line and in the stored `last_error` (12 rows, same on the old head); the injection detector log line carries the detector's exception text for 3 of 3 markers. The timing flake test failed 3 of 3 alone on the head (known, fix lives on `core/fix-timing-harness-flake`, do not touch). Not run: Vault-backed tests (IMPOSSIBLE-NOW, need a CI run with `HADAVIN_REQUIRE_VAULT_ENGINE=1` before 2026-12-11), pip-audit, Semgrep, zizmor, Python 3.12, full suite on main.

## Escalated to the owner or lead (listed first)
- **E1** [`design`/`codebase`] Severity: Major (REDACTED reason). Which names and ids may be shown at all is the open owner question `q-q8a1-hide-ids`. The safe default stays "do not show". *AI Suggestion:* ESCALATE for the question only; the false REDACTED claims are fixed in Issues 1 and 2 regardless.
- **E2** [`design`] Severity: Minor (carried from r11 Issue 12). The `ConfigName` type is an owner choice. Nothing to build. *AI Suggestion:* ESCALATE.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` D1 + `codebase` M1] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/guard/injection.py:92-97`, `guard/bedrock_guardrail.py:104-109`, `tests/_guard_allowances.py:26, 539-542`.
*   **Discrepancy Description:** `injection_check` logs `safe_head(str(exc), 300)` for any detector error. The shipped `GuardrailDetector.check` calls `apply_guardrail` with no class-only wrapper, so a botocore error text (guardrail id or ARN, role ARN, account id, region) reaches a WARNING line on every flagged run. The start-up twin `check_filter` is wrapped in `call_class_only`. The builder's own test `test_a_failing_detector_is_logged_by_class_only` failed on old code, was dropped from the head, and the row was relabelled CLASSNAMES to REDACTED with no code change. The REDACTED reason ("a custom detector is the operator's code") is false for the built-in detector.
*   **Rationale:** Breaks the "do not show" default and the fix-do-not-defer rule. Evidence confirms: 3 of 3 markers appear in the log line.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid and confirmed by independent evidence. Same class as the start-up call, which was already fixed.
*   ***Proposed Edit:***
    *   Location: `bedrock_guardrail.py` run-time `apply_guardrail` call; `injection.py` log line; the allowance row; tests.
    *   Change: wrap the call in `call_class_only`; log the class name only (operator detector text only for a non-shipped kind, and only through the same filter); restore `test_a_failing_detector_is_logged_by_class_only`; add a Bedrock-shaped case with a bare guardrail id in the error text; add a mutant whose killer is that test; correct or delete the REDACTED claim for this row.

### [Issue 2] [`design` D2 + `codebase` m1, m3, m4] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/runtime/tick.py:379-384, 409-410` (`_message`, `_DRIVERS`), allowance row `tests/_guard_allowances.py:592`, `_each` `tick.py:128-143`, `tick.py:272, 369, 390, 411, 474, 488, 496`, `errors.py:87-105`.
*   **Discrepancy Description:** For any error not from `_DRIVERS` (psycopg, urllib, http, botocore, boto3, socket, ssl), `_message` returns `safe_head(str(exc), 500)` into the persisted `tick_state.last_error` and an ERROR log. Errors from azure, google, hvac, kubernetes, httpx, requests, anthropic, openai, psycopg_pool pass as text. The REDACTED reason does not describe tick steps, and the test only asserts `startswith("ValueError")`. Related: `_each` no longer logs "moved by another worker, skipped" (undisclosed); `Failed()` and `suppress(Exception)` are blind handlers without a written reason, and the test greps for strings.
*   **Rationale:** Evidence: 12 rows show the marker on the head and on the old head. A configured host, namespace or resource name can land in the database and the log.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. Inverting the rule (show text only for a class defined under `hadavin_sdk`) closes the whole class, not one library list.
*   ***Proposed Edit:***
    *   Location: `tick.py` `_message`; tests; notes.
    *   Change: text only for `hadavin_sdk`-defined error classes, class name for everything else; planted-marker test plus mutant; keep the debug line for a CAS loser or state in the notes why it was removed; give each `Failed()` and `suppress(Exception)` site a one-line written reason, and make `test_tick_has_no_blind_handler_and_no_suppression_comment` check the structure (an AST scan of the handlers) instead of two strings; fix the REDACTED reason text.

### [Issue 3] [`design` D3 + `codebase` M5] - Severity: Major
*   **Affected Scope:** `tests/test_guard_reasons.py:98-105, 159-162, 271-292, 659-672`, `tests/stage_mutants.py:835-846`.
*   **Discrepancy Description:** Several "checked" reasons have checks that cannot fail. `check_keyver`: the status clause is always false (`status_text` is in the import line) and the path regex expects a bare first argument while real calls start with a quoted method, so the loop runs zero times. `check_label`: `A or (B and C or D)` accepts any f-string lacking `shown_name` and the bare names `what`, `label`, `name`. `check_listed` swallows `AssertionError` and continues, so a renamed function silently stops being checked. `check_words` allows generic names. `check_seq` (string order), `check_state` (annotation text), `check_time` (spelling regex) are textual. 10 of the 12 newly checked reasons (GEN, SIGN, TIME, CLASSNAMES, SEQ, BUILT, KEYVER, MIGNAMES, FIELDS, ARG) have no mutant; Z59-Z64 cover DIGEST and STATE only.
*   **Rationale:** The claim "12 more reasons checked" overstates what is proven.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; read from the lines by both reviewers.
*   ***Proposed Edit:***
    *   Location: `tests/test_guard_reasons.py`, `tests/stage_mutants.py`.
    *   Change: KEYVER by AST (every `{status}` in a `VaultError` raise is `status_text(...)`; request path starts with `keys` or `sign`); LABEL requires a `Constant` or an exact parameter and walks the callers; `check_listed` fails when the function is missing; `check_words` tests where values come from, not names; `check_seq`, `check_state`, `check_time` by AST or `get_type_hints`; one mutant per reason, each killed by the reason check with a message naming it.

### [Issue 4] [`design` D4 + `codebase` M4] - Severity: Major
*   **Affected Scope:** `tests/test_guard_reasons.py:24-26, 769`, notes "Not done" bullet 1.
*   **Discrepancy Description:** 12 reasons are unchecked (BUNDLE, CARD, KIND, LLMREQ, MODELTEXT, NUM, NUMFIELD, PKGERR, PROC, REDACTED, STOREID, URL). The stated reason, "the AST cannot show the declared type of a field", is untrue: the same file already uses `typing.get_type_hints` (`check_report`) and `model_fields` (`check_literal`). STOREID is wrong at Issue 5 and BUNDLE partly wrong at Issue 8.
*   **Rationale:** Only REDACTED has a true exception reason (owner question). The preamble allows deferral only for impossible, owner or third-party cases.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. The unchecked list may only shrink.
*   ***Proposed Edit:***
    *   Location: `tests/test_guard_reasons.py` `UNCHECKED` and the checks.
    *   Change: check NUM and NUMFIELD (resolve each named field's annotation), KIND (`Literal` or a table lookup), PKGERR (every `ConfigError(`, `StoreUnavailable(`, `AuditUnavailable(` call has a constant message and every `except ... as exc` that prints `{exc}` catches only `hadavin_sdk` error classes), PROC (reuse the KEYREF "not in raise, print or log" walk) now; for CARD, LLMREQ, STOREID, URL, BUNDLE, MODELTEXT, check them too or name which of the three exceptions applies with the next step; REDACTED stays with the owner (E1); lower the pinned size to match.

### [Issue 5] [`codebase` M2] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/store/postgres.py:78, 82-86, 161`, `tests/_guard_allowances.py:695-697, 703`.
*   **Discrepancy Description:** `mode = sslmode or parts.get("sslmode")` where `parts` comes from `conninfo_to_dict(dsn)` and `dsn` is the resolved secret. The setting is a `Literal` (`table.py:122`) but the DSN fallback is not validated; with `iam_auth` an odd sslmode value is printed in a start-up refusal that `cli.py:75` shows. The STOREID reason ("an id the code generated") is false for this site.
*   **Rationale:** The DSN is the most sensitive secret in the store; the guard row certifies the opposite.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; read from the lines.
*   ***Proposed Edit:***
    *   Location: `postgres.py` the two refusal messages.
    *   Change: print `mode` only if it is one of the six libpq modes (disable, allow, prefer, require, verify-ca, verify-full), else `<not shown>`; a test with a planted odd value in the DSN; a mutant; give both rows a true reason and a check.

### [Issue 6] [`design` D6 + `codebase` M3, m8] - Severity: Major (codebase's severity kept; the design persona called it Minor)
*   **Affected Scope:** `tests/_text_guard.py:30, 57-61, 618-621`, `src/hadavin_sdk/registry.py:306-307, 409-422`, `src/hadavin_sdk/audit/chain.py:484, 506-513`, `errors.py:117-118`, `postgres.py:174-178`, `chain.py:530-543`.
*   **Discrepancy Description:** A list append, extend, add or insert is a message site only when the receiver name matches `PROBLEM_LIST`, though the module says "Names do not decide, only the proof". `registry.py:421` `out.append(str(exc))` is joined into `ConfigError("; ".join(pin_problems))` and is not a site. `chain.py:510-513` prints `sorted(labels)` (filled from an anchor body's `key_label`) in the offline `could not verify:` output with no row. Also: `zip` and `enumerate` are in `SAFE_CALLS` but return their arguments' elements; `from None` inside an `except` leaves `__context__` set; callers are resolved by function name, which is not conservative for an imported function sharing the name of an all-safe tree function.
*   **Rationale:** The same "list of spellings" class that r11 Issue 2 said to remove. The guard cannot see these paths, so the next edit would not be caught.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; both personas read the same sites.
*   ***Proposed Edit:***
    *   Location: `tests/_text_guard.py`, `registry.py`, `chain.py`.
    *   Change: any `append/extend/add/insert` of a non-proven value on a local list that later reaches a return, join or raise is a site whatever the receiver is called; remove `zip` and `enumerate` from `SAFE_CALLS` (or treat them as their arguments); resolve callers by the real definition (module and qualified name), not the bare name; give `chain.py` labels through `shown_name` or by count; planted-fault rows (receiver `out`, a `zip` pass-through, a same-name imported function); a mutant per new branch.

### [Issue 7] [`design` D5] - Severity: Major
*   **Affected Scope:** `CHANGELOG.md:27`.
*   **Discrepancy Description:** The paragraph names the reason `UNREAD` (164 at the end of batch 12, listed and counted by a test that no longer exists) and "mutants Z1 to Z5". The batch has no entry for: `Route.model_id` now needing `^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$` at load (`config.py:80`, a new load-time refusal); hosts cut by `_HOSTNAME`; provider error codes cut by `_DETAIL`; `errors.Failed` and `status_text`; the gate line using `shown_name`.
*   **Rationale:** A new load-time refusal needs an upgrade note; the changelog claims what the code no longer keeps.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid.
*   ***Proposed Edit:***
    *   Location: `CHANGELOG.md` Q8a-1 entry.
    *   Change: rewrite the stale paragraph from the real counts of the final head; add a breaking-change line for `Route.model_id` (what is refused, how to check a config before upgrading); one line each for the other changes, in plain words, plus what the widened guard catches and what an AST scan cannot see.

### [Issue 8] [`design` D7, D8, D9, D10, nits + `codebase` m2, m5, m6, m7, nits] - Severity: Minor and Nit (merged)
*   **Affected Scope:** `llm/retry.py:27-29, 83-87`; `guard/egress.py:11-14, 13`; `executor.py:148-149`; `secrets_vault.py:90, 94, 118`; `tests/test_q8a1_b13_fixes.py:66-70, 128-137`; `k1b/bundle.py:188-190`; `config.py:78-80`; `tests/_text_guard.py:1206`; `tests/test_guard_reasons.py:639-643, 66`; `errors.py` `status_text`; notes.
*   **Discrepancy Description:** (a) `_DETAIL` keeps up to 80 characters with spaces, so a plain sentence passes and a test asserts it is kept. (b) The HOST filter comment and reason overclaim: a lowercase hex or hyphenated key matches `_HOSTNAME` and prints whole. (c) The executor `http_418` pin has no mutant and cannot fail (a text status raises `TypeError` at the comparison first); `secrets_vault.py` has four `status_text` sites and only sign-in is tested. (d) 45 `noqa: BLE001` remain in src (agent_loop 19, chain 8, local_dir 4, cli 4, tools 3, requests 3 and others), each `as exc` handler needing a per-site read. (e) The strict-model test covers config, registry and tools only; `extra="forbid"` appears in 9 source files. (f) Notes overclaim "signer_vault status_text, a real leak found": shipped providers return an int, so it is hardening only. (g) `k1b/bundle.py:188-190` prints `case = path.name` before validation (the operator's command-line argument; class ARG; unbounded and unescaped), and the BUNDLE reason says names are refused unless valid. (h) `config.py:78-80` comment says a pasted key is refused at load, but a token-shaped key up to 128 characters passes; no long-run test. (i) Nits: `_text_guard.py:1206` comment says `sep=`, `end=` say where and how while Z34 pins that they are scanned; `raise_after_handler` computed and unused, and the `%14` index never picks the last character `é`; `status_text` calls `str()` on an `int` subclass so a subclass `__str__` could print its own text.
*   **Rationale:** Small, real, and each is a claim the code does not keep. The fix-do-not-defer rule applies to Minors and Nits that are worth a line of work; all of these are.
*   ***AI Suggestion:*** PROPOSE FIX (all; none declined)
*   ***Justification:*** Each was read from the lines. Minors are fixed in the same push without a new review round beyond the normal result review (security path: no cap anyway).
*   ***Proposed Edit:***
    *   Location: the files listed above.
    *   Change: (a) `[A-Za-z0-9._-]{1,48}`, statuses joined outside `detail`, test updated; (b) reword the comment and reason, or show a host only if it has a dot, is `localhost` or an IP; (c) a mutant for `http_418` or remove the dead defence, and a status test for `secrets_vault.py:90`, `:94`, `:118`; (d) state the leftover `noqa: BLE001` per site (file, line, what the handler prints) in the notes, and fix any that print `{exc}`; (e) walk every `pydantic.BaseModel` subclass under `src`, or list each exempt module with its reason; (f) correct the notes wording; (g) validate or class-only the bundle case name (`shown_name`), fix the reason; (h) fix the comment, add a long-run test for the pattern; (i) fix the comment, delete the unused variable and make the index reach the last character, use `int.__repr__` in `status_text`.

## Handoff
- Accepted fixes (PROPOSE FIX): 8 issues (Issues 1-8), covering all 7 Major groups and the merged Minors and Nits.
- Contested: 0.
- Escalated: 2 (E1 `q-q8a1-hide-ids`; E2 the `ConfigName` type, carried from r11 Issue 12).
- Declined: 0.
- Remaining unaddressed issues: 0 in this report; the code is not yet changed.

## Who fixes it
One batch-14 builder (Sonnet 5.5) on a new branch from 918c0345, pushing to `wip/cloud-q8a1-b14`. Files: `guard/injection.py`, `guard/bedrock_guardrail.py`, `runtime/tick.py`, `store/postgres.py`, `registry.py`, `audit/chain.py`, `llm/retry.py`, `guard/egress.py`, `k1b/bundle.py`, `config.py`, `errors.py`, `tests/_text_guard.py`, `tests/_guard_allowances.py`, `tests/test_guard_reasons.py`, `tests/stage_mutants.py`, `tests/test_q8a1_*.py`, CHANGELOG, builder notes. Order: Issue 6 first (the guard rewrite decides what else is flagged; run the widened guard over all of `src/` and fix or give a true reason for every new site), then 1, 2, 5, 8, 3, 4, 7. Each new test is shown failing on 918c0345; each new branch of the guard and each fix gets a mutant. The independent evidence runner and two `egm:*` reviewers follow the next head.
