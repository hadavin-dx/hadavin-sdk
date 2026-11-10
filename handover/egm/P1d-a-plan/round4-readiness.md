# P1d-a plan pass 4 (ticket rev 6) readiness review (egm:egm-implementation-readiness, agent a5e84e1d79580c078, Sonnet). Saved by the lead from the agent's hand-back.
Verdict: NOT READY to build. 4 blockers, 5 majors (reviewer read all 350 lines).
B1 K41 cannot be built or passed: row K41 "on base" cell equals its "expected after" cell, so the STOP rule (MISFIT/MISMATCH) halts BS-0 either way; no code given for the fix (Code shape keeps key `{0,40}` "unchanged"); the builder would choose regex, ReDoS bound and mutant text.
B2 A15 self-contradictory: line 226 "expected survivor", 238 "killer K41", 341 still open; removing the query lookbehind only adds masking so K41 cannot kill A15; decide equivalent with written reasoning or add a real killer; add a mutant for the new key bound, killed by K41.
B3 A44 and the AST choke-point test unspecified: no table row (48 rows, not 49); which functions count, per Return or per function, `_neutralise` must not end in defang_text, `_blocks` returns dicts, how a call is recognised, test file unnamed (mutant run runs only tests/test_p1d_a_rows.py).
B4 rebase protocol conflicts: "A7" undefined and collides with mutant A7; "stable" undefined; Depends line still says "no product dependency, ships first" (G3 fix failed); ORDER 230 queues P1d-a before P1b; ticket says builder edits no ticket text yet "replace the base sha in this ticket"; `0dabf1f` hard-coded; Risks row says four files, BS-0 lists five.
M1 build phases do not deliver "named tests green" (phase 2 rows need phase 3 wiring; FB1/FB2 belong in phase 2; many rows unplaced: give every row and property one phase).
M2 differential defined two ways (live calls vs frozen base clean outputs; fixture holds sanitise_text outputs only; G-TXT not frozen).
M3 row count stale (69 rows, fb 36).
M4 fixtures "built from parts" only for EM, SV_A, SV_B; REAL lines, hunter22 etc. unspecified; no action on a gitleaks/semgrep hit (reword, never suppress).
M5 K41 after-string unprobed (P6 did not cover it); why INFO-K41 uses hunter22 and K41 SV_B.
Nits: R0 reads stale after rebase; `seeded` in `_blocks` undefined.
