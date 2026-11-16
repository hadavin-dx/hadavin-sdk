**Package PR89 (tools/mutation_runner.py), head 4cc427b5bfbf1ff07beb8db03da80c9e59b44fc6, round 23, persona codebase details**

Verdict: no Blocker. The r22 codebase finding (str guards at only three places) is fixed. Three Majors and four Nits remain. I read the snapshot only and could not run pytest, mypy, the mutants or sha256 (see "Not checked").

### [C1] Major - the mypy win32 "13" pin is a hand count and probably short by one
Where: `tools/mutation_runner.py:1208`, `tests/test_mutation_runner_keywords.py:5790-5862`, docstring line 46, CHANGELOG:26.
What: The pin test counts `os.`/`signal.` names with `ast` against a hand-written table. It never runs mypy. The table puts `os.fchmod` (line 5814) in OTHER_NAMES with the reason "if _IS_WINDOWS branch that mypy reads as reachable".
- `_IS_WINDOWS = (os.name == "nt")` (line 410) is a plain variable. mypy narrows only on `sys.platform` and `sys.version_info`, so `os.fchmod` at 1208 is type-checked for win32.
- I recall typeshed marking `fchmod` as unavailable on win32 before Python 3.13. The package requires `>=3.12`. I did not verify this in typeshed.
- If so, `--platform win32` on 3.12 gives 12 + fchmod + 1 untyped import = 14, not 13.
- `os.waitid` at 1470 is also treated as "behind hasattr". I doubt mypy narrows a module attribute that way, but I am not sure. That could add one more error.
Why it matters: The docstring, CHANGELOG and test all state a number that nobody measured, and the test cannot catch this kind of miscount. r22 item 14 (m8) asked for a count that is noticed when it changes. The count is pinned, but not shown to be true.
Suggested fix: Run `mypy --platform win32 tools/mutation_runner.py` once on 3.12. Record the real count and the error lines. Move `os.fchmod` (and `os.waitid` if reported) into POSIX_ONLY_NAMES, or `getattr` them. Correct the three texts.

### [C2] Major - "every other killer runs on both systems" is false for round 23
Where: `tests/mutation_runner_mutants.py:37` and 48-52 (header); CHANGELOG:26; killers at `tests/test_mutation_runner_keywords.py:5157-5503`.
What: CHANGELOG:26 says the mutants that would not be killed on Windows "are named in the header". The header lists the older POSIX-only killers and says "Every other killer is written to run on both systems". The round-23 killers carry `@posix_only` (skipif win32). They are:
- `test_every_folder_and_file...`, `test_the_temp_folder_is_checked_*` (two), `test_the_snapshot_folder_is_checked_after_the_copy`
- `test_the_folder_of_the_settings_file_is_checked`, `test_a_folder_that_is_not_private...`, `test_a_private_folder_is_made...`
- `test_the_parts_between...`, `test_a_private_file...`, `test_the_lock_folder_and_the_lock_file_are_private_under_umask_0`

These kill the mutants at `mutation_runner_mutants.py:560-575`, `578-581` and `582`, which is 21 mutants. They survive on Windows, and the header does not name them.
Why it matters: A reader on Windows gets "every other killer runs on both systems". That is false for these 21 mutants.
Suggested fix: Add the 21 mutant names to the header's POSIX-only list. Drop or qualify line 37.

### [C3] Major - r22 item 10 (order mutants) declined on a false ground
Where: `tests/mutation_runner_mutants.py:48-52`; `tools/mutation_runner.py:1836-1840` and `1906-1911`.
What: The header says the order of the secret-count step against the address step, and the order of the junction checks against `mkdtemp`, have no mutant because "one replacement cannot move a block". The mutant list contradicts this: mutants 561 and 562 use multi-line `old` texts, and `new` can be any text. A mutant can move the `_refuse_unsafe_address` loop (1838-1840) above `_secret_values` (1837), or move `_refuse_junctions` (1906-1909) below `mkdtemp` (1911). The r22 report asked for exactly this (item 10, "mutant that swaps the loops").
Why it matters: The order test at `tests/test_mutation_runner_keywords.py:4496` pins the order. The 901-layer and `odd_many` values are good for that. But the mutant list does not show that the test fails for a swap, and the header gives a wrong reason.
Suggested fix: Add the two swap mutants with the order test as killer (the junction one would use the `made` list check at 5656-5683). Otherwise state plainly that the item is not done and why.

### [C4] Nit - CHANGELOG:57 overstates which files are "CHECKED"
Where: CHANGELOG:57; `tools/mutation_runner.py:1199-1210`, `1413-1419`.
What: CHANGELOG says every folder and file "is CHECKED (not a link, owned by the user, no group or other bits) when it is made". That is true for the four folder kinds and the lock file (`_check_lock_file`, 1297-1311). The settings file and the result file are only created at 0600 with `O_NOFOLLOW` plus `fchmod`. No `fstat` or owner check follows. The docstring (222-228) says it correctly; the CHANGELOG sentence is wider than the code.
Suggested fix: Say "made with mode 0600 (not checked afterwards)" for those two files.

