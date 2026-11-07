# STANDING ORDERS (lead, 2026-11-07, permanent until the lead writes "STANDING ORDERS LIFTED")
Why: the owner saw the cloud idle several times. Idle = the session ends its turn or waits for a lead message while work exists. These orders replace "wait for the lead".
1. NEVER END A TURN WITH WORK LEFT. If you have no lead order to act on, take the first open item of the BACKLOG below. Wait only inside a running tool call (queue job, builder), never by ending your turn.
2. Keep a self-pacing wake-up: at the end of every turn schedule your own next check in <= 8 minutes (cron/loop tool of your session) so you resume on the clock without a lead message. Heartbeat line by `date -u` at least every 8 minutes.
3. Agents are cheap, test slots are not: start a builder or reviewer for every independent item at once; only heavy test runs queue.
4. PUSH EVERYTHING: every checkpoint is committed and pushed to its own branch the same turn (branches core/*, handover). Nothing may exist only in the cloud working tree. At each heartbeat list any unpushed branch (should be none).
5. Report in questions-for-lead.md (qNNN) only what needs the lead or is a result; do not wait for an answer on the items you can continue.
6. BACKLOG (in this order; skip an item only when it is done or blocked by a named item):
   a. Fix batches + evidence + fresh egm reviewers for open heads: P1b (core/P1b-fixwip), PR 66 delta, PR 72, PR 73, PR 83, PR 80, PR 85, PR 86. Evidence runner and reviewer are different agents (EGM sequence).
   b. Plan A8 (plan-v4.1): write it from studio-notes/plan-v4-1-resolve-round1.md, then 3 fresh reviewers (design, readiness, comprehension), save reports in reviews/plan-v4-round2/.
   c. CI lint branch `core/ci-lint-set` (draft PR, own branch, NOT main): add pyright (or mypy), import-linter, actionlint, deptry, vulture to .github/workflows/ci.yml + pyproject, each with a licence line (SPDX read from the raw LICENSE), a trial run on main with the findings listed, and ZERO suppressions; fix findings in the same PR or list each as a ledger row.
   d. Own-meter 50-parallel test (T1) and ledger replay harness (T2: 6 min, 25 h, 31 d on the ledger layer with a fake clock) as test files on a draft branch.
   e. Ledger: append all review findings to the ledger the same turn; run the ledger check; list OPEN blockers.
   f. Cross-check the session handoff file (handoff/SESSION-HANDOFF.md on the laptop; you keep handover/STATUS.md) against reality every hour.
7. Honesty rules stay: raw output, no verdicts by evidence runners, slips reported plainly.
