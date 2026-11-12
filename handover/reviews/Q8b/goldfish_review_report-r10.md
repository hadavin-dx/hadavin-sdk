Status: resolved

# Goldfish Annotated Review Report (Q8b batch 9, round 10)

**Target:** branch `wip/cloud-q8b-b9`, head `c36ce0dc37b4c230116668505ffdafee1ef2d7bb` (delta `3eaae7c1..c36ce0dc`). REDACTION path, no round cap. No person was available: recommended option for every item; the one owner question (Issue 7) is escalated with a safe default.

**Evidence status (first).** Independent evidence `handover/evidence/Q8b/c36ce0dc/RESULTS.md`: ruff, format, bandit, `scan_repo`, gitleaks exit 0; `q8b_mutants` 175 of 175; `stage_mutants` 37 of 37; `mutation_runner_mutants` as user nobody 64 of 64; full pytest on the head exit 0 (10945 passed, 1 skipped); cost ratios 2.6 to 3.5 times main; known timing flake only (head fail, pass, pass; main fail, fail, fail). Not run: CI perf step, Python 3.12, Windows, CodeQL, SonarCloud, CodeRabbit, Semgrep, zizmor. The evidence probe (432 cells) found 21 cells readable on the head AND on the previous head `3eaae7c1` that main masked: nothing got worse in this batch, but the batch's own claim "0 cells are readable that main masked" is false. The runner did NOT probe wrapped tokens of 8 to 15 characters, so the Blocker's exact inputs rest on reading until the batch-10 builder probes them. No new finding was added by the lead; nothing was contested.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` R10-1, `codebase-details` F1] - Severity: Blocker
*   **Affected Scope:** `src/hadavin_sdk/guard/redact.py:48-64` (`_SCHEME_GAP`, `WRAPPED_TOKEN_MIN = 16`), used at `:786` (Basic rule) and `:894-896` (generic Authorization rule); `tests/test_q8b_batch9.py:75-86`, `:111-138`; CHANGELOG batch 9 item 1.
*   **Discrepancy Description:** After a plain line break the head needs a wrapped token of 16 or more characters from `A-Za-z0-9+/_=<>-` holding a capital, a digit or one of `+/_=<>`. Main needed only 8 characters (`[a-z0-9+/<>_]{8,}` for Basic, `[^\s"']{8,}` for the generic rule) after any white space. Readable on the head, masked on main (by reading): `Authorization: Basic\ndXNlcjpwYXNz` (12 characters), `Authorization: Token\nabcd1234efgh`, `Token\nab.cdefghijklmnopqrstu`, `Basic\n\n  <12 characters>`, a lowercase-only token alone on the next line. Evidence confirms 21 cells readable on the head and on `3eaae7c1` but masked on main: Authorization `Token`, `ApiKey`, `Digest` followed by LF or CRLF then the value; `Basic` or `Token` followed by LF and a lowercase-only 16-plus-letter value alone. The CHANGELOG sentence "After the fix 0 cells are readable that main masked" is false and contradicts the cost sentence in the same item. The differential test `test_b9_1_every_shape_that_main_masked_is_masked_now...` builds its oracle only from tokens of 16 or more with a capital or digit, so it cannot see the class; mutant M161 detects only a raise of the minimum to 64.
*   **Rationale:** Short Basic credentials are the typical weak test credentials; the ticket promises Authorization values are masked; this is a regression against main of a promised secret.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid and the same root in both reports; evidence confirms the class. Over-masking a following prose word is the safe direction on a redaction path.
*   ***Proposed Edit:***
    *   Location: `redact.py` `_SCHEME_GAP` and its two users; `tests/test_q8b_batch9.py`; `tests/q8b_mutants.py`; CHANGELOG.
    *   Change: (1) FIRST probe the reviewers' exact inputs on main, `3eaae7c1` and the head (12-character `Basic`, `Token\nabcd1234efgh`, a dot or `~` or `:` inside the first 16 characters, `Basic\n\n` plus 12 characters, lowercase-only 8 to 20 letters, LF and CRLF, `Token`, `ApiKey`, `Digest`, `Bearer`, `Basic`) and save the table. (2) Set the wrapped-token minimum to the rule's own minimum (8) and widen the character class to what main's generic rule accepted (`[^\s"']{8,}`), for every scheme word including `Token`, `ApiKey`, `Digest`, `Bearer`, `Basic`, after LF, CRLF and a blank line. (3) Accept over-masking of a following prose word of 8 or more characters; state the cost with a measured count on an ordinary-text corpus (name the corpus and the count of changed lines). (4) Differential oracle in `test_b9_1_...` gains short tokens (8 to 15), dots, `~` and `:`, lowercase-only; mutants on the minimum (too high and too low) and on the character class; keep a pinned "readable by choice" row only for a case the measurement shows cannot be masked without hiding prose, and then raise it in the owner question (Issue 7). (5) Delete the false CHANGELOG sentence and replace it with the measured table. (6) Run the full evidence probe cells again and show the 21 evidence cells and the reviewers' cells all masked.

### [Issue 2] [`codebase-details` F2, F3] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/guard/redact.py:874-887` (Digest rule); CHANGELOG items 1 and 6; `src/hadavin_sdk/k1b/redaction.py:76` (LIMITS); `tests/test_q8b_batch9.py:100-108`, `:452-457`.
*   **Discrepancy Description:** A Digest header folded over more than one line leaves the response hash readable: the rule ends at `([^\r\n]{8,})`, the first line after the scheme word, and continuation lines are never consumed. `Authorization: Digest username="u",\n    realm="r",\n    response="8ca523f5e9506fed4657c9700eebdbec"` leaves `response=` (32 hex, offline-crackable) and `nonce` readable; no other rule catches it. CHANGELOG item 6 and LIMITS say "a fold is masked"; tests fold once only. Main leaked too (not a regression), but it is a readable secret behind a new claim. Separately, CHANGELOG item 1 says one gap rule `_SCHEME_GAP` serves the Basic, the generic and the Digest rule; the Digest rule builds its own fold-only gap and only the other two use `_SCHEME_GAP`.
*   **Rationale:** A false current-state claim; a readable secret on a redaction path.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. Fixing the code is cheap and linear; per rule 5 do not defer.
*   ***Proposed Edit:***
    *   Location: `redact.py` Digest rule; CHANGELOG items 1 and 6; LIMITS; tests; mutants.
    *   Change: after the first line also consume following lines that start with a space or tab, linear and possessive (for example `(?:[^\r\n]*+(?:\r?\n[ \t]++[^\r\n]*+)*+)`); a three-line RFC 7616-style row (`username`, `realm`, `nonce`, `response` over three lines, LF and CRLF) in the tests; a mutant on the continuation group; timing shape for a long run of fold lines; reword item 1 to "two rules use `_SCHEME_GAP`; the Digest rule has its own fold-only gap" and item 6 to what the rule really masks.

