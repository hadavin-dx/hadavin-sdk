# M4 evidence report (facts only)

Commit tested: f3c39cf89ec989f032ea48a23cfd824b88da9c68 (worktree /home/user/work/m4-tree, detached). Python 3.13 venv.

## Failures first
- Without the gitleaks binary: 30 failed, 42 passed (3 hygiene files). With the verified binary: 0 failed in every run below.
- Not checked / not shown: the skip reasons of the 169 skipped tests in the full run. `-rs` printed no SKIPPED lines in the log (cause unknown, not investigated). No test named semgrep appeared in any log (grep "semgrep" in full log = 0 hits).
- No unexplained failure remained, so no 3x re-run was needed.

## Binary (step 1)
- URL: https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz (via the preconfigured proxy, TLS verification on, HTTP 200)
- Checksums file: .../v8.30.1/gitleaks_8.30.1_checksums.txt
- Published sha256 = computed sha256 = 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb (`sha256sum -c`: OK)
- `gitleaks version` output: 8.30.1
- Files: /home/user/work/priv/gitleaks-bin/ (archive, checksums), binary at /home/user/work/priv/gitleaks-bin/x/gitleaks

## Runs (pytest's own rc written to the log by the script; flags -q -rs -rf -p no:cacheprovider, TMPDIR=/home/user/work/priv/m4-tmp, --basetemp inside it, DPLD_REQUIRE_SCAN=1, PYTHONPATH=/home/user/work/priv/shuffle, AWS_*/ANTHROPIC_* unset)
| Run | GITLEAKS_BIN | Seed | Result | rc | Wall | Log |
|---|---|---|---|---|---|---|
| 3 files, quick | not set | 20261114 | 30 failed, 42 passed | 1 | 35 s | raw/m4-nobin.log |
| 3 files | set | 20261114 | 72 passed | 0 | 67 s | raw/m4-bin-s20261114.log |
| 3 files (reversed) | set | 0 | 72 passed | 0 | 66 s | raw/m4-bin-s0.log |
| FULL suite (tests/) | set | 20261114 | 3714 passed, 169 skipped, 0 failed | 0 | 924 s | raw/m4-full.log |

## The 30 failures without the binary
Sorted failed-test ids from m4-nobin.log are identical to raw/m2-rerun/ids-d1 (diff empty; 30 lines each). Names are in that file and in the FAILED lines of raw/m4-nobin.log (for example tests/test_hygiene.py::test_hygiene_scan_public, whose assertion starts "gitl..."; and test_gitleaks_reports_a_carriage_return_in_the_key_file_but_not_the_lf_copy). Same 30 tests pass once the verified binary is present: the missing program is the cause for these 30 in this container.

## Clean-tree check
- git status --porcelain in worktree: empty before (raw/m4-status-before.txt) and after (raw/m4-status-after.txt). `git add -A` was not needed and not run; nothing committed or pushed. Source clone /home/user/work/src status: empty.
- New files outside the tree: /home/user/work/priv/gitleaks-bin/, /home/user/work/priv/m4-tmp/ (basetemps and test temp dirs), /home/user/work/priv/m4-run.sh (my run script), logs under evidence/raw/m4-*, progress-M4.txt, and a git worktree record for /home/user/work/m4-tree in the src clone (.git/worktrees). Scratch /tmp/claude-0/n.txt, o.txt (my diff helpers). All attributable to me; no guesses.
- No semgrep installed or touched. No stray processes checked beyond the runs having finished with rc lines.
