<!-- full hand-back report of sub-agent a1db18a8, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, round 2, core/fix-timing-harness-flake @ a8c269c8. Mode: REVIEW. Read-only; nothing was executed. Snapshot only: `/home/user/build/snap/flaky-a8c269c/`.

## Verdict

NOT CLEAN. Blocker 0, Major 1, Minor 11.

- The one Major is missing evidence, not a code defect. It closes if a RESULTS.md for a8c269c confirms the claims listed under M1.
- By static reading I found no Blocker and no Major in `tests/fixtures/timing.py`, its tests, the two users or the mutant list.
- Production code cannot loop forever (proof under "Line-by-line answers").

Evidence file: `/home/user/hadavin-sdk/handover/evidence/timing-harness/a8c269c/RESULTS.md` is NOT present (checked at the start and at the end). Only `fa3f8c1/` exists there; it describes the previous head and proves nothing for this one.

## Findings

### M1. Major: every run-dependent claim is unproven at this head
Scope: `CHANGELOG.md:258-281`, `tests/fixtures/timing.py:31-37`.
- "80 tests" is confirmed by static count (10+8+12+3+1+1+5+5+6+1+1+1+5+1+1+1+1+2+3+8+1+1+1+1 = 80; no empty parametrisation). That they pass is unproven.
- "plants 21 faults in the rule ... each must be caught": 21 confirmed by count; killed-by-run unproven (my traces below say each would be).
- Unproven as written: "it is much steadier on a busy machine"; "16 fails in 30 runs"; the whole table at `:268-276`; "200 of 200 passed"; "127 of 127 passed"; "took 129 s ... the sweep alone 95 s"; "All 216 pattern-and-text cases of the sweep and all 18 cases of the migration lexer test pass at the new sizes".
- 18 = 2 functions x 9 units is statically right. 216 cannot be checked (PATTERNS is outside the snapshot), and the test only pins `>= 150` (`tests/test_k5_perf.py:74`).
- Fix: the evidence run for a8c269c. Minimum: stand-in tests repeated idle and under load, fail counts per test, mutant script output, the 80-test file, durations.

### m1. Minor: work that waits makes the helper run very long and then answer from processor time alone
Scope: `tests/fixtures/timing.py:108-115, 124-126`; docstring `:39-40`.
- Input: on Linux, `fn = lambda t: time.sleep(0.01)` (about 5 microseconds of processor time per call).
- Actual: `batch(1)` reads about 5e-6 s; `_more_calls` asks for about 4,800 calls; one batch is 48 s of wall time; six or more batches per size. There is no wall-clock bound and no message, and the verdict is computed from processor time only.
- Expected: a loud refusal, as for the other untimeable cases.
- The docstring says waiting work "is not counted at all" but not that the run time explodes. It says nothing about child processes; `time.process_time` does not count them, so work done in a child is read as near zero.
- Current users: `_scan` (regex) and the three stand-ins are in-process and single-threaded by reading. `mn.lex`, `mn.refused_statements` and `runmap.redact_untrusted` are outside the snapshot: not verified.
- Smallest fix: read `time.perf_counter` around each counted batch and raise `ValueError` when wall time is far above processor time; add "child processes are not counted" to the docstring.

### m2. Minor: `problems` relabels a `ValueError` raised by the case's own function
Scope: `tests/fixtures/timing.py:165-166`.
- Input: a case function that raises `UnicodeEncodeError` or `json.JSONDecodeError` (both are `ValueError` subclasses).
- Actual: reported as "NAME on UNIT: could not be timed: <message>"; type and traceback are lost. The test still goes red, so nothing is passed.
- Sibling: any other exception type from a case function leaves the sweep without naming the case, and the lines already collected are lost. This contradicts the intent stated at `:158-159`.
- Smallest fix: raise a private `Untimeable(ValueError)` from `check_sizes`, `_check_time`, `_more_calls` and the unit check, and catch only that; or put `type(refused).__name__` in the line.

