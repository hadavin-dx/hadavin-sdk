# P1d-a builder report (saved by the cloud session, condensed from the hand-back)
Head 6875f27948513d5a8f81d71cee84037a103fbfa3 pushed to origin/core/P1d-a. No PR opened. Builder-only evidence: NOT independent, no EGM review yet.
## Failed / not run
1. Mutant run (50 mutants incl. A15, A44, A45) NOT RUN (no heavy slot in 30 min). A15 verdict (killer K41q) unknown. Command: `/home/user/build/heavy.sh <log> /home/user/build/venv-p1da/bin/python tests/p1d_a_mutants.py` from /home/user/build/WT-P1da.
2. Two builder properties FAIL on the build (not edited): test_stored_card_round_trip 29/2000 fail (137 on base; minimal case `m@e.na.@l.ln` -> `<EMAIL_1>.@l[.]ln`, Slack's second redaction gives `<EMAIL_1><EMAIL_2>`: e-mail pattern not idempotent; outside P1d-a scope); test_no_link_outside_code_on_card 35/2000 fail (222 on base), all with a backtick (gate reads inline code per line, CommonMark per paragraph; pre-existing gap). tests/test_p1d_a_rows.py: 94 of 96 pass.
3. BS-1 over-mask corpus (635 samples) exits 4: 2 of 268 S5x samples over-mask by one `;` where the secret ends in an HTML entity name (&ne;, &ge;).
4. Not done: BS-0 step 6 grep not recorded; step 7 (two P1d V8 fuzz tests) not read; step 8 (WHATWG 5.1) UNVERIFIED per ORDER 192; LIT collected only 18 strings; no Python 3.12 run, no evidence snapshot worktree, no pip-audit/semgrep/zizmor/gitleaks/Trivy; ORDER 192 ticket text edits only listed in the build notes; full-suite log has no exit= line.
## Ticket corrections needed
ALPHABET-A has 72 entries (ticket says 63), ALPHABET-B has 66 (ticket says 57). BS-0 L9 and L8 fixed (see notes). New rows K41 (card, model) and K41q (model); mutants A44 (killer K41 model), A45 (killer K41q model); A15 assigned killer test_row_K41q_model.
## Deviation needing the lead's yes
`_defang_prose` starts with `_LEGACY_DOT.sub(".", part)` so defang_text is idempotent; side effect: clean() shows a typed `[.]` between name characters as `.` (matches ORDER 192 item 3; CHANGELOG lists two examples).
## Results (builder's commands, /home/user/build/WT-P1da)
BS-0 on base: all 89 row cells FIT. Fail-before on base: 61 failed, 35 pb rows passed. Full suite on head: 10174 passed, 454 skipped, 28 deselected (259 s). Gate/redaction/K5 tests: 4545 passed, 3 skipped. test_k5_perf -m perf: 8 passed (0.03-0.05 s hostile inputs). ruff, ruff format --check, bandit -ll on src clean.
## Files
Modified: approvals/gate.py, channel.py, slack_channel.py, guard/redact.py, CHANGELOG.md. New: tests/fixtures/p1d_cases.py, tests/test_p1d_a_rows.py, tests/p1d_a_mutants.py, tests/fixtures/p1d_a_base_rows.json, p1d_a_gate_base.json, tools/p1d_corpus.py. Evidence: handover/evidence/P1d-a/ ; notes handover/studio-notes/bd-P1d-a-build-notes.md and bd-P1d-a-checkpoint.md.
