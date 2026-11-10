# A22 PR71 (core/P0a head 151d3e1) egm-design review, saved by the cloud session (reviewer read the snapshot only; ran nothing)
Verdict: 0 Blocker, 2 Major, 3 Minor/Nit. Reviewer's words, unverified until checked.
- MAJOR 1: report/ticket mismatch: ticket rung row BN-4 says one test under 50 lines; builder report says 61 lines and 4 mutants; the file at 151d3e1 has 175 lines and 19 mutants. Ask which head the report describes; accept the extra size only with a written reason.
- MAJOR 2: test unrun on real main: it fails with "no python file scanned" if demos/ or tools/ hold no .py on main, and may scan a nested .venv/node_modules. Needs `pytest tests/test_no_pglast_in_runtime.py` on the real head and CI results.
- MINOR: `_hit` raises KeyError on an include-group dict without `name` (cyclic group); skip dicts without name.
- NIT: string-built imports, `__import__`, `.dylib` not covered; state the best-effort limit in the docstring.
- NIT: lines over 100 characters (ruff E501 unknown); run ruff check and format --check.
Not checked by the reviewer: nothing was run; no pyproject, uv.lock, ci.yml; the 9657-test claim; no evidence file supplied.
Next: evidence runner on 151d3e1 (the test alone plus ruff) and a builder fix for MINOR/NIT items; Majors need the lead's answer on the head.
