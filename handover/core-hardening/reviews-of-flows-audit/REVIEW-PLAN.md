# REVIEW-PLAN round 2 (ORDER 013 item 1): re-review of branch cloud/flows-audit after its ORDER 007 changes
EGM: this is the delta plan on top of REVIEW-PLAN-r1.md (v2, reviewed in plan-review-1a, 1b, 2a, 2b, resolved in plan-resolve-2.md). Method, rubric and word list are unchanged; only the target and the questions change. Not re-reviewed as a plan (same method as a reviewed plan, time); say so in REVIEW.md.
RUNG: rung 1 reuse (git archive, git apply --check, python3 -I json). n8n flows are rung 3 and never called wrong. STATIC only: no n8n, no network, made-up data.
## Target (pinned)
Branch origin/cloud/flows-audit head 53079836 content (head f3c2225f only adds orders). Round 1 reviewed 35235ace (REVIEW-r1.md). Scratch copy: SCRATCH/new (now) and SCRATCH/old (35235ace), SCRATCH=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/r2. Deltas: patches-delta.diff, findings-delta.diff, fixplan-delta.diff there.
## Questions (ORDER 013 item 1)
Q1 Do the five patches apply to the flow JSON and generator (git apply --check on a copy of the checkout files; in my own checkout handover/demo/n8n-flows-*-v5 is absent, so the copy comes from the audit branch)? Q2 Do they break a connection (rebuild, then every connections source and target is an existing node, no orphan, no duplicate name, JSON valid, error outputs wired)? Q3 Are the new ratings and the Nit demotions justified by the one rating rule (impact times reachability today)? Q4 Anything missed, including the 7 items M1-M7 of round 1: are they now covered, rated right, or still missing? Q5 Is the new split BEFORE THE VIDEO / AFTER sound (order, 9 items, T-tests, estimate)?
## Jobs (parallel, all sonnet, registered on the board before start)
D = egm:egm-design (Q3, Q4, Q5). C = egm:egm-codebase-details (Q1, Q2 read from JSON, cites). E = EVIDENCE RUNNER (apply checks, rebuild, connection graph, cite check of the top 10, old-vs-new severity table); records, never judges.
## Stop rule
Max 2 rounds (non-security path). A verdict needs: verdict first, failures first, what was not checked. Corrections go to CORRECTIONS.md, ledger rows (9 columns) to LEDGER-ROWS.md.
