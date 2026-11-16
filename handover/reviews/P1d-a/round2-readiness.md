# P1d-a rev 2 plan review r2, egm-implementation-readiness (a5a3316c), redaction path
Verdict 0B/8M/7N. Decisions concrete; harness left to builder.
M1 BS0 cells: rule/hard stop ambiguous (pb row whose base differs; fb row whose base equals expected; L8/T1 expected = BS0 string; who copies BS0 outputs into tests/fixtures/p1d_cases.py). Say a BS0 row is a STOP if it does not fit its class.
M2 tools/p1d_corpus.py --rows/--freeze-gate by name only; input/output format, D3a-d on base, bs0-base.txt format, base-worktree commands (PYTHONPATH=<wt>/src), copying tests, pytest call.
M3 Evidence paths/working trees mixed (core/P1d-a from main vs handover worktree); use /home/user/hadavin-sdk-handover/handover and /home/user/build/<TICKET>; qsubmit.sh absent, log ends exit=<rc>.
M4 Mutants lack file/symbol/exact edit and registration with tools/mutation_runner.py; A15 "Q2 or written equivalence" decide now; missing mutants for ~~~ body/info string defang threading, D2 `#`/whitespace terminators, defang_text closer line, D3 wide dots.
M5 test_card_masks_what_model_masks cannot read the card map (channel.clean mapping local, alt branch joined_map).
M6 C-AMP under-specified (alphabets, tail, H34 shape, leak measurement rule, over-mask/longest-run computation, which path, --kind selection).
M7 D3 "exact" test cannot see the defect (_DOMAIN lookbehind blocks `.example.com` after a dot); relabel best effort or add oracle for `.` after placeholder; wide dots after D3.
M8 Literal-form ambiguities: U+200B in Z1-Z3, W1 `|` escape, per-path base strings for H27/H34.
Nits: stale refs; name D3 constant; property test time bound/marker; rows without mutants intentional; accepted un-defang of typed `[.]`; dblink-connect known failure; template fields.
Not checked: base commit, tools/mutation_runner.py (not on disk), qsubmit.sh, any run.
