# PR89 round 14, slice tests/test_mutation_runner_keywords.py lines 1-1,200 (egm-codebase-details, fresh), head e957592d8006
Coverage: 1,200 / 1,200 lines; runner 225-675, 938-1010, 1020-1050, 1105-1184; rest of test file grepped only. No code run. Verdict: no Blocker, 2 Major, 8 Nit. Masking tests in the slice are tied to the secret (absence plus [REDACTED] or exact output); positive controls at 421-452 and 530-546. Each runner masking point (1000, 1004, 950, 981/984, 990, 1164, _fragment_spans, EDGE_MIN) has a test; mutant for 1004 expects "postgresql" which matches the unmasked line.
M1 (Major, 560-561): `"Tk8%2FVq2"` and `"Tk8/Vq2"` written whole; build from parts like line 556.
M2 (Major, 625-630): `long_value = "north-river-stone-bridge-glacier-delta"` whole fake secret; build from parts.
N3: failure messages print the secret (461, 476, 506, 509, 546, 562, 593-605, 629, 641-643, 418, 452, 406): print counts/positions.
N4 (646-648): control `'abc...def'` depends on the digest not starting with ab/bc or ending with ef; use non-hex letters.
N5 (199-213): hostile plugin names are nonexistent files, so the loop would still pass without `_plugin_module` at line 1030; assert "conftest must be" in the message or create the files.
N6 (549-566, 455-479): absence-only asserts pass if _masked returns ""; add exact expected output.
N7 (530-546): control passes whether or not pytest shortens the value; assert "..." in seen["flip"] for the 297-character value; `_long_value` says 300 but is 27 x 11 = 297.
N8 (655): differential test has no guard against all-empty comparisons; add assert any(non-empty spans).
N9: `first_lines.clear()` (runner 1021) untested; call with a dict already holding a stale "flip" entry.
N10 (1003-1013): xfail test has no positive control in the same test.
Sound: _dsn_left_as_found guard (80-87), lock tests 853-913 (name format pinned; password independence is in 2257-2277), canary tests, forbid_skips pair, COLLECTION ERROR tests, timing backstops.
