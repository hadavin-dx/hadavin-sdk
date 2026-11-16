Status: resolved

# Goldfish Annotated Review Report (PR89, round 23)

**Target:** `tools/mutation_runner.py` and tests at head `4cc427b5`, snapshot `/home/user/build/snap/pr89r23-4cc427b5/files`. Security path (secrets in a child process's output), no round cap. No person was available: recommended option for every item. Reviews: `/home/user/build/reports/pr89-codebase.md` (3 Majors, 4 Nits, no Blocker), `pr89-design.md` (no Blocker, no Major, 1 Nit), evidence `pr89-EV.md`. Decision D-026 item 2 applies: the class-name leak is fixed, not documented.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase`] C1 - Severity: Major
*   **Affected Scope:** `tools/mutation_runner.py:1208` (`os.fchmod`), `tests/test_mutation_runner_keywords.py:5790-5862`, docstring line 46, CHANGELOG:26.
*   **Discrepancy Description:** The mypy win32 count "13" is a hand count; the pin test never runs mypy, and `os.fchmod` (and perhaps `os.waitid` at 1470) may add errors on win32 under Python 3.12.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A number stated in three places that nobody measured; the reviewer could not verify it, and neither could the test.
*   ***Proposed Edit:*** Run `mypy --platform win32 tools/mutation_runner.py` on 3.12 (uv, own venv; record the command and output in the evidence folder), take the measured count and error lines, move `os.fchmod` (and `os.waitid` if reported) into the POSIX-only names or use `getattr`, and correct the docstring, CHANGELOG and test. If possible make the pin test run mypy itself (skipped with a stated reason where mypy is absent) so a miscount is noticed.

### [Issue 2] [`codebase`] C2 - Severity: Major
*   **Affected Scope:** `tests/mutation_runner_mutants.py:37`, `:48-52`; CHANGELOG:26; killers `tests/test_mutation_runner_keywords.py:5157-5503`.
*   **Discrepancy Description:** The header says every other killer runs on both systems; the round-23 killers are `@posix_only`, so 21 mutants (`mutation_runner_mutants.py:560-575`, `578-581`, `582`) survive on Windows without being named.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Derive the POSIX-only list instead of typing it: a test collects every killer carrying `posix_only` and compares the mutant names with the header list. Then name the 21 in the header and qualify line 37 and CHANGELOG:26.

### [Issue 3] [`codebase`] C3 - Severity: Major
*   **Affected Scope:** `tests/mutation_runner_mutants.py:48-52`; `tools/mutation_runner.py:1836-1840`, `:1906-1911`; order test at `tests/test_mutation_runner_keywords.py:4496`.
*   **Discrepancy Description:** The order mutants (secret-count step against the address step; junction checks against `mkdtemp`) were declined on the ground that one replacement cannot move a block; multi-line mutants exist (561, 562).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Add the two swap mutants (the address loop above `_secret_values`; `_refuse_junctions` below `mkdtemp`), killer = the order test; correct the header text.

### [Issue 4] [`codebase`] C4 - Severity: Minor to Major (a creation site that bypasses the helpers)
*   **Affected Scope:** codebase review C4 (read the review text; the reviewer names a creation site outside the private-folder helpers).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Route that site through the same helper (choke point), grep for any other creation site, test and mutant.

### [Issue 5] [`design`] N1 and evidence - Severity: Nit by the reviewer; FIXED by decision D-026
*   **Affected Scope:** `tools/mutation_runner.py:1044-1045` (`_shown_class`), `:1054-1062` (`_shown_line`); docstring lines 186 and 907. Evidence: 2 of 498 cases still shown (password equals `TimeoutError`, child raises that class).
*   **Discrepancy Description:** `_shown_class` returns a built-in class name unchanged, so a password equal to a built-in class name reaches `first_lines`.
*   ***AI Suggestion:*** PROPOSE FIX (a readable secret on a security path is never declined)
*   ***Proposed Edit:*** Class names pass the same value-masking as every other shown text (check against the secret values before showing); the 498-case probe must read 0 of 498 shown. Test: password equal to each built-in class name in the table.

### [Issue 6] [`codebase`] remaining Nits (4 in the review: see `pr89-codebase.md`)
*   ***AI Suggestion:*** PROPOSE FIX (one push, no new review for them under the round rule, but the next round reads them)
*   ***Proposed Edit:*** Builder reads each Nit at its lines, fixes it, or writes the line-level reason it is not a defect.

### [Issue 7] [`evidence`] full-suite failure from the runner's own setup
*   **Discrepancy Description:** The recorded full run has 1 failure; the evidence runner started Postgres without PGHOST/PGPORT in the server's environment (that file passed alone, 253 tests).
*   ***AI Suggestion:*** PROPOSE FIX (process)
*   ***Proposed Edit:*** The next evidence run starts Postgres with PGHOST and PGPORT set in the server's environment and records a full run with 0 failures at the final head.

## Handoff counts
Accepted (PROPOSE FIX): 7. Contested: 0. Escalated: 0. Declined: 0. Remaining unaddressed: 0 until the fix batch. Round 24 review needed (security path, no round cap); evidence includes mypy win32 output and the 498-case probe.
