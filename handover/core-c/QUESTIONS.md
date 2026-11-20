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
