# Q8b batch 12: builder notes (evidence list)

Base 2153ad85. Files here: fail-before of the new tests on the clean 2153ad85 copy (import path printed first line), the 50 batch-11 tests that passed on the old code with one line each, the 15 batch-12 tests that pass on old code with their reason below, probe regress tables (old = 2153ad85, new = this head, against main), cost numbers.

Fail-before (2153ad85): test_q8b_batch12.py 15 failed, 15 passed; test_q8b_batch8.py and test_q8b_batch10.py 16 failed, 75 passed (the changed pins of group 1 expect the main behaviour, so the old code fails them). Probe: pair cells that main masks and 2153ad85 left readable 340 (old-regress file; corrected in batch 13: the file has 340 rows, the first text said 339) and 0 on this head; the 15 cells of the bare ordinary word are the owner question q-q8b-bare-bypass (shown).

Batch-12 tests that pass on old code, with the reason:
- test_b12_1_the_bare_ordinary_word_*_stays_shown (8) and test_b12_1_a_non_ordinary_word_*: controls for the owner decision (the bare word stays shown; the old code showed it too). Killers: M234, M235, M236 change the exemption.
- test_b12_2_* (3): the old code was right; they are the killers for M190, M159, M163, which survived before (no test could tell the fault).
- test_b12_4_a_lower_case_hyphen_token_is_not_read_as_a_scheme_word: control, killed by M240 (fault). test_b12_4_a_header_with_many_extra_words_*_linear_time: killed by M241 (fault).
- test_b12_5_a_capitals_cookie_key_*: control for a claim that the run contradicted (main and old both mask on the five paths).

Batch-11 passed-on-old list: b11-passed-on-old.txt (44 have killing mutants; six have none: the four test_b11_8_a_second_word_* pins are stated owner limits, test_b11_4_the_bare_scheme_* is the PINNED LEAK, test_b11_8_a_long_run_of_folded_lines_is_read_in_linear_time is a wall-clock control with NO planted fault yet: a fault that is quadratic on that text and cheap to run was not found; open).

Open, not done: the controls with no planted fault (the three of tests/test_q8b_batch8_lines.py plus the b11_8 linear test above). Owner: q-q8b-bare-bypass, bare scheme plus token class, shape C and the A residue, the absolute cost budget. Impossible now: Python 3.12, semgrep, zizmor, trivy, pip-audit not installed here; fail-before against main (3 of 5 test files do not exist there).

Gates, all on commit 6b5e7e69 (the evidence commit after it changes only files under handover/): ruff check and ruff format --check (src tests demos tools) rc 0; bandit -ll -r src rc 0 (0 issues); tools/scan_repo.py rc 0; tests/stage_mutants.py 37 of 37 good rc 0; tests/q8b_mutants.py 241 of 241 good rc 0 as root and rc 0 as nobody; tests/mutation_runner_mutants.py as nobody 64 of 64 good rc 0; one full pytest -m "not live and not perf" against own Postgres 16.15: 11147 passed, 1 skipped (tests/contracts/test_llm.py:95, a Stubber case), 16 xfailed, rc 0; gitleaks (origin/main..HEAD, 25 commits) no leaks, rc 0. Cost numbers were measured with other builders running (load about 3.7), not alone.
