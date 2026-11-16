Status: resolved

# Goldfish Annotated Review Report (Q8b batch 8, round 9)

**Target:** branch `wip/cloud-q8b-b8`, head `3eaae7c1b754d4c0e4f624d0d9fd1e6d0dde6a81` (delta `b7d7cd18..3eaae7c1`). REDACTION path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `q8bb8-design-r9.md` (0 Blocker, 2 Major, 4 Minor, 2 Nit) and `q8bb8-codebase-r9.md` (0 Blocker, 2 Major, 2 Minor, 1 Nit). Previous round: `goldfish_review_report-r8.md`. Independent evidence: `handover/evidence/Q8b/3eaae7c1/RESULTS.md` and `probe-table.md`.

**Evidence status (first).** ruff, format, bandit, `scan_repo`, gitleaks exit 0; `q8b_mutants` 155 of 155; `stage_mutants` 37 of 37; `mutation_runner_mutants` as user nobody 64 of 64; full pytest exit 0 (10844 passed, 1 skipped, 16 xfailed). Not clean or different from the builder: (a) the CI install `uv sync --locked --no-build` failed in the evidence environment (installed without `--no-build`); (b) the timing test is the known flake (head pass, fail, fail; main fail x3; fix on `core/fix-timing-harness-flake`, not touched); (c) the builder's "120 readable cells" was not reproduced: the runner's own probe has 118 cells, 28 readable on head, and 2 cells (`possession_id=V`, `obsession_id=V`) readable on head and masked on main; (d) fail-before: 18 of 72 tests in the four delta files fail on b7d7cd18, 54 pass on old code (Issue 11 of r8 and Issue 11 here); (e) cost on a 200 kB hostile text: median head/main ratio 1.50 to 3.48, head up to 1.25 s, no error; (f) the ticket's A1-A5 and X1-X9 rows, Python 3.12, Windows, CodeQL, SonarCloud were not run. The builder also edited `tests/test_q8b_batch6.py` outside its allowed list; the reviewer judged it narrow and acceptable (ledger row).

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase-details` C1] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/guard/redact.py:731` (Basic rule `[ \t]+`, main `\s+`) and `:829` (Authorization rule `(?:[a-z]+[ \t]+)?`); `test_b8_10_a_line_break_ends_a_digest_header_and_a_scheme_word`; mutant M130; CHANGELOG item 10.
*   **Discrepancy Description:** A wrapped header `Authorization: Basic<LF><b64>`, `Token<LF><token>`, `ApiKey<LF><token>` leaks its credential. Masked on main, readable now. Round 8 Issue 10 asked for the line-break stop in the Digest rule only; the builder changed the two main-behaviour rules too. The Bearer rule kept `\s+`, so the shapes are inconsistent. Also `\x0b`, `\x0c`, `\x1c-\x1f`, `\x85`, U+2028/9 are no longer a separator. CHANGELOG item 10 names no cost. Reviewer read only; the evidence runner did not probe this shape.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A regression of a ticket-promised secret (Authorization header values) against main; no true reason to accept.
*   ***Proposed Edit:*** Keep the line break out of the Digest rule only. For Basic, Token, ApiKey allow one `\r?\n` followed by space or tab (obsolete line fold), or a line break followed by a 16+ character base64 token. Add rows that must be masked (Basic, Token, ApiKey, wrapped; also the other separators); run before/after on main and save the output; add a mutant on the generic Authorization rule `[a-z]+[ \t]+` and on the Basic rule (M27 has identical old/new text: make it differ). State in CHANGELOG exactly which shapes changed.

### [Issue 2] [`design` D9-1] - Severity: Major
*   **Affected Scope:** CHANGELOG batch 8 item 11 ("nine pinned cases instead of seven"); LIMITS in `k1b/redaction.py:74` ("`--pass2 a b`, `authorization=a b`: pinned in tests/test_q8b_batch8.py").
*   **Discrepancy Description:** The claimed pins do not exist. Batch 8 test file has no `--pass2` or `authorization=a b`; only `test_b7_4` (seven flags). Evidence confirms a second word stays readable after `--pass2`, `--password`, `--newpass`, `authorization=` on head and on both older trees.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A false claim in shipped text; the pin is cheap.
*   ***Proposed Edit:*** Add `--pass2` to the tuple at `test_b7_4:374-382` and a row for `authorization=a b` with the exact outcome (readable second word, a stated cost); keep LIMITS wording only if it matches the rows; otherwise delete the claim. Correct "nine" to the real count.