### [Issue 3] [`design` R10-2, `codebase-details` F4] - Severity: Major
*   **Affected Scope:** `tests/test_q8b_batch8_lines.py:10-11`, `:176-182`, `:186-199`, `:241-251`, `:287-295`; builder notes lines 17-18; CHANGELOG item 3.
*   **Discrepancy Description:** r9 Issue 3 is still open. Evidence: of 74 controls, 39 have a planted fault, 28 have neither a planted fault nor a reason, 7 carry a no-fault reason. `UNPLANTED_MAX = 28` is a ceiling nothing forces down. The builder's reason is "NOT DONE in this batch (time box)", which preamble rule 5 does not allow, and the notes say "Owner decision not needed". The 7 NO_FAULT reasons ("no product line can be faulted") are untrue: the mutant table already plants faults in test files through `test_file_mutant` (M136, M142 edit `tests/test_k5_round11.py` and `tests/mutation_runner_mutants.py`). `planted_killers` (`:176-182`) counts a control as PLANTED if any mutant names its test, without checking the mutant relates to what the control guards. The batch 9 timing tests have no planted fault.
*   **Rationale:** A ratchet of 28 pins the weakness.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; the work is plain and known; "time box" is not an exception. Not owner-only.
*   ***Proposed Edit:***
    *   Location: `tests/test_q8b_batch8_lines.py`, `tests/q8b_mutants.py`, builder notes, CHANGELOG item 3.
    *   Change: plant a fault for each of the 28 and each of the 7 (timing tests: a concrete non-linear mutant, for example making a possessive `_LINE_SPACE++` non-possessive and timing it); where a control truly cannot be faulted give a true reason that names the rule-5 exception or the checkable property; make the check fail if any control is unplanted without a true reason; lower `UNPLANTED_MAX` to the real count (target 0) and make the check require that each PLANTED claim names a mutant whose snippet touches what the control guards; remove "Owner decision not needed".

