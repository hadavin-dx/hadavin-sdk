# patch-copies round 8 stranger read (agent a0dfe64), uncapped. Saved by flows-audit, condensed. Reviewer words unverified. Did not read .patch files, ci.yml, src cites, REVIEW.md beyond 1-12. Nothing run. R=README.md, D=DEAD-MAN-CHECK.md.
B1 R:5-8 "apply nothing" above R:87 "recipe runnable": add one top sentence: running the recipe on a throwaway clone is allowed; applying to the repository is not. "apply" undefined (C1); R:3 "nothing changes src/tests" should say "in your repository" (C2).
B2 R:89-101 SRC GitHub URL and `git fetch origin $SHA` may be refused for a bare SHA; no fallback or failure message; local path fallback exists only on the writer's machine; P= absolute path not flagged to change.
B3 R:154 verdict script needs W, C and logs present: single-terminal warning only at R:87; repeat at R:148.
B4 R:166/177/188-190: baseline red and patched green gives NOT PASSED by script (a fails) with no explanation; state the case at R:190.
M3 R:5-8 uses lead, studio head, DEFERRED, C-01 extras, G5 before box R:18-45 defines them: gloss in the first paragraph.
M4 "this pass" used at R:74,193,210,230,235 with different meanings: replace by pass numbers. Unmarked UNVERIFIED: R:226 pydantic message "match=finite"; R:286 cli.py:216 same at both commits.
M5 D:12 "five names" vs shipped four names (D:5,33,81): say the four-name form was not run.
M6 D:70 PGSSLMODE/PGSSLROOTCERT for "that one command": show one runnable line with env prefix.
M7 D:72-73,135: secret location UNANSWERED blocks T2 and negative test (marked).
M8 D:95/100/102: one admin login enough or not: pick one sentence.
M9 R:26,56 / D:24: database administrator named human vs default "studio head": same person allowed? say.
M10 R:57 table "I" = fixer session: use "the fixer session".
M11 R:114 CI uses --no-build, local does not: README says gates match CI; reword.
M12 R:213/275 prices 0, 0.00, -1: say why 0 and 0.00 are two cases.
C6 D:22 T3 "apply A-01 only if D1 yes" omits README rows 5 and 6: add.
Pointers: R:15 two path styles in one sentence; REVIEW.md "item 3 of its list" 'DO NOT APPLY NOW' exists at REVIEW.md:142 as heading, possible mis-cite (R:6, D:3-4); R:36 lines 384-390 unchecked.
Non-expert verdict: mostly cannot follow the recipe without help (uv, terminal, P/SRC change, fetch failure, reading (b) FAILED, what to do on NOT PASSED; no "if this fails send file to X"). Minors: pass history R:15,199,229-238 inside instructions; D:13 2,000-character paragraph; green/red undefined; negative test D:168-171 no pass numbers.
