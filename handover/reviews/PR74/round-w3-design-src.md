# PR74 (A15, core/P5a) fresh result review, design slice, head 21ca680 (ORDER 238)
Reviewer egm-design, read-only, nothing run. Coverage: codes.py 1-257/257; guard/diagnostic.py 1-504/504; guard/textnorm.py 1-627/627; defaults.py and app.py diff hunks only; _confusables.py and _scripts.py 30 lines each of ~540/~940 (generated, digests unchecked); ticket P5a.md 1-106 and 243-364 of 364. Tests not read.
M1 Major, guard/textnorm.py:497-517 vs fix1 note "Scan time budget (G7)": note says scan_keyset refuses with TextTooLong after defaults.REDACT_BUDGET_S; textnorm.py never reads it (grep: only defaults.py:49) and has no time import; docstring still says "no clock". Hostile text at the 262,144-char cap: 2 readings x up to 4 tag texts x up to 3 passes, per-character Python loops, no wall-clock stop. Runtime of scan_keyset UNVERIFIED. Fix the code or strike the note and state the bound.
M2 Minor, diagnostic.py:126-136: _GUARD_FAILURES dict updated without a lock; note says lock-guarded.
M3 Minor, diagnostic.py:321-335, 55-57, 89-99: closed-list guarantee for token facts holds only if callers pass constant sets (SafeToken.of(x, frozenset({x}))). Callers not wired in P5a; add pointer to P5b3 call-site check.
M4 Minor, diagnostic.py:165-184: tp.__module__/__qualname__ read twice (TOCTOU with hostile metaclass); render re-check catches it, no leak. Read once.
M5 Minor, app.py:85-87: require_pinned_unidata() runs after make("secrets") so "before anything else" is false; it also changes existing pilot/prod start behaviour (UnidataMismatch on Python 3.12 Unicode 15.0.0), against "no existing source behaviour changes". Confirm intent.
M6 Minor (single-dependency): db_error/phase only for psycopg; documented v1.1 row; lock-in guard holds.
M7 Nit: str(value) for huge int on a hand-built Diagnostic raises ValueError -> fixed fallback (safe).
M8 Nit: _links runs twice per diagnosis.
Passed (by reading): masking by construction (no str/repr/args/__notes__/__cause__), render fullmatch, family order, BN-3/4/5/7, least privilege (pure functions), closed-list counts.
Not checked: tests fail on old code; test_no_hardcoded_values vs FACT_BOUNDS/TICK_STEPS literals; TICK_STEPS vs runtime.tick.STEPS; discovery test of OWN_CODES; generated tables; scan_keyset runtime.
