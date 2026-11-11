Status: resolved

# Goldfish Annotated Review Report (Q8b, round 4)

**Target:** branch `core/q8b-partial-mask-and-card-redaction`, head `4091f8b1`, snapshot `/home/user/build/snap/q8b4-4091f8b1`. Redaction path: no round cap. No person was available: recommended option for every item, every real finding is PROPOSE FIX. Reviews: `/home/user/build/reports/q8b4-design-r4.md` (1 Blocker, 1 Major, 3 Nit) and `/home/user/build/reports/q8b4-codebase-r4.md` (0 Blocker, 1 Major, 4 Nit); both read only, nothing run. Independent evidence: `handover/evidence/Q8b/4091f8b1/RESULTS.md`, `addon-table.md`, `main-masks-head-readable.txt` (ruff, format, bandit, scan_repo, gitleaks exit 0; `stage_mutants` 37/37, `q8b_mutants` 63/63, `mutation_runner_mutants` 62/62; full pytest 10739 passed, 1 skipped, 29 deselected, 16 xfailed, exit 0; fail-before: on main source 168 failed, 117 passed, on `13ea6b75` source 17 failed, 267 passed; timing flake fails 3 of 3 on head and on main, not in the diff). Round-3 Issues 1-8 were verified fixed by reading (both reviewers).

## What the evidence run changed

- D1 is confirmed by running it, not only by reading. Keys that main masks and the head does not (quoted styles; card, tool-result and log paths; 30 probes): `passcode`, `passkey`, `pass_code`, `session_key`, `sessionkey`, and the `_value` forms `pass_value`, `PASS_value`, `Pass_value`, `session_value`, `SESSION_value`, `Session_value`. This is a regression against main.
- Leaks the head shares with main (so not regressions, still defects under the redaction rule, to be fixed in the same piece of work): the 12 `pass`/`auth`/`session`/`bearer` words with a `_value` suffix on tool and log paths; on the card path also the hyphen spellings `key-data`, `cert-data`, `certificate-data`; bare `key=a;b` leaves the part after `;` readable for all 806 spellings. The runner did not judge whether the ticket intends the `;` stop; the builder must read the ticket's rule 1f and either keep it by design and state it in the CHANGELOG in plain words, or fix it.
- Totals (806 spellings x 4 paths x 3 value styles): readable-secret probes 2,550 on the head against 7,167 on main; 4,674 probes where the head masks and main does not. Benign masked keys identical to main (`password_policy_enabled`, `token_count`).
- Not run by anyone: the Vault tests, CodeQL, SonarCloud, CodeRabbit, semgrep/trivy/pip-audit/zizmor. `tests/migration_numbers_mutants.py` is not a CI step and failed without a Postgres environment (cause unchecked; the builder checks it once).

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` D1, `evidence` add-on table] - Severity: Blocker
*   **Affected Scope:** `src/hadavin_sdk/guard/redact.py:700`, `:707` (both quoted-value rules now start with `(?:KEY_WORDS)`), `KEY_ALTERNATIVES` `:152-159` (`pass(?=...)` and `session(?=...)` match only when `=` or `:` follows at once); main `redact.py:580`, `:587` (bare `pass`/`session` prefix plus up to 20 key characters); `tests/q8b_key_corpus.py` (`CREDENTIAL`, no `passcode`, `passkey`, `session_key`).
*   **Discrepancy Description:** Regression against main. `session_key="abc def"` and `passcode="hunter 2"` were masked whole on main and are shown as written at the head on the card, tool-result and log paths; the record-walk path still masks `session_key`, so the paths disagree again. Reproduced by the evidence runner (30 probes). No test or mutant restores a bare prefix.
*   ***AI Suggestion:*** PROPOSE FIX (decided by the lead, reversible: yes).
*   ***Justification:*** A readable credential that main hid is the worst class on this path. Round 3 Issue 2 made "one key list" the fix; the edit that built the quoted rules from `KEY_WORDS` dropped main's two prefixes, so the single list is not a superset of main.
*   ***Proposed Edit:*** Make the single key list a strict superset of every key main masks: add main's bare `pass` and `session` prefixes (with the 20-character key tail) to the quoted rules, written once in the one shared list or one shared quoted-rule builder, not per path. Fix in the same change the evidence facts that main also leaks: the `_value` suffix forms of `pass`, `auth`, `session`, `bearer`, and the hyphen spellings `key-data`, `cert-data`, `certificate-data` on the card path. Add all of them (11 keys above plus the suffix and hyphen forms) to `CREDENTIAL` in both quote styles and the bare style, on card, tool-result, log and walk paths. Mutant: drop the two prefixes (must be killed). Add a test that every key main masks is still masked (take main's regexes as the oracle on the corpus: any key main masks and the head does not is a failure). Before editing, reproduce D1 by running the inputs and keep the output.

### [Issue 2] [`design` D2] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/k1b/redaction.py` (`GLUED_PREFIXES`, `PREFIXED_ENDINGS`, `sensitive`), `LIMITS` bullet, CHANGELOG copy, `tests/test_q8b_batch3.py:171-190`.
*   **Discrepancy Description:** The round-3 fix keeps an allow-list of 28 words allowed before `pass`, `auth` and `session`. `{"newpass": ...}`, `oldpass`, `confirmpass`, `defaultpass`, `postgresauth`, `jenkinssession` stay readable in a case bundle while `newpass=hunter2` as text is masked. The benign English words ending in these are a small closed set; the test pins "unlisted word in front stays readable" as intended.
*   ***AI Suggestion:*** PROPOSE FIX (decided by the lead, reversible: yes, confidence medium).
*   ***Justification:*** An allow-list fails open (readable secret); a deny-list of benign endings fails closed (a harmless value is hidden). Redaction and least-privilege rules prefer the closed direction. The benign corpus was written by the builder to fit the list, so "measured" cannot carry the claim.
*   ***Proposed Edit:*** Invert the walk rule: a record key whose last word (after stripping glued prefixes and splitting on separators and case changes) is `pass`, `auth` or `session` is a credential unless the whole key is in a short benign list: `bypass`, `compass`, `encompass`, `overpass`, `underpass`, `surpass`, `trespass`, `impass`, `oauth`, `obsession`, `possession`, `supersession`, and any the builder's benign corpus shows. The over-mask set (benign keys that become masked) is pinned by the corpus test and listed in LIMITS in plain words with an example. Tests: `newpass`, `oldpass`, `confirmpass`, `defaultpass`, `postgresauth`, `jenkinssession` masked in a record; the benign list stays readable; mutant that restores the allow-list. Reproduce D2 by running the inputs first.

