# R7Q results (builder 2; claims are unverified until an evidence runner and a fresh reviewer check them)

## What failed or was not done, first
- The first builder-2 run was stopped by a permission denial (an ad-hoc probe script of item 3). Not retried. The lead then ordered item 3 settled from source only.
- Item 3 (M9-74) is NOT PROBED, argued from source (below).
- The hygiene scan (secrets, personal data, names) was NOT run by the builder. The independent evidence runner does it.
- I did NOT run the full suite. I did NOT run the old-tree (r7p) comparison again after adding test q9 (q9 is a PIN: it passes on r7p, a mutant kills it).
- No git init was run. The patch verify folders are plain folders (git apply works outside a repository); build_patches.sh differs from the r7p one only there.
- My own count of `nosemgrep` is 40 for BOTH r7p and r7q (grep -o over the tree); the brief's figure 31 does not match my method, the delta is 0 either way.
- A test run of mine was disturbed once: I appended test q9 while a run was in progress, and `test_the_driver_tests_leave_no_fake_flags_behind_for_a_later_test_file` failed with "FILE CHANGED BY THE TEST RUN: tests/test_r7q_findings.py". Re-run on stable bytes: passed (log tmp2/s2.log).

## Items (NEEDED-CHECK v1)
| # | state | what | evidence |
|---|---|---|---|
| 1 | NEEDED (money) | banner cost = longest request of the plan the run sends. `new_tag()` made once; `longest_request_bytes(live, plan)` uses `request_body`, `question_text`, `normalise_email`, a lead id of the real length (prefix + 12 hex). | tests q1 (5 parametrised banner cases incl. longer tag, longer domain, 120 people; helper vs independent JSON; one-builder; email key) and q2 (one tag for banner and run). On r7p (out/R7Q/old) the banner test fails on the number (7.7708 expected). Mutants Q10-Q16, Q19 killed. |
| 2 | NEEDED, PIN | factor 3 x 2 desk processes x (people + 3). Holds from source: at most one model call per automatic try, at most SEND_MAX_ATTEMPTS (5) tries per lead kept in the book, so 6 per lead covers 5; people + 3 covers people + twin. The hard bound is the per-run cap in the ledger, printed on the same line. `MODEL_CALLS_PER_LEAD` is now `MODEL_CALLS_PER_LEAD_MAX` (one source). Reachable maximum NOT measured. | q3, r7o pin; Q17, Q18 killed |
| 3 | NOT PROBED, argued from source | The exit is `0 if result["ok"] and written and not left else EXIT_FAILED`. A cleanup that knows it left contacts fails (r7o pins). A contact the desk created that the HubSpot list does not show, for a lead not yet CRM-done, is not in `crm_pairs`: not archived, F3 does not fire, exit 0 is possible. A lead already CRM-done with a hidden contact fails F3. Without --cleanup the run exits 0 with contacts in HubSpot by design. No source change made. Reason: the candidate fix (desk counter `created` vs archived + left) could give false failures from stale counter files in a shared run folder. Next step for the reviewer: decide if the case is reachable with the real HubSpot list lag (the script itself marks it UNVERIFIED); if yes, add the check with a run-id-scoped counter. | none |
| 4 | NEEDED | MemoryError is handed back (chain scrubbed), as `_dialogue` and callers mean (tests/test_except_clause_hierarchy.py). | q4 (fails on r7p), Q01, Q02 killed |
| 5 | NEEDED | R08: q5 (KeyboardInterrupt, SystemExit). K01: q6. | R08, K01 killed (were survivors in the r7n review) |
| 6 | NEEDED | repo-wide guard recursive (src, scripts, load_tools, tools), getattr/authenticate/login_cram_md5, alias assignment, more header and path names, lambdas, dead `if False`, local guard names; `_key` only as `x._key()` (the first rewrite flagged tools/pathconfine.py::_match: fixed). | q7: 23 planted forms caught, 7 clean forms not flagged, known-guarded-functions assert on the real tree, recursion test; real tree not flagged. G01, G02, G03 killed |
| 7 | NEEDED | reviewer mutants on the r7n tests (r7p _EchoImap rewrite): X2, R05, I01 KILLED. X1 on the login branch (X1a) KILLED. X1 on the not-repeated branch (line `raise ImapConnectionError(...)`) SURVIVED the r7n tests: new test q9 kills it. | table below |
| 8 | NEEDED | QuietServer silences only BrokenPipe, ConnectionReset, ConnectionAborted, Timeout; every other error still printed; used by the three fakes; `import sys` order fixed. | q8; Q20-Q25 killed. demo_only tests (test_codeant_demo_only, test_codeant_fakes) and test_fakes_body_before_answer pass |
| 9 | kept | scrub.py docstring read against the code: correct | read |

