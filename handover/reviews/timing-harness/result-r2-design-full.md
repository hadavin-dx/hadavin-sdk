<!-- full hand-back report of sub-agent ac12b987, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, round 2, core/fix-timing-harness-flake @ a8c269c8. Mode: REVIEW. Read-only; nothing was executed.

## Verdict
NOT CLEAN. Blocker 1, Major 2, Minor 9.

- The helper's code and its clockless tests hold up by reading. I found no defect in `tests/fixtures/timing.py` and no caller that became weaker.
- What is open: there is no independent evidence at this head; the flake is fixed as a class only for the four stand-in tests; one written-rule break (the hand-repeat note); several claims run past what was measured.
- Evidence: `/home/user/hadavin-sdk/handover/evidence/timing-harness/a8c269c/RESULTS.md` does not exist. Only `fa3f8c1/RESULTS.md` is there, for the previous design (wall clock, fastest of three, sizes not taking turns); I read it. Every run-dependent claim at a8c269c is therefore unproven.

## Findings

### B1. Blocker (gate, no code change): no independent evidence at a8c269c
- Scope: `/home/user/build/snap/flaky-a8c269c/CHANGELOG.md:264-281`; `tests/fixtures/timing.py:31-37`.
- Unproven at this head:
  - 200 of 200 and 127 of 127 stand-in runs;
  - the seven-row ratio table;
  - "All 216 ... and all 18 ... pass";
  - 129 s and 95 s run times;
  - "80 tests" (the count is right by my own count; that they pass is unproven);
  - 21 mutants caught.
- The fa3f8c1 evidence cannot be carried over. It showed 2 failures in 30 runs beside four busy loops (one missed quadratic, one false alarm), which is the reason this round changed the design.
- The CHANGELOG names no raw log for its table.
- Rule broken: CLAUDE.md Honesty ("never write passed without the command and its output"); honest-tamper-evidence-claims ("never state a number as measured unless the source file was read").
- Smallest fix: the EVIDENCE RUNNER, alone on the machine (review-loop-speed-rules: timing tests run alone), saves at a8c269c:
  - (a) `pytest -m perf tests/test_k5_perf.py tests/test_migration_numbers.py`, at least 20 times without and 20 times beside four busy loops, with fail counts per test;
  - (b) the four stand-ins 200 and 200 times;
  - (c) one run that prints the measured big/small ratio of every real case (the 216 sweep cases, 18 lexer cases, 5 end-to-end units, the two patterns at `test_k5_perf.py:63-64`);
  - (d) wall time against processor time of one big call for the sweep, the lexer and `redact_untrusted`;
  - (e) the mutant script with its duration;
  - (f) `tests/test_timing_fixture.py` with its duration, and the new tests against main's `timing.py`;
  - (g) the full suite and lint once.

### M1. Major: the hand-repeat note is a deferred, fixable check, and its stated reason is now false
- Scope: `tests/test_k5_perf.py:81-82`, `:105`; `CHANGELOG.md:278`; `tests/fixtures/timing.py:164`.
- The note still says "wall clock on a shared runner is noisy; a red run is repeated once by hand ... one red is noise". On Linux these five tests now use processor time through the same helper as the stand-ins, so the reason given is wrong.
- The CHANGELOG admits the end-to-end tests were not run under load. That is a five-test, few-second run the builder already had the loop for. It is none of the three allowed exceptions (impossible, needs the owner, needs a third party).
- Scenario 1: nobody knows how close the end-to-end ratios are to the limit of 48. No number for them exists in the snapshot. The builder's own table shows processor time moving an "n log n" ratio from about 20 to 25.1 (+24%). A unit whose true ratio is near 38 would fail by chance.
- Scenario 2: a real regression from 30 to 45 fails about half the time, and the note tells the developer to call a single red "noise".
- Scenario 3: the failure text makes it worse. `problems` prints only "grows faster than its input", and `test_k5_perf.py:105` is a bare assert. A person cannot tell 49x from 250x, so re-running is the only move left.
- Rule broken: fix-dont-defer-be-honest rules 1 and 2; class-level-fixes (the fix was proven for one user of the choke point, not all).
- Smallest fix:
  1. Put both times, the ratio and the limit in the `problems` line and in the end-to-end assert message.
  2. Take B1 (a) and (c).
  3. If the largest real ratio is well under the limit (the stand-in noise was at most about +25%), delete the re-run policy.
  4. If some case sits near the limit, that is a growth to look at; a retry does not fix it.

