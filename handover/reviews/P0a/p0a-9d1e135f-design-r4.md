# p0a-9d1e135f-design-r4: PR 71 fix 2, head 9d1e135f, round 4 (confirming), persona design

Source: hand-back of the design reviewer (agent ab5d55cf111265d2b), saved by the lead session (condensed). SECURITY path. Hand trace only; nothing was run. Snapshot `/home/user/build/snap/p0a-fix2-9d1e135f`. **0 Blocker, 0 Major.** Round-3 finding M1 and the round-3 design minors are fixed or documented as limits.

## Minor
- m1 `.ipynb`, `.pyz`, `.pth` and suffixed scripts (shebang in `run.txt`) are not parsed; a notebook under demos with `import pglast` passes. Add to the limits or flag `.ipynb`.
- m2 PEP 723 check reads only `dependencies` and `[tool.uv.sources]`; other `[tool.uv]` keys in a script block are not read and not listed as a limit.
- m3 `BINARY` "ANY compiled file" is overstated: `.a`, `.exe`, `.node`, `.wasm`, `.pyc` under another name are not flagged; only `.pyc` is listed. Say "the listed suffixes".
## Nits
`pglast-stubs`, `types-pglast`, `.egg-link`, Windows junctions not flagged; the `f"pglast{x}"` over-flag claim has no row; the row "src absent while demos and tools are clean" is confusingly named; `_script` opens every suffix-less file (a FIFO would hang it). Trade-off noted: renaming tools/ or demos/ leaves that tree unscanned without failure (TREES hardcoded).
## Not checked
Nothing run; real repo files (pyproject, uv.lock, tree contents) not read, so false positives on the clean tree unknown; packaging outside the three trees; Windows, macOS, Python 3.13+.
