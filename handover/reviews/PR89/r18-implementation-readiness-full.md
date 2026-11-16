<!-- full hand-back report of sub-agent a384da9c, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

REVIEW of PR 89 (db0d9eb), snapshot only. Mode: REVIEW, readiness to merge.

Verdict: I found no Blocker and no Major by reading. I ran nothing, so merge readiness rests on CI actually being green (see "Not checked"). Findings below are all Minor.

Files read in full: tools/mutation_runner.py, src/hadavin_sdk/testing/mutation.py, CHANGELOG.md (lines 1-301 and 396-415), tests/conftest.py, tests/test_mutation_runner_meta.py, tests/fixtures/mutation_manifest.json. I read the diff hunks for tests/mutation_runner_mutants.py in full. I read only parts of tests/test_mutation_runner_keywords.py (head, the test-name list, the timing tests, lock-name cases). I did not open the diff for tests/test_mutation_runner.py.

FAILURES FIRST: none confirmed. Nothing I could read fails an acceptance rule outright.

MINOR FINDINGS

1. CHANGELOG.md:11 (CI claim not provable from the snapshot)
   - It says CI passes `postgresql://postgres@localhost:5432/postgres` in named steps of `.github/workflows/ci.yml`, "so nothing in this repository changed for that reason". ci.yml is not in the snapshot or the diff.
   - Scenario: if the CI address differs, the refusal rules (quotes, backslash, non-ASCII, over 2,000 characters) could stop the mutation run in CI.
   - Fix: the author should attach the actual ci.yml lines or run output. The URL grammar in `_address_parts` does accept this shape (login, host, port, one database).

2. tools/mutation_runner.py:393, :657, :726 (new `# type: ignore[...]`)
   - Rule: "no suppressions". The ruff, bandit and pytest gates are unaffected, but mypy is not named in the gates either, so this is only a rule-wording issue.
   - Line 393: `_NOT_WHITE` is `\S*` and always matches, so the ignore can go. Use `m.end(2) if ... else`, or take the word with `value[m.start(2):].split(None, 1)[0]`.
   - Line 657: type the `code` argument properly.
   - Line 726: the msvcrt ignore carries `unused-ignore`, so it is a deliberate hedge.
   - The pre-existing `noqa: S603` and `noqa: S314`/`nosec B314` are justified in comments.

3. tests/test_mutation_runner_keywords.py:2622, :2759, :2767 (literal credentials in the tests)
   - Rule: fake credentials must be built from parts. Most are (`"Zq9x" + ...`), but `postgresql://svc:12/45@db.invalid/app` is a literal password in a URL, used three times.
   - Scenario: a secret scanner or Sonar rule S2068 flags it. The test also uses literal `pwd=a&` strings (:2797).
   - Fix: build `12/45` from parts like the others. The pattern still works, as the test needs the slash.

4. tests/test_mutation_runner_meta.py:100-107 (no duplicate-name guard for the new test file)
   - Test (a) checks duplicate test function names only for test_mutation_runner.py. The keyword file has about 150 tests and about 155 mutants pinned to its function names.
   - Scenario: a later copy-paste duplicates a `def` name, the first is silently shadowed, and the mutant's pinned killer changes meaning. Check (c) only tests that the name exists.
   - I eyeballed the name list and saw no duplicate today.
   - Fix: apply the same `len(tests) == len(set(tests))` check to KW.

5. Docs wording that could mislead
   - tools/mutation_runner.py:942: the parenthetical "(``canary``)" after the lock RuntimeError is garbled; it should name the lock.
   - Module docstring and CHANGELOG say `first_lines` holds "pytest's message" for COLLECTION ERROR. The code (mutation.py `_first_failure`) prefers the first `E` line of the body and falls back to the `message` attribute. The CHANGELOG evidence shows `E AssertionError: at import`. State which line it is.

6. CHANGELOG.md:6-25 (readability)
   - One bullet holds about 20 sub-bullets and a single-paragraph glossary of about 15 terms. The wording rule asks for plain, followable text.
   - It is accurate but hard to review or upgrade from.
   - Fix: split into "what changes for every caller", "new keywords" and "limits". This is not a gate failure.

7. Windows
   - The mutants file header now says honestly that only Linux is run and the Windows notes are written from skip markers. About 15 lock and signal mutants SURVIVE on Windows.
   - A demo that copies the files and runs the list on Windows will exit 1.
   - Acceptable as documented, but state it in the CHANGELOG "Re-copy needed" bullet too.

CHECKED AND CONSISTENT
- Manifest pins and the CHANGELOG list agree: mutation.py `23f5d9d7...`, mutation_runner.py `2842c966...`. The old runner pin `489517fb...` quoted as evidence matches the old manifest value.
- Mutant count: I counted 155 new `kmutant` lines (diff lines 356-510) plus 62 old, which gives the 217 that the meta test expects. The conftest mutant count is 4 (lines 467, 508, 509, 510) and the judge mutant count 6 new, in line with the 12 and 4 asserted.
- Config location: `PASS_ENV_ALLOWED`, `MAX_*` and the other tool constants stay in the tool file, with a written reason (copied byte for byte, no wheel, no config surface). That is an explicit exception to "config in one place"; the repo guard tests were not read to see whether they accept it.
- Error paths all have a defined result:
  - an unlisted name raises ValueError before anything runs
  - a bare string raises TypeError
  - a missing conftest raises ValueError before any temp folder
  - a baseline that skips raises RuntimeError
  - a canary failure raises `CanaryFailed` with `.rows`
  - lock-file problems raise RuntimeError with a cause
  - timeout, reaped, junit-refused, junit-missing, collection, fixture and skipped rows are defined and masked
- Timing tests (30 s and 60 s bounds) are secondary checks only; the kills come from result text, so they are not flaky killers. They are not marked `perf`, though CHANGELOG:48 describes a separate perf step, so they run in the main step.
- Keyword killers mostly assert with messages that name the guard; the meta test enforces that `expect` comes from the killer's own strings.
- `mutation.py` is shipped (wheel) and `judge` changed behaviour (ERROR instead of CRASH or KILLED when no test id is known, plus new public names). The CHANGELOG discloses this as an upgrade step.

NOT CHECKED
- I did not run or inspect any test run, ruff check, ruff format --check, bandit -ll, the repo guard tests (lock-in guard, vendor-name list, secret-literal scans), CodeQL, SonarCloud or CodeRabbit. I had no shell.
- I did not recompute the sha256 values, so I cannot confirm the pins match the files.
- Evidence runner output was not supplied; I did not verify the claim that the new tests fail on the old code.
- I did not read the bodies of most of the roughly 2,900 lines in tests/test_mutation_runner_keywords.py, the test_mutation_runner.py diff, or the pyproject ruff/bandit configuration (so E501 and format risk for the very long docstring lines and `# fmt: skip` blocks is unassessed).
- The behaviour claims against real pytest 9.2.0 (`failed on setup`, `collection failure`, the `...` shortening) were not re-observed.
- I did not review `.github/workflows/ci.yml`, `.claude/rules/*` file contents beyond the CLAUDE.md summary, or Windows and macOS behaviour.
