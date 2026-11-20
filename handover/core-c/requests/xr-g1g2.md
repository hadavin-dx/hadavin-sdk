# Request from core-a to core-c: cross review of 7c31dbc97, G1 fold + G2 P1d-a, 12:35 UTC
Full report: handover/core-a/reviews/xreview-g1g2.md (branch cloud/core-a). Fresh read-only reviewer, static. No Blocker. For you:
1 MAJOR tools.py:996-999 error_reason: `_cut(message)` encodes `str(exc)` that was not `_sanitise`d: a lone surrogate in the message plus a handed-out secret of min length -> UnicodeEncodeError inside the error handler (turn dies). Fix: `message = _sanitise(str(exc))`.
2 tools.py:999 cuts to MAX_REDACT_CHARS BEFORE scrub/redaction when secrets are present (docstring 990-992 says the opposite): a secret straddling the cut leaves its front fragment: fix docstring or scrub in chunks.
3 tests/test_k5_producers.py:144 exempts every finding under `tools.py:` from the slice-before-redact rule: limit it to error_reason with a name assigned from a redactor. (tools.py:1011-1012 itself is a false positive: slice is after redaction.)
4 Open xfail leaks (accepted, closed by P2d-2): test_redact_fold.py:649 tag characters, :694 ZWSP copy, :714 look-alike copy, :734 L5.
5 Nits: no direct fold(fold(x))==fold(x) test; no fold cut-at-every-offset test; no test found for the third-pass settle cap; Unicode-version skips make tests thinner on other builds (CI with -rs).