### M2. Major: sibling timing bounds were neither fixed nor named
- Scope: `tests/test_k5_perf.py:108-124`; `CHANGELOG.md:23`.
- `test_the_slowest_measured_shape_at_the_cap_stays_under_a_ceiling` is in a changed file and is untouched. It keeps a fixed 30 s wall-clock bound (`time.perf_counter`) with its own built-in retry ("best of two").
  - Margin: 3.8 s at load 10 in the fa3f8c1 evidence, 7.2 s on the Windows laptop named in its docstring.
  - Scenario: on that laptop a 4x slowdown twice in a row turns it red. review-loop-speed-rules records exactly that machine state ("8+ agents ... timing tests flaked").
  - The risk is low, but it is the same class and the CHANGELOG is silent on it.
- `CHANGELOG.md:23` names a "perf-marked 100 KB timing test" in `tests/test_k5_layers.py`. That file is not in the snapshot and not in the diff, so I could not check it. Nothing says whether it uses the helper or its own wall clock.
- Rule broken: class-level-fixes ("grep for siblings"); fix-dont-defer rule 4 (say what was not checked).
- Smallest fix:
  - Read both ceiling readings from `timing.CLOCK` (processor time on Linux), or keep the wall clock and say so with the margin under "What it does not see or survive".
  - State in the CHANGELOG what `tests/test_k5_layers.py` does, and route it through the helper if it times with the wall clock.
  - Add one sentence listing the search done for other timing assertions.

### Minors (fix in the same push; no new round needed)
- **m1. Windows.** `CHANGELOG.md:262`, `timing.py:42-44, 67`, `test_timing_fixture.py:314-319`.
  - The limit is stated, so it is not hidden. But "On Windows (wall clock) ... gave one false alarm in a hundred" reads as measured on Windows; it is the Linux wall-clock row.
  - "Windows was not run" is written nowhere in the snapshot.
  - The test repeats the code's own condition, so the Windows side runs on no machine. A wrong platform string would pass every test and mutant on Linux.
  - The mutant "the wall clock everywhere" cannot be killed on Windows, so the mutant script would exit 1 there.
  - Fix: write "measured on Linux with the wall clock; Windows itself was not run". Make the choice a function of the platform string and test both strings on any machine.
- **m2. Overclaim in the docstring.** `timing.py:17`: "so a busy machine does not move the result". The builder's own rows show it moves (linear 14.6 to 16.8, n log n 17.1 to 25.1). Write "moves it far less (measured up to about a quarter)".
- **m3. What passes is not said in plain words** (`timing.py:9-12`). Add:
  - the rule passes anything up to 3 times slower at the big size than straight-line growth from the small size;
  - at a gap of 16, a quadratic part of up to about 15% of the small run passes, which is about 3.5 times slower at the big size (my arithmetic);
  - nothing above the big size is seen. The end-to-end big size is 64 KiB, a quarter of the 256 KiB cap, so such a part is about 10 times the linear part at the cap, where only the "curl -u" ceiling test looks.
- **m4. Two blind spots are not stated** (`timing.py:39-44`).
  - Work done in a child process is not counted.
  - A function that remembers its result per text is timed only on the remembered path, because the first real call falls in the discarded sizing batch. Main had the same exposure.
