# P1 build-start correctness review (rev 16, FROZEN)
Status: REPORTED (saved by the lead session from the reviewer hand-back, condensed to the findings table; model output, not user authority). Reviewer read-only, nothing run, did not read reviews/ or evidence/. All traces UNVERIFIED. No shell; every Unicode count UNVERIFIED.
Verdict: builder CAN start; no Blocker; 2 Major, 5 Minor, 2 Nit.
| id | sev | ticket line | problem | fix |
|---|---|---|---|---|
| BS-P1-COR-1 | Major | 42,121,111(g) | Mutant #6 search string "ch not in FILLERS" occurs twice in 748849c textnorm.py (fold line 71, has_mixed_script line 165); runner replaces all occurrences (mutation_runner.py:257); meta-test (g) requires count==1, red before any run. Line 42 "no search string changes" is false for #6. | Give #6 a unique string (whole line-71 condition); re-derive for P1b; print "occurs once" in (g); run count over all 28 rows at P1a head (only 11 of 28 checked by eye). |
| BS-P1-COR-2 | Major | 107,202 | PIN-ENCL asserts "135 code points" with no exact predicate; generating script is in a review file builder is not given; builder may tune to 135. 8 runs sum 21+30+2+2+26+27+1+26=135. | Write exact predicate (regex + names-a-letter/digit/number test) in build notes; test also compares set with the 8 runs. |
| BS-P1-COR-3 | Minor | 151-154 | Evidence path flat; order 20(4) wants handover/evidence/<package>/. | Use evidence/P1m/, P1a/, P1b/. |
| BS-P1-COR-4 | Minor | 153 | gen_confusables.py --check cannot work (main takes one INPUT FILE arg). | Delete command; test 2068 covers regeneration. |
| BS-P1-COR-5 | Minor | 85-92,71-78 | No placement table: which of the 4 new test files each moved test goes into; only_test/test_file depend on it (rows 7,8,9,18,19-23,28). | Add placement table; builder sets test_file where killer not first file. |
| BS-P1-COR-6 | Minor | 74-77 | Moved code keeps hardcoded numbers (MAX_JUNIT_CHARS 8_000_000, TREE_KILL_TIMEOUT 60.0); testing/mutation.py ships in wheel; repo rule says thresholds from config. | State one decision: dev tooling exempt, or move numbers. |
| BS-P1-COR-7 | Minor | whole | File 334 KB > 256 KB read limit; ~40 KB history at top; coverage sentence copied at 6 places, line 8 stale. | Add top line naming authoritative sections; copy coverage sentence from line 20 only. |
| BS-P1-COR-8 | Nit | 69,56,41 | TEXTNORM_MAX_PASSES added in P1a unused until P1b. | None. |
| BS-P1-COR-9 | Nit | 76 | Rewrite removes noqa S311 at test 764 and Windows branches; other random noqa lines are in unmoved tests. | None. |
Verified (read): 17 template fields; PR #50 748849c textnorm.py/_confusables.py/mutation_runner.py/promoted_mutants.py/test_promoted_controls.py cites; core absence of guard/textnorm.py, tools/, testing/; arithmetic (mutants 80, runs <=121, lines 10,864, size rule 87,381x3=262,143); order 20 S0 EXIT chain.
Not checked: all Unicode counts; whether mutants end KILLED or CRASH after move; ce70eb5 vs current main; Intake/dealdesk heads; 11-script claim; ruff/bandit on tools/; Unicode License text; timings; P1b keeping P1a search strings; other tickets.
