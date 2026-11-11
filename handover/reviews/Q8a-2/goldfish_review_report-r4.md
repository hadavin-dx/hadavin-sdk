Status: resolved (by egm:egm-resolve, autonomous mode, recommended option for every item; no person was available or asked)

# Goldfish Annotated Review Report

**Target:** the Q8a-2 code at head 3210f93a (src/hadavin_sdk/approvals/receiver.py, hmac_v0.py, tests/test_q8a2_callback.py); ticket handover/tickets/Q8a-2-neutral-callback-and-guard.md
**Findings from:** handover/reviews/Q8a-2/result-r4-codebase-full.md (reviewer egm-codebase-details, round 4, by reading; evidence runner a4b5e2ea still running)

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase-details`] - Severity: Major-less minor (m1)
*   **Affected Scope:** receiver.py:198 (`hung_up = isinstance(sys.exception(), ConnectionError) and len(kinds) == 1`)
*   **Discrepancy Description:** a handler failure that is itself a builtin ConnectionError (store outage: ConnectionRefusedError) is logged only at DEBUG.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid. I read the same line; the decision uses the exception type, so a store outage looks like a hang-up. The reviewer's fix (decide from state: mark once the body is read and the handler runs) is the class-level fix.
*   ***Proposed Edit:*** set a per-request flag when the handler is entered; `handle_error` treats a ConnectionError as a hang-up only when the flag is not set. Add a test where the recorder raises ConnectionRefusedError and ERROR is expected; add it to the mutant list.

### [Issue 2] [`codebase-details`] - minor (m2)
*   **Affected Scope:** receiver.py:165-166 (`_answer` in the `finally`) and stdlib `handle_one_request`
*   **Discrepancy Description:** a write timeout while answering after a handler failure is swallowed as "Request timed out" at DEBUG; the handler's ERROR line is lost.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid and rare, but the failure is silent. Fix with Issue 1: log the handler failure (kind only, no message) at ERROR at the point it happens, and make `handle_error` skip a second line for the same failure (one flag), so there is exactly one ERROR line per failed request.
*   ***Proposed Edit:*** log inside do_POST on handler failure, then re-raise; test with a peer that stops reading and a failing handler; check exactly one ERROR line.

### [Issue 3] [`codebase-details`] - minor (m3)
*   **Affected Scope:** tests/test_q8a2_callback.py:784
*   **Discrepancy Description:** `_plain` test misses \x7f, U+2029, bidi (U+202E, U+2066) and U+200B.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid; a mutant that swaps `isprintable()` for a hand-written range would survive. Add the characters and a mutant for it.
*   ***Proposed Edit:*** add those characters to the test string; expect `?` for each.

### [Issue 4] [`codebase-details`] - minor (m4)
*   **Affected Scope:** receiver.py:195-197
*   **Discrepancy Description:** the error-kind chain is unbounded (a `__context__` cycle loops forever; a long chain makes a long line).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid; python normally prevents cycles but a hand-built one is possible. Bound at 5 kinds and stop at a repeat (seen-set), append `...`.
*   ***Proposed Edit:*** loop with seen-set and cap; test with a cycle and with a 10-long chain.

### [Issue 5] [`codebase-details`] - Nit (n1)
*   **Affected Scope:** receiver.py:67-68 docstring "the outcome is audited and the outcome is audited"
*   ***AI Suggestion:*** PROPOSE FIX (trivial wording fix, worth it)
*   ***Proposed Edit:*** one sentence: "the outcome is audited, and tick updates the channel message".

### [Issue 6] [`codebase-details`] - Nit (n2)
*   **Affected Scope:** receiver.py:121 over-long docstring line
*   ***AI Suggestion:*** PROPOSE FIX (ruff format leaves it; wrap by hand)

### [Issue 7] [`codebase-details`] - Nit (n3)
*   **Affected Scope:** `log_message` drops the client address
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** adding the peer address puts a personal identifier in logs, against the repo rule to keep personal data out of logs; hang-ups are correlated by time. Recorded, not fixed. Evidence: CLAUDE.md "Mask personal data ... before it reaches ... a log".

## Handoff
Accepted fixes: 6 (m1-m4, n1, n2). Contested: 0. Escalated: 0. Declined: 1 (n3). Unaddressed: 0. Gate: independent evidence on the final head (runner a4b5e2ea covers 3210f93a; delta evidence needed for the batch 4 push), non-security path, no new review for minors.