### [Issue 3] [`design` D9-2 + `codebase-details` C2] - Severity: Major
*   **Affected Scope:** `tests/test_q8b_batch8_lines.py:17-91, :196-231`; `tests/q8b_mutants.py` M133-M157; CHANGELOG item 13.
*   **Discrepancy Description:** Round 8 Issue 13 (every one of the 74 control ids shown to fail or given a checkable reason) is delivered in form only. 27 of 74 lines name a mutant, 47 say `pytest <id>` and carry boilerplate reasons; lines 24-26, 28, 30, 44 have M133-M139 but say pytest, so two hand-kept lists disagree; `test_the_check_itself_fails_when_a_line_is_missing` recomputes a set difference and cannot fail; `assert planted >= 27` pins the weakness as a floor; M145, M150, M151 missing from the numbering; weak expect fragments (M133 `channel.py:`, M138 `approvals/channel.py:`, M136 `assert False`, M142 `(1, `). CHANGELOG item 13 reads as if each test was shown to fail.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The reviewer's findings are right and reproduced by reading; the owner standard is that "done" needs evidence.
*   ***Proposed Edit:*** Generate the control-to-mutant column from the mutant table (`pinned=`), so one source; one planted fault per remaining control, or an explicit "no fault possible because X" that a reviewer can check; pin each `expect` to the test's own message; a test that runs `_parsed()` on a LINES text with a line removed and must fail; drop or derive the floor; explain M145/M150/M151 or fill them; reword CHANGELOG item 13 to what was shown.

### [Issue 4] [`design` D9-3 + `codebase-details` C3 + evidence] - Severity: Minor
*   **Affected Scope:** `guard/redact.py:115-118` (`_COOKIE_KEY_BODY`); `k1b/redaction.py` (`_key_words`, `_TRAILING_DIGITS`); `redact.py:208` lookahead `[0-9]*` vs consumer `[\w.\-]{0,20}` (:974, :345, :360, :466).
*   **Discrepancy Description:** (a) `cookie2=<v>` / `Cookie2: <v>` stay readable in text but the record walk strips trailing digits (drift class of r7 Issue 1). (b) bare word + more than 20 digits + `=` leaves the value readable in text and masked as a record key; evidence: 40 and 41 digits after `pass` or `password` readable on head and both older trees; the test skips n > 20 (`test_b8_8:377-392`); LIMITS names only `pass`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same class twice (text path and record path disagree); fix at the shared word list.
*   ***Proposed Edit:*** Allow `[0-9]*` after cookie words; add `cookie2`, `cookie_name2` to `COOKIE_WORD_KEYS`; make lookahead and consumer share one bound (consumer `[\w.\-]*` or the bare-word alternative consumes its own digit run); pin 21 and 40 digit rows for pass, auth, session, bearer; mutants for each.

### [Issue 5] [`design` D9-5] - Severity: Minor
*   **Affected Scope:** `redact.py:228` (`_AUTH_FLAG` literal `{0,6}`) vs `FLAG_PREFIX_WORDS` (:315); timing test; exact cookie names in `FLAG_EXACT_WORDS` vs curl rule (:877).
*   **Discrepancy Description:** Copies not tied: literal 6 with no mutant; the timing test measures only `_CRED_FLAG`, not `_AUTH_FLAG`, `_DIGEST_WORD`, `_COOKIE_KEY_BODY`; exact cookie names exist twice and differ (`--sessioncookie`, `--set_cookie`). Evidence: a `--password` flag preceded by 7 prefix words is readable on head and both older trees (accepted stated cost).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One source of truth rule; timing is a security property (untimed patterns).
*   ***Proposed Edit:*** Build `_AUTH_FLAG` from the constant; mutant on it; extend the timing test (200 kB of `--a-authorization `, unclosed-quote Digest, long run after `cookie`); one cookie-name table used by both rules.

