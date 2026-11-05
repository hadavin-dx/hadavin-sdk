---
name: review-loop-speed-rules
description: "Owner 2026-11-02: reviews take too long; lead applies a round cap, batched fixes, parallel evidence+review, sampled mutation, max 4 heavy jobs"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-02T12:41:57.161Z
---

Owner asked (2026-11-02) to find why the whole pipeline is slow and fix it.
**Causes found:** (1) every PR looped evidence -> review -> fix -> evidence 5-8 times because each fresh reviewer finds new minors; the studio cap (non-security paths max 2 rounds) was ignored by treating almost everything as security; (2) one shared laptop overloaded by 8+ agents, so full suites took 20-30 min, mutation runs hours, timing tests flaked and had to be re-run; (3) design rounds for Jagrat ran to v14; (4) evidence re-run in full for tiny deltas.
**Rules from now (lead applies them):**
- Round cap: security/money/redaction paths are uncapped; every other path max 2 review rounds. After round 2 only blockers and majors get another pass; minors are fixed in the same push without a new review and listed in the ledger.
- Batch: a builder reports once when ALL findings of a review are fixed; no review of intermediate pushes.
- Reviewer starts in parallel with the independent evidence runner (reads builder evidence + diff), then reads the independent evidence when it lands; no waiting.
- Delta evidence: full suite + lint once on the final head; mutation runs = only changed/re-pointed mutants + a 60-mutant sample; the full mutation run only once per PR on the final head, alone.
- Max 4 heavy jobs (full suites, mutation, load, Docker scans) at once; timing/perf tests run alone.
- Design docs: stop after the round with 0 blockers; remaining majors become build-time fixes.
**Why:** quality stays (independent evidence + fresh reviewer before every merge) but the number of loops drops. **How to apply:** state the round number in each brief; refuse a new round for minors. Related: [[egm-review-routing]], [[blocker-ledger-rule]].
