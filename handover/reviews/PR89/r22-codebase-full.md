<!-- full hand-back report of sub-agent a8db9264, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW r22, PR89 head c2f98f49 (snapshot /home/user/build/snap/pr89-c2f98f49/). Verdict: NOT READY. There is one Major and no Blocker. The Major is a false statement in the documentation and costs a re-pin to fix.

Limits of this review:
- I had read, grep and glob only. I ran no tests, no mutants, no mypy and no hash recomputation. All kill claims below come from reading the mutant and the killer test, not from a run.
- /home/user/hadavin-sdk/handover/evidence/PR89/c2f98f49/EVIDENCE-REPORT.md does not exist yet. The newest evidence folder is 7a2eb4c.

## Major

**M1. "A bare string in place of a list is a TypeError" is false for three arguments.**
- Where it is stated:
  - tools/mutation_runner.py:105-106, the module docstring about refusals 1 to 12.
  - tools/mutation_runner.py:1466, the `run_mutants` docstring.
  - CHANGELOG.md:34.
- The code raises TypeError only for `pass_env` (:494), `throwaway_hosts` (:728) and `shown_classes` (:958).
- `tests`, `extra_dirs` and `only` are not checked.
- Failure scenarios:
  - `run_mutants(root, ms, "tests/test_x.py")`: the loop at :1691 calls `_relative` on each letter. The letter "/" gives a ValueError ("path escapes"), not a TypeError. A string with no slash, such as `"test_x.py"`, passes the loop letter by letter.
  - `extra_dirs="fixtures"`: each letter is accepted. At :1735 `_inside(snap, "f").exists()` is false, so the fixtures are silently not copied.
  - `only="flip"`: at :1810 the test `any(o in m.name for o in only)` runs per letter, so it selects far more mutants than intended.
- Fix: limit the sentence to the three keywords named in the code, or add `isinstance(..., str)` checks.
- Any docstring edit changes the byte-copied runner, so the pin in tests/fixtures/mutation_manifest.json and in the CHANGELOG list (:497) must change with it.

## Minor

**m1. The order test does not pin step 8 against steps 9 to 11, and its docstring says it pins all 13.**
- Location: tests/test_mutation_runner_keywords.py:4475-4533.
- The `many` value (:4486) is a valid-shape URL with a listed host. It passes steps 9, 10 and 11, so it is not wrong for any later step.
- The next value, "not an address" (:4503), has no password forms, so it passes step 8.
- Moving the `_refuse_unsafe_address` loop (tools/mutation_runner.py:1706) before `_secret_values` (:1705) leaves both values giving the same messages. Step 8 versus steps 9 to 11 is therefore not pinned, and there is no such mutant.
- Step 7 versus step 8 is also unpinned. That is less likely to matter, because the odd-character check sits inside the decode loop.
- A value that has 901 layers and also an unlisted host (or a bad shape) would pin the order.
- The test docstring claims "everything a LATER step refuses is still wrong", which is false for step 8.
- The other 11 steps are pinned. Step 1 against 12 holds because `stray` is wrong in every call. The 6, 7 and 9 pair holds through the first two address values.

**m2. The 901-layer value is correct for step 8, but the 300 bound itself is unpinned.**
- The password is "%" + "25"×900 + "40". It decodes in 901 steps to "@", has no odd character, and is about 1,843 characters long, which the assert at :4489 keeps under the 2,000 limit.
- Removing step 8 makes the test fail on the message, so the test does guard the refusal.
- Only one mutant touches the limit: tests/mutation_runner_mutants.py:491, which replaces the check with `if False`.
- Nothing pins `MAX_SECRETS = 300`, `>` versus `>=`, or the "more than 300" wording in the docstring (:119) and CHANGELOG (:42). Any bound from about 300 to about 5,000 passes the 901-layer test.
- By contrast, EDGE_MIN, MAX_FRAGMENT_HITS and MAX_VALUE_CHARS all have boundary mutants.

**m3. The "300 seeded draws" statement is true, but the property test is partly wrong-reason.**
- Location: tests/test_mutation_runner_keywords.py:4116-4135.
- It draws 300 values into a set and asserts at least 290 unique ones remain. The statement in CHANGELOG.md:107 is accurate.
- The alphabet includes ":", "-" and ".". `_must_refuse` (:4127) checks only that some refusal happens, not which one.
- A draw such as "ab:" or "-x" can be refused by the shape grammar (step 9) instead of the host list (step 11), so such draws do not test the host rule.
- The `near` list is fine.

**m4. Two of the three bare-string TypeError guards have no mutant.**
- Only the `pass_env` guard has one (mutants file :400). Its `old` text includes `"pass_env is`, so the replace touches only that guard.
- The guards at tools/mutation_runner.py:728 and :958 have tests (tests/test_mutation_runner_keywords.py:4174 and :3533) but no mutant.
- The mutants-file header does not list them among the tests without a mutant. It says it does not list them all.

**m5. CHANGELOG.md:57 is broader than the code.**
- It says "The environment is read once... A variable changed during the run changes nothing."
- `XDG_RUNTIME_DIR` is read later, in `_lock_dir` (tools/mutation_runner.py:1105), and `tempfile.gettempdir()` is called there too.
- The module docstring says so at :244. The CHANGELOG sentence should be limited to the passed variables.