### m3. Minor: two non-`ValueError` paths with an injected clock only
Scope: `tests/fixtures/timing.py:114, 125, 133`.
- `took = 5e-324`: `calls * 1.2 * MIN_BATCH_S / took` is `inf`, and `math.ceil(inf)` raises `OverflowError`, which is not caught by `problems`.
- A clock difference that is not-a-number: `nan < MIN_BATCH_S` is False, so sizing ends and `seconds_per_call` returns `nan` without refusal. `is_superlinear` still refuses it through `_check_time`.
- Neither is reachable with `process_time` or `perf_counter` (differences are 0 or at least about 1e-9).
- Fix: `if not took > 0` for the ten-times branch, and clamp `wanted` before `ceil`.

### m4. Minor: the Windows arm is not exercised, and its test mirrors the production expression
Scope: `tests/fixtures/timing.py:67`; `tests/test_timing_fixture.py:316-319`; `tests/migration_numbers_mutants.py:494-502`.
- `CLOCK` is chosen once at import with `sys.platform == "win32"`. The made-up clock cannot reach that branch; the test restates the same conditional. On Linux, a mutant `"win32"` to `"windows"` survives.
- On Windows the mutant "the wall clock everywhere" is equivalent, so the mutant script reports it BAD and exits 1 there. `tests/test_k5_perf.py:110` records measurements from a Windows laptop.
- Fix: a function `_pick_clock(platform)` tested with both literals; mark that mutant non-Windows.

### m5. Minor: the boundary of the limit is not pinned
Scope: `tests/fixtures/timing.py:100`; `tests/test_timing_fixture.py:113-126`; `CHANGELOG.md:281` ("the exact limit").
- The code is strict: `t_big > 3.0 * (big / small) * t_small`; exactly 12.0x at a gap of 4 passes. Tests pin 11.9 and 12.1 only, so `>` to `>=` survives.
- No float-equality risk in the pins: 3.0 * 4.0 * 1.0 is exactly 12.0.
- Fix: one assertion at exactly 12.0, or reword "the exact limit".

### m6. Minor: the "too fast to time" refusal has no mutant
Scope: `tests/fixtures/timing.py:109-112`; the list in `tests/migration_numbers_mutants.py`.
- The builder's sentence "every one-line form of it loops forever" is not in the snapshot. The place is this `raise`: it is the only exit of both loops when a batch stays short. With `if False:` there, `min(MAX_CALLS, ...)` holds `calls` at the cap and `while (took := batch(...)) < MIN_BATCH_S` never ends on a stopped clock.
- Rule left without a mutant: "a call too fast to time is refused, never passed as linear" (`CHANGELOG.md:261`). The test exists (`tests/test_timing_fixture.py:192-204`).
- Fix: a multi-line mutant that returns `calls` unchanged and breaks the loop, or a mutant the runner expects to time out.

### m7. Minor: CHANGELOG and docstring statements that are wrong, inconsistent or unprovable
- `CHANGELOG.md:280`: "Longer batches did not make the wall clock steadier". `timing.py:37`: "Batches of 50 ms and 100 ms were no steadier". The table at `:273-275` shows narrower ranges in all three columns for both longer batches (linear width 15.0, then 11.2, then 7.5; n log n 15.1, 6.5, 10.7; quadratic 219, 65, 89). Load also differed (7 to 10 against 5 to 7), so the rows are not comparable either way.
- `timing.py:17`: "so a busy machine does not move the result". Its own figures move (`CHANGELOG.md:270`: n log n 17.1 to 25.1 on processor time). "Moves it far less" is what the data supports.
- `timing.py:33`: "(load 7 to 13)" for processor time beside four busy processes; the table row `CHANGELOG.md:271` says "8 to 13".
- `timing.py:42-44` and `CHANGELOG.md:262` name only the n log n false alarm on the wall clock. The same row (`:276`) has linear down to 2.5, a small run inflated about 6.4x; a quadratic is missed at 5.3x. A missed quadratic on Windows under that load is inside the observed disturbance and is not stated.
- `CHANGELOG.md:260`: "on Windows the wall clock, because that clock moves in 15.6 ms steps there". "That clock" reads as the wall clock; the coarse one is `process_time`.
- `CHANGELOG.md:281`: "21 faults in the rule, 18 of them new". Against main, 2 are retargeted and main's third timing mutant was deleted, so 19 are new by my count.
- `CHANGELOG.md:265`: "when most of its cases were not really compared" is unprovable here.
- `CHANGELOG.md:264`: "a cost growing as size to the power 1.40 or more is flagged" is true; the bound is 1.396.
- `tests/migration_numbers_mutants.py:8`: "under a minute" is still there with 54 mutants; unproven.

