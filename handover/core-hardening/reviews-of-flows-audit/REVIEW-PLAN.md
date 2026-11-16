# REVIEW-PLAN v1 (ORDER 005 task A): independent cross-review of branch cloud/flows-audit
Reviewer role: independent. I did not write the target. Static only: no n8n, no network, made-up data. Target copy (read-only, outside the repo): scratchpad/fa (git archive of origin/cloud/flows-audit at its current head). Ladder line: rung 1 reuse (no new tooling; plain git, python3 stdlib, jq-like json parse); n8n flows are rung 3 and are never called wrong here.
## Goal
Answer for the lead: can the take (flows in handover/demo/n8n-flows-real-v5 and n8n-flows-film-v5) trust FINDINGS.md, FIX-PLAN.md, CUT-LIST.md and patches/? Which claims are wrong, what did the audit miss, can any patch break the take?
## Checks (each has an owner and an output)
C1 Citation check: every Blocker (F-001, F-002) and at least half of the Majors (22 Majors; check at least 12, chosen so every flow file and every patch is touched): cited file:line against the real file: CONFIRMED / WRONG / UNVERIFIABLE with a raw excerpt. Output: evidence-A1.md (EVIDENCE RUNNER, never judges).
C2 Flow dump: for mf-hook, mf-form, mf-recovery, mf-sub-crm-mail in real-v5 and film-v5: node list, connections (main output 0 and error output), onError and retry settings, the Claim and ClaimStuck SQL text, alert nodes, mail nodes. Output: evidence-A2.md (EVIDENCE RUNNER).
C3 Patch check: each of the 5 patches `git apply --check` on a scratch git copy; after applying F-002 re-run the rebuild command from V5-README if it needs only python3 stdlib; parse the produced JSON; diff node/connection sets. Output: evidence-A3.md (EVIDENCE RUNNER).
C4 Idempotency trace (reviewers): same lead key twice gives one processing (the claim INSERT conflict rule); empty key; Postgres down; retry vs 422/503 contract; lease 45 s and ClaimStuck; alert cap; mail node on error. Done by egm:egm-design against flow JSON plus evidence A2.
C5 Patch-could-break-the-take (egm:egm-design plus egm:egm-codebase-details): for each patch, what node/connection/column/environment variable changes and what the take run would hit.
C6 One-place-per-job verdicts and CUT-LIST: a NEEDED item called DUPLICATE or the reverse; anything proposed for deletion instead of archive; referrers still named by live documents (egm:egm-zoom-out).
C7 Missed items: what no finding covers (egm:egm-zoom-out and design).
C8 Plain wording of FINDINGS short answer and FIX-PLAN (egm:egm-comprehension).
## Agents (register in REPORT.md before each start; 60 min box; model set on every call)
P1 plan reviewers: egm-design + egm-implementation-readiness, sonnet, read-only (via egm:egm-review-loop skill).
E1 EVIDENCE RUNNER (general-purpose, sonnet): C1, C2, C3 in one run, raw output to evidence-A1..A3.md in this folder. MUST-NOT: edit outside reviews-of-flows-audit/, edit the target copy, call network, judge or rate.
R1..R4 result reviewers (sonnet, read-only, parallel after E1 lands): egm-codebase-details (C1, C3, C5), egm-design (C4, C5), egm-zoom-out (C6, C7), egm-comprehension (C8). Max 2 result rounds.
## Outputs (this folder): REVIEW.md (verdict first, failures first), CORRECTIONS.md (exact fixes to the target), LEDGER-ROWS.md (9 columns: id | source | severity | area | summary | status | fixing artifact | verified-by | date), result-review-*.md saved copies, result-resolve-*.md, then FINAL block in ../REPORT.md, push, stop. Task B (ORDER 002 part 2) only after task A is pushed.
## Stop rule
No Blocker or Major left open in my own review; unverifiable items named with the next step. Honest limit: n8n semantics (retry, onError wiring, Postgres ON CONFLICT behaviour inside the n8n Postgres node) are checked by reading the JSON, not by running it; those parts are marked UNVERIFIED.
