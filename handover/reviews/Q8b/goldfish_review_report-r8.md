Status: resolved

# Goldfish Annotated Review Report (Q8b batch 7, round 8)

**Target:** branch `wip/cloud-q8b-b7`, head `b7d7cd18f9c0faf4f380dc71d399208a2f3aa7b4` (delta `8e8ccbef..b7d7cd18`). REDACTION path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `q8bb7-design-r8.md` (0 Blocker, 0 Major, 5 Minor, 3 Nit) and `q8bb7-codebase-r8.md` (0 Blocker, 1 Major, 4 Nit). Previous round: `goldfish_review_report-r7.md`. Independent evidence: `handover/evidence/Q8b/b7d7cd18/RESULTS.md` and its probe files.

**Evidence status (first).** ruff, format, bandit, `scan_repo`, gitleaks exit 0; `stage_mutants` 37 of 37; `q8b_mutants` 115 of 115 (no WRONG_REASON line); `mutation_runner_mutants` as user nobody 64 of 64; full pytest exit 0: 10815 passed, 1 skipped, 16 xfailed, 0 failed. The timing test is the known flake (head pass, fail, fail; main pass, fail, fail; its fix is on `core/fix-timing-harness-flake`). The appendix checks P1, P2 and N9: head 0, 0, 0 (main 2545 / 2874 / 0; the ticket measured 1 for N9 on main, the runner got 0: recorded). The runner's own probe, 1,209 cells over card, tool, run, log, record message and record key: no cell readable on the head that main masked, apart from the 120 intended ordinary-word cells. The 200,000-key check: 0 refused by the head. Cost of `redact()` on 200 kB hostile text: 1.1 to 3.5 times main, no timeout. Fail-before on main source: 228 failed, 451 passed, 14 xfailed; of the 28 tests in `test_q8b_batch7.py` 7 pass on old main (the six fuzz rows `test_b7_1_..._stay_masked[0..5]` and `test_b7_2_a_count_of_tokens_stays_readable_as_a_flag`).

**Not run (listed, not hidden):** the perf step (the ticket names none), the Python 3.12 job, the security job, the Vault-backed tests, the appendix rows A2 and A4 typed one by one, the X1 to X9 table outside the full suite, the oracle on main (main has no copy). The next evidence runner types A2, A4 and X1 to X9 by hand and reproduces Issue 2 (cookie flags) before the builder fixes it.

**Reviewers disagree on one point.** The codebase reviewer reports no over-masking beyond what the CHANGELOG names; the design reviewer reports that `wget --no-cookies http://example.com/path` shows `--no-cookies <SECRET_1>`. The runner's probe did not include that input. I treat the design finding as real until a probe says otherwise (Issue 2).

## Prioritized Findings & AI Suggestion

### [Issue 1] [`codebase` R8-1 (Major), `design` D8-1 (Minor): one finding] - Severity: Major
*   **Scope:** `guard/redact.py:239-253` (`_PLURAL_TOKENS`, the `(?:s(?<!tokens))?` group), `k1b/redaction.py:203, 234-238, 111` (`_CAMEL`); `tests/test_q8b_batch7.py:239-249`.
*   **Description:** A plural `tokens` flag after a glued or camelCase word stays readable: `run --apiTokens Jq7firstValue now`, and `--accessTokens`, `--refreshTokens`, `--idTokens`, `--accesstokens`, `--idtokens`, `--authtokens`, `--apitokens`. The record walk masks `apiTokens` (it cuts camelCase, finds the word `tokens` after a non-count word). Same class as round 7 Issue 2; the CHANGELOG says the class is fixed "as for the record walk". Readable on main too, so not a regression, but the claimed class is not closed. The drift test cannot see it because its keys come from `KEY_ALTERNATIVES`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Readable credential in the redaction class; fix, not defer.
*   ***Proposed Edit:*** One definition of "a plural `tokens` is a credential when the word before it is not a count word", used by both files, covering `_`, `-`, glue and camelCase boundaries (case scoped with `(?-i:...)` since `(?i)` is global). Keep `max_tokens`, `maxTokens`, `input_tokens`, `audio_tokens` and bare `--tokens` readable (stated). Add `apiTokens`, `accessTokens`, `refreshTokens`, `idTokens`, `accesstokens`, `authtokens`, `apitokens`, `maxTokens` to `PLURALS` and the test at `:239-249`; make the drift test read the record walk's own word split, not only `KEY_ALTERNATIVES`; one mutant per branch.

