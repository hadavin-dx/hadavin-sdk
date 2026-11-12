Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8a-1 batch 14, branch `wip/cloud-q8a1-b14`, head `fef4ddd5` (round 14, SECURITY path: configured names and library error text must not reach a message, log or tick; no round cap).
**Inputs:** `handover/reviews/Q8a-1/q8a1b14-design-r14.md` (0 Blocker, 3 Major, 5 Minor, 3 Nit), `handover/reviews/Q8a-1/q8a1b14-codebase-r14.md` (0 Blocker, 1 Major, 8 Minor, 4 Nit), previous report `goldfish_review_report-r13.md`, independent evidence `handover/evidence/Q8a-1/fef4ddd5/RESULTS.md`.
**Mode:** automated; no person available; the recommended option is taken for every item. No severity is changed. No finding is contested: every one is checkable against the snapshot and is valid or a stated owner item.

## Evidence summary (what the runner recorded, not judged)
- Full pytest on the head: 11381 passed, 1 skipped, 28 deselected, rc 0 (own Postgres 16.15). The builder's two failures did not reproduce, so the full suite after the `test_k5_round5` edit is verified (group 10).
- `stage_mutants.py`: 281 of 281 good (Z65-Z99 all KILLED, Z89 killed, Z28, Z47, Z55 killed).
- ruff, ruff format, bandit -ll, scan_repo, gitleaks: exit 0.
- Guard over `src/`: 101 modules scanned, 590 sites, 563 allowance rows (118 + 445) all used, FOUND 0, STALE 0. UNCHECKED rows: CARD 22, REDACTED 4, STOREID 39, URL 8 (73 in total).
- Fail-before on 918c0345: b14 file 22 failed / 88 passed; guard reasons 2 failed (BUNDLE, HOST) / 43 passed; `test_stage_names.py` 1 failed. 131 new tests pass on old code (88 + 43).
- Probes: bare Bedrock-shaped ids accepted (correct); 31-character run accepted, 32 refused; empty string refused with the empty value in its text; `RuntimeError` text shows `(details withheld)`; odd sslmode with iam_auth shows `<not shown>`.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design D1`, `codebase M1`] - Severity: Major
*   **Affected Scope:** `tests/_text_guard.py` (`sites` ~765-837, `_reaches_message` ~839-883, `SAFE_CALLS` 28-34, UPPER rule ~653); `src/hadavin_sdk/cli.py:81-82`; CHANGELOG limits list.
*   **Discrepancy Description:** The guard sees only syntactic sinks. Unseen shapes: unproven text passed as a constructor keyword or assigned to an attribute (`RunResult(error_code=str(exc))`); a returned-only value; an out-parameter list filled by a helper and joined in the caller (`_put(problems, exc)` then `"; ".join(problems)`); an exception object built outside a `raise` (`err = ConfigError(exc_text); raise err`, `def _err(): return ConfigError(...)`); a Path `/` BinOp; `sys.exit(str(x))`; `raise X("fixed")` inside an `except` with no `from` (implicit `__context__`); `exc_info=True`, `.exception(...)`, `traceback.print_exc()` with a constant message (`cli.py:82` prints the chain under `HADAVIN_DEBUG=1`); a bare-name call trusted by `SAFE_CALLS` before resolution (`raise A(shown_name(name))` where `shown_name` is a parameter, or `from lib import status_text`); an UPPER_CASE name filled at run time (`_LOADED.get()`).
*   **Rationale:** a later edit in any of these shapes passes the guard and every reason check; the CHANGELOG list of what an AST scan cannot see is closed but incomplete. This is the r13 Issue 6 class closed only partly.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Both reviewers give inputs that follow from the code as read; the evidence shows the guard is clean on today's `src/` (FOUND 0), so this is about the next edit, not a live leak. Fixing at the guard (the choke point for all callers) is cheaper than relying on the sites staying clean.
*   ***Proposed Edit:***
    *   Location: `tests/_text_guard.py` (`sites`, `Analysis`), `tests/stage_mutants.py`, `tests/test_stage_names.py` planted faults, `CHANGELOG.md` batch-14/15 limits paragraph.
    *   Change: (a) an unproven value passed as keyword or argument to any call that is not a proven filter, or assigned to an attribute, is a site; (b) any `X(...)` of an Error/Refused class is a site whether or not raised, and a `raise name` or `raise f()` resolves to the construction it reaches; (c) a list passed as an argument to a function in the tree is read in the caller (an out-parameter binds the caller's collection); Path `/` BinOp joins `Add` and `Mod` as a site when the operand is unproven; (d) `raise` with no `from` inside an `except` is a site unless the raise is `call_class_only`-style or says `from None` with the class-only helper; `exc_info`, `.exception`, `print_exc`, `sys.exit(str(...))` flagged; (e) `SAFE_CALLS` names resolved through `resolve` (a parameter or import named `shown_name` is not safe); (f) an UPPER_CASE name is safe only if it is assigned once at module level from a constant or a literal collection; `_LOADED.get()` is not; (g) one planted fault per shape (new R-numbered rows in `tests/test_stage_names.py`) with a mutant each; (h) the CHANGELOG limits list is rewritten to name only what the scan truly cannot see after (a)-(g), with one sentence each. Run the widened guard over all of `src/` and fix or give a TRUE reason for every new site (the allowance table may grow; every row keeps a checked reason or an allowed exception).

### [Issue 2] [`design D2`] - Severity: Major
*   **Affected Scope:** `CHANGELOG.md:27`.
*   **Discrepancy Description:** The line still says reason `UNREAD` has 164 sites "listed and counted by `test_the_unread_sites_are_counted_and_listed`; the count may only go down". That test is gone; `tests/test_stage_names.py:3790` asserts `UNREAD` is not in `REASONS`. This was r13 Issue 7 and is not fixed.
*   **Rationale:** an operator reading line 27 believes a counter that does not exist; a claim the code does not keep is a defect (preamble: never claim more than the evidence shows).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The reviewer's quote and the test file line are checkable and the b14 paragraph (445 rows, 48 reasons, 44 checked + 4 unchecked) shows the real state.
*   ***Proposed Edit:***
    *   Location: `CHANGELOG.md:27`.
    *   Change: rewrite from the real state (every guard allowance row carries one reason from `REASONS`; `UNREAD` no longer exists; the count of rows and of unchecked rows is the one in the final batch paragraph). Add a test that reads every sentence of the CHANGELOG containing "may only go down" or a test name in backticks and fails if the named test or counter no longer exists.

### [Issue 3] [`design D3`, `design D4`, `codebase m1`, `codebase m2`] - Severity: Major
*   **Affected Scope:** `tests/test_guard_reasons.py` (`check_listed` 179-211, `check_llmreq`, `check_pkgerr`, `check_num` 1136-1145, `_numeric` 1129-1130, `_declared_numbers` 1064-1083, `check_words` 117-121, `_NUMBER_FUNCS`, `_module_never_shows` 1325), `tests/_guard_allowances.py` (LLMREQ rows for `Bearer` and URLs), `tests/stage_mutants.py`.
*   **Discrepancy Description:** The "44 real checks" are overstated: `check_listed` accepts any Call so `out.append(str(exc))` (the r13 defect) passes, and looks only at `.append`; LLMREQ rows hide URL and secret rows (`f'Bearer {self._key()}'`, `base_url... + '/chat/completions'`, the gemini URL) and `check_llmreq` looks for seven names only; GEN, SIGN, CLASSNAMES, BUILT, MIGNAMES, FIELDS, ARG have no mutant; `check_pkgerr` compares class names only (a package class inheriting a library class passes); NUM and NUMFIELD decide by attribute name (`key_version` is int at `backends/table.py:323` and str at `:254`; `step` is int at `models.py:187` and str at `models.py:236`); a loop target named `name` in `enumerate`/`range` counts as a number; `_NUMBER_FUNCS` holds `min`, `max`, `index`, `find`, `count`, `sum`.
*   **Rationale:** r11 and r13 told the builder to remove name-decided checks; a check that cannot fail on its own regression is not a check.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** All items are quoted from the snapshot with line numbers; none is contested. A check that passes the exact defect it was written for is the most serious of them.
*   ***Proposed Edit:***
    *   Location: `tests/test_guard_reasons.py`, `tests/_guard_allowances.py`, `tests/stage_mutants.py`.
    *   Change: LISTED accepts only a Constant, a JoinedStr whose values are proven (`Analysis.safe`) or a Call to a proven code-owned function, and looks at `.append`, `.extend`, `.add`, `.insert`; re-tag the `Bearer` and URL rows as URL and check them with `_module_never_shows` (a URL or key never reaches a raise, print or log in its module) instead of leaving them in LLMREQ; PKGERR resolves the class through imports and requires every base to be a package class or a builtin; NUM and NUMFIELD resolve an attribute through the annotation of the receiver's class (or require a name unique to numeric fields) and bind loop targets by position (`enumerate` item is not a number); drop `min`, `max`, `index`, `find` from `_NUMBER_FUNCS` unless the argument is proven numeric; `check_words` drops the single-letter and generic names (`a`, `p`, `i`, `name`, `cfg`, `config`, `reason`) or proves them by type; one mutant per checked reason lacking one (GEN, SIGN, CLASSNAMES, BUILT, MIGNAMES, FIELDS, ARG), killed by the reason check with a message that names it, plus planted-fault rows for the `key_version`/`step` collisions and for `out.append(str(exc))` under LISTED.

### [Issue 4] [`codebase m4`, `design D5`] - Severity: Minor
*   **Affected Scope:** `tests/test_guard_reasons.py:24-31` (UNCHECKED comment), `tests/_guard_allowances.py:631` (tick row), `src/hadavin_sdk/store/postgres.py:247`, `:269` (`NotFound(value)`), `src/hadavin_sdk/runtime/tick.py:352-365`.
*   **Discrepancy Description:** STOREID and URL name "a data-flow check" as the next step, which is not an allowed exception (impossible now, needs the owner, needs a third party); CARD needs the demo repositories' portal fixture and is not stated as such; STOREID is false for `NotFound(value)` (the value is a caller-passed id such as an argv run id or an id parsed from a Slack payload; `NotFound` is a `KeyError` subclass and `_own_error` shows its text in the tick); the tick row `f'{type(exc).__name__}: {_message(exc)}'` is labelled REDACTED although its real rule is `_own_error` and needs no owner decision (r13 Issue 2 asked to fix this label). Evidence: UNCHECKED stays at 73 rows (CARD 22, REDACTED 4, STOREID 39, URL 8).
*   **Rationale:** preamble rule 5: a gap is fixed now or classed as impossible-now / owner / third party with the next step; "a data-flow check" is neither.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** STOREID and URL are buildable now with `_module_never_shows` (the reviewer says so and the helper exists), so the deferral does not hold. CARD is a true third-party/other-repository dependency and REDACTED is a true owner item (q-q8a1-hide-ids, already ledgered).
*   ***Proposed Edit:***
    *   Location: `tests/test_guard_reasons.py` (STOREID, URL checks, UNCHECKED comment), `tests/_guard_allowances.py` (NotFound rows, tick row 631).
    *   Change: build STOREID and URL checks by data flow (the id or URL is generated in the same module, never read from a caller or an environment value, and never a parameter); relabel the `NotFound` rows that take a caller-passed id (they are not STOREID: either show only the class name there, or add a named reason with a check that the id passed is a store-generated run id); relabel the tick row with a PKGERR-like reason and a check that `_message` returns a constant unless `_own_error` holds; CARD stays unchecked with the exception written: "needs the card portal fixture that lives in the demo repositories (other repository); next step: copy the fixture into `tests/` when the demo repository publishes it, due when Q8a-1 closes"; REDACTED stays OWNER-ONLY. The UNCHECKED set may only shrink; pin it.

### [Issue 5] [`codebase m3`, `design D8`, `design D6`] - Severity: Minor
*   **Affected Scope:** `src/hadavin_sdk/config.py:65-95` (`Route.model_id`, `_no_key_shaped_run`), `src/hadavin_sdk/cli.py`, CHANGELOG batch-14 item 1, `tests/test_q8a1_b14_fixes.py:301-341`.
*   **Discrepancy Description:** The rule refuses immutable pins (`model@sha256:<64 hex>`, `org/model@<40-hex commit>`) with no hint that the pin case is the reason; the upgrade hint "Load your config once with the new version before you upgrade a running system" names no command (the CLI has gate, limits, tick, migrate, audit, replay, score; no validate-only command); the CHANGELOG says a key "has that shape" (probabilistic: a 95-character key has a small chance of no 32-run and passes); the fuzz alphabet cannot make 32 alphanumerics so its oracle mirrors the pattern (the deterministic cases carry the test).
*   **Rationale:** a breaking change must tell an operator exactly how to check a config before upgrading (r13 Issue 7); an over-refusal without a hint is a surprise at upgrade time.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The probe confirms the behaviour (32 refused, 31 accepted, bare Bedrock ids accepted). Over-refusal of immutable pins is real; the remedy is a hint or a narrow allowance, not removing the rule.
*   ***Proposed Edit:***
    *   Location: `config.py` validator, `cli.py`, CHANGELOG, `tests/test_q8a1_b14_fixes.py`.
    *   Change: add a side-effect-free `check-config` command (loads the registry the way `tick` does, prints only the field and rule on refusal, exit 0/1, never connects or writes); allow an `@sha256:<64 hex>` or `@<40 hex>` pin suffix exactly (a 32+ run is accepted only as the whole suffix after `@`, nothing else) with a test and mutant, or, if the builder shows this widens the leak path, keep the refusal and make its sentence say "a model id has no run of 32 or more letters or digits; for an immutable pin set the alias in `model_alias` instead" (the builder picks one, states why); the CHANGELOG names the command, says "usually" for key shapes, and says the fuzz oracle mirrors the pattern; the empty-string refusal text must not contain the value (evidence says it contains the empty string, which is fine, but pin it).

### [Issue 6] [`codebase m5`, `design D6`] - Severity: Minor
*   **Affected Scope:** `src/hadavin_sdk/actions/executor.py:147-148`, `src/hadavin_sdk/tools.py:557`, `:653`, `src/hadavin_sdk/llm/retry.py:31` (`_DETAIL`), `:39-44` (`status`), `:88` (`describe`).
*   **Discrepancy Description:** `int(status)` replaced `status_text` at four places (the `errors.py:125` docstring says `int(x)` raises a `ValueError` quoting the text; in tools `int(code)` on a non-number `HTTPError.code` raises from the handler instead of `ToolRefused`); `describe` at `retry.py:88` still prints `str(status(exc) or "")` and `status()` returns an `int` subclass as is, so a subclass with its own `__str__` prints its own text (the class `status_text` was fixed for); the executor change has no test or mutant (builder admits); `_DETAIL` (`[A-Za-z0-9._-]{1,48}`) lets a 40-48 character key-shaped token through.
*   **Rationale:** one shared place for a status text (the CHANGELOG says so); a sibling site that still prints the raw value is the same class.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Hardening, not a live leak (the executor comparison raises `TypeError` first); fixing at all four sites plus a mutant is cheap and removes the sibling.
*   ***Proposed Edit:***
    *   Location: the five source lines above.
    *   Change: use `status_text` at executor, both tools sites and `describe`; `_DETAIL` becomes `{1,32}` plus the 32-run exclusion used by `model_id`; one fix test and one mutant per site (the executor change gets a mutant killed by a test whose message names it); fail-before on `fef4ddd5` shown for each.

### [Issue 7] [`codebase m6`] - Severity: Minor
*   **Affected Scope:** `CHANGELOG.md:9` items 4 and 5 (batch-14 entry).
*   **Discrepancy Description:** Items 4 and 5 present batch-13 code as batch-14 changes: `errors.Failed` and the shared places existed in batch 13 (the `errors.py` docstring says "Round 13"); the gate line via `shown_name` is `cli.py:159`, not in the batch delta. Only the bundle folder, sslmode and `status_text` are new.
*   **Rationale:** a CHANGELOG entry must say what changed in this batch.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The reviewer's check (DELTA-FILES, docstring) is checkable; counts (445 rows, 44 + 4 = 48, 54 BLE001 sites) were verified.
*   ***Proposed Edit:***
    *   Location: `CHANGELOG.md` batch-14 entry (and the batch-15 entry when written).
    *   Change: split "new in this batch" from "kept from batch 13"; remove `errors.Failed` and the gate line from the new list.

### [Issue 8] [`codebase m8`, `design D7`] - Severity: Minor
*   **Affected Scope:** `tests/stage_mutants.py` (killers of Z80, Z81, Z87, Z90, Z91, Z94, Z96-Z98; `_own_error` mutants), `tests/test_q8a1_b14_fixes.py:226-274` (strict-model walk).
*   **Discrepancy Description:** Killers named by generic words (`assert`, `AssertionError`) match any pytest failure; Z80 and Z81 are killed by "not found" and "integer check" (row staleness and spelling) rather than the TIME and SEQ claims; `_own_error`'s `not isinstance(exc, OSError)` clause and its all-bases clause have no mutant (Z92 replaces the whole function); the strict-model walk takes only models with `extra == "forbid"` and silently skips the others.
*   **Rationale:** a mutant killed for an unrelated reason shows nothing; a silent skip hides a model that ignores unknown keys.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The reviewers cite lines and the evidence shows all 281 mutants killed, so the weakness is the kill message, not a surviving mutant.
*   ***Proposed Edit:***
    *   Location: `tests/stage_mutants.py`, `tests/test_q8a1_b14_fixes.py`.
    *   Change: each of the listed killers names a message only the intended assertion prints (the claim being pinned plus the planted value); two new mutants (drop the OSError exclusion; drop one base-class condition) each killed by a test whose message names it; the strict-model walk lists every model it skipped and asserts the skipped list equals a pinned, reasoned list.

### [Issue 9] [`design nits`, `codebase nits`] - Severity: Nit
*   **Affected Scope:** `tests/test_guard_reasons.py:1292` (`__str__` scan), `tests/test_k5_round7.py:41-50`, `llm`/egress `_shown_host`, `check_keyver`, `check_label`/`check_bundle`/`check_seq` (`:415`, `:1393`), `tests/test_q8a1_b13_fixes.py:63-70`, `runtime/tick.py` `_own_error`.
*   **Discrepancy Description:** The `__str__` scan covers only `*Error` and `*Unavailable` classes (`ToolRefused`, `StaleState`, `NotFound`, `ProviderExhausted`, `EgressRefused` are not covered); the detector half of the round-7 test passes vacuously now that the log prints no text; `_shown_host` prints `?` for a dotless in-cluster host such as `vault` (disclosed, no operator hint); `check_keyver` looks for the name `status` only; `check_label`, `check_bundle`, `check_seq` compare text positions or `lineno` rather than control flow; `test_q8a1_b13_fixes.py:63-70` no longer fuzzes the new `ddd code` prefix; `_own_error` withholds every builtin-class error, so the sentence of a `RuntimeError` or `ValueError` raised by the package's own steps (`tick.py:123`) is lost in `last_error`.
*   **Rationale:** minor weakness or documentation gaps; none is a leak.
*   ***AI Suggestion:*** DECLINE (record, fix when touched)
*   ***Justification:*** Nits; the batch-15 builder fixes any that sit in a file it already edits (the `__str__` scan classes list, the vacuous round-7 half, the `ddd code` fuzz, one line in the upgrade note about `last_error`, the `?` hint in the CHANGELOG) and lists the rest in the notes with a reason; no new review round for them.
*   ***Proposed Edit:*** none required.

### [Issue 10] [`evidence`] - closed by evidence
*   **Affected Scope:** the builder's open items: full pytest after the `test_k5_round5` edit, gitleaks, mutant gate Z89, "88 + 516 pass on old code".
*   **Discrepancy Description:** The builder reported 2 full-suite failures, one test edit after the full run, gitleaks not run, and Z89 "snippet not found".
*   ***AI Suggestion:*** none (closed; recorded, not fixed)
*   ***Justification:*** The independent runner recorded full pytest 11381 passed, 1 skipped, 28 deselected, rc 0 on the head (both builder failures did not reproduce, so the test edit is covered), `stage_mutants` 281 of 281 with Z89 killed, gitleaks and ruff and bandit and `scan_repo` exit 0, guard FOUND 0 STALE 0. Still open from this group: 131 new tests pass on old code (88 + 43) and the builder's notes give one sentence for all; one line per test id (a killing mutant or a true reason) is required, listed under the batch-15 task below.
*   ***Proposed Edit:*** none to code. The ledger row for this group is FIXED-VERIFIED for the items above; the per-test-id reasons are carried by Issue 3 and the batch-15 notes (below).

## Escalated (owner items, not fixed here)
- **E1 `q-q8a1-hide-ids`** (what may be shown: `error_reason` at `agent_loop.py:312` and `tools.py:1020-1045` still sends up to 160 characters of non-`OSError` library text, such as a `botocore` `ClientError`, to the model and the stored evidence; the REDACTED guard row). Already in the question file and the ledger (`Q8a1b13-r13-owner`). Both reviewers say it is inconsistent with the tick rule, so the owner should know. Safe default stays: unchanged and disclosed.
- **E2 `ConfigName` type** (same ledger row). Unchanged.

## Handoff
- Findings in: design 3 Major + 5 Minor + 3 Nit; codebase 1 Major + 8 Minor + 4 Nit; merged into 10 groups.
- PROPOSE FIX: 8 groups (Major 1-3; Minor 4-8). DECLINE (Nits, fix when touched): 1 group (9). CLOSED BY EVIDENCE: 1 group (10). CONTEST: 0. ESCALATE (owner, already ledgered): 2 (E1, E2).
- Applied edits: none to code by this skill. The batch-15 builder applies them.
- Remaining unaddressed: groups 1-8 (OPEN) until batch 15 is built, evidenced and reviewed. No Blocker found; no live leak in `src/` at this head.
- **Who fixes it:** one batch-15 builder (general-purpose, Sonnet) on a new branch `core/q8a1-b15` from `fef4ddd5`, pushing to `wip/cloud-q8a1-b15`. Files: `tests/_text_guard.py`, `tests/test_guard_reasons.py`, `tests/_guard_allowances.py`, `tests/test_q8a1_b14_fixes.py` (or a `tests/test_q8a1_b15_fixes.py`), `tests/stage_mutants.py`, `tests/test_stage_names.py` (planted faults), `src/hadavin_sdk/{config.py,cli.py,actions/executor.py,tools.py,llm/retry.py,store/postgres.py}` as needed, `CHANGELOG.md`, builder notes. Order: group 1 first (the guard decides what else is flagged: run the widened guard over all of `src/` and fix or give a TRUE reason for every new site), then 3, 4, 5, 6, 8, then 2 and 7 (CHANGELOG), then the nits that sit in edited files. Method per bug: name the class, fix at the shared choke point, grep for siblings, add property or fuzz tests, show each new test failing on `fef4ddd5`, one mutant per new fix and guard branch killed by a test whose message names it; one line per test id for every test that passes on old code (a killing mutant or a true reason; the 131 from b14 included). Gates once on the final head: ruff, format, bandit -ll, scan_repo, `stage_mutants`, one full pytest on the builder's own Postgres 16. Security path: no round cap.