### m8. Minor: stale comments in `tests/test_k5_perf.py`
- `:58`: "# timing-based (16x vs a 12x limit)". The test at `:63-64` uses a gap of 8 (64x against 24x). Round-1 m11 named this; not fixed.
- `:81-82`, quoted: "RE-RUN POLICY: wall clock on a shared runner is noisy; a red run is repeated once by hand (`pytest -m perf -k end_to_end`); two reds in a row on the same shape are a real regression, one red is noise." The premise is stale: off Windows these tests no longer use the wall clock. `CHANGELOG.md:278` keeps the note on purpose and withdraws the claim for these tests, which is consistent.
- No automatic rerun exists in the snapshot files: no `flaky`, `rerunfailures`, `reruns`, `xfail` or retry marker. One in-test retry remains, untouched by this branch: `:117-124`, best of two `time.perf_counter` runs against an absolute 30 s ceiling. It is the only remaining wall-clock assertion in the two user files.

### m9. Minor: a fixed per-call cost at the small size hides growth, and the advice ignores it
Scope: `tests/fixtures/timing.py:12` ("a test should use 16 where the input allows it"); `tests/test_k5_perf.py:105` (small lowered from 16 KiB to 4 KiB).
- With a fixed cost F per call the ratio is (F + T_big) / (F + T_small). A pure quadratic with F = 5 x T_small gives 261 / 6 = 43.5, under the limit of 48: missed.
- Not listed under "WHAT THE RULE DOES NOT SURVIVE". The fixed cost of `redact_untrusted` at 4 KiB is unknown to me.
- Fix: one sentence in the docstring; widen the gap upward where time allows.

### m10. Minor: round-1 test leftovers
Scope: `tests/test_timing_fixture.py`.
- `:272-273`: both assertions hard-code `tick=0.001`, so they run twice identically under the `tick` parametrisation.
- `:39`: `Model.clock` assumes exactly two clock reads per batch (a `timeit` internal).
- `:305`: `assert gc.isenabled()` fails if the suite runs with the collector off. The helper itself restores the previous state and does not force it on.

### m11. Minor: a resize re-times every text
Scope: `tests/fixtures/timing.py:127-137`. When one text is short, all texts run five more batches and the earlier runs of the others are thrown away. For the end-to-end case (first small call includes an import, so sizing reads long, then a resize) the 64 KiB text is timed ten times. Cost only; the result is right.

## Line-by-line answers (`tests/fixtures/timing.py`)

**Batch loop**
- Each text has its own `calls[i]`, starting at 1 (`:123`). Per-call time is `best[i] / calls[i]` (`:135`). Small and big do not share a count.
- Growth (`:114-115`): `ceil(calls * 1.2 * 0.02 / took)`, or ten times when `took` is not above 0; at least double; capped at 10,000,000.
- No integer overflow; see m3 for `OverflowError` on a denormal `took`.

**Termination**
- Every pass through `_more_calls` at least doubles `calls[i]` or raises at the cap. Sizing takes at most about 24 batches per text; the outer `while True` at most about 48 rounds for two texts.
- Stopped clock: 1, 10, ..., 10,000,000 calls, then `ValueError`. That is about 1.1e7 calls, bounded but long if a call is slow in wall time (m1).
- A function that gets faster: handled by the resize on the fastest batch (`:136-137`), ending at the cap with a refusal.
- Coarse clock: reads 0 then whole ticks; terminates; error up to tick / batch.
- Empty `texts` returns `[]`.