### [Issue 2] [`design` D8-2] - Severity: Minor (over-mask regression versus main)
*   **Scope:** `guard/redact.py:231` (`"cookie"` in `FLAG_ONLY_WORDS`), `:249` (plural `s`), `:791` (curl rule `(?:[a-z0-9]+[_\-]){0,2}cookies?`).
*   **Description:** `cookie` is now a flag word that accepts a plural and up to three prefix words, so a boolean or file-taking option masks the next argument: `wget --no-cookies http://example.com/path`, `--keep-session-cookies <url>`, `--junk-session-cookies <url>`, `--load-cookies cookies.txt`. Main left these readable.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Not contested: no code reason found; the codebase reviewer did not test this input and the runner's probe did not include it. The builder reproduces it first (script in the evidence folder) and states the result.
*   ***Proposed Edit:*** For the `cookie` flag word: the exact names `cookie`, `set-cookie` and `session_cookie` only; no plural, no prefix groups; `--no-cookies`, `--keep-session-cookies`, `--junk-session-cookies`, `--load-cookies`, `--save-cookies` stay readable (pinned rows both ways); name the cost in LIMITS and CHANGELOG item 3 if any spelling stays masked. Mutant for each.

### [Issue 3] [`design` D8-3] - Severity: Minor
*   **Scope:** `guard/redact.py:195-202`: `session[_\-]?id`, `session[_\-]?key`, `session[_\-]?cookie`, `session[_\-]?value`, `pass[_\-]?code`, `pass[_\-]?key`, `pass[_\-]?value`, `auth[_\-]?value` are unguarded; the ordinary-word look-behinds are only on the bare words.
*   **Description:** `possession_id=<v>`, `obsession_id=<v>`, `bypass_key=<v>`, `compass_code=<v>` are masked, contradicting "ordinary words stay readable in every form" (CHANGELOG item 5, the `:148-151` comment, the `test_b7_5` docstrings). Over-mask, not a leak.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Put the same `_not_after_ordinary_word` look-behind on each of those alternatives; keep `xbypass_key` style real keys masked; add `possession_id`, `obsession_id`, `bypass_key`, `compass_code` as readable rows and `xbypass_key`, `bypasspass_key` as masked controls; mutants. If a spelling is meant to stay masked (`bypass_code`), say so in `CARD_COST` with the reason.

### [Issue 4] [`design` D8-4, `codebase` R8-3: one finding] - Severity: Minor
*   **Scope:** `guard/redact.py:396-397` (`AUTH_SCHEMES`, `_AUTH_SCHEME_WORD` with `(?=[^\s"'-])`), `:743`, `:804-805`, `:813`, `:648`; claim at `k1b/redaction.py:68` and CHANGELOG item 4.
*   **Description:** The flag form knows five scheme words while the header form takes any word: `--authorization NTLM|Negotiate|OAuth|Splunk <t>` shows the token; `--authorization Bearer 'eyJ...'` (a quote after the scheme word) masks only `Bearer`; `--authorization Digest username=u, response=h` masks only up to the first quote or space. Not a regression.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** For `--authorization` and `--bearer` only: any alphabetic first word followed by one more word is masked, quoted or not, to the closing quote; a Digest value is masked to the end of the logical value. Generic credential flags keep the stated one-word rule (Issue 11). Rows for each shape, a mutant, and the LIMITS sentence names the exact rule.