### [Issue 4] [`design` R10-3, `codebase-details` F5] - Severity: Major
*   **Affected Scope:** builder notes lines 3-15 and 21; evidence `7-new-pass-on-old.txt`, `7-new-fail-on-old.txt`.
*   **Discrepancy Description:** "69 tests pass on old code, each with a true one-line reason" does not hold. The notes itemise about 43 tests; the rest are lumped as "batch 8 tests ... old tests". Evidence: of the 33 test names added in DELTA.patch, 58 ids fail and 47 ids pass on the old code (43 in `test_q8b_batch9.py`, 4 in `test_q8b_batch8_lines.py`); three failed ids are not among the added names. Reasons for `test_b9_2_...` (10 cases) and `test_b9_8_...` say "no single planted fault possible" while the same note says "a mutant that masks the second word would kill it"; M177 is killed by `test_b9_5_...`, not by these. No line for `test_b9_8_a_quoted_text...512`, `test_b9_6_a_bare_bypass...`, `test_b9_6_a_wget...`, `test_b9_6_a_line_break_ends_a_digest...`, `test_b9_6_the_changelog...`, `test_b9_8_the_changelog_numbers...`.
*   **Rationale:** The "pass on old code" table is the proof that a test can fail; reasons must be true per test.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; the evidence list gives the exact ids.
*   ***Proposed Edit:***
    *   Location: builder notes; `tests/q8b_mutants.py` (new mutants).
    *   Change: one line for every id in `7-new-pass-on-old.txt` with a killing mutant name or a true reason ("control", "pins existing behaviour", "plant: M..."); a mutant for the two stated-cost pins; rewrite contradictory reasons; the counts in the notes are the evidence runner's counts (58 fail, 47 pass), not the builder's 61 and 69.

### [Issue 5] [`design` R10-4, `codebase-details` F6] - Severity: Major
*   **Affected Scope:** builder notes (gate commits); `tests/q8b_mutants.py`.
*   **Discrepancy Description:** The builder's full pytest ran on `fd183989`, not on `c36ce0dc`; six test files read `tests/q8b_mutants.py` and `planted_killers` parses it by regex, so "only a script changed" was no reason to skip the run.
*   **Rationale:** A gate must run on the head it is cited for.
*   ***AI Suggestion:*** PROPOSE FIX (closed by evidence, no code change)
*   ***Justification:*** The independent evidence ran the full pytest on the head: exit 0, 10945 passed, 1 skipped, 29 deselected, 16 xfailed; `q8b_mutants` 175 of 175 with 0 "SNIPPET NOT FOUND" on the head (`handover/evidence/Q8b/c36ce0dc/RESULTS.md`). The ledger row is FIXED-VERIFIED.
*   ***Proposed Edit:***
    *   Location: builder notes.
    *   Change: each gate line names the commit it ran on; the batch-10 notes must not carry a gate over a commit that touched a file the gate reads.

