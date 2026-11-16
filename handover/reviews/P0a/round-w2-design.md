# A22 PR71 (core/P0a head 151d3e1) egm-design review, saved by the cloud session (reviewer read the snapshot only; ran nothing)
Verdict: 0 Blocker, 2 Major, 3 Minor/Nit. Reviewer's words, unverified until checked.
- MAJOR 1: report/ticket mismatch: ticket rung row BN-4 says one test under 50 lines; builder report says 61 lines and 4 mutants; the file at 151d3e1 has 175 lines and 19 mutants. Ask which head the report describes; accept the extra size only with a written reason.
- MAJOR 2: test unrun on real main: it fails with "no python file scanned" if demos/ or tools/ hold no .py on main, and may scan a nested .venv/node_modules. Needs `pytest tests/test_no_pglast_in_runtime.py` on the real head and CI results.
- MINOR: `_hit` raises KeyError on an include-group dict without `name` (cyclic group); skip dicts without name.
- NIT: string-built imports, `__import__`, `.dylib` not covered; state the best-effort limit in the docstring.
- NIT: lines over 100 characters (ruff E501 unknown); run ruff check and format --check.
Not checked by the reviewer: nothing was run; no pyproject, uv.lock, ci.yml; the 9657-test claim; no evidence file supplied.
Next: evidence runner on 151d3e1 (the test alone plus ruff) and a builder fix for MINOR/NIT items; Majors need the lead's answer on the head.

# Round 2 (egm-codebase-details, head 945bfd6; read-only, ran nothing; evidence file for 945bfd6 did not exist yet)
0 Blocker, 1 Major open, 4 Minor/Nit.
- MAJOR open: guard unrun on real main at this head (cloud evidence at 151d3e1 DID run the test on the PR tree: 21 passed, demos 28 .py, tools 3 .py; evidence for 945bfd6 is running); `_code` has no error handling for an unparsable .py (loud failure, not false pass).
- Item 2 (size 221 lines, 28 mutants vs ticket "under 50 lines"): lead/ticket must write the reason (many fail-open classes) or correct BN-4/BN-P0a-build.
- Round-1 minor (KeyError) and nits (.dylib, docstring) FIXED by reading; line length unverified.
- NEW minor: `os.walk` has no `onerror` (unreadable directory skipped silently; should raise); prune of `.venv`/`node_modules` at any depth may hide shipped code (prune only at tree top, or confirm packaging); no symlink test.
- NEW nits: single-file `pglast.py/.pyi`, `pglast.libs`, `.pyc/.pyx/.dll`, upper-case suffix not covered; name them in the docstring.
