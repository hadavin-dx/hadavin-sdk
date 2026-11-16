Status: resolved (no person available; recommended option taken for every item)

# Goldfish Annotated Review Report

**Target:** `tests/fixtures/timing.py`, `tests/test_timing_fixture.py`, `tests/test_runmap_partial_escape.py`, `CHANGELOG.md` at head 2f94c2b2 (snapshot `/home/user/build/snap/timing-2f94c2b2/`), full files. Non-security path, round 1 of 2.
**Inputs:** `r1-design-full.md`, `r1-codebase-full.md`. Evidence runner ad18b1b5 not finished; the fix batch waits for it so it can fix its findings in the same push.

Counts: PROPOSE FIX 12, CONTEST 0, ESCALATE 0, DECLINE 2.

## Findings

### 1 [design Major 1 = codebase M1] The wait guard raises `Untimeable` on one preempted tiny batch
* Checked: `timing.py:172-181`. `batch(n)` raises when `waited >= WAIT_MIN_S and waited > WAIT_FACTOR * took` for every batch, including n=1,2,4 sizing batches whose processor time is tens of microseconds. A 5-10 ms scheduler pause gives a ratio far above 50. True; this reintroduces the flake class the change removes.
* ***PROPOSE FIX***: judge waiting only on a batch that reached `MIN_BATCH_S` (a pause then needs to be longer than about 50 times the batch to trip it), or on the aggregate of the repeats. Sleep and child-process detection stay (their first big batch is caught). Tests: a made-up wall clock with one 8 ms pause inside a 60 microsecond batch must NOT raise; a sleeping function must still raise. Fail-before on 2f94c2b2 for the first. Add a mutant.

### 2 [design Major 2] Real-clock tests are not marked `perf`
* Checked: `test_timing_fixture.py:1-2` says they are marked `perf`; grep finds no `pytest.mark.perf` or `pytestmark`. True.
* ***PROPOSE FIX***: mark the three real-clock tests `perf` (sleep, child process, ordinary computing) and run the child-process test in a `spawn`/subprocess form (no fork from a threaded pytest, no fork DeprecationWarning under `-W error`). Alternatively make them deterministic with an injected wall clock; do both where cheap.

### 3 [design Major 3, conditional] Guard tests cannot pass on win32
* Checked: `pick_clock("win32")` gives `perf_counter`, wall equals CPU, the guard never fires.
* ***PROPOSE FIX***: `skipif(sys.platform == "win32")` on the two guard tests with the reason; the CHANGELOG says plainly that Windows is not covered and the guard is off there (also codebase m1: say "off Windows", and key the guard on the real processor-time clock, not on `clock is None`).

### 4 [design 4] Sentinel runmap test has no control
* ***PROPOSE FIX***: add a control `growth(lambda run: _old("x"+run+"y", 0), "%C3", 1_500, 12_000)` asserting `flagged`; keep only the units with documented quadratic history for the flagged-control claim and say the others are linear guards only.

### 5 [design 6 / codebase m6] Stale or unmeasured CHANGELOG claims; 335-line block
* ***PROPOSE FIX***: line 28 reworded (wall-time ratio claim is false, now processor time); pass counts "60 of 60", "14 of 14", "19 of 30" re-measured at the final head by the evidence runner or marked "not re-measured at this head"; move the test-only entry to a dev-only section.

### 6 [codebase m2] The search heading overstates coverage
* Checked in the older checkout: `time.monotonic` ceilings remain at `tests/test_migrate_regex_linear.py:25-27`, `test_k5_round5.py:252-255`, `test_s4_llm_guard.py:218-220`, `demo_askdata/test_validate_fuzz.py:90-104`. True (outside the snapshot, I read them in the checkout).
* ***PROPOSE FIX***: move those four to `timing.CLOCK` (same class, same fix at the shared choke point), or state per file why wall time is intended; reword the heading to the real search. Also route the two direct `process_time` calls (`test_k5_round10.py:128-135`, `warden_port/test_redaction_bank.py:357-362`) through `timing.CLOCK`. Intended wall-clock tests (hang abandoned at deadline, pg_sleep watchdog, subprocess) stay and are listed.

### 7 [codebase m4] CPU ceilings cannot catch a blocking regression
* ***PROPOSE FIX***: one sentence in the CHANGELOG and the module docstring: these ceilings catch computing cost only; a sleep or I/O regression needs a wall-time test (name where they exist).

### 8 [design 5] Hostile-input ceilings are coarse (n^1.3 would pass)
* ***PROPOSE FIX***: no new tests; add the sentence that only the `perf` ratio test catches mild super-linear growth, and keep the tight `< 2.0 s` case in the default suite.

### 9 [codebase m3] Stale "busy runner" comment at `test_runmap_partial_escape.py:116-118`
* ***PROPOSE FIX***: delete the comment.

### 10 [codebase m5] Direct `Growth` construction can divide by zero or print NaN
* ***PROPOSE FIX***: `ratio` goes through `_check_time` (cheap); test.

### 11 [design 7] Admitted caveats (threads counted by process time, memoised paths, GC off)
* ***DECLINE***: already stated in the docstring and CHANGELOG; no change.

### 12 [builder, open] m11 a resize re-times every text in the sweep
* ***PROPOSE FIX***: re-time only the texts whose batch size changed (cost only; no wrong result). If it grows the diff past one push, record it in the ledger as a cost item with the reason.

### 13 [codebase m6b] The measurement script behind "19 of 30" is not in the repo
* ***DECLINE*** as a separate item: covered by item 5 (numbers re-measured by the evidence runner, raw output kept in `handover/evidence/timing/`).

## Handoff
Accepted fixes 12. Contested 0. Escalated 0. Declined 2. Unaddressed 0.
Next: one fix batch (round 1 of 2) after the evidence report lands, then delta evidence and reviewers; after round 2 only Blockers and Majors get another review.