### [Issue 5] [`design` D8-5] - Severity: Minor
*   **Scope:** `guard/redact.py:245` (`{0,3}`), CHANGELOG item 15, `tests/test_q8b_batch7.py:471-479`; LIMITS "hyphen-joined".
*   **Description:** The limit is justified by a cost nobody measured, and the test pins a readable credential (`--cloud-sql-proxy-db-password Jq7secret now`) so a later fix would fail it. `_` also joins words.
*   ***AI Suggestion:*** PROPOSE FIX (the stronger option)
*   ***Justification:*** Work that is worth doing is done now: measure and raise.
*   ***Proposed Edit:*** Raise the bound to 6, add a timing test on hostile flag text (long `a-` runs, 200 kB, bound in seconds and relative to the bound 3), change "hyphen-joined" to "joined by `-` or `_`", and turn the leak-pin into a masked row.

### [Issue 6] [`design` D8-6] - Severity: Nit
*   **Scope:** CHANGELOG batch-6 "Incident cases" entry: "see the batch 7 entry below" (it is above).
*   ***AI Suggestion:*** PROPOSE FIX (one word).

### [Issue 7] [`design` D8-7] - Severity: Nit
*   **Scope:** `guard/redact.py:732-737`, CHANGELOG item 4; `tests/q8b_mutants.py` M103 and M108 (`expect="AssertionError"`).
*   **Description:** The Digest rule masks `[^\r\n]{8,}`: in one-line JSON everything after the header, including closing quotes and braces, is masked (the text no longer parses); the CHANGELOG says "prose". The two mutant expectations accept any failing assert.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** When the header value is quoted, stop at the closing quote; otherwise name "the rest of the line, including JSON structure" in the CHANGELOG; pin M103 and M108 to the test's own message. Together with Issue 10 (`\s+` to `[ \t]+`).

### [Issue 8] [`design` D8-8, `codebase` R8-2: one finding] - Severity: Nit
*   **Scope:** `guard/redact.py:185` (`[0-9]{0,9}`) against `k1b/redaction.py:113, :203` (unbounded).
*   **Description:** `pass1234567890=Jq7secret` (10 digits) is a record key but readable as `key=value` on the card; `{0,9}` mutated to `{0,3}` survives.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** `[0-9]*` (the look-ahead needs `[:=]` right after; linear); rows with 9, 10 and 40 digits; a mutant on the bound; the CHANGELOG sentence "up to nine digits" is removed.

### [Issue 9] [`codebase` R8-4] - Severity: Nit
*   **Scope:** CHANGELOG batch-7 items 2 and 4.
*   **Description:** Item 2 says a plural `tokens` is a credential only after a non-count word "as for the record walk", but the record walk also masks bare `tokens` and `--tokens` is a deliberate exception (test `:230`). Item 4 says the scheme word stays readable in the `=` and `:` forms; `--authorization=Token abc` masks both words (`_VALUE_TAIL`, `:813`); the test (`:322-336`) checks only that the token is gone.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Reword both sentences to the code ("except the bare `--tokens`"; "in `Authorization: Token <t>` the scheme word stays readable; after `--authorization=` both words are masked"); the test asserts the scheme word too.

### [Issue 10] [`codebase` R8-5] - Severity: Nit
*   **Scope:** `guard/redact.py:736` (`digest\s+...` crosses a newline); `tests/test_q8b_batch7.py:471-480` asserts under 20 seconds, no mutant.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** `[ \t]+`; a row `Authorization: Digest` + newline + a prose line stays readable; the neighbouring `[a-z]+\s+` rule on the same lines gets the same check (it is also on main: fix it, and say so). The timing test becomes the one of Issue 5 with a mutant that removes the bound.