**m6. The `noqa: S603` comment on the taskkill call (tools/mutation_runner.py:1363-1364) says "Fixed argv".**
- The program path comes from `_taskkill()` (:427-430), which reads `SystemRoot` or `SYSTEMROOT` from the environment.
- That is the same trust level as PATH, and a planted `SystemRoot` is the caller's own choice. Still, the comment should say "program path from SystemRoot".
- Justification verdict:
  - `noqa: S603` on the Popen at :1305: justified. The executable is `sys.executable`, there is no shell, and caller strings are only pytest operands that `_plain_operand` has refused when they start with "-" or "@".
  - `noqa: S314 # nosec B314` at src/hadavin_sdk/testing/mutation.py:138: justified. The size ceiling (:131), a case-insensitive DOCTYPE/ENTITY refusal (:133-135) and a stdlib-only constraint come before it. Lower-casing makes the refusal stricter than XML itself.

**m7. Huge port: accepted, harmless, and inconsistent with `connect_timeout`.**
- The URL regex at :632 takes `([0-9]+)`, and `_ADDRESS_VALUE["port"]` at :644 takes `[0-9]+`. So 99999999999 is accepted, as are 0 and leading zeros.
- The host is still checked against the list, and `connect_timeout` is capped at 5 digits (:650). So the exposure is the database library's own refusal.
- The lock-name spelling is documented. The docstring says nothing about the port range.
- Accepting it is fine. Either bound it to 5 digits like `connect_timeout`, or say "no range check" in the docstring.

**m8. The mypy count is not pinned by any test.**
- The claim "13 errors: 12 POSIX plus 1 import" matches evidence/PR89/7a2eb4c/mypy-win32-errors.txt. That file has 13 lines: 4 getuid, O_DIRECTORY and O_NOFOLLOW, P_PID, WEXITED, WNOHANG and WNOWAIT, killpg and SIGKILL, plus the import error.
- My read of the code reproduces 12 POSIX errors. The `hasattr(os, "waitid")` guard at :1338 appears to narrow the `waitid` call itself.
- Any new `os.getuid()` call, or any other POSIX-only name, silently changes the number. That is acceptable for a documented snapshot count, but it is not guarded.

## Checks that came out clean

**The two new tests that pass on the old code have real mutants.**
- The mutants are tests/mutation_runner_mutants.py:531 and :532.
- `test_a_link_to_a_private_folder_is_no_runtime_folder_for_the_lock` (test :4904) with `os.lstat` changed to `os.stat` at tools/mutation_runner.py:1088:
  - A link to a 0700 folder then counts as private.
  - The assert at :4911 fails, and so would the `_lock_dir().parent` assert at :4916.
  - This is a real mutant and a fail-on-removal test. It guards behaviour the old code already had.
- `test_a_failed_baseline_with_an_unusable_result_file_says_only_how_the_run_ended` (test :4919) with the `except _UNUSABLE_JUNIT:` at :1585 changed to catch `ZeroDivisionError`:
  - A ValueError or SyntaxError then escapes.
  - The test turns that into "raised X", which differs from the expected text, so it fails.
  - This is real. The three inputs (truncated, bad byte, DOCTYPE) all land in the ValueError/SyntaxError part of `_UNUSABLE_JUNIT`.
  - The OSError part is not tested on this path. Mutant :549 covers it only for the row path.
- Mutant :533 (raise inside the except block) is a separate chain test and is fine.

**Counts and pins.**
- The mutants file has 261 `mutant(`/`kmutant(` entries (62 plus 199), which matches CHANGELOG :108 and the "199" in the header.
- The four mutants with `allow_crash=True` match the header. The fifth grep hit is the header text itself.
- The manifest and CHANGELOG :494-497 carry identical hashes, and tests/test_mutation_runner.py:1534 enforces them against the files.
- I did not recompute the hashes myself. I could not confirm that the `mutation.py` docstring edits claimed this round are reflected in the pin, because `mutation.py`'s hash looks unchanged from the earlier CHANGELOG value. If the suite run on c2f98f49 passed, the manifest test passed; check that run, not my reading.

**Statements that match the code.**
- "Whole name without regard to case":
  - `_checked_throwaway_hosts` lower-cases names and keeps socket folders as written (:732-735).
  - `_address_fields` lower-cases host and hostaddr except socket folders (:687, :709).
  - The membership test at :769 is a whole-string match.
  - The test at :4137-4147 checks mixed case in both directions.
- The refusal order in the docstring matches the code order: path checks at :1691, then names, hosts, classes, conftest, then `_secret_values` (steps 6 to 8), the address checks (9 to 11), `test_file` (12), and the lock (13, RuntimeError, taken before `mkdtemp`).
- The Windows statements match the code:
  - The lock sits directly in the temp folder and nothing is checked about it (:1103, :1117, :1178).
  - `_kill_tree` is not called after a normal exit on Windows (:1319).
  - `isjunction` is looked up with `getattr` and loops over the path parts (:1528-1535).
  - I did not find an overclaim there.
- "About 70 exception class names" is consistent with the built-in exception names plus `Failed`.
- The grammar is tight against host smuggling:
  - All matches are `fullmatch`.
  - The login excludes "@", "/", "?", "#" and whitespace.
  - Every key is on the allowlist, none may repeat, and the database name has no "=" or ":".
  - I found no way to name a host that the check does not see.

Fixing M1 changes the file, so the sha256 pin changes again. Fix M1 and m1, add a MAX_SECRETS boundary mutant (m2), and re-run the 261 mutants and the pin test on the new head. Then I would call it READY.
