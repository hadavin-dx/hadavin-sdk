# fix-lint: ruff cleanup of flows-audit tools, claims-count.py, patch-apply (2026-11-16)

## Failures and deviations first
- The job said about 53 errors; the real count at start was 134 (59 UP031 printf-format, 30 SIM115, 12 I001, and others). All fixed.
- `bandit -ll` exit code is 1 when run on `tools/` as a whole: 48 medium B608 findings, all inside `tools/scratch/**/build_mainframe.py` (copies of demo files, not in scope, not touched). With `--exclude handover/flows-audit/tools/scratch` the exit code is 0.
- S603 (subprocess with non-literal arguments) cannot be satisfied by any argument list that has a variable in it (tested with ruff 0.16.9; only fully literal lists pass). So no code calls subprocess any more: `dump_nodes.py` got a `main(argv)` function and `assemble_lane.py`, `make_out.py`, `test_dump_nodes.py` call it in-process (same code, same output, `contextlib.chdir` to the demo folder where the old call used `cwd=`). `checker-negative-tests.py` loads `check_flows.py` fresh for every case with importlib and calls its `main`.
- One real behaviour change, found by that move: with a flow node that has no `name`, `check_flows.py` printed its FAIL lines and then crashed with `KeyError: 'name'` (traceback, exit 1). In-process the crash would have aborted the whole negative test. Fixed in `check_flows.py` (`get()` and `node_diff()` now skip or tolerate nodes with no name; the FAIL line for the missing name is unchanged). Exit code is still 1. Only `patch-apply/negative-output/no_name.out` differs (traceback replaced by the normal remaining output).
- `checker-negative-tests.py` work folder is now `<tempdir>/pa13b` (was literal `/tmp/pa13b`, S108). Same path when TMPDIR is unset; `run-round2.sh` (not edited) still writes `/tmp/pa13b`.
- `check_flows.py` and `checker-negative-tests.py` made executable (EXE001, shebang present).
- Not done: flow-check/ and fill_flows/ untouched as instructed. Other files under flows-audit changed during this work (flow-check/raw/*); not mine.

## Fixes by rule
UP031/UP032 f-strings; SIM115 `with open` (or helper functions); I001 import order; S101 assert replaced by explicit raise; PLW1510 gone with subprocess; BLE001/S112 specific exceptions (`OSError, ValueError, ...`, `OSError, UnicodeDecodeError`); RUF015/RUF059/B007/PERF102/FURB167 per ruff; B023 `has()` moved out of the loop and takes `outs`; B905 `zip(..., strict=True)` (lengths already checked equal on that branch). No noqa, nosec, type: ignore or ignores added (grep confirmed).

## Before/after outputs (raw files in scratchpad base/ and after/, compared with cmp)
Identical (cmp): check_patches.sh (PASS 4 patches, rc 0), check_runsheet_paste (RESULT: PASS), claims-count (ids 327 unique 327), count_findings (Blocker 5, Major 7, Nit 33), check_secrets (PASS 0 hits in 1675 files, rc 0), check_counts (PASS 52 files / 655 nodes), check_names (PASS 655 rows), check_refs (FAIL unresolved CUT-LIST.md:17, rc 1: same failure before and after, not caused by this work and not fixed here), test_dump_nodes (PASS 8/8), checker-negative-tests (26 of 26 as expected). `tools/out/` unchanged after the run. Negative-output files identical except no_name.out (above).

## Final gates
`ruff format --check`: exit 0 (69 files already formatted). `ruff check`: exit 0. `bandit -ll`: exit 1 on all of tools/ (scratch only, see above); exit 0 excluding tools/scratch.
Backup of originals: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-lint/
