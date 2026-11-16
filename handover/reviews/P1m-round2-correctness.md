# P1m round 2, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

Note: the reviewer opened evidence/P1m-fix/INDEX.md for its title line only (as it disclosed below) and used nothing from it.

P1m round 2, correctness, head 7442c0f (snapshot). Result: 0 Blocker, 0 Major, 2 Minor, 4 Nit. Order 25, order 26 Majors 1-3 and Minors 4-11 are each fixed in the code I read. I could not run code, so no test, mutation or lint result is confirmed.

Disclosure: I opened `handover/evidence/P1m-fix/INDEX.md` for its first line only (the title) while hunting for the ticket. I used nothing from it. I read nothing under `handover/reviews/`. The ticket text is in `handover/tickets/P1.md` (there is no `P1m.md`), and I read its P1m test and mutant paragraphs.

| id | severity | file:line | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Minor (UNVERIFIED, needs a Windows run) | `tests/test_mutation_runner.py:333-345`; mutant "runner: a link out of the tree is listed" in `tests/mutation_runner_mutants.py:99-101` and the Windows note at `:19-21` | The killer makes the folder junction first and asserts it is refused (label "a file listed through a folder link"), then makes the file link. On Windows, `os.walk` probably enters a junction (`DirEntry.is_symlink()` is false for a junction). Then the folder case reaches the real-path check, and the mutant `if True:` fails the FIRST assert with a label that does not contain `expect` ("a file link out of the tree was listed"). The verdict on Windows is WRONG_REASON, never KILLED, even with the symlink privilege. The docstring blames only the privilege, so it is wrong or incomplete. | Split the file-link case into its own test, which is the killer and skips only on 1314. Or put the file-link assert before the folder-link assert. Then state in the docstring what Windows really gives. |
| R2-COR-2 | Minor | `tools/mutation_runner.py:180-181`, `:185-204` | After a normal exit `_kill_tree(proc)` runs on a pid that `wait()` has already reaped. On Windows `taskkill /F /T /PID <dead pid>` cannot find the children (the docstring says so) and, if Windows reuses that pid, it kills an unrelated process tree. On POSIX `killpg(proc.pid)` has the same pid-reuse chance once the group is empty, but it is tiny. | On Windows, skip the call after a normal exit. Or only kill after normal exit when `_IS_WINDOWS` is false. Update the "kills the group once more" test to POSIX only; it already skips on Windows. |
| R2-COR-3 | Nit | `tests/mutation_runner_mutants.py:73,125,182` (CRASHROW), `:85,96` (FORGED), `:66-72` (JUDGE) | The claim "each mutant has its own killer test" is false for 8 of the 37. Three mutants use JUDGE, three use CRASHROW and two use FORGED. The JUDGE ones differ by `expect`, so they are told apart. Mutants #4 ("crash counts as good") and #21 ("b3: a crash row is good whatever the exception") have the same killer AND the same `expect`, so the table cannot say which edit was caught. #4's natural killer is `test_the_runner_kills_a_mutant_of_a_tiny_package` (the `crash mutant` assert), not CRASHROW. #8 and #12 are the same edit written two ways. | Point #4 at the tiny-package test with its message ("a mutant of a tiny package was not killed as expected"). Or say in the mutants docstring that shared killers are allowed when `expect` or the edit differs. |
| R2-COR-4 | Nit | `tools/mutation_runner.py:131` | `_leading_class` uses `removeprefix("E")`. A line without the pytest `E   ` prefix (the JUnit `message` fallback at `mutation.py:104`) loses the first letter of a class that starts with E, so "Exception" becomes "xception". A declared `crash_type="Exception"` or `"EOFError"` is then never good. It fails safe (not good), not unsafe. | Strip `E` only when it is followed by whitespace (a regex such as `^E\s+`). Add a test row. |
| R2-COR-5 | Nit | `.github/workflows/ci.yml:121,125` | Lint and format now cover `tools`. Bandit (`-r src demos`) and Semgrep (`src tests demos`) still skip `tools/`, which holds the one subprocess-spawning runner. Order 25 item 2 asked only for ruff, so this is a gap against PENDING LEAD 22 in `tickets/P1.md` line 238 (ruff check, ruff format and bandit), not against the order. | Add `tools` to the bandit and Semgrep paths, or state in the PR body that they are left out on purpose. |
| R2-COR-6 | Nit | `tests/mutation_runner_mutants.py:24-26` | The "no mutant" list omits `test_the_leading_class_of_an_error_line_is_parsed_not_searched` (its guard `_leading_class` has no mutant of its own). "Timeout and baseline defaults" is loose: the `seen == [9, 9]` fallback has no mutant, while `test_the_baseline_run_gets_its_own_timeout` has #16. | List the test and the unmutated fallback exactly. |