### [Issue 6] [`design` D9-6 + evidence] - Severity: Minor
*   **Affected Scope:** `guard/redact.py:121-130, :200-208`; `k1b/redaction.py:212-222`; main rule `:599-606`.
*   **Discrepancy Description:** The ordinary-word guard makes credential names readable that main masks: `x-vercel-protection-bypass: <v>`, `bypass=<v>`, `bypass_key=<v>`, `bypass_code=<v>`, `bypass-code`, `bypass_value`. CHANGELOG names only bypasskey and bypasscode: the real cost is larger. Evidence adds, readable on head and masked on b7d7cd18: `bypass_key`, `compass_code`, `bypass_code`; wget `--no-cookies`, `--keep-session-cookies`, `--junk-session-cookies`, `--load-cookies`, `--save-cookies`, `--cookies` followed by a URL; `Authorization: Digest` + newline + a prose line; and the two cells `possession_id`, `obsession_id` (readable on head, masked on main). (The reviewer's Duo and Vercel claims are from memory and unchecked.) 26 cells go the other way (masked on head, readable on b7d7cd18): good, recorded.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each is a regression versus main or versus the last reviewed head. The word guard should reject "compass", "possession", "obsession" as before and still mask `bypass` + key/code/token/secret/value/phrase and `protection-bypass`.
*   ***Proposed Edit:*** For each cell on the evidence list: fix (mask) or give a TRUE reason it stays readable. Mask `bypass` + key/code/token/secret/value/phrase and `x-vercel-protection-bypass`; keep `compass`, `encompass`, `possession` readable only if the guard needs them (then state why, e.g. a word-boundary test) and pin both sides; wget flags that take a file or a URL are accepted readable only with a pinned row saying "not known to take a credential" (honest wording, replaces "switches or file names"). The lead keeps one owner question: if any `bypass` name stays readable by choice, ask the owner with the cell list.

### [Issue 7] [`codebase-details` C4] - Severity: Minor
*   **Affected Scope:** `tests/q8b_mutants.py` M136, M142, M143/M144, M146/M154, M145, M150, M151, M158.
*   **Discrepancy Description:** M143/M144 and M146/M154 have identical old/new text; M145, M150, M151 missing without a reason; M158 (curl cookie rule `(?:set|session)` -> `(?:set)`) may survive because `FLAG_EXACT_WORDS` holds `session[_-]?cookie`; M136 `assert False` and M142 `(1, ` match any failure.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A mutant that is a duplicate or may survive proves nothing.
*   ***Proposed Edit:*** Make duplicates differ or merge; say why 145/150/151 do not exist (or add them); run M158 and show it killed with its output, or remove the overlap; replace the weak expect strings with the test's own message.

### [Issue 8] [`design` D9-7 + `codebase-details` C5, D9-8] - Severity: Nit
*   **Affected Scope:** LIMITS and CHANGELOG.
*   **Discrepancy Description:** Wrapped-header cost not in LIMITS (fixed with Issue 1); CHANGELOG "new mutants M115 and later" (M115 is batch 7, batch 8 starts M116); `--apiInputTokens` stated exception not pinned (both outcomes); quoted value after `--authorization <scheme>` capped at 512 (`_QUOTED_TEXT`) not named in LIMITS; `COOKIEJAR=v`, `COOKIESTORE=v` masked in capitals (`(?-i:(?=[A-Z]))` at redact.py:65) and readable in lower case: pin lower only (over-mask).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Cheap, same files.
*   ***Proposed Edit:*** Correct the numbering; pin both outcomes for `--apiInputTokens`; name the 512 cap in LIMITS; add the capital/lower case rows for COOKIEJAR and COOKIESTORE.

### [Issue 9] [evidence: fail-before and cost] - Severity: Minor
*   **Affected Scope:** `evidence/Q8b/3eaae7c1/7-failbefore-old-passed.txt`, `8-cost.txt`.
*   **Discrepancy Description:** 54 of the 72 tests in the four delta files pass on b7d7cd18 old code; no per-test line says control, killing mutant or why. Largest cost ratio head/main: `--a*39 pass` flag 3.48, cookie prefixes 2.94, glued plural tokens 2.88 (up to 1.25 s on 200 kB), not stated in CHANGELOG.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Standing r7 Issue 11 rule: a test that passes on old code needs a stated reason.
*   ***Proposed Edit:*** One line per each of the 54 (control and reason, or killing mutant, or a fail-before proof) in the builder notes; the cost numbers (ratio per shape and absolute time) go into CHANGELOG; run the three worst shapes after the fix.

### [Issue 10] [deviation] - Severity: Nit
*   **Affected Scope:** `tests/test_q8b_batch6.py` (outside the builder's allowed list).
*   **Discrepancy Description:** Edited without leave; the reviewer judged it narrow and acceptable.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** Recorded in the ledger; the batch-9 brief lists the file as allowed and asks the builder to say which lines changed.
*   ***Proposed Edit:*** None.

## Handoff counts
Accepted (PROPOSE FIX): 9 (3 Major-group items: Issues 1, 2, 3 plus 6 Minor/Nit items: 4, 5, 6, 7, 8, 9; Issues 4 and 9 include evidence-derived cells). Contested: 0. Escalated: 0 (one owner question will be raised by the builder or lead only if a `bypass` name stays readable by choice, Issue 6). Declined: 1 (Issue 10). Remaining unaddressed: none. Severity unchanged from the reviews (Issue 9 is an evidence item labelled Minor, as in r8 Issue 13).

## Who fixes it
One batch-9 builder on a new branch `core/q8b-b9` from `3eaae7c1`, plain push to `wip/cloud-q8b-b9`. Files: `src/hadavin_sdk/guard/redact.py`, `src/hadavin_sdk/k1b/redaction.py` (including LIMITS), `tests/q8b_mutants.py`, `tests/test_q8b_batch8.py`, `tests/test_q8b_batch8_lines.py`, `tests/test_q8b_batch9.py` (new), `tests/test_q8b_batch6.py` (only the lines named in the notes), the controls lines file, `CHANGELOG.md`, builder notes. Gates once on the final head, as in the batch-8 brief. Anything found while fixing is fixed in the same batch or listed with its exception reason.
