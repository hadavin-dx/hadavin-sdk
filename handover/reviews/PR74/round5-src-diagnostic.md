# PR74 / A15 round 5, slice A: diagnostic source (head a63aaf1)
Reviewer a9b998b438266e6ef, read only, nothing run. VERDICT: 0 Blocker, 0 Major. Redaction path judged clean by reading: foreign text cannot reach a diagnostic (class names regex-checked, locators from package path + int, facts exact-type and bounded, render re-validates ASCII); single traceback walk correct; step cap (DIAG_TB_STEPS 2000, innermost 32 frames) holds; group handling holds; RLock claim true as stated; app.py order as CHANGELOG states (load_config :80, require_pinned_unidata :85 live only, load_registry :86, secrets :88).

Minors
1. diagnostic.py:1-13 docstring "Pure functions" loose (global counter, sys.modules read :396).
2. :71-77,104 SafeToken "made only by" of/sqlstate, but SafeToken(v, SafeToken._MINT) works: convention, not a seal.
3. defaults.py:149-151 comment: over-cap traceback gives foreign_exception only on the internal_bug path; own-class/builtin-mapped keep their code (370-372); only locator becomes "-".
4. :321 error_count() above FACT_BOUNDS (10**6) prints 5 types with no "+N more" (silent truncation); :299-301 errors() builds all entries before slicing to 5.
5. :264-277 `_locate`: own frame with tb_lineno None (3.11+) or filename outside _PKG_DIR returns ("-","-","-") instead of trying the next outer own frame.
6. :195, codes.py:223 FOREIGN_PACKAGES_OK includes all sys.stdlib_module_names, likely `__main__`: an app exception in the entry script prints as `__main__.Name`.
7. :387,203-204 `_error_types` / `tp.__mro__` not locally guarded; hostile object collapses to fixed fallback (fail-safe).
8. codes.py:251-254 UnidataMismatch maps to scan_failed via MRO (odd, consistent).
Nits: :133-141 RLock removes deadlock, not lost updates (comment accurate); :519 backslashreplace encode is dead code.

COVERAGE: diagnostic.py and codes.py in full; DELTA.patch; app.py 55-135; defaults.py 140-154; CHANGELOG only the DELTA hunk (A15 paragraphs at lines 7-9); greps for OWN_CODES classes and TextnormError subclasses. Test files only as DELTA hunks; rest of textnorm.py not read; test/mutant claim numbers (21 codes, 26 validation types, 9 DIAG_*) not verified.
