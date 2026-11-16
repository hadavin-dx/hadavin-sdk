# Q8a-1 batch 13 PR notes (head: see GATES.md)

## Not done or not run (first)
- 12 older allowance reasons have no check by code yet (pinned list `UNCHECKED` in tests/test_guard_reasons.py, may only shrink): PROC, CARD, LLMREQ, NUM, STOREID, URL, BUNDLE, KIND, PKGERR, MODELTEXT, REDACTED, NUMFIELD. Reason: each claim needs the declared type of a field or a data-flow fact that the AST cannot show; next step is a type-aware check (resolve annotations through typing.get_type_hints per site). REDACTED stays tied to owner question q-q8a1-hide-ids.
- Whole-file settings models and StrictConfigModel (task 6): impossible to unify. A before-validator that raises aborts the whole model, so the other problems reported next to it are lost (the "dev renamed to demo" sentence and `<unknown key>: Extra inputs are not permitted`). I tried it: 12 tests failed (tests/test_stage_names.py and tests/test_p1b_backends.py), then reverted. Both paths already hide the typed key; a property test over every forbid-extra model pins that.
- Executor `http_418` pin and gate-line tests (tests/test_q8a1_b13_live.py) need conftest fixtures, so they have no mutant (stage_mutants runs with --noconftest).
- About 50 other `# noqa: BLE001` remain in src (agent_loop, chain, local_dir, requests, cli, tools, others): fail-closed handlers outside this brief. tick.py is clean.
- Guard finding: the guard resolves callers by function name, so a local variable called `probe` made audit/signer.py newly unsafe. Renamed in tick.py; the name-based resolution is not fixed.
- Issue 12 (ConfigName type) stays an owner question.

## What changed
- All 164 UNREAD rows read; UNREAD removed. Reasons are claims checked in tests/test_guard_reasons.py (21 new categories plus GEN, STATE, DIGEST, TIME, SIGN, CLASSNAMES, SEQ, BUILT, KEYVER, MIGNAMES, FIELDS, ARG now checked; SQL and PATTERN had no rows and are gone).
- errors.Failed replaces the broad handlers in errors.call_class_only, llm/retry.py and runtime/tick.py (no cause, no context).
- Fixes: status_text, egress host cut, provider error detail filter, Route.model_id pattern, cli gate line shown_name, signer_vault status through status_text.
- Checks found real defects: signer_vault printed a text status; the CLASSNAMES row for the detector log was wrong (the line prints the detector message, redacted: relabelled REDACTED).
- New guard sites count: new guard sees 539 sites (512 distinct keys), c6028abb guard 162 (160) with no allowances, difference 377; against the new src the old guard finds 6 sites outside its table and 7 stale rows.

## Fail on old (0e7da095)
Evidence: /home/user/build/B-Q8a1-b13-fail-on-old.txt (8 of 33 fail), -guard.txt (4 clean rows fail), -tick.txt (3 of 6 fail: no BLE001 in tick, transit status text). The others pin behaviour that already held.