### [C5] Nit - "a bare string is a TypeError ... checked first" is exact only for three keywords
Where: docstring 105-106; `tools/mutation_runner.py:1820-1826`; `tests/test_mutation_runner_keywords.py:5534`.
What: The three new guards run first (1820-1822). The `pass_env`, `throwaway_hosts` and `shown_classes` guards run after `_relative(t)` (1823-1824). A bad `tests` path together with `pass_env="X"` gives a `ValueError`, not a `TypeError`. The test comment at 5534 ("with slashes: a ValueError before") is stale. CHANGELOG:58 says a bare string "used to be read letter by letter" for `throwaway_hosts` and `shown_classes` too, but those two were already guarded in r22.
Suggested fix: Reword "checked first" to "the three before the path check". Fix the comment and the CHANGELOG clause.

### [C6] Nit - `connect_timeout` is capped at five digits, but the texts say "digits"
Where: `tools/mutation_runner.py:677`, docstring 125-126, error text 796, CHANGELOG:46.
What: `_OPTION_VALUE["connect_timeout"]` is `[0-9]{1,5}`. A six-digit value is refused as "not in a shape", while every text says it "takes digits". The mutant at `mutation_runner_mutants.py:492` is only about `port`.
Suggested fix: Say "one to five digits" or widen the pattern.

### [C7] Nit - sibling bare-string case outside the `run_mutants` keywords
Where: `tools/mutation_runner.py:355-357` (`Mutant.crash_markers`).
What: A bare string for `crash_markers` is passed to `judge_report` and iterated letter by letter (the judge code is in `mutation.py`, which I read only as a diff). This is outside the stated promise ("every keyword of `run_mutants`"), so it is not a broken claim. Mention it only if the class is meant to be closed.

### Checked and found fine
- **r22 #4 (str guards):** `_refuse_bare_string` (512-516) is called for `tests`, `extra_dirs` and `only` at 1820-1822. The messages match the tests' `"<kw> is a sequence"` check. The three guards at 521, 764 and 994 are intact. Mutants 583-587 remove each guard with a distinct killer and expect text. `only=""` is covered.
- **r22 #1 (temp folder):** `build()` (1858-1875) checks, empties with `_empty_dir`, makes `tmp/tests` with 0700, then checks again. `_empty_dir` (1184-1196) does not follow links. Tests at 5158-5273 cover it, including the check before anything is removed (5178-5251). The old rmtree-and-mkdir behaviour would fail the mode assertion in the child.
- **r22 #2 (snapshot):** `_make_private_dir` (1162-1168) runs mkdir 0700, chmod, then the lstat check. It is called at 1915 and the check is repeated at 1930.
- **Sibling folders and files:** all creation sites (mkdtemp, snap, ini_dir at 1413-1414, `_make_dirs`, `tmp/tests`, `_make_private_file`, `_open_lock_dir`) go through the helpers, except for the C4 gap. The `copytree` subfolders keep the caller's modes inside the private parent, and docstring 226 says so.
- **r22 #3 (D-023):** Docstring 236-239, CHANGELOG:66 and the test at 5753-5783 agree with `_shown_line` and `_shown_id` returning the raw text when nothing is passed.
- **r22 #5, #6, #8, #9:** The forged result file is stated at docstring 217-219. `_refuse_lock_folder_in_tree` is at 1226-1235, called at 1900, and tested (5624). The "read once" sentence excepts `XDG_RUNTIME_DIR` (159). The lock-limit text is at 251-260 and the link-check exception at 107-108.
- **r22 #7 (port):** `_port_in_range` (703-705) is used in the URL form (718) and the key=value form (743). The regexes are `{1,5}` at 659 and 671. Mutants 588-593 quote old texts that appear exactly once.
- **r22 #11 (MAX_SECRETS):** The boundary test (5694-5711) agrees with line 845. Mutants 596 and 597 cover `+1` and `>=`, and 497 and 588-590 cover the constants.
- **r22 #14:** The `noqa` comment at 1489 says the program path is built from SystemRoot. CHANGELOG:65 limits "read once" to the passed variables.
- **Manifest pin consistency:** `tests/fixtures/mutation_manifest.json` and the CHANGELOG diff lines 132-137 hold identical values for all four files (`3489a198...` for `mutation.py`, `8c1178ff...` for the runner).
- **Mutant count:** `kmutant(` appears 299 times in `tests/mutation_runner_mutants.py`, and `EXPECTED_MUTANTS` is 299 in the meta test. The meta test's split is 13 + 4 + 282. The header says 237 keyword mutants plus 62 base mutants, which also gives 299. Spot-checked `old` texts against the runner for 561-565, 569-575, 578-582 and 588-597; each appears once.
- **Killers kill for the stated reason:** For 560-575, the killer's `expect` string comes from the test's own `AssertionError` wrapper. Where the runner's own `RuntimeError` fires, the wrapper turns it into that same text. `only_test` pins the killer.

### Not checked
- The sha256 values against the file bytes. I have no hashing tool here. I only checked that CHANGELOG and manifest agree with each other. The repository's manifest test computes the real values.
- "38 new mutants, 18 new tests fail on old code". I could not run tests. I did not read all 38 mutant lines (my grep filtered some, about 34 shown) and did not count the new tests; I only read that the bare-string and port tests would fail on the old code.
- The real mypy result, and typeshed's availability for `os.fchmod` and `os.waitid` (see C1).
- Windows and macOS behaviour.
- `src/hadavin_sdk/testing/mutation.py` and `tests/conftest.py`, beyond how the meta test and the manifest refer to them.