Status: resolved

# Goldfish Annotated Review Report (PR89, round 26)

**Target:** branch `wip/cloud-PR89-r26`, head `916c71ea`, snapshot `/home/user/build/snap/pr89r26-916c71ea`. Mutation runner hardening (`tools/mutation_runner.py`, its mutant lists and pins). No person was available: recommended option for every item. Reviews (both read-only, nothing run): `handover/reviews/PR89/pr89r26-design.md` (0 Blocker, 0 Major, 4 Nit) and `pr89r26-codebase.md` (0 Blocker, 2 Major, 5 Nit). Evidence (independent, head confirmed, tree clean): `handover/evidence/PR89/916c71ea/RESULTS.md`: full pytest 10826 passed, 3 skipped (Stubber, 2 mypy tests), 28 deselected; full mutant runner 327 of 327 good (run as root); `stage_mutants` 37 of 37; ruff, format, bandit, scan_repo, gitleaks exit 0; fail-before 9 failed on old code, 5 new tests pass on old; 24 of 24 hostile probes refused; mypy 13 errors on 3.12 and 3.13 (scratch overlay, flags approximate the test's); timing test flaky (head fail, pass, fail; main fail, pass, pass). Not run: Windows, macOS, semgrep, zizmor, trivy, pip-audit, pytest on 3.12, perf.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase` F1] - Severity: Major
*   **Affected Scope:** `tests/mutation_runner_mutants.py:189` (mutant "folders between made without the private helper"); killer `tests/test_mutation_runner_keywords.py:5421-5441`, comment `:5428`.
*   **Discrepancy Description:** The mutant replaces `_make_private_dir(here, "folder of the copy")` with `os.mkdir(here, 0o700)`. The killer runs `_make_dirs` under `_umask(0o277)` before any assertion; the mutated mkdir gives mode 0500, and the nested `mkdir a/b` raises `PermissionError` for a non-root user, leaving the test before the assertion that holds the expect fragment. A non-root run gets a first failing line without the fragment, so the mutant is not killed for its reason and the list exits 1. As root EACCES is skipped, which is why the evidence run (root) shows 327 of 327. The comment says 0400, wrong.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The evidence runner ran as root, so it cannot see this; a mutant list that only passes as root is a false green for anyone running it normally.
*   ***Proposed Edit:*** Put the helper-spy check (`whats == ["folder of the copy"] * 3`) before the umask block, or catch `OSError` around the call and re-raise as `AssertionError` with the fragment "under umask 0277 the part"; correct the comment to 0500. Next evidence run executes the mutant list once as a non-root user (state how).

### [Issue 2] [`codebase` F2] - Severity: Major
*   **Affected Scope:** `CHANGELOG.md:23` (item 4), `:28`; `tests/mutation_runner_mutants.py:33-36`, `:100-102`, `:116`.
*   **Discrepancy Description:** CHANGELOG item 4 still says the killers that skip inside their body are "named in the prose of the header by hand"; the code now has a derived list (BODY-SKIP-MUTANTS-BEGIN/END, compared both ways) and line 28 says so. Header line 100 says the prose says why each one skips, but the symlink-privilege paragraph names three killers and not "runner: a link out of the tree is accepted" (listed at 102); CHANGELOG line 28 says that omission was fixed.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Two sentences of the same changelog contradict each other and a claim of a fix does not match the text; documentation claims are held to the same bar as code.
*   ***Proposed Edit:*** Rewrite item 4: both lists (POSIX-only, body-skip) are derived and compared both ways by a test. Add the missing killer to the prose at lines 33-36 or drop the sentence at 100 and the claim at CHANGELOG 28.

### [Issue 3] [`codebase` F3] - Severity: Nit
*   **Affected Scope:** `CHANGELOG.md:30`; `tests/mutation_runner_mutants.py:137`.
*   **Discrepancy Description:** "5 re-pointed" is 7; missing are "a made file is not checked" and "the address step comes before the count of the secrets". Totals are correct (327 = 320 + 7).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Say 7 and list all seven.

### [Issue 4] [`codebase` F4, `design` N3] - Severity: Nit
*   **Affected Scope:** `tools/mutation_runner.py:1293-1309` (`_make_private_file`), tests ~`:6033`.
*   **Discrepancy Description:** `os.chmod(fd, 0o600)` runs before `_file_problem`, so a refused second-name file has its shared inode narrowed to 0600 (same user only); no `O_NONBLOCK`, so a FIFO under a result or settings name blocks `os.open(O_WRONLY)` (not a regression: the old `O_TRUNC` open blocked too; the lock file and JUnit reader guard it); the FIFO case is tested only through `_file_problem`; the docstring says another owner is refused though a non-root caller fails earlier with `PermissionError`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A hang on a planted FIFO is a small denial path in a tool that claims to refuse such files; the fix is two lines and a test.
*   ***Proposed Edit:*** Add `O_NONBLOCK` on POSIX; run `_file_problem` before `chmod`; test `_make_private_file` on a FIFO with a timeout; soften the docstring ("the other-owner refusal is reached only by root").

### [Issue 5] [`codebase` F5] - Severity: Nit
*   **Affected Scope:** `tests/test_mutation_runner_keywords.py:6100-6200`; `tools/mutation_runner.py:244-248`.
*   **Discrepancy Description:** The creation-site pin records owner function names per spelling, not call counts, and the walk misses assigned names, `getattr`, `map`/`partial`, `os.fdopen`, `io.open`, `codecs.open`, `Path` methods and `shutil.copyfileobj`; intermediate parents of `extra_dirs` destinations are made by `copytree`/`makedirs`, so "every folder the runner makes" is slightly too broad.
*   ***AI Suggestion:*** PROPOSE FIX (wording and count pin; the missing spellings are listed in the docstring as not found)
*   ***Justification:*** Pinning (spelling, owner, count) is cheap and closes the "second call in the same function" hole; a complete spelling list is open-ended and the docstring already says a non-listed spelling is not found.
*   ***Proposed Edit:*** Pin counts; soften "every folder" to "the listed spellings, per function"; name the missed spellings in the docstring.

### [Issue 6] [`codebase` F6, `design` N4] - Severity: Nit
*   **Affected Scope:** `tests/test_mutation_runner_keywords.py:5940-5995`; `tools/mutation_runner.py:47-53`; CHANGELOG mypy lines.
*   **Discrepancy Description:** The sentence "CI does not run the mypy count" is asserted only inside a test that is skipped when mypy is absent (the CI case). The "13 errors at mypy 2.4.1" figure was measured at round 24; the independent evidence run re-measured 13 on 3.12 and 3.13 with a scratch overlay and approximate flags; "left to the lead" is process text in a user-facing changelog.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Honest wording is cheap; adding mypy to the lock is a separate decision for the owner (`q-pr89-mypy-in-lock`, safe default: not in the lock).
*   ***Proposed Edit:*** Move the "CI does not run" assertion into a test that always runs; CHANGELOG: "13 errors, measured by an independent run at head 916c71ea with mypy 2.4.1 on 3.12 and 3.13 (the repo test is skipped where mypy is not installed)"; delete "left to the lead".

### [Issue 7] [`codebase` F7] - Severity: Nit
*   **Affected Scope:** `tests/test_mutation_runner_meta.py:228-321`; `tests/mutation_runner_mutants.py:28-31`, `:116`.
*   **Discrepancy Description:** `_windows_skip_mark` short-circuits (`whole or any(...)`), so decorators after a `posix_only` one are never read and an unreadable one after it does not raise; `_calls_skip` follows only same-file helpers; killers that drop a branch by `os.name` without `pytest.skip` ("a JUnit symbolic link is followed", "the descriptor of the lock folder leaks") sit in neither list and are named by hand in the prose.
*   ***AI Suggestion:*** PROPOSE FIX (read every decorator even after a true mark; list the two hand-named killers in a derived third list or state the hand-kept names in the CHANGELOG as unchecked); DECLINE following imported helpers (no such skip exists today; reviewer found none).
*   ***Proposed Edit:*** Replace short-circuit with an `all-read` pass that raises on any unreadable decorator; add the two names to a small hand-kept list checked by one test that each still occurs in the killers' bodies.

### [Issue 8] [`design` N1] - Severity: Nit
*   **Affected Scope:** `tools/mutation_runner.py:1101-1106` (`_shown_class`), `:1001-1007` (`_own_text`), `:956-957`.
*   **Discrepancy Description:** Caller-owned class names are hidden when they hold a secret or a piece of it, built-in names only when equal; a reader sees `[class not shown]` for `OwnCrash` with password "Crash" and learns one bit. The docstring says the reader "can no longer infer", true for equality only. (Round 25 codebase N1 raised the related case-sensitivity of caller-owned names.)
*   ***AI Suggestion:*** DECLINE the behaviour change; PROPOSE FIX for the wording
*   ***Justification:*** The channel is one bit per row, the same as test ids and expect slots (docstring says "on purpose"); holding-a-piece hiding is the safe direction. Reword: "can no longer infer the password from an equal name; a name that holds a piece of it is hidden and the hiding itself shows that the piece is in that name". Round 25's case-insensitive equality for caller names stays as decided in round 26 (casefold equality covers derived forms).
*   ***Proposed Edit:*** Docstring and CHANGELOG sentence as above.

### [Issue 9] [`design` N2] - Severity: Nit
*   **Affected Scope:** `tools/mutation_runner.py:238-239`, `:1963-1977`, `:1966`, `:2031`.
*   **Discrepancy Description:** The docstring says every listed folder is checked again after every rebuild; the code re-checks only temp (`1963`, `1977`) and snapshot (`2031`); `tmp/tests` is checked once, and `copytree(dirs_exist_ok=True)` of an `extra_dirs` "tests" can set the private `tmp/tests` to the caller's mode (nothing becomes readable: the parent is re-checked and gates access).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Reword to "the temp and snapshot folders are re-checked after every rebuild; the others once, when made" or re-check `tmp/tests` at line 1977; reword is enough.

### [Issue 10] [`evidence`] - Severity: Minor
*   **Affected Scope:** Evidence RESULTS.md.
*   **Discrepancy Description:** 5 new tests pass on old code (module-level pytestmark/named mark reader, unevaluable skipif is an error, creation-site walk, header names every body-skip mutant, mypy error pattern); the mutant list ran as root only; mypy ran with scratch flags and a venv interpreter (3.13.18), not 3.12; the timing test fails on head 2 of 3 and on main 1 of 3.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** For each of the 5 either a mutant that kills it or a stated control reason is needed (class of Issue 7 of Q8c-1 round 6); the non-root mutant run closes the Issue 1 gap.
*   ***Proposed Edit:*** Fix builder adds one line per passing-on-old test (reason, mutant); next evidence run executes the mutant list as non-root and runs mypy on a real 3.12 interpreter.

## Handoff counts
Accepted (PROPOSE FIX): 9 (Issues 1-7, 9, 10; Issue 8 wording only). Declined: Issue 8 behaviour change and following imported helpers in Issue 7. Contested: 0. Escalated: 0 (`q-pr89-mypy-in-lock` default stays: do not add mypy to the lock). Two Majors (Issues 1 and 2) need a fix builder; round 27 reviews are limited to Blockers and Majors per the cap, with the Nits fixed in the same push. Ledger: PR89 round 26 Majors OPEN until the fix is verified (the non-root mutant run is the verifying evidence for Issue 1).