## Changed existing tests
| test | old assertion | new assertion | why not weaker |
|---|---|---|---|
| tests/test_r7n_findings.py test_m9_43 (run_real_check part) | cost from the placeholder body (`x@example.com`, lead id L000000000000) x 3 x (people+3) x 2 | the same arithmetic, body = max over every person address and the twin for a fixed tag (`new_tag` set to rabcdef) | the expected number is larger and still exact to 4 decimals |
| tests/test_r7n_findings.py guard section (rewritten by builder 1, fixed by me) | name list in 3 folders, non recursive | recursive, 4 folders, more forms | catches strictly more; the old planted-site test is kept and still passes |

## Test runs (pytest only, lo_up driver, unshare -n, test_load_tools first)
- load, r7q, r7n, except_clause_hierarchy, codeant_demo_only, codeant_fakes, fakes_body_before_answer, r7o, r7p: 378 passed, 1 failed (the disturbed run above), log tmp2/s1b.log. After that: load, r7q, r7n (-k not n1_a_refused/dry): 224 passed (tmp2/s2.log). Earlier on the same code: 330 passed (tmp2/s1.log).
- New file on r7p copy: 44 failed, 17 passed (61 tests then; many failures are "helper missing"; behavioural: banner number, one tag, MemoryError, guard forms, QuietServer).
- ruff 0.17.1 on a copy: check "All checks passed!", format --check "229 files already formatted".

## Suppressions (grep -o over the tree, r7p -> r7q)
noqa 188 -> 193 (+5: 4 x E402 in tests/test_r7q_findings.py, the module imports after the sys.path insert, same pattern as test_r7o_findings.py; 1 x PLR2004 in the guard `len(f.args) >= 2`, from builder 1). type: ignore 126 -> 126. nosemgrep 40 -> 40. nosec 8 -> 8.

## Mutants (mut.py, one runner on out/R7Q/mut, every file restored and byte-compared after each: restored-byte-equal=True for all)
See mut-results.tsv. All KILLED: X1 (by q9), X1a, X2, R05, I01, G01, G02, G03, R08, K01, Q01, Q02, Q10-Q25 (Q13 banner placeholder, Q14 second tag, Q19 fixed tag, Q20-Q25 QuietServer variants). Survivors: none after q9. EQUIVALENT: none claimed. (The "SURVIVED" rows for X1/X2/R05/I01 against tests/test_r7p_findings.py are the wrong test file; the killing tests are in r7n and r7q.) Lines of run_real_check.py not mutated: the unchanged r7p lines.

## Files
patches in /home/user/build/rr6/out/R7Q: core-fix-on-frozen-r7q-crlf.patch, core-fix-on-frozen-r7q-lf.patch, core-fix-r7p-to-r7q-delta.patch, sha256-r7q.txt, apply-matrix-r7q.txt (a-crlf, b-crlf, c-lf git apply --check rc 0; crlf patch on frozen2 = tree byte for byte; delta on r7p = r7q).
Changed files: demo_only/bad_request.py, fake_hubspot.py, fake_model_server.py, fakes_server.py, scripts/run_real_check.py, src/lead_desk/scrub.py, tests/test_r7n_findings.py, tests/test_r7q_findings.py (new). Off-path items (run_live_check, CHANGELOG, README, docs, n3, ledger) untouched.