### [Issue 11] [evidence probe `--pass2`, `--password`, `--newpass`, `authorization=a b`: second word readable (25 + 20 cells)] - Severity: Minor
*   **Scope:** a credential flag followed by two space-separated words; `authorization=a b` with no scheme word.
*   ***AI Suggestion:*** CONTEST (the generic second word); PROPOSE FIX (pin and wording only)
*   ***Justification:*** Checkable evidence the reviewers could read: round 7 Issue 4 (`goldfish_review_report-r7.md`, lines 34-39) and the round 7 design review accepted this as a stated design choice: in a shell the second word is a separate argument, and main showed both words for four of these flags only because they were not flags. Masking the second word would hide ordinary arguments (`--password x file.txt`). The head is not a regression (both words were readable on main). The scheme-then-token format is the part that is a credential; Issue 4 above widens that. This stays a stated limit, in LIMITS and CHANGELOG.
*   ***Proposed Edit:*** No behaviour change. Add `--pass2` and `authorization=a b` to the seven pinned flags list (now nine) and name them in LIMITS ("a second word after a credential flag is shown"). Note in the ledger row that the owner question `q-prh-spaced-secrets` (PR H) is the same kind of limit and has the same safe default.

### [Issue 12] [evidence `cookie_name=v` and `cookie_name: v` readable in the text forms (10 cells)] - Severity: Minor
*   **Scope:** `guard/redact.py` `_COOKIE_ASSIGN_KEY` (the underscore breaks the rule); the record walk masks `cookie_name`; CHANGELOG item 3 names `cookie_name` as an over-masking cost for record keys only.
*   **Description:** Card, tool result and log text show `cookie_name=v`; the record message masks it. Drift between the two paths.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Make the text rule follow the record walk for `cookie` followed by `_` or `-` and a word (`cookie_name`, `cookie-policy`); this is the same word list as the record walk: one source. Rows both forms and a mutant. If the walk's rule over-masks on purpose, state the cost in LIMITS and CHANGELOG.

### [Issue 13] [evidence: 66 test ids (47 functions) of the 139 old-main-passing tests are named in no mutant file] - Severity: Minor
*   **Scope:** `evidence/Q8b/b7d7cd18/139-not-named-anywhere.txt` (all 139 pass on head and on old main; 15 named by `q8b_mutants.py`, 58 more by `mutation_runner_mutants.py`, 66 by none).
*   **Description:** Round 7 Issue 11 asked one line per test: fails on old code, or control with a reason, or the killing mutant. The builder's notes (`q8bb7-builder-notes.md`) hold control lines for the K5 tests ("no mutant run for it in this batch"); the evidence text match cannot tell a stated control from a missing line.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** The builder writes one machine-checkable line per test id (the 66 and any new ones): `<test id> | control | <reason one reader can check> | <the command that shows it can fail, or the mutant that does>`. For the K5 round-11 and producers controls: run one planted fault each (rename the choke point in a scratch copy and show the test fail; the builder lists the command and output) or give the mutant. A script `tests/...` or tools check reads the notes and fails on a missing id; the next evidence runner repeats it.

## Handoff counts
Accepted (PROPOSE FIX): 12 (Issues 1-10, 12, 13; Issue 11 is partly accepted: wording and pins). Contested: 1 (Issue 11, the generic second word; evidence: round 7 report Issue 4 and the round 7 design review). Escalated: 0. Declined: 0. Remaining unaddressed: none. Severity unchanged from the reviews (Issue 1 Major). Because the path is redaction with no cap: one batch-8 builder fixes Issues 1-13 and reports once; then an independent evidence run (full suite, all mutant runners, my own probe of the 1,209 cells plus the new shapes, A2, A4 and X1-X9 typed by hand, the fail-before and the per-test line check) and two `egm:*` reviewers read the new head.

## Who fixes it
One batch-8 builder on a new branch `core/q8b-b8` from `b7d7cd18`, plain push to `wip/cloud-q8b-b8`. Files: `src/hadavin_sdk/guard/redact.py`, `src/hadavin_sdk/k1b/redaction.py` (including LIMITS), `tests/test_q8b_batch7.py`, `tests/q8b_mutants.py`, `tests/q8b_key_corpus.py`, `tests/q8b_helpers.py` if the drift test needs the record walk's split, `CHANGELOG.md`, the builder's notes. Edits `redact.py` regions that PR H touches at `:954-976` (different lines): the later of the two rebases. No other open package edits these files.