- **m5.** `test_k5_perf.py:58` still says "16x vs a 12x limit"; the test is 64x against 24x. This is left over from round 1.
- **m6. Mutant list.**
  - `migration_numbers_mutants.py:8` still says "under a minute" although the list grew; unmeasured.
  - `CHANGELOG.md:281` says "18 of them new". The diff against main adds 19 timing mutants and removes one ("the small run is not floored"). Say which count is meant.
- **m7. Round-1 leftovers in `test_timing_fixture.py`.**
  - `:272-273` ignore the `tick` parameter and run twice identically.
  - `:39` assumes two clock reads per batch, a `timeit` internal.
  - `:305` fails if the suite runs with the collector off.
  - The file's run time in the ordinary suite is unstated; it now drives several million model calls.
- **m8. Gap of 4.** `timing.py:73-77`.
  - A gap of exactly 4 is allowed, but no real-clock test uses it, and its margin for a quadratic cost is 1.33x.
  - "cannot tell a quadratic cost from a linear one" is strictly true only up to a gap of 3.
  - Either raise the floor to 8 (every real user is at 8 or 16) or reword.
- **m9. Wording.** "stand-in" is used in `CHANGELOG.md:266` without saying it is a small test function whose growth is known. `test_k5_perf.py:5` is one over-long, hard-to-read line.

## Answers to the questions
1. **Processor time.**
   - It is the right measure for the three real users as far as the snapshot shows: scanning with `re`, the pure-Python lexer and `redact_untrusted` are computing in one thread, which processor time counts in full, including C code and other threads of the process.
   - It does not see: sleeping, input and output, lock waits, child processes, swapping. Collector cost is not seen on either clock, because `timeit` switches the collector off.
   - Whether any real user has such a part I could not verify; the package source is outside the snapshot. B1 (d) settles it.
   - It also counts a plugin's background thread. A steady one inflates both sizes alike, and a burst is removed by taking the fastest batch. `time.thread_time` would miss work the function hands to a thread, so `process_time` is the better choice.
2. **Fastest of five, taking turns.**
   - The fastest batch is the right statistic for work that does the same thing on every call. Noise only adds time.
   - It can hide a cost that occurs only in some calls when the big batch is a single call. The real case of that is remembered results (m4).
   - Resizing: different call counts per size are sound. The loop overhead per call (tens of nanoseconds, my estimate) could hide a quadratic cost only if the small call took about 10 ns.
   - A first-call cost (the import inside `_e2e`, a pattern compile) lands in the sizing batch. The re-size at `timing.py:133-137` then corrects a batch sized too short; I traced it.
3. **Limits.** See m3 and m8. The exponents 1.79, 1.53 and 1.40 are correct. Refusing a gap under 4 is right as a floor.
4. **Windows.** Stated, but with a misattributed figure and a branch no test runs (m1).
5. **Class.** Not closed (M1, M2).
   - Counting operations is not better for the stand-ins. They exist to prove the real clock separates the shapes, and the clockless tests already cover the rule's logic.
   - It would be better for the lexer only, which is our own pure Python. That is optional and not needed for this change.
   - It is not possible for the pattern sweep or the end-to-end tests: the cost is inside the C regular-expression engine, which exposes no step count.
6. **Claims.** See B1, m1, m2, m6.
   - "much steadier" is suitably hedged.
   - The stopped-early 127, the missing eight-loop runs and the missing end-to-end load runs are stated honestly.
   - 327 clean runs bound the failure rate only to about 1% (2.4% under load). The stronger argument is the margin: worst n log n ratio 25.1 against 48, lowest quadratic 212.

