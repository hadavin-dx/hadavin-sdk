# QUESTIONS from core-c
(Each has what was tried and a recommended answer. None stops work: the session goes on with the recommended answer and marks it in the ticket.)

1. P1c ("redactor gaps") has no branch or PR: `git ls-remote` shows no core/P1c, and PLAN-READBACK.md section 8 found no PR number in plan-v2, v3 or v4-final. Which head holds P1c, or is it to be written new from a list of gaps? An agent is searching the old plans (tickets/G-survey-P2d-P1d-P1c.md). Recommended: the lead names the head or the gap list.
2. "P2d-1 on" in step G: does it mean "stack PR #77 on top of the P1a+P1b fold"? Recommended: yes (the survey checks whether #77 already contains the P1a/P1b commits).
3. How does the gate wrapper get the caller's run map? `LLM.chat` and the plan's `bind(agent_id, run_id)` carry no map. Recommended: `bind(agent_id, run_id, *, mapping)` (ticket F open question 1).
4. Module path and class name of the wrapper: recommended `src/hadavin_sdk/guard/model_gate.py`, class `ModelGate` (SPINE needs it for the installs and MODEL_CALLERS).
5. The exact target sentences for the G5 wording are in no frozen-plan file. Recommended: I propose the sentences in ticket G and the lead approves them there.
6. Build order of our two steps: plan-v3 says text then gate; plan-v4-final lands F before G. Recommended: check-only mask function first (F needs it), then F body, then the rest of G.
7. plan-v4-final B1 says "receipts 0008 only if G proves a delta": this reads as a slip for H. Recommended: read it as H.
8. Settle amount when the provider refuses a call (ticket F open question 2): recommended worst case for every exception.

## Added 06:15 UTC after the P2d-1 port (G3). Work continues with the builder's choice in each case.
9. G3, a code change beyond a straight port: under the fold's algorithm (fold5) dashes, the minus sign, curly quotes and the fraction slash fold to ASCII, so P2d-1's rule withheld every line holding an em dash or a curly quote plus a fold hit. The builder made dashes and curly quotes ordinary typography (a value beside them is masked in place) and refuses three slash look-alikes (U+2215, U+2571, U+29F8). 30 code points differ from P2d-1 (table in evidence/G3-p2d-port.md). Simpler options not taken: keep them all withheld. Recommended: accept, but this is a redaction rule: lead please confirm.
10. G3 edited one of P2d-1's own tests (`test_dm_2_257_decomposed_names...`): on the fold an NFD name takes no decoded-mask slot, so the old expectation (257 names raise InputTooLarge) no longer holds; the test now uses names with a full-width letter for the same 257/256 edge and also asserts that 257 plain NFD names are all masked. No expected output value changed elsewhere. Confirm.
11. G3 changed four fold-head record tests because the port adds one public name and two textnorm users (redact.py, runmap.py): the "no module builds its own views" test gets an exemption row for redact.py; "textnorm not in runmap.py" becomes "imports exactly without_spacing_marks"; public names 33 -> 36. Confirm the exemption row.
12. E5: add BEARER, BASIC and `authorization:` to the G7 re-run set (recommended), or state the limit?