**Alternation**
- Sizing is not interleaved: all sizing batches of the small text, then of the big (`:124-126`). They are not counted and act as the only warm-up.
- Counted rounds are strictly small, big, five times, small first (`:129-131`). A resize discards the round.

**Minimum, division, comparison**
- `min(r)` per text (`:132`).
- No division by a time anywhere in the ratio. `big / small` is guarded by `check_sizes`; `seconds / n` has n at least 1.
- Limit: `3.0 * (big / small) * t_small`, strict `>`. Exponents 1 + ln 3 / ln g are 1.792, 1.528 and 1.396: the stated 1.79, 1.53 and 1.40 are right, as are 1.33x and 5.3x.

**Collector**
- `timeit.Timer.timeit` disables it, runs in `try`, and re-enables in `finally` only if it was enabled. So it is restored on exceptions and not forced on.

**Validation**
- `check_sizes`, then the empty unit, then work (`:147-151`). All refusals are `ValueError`; a non-integer size is `TypeError` before any work.
- Zero calls before refusal is pinned at `tests/test_timing_fixture.py:173, 189`.

**Users**
- Sizes: sweep 16 KiB to 256 KiB (`tests/test_k5_perf.py:30, 76`); end-to-end 4 KiB to 64 KiB (`:105`); lexer 16 KiB to 256 KiB (`tests/test_migration_numbers.py:809`).
- No `perf_counter` remains in `tests/test_migration_numbers.py`.

**Clock seam**
- Injected through the `clock=` parameter. `timing.CLOCK` and `timing.MAX_CALLS` are changed with pytest `monkeypatch` only. `time` is never patched globally: no leak.

**Suppressions added**
- None in either diff (no `noqa`, `type: ignore`, `pragma`, `skip`, `xfail`).

## Mutants checked

All 21 harness mutants: `old` occurs exactly once in the head file, the killer exists, and it fails for the stated reason by trace.

| # | Mutant | `old` at | Killer fails because |
|---|---|---|---|
| 1 | `PER_SIZE` 1000 | `:62` | `[1e-11-gap4]` is the first parameter set; 16x against 4000x is not flagged |
| 2 | `PER_SIZE` 0.001 | `:62` | `[1e-09-gap4]` is first; linear is flagged |
| 3 | `PER_SIZE` 1.2 | `:62` | 11.9 is above 4.8 |
| 4 | `PER_SIZE` 3.99 | `:62` | 12.1 is not above 15.96 |
| 5 | 4 ms floor back | `:95` | limit 0.048, 0.016 not flagged |
| 6 | zero seconds passed | `:81` | `[0.0]` does not raise |
| 7 | big run not checked | `:99` | `[0.0]` returns False, does not raise |
| 8 | sizes not refused | `:71` | swapped and equal still raise through the 4x check; `[negative]` is the first that does not |
| 9 | gap under 4 not refused | `:73` | (1000, 3999) does not raise |
| 10 | `MIN_GROWTH` 2 | `:62` | (1000, 3999) does not raise |
| 11 | checks after the work | `:147-151` | the multi-line text matches; calls are not 0 |
| 12 | median | `:132` | 0.031 / 240 is not 1e-4 |
| 13 | slowest | `:132` | same as 12 |
| 14 | one repeat | `:63` | 2 calls, not 6 |
| 15 | batch a tenth | `:63` | 2,400 calls, under 20,000 |
| 16 | not sized again | `:133` | the last five batches have 1 call |
| 17 | no turns | `:129-131` | order is five small then five big |
| 18 | hand loop, collector on | `:105` | six True values seen |
| 19 | sweep stops | `:165` | the `ValueError` "too fast to time" escapes |
| 20 | wall clock everywhere | `:67` | identity check fails off Windows (m4) |
| 21 | wall clock without a clock | `:122` | real time of about 1e-7 s against the expected 1e-4 s |

