Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8b batch 11, branch `wip/cloud-q8b-b11`, head `2153ad85`, round 12 (REDACTION path: no round cap).
**Inputs:** `q8bb11-design-r12.md` (1 Blocker B1, 4 Major F1-F4, 2 Minor F5-F6, Nits), `q8bb11-codebase-r12.md` (Major C1-C5, Minor C6-C7, Nit C8), `q8bb11-builder-addendum.md`, previous report `goldfish_review_report-r11.md`, independent evidence `handover/evidence/Q8b/2153ad85/RESULTS.md`. Automated mode, recommended option for every item, no severity changed, nothing contested.

## Evidence summary (recorded by the runner, not judged)
- **Not green:** `q8b_mutants` exit 1, 212 of 229 good, 17 not good: SURVIVED M159, M163, M190; WRONG_REASON M192, M198, M199, M200, M215, M216; OTHER_TEST M193, M196, M197, M203, M223, M224, M225; CRASH M226 (InputTooLarge). The 17 are the same rows the builder listed in its addendum.
- Green: full pytest 11117 passed, 1 skipped, exit 0 (so the baseline failure the design reviewer feared (B1) did not reproduce; the builder's own gate files were still invalid); ruff, format, bandit, scan_repo, gitleaks exit 0; `stage_mutants` 37 of 37; `mutation_runner_mutants` 64 of 64.
- Fail-before on `166d1313`: 57 failed, 169 passed (50 batch-11 tests pass on old code and need a reason or a mutant each).
- Unplanted controls: 74, 3 not named by a mutant (`UNPLANTED_MAX = 3`).
- Cost, `clean()` on 60,000 characters, alone: head 2.07x main (hostile), 2.01x (prose); `166d1313` 1.68x and 1.55x.
- **Regressions against main (readable on head, masked on main):** 16 cells in `probe` (bare compass, overpass, encompass, bypass; eq, colon, json, quoted forms) and 340 cells in `probe_extra` (json form of ordinary-word pairs joined by underscore, hyphen, dot or digits). Capitals cookie forms: 18 of 38 text cells and 7 of 19 record cells readable on head; main masked all (equal to `166d1313`: 18 and 9).
- Wrapped-header shapes, 3000 random texts: A (same line) head 273 of 979 readable; B (indented continuation) 0 of 1042 (main 879); C (no indent) 807 of 979 (main 852).
- The known timing test fails on head and main alike (do not touch). Python 3.12, semgrep, zizmor, trivy, pip-audit are IMPOSSIBLE-NOW.

## Prioritized Findings & AI Suggestions (all PROPOSE FIX unless marked)

### [Group 1] [evidence regression; design F5 scope] - Major (redaction regressions against main; the reviewers' "nothing readable that main masked" was by reading and is contradicted by execution)
Scope: `redact.py` `ORDINARY_WORDS` (~175-180), `is_ordinary_pair` (`startswith`, ~254-258), `_FLAG_NOT_ORDINARY`, the pair, bare-word and json paths; capitals-cookie reading (NFKC, fullwidth, zero width) in text and record walk.
Gap (class: an exemption list or new rule that makes a value readable which the older reading masked): 16 plus 340 cells and the capitals cookie cells above. Name the class "exemption wider than the reading it replaced" and fix at the shared pair table so text, record walk and flag rule agree.
Fix: for each of the 356 named cells and the capitals cookie cells, either mask on head as main did or put it to the owner (group 8) with the exact cell list; the default is to mask (main's behaviour), and an exemption stays only where a test shows the value is not secret-shaped. Add a test per cell class that fails on `2153ad85`; add the json form of ordinary-word pairs with each joiner as a seeded generator; a mutant per branch. Re-run the three probe sets and report head against main (target: 0 readable on head and masked on main).

### [Group 2] [codebase C1, C2, C3; design F4, F6; evidence 17 bad rows] - Major (mutant gate not green)
Scope: `tests/q8b_mutants.py`, `tests/test_q8b_batch11.py`, mutant rows M159, M163, M190, M192, M193, M196-M200, M203, M215, M216, M223-M226.
Gap: M190 is an equivalent mutant (rule 2 masks the same folded lines; the first-token-under-8 case is not tested): add the short-first-token test (`token=Bearer abc` then an indented long continuation) or delete the branch (CODE-LAST). M192, M193, M196-M200, M203 are pinned to the wrong parameter or another test (OTHER_TEST or WRONG_REASON): re-point each to a killer whose message names the mutant and that fails for the named reason. M159 and M163 survive: add killers. M215 and M216 WRONG_REASON, M223-M225 OTHER_TEST: fix pins; M222 and M223 have identical old and new text (duplicate pattern, r11): make each plant a distinct fault. M226 crashes with InputTooLarge: choose a plant whose input stays under the cap. The structural test `test_every_planted_fault_is_in_its_product_file_once_...` must also check old differs from new and that the killer fails (F6). The 3 unplanted controls get a smaller planted fault (no deferral to "the next builder").
Fix gate: `python tests/q8b_mutants.py` exits 0 with every row good, run alone as root and as nobody on the final head.

### [Group 3] [codebase C4; design F3; evidence cost] - Major (cost)
Scope: fold and key-word patterns (`redact.py:916-945`), `_pair`, `clean()`.
Gap: cost is 2.07x and 2.01x main at 60,000 characters (builder measured 2.69x and 2.45x on the wrong commit 82e31c80); the new patterns start with an alternation of about 35 words with no literal prefix, tried at every position; "linear" rests on two sizes; no ceiling in the performance step.
Fix: measure on the final head at three or more sizes (30k, 60k, 120k and the 262,144 cap) against main, alone; add a literal prefilter (cheap keyword scan before the alternation) at the shared choke point; add a ceiling test that counts work, not seconds (the timing test is flaky and stays untouched); state the measured ratio and the absolute seconds at the cap in the CHANGELOG. The owner is asked to state an absolute budget (group 8).

### [Group 4] [codebase C5; design F1, F2; evidence shapes A and C] - Major (folded-header class not closed)
Scope: `redact.py:916-945` `_AUTH_SCHEME_NAMES`, fold rule, header branch; tests `test_b11_8_*`.
Gap (class: a wrapped credential header whose secret ends up on a line the rule does not reach): shape A (secret cut on the same line) 273 of 979 readable, shape C (no-indent continuation) 807 of 979, a second word on the first line (`Authorization: Bearer <tok> x` then indented line) switches the fold off, schemes outside the five (NTLM, Negotiate, OAuth, Splunk, Hawk, AWS) are masked by the flag rule but not the header rule, a folded header with no scheme word, and the line breaks U+2028, vertical tab, form feed and U+0085. Shape C has no owner decision.
Fix: take any scheme word `[A-Za-z][\w-]*` on the authorization branch (make header and flag paths agree); anchor the fold at the header name so one extra word does not switch it off and the rule stays linear; handle the five break characters; one test and one mutant per shape; shapes A and C that cannot be closed without masking ordinary prose go to the owner as group 8 with the measured numbers; until answered they are stated in LIMITS with the exact reach (not "all five schemes").

### [Group 5] [design B1 (builder gate), F5; codebase C6, C7, C8] - Major (documents and gate files)
Scope: `CHANGELOG.md` batch 11 items 1(a), 1(c), 4 and batch 10 item 6; `LIMITS` text (printed in customer reports); `tests/test_q8b_batch11.py` group 6 and the controls table; `builder-evidence/` files of b11; notes row for M191.
Gap: the builder's own gate files are invalid (full-pytest log with no summary, four aborted mutant runs, empty full log, final-head file holding only the SHA); CHANGELOG item 4 points at private builder notes; item 1(c) lists 3 bare names while `ORDINARY_WORDS` holds 15 that stay readable bare; item 1(a) names the wrong commit; batch 10 item 6 says one table serves all paths but `compass_keyboard`, `possession_identity`, `bypass_keyboard` are masked in text and record walk and only flagged by the flag rule (not named); LIMITS names internal test files (preamble rule 14); the notes say the linear-time test is killed by M191 (its pin is another test); the controls-table (group 6) and COOKIEſTORE canonical-form claim (C7) are false or unsupported.
Fix: rewrite each sentence with measured numbers from this evidence and plain words; replace private-note pointers with the repository file; remove test-file names from LIMITS; correct the M191 note; give the linear-time test its own mutant; keep the three unmet nits of design (keep `==` in the ceiling test, mark the pinned-leak control test so it fails visibly when the owner decides to mask bare Token, ApiKey, Digest). Every gate line names its commit.

### [Group 6] [fail-before and per-test reasons; evidence item 7] - Minor
Scope: batch 11 tests passing on `166d1313` (50 ids, `batch11-passed-on-166d1313.txt`).
Fix: one line per passing-on-old test with a stated reason or a killing mutant; re-record fail-before for groups 3, 4, 5 and 10 against `2153ad85` (clean detached worktree with only the new tests copied in); give exact counts including collection errors.

### [Group 8] [OWNER-ONLY: `q-q8b-bare-bypass`] - Major (owner decision, not fixed here)
Scope: bare ordinary words (compass, overpass, encompass, bypass and the other 11 of `ORDINARY_WORDS`), shape C (unindented continuation, 807 of 979 readable, main 852), shape A residue, the absolute cost budget.
AI Suggestion: ESCALATE-to-owner, kept OWNER-ONLY. How much ordinary text may be masked to close these is a product choice. The default stays masking as main did (group 1) until the owner answers; the measured numbers above are the basis. Not marked fixed.

### [Group evidence] [independent evidence deviations] - Minor
- 17 of 229 mutants not good (group 2); baseline green and full pytest 11117 passed (so design B1's baseline failure `test_n6_a_domain_after_a_placeholder` did not reproduce on this head; the builder's gate files are invalid regardless, group 5).
- Cost measured lower than the builder's (2.07x against 2.69x); builder numbers on the wrong commit.
- Not run: pip-audit, semgrep, zizmor, trivy, Python 3.12 (IMPOSSIBLE-NOW), `pytest -m perf` (the ticket names no perf item); `uv sync --locked --no-build` fails here (venv built without `--no-build`); fail-before against main impossible (3 of 5 test files do not exist on main); timing test fails on head 2 of 3 and main 3 of 3 (not touched).

## Who fixes it
One batch-12 builder (Sonnet 5.5) on a new branch `core/q8b-b12` from `2153ad85`, pushing to `wip/cloud-q8b-b12`. Order: group 1 (regressions) first, then 4, 2, 3, 5, 6, evidence. Method per bug: name the class, fix at the shared choke point, grep siblings, show each new test failing on `2153ad85`, one mutant per fix with a killer that fails for the named reason, final-head full suite, `q8b_mutants` fully good as root and as nobody, `stage_mutants`, the three probe sets head against main, perf measured on the final head at three or more sizes against main. No readable secret-shaped value in any committed file or log.

## Handoff
- Accepted fixes (PROPOSE FIX): 6 groups (1 to 6) plus the evidence group, covering 1 Blocker (B1, now an invalid-gate and 17-bad-mutant finding), 9 Major, Minor and Nit items.
- Escalated: 1 group (8, OWNER-ONLY). Contested: 0. Declined: 0.
- Remaining unaddressed: all of the above until batch 12 is built, run through independent evidence and reviewed (round 13, no cap on this path).