### [Issue 6] [`design` R10-5, `codebase-details` F7] - Severity: Major (names ending _key); Nit (the rest)
*   **Affected Scope:** `redact.py` ordinary-word guard and `BYPASS_SECOND_WORDS`; `k1b/redaction.py:76` (LIMITS), `:265` (record rule); `tests/test_q8b_batch9.py` (`test_b9_8`, COOKIEJAR pin); CHANGELOG (ticket 1f).
*   **Discrepancy Description:** `compass_key`, `overpass_key`, `encompass_key`, `compass_code`, `overpass_value`, `encompass_phrase` are readable although a name ending `_key` says it is a key; only `bypass` gets the second-word rule, so `compass_key` is readable while `bypass_key` is masked. Evidence: the JSON forms are readable on the head and on `3eaae7c1` but masked on main; the text forms are readable on main too. `possession_id`, `obsession_id`: regressions by the letter of main but ids, not credentials; ticket 1f's "every key main accepts is accepted (107,041 / 0)" no longer holds. COOKIEJAR: the text rule masks it (pinned) but `R.sensitive("COOKIEJAR")` is False, so a record key `COOKIEJAR` with a real cookie value is readable (text-versus-record drift, the r7 class). LIMITS lists "`authorization=a b`" among "flags" and "pinned for nine flags"; nine is right, but `authorization=` is not a flag.
*   **Rationale:** A name that says it is a key must be treated as one on every path; text and record paths must agree.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. Masking an ordinary word followed by `_key`, `_secret`, `_token` or `_password` is the safe direction; `_code`, `_value`, `_phrase` and the two id names are Nit-level and are decided with pinned rows, not left open.
*   ***Proposed Edit:***
    *   Location: `redact.py`, `k1b/redaction.py`, tests, mutants, CHANGELOG, LIMITS.
    *   Change: apply the `bypass` second-word rule to every ordinary word ending `_key`, `_secret`, `_token`, `_password` in the text rule, the record walk and the flag guard, one shared word list, tested on all three paths, pinned both sides (ordinary word alone stays readable, ordinary word plus those endings is masked); `_code`, `_value`, `_phrase`: decide, pin both sides and say which in CHANGELOG; `possession_id`, `obsession_id`: accept readable with a pinned row and correct ticket 1f's count in the CHANGELOG; make the record side mask `COOKIEJAR`-shaped keys like the text side, or state in LIMITS that the record side shows it and why, with a pinned row; reword LIMITS so `authorization=a b` is not called a flag.

### [Issue 7] [`design` R10-5, `codebase-details` F7] - Severity: Minor
*   **Affected Scope:** `redact.py` bypass rules; `tests/test_q8b_batch9.py` (`test_b9_6_a_bare_bypass...`); r9 report (owner question condition); builder notes line 21.
*   **Discrepancy Description:** A bare `bypass` with a value (`bypass=V`, `bypass: V`, JSON `bypass`) is readable on the head and on `3eaae7c1`; main masked it only through an unbounded `pass` match (the ending of `bypass`). `bypass=true` is a common switch; the reviewers call it Minor and acceptable. The r9 report required the lead to raise one owner question if any `bypass` name stays readable by choice; the builder wrote "Owner decision not needed". Also: a lowercase-only 16-plus-letter token alone on the next line after `Basic` or `Token` stays readable (real but rare); with the Issue 1 fix it should be masked, and if it cannot be masked without hiding prose the owner needs the measured count.
*   **Rationale:** Whether a bare word `bypass` with a value counts as a secret is a product decision about what a person reading logs may see.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** The evidence needed for the decision (what the studio calls a secret for a bare switch word) is outside every file the reviewer could read; it is the owner's call under the redaction promise. Do not fix by guessing. Safe default until answered: keep the bare `bypass` readable and pinned both sides, state it in CHANGELOG and LIMITS, and ask.
*   ***Proposed Edit:***
    *   Location: `handover/questions-for-lead.md` (new item `q-q8b-bare-bypass`), CHANGELOG, LIMITS, builder notes.
    *   Change: lead writes one plain question: "Should a bare word `bypass` followed by a value, such as `bypass=true`, be hidden as if it were a password? Hiding it also hides harmless switches; showing it could show a real bypass token." Default: shown. Builder removes "Owner decision not needed", names the question id, keeps the pinned rows, and adds the measured count of ordinary lines changed if the owner later says hide.

## Handoff

- **Counts:** 7 issues. PROPOSE FIX 6 (Issues 1 to 6, of which Issue 5 is closed by evidence), ESCALATE 1 (Issue 7), CONTEST 0, DECLINE 0. Severity as reported, none changed: 1 Blocker, 5 Major, 1 Minor. Remaining unaddressed: all except Issue 5.
- **Who fixes it:** one batch-10 builder on a new branch from `c36ce0dc`, pushing to `wip/cloud-q8b-b10`. Files: `src/hadavin_sdk/guard/redact.py`, `src/hadavin_sdk/k1b/redaction.py`, `src/hadavin_sdk/approvals/channel.py`, `tests/test_q8b_batch9.py`, `tests/test_q8b_batch8_lines.py`, `tests/q8b_mutants.py`, `CHANGELOG.md`, builder notes. Fix order: Issue 1 first (probe, then code, then oracle), then 2, 6, 3, 4, then notes (5, 7).
- **Owner:** one question (Issue 7). Safe default stated.
- **Not run in evidence:** CI perf step, Python 3.12, Windows, CodeQL, SonarCloud, CodeRabbit, Semgrep, zizmor.
