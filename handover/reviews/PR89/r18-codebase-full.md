<!-- full hand-back report of sub-agent a2a4d816, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Review of PR 89 (head db0d9eb) found no Blockers and no Majors, and 4 Minors. I could not run any command: this session had read, grep and glob only. Everything below comes from reading code, so none of it was reproduced. Snapshot read: /home/user/build/snap/p89-db0d9eb/.

## Findings, failures first

**1. Minor: the fixture-error and collection-error fix lives only in the runner, not at the shared judge path.**
- Where: src/hadavin_sdk/testing/mutation.py:1-18 (the "Harness contract" paragraph), lines 180-184 (`first_failure_junit`), and tools/mutation_runner.py:1057-1062.
- The module docstring still says to call `first_failure_junit(xml)` and then `judge(...)`. Only `read_junit(...).fixture_failed` and `.collection_failed` tell a fixture error from a real failure, and only `_row` uses them.
- Scenario: a demo harness that follows the documented contract (not `tools/mutation_runner.py`) gets rc=1 plus `E   AssertionError` from a fixture setup assert. That harness returns KILLED, which is the false kill this PR closes in the runner.
- I found no such caller in this repo. The risk is for repos that copy `mutation.py` on its own.
- Fix: change the contract paragraph to say that fixture and collection errors are only visible through `read_junit` and must be checked first. Alternatively, add a `judge_report(rc, report, ...)` helper that applies those checks. The class-fix rule asks for the choke point.

**2. Minor: an `OSError` from the JUnit file is uncaught in `_row`, though the baseline path catches it.**
- Where: tools/mutation_runner.py:1048-1052 and 1003-1014. `JUNIT_REFUSED` is `(ValueError, SyntaxError)`. `_junit_text` can raise `PermissionError` or another `OSError` from `lstat` or `read_text`.
- Scenario: a test or mutant that does `chmod 000 r.xml` after pytest writes it crashes the whole `run_mutants` call mid-run. All earlier rows are lost unless `on_result` was used.
- `_refuse_skips_in_baseline` (line 1021) does catch `OSError`.
- Fix: catch `(OSError, *JUNIT_REFUSED)` in `_row` and return the `JUNIT REFUSED` row.
- Test gap: no test covers this.

**3. Minor: the `NO FAILING TEST NAMED` label and the `first_lines` docs are slightly off.**
- Where: tools/mutation_runner.py:1080 and 1077; docstring at lines 112-114 and 946.
- Line 1080 gives `NO FAILING TEST NAMED` for every ERROR verdict with an empty id. That includes exit code 3 or 4 (usage error), a SIGKILL exit code of -9, or a missing JUnit file with exit code 2. The docstring says "the run failed, the JUnit file names no failing test", which is not accurate for those cases.
- Line 1077 sets `first_lines[m.name]` even when there is no E line, so the entry is `""`. The docstring says only rows "that have a first E line" get an entry.
- Fix: either change the docs, or write `""` entries only when there is a line. Optionally show `ERROR rc=<n>` for exit codes other than 1.

**4. Minor: a failed baseline gives no diagnostic.**
- Where: tools/mutation_runner.py:1205-1206.
- `RuntimeError("the unmutated copy does not pass its tests")` carries no exit code and no first failing line. With `pass_env` set, the most likely cause is an unreachable database, and the caller cannot tell that from a real failure.
- Fix: include `_run_end(base_rc)` and the masked first line from `base.xml`. The masking machinery already exists, so this is safe.

**5. Nit: stray wording in the `run_mutants` docstring.**
- Where: tools/mutation_runner.py:942. "another runner holds the lock for the same database address (``canary``)" has a leftover word.

## Checked and found correct (by reading)

- **`judge` empty-id rule.** The `not test_id` check (mutation.py:63) sits after the rc checks and before `expect`, as documented.
  - Callers: the only users of `judge` and `first_failure_junit` in the repo are the runner and its tests. The other grep hits are unrelated functions named `judge`.
  - `first_failure(stdout)` returns an empty id when no FAILED line is present. Such a harness now gets ERROR, which the docstring states.
- **`_first_failure`.** The fixture-versus-body ordering matches the author's description of real pytest behaviour: a body failure is written first, then a teardown error as a second testcase.
  - I did not re-run pytest to confirm this.
  - The tests include real pytest runs for the collection, setup and teardown cases.
- **`_plugin_module`.** The `-p tests.conftest` module identity matches how the repo's own tests import it (`from tests.conftest import ...`), so the plugin is not loaded twice.
- **Masking.**
  - The KMP head/tail scan (`_longest_overlap`) never indexes past the pattern, because the window is shorter than the pattern.
  - Overlapping `...` hits handle a secret that ends in a dot.
  - The `marked` bookkeeping marks each character once.
  - Masking covers the test id, `first_lines`, the COLLECTION, FIXTURE and SKIPPED messages, and the baseline and canary skip messages. I found no other path where secrets reach the caller. The `CanaryFailed` message holds only a mutant name and an exit description.
- **Snapshot read once and canary.** `canary` and the lock use only `environ`, and the child environment comes from the same snapshot.
- **Lock.** The file descriptor is created close-on-exec, so the child does not inherit the lock. It is released in the `finally` block.
- **New autouse fixture in tests/conftest.py.** I found no existing test that writes `HADAVIN_TEST_PG_DSN` directly, so the fixture should not break other tests.

## Not checked

- I ran no tests, `ruff`, `bandit` or `pytest`, so nothing is evidence of green.
- I did not verify the sha256 pins in the CHANGELOG or in tests/fixtures/mutation_manifest.json against the head files. This is the biggest open item: a wrong hash fails the repo guard test.
- I read only lines 1290-1540 of tests/test_mutation_runner_keywords.py (3,000+ lines) and a grep summary of the rest. I did not read tests/test_mutation_runner_meta.py, tests/test_mutation_runner.py or tests/mutation_runner_mutants.py beyond grep hits. So I cannot say whether each new mutant fails on the old code.
- The claims "pytest 9.2.0 prints head...tail with the first 12 and last 13 characters" and the two wall-clock tests (20,000 `...` under 30 s; 3,000,000 characters under 60 s) are unverified. The wall-clock tests may be flaky on a loaded CI runner.
- I did not review the CI workflow changes, Windows branches, or the signal-handling code beyond reading it.
