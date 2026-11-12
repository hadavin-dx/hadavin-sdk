---
name: egm-review-routing
description: "HARD RULE (owner 2026-11-01, said three times): every task and every agent follows EGM in sequence: brainstorm/draft -> EGM plan review -> build -> evidence runner -> EGM result review by egm:* agents -> resolve -> repeat -> drift report; hook enforces the brief; no skipping for urgency"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-01T14:25:31.224Z
---

Owner 2026-11-01 (three messages): "make sure we are using EGM for all of them perfectly, even for new agents and their tasks"; "everywhere it is better or needed or gives better results, only things that really are not needed may skip it; whatever until now we haven't used, use EGM for them to double check; every task uses EGM in sequence; keep it a very hard rule in memory, guardrails, wherever needed; no agent should skip it"; "EGM must be for all of them, in sequence every time, not even one agent missing or making a mistake."

**What went wrong (admitted):** most code reviews were first run by `general-purpose` agents with the preamble instead of the `egm:*` reviewer agents; the EGM skills were not invoked through the Skill tool; the synthesizer returns before its reviewers finish (harness quirk), so the lead must collect the reviewer reports and run `egm-resolve` itself. Reports were saved in `egm\<topic>\` but the sequence was not followed.

**The sequence (every plan, design, document, script, config, infra/cloud/DNS action, client-facing text, non-trivial code change, and every new agent task):**
1. New idea/design: `Skill egm:egm-brainstorm`, then `egm:egm-draft` (Opus 5.5).
2. EGM review of the PLAN/DESIGN before building: `egm:egm-review-loop` (small) or `egm:egm-review` (big), then `egm:egm-resolve`.
3. Build (Sonnet 5.5).
4. EVIDENCE RUNNER (general-purpose agent; brief says "EVIDENCE RUNNER"): runs tests, mutation checks, hostile inputs; saves raw output to `egm\<topic>\evidence-<n>.md`; never judges.
5. EGM review of the RESULT by `egm:*` agents (`egm-design`, `egm-codebase-details`, `egm-implementation-readiness`, `egm-structural`, `egm-style`, `egm-comprehension`, `egm-zoom-out`) reading diff + spec + evidence. They have Read/Grep/Glob only, so the lead saves their reports to `egm\<topic>\`.
6. `egm:egm-resolve`; fix all blockers/majors; repeat 5 until a fresh pass finds none (security, money, redaction: no round cap; other paths: 2 rounds unless the owner says more).
7. `egm:egm-drift-report` before "done" and after each merge batch.
Skip only for a typo, a status check, a read-only question or a one-line mechanical edit, and write "EGM skipped: reason".

**Guardrails in place (2026-11-01):** (a) `templates\agents\BRIEF-PREAMBLE.md` rule 13 `EGM-GATE v1`; (b) PreToolUse hook `<studio>/tools\hooks\agent_preamble_gate.py` denies general-purpose briefs lacking the preamble or `EGM-GATE v1`, and denies general-purpose briefs worded as independent reviews unless they say `EVIDENCE RUNNER`; (c) global `~/.claude/CLAUDE.md` and studio `CLAUDE.md` hard-rule blocks; (d) bible R374; (e) this memory; (f) the prompt-gate hooks that print the EGM reminder on every prompt.

**Backlog:** work done before this rule without the full sequence is re-run through EGM (list in `egm\egm-backlog-2026-11-01.md`).
Related: [[egm-for-every-plan]], [[reviewer-independence]], [[class-level-fixes]].
