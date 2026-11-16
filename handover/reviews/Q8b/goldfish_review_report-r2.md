Status: resolved

# Goldfish Annotated Review Report (round 2)

**Target:** `core/q8b-partial-mask-and-card-redaction` head `bcb2bfec` (one fix commit on `be53718c`), snapshot `/home/user/build/snap/q8bb1-bcb2bfec/files`. Redaction path: security, no round cap. No person was available; the recommended option was taken for every item. Nothing was DECLINEd where a secret stays readable.

Sources: `result-r2-design-full.md`, `result-r2-codebase-full.md`, `handover/evidence/Q8b/bcb2bfec/RESULTS.md`.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase`] C1 - Severity: Blocker
*   **Affected Scope:** `redact.py:266` (`_NO_GLUED_KEY`, 255-character look-ahead) against `redact.py:630` (key rule, `{0,40}` prefix); late EMAIL step at `redact.py:721-726`.
*   **Discrepancy Description:** A domain longer than 40 characters before a glued key leaves the value readable. The guard looks 255 characters ahead, the key rule only 40 back, so the two rules disagree and the late EMAIL step takes the text first.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Verified at the lines. Same bug class as a hand-kept pair of bounds: the guard and the key rule must come from one constant.
*   ***Proposed Edit:*** One shared bound constant used by both; the late EMAIL step stands aside whenever the key rule can match. Add LEADS with domains of 41, 100 and 255 characters, each with the value masked. Add a mutant that changes the bound in one place only.

### [Issue 2] [`codebase` C2, `design` B2] - Severity: Major
*   **Affected Scope:** `approvals/channel.py:66-69` (`_ASSIGNED`).
*   **Discrepancy Description:** Third hand-copied key list; it can drift from `redact.KEY_ALTERNATIVES`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Core rule: one source of truth. Class-level fix, not a patch of the spellings missing today.
*   ***Proposed Edit:*** Build `_ASSIGNED` from `redact.KEY_ALTERNATIVES` plus the `_ASSIGNMENT_KINDS` placeholders. Add a drift test over every spelling in the shared list (card and Slack paths) and a mutant that drops one spelling.

### [Issue 3] [`codebase`] C3 - Severity: Major
*   **Affected Scope:** CHANGELOG entry for Q8b.
*   **Discrepancy Description:** States a test that compares the CHANGELOG with LIMITS; no such test exists.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A claim without a test is an unverified claim.
*   ***Proposed Edit:*** Add the test (CHANGELOG limits text equals the LIMITS constants). If it cannot be written cleanly, remove the sentence.

### [Issue 4] [`design`] B1 - Severity: Major
*   **Affected Scope:** `approvals/channel.py:64-90` (`_TAIL_WORD`, `whole_assignment_values`).
*   **Discrepancy Description:** Deletes text from the approval card: `--force --target prod` and the `Plan <hash>.` suffix vanish.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The approver must see the whole action. Safe default from the task: keep all text visible, mask only the value.
*   ***Proposed Edit:*** Stop deleting text. Mask the value span only. Where a space-separated tail stays readable after a key from the shared list, mask that tail by the rule of E2 (words after the key up to the next flag or the plan suffix) and keep flags and the plan hash. A person sees `password=<SECRET_1> --force --target prod`. Tests: `--password=x --force` keeps `--force`; the `Plan <hash>.` suffix survives.

### [Issue 5] [`evidence`] E-1 - Severity: Major (readable secret)
*   **Affected Scope:** record-walk path, RESULTS.md E2.
*   **Discrepancy Description:** `password=<SECRET_1> horse battery staple` leaves the rest of a passphrase readable. Same on main, but it is a readable secret on the redaction path.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Mask the space-separated tail after a shared-list key on the walk path with the same rule as Issue 4. Same for the key `passphrase=correct horse battery staple` (nothing masked on head or main).

### [Issue 6] [`evidence`] E-2 - Severity: Major (readable secret)
*   **Affected Scope:** card and Slack path; link followed by `password: `.
*   **Discrepancy Description:** `[link removed] <value>`: 8 cases, value readable, same on main.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:* ** Apply the key rule after link removal, or before it, so the key is seen. Add the 8 cases as tests for both paths.

### [Issue 7] [`evidence`] E-3 - Severity: Major (readable secret)
*   **Affected Scope:** 38 Bearer cases.
*   **Discrepancy Description:** Readable on head and main.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Builder lists the 38 cases from the evidence files, fixes at the choke point (Bearer token rule in `redact.py`), adds the cases as a test table. If a case turns out to be a plain word (not a token), the builder says so per case.

### [Issue 8] [`evidence`] E-4 - Severity: Minor
*   **Affected Scope:** `redact.py` diff against the ticket.
*   **Discrepancy Description:** The ticket says no edit of `redact.py`; the diff edits it. PR77 touches the same file.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Record in the ledger and in questions-for-lead: PR77 conflict expected; Q8b merges first or PR77 is rebased. Builder keeps the `redact.py` change minimal.

### [Issue 9] [`evidence`] E-5 - Severity: Minor
*   **Affected Scope:** head test files.
*   **Discrepancy Description:** They cannot be collected on main (one helper import, `_ONLY_PLACEHOLDERS`), so fail-before cannot be shown for all tests.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Move the helper into a shared test module that also exists on main, or run fail-before with the helper copied. The evidence runner records: 40 new tests pass on old code, so those 40 must be rewritten to fail on old code.

### [Issue 10] [`codebase` C4 / m1] - Severity: Minor
*   **Affected Scope:** `cards.py:85` (`render_shadow`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Route the shadow label through the same label function as `summary`; add a test.

### [Issue 11] [`codebase` C5, C6] - Severity: Minor
*   **Affected Scope:** test line 326 (dead assertion); plan-hash line.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Make the assertion live (it must fail when the code is mutated); C6 is covered by Issue 4.

### [Issue 12] [`design` m2, n1, n2, n3] - Severity: Nit
*   **Affected Scope:** fence decision; glued spellings in R7; perf test bound; `:` and `"key":"v"` rows.
*   ***AI Suggestion:*** PROPOSE FIX (all four; cheap, and two touch redaction)
*   ***Proposed Edit:* ** m2: assert no new fence appears. n1: add glued spellings to R7. n2: replace the 30-second bound with the ratio method. n3: add `:` and `"key":"v"` rows.

## Handoff counts
Accepted (PROPOSE FIX): 12 issues. Contested: 0. Escalated: 0. Declined: 0. Remaining unaddressed: 0 until the fix batch.
Escalation to the lead (questions-for-lead): card target label semantics; PR77 order.
Fix batch 2 builder: Sonnet; round 3 review needed (redaction path, no cap).
