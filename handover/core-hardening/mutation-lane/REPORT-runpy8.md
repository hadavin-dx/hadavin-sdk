# REPORT run.py r7 / safety-tests.sh r7 (builder)

## Failures, doubts, what was not done (first)
- No git, no bible, no EGM skills or agents were available here: no R-numbers cited; the lead runs EGM review and evidence.
- T82c (reversed patch) and the three "genuine restore afterwards" follow-ups and T76d are guards: they PASS on r6 code too (r6 already refused / already restored). The other 31 of 36 new checks fail on r6 (evidence-r7/T76-86-on-r6code.txt). T79 fails on r6 only by a signature difference (weaker proof).
- Not fixed on purpose: the two S603 ruff items stay (run.py lines ~569, ~1380); Q32 behaviour unchanged (text only); T66e/T67e observation not a fix. Chmod: only the target file's mode is restored; other files' modes are not compared (documented in the docstring).
- `--no-control` exits 5 (my choice; the lead may prefer refusing).
- Not run: nothing was run against real code, only the toy repo. The `-rfp` / `passed_total` change came late; it is covered by T25, T48, T86 in the final full run, but has no separate fails-on-r6 proof beyond T86.
- My own slips: a first full run was invalid because I edited files while it ran (kept as evidence-r7/prelim-full-run.txt, do not use). Two test-harness bugs fixed: T47a (the in-process loop did not reset the new `SIG.exiting` flag), grep of 'COMPLETE' matching inside 'INCOMPLETE'.

## Result
- Final full run on the final r7, once, nothing edited meanwhile: `FAILED CHECKS: 0 (of 353 checks run; skipped: none)` (evidence-r7/full-run.txt).
- New checks T76-T86 alone: r7 `FAILED CHECKS: 0 (of 36)`; r6 code `FAILED CHECKS: 31 (of 36)`.
- ruff format --check: already formatted; ruff check: only the 2 S603. py_compile and bash -n ok. Banned-brand scan: 0 hits.
- sha256 in evidence-r7/hashes.txt (run.py 01a741d2..., safety-tests.sh 5a06a0f5...). r6 backups unchanged under raw/.codecopies/.

## Findings fixed (test in safety-tests.sh)
M1 `--restore` exit 3 after a valid marker, 2 only forged (T53, T76a-d); M2 baseline default, `--no-control` exit 5 (T34, T66f, T77a-f); nit stale comment/T64b; signal-guarded `--restore` and exit unwind (T78a-b, T47a); sweep_group start-time window (T79); `--out-json` inside root / missing parent / hard links (T80a-e); tarfile/OSError, surrogates, bad list, internal error (T81a-f); patch `--batch --forward --no-backup-if-mismatch`, stdin /dev/null (T82a-c); `--sha` prefix check (T83); root rename/decoy identity (T84a-c); chmod set back (T85); new bug found: doubled `-q` hid pytest's summary, fixed by dedupe and `-rfp` + `passed_total` (T86, T48, T25).

## Files
run.py, safety-tests.sh, REPORT-runpy8.md, checkpoint-runpy8.md, evidence-r7/{full-run.txt, prelim-full-run.txt (invalid), T76-86-on-r7.txt, T76-86-on-r6code.txt, t76-86-derived.sh, hashes.txt}. Head SHA: none (no git). Scratch removed; a pre-existing scratchpad/venv belongs to another agent and was left. Token use: not measurable from here.
