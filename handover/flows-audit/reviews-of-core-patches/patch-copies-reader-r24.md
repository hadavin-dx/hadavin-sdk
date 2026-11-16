# patch-copies README.md + DEAD-MAN-CHECK.md pass 24 re-read (agent aeb0421e, egm-design), security path, uncapped
Saved by flows-audit, condensed. Reviewer words unverified; static. Read README 14-35, 276-289, 345-524, 730-733 and DMC line 485 only. NOT read: DMC 241-444, README 1-13, 36-275, 290-344, 525-729, bodies of E/need_w/gates/setup/keep_logs/cleanup, patch bodies (grep only). 0 Blockers, 0 Majors, 6 Minors. No path found printing PASSED/ADDS NO NEW FAILURE/FINAL while a step failed. pwant/pnames/pcheck sort keys agree; function order ok; DMC exit-code table and signal numbers right.
M1 README 483-484: proof's cleanliness check refuses `.hypothesis/` that `ut` (363) allows; fail-closed. Fix: grep -v '^\.hypothesis/' in 483.
M2 README 402: stamp computed after clauses (a)-(e) read the files; take s0=$(sg "$W/patched") before (a) and require equal at 402.
M3 README 364, 453-454: unpatched clone not in stamp; text at 453 omits hf and vs_ok from needed functions. Optional: hash unpatched clone into proof.txt line 2, final rechecks.
M4 README 507: "run the functions verdict and proof first" also printed when proof refused via vs_ok; reword to "read the STOP line printed by proof".
M5 Wording: row 21 lacks "not a merge clearance"; "cannot occur today" -> "at commit b4cce5b"; lines 359/426 say "print clause (f)" but no line begins "(f)" (PROOF OK then FINAL:); line 17 "three names" then "fourth case".
M6 README 418-421: if stamp write fails the screen still shows PART 1 OF 2 PASSED/ADDS and exit 0; set ok=0 on failure.
Fixer claim (fix-patchcopies26 scratch tests) unchecked; whole recipe never run.
