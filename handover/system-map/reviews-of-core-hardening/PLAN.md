# PLAN for ORDER 005: independent cross-review of core-hardening (version 1)

Target (read only): branch `cloud/core-hardening`, folder `handover/core-hardening` (MASTER-MAP.md 800 lines, AUDIT-FINDINGS.md 587 lines with 150 findings: 5 Blocker, 80 Major, 65 Nit; patches/; result reviews). The target audited commit `b4cce5b` of the core; `git diff b4cce5b origin/cloud/core-hardening -- src demos tests` is empty, but my own branch is on a later base (22 files in `src/` differ). So all code is read from a snapshot of `b4cce5b` (scratch folder `snap/`, made with `git archive b4cce5b`). A claim that holds at `b4cce5b` may be stale at today's head; that is stated in REVIEW.md, not checked line by line.
I am the independent reviewer: judge, do not defend. Static only: no program is run, no network, made-up data.

## Goal and outputs (in `handover/system-map/reviews-of-core-hardening/`)
REVIEW.md (verdict first, failures first), CORRECTIONS.md (exact fixes to the target), LEDGER-ROWS.md (9 columns: id | source | severity | area | summary | status | fixing artifact | verified-by | date).

## Method (tool ladder: no code needed beyond small checks; reading agents do the work)
1. Verify: every Blocker (5) and at least half of the Majors (target: at least 50 of 80) against the real file:line in `snap/`. Verdict per finding: CONFIRMED / WRONG / UNVERIFIABLE with one line of evidence (file:line and a quote of 6 to 120 characters). Slices: V1 lane A and X (2 Blocker, 22 Major), V2 lane B and D1 (1 Blocker, 14 Major), V3 lane C and D3 (1 Blocker, 27 Major), V4 lane D2 (1 Blocker, 17 Major). Each verifier checks all Blockers and Majors of its slice if time allows, minimum the Blockers plus 60 percent of the Majors, chosen by a fixed rule: odd ids first, then the rest (so the sample is not hand-picked by the author's order).
2. Misses (what the target did not find): H1 hunts vendor SDK imports outside kind modules, stage names other than demo/pilot/prod, least privilege (roles, wildcards, long-lived keys), secrets and hardcoding in `src/` and `demos/`; H2 hunts dead or idle modules (no importer outside tests), duplicate stores, engines and filters, and a second source of truth for core modules in `demos/`. Each lists candidates only if it can quote file:line; each says what it did NOT read.
3. Verdicts and cut list: V5 re-checks the target's one-place-per-job verdicts and cut list (AUDIT-FINDINGS sections 4, 5, 6, 7 and the lane verdict columns): a NEEDED item called DUPLICATE or the reverse; any item proposed for deletion instead of archive; an item with a caller proposed for archive.
4. EVIDENCE RUNNER (separate sonnet agent, runs and records only, never judges): runs `tools/check_citations.py`-style quote check of every `path:line "quote"` in the target's AUDIT-FINDINGS.md and MASTER-MAP.md against `snap/`, and a count script (findings per lane and severity versus the target's own table). Raw output saved in `work/evidence-ch-1.md`.
5. Merge: I write REVIEW.md, CORRECTIONS.md and LEDGER-ROWS.md from the agents' files and the evidence; unverified agent reports stay UNVERIFIED until I have checked a sample of their CONFIRMED lines myself.
6. Result review: two or more fresh `egm:*` reviewers of different types (codebase-details, zoom-out, design, comprehension) read REVIEW.md, CORRECTIONS.md, LEDGER-ROWS.md plus the evidence file, never my verdict alone; then `egm:egm-resolve`; at most 2 rounds.
7. Drift check (`egm:egm-drift-report`) of numbers in REVIEW.md against the evidence, then FINAL block in REPORT.md, commit and push to `cloud/system-map`, stop.

## Rules for every agent brief
Starts with `STUDIO-PREAMBLE v1`, `EGM-GATE v1`, `CODE-LAST v1`, and a MUST-NOT list: no edits outside the agent's own output file under `handover/system-map/reviews-of-core-hardening/work/`, no commands that change the repository, no network, no secrets, no live model calls, no deletion, no push, no unbounded loops. Model set on every Agent call (sonnet-5-5). Time box 45 minutes; a checkpoint note every 20 minutes. Every report starts with what was not checked.

## Ladder line
Rung 1 reuse: the existing citation checker from ORDER 002 is reused. Rungs 2 to 6 not needed. Rung 7 (custom code) only for the count script.

## Stop rule
Result round 2 is the last; after it only Blockers and Majors get a pass, Nits are fixed in the same push. Hard stop 09:30 UTC (15:00 IST).
