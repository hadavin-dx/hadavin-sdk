# M3 build notes (E19: wall-clock deadline for the text fold; M4 docstrings), branch wip-m3

Base: cloud/core-c HEAD 8546d2ee0. Code commit: "code G: M3 wall-clock deadline ..." (src, tests only).

## What changed
- `defaults.INJECTION_WALL_FACTOR = 2.0` (new, named setting; derived from the lead's "about 2x the CPU budget"). Validated like `INJECTION_BUDGET_S`: a finite number of at least 1 (a factor under 1 would flag a check that is on time), else `ValueError`, and the run is flagged `guard_unavailable`. Checked in `injection._deadline` and in `textnorm._deadline_of`.
- `textnorm._deadline_of(budget_s)` returns a pair (thread_time + budget, monotonic + factor x budget), both read in the calling thread; `_tick` raises `DeadlinePassed` when either clock is at its deadline. `budget_s=None` reads no clock (unchanged).
- `injection._deadline()` returns the same pair; `injection._left()` returns min(CPU left, wall left / factor), so the relative `budget_s` handed to `scan_views_no_value` carries both (the callee recomputes both deadlines in its own thread). Deadline type annotations changed to `_Deadline = tuple[float, float]`.
- M4: module docstring PRODUCTION CALLERS paragraph (the 14 unwired names, owner item O-1); three stale sentences corrected (the "consumers arrive with the redaction package" claim in `register_value`, "the redaction package and the hold check of P1b" in UNNAMED CHARACTERS, "the redactor" as `scan_holds` consumer, and the "no module scans yet" parenthesis now points at the new paragraph). No code moved or deleted; the public names (37) are unchanged.

## Tests and mutants
- `tests/test_textnorm_deadline.py`: 17 tests (13 at HEAD, 4 new): wall wait with a frozen CPU clock raises at 2x (and not at 1.75x), no budget reads no clock, injection hands both deadlines to the fold, the factor setting is checked. The fake clocks gained a `monotonic` counted apart from the pinned thread_time readings; D-6 passes a pair as deadline (API change). No test loosened or deleted.
- Mutants 256 -> 263 (7 new, 251 behaviour / 12 wording by `split_counts`); 4 existing deadline mutants re-pointed at the edited lines (same mutation, killer, expect).
- Manifest and CHANGELOG hash: `ef69daa949b2c064de8d8758aecc50df62c07c1aea5d63ff4a76528dd6cd7185` (sha256 of guard/textnorm.py after the last edit).

## Runs (box load high, one heavy run at a time, -n 2)
- Gate `pytest -n 2 -m "not live and not perf"` over tests/test_textnorm*.py, the INJ list and the CANARY list of the G10 ticket: 1253 passed (300 s), with the manifest and CHANGELOG pin in place.
- Mutant runner, `deadline:` group plus the injection ones and the three new `injection:` names: 22 of 23 good on the first run; the one BAD (`deadline: the wall allowance is the CPU budget`, WRONG_REASON) was a test layout fault (the assert sat inside the except block, so the runner saw the chained DeadlinePassed); fixed in the test, then the 4 `deadline: the wall` mutants: 4 of 4 good. The other 19 were killed with the right reason in the first run.
- ruff format --check src tests tools clean; ruff check clean on src and the edited test files; bandit -ll: no medium or high finding.
- NOT RUN: perf rows (`-m perf`), the full 263-mutant list, the rest of the suite outside the gate.
- Code commit and the red between commits: tests/test_textnorm_meta.py test i and the manifest test read CHANGELOG.md, so they are red on the code commit alone and green with the notes commit.
