# run.py r10 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw output: mutation-lane/evidence-r10-independent/ (00-TABLE.md). Recorded, not judged. Copies match evidence-r10/hashes.txt.

## Failures and deviations first
- D1 signals 0 to 0.2 s after launch of `--restore` (30 runs, root): 15 of 30 ended with an exit other than 0, 130, 143. 11 killed by default action; 9 of them (0 to 0.05 s) kept the marker and file stayed planted (documented start-up window). 2 (H5-22, H5-23) were TERM on the `--sha` path at 0.08 and 0.12 s: restore finished, marker gone, yet exit -15 (later than the documented window). All 30 follow-up `--restore --sha` exited 0, file restored.
- D2 KeyboardInterrupt: 4 runs (H5-2, H5-14, H5-25, H5-27, delay 0.01-0.02 s) exit 1 with KeyboardInterrupt text (12 traceback lines in H5-27, 9 in H5-3); marker kept, file planted. "Early handlers, exit 128+N" held in H5-9, H5-15, H5-21 only.
- D3 plain `--restore` with forged marker + matching backup: exit 0, swapped text written (root and nobody). `--sha` gives exit 3, nothing written (documented limit d).
- D4 forged marker mode 0777, 4755, 2755: file modes 777, 4755, 2755, exit 0 (root and nobody); special bits not masked. T98e2 wording "masked to 0777 at most" does not match. With `--sha`: exit 3.
- D5 "T98 fails 7 of 7 on r9" does not reproduce: alone (`ONLY=T98`) T98d/e/e2 fail only because T97 helpers are missing; with `ONLY="T96 T97 T98"` on r9, 23 of 46 fail (T96e 1, T97 18, T98 4: a, b, c, f); T98d/e/e2 pass on r9.
- D6 ruff on run.r9.py: 2 S603 (expected).
- D7 other agents' jobs shared the cores (load 2-4); 3 /tmp/safety-only.*.sh files are not the runner's.

## Passes
Full safety-tests.sh as root 832 s exit 0: root 0 of 442 failed, child uid 65534 0 of 87, none skipped. Over-long paths (4097 B, 120,000 B, 300-byte names; --root, --sha, --file, --repo; 13 cases) all exit 2, 0 traceback lines, file unchanged, root and nobody. Names with newline: exit 2. ruff check run.py: 0 S603, 0 noqa; format clean; bash -n ok. git status src tests: 0 lines. No leftover processes. Banned scan 0.

## Not run
Signals as nobody; marker mode 1755; mutation runs and N0-N10 controls; the pointer file item (not built); signal runs on an idle machine.
