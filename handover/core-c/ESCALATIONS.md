# ESCALATIONS of core-c (newest on top)

## E4. Fold G1: one test fails because two input heads give `has_mixed_script` opposite rules (2026-11-20T05:47Z)
- Item: BUILD G1, tries 1. Branch wip/cloud-core-c/g1-fold (pushed, 5 commits on main 51c9fc4, tip 8e4d234). Raw output: evidence/G1-fold.md.
- Failing test (NEW, not edited): tests/test_textnorm_round1.py::test_m16_a_spacing_mark_or_modifier_symbol_does_not_split_a_mixed_script_word, `AssertionError: assert (True is False)` for `has_mixed_script("ab" + U+0903 + "cd")`.
- Cause: P1a fix8 (only on rebase/P1b-o140) flags a Latin word with a foreign spacing mark as mixed script (its rule b); fix round 1 item M16 (only on core/P1b-fixwip) wants it NOT flagged. The two heads never met. The fold keeps fix8.
- Batch result with that one failure: 1 failed, 8616 passed, 17 skipped (67 test files, 3 workers, 245 s); perf file 17 passed.
- Options: (a) keep fix8's rule and change that one test clause to fix8's answer (recommended by the builder and by me: flagging is the stricter side); (b) drop fix8 rule (b).
- Not tried: no change to the test or to either rule (a test is never edited to get green without the lead). Whether the test also fails on a head: UNVERIFIED, no head was run.
- Also for the lead from the same build: Python 3.12.3 carries Unicode 15.0.0 (measured), 3.13.18 carries 15.1.0: the fold's start-up check refuses pilot and prod on 3.12. And `contains` now finds MORE than main when an invisible character (U+200B, U+00AD, U+2060) sits between a letter and its accent (pinned by a named test).

## E2. The gate's mask check would refuse normal traffic as the producers work today (2026-11-20T05:31Z)
- Item: step F, ticket review round 1, finding cb-1-B1 (tickets/F-review-1.md). Not a failed try: a design conflict found by reading, nothing executed yet.
- Fact 1: tool inputs are masked leaf by leaf (guard/runmap.py:588-598) but sent as one composed JSON string (runtime/agent_loop.py:574-577; k1b/loop.py:147, 214). A key and a value that are each clean can match a pattern once composed.
- Fact 2: the run map grows after each tool result (agent_loop.py:513, 534); the document and earlier messages were masked with the smaller map and are re-sent unchanged (470-476). A later-found value that also occurs earlier makes the re-check say "unmasked".
- Effect: "mask failure means no call" (plan-v3 A3) would stop real runs, or the check must be weaker than the plan says.
- Options: (a) SPINE masks the composed string and re-masks earlier text when the map grows, in the install change; (b) the gate treats these two cases as a documented limit; (c) the gate masks instead of checks (the plan forbids a new map, not a write to the caller's map: lead to decide).
- My recommendation: (a). It keeps the guarantee as written. Gives up: more edits in SPINE's files.
- What I do meanwhile: build the module with the strict check and a test group that pushes real producer output through it, so the lead sees measured refusals instead of this reading.

## E1. One-minute board cron could not be created (2026-11-20T05:20Z)
- Item: ORDER 003 item 1, session cron `* * * * *` for the board.
- Tries: 2 (05:20 UTC and 05:22 UTC, CronCreate tool). Stopped at 2, not retried a third time.
- Exact error both times: "Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Destructive or Unwanted Actions]."
- Cause as I understand it: the session's own permission layer refuses a recurring every-minute job. This is a control of the cloud session, not a fault in the repo.
- What I did instead (the fallback the order itself gives for "no cron tool"): a board script renders, commits, pulls --rebase and pushes the board at the end of every tool batch.
- Gap this leaves: when I am only waiting for background agents and run no tool, no board is pushed. Boards can then be older than 1 minute.
- Not tried on purpose: a background shell loop that pushes every minute. That would go around the denial (ORDER 003 item 4: do not work around a denial).
- Needed from the owner: allow the cron in this cloud session's permission prompt/settings, or accept boards per tool batch.
