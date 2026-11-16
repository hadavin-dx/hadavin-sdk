# PR 67 (P0t, head 7835078) round 2 code review (egm-codebase-details), saved by the lead 2026-11-06, condensed
Verdict: no Blocker in the code; one Major (evidence). p0t-001..007: 001,002,003,005,006,007 verified fixed at file:line; 004 (evidence) partly closed.
F1 Major evidence: "1 failed, 9684 passed" with failing test unnamed; fail-before is ImportError only; Postgres and POSIX-only tests skipped (CI must be green on Linux with Postgres).
F2 Minor: old-word check exact only; Dev, DEV, " dev", "dev\n" refused only by the generic Literal error and untested: add to INEXACT.
F3 Minor: class test bypassable: misses env: dev, ENV=dev, target: dev, deploy = "dev", if env == "dev", {"dev": ...}; SCANNED omits tools/, scripts/, root *.md: add generic position (==|!=|=|:)\s*quote dev quote outside the split places; add tools and root md.
F4 Minor: Literal, STAGES and four "demo" comparisons separate copies: assert get_args(...) == STAGES.
F5 Minor mutant gaps: app.py live=False, deferred.py/registry.py if True, removal of isinstance(value,str) guard, drop demo from redact.py common words.
F6 Nit: "Demo" no longer masked as a name (same trade-off as prod, dev). F7 Nit: duplicate tests (test_each_site_is_asked_separately; test_the_scan_reads_the_places_it_claims_to).
Clean checks: no stored or free-text environment label; _anchor_refusals only compares prod; no normalisation in the refusal path; CHANGELOG note accurate.