**Verified (by reading the code)**

1. **Order 25 (a), symlink skip:**
   - `_symlink_or_skip` skips only when `sys.platform == "win32"` and `exc.winerror == 1314`; any other error re-raises.
   - Folder cases use `_winapi.CreateJunction(target, link)` on Windows (`_dir_link`) and a symlink elsewhere.
   - `tests/test_mutation_runner_helpers.py:172-190` pins this with a fake 1314, a Windows error 112, EPERM on Linux, and 1314 on Linux (both must raise).
2. **Order 25 (b), `_pid_alive` Windows branch:**
   - Access is 0x1000 and STILL_ACTIVE is 259.
   - `OpenProcess` returns `c_void_p`. A null handle returns `get_last_error() == 5` (access denied means alive; 87 means dead).
   - `CloseHandle` is in a `finally`, so the handle is closed even when `GetExitCodeProcess` fails.
   - A failed read raises OSError, which `_pid_alive_windows` catches (with AttributeError) and sends to `tasklist`.
   - `tasklist` is called by `%SystemRoot%\System32\tasklist.exe` and matched as `,"<pid>",`, so 14242 does not match 4242.
   - POSIX keeps the signal check plus the `/proc` `Z` test, so a zombie counts as dead.
3. **Order 26 Major 1:** the Windows `_pid_alive` fix is the one in item 2. `test_a_timeout_kills_the_whole_process_tree_not_only_pytest` still runs on Windows (no skip). It is the only test that uses the `taskkill /T` path with a real grandchild.
4. **Order 26 Major 2:**
   - `test_the_runner_refuses_paths_that_leave_its_tree` is split into one test per guard (absolute/drive, dotdot, stream, short expect, `_inside` link, `_locate` link, forged path, test/fixture paths).
   - `_must_refuse(label, ...)` makes the label the first assert line, so `expect` is a fragment of that message.
   - The meta test (`test_mutation_runner_meta.py:93-95`) forbids `expect` equal to, inside, or containing the killer name. That is stronger than order 26 asked.
   - Every mutant has `test_file`, `only_test` and `pinned == PIN + only_test`.
5. **Order 26 Major 3:**
   - `except BaseException: _kill_tree(proc); raise` is at `tools/mutation_runner.py:177-179`, and `_kill_tree` runs after a normal exit at `:181`.
   - `test_an_interrupt_while_waiting...` checks that the pid killed equals the child pid and that the interrupt propagates.
   - The test reaches that branch: its patched `proc.wait` raises KeyboardInterrupt after the pid file exists.
6. **Order 26 Minors 4-11:**
   - **4:** the split symlink test, the junction, and the POSIX-only and privilege notes are in the mutants docstring.
   - **5:** `crash_type` is compared as the parsed leading class (`_leading_class`), with a lookalike test and mutant #36.
   - **6:** the env-allowlist and live-tree mutants are added, along with six more (taskkill path, interrupt, finished-run, ini, baseline 0, stream name). The docstring lists the unmutated guards honestly, apart from the small gap in R2-COR-6.
   - **7:** `-c <empty mutant_run.ini> --rootdir=<copy>` is in the command at `:160`, with a test and a mutant.
   - **8:** the timeout test uses `try/finally` with `_force_kill` and polls for the pid file (`_patient_wait`).
   - **9:** `r"C:\Windows"` has a single backslash, `baseline_timeout=0` is a real timeout, and the setsid/orphan limit and the `heavy_slot` Job Object are in the module docstring.
   - **10:** the dev-tool constants exemption is in the docstring and names 900.0.
   - **11:** "lead decision / PENDING LEAD 22" no longer appears in `src/hadavin_sdk/testing/mutation.py`.
