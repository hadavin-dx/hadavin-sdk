# PR89 round 11, codebase-details lens, head 025ec61570c98b201aa10de4713072960c6c221a
Verdict: 0 Blocker, 1 Major, 7 Minor, 3 Nit. Reviewer ran nothing (no shell): sha256 values not recomputed, no tests, mutants or timings run; no independent evidence existed yet. Saved by the cloud session from the reviewer's inline report (condensed; the finding texts are the reviewer's).

## Major
1. A run pattern is built for LONG secrets too. tools/mutation_runner.py:496-525 (_run_pattern) and :589 (_stripped_spans). Docstring (:498) says "shorter than FRAGMENT_MIN"; code (:503-505) has no length check. Module docstring 3(c) (:74-78), CHANGELOG line 8 and NOTES line 5 ("built only when a short secret needs it") say the same false thing. No leak (run match is a subset of the stripped match), but every long base is matched twice, both feed the same `spans`, so MAX_MATCHES (:597) is reached at about 50,000 real matches, and the run view (two arrays, 8 bytes per character) is built for every masked line with a quote or non-ASCII base. No test pins it. Fix: return None from _run_pattern when len(kept) >= FRAGMENT_MIN plus a test (long quote-containing base, _run_pattern is None), or change the docs.

## Minor
2. CHANGELOG line 8 claims with no test or raw evidence: "1,000,000 characters took 0.2 to 0.4 s in three cases", "100,000 matches and a line over the ... limit finish in under 10 s" (the dots test asserts 30 s), "1.1 s for 1,000 dots". Repeats r10-04 6c, 6d.
3. Speed test gaps (:2265-2287): "near misses" text starts with `a`, so it is not a near miss; no "..." in the partial or near-miss texts, so edge patterns are timed only by the 1,000-dots case; no short-secret timing (run-view build and run pattern untimed); text is 200,000-400,000 characters, not megabytes; `assert len(out) >= 1` is trivial; other limits still 30 s (:725, :1473).
4. Wording: CHANGELOG line 8 is one bullet of thousands of words with about ten nested parentheses; module docstring 3(a) uses "layer 0/1/2" undefined; "FRAGMENT_MIN" without the value 6 in 3(b)-(d).
5. Mutant gaps (from reading, unverified): edge-match guards `found.end() - found.start() >= FRAGMENT_MIN` (:614, :617), position mapping in _view_with_places (:566-581), `len(kept) <= FRAGMENT_MIN` return of _edge_patterns (:534) have no dedicated mutant; 438 replaces the whole _run_pattern guard so the long-base case is not distinguished. test_a_head_or_tail_cut_inside_an_escape_is_hidden (:2126-2152) has no mutant.
6. Memory claim in NOTES line 5 too narrow: a line also holds hit, where, flat and reverse, view, and the out list; no test or CHANGELOG backs a memory figure.
7. lru_caches (:448, :484, :496, :528) key on secret text, so secret values stay in process memory after run_mutants ends; add cache_clear in cleanup.
8. r10-04 item 4 NOT FIXED: shared expect texts. 381, 382, 421, 423 share killer test_a_short_value_printed_in_two_layers_leaves_nothing_readable and one expect; 425, 426 share one; new 438, 440, 441 share one killer and one expect. Tests print only the first leak (:1871, :2082).
(r10-04 6c and 6d not fixed, see 2. Fail-before: only 4 of the 6 failing tests are real behaviour fails; the cut-inside-an-escape and pattern-count tests fail only because of the shim; honest in NOTES, weaker than "6 of 9".)

## Nit
9. _readable regex (:1785) still strips any b before a quote; DEEP_VALUE (:1986) holds "db"; a leak of just "b" is theoretically missed.
10. _the_conftest_module reads __file__ of every sys.modules entry; getattr default absorbs only AttributeError.
11. _RUN = "\x00" (:428) is also a real NUL in a line; harmless over-masking.

## Previous findings: fixed
r10-03 (vacuous pin) FIXED (tests :2062-2083, :2214-2232; fail on old code 11,116 leaks). r10-02 item 2 (head/tail depth 3+) FIXED (_edge_patterns :528-551; mutants 446-450). r10-02 item 5 (lock-file name) FIXED. r10-04 items 2, 3 (in effect), 7, 8, 9, 11 FIXED; items 5, 10 PARTLY. Manifest pins equal CHANGELOG text (text comparison only); EXPECTED_MUTANTS 192 matches the reviewer's count (130 kmutant + 62).