- The float-shaped test ids (`1e-11`, `1e-09`, `0.0`, `0.007`) match pytest's ids. The round-1 pin `assert 0.0501` is gone.
- Still unpinned besides m5 and m6: the value of `MAX_CALLS` (any value above about 24,000 passes), and the ten-times and at-least-double growth factors.

## Round-1 checklist

| Item | Status | Where verified |
|---|---|---|
| B1 evidence | Not resolved for this head | no RESULTS.md for a8c269c (M1) |
| M1 statistics | Resolved in code; measurements unproven | turns `timing.py:129-131`, five repeats `:63`, limits stated `:39-44`, slow-spell tests `test_timing_fixture.py:291-300` |
| M2 size gap | Resolved | `test_k5_perf.py:30, 105`; stand-ins at the sweep's sizes `test_migration_numbers.py:843, 851` |
| M3 constants and mutants | Resolved | literals `test_timing_fixture.py:68, 113-126, 250`; n log n model `:56`; except m5 and m6 |
| m4 big time checked | Resolved | `timing.py:99` |
| m5 minimum gap | Resolved | `timing.py:73` |
| m6 validation first | Resolved | `timing.py:147-149` |
| m7 too-fast refusal wording | Resolved | `timing.py:49-51`; `CHANGELOG.md:261` |
| m8 sweep names the case | Resolved | `timing.py:155-167`; see m2 |
| m9 collector off stated | Resolved | `timing.py:22-23`; `CHANGELOG.md:260` |
| m10 weak assertions | Partly | leftovers in m10 above |
| m11 re-run policy | Partly | claim withdrawn at `CHANGELOG.md:278`; stale comment at `test_k5_perf.py:58` |
| m12 CHANGELOG | Partly | m7: mutant count, "under a minute", 216 |

## Not checked

- Nothing was run.
- Anything outside the snapshot:
  - `tools/mutation_runner.py` (what "fails first" and `only_test` do) and `test_every_mutant_still_applies_to_the_source`.
  - CI workflow and `pyproject` (a `--reruns` option or a flaky plugin could be configured there; whether `perf` is deselected in the unit step).
  - `hadavin_sdk.guard.redact.PATTERNS` (the 216).
  - Whether `redact_untrusted`, `lex` or `refused_statements` use threads, child processes, waiting or memoisation on the text.
  - Other users of the helper elsewhere in the repository, for example the perf-marked test in `tests/test_k5_layers.py` named at `CHANGELOG.md:23`.
- `tests/test_migration_numbers.py` outside lines 1-60 and 770-919, except by search for timing, clock, retry and suppression words.
- `CHANGELOG.md` lines 354-419 (older entries; the diff has one CHANGELOG hunk, at 258-281).
- `process_time` behaviour on Cygwin or MSYS (`sys.platform` is not `win32` there).

Files: `/home/user/build/snap/flaky-a8c269c/DIFF-vs-main.patch`, `/home/user/build/snap/flaky-a8c269c/DIFF-fix1.patch`, `/home/user/build/snap/flaky-a8c269c/tests/fixtures/timing.py`, `/home/user/build/snap/flaky-a8c269c/tests/test_timing_fixture.py`, `/home/user/build/snap/flaky-a8c269c/tests/test_k5_perf.py`, `/home/user/build/snap/flaky-a8c269c/tests/test_migration_numbers.py`, `/home/user/build/snap/flaky-a8c269c/tests/migration_numbers_mutants.py`, `/home/user/build/snap/flaky-a8c269c/CHANGELOG.md`, `/home/user/build/snap/flaky-a8c269c/result-r1-full.md`. Persona read: `/root/.claude/plugins/cache/egm/egm/0.1.1/agents/codebase_details.md`. No further standards were supplied.