### [Issue 3] [`codebase` C1] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/approvals/channel.py:43`, `:71-80` (`_secret_originals`, `runmap.SECRET_KINDS`), `tests/q8b_mutants.py` (M22, M53), `tests/test_q8b_batch3.py:189-209`, `:294-297`.
*   **Discrepancy Description:** The card's second-view test was widened from five assignment kinds to all 13 kinds (IBAN, card number, private key, JWT, ...). Nothing restores or detects the old subset: M22 and M53 target other lines, `M22_TEXTS` are token/secret assignments, test_i8 only checks the old name is gone and the two sets are equal. Narrowing back to five kinds passes every test; a card number or IBAN split by tags would then be returned readable.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The widening is the fix for a real class; an unguarded fix returns without anyone noticing.
*   ***Proposed Edit:*** Add a mutant that restricts the set to the five assignment kinds, and a test that kills it: a card number and an IBAN split by tags (for example `4111<i></i>1111...`, made-up numbers) through `clean`, asserting the number is not readable. Confirm M22's two texts really fail under M22 by running them (the reviewer could not).

### [Issue 4] [`design` D3, `design` D4, `codebase` C2, C3] - Severity: Nit (PROPOSE FIX, cheap)
*   **Affected Scope:** `LIMITS` bullet in `k1b/redaction.py` and its CHANGELOG copy; CHANGELOG bullet "A credential value with spaces..." (delta lines 9-10); CHANGELOG `:9` ("a quote, `;`, `,` or `&`"), `:11`; `redact.py:149` (`_VALUE_CHAR`), `:154-159`.
*   **Discrepancy Description:** Shipped text cites the internal decision D-032, which a user of the SDK cannot read; the CHANGELOG calls `<A>` a placeholder (the shape is `<[A-Z]+_\d+>`) and repeats the "Cost: prose right after an unquoted credential value..." sentence; the comma wording is wider than the code (a comma ends the value only when a new `key=` follows; `password=ab,cd ef` is masked whole); the redactor entry does not name the new keys `signing_key`, `encryption_key`, `bearer:`, nor the new over-masking (`Bearer: John Smith paid` is masked to the end of the line).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Remove D-032 from shipped text; list five example keys instead (D-011 says the LIMITS text is exact: the lead decides here that removing the pointer is allowed, record it in `DECISIONS.md`). Say "a value in angle brackets"; drop the duplicate sentence; reword the comma rule to the code's; add one sentence naming the redactor-wide key additions and the `bearer` cost; add a pinning row for the comma case. If the ticket's rule 1f makes `;` a stop, say so plainly in the CHANGELOG ("the part after a `;` is not masked, by design, because ..."); if not, fix it.