7. **Mutant table count:**
   - 37 `mutant(...)` entries, counted by hand. The count agrees with `EXPECTED_MUTANTS = 37`, with 5 on `mutation.py` (`MU`) and 32 on the runner (`MR`).
   - Names are unique, and exactly 3 mutants carry `allow_crash` and a `crash_type` (PermissionError, ValueError, ParseError).
8. **`expect` fragments and killers:**
   - For all 37 I traced the killer, the mutated code and the first `E` line. Each `expect` occurs in that killer's own assertion message: the `_must_refuse` label, the plain assert message, or the exception text for the three crash rows.
   - None is in the killer's name.
   - Within a shared killer the `expect` strings differ, except #4/#21 and #8/#12 (R2-COR-3).
   - Each `old` string occurs once in the runner or judge file, by eye against the snapshot (the meta test (g) recounts it).
9. **Manifest and CHANGELOG:**
   - The four sha256 values in `tests/fixtures/mutation_manifest.json` and in CHANGELOG lines 348-351 are textually identical.
   - The manifest's file set matches the four files named in the test.
   - `tools/__init__.py` has no content lines, and `e3b0c442...b855` is the sha256 of the empty string.
   - The CHANGELOG prose matches the code changes.
10. **ci.yml:** lines 79 and 81 are now `ruff check src tests demos tools` and `ruff format --check src tests demos tools`. The scan step is unchanged.
11. **Faked-ctypes helper tests really run the branch, on Linux:**
    - `_pid_alive_windows` does `import ctypes` inside the function, and the tests patch the same module's `WinDLL` and `get_last_error` (`raising=False`).
    - The real `c_ulong`, `byref` and `POINTER` are used, and the fake reads `ref._obj`.
    - The tests assert access `(0x1000, 0, pid)`, handle closed on the success, dead, and failed-read paths (closed list `[0x1234]`, empty on no-handle), 259 vs another exit code, 87 vs 5 on a null handle, and the tasklist argv by full System32 path.
    - They also cover a pid that only contains the number, the "no kernel32" fallback, and `_pid_alive` choosing the Windows probe only when `sys.platform == "win32"`.
    - `_dir_link`'s junction call is asserted with a fake `_winapi`.
    - The kernel32 stub does not prove real argtypes or restype behaviour. The test docstring says a real Windows run is still needed.

**Not checked / UNVERIFIED**

- **Hashes:** I did not recompute the sha256 values of `testing/__init__.py`, `mutation.py` and `mutation_runner.py` (no hashing tool, and the line-ending normalisation). UNVERIFIED.
- **Test and lint runs:** I did not run the tests, the 37 mutants, or ruff check/format. UNVERIFIED that they are green, including the new `tools` lint on a file I could not see for the other `tools/` content.
- **Linux mutant kills:** I traced them by reading only. Whether each mutant ends KILLED (not WRONG_REASON or OTHER_TEST) is UNVERIFIED.
- **Windows:** I did not run anything. The junction behaviour in `os.walk` (R2-COR-1), the real `ctypes` calls, and `taskkill /T` on a real tree are UNVERIFIED.
- **`uv build`:** I did not check that `tools/` stays out of the wheel and sdist (order 26 closing item). I did not see `[build-system]` settings beyond `uv_build` and the unchanged default.
- **`tests/__init__.py`:** I did not confirm it exists at the PR head. `test_mutation_runner_helpers.py:17` imports `from tests import test_mutation_runner`, and the meta test already uses `from tests import ...`.
- **Other lint and scanner jobs:** I did not check Semgrep, CodeQL or SonarCloud on the new files.
- **Evidence and review files:** I read none of the P1m evidence or review content (apart from the one title line above), so I do not know whether the numbers in the PR body agree with the code.
