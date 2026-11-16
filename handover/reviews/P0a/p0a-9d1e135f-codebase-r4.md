# p0a-9d1e135f-codebase-r4: PR 71 fix 2, head 9d1e135f, round 4 (confirming), persona codebase details

Source: hand-back of the codebase reviewer (agent ad68d8bcb4704f190), saved by the lead session (condensed). SECURITY path. Hand trace only (no shell). **0 Blocker, 0 Major, 6 Minor.** Checked accurate: 99 MUTANTS rows plus 4 RAISES (58 old, 41 new); PEP 723 regex and de-commenting equal the reference; suffix handling, symlink and dangling-link raises, uv.lock rows, test-group exemption by normalised name, only src required to hold python.

## Minor
1. Docstring lines 51-53 say an unreadable or vanished file raises; only python-named and suffix-less files are opened, so a broken link or unreadable `x.txt`/`x.so`/`x.whl` is silently ignored and unpinned. Say "unreadable python or suffix-less file or folder".
2. Row "upper-case python suffix" writes `src/M.PY` next to `src/m.py`: same file on macOS or Windows. Use a different stem (`src/Up.PY`).
3. VENDORED alternatives survive deletion: `\.dist-info`, `whl`, `zip`, `tgz`, `txz`, `tbz2`, `7z`, `tar\.gz` are matched by the digit branch in every row; add digit-free rows (`pglast.dist-info`, `pglast.whl`, `pglast.zip`, `pglast.tgz`, `pglast.7z`). Guard behaviour correct (ARCHIVES also catches them); the claim of 29 rule-deletion mutants all killed is therefore NOT confirmed for these 8 alternatives.
4. "ANY symbolic link" claim: top-level `.venv` and `node_modules` links are skipped first; add "except those two names" to the symlinked-dir bullet (line 22).
5. PEP 723 `dependencies = "pglast"` (a string) iterates by character and passes; add `isinstance(list)` else report.
6. Duplicate row: "src absent while demos and tools are clean still fails" equals the "missing src" row.

## Not checked
Nothing run (99 passed, 29 mutants not verifiable here); real tree for false positives; uv leniency for the PEP 723 tag; Windows junctions, Python 3.14; packaging outside the three trees.
