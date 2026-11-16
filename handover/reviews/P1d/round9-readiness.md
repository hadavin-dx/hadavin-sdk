# P1d rev9 / P1d-learn rev2 / P1d-gate rev2, round 9 readiness: 1 Blocker, 9 Major
B1 row H25 (password=SV_A+ESC[1m+SV_B) cannot be withheld by the algorithm (SV_A 5 chars < min_key_chars 8, no residue found): give row a known first half or move to P1d-learn.
M2 pseudocode redact_text/_withhold catch bug: _withhold inside try, its raise is caught (double log, class name lost, exc=None for size). Call _withhold outside try or re-raise handled.
M3 existing tests break and not listed: test_s6_approvals (_request lacks save_plan -> card_withheld), test_k5_fixes2:96-116 (261000-byte doc vs 30000 default, validator refuses MAX_REDACT_CHARS).
M4 fail-before harness undefined (p1d_api, marker p1d, NEW_SURFACE:/LEAK: prefixes). M5 hypothesis not a dependency (claim 0 new dependency). M6 row classes wrong: MP-4 and F20 are fb not pb; undecided classes H17k, "pb?" rows, H29a.
M7 rows not self-contained: C01-kv..C10-kv (only C01, C08 spelled), H12a-d-kv, H21-kv Cyrillic placement, F02/F02b/F14/F19 no literal, LK-UNFOLD either/or, S1-S5 no argument form.
M8 no row/mutant for the standalone leg (known EMAIL/NAME split copy via standalone_hit on views b1/c/d); deleting that branch fails no test.
M9 folded sweep: pass must run on fresh _PLACEHOLDER split / pre-replacement segment with offsets; overlap rule vs written placeholders.
M10 caller table gaps: SlackChannel.notify (slack_channel.py:197), cards<->requests import cycle (function-local import), unused card_withheld_text(inputs=True), FakeChannel.update tuple, withheld send repeats on sweep escalation.
Minor: M60/M26/M6 mutant issues; counts (55 vs 49/52 mutants; 424 lines); line refs off by one (redact.py:897, agent_loop.py:382); BS-0 lettering gaps, BS-2 absent; P1b names not on branch; SUM/C test-name collisions between P1d and P1d-learn; finder cache pattern form unspecified; _views.py unused names; clean step 2 snapshot undefined.
P1d-learn: test_marker_means_rule_runs undefined; M54 killer undecided; FLOOD keys unspecified; H37 prefix. P1d-gate: canary placement vs existing refusals, spy targets, pilot_cfg config, C-LEARN depends on one digit in 2-7.
