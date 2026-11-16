# p0afix-f0de7b75-codebase-r2: PR 71 pglast guard, fix head f0de7b75, round 2, persona codebase details

Source: hand-back of the codebase reviewer (agent a750408484df89b34), saved by the lead session (condensed). Read-only, snapshot `/home/user/build/snap/p0afix-f0de7b75`, nothing run. Verdict: 0 Blocker, 0 Major, 4 Minor, 3 Nit. Both round-1 Majors fixed (hand-traced tables for `_norm`/`_vendored`/`BINARY`; symlink skip; utf-8-sig; `_flat` cycles; markers in `_is`). Counts 46 planted + 4 other = 50 tests recounted true; "was 35" unverifiable (12 new cases would imply 34); failbefore 10 failed 40 passed means the tmp file ran all 50 tests.

## Minor
- m1 PR-NOTE line 9 under-describes `_lock` (also requires-dist, requires-dev except test; skips pglast's own entry).
- m2 any compiled file (.so/.dll/.dylib/.pyd) under src, demos, tools fails with message "vendored", pglast or not; docstring does not say so.
- m3 not-caught lists omit: archives (.whl, .egg, .zip), odd suffix `.so.1a`, f-string pieces `f"pglast.{x}"`, other build tools' tables (hatch, poetry, pdm), top-level `src/.venv` / `src/node_modules` skipped on purpose (a real bypass on a licence path).
- m4 group dict comprehension lets the later of two colliding normalised names overwrite the earlier (theoretical).

## Nit
- "vendored dir" message omits the folder name; string regex vs import check normalise differently (docstring says exactly a module name); unreadable or broken-symlink .py raises instead of being reported (fails loud).

## Not checked
Nothing run, including the "90 passed" claim; real repo tree, pyproject.toml, uv.lock not read; Windows junctions, case-insensitive filesystems, symlink skip path on Windows not tested.