### [Issue 5] [`design` D5, `codebase` C5] - Severity: Nit (PROPOSE FIX, cheap)
*   **Affected Scope:** `tests/test_q8b_batch3.py:239`, `:1251` (disjunct `... is None or "EMAIL" not in out`), `:136` (`code.count("KEY_WORDS") >= 6`), `tests/test_q8b_batch2.py:961-983` (scan sees only lines holding both "password" and "passwd"; `code.count("signing[_") == 1`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Delete the vacuous `or`; replace the string counts with behaviour (every spelling of the one list is masked; a second hand-written key list fails the drift test, including a list written one entry per line); make the drift scan not depend on two words sharing a line.

### [Issue 6] [`codebase` C4] - Severity: Nit (PROPOSE FIX; same on main, not a regression)
*   **Affected Scope:** `redact.py:40-43`, `:666` (`_CRED_FLAG`), `tests/test_q8b_batch2.py` (`allowed` tuple, `"api-?key"` entry).
*   **Discrepancy Description:** A second hand key list excused from the drift test by a substring; hyphens only, so `--client_secret hunter22` and `--api_key hunter22` (space form) are not matched; the `=` form is.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Round 3 Issue 2 asked for a grep for any other key list; a readable value after an underscore flag is the same class. Fix at the one list: build `_CRED_FLAG` from `KEY_ALTERNATIVES`, allow `[_-]`, and drop the excuse in the drift test.
*   ***Proposed Edit:*** Derive the flag rule from the shared list with `[_-]`; tests for `--client_secret`, `--api_key`, `--api-key`; remove the `api-?key` allowance.

### [Issue 7] [`codebase` C5] - Severity: Nit (PROPOSE FIX)
*   **Affected Scope:** `k1b/redaction.py:152` (`super` + `session` makes `supersession` a masked key), `tools/mutation_runner.py` `_run_mutants` (both `extra_files` copy loops), `tests/test_i5_*`, `EXPECTED_MUTANTS = 62`.
*   **Discrepancy Description:** `supersession` is not in the benign corpus (covered by Issue 2's benign list); the new runner parameter has no mutant in the runner's own suite and `test_i5` passes if either copy loop works.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Add `supersession` to the benign corpus and `WALK_COST`; add two runner mutants (skip the copy in the baseline tree; skip it in the per-mutant tree), each killed by a test that fails when only that loop is gone; move `EXPECTED_MUTANTS` and the manifest hash together and re-run the runner mutants once. Note: the runner is shared with PR89; the lead sequences the merge, the builder states the manifest hash conflict risk.

### Items recorded, no change
*   Round-3 Issue 9 (fail-before controls) was not visible in the delta: the evidence list `fail-before-main-q8b-tests-that-PASS-on-main.txt` (48 ids) is the record; the builder adds one line per passing-on-main test (control for an earlier class, or the mutant that proves the guard live).
*   PR77 conflict risk unchanged (trial merge conflicts in `CHANGELOG.md` and two hunks in `guard/redact.py` `_mask`); merge order stays with the owner or lead.
*   The corpus is made up by the builder; the `WALK_COST` numbers are measured on it only and must be written that way.

## Handoff counts
Accepted (PROPOSE FIX): 7 (Issues 1-7). Contested: 0. Escalated: 0. Declined: 0. Round 5 review needed after the fix batch (redaction path, no round cap). The fix builder: reproduces D1 and D2 first, runs the whole suite once at the final head and shows the line, runs `q8b_mutants`, `stage_mutants` and `mutation_runner_mutants`, and includes a table of readable probes (head before, head after, main).