## Round-1 checklist (verified by reading; run results unproven)
| Item | Status | Where verified |
|---|---|---|
| B1 evidence | Not resolved at this head | Builder's figures cover only the four stand-ins, not `pytest -m perf` as asked |
| M1 statistics | Resolved in code | Turns `timing.py:129-131`; five repeats `:63`; limits stated `:39-44`; slow-spell tests `test_timing_fixture.py:291-300` |
| M2 size gap | Resolved | Sweep at 16 KiB to 256 KiB `test_k5_perf.py:30`; stand-ins at the same sizes `test_migration_numbers.py:843, 851`; exponents stated |
| M3 constants and mutants | Resolved | 21 mutants, each `old` text present once in `timing.py`, each killer traced; n log n and gap-16 models; literal pins (20,000 calls, 6 calls, 11.9/12.1, 47.9/48.1) |
| m4 big time checked | Resolved | `timing.py:99` |
| m5 minimum gap | Resolved | `timing.py:73` |
| m6 checks before work | Resolved | `timing.py:147-149` |
| m7 "too fast to time" | Resolved (stated) | `timing.py:49-51`; loop overhead not mentioned |
| m8 sweep names the case | Resolved | `timing.py:155-167`; numbers missing, see M1 |
| m9 collector off | Resolved (stated) | `timing.py:22-23`, `CHANGELOG.md:260` |
| m10 weak assertions | Partly | Fixed: name checks, call volume, float-text mutant. Open: m7 |
| m11 re-run policy | Partly | Claim withdrawn for end-to-end; policy text now wrong (M1); `:58` not fixed (m5) |
| m12 CHANGELOG | Mostly | Open: "under a minute" header and the count of new mutants (m6) |

## Not checked
- Nothing was run.
- Package source: `redact_untrusted`, `PATTERNS` (the count 216), the lexer; whether any of them waits, uses threads or child processes, or remembers results.
- `tests/test_k5_layers.py`, and any other user of the helper outside the six changed files.
- `tools/mutation_runner.py`, the CI workflow, pytest markers and plugins.
- `tests/test_migration_numbers.py` outside lines 780-875 and the import hunk.
- `tests/migration_numbers_mutants.py` lines 60-300 (the non-timing mutants).
- `CHANGELOG.md` lines 354-419: keyword search only.
- `DIFF-vs-main.patch`: I read its `test_k5_perf.py` and `test_migration_numbers.py` hunks; for the other files I read the full files and `DIFF-fix1.patch` instead.

Files read:
- `/home/user/build/snap/flaky-a8c269c/tests/fixtures/timing.py`
- `/home/user/build/snap/flaky-a8c269c/tests/test_timing_fixture.py`
- `/home/user/build/snap/flaky-a8c269c/tests/test_k5_perf.py`
- `/home/user/build/snap/flaky-a8c269c/tests/test_migration_numbers.py`
- `/home/user/build/snap/flaky-a8c269c/tests/migration_numbers_mutants.py`
- `/home/user/build/snap/flaky-a8c269c/CHANGELOG.md`
- `/home/user/build/snap/flaky-a8c269c/DIFF-fix1.patch`
- `/home/user/build/snap/flaky-a8c269c/DIFF-vs-main.patch`
- `/home/user/build/snap/flaky-a8c269c/result-r1-full.md`
- `/home/user/hadavin-sdk/handover/evidence/timing-harness/fa3f8c1/RESULTS.md`

Standards read:
- `/root/.claude/plugins/cache/egm/egm/0.1.1/agents/design_critic.md`
- `/home/user/hadavin-sdk/CLAUDE.md`
- `/home/user/hadavin-sdk/.claude/rules/class-level-fixes.md`
- `/home/user/hadavin-sdk/.claude/rules/fix-dont-defer-be-honest.md`
- `/home/user/hadavin-sdk/.claude/rules/honest-tamper-evidence-claims.md`
- `/home/user/hadavin-sdk/.claude/rules/wording-clear-for-everyone.md`
- `/home/user/hadavin-sdk/.claude/rules/verify-tests-and-evals.md`
- `/home/user/hadavin-sdk/.claude/rules/review-loop-speed-rules.md`
