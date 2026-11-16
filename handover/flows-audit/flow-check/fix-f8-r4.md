# fix-f8-r4 (round 4, past the cap: Blockers/Majors plus cheap nits), 2026-11-16 (UTC; IST = UTC + 5:30)
Backup of the folder before any edit: scratchpad `bak/` (not in the repo). No commit. Only files in `flow-check/` changed (new: `take_check.sh`, `fix-f8-r4.md`).

## NOT DONE / NOT VERIFIED (first)
- n8n was never run. Every rule tagged `n8n rule UNVERIFIED` is still from memory of n8n; I did not look any of them up (no source in this repo, no n8n available here).
- n8n's environment-access setting cannot be seen by any file check; only stated loudly (README, closing block, `take_check.sh`).
- `run_all.sh` and `take_check.sh` have no self-test of their own; only their output was read.
- A `--accept-if` entry that matches no step is silently unused (not built).
- Skips (58) still never fail the run; the quoted numbers are from my runs, not independent ones. The mutation check of the 3 survivors is my own.
- Round-4 findings not done: nit 2 (error-output target only checked non-empty), nit 4 (narrow credential coverage, continueOnFail, multi-output nodes, fixed placeholder list, env scan scope).
- The old `/tmp/fc8*` folders on this machine are not mine and were not touched.

## Majors
1. Cross-folder duplicates: `cross_file` now takes one `seen` for the whole run; form triggers compared by path (key `FORM`), both types by webhookId; missing, empty or non-text path gives its own WARN (not "none"). Selftest: 8 multi-folder cases (same method+path, same webhookId with different paths, same form path, form vs webhook with the same path is NOT a clash, single folder no clash, missing path default/strict).
2. README: OPEN LEAD DECISIONS first; says no static tool can see n8n's env-access setting; `--block-env-access` named. New `take_check.sh` prints them before the full output. Closing block prints the same sentence.
3. Memory-sourced rules (auth values, auth without credentials block, credential kinds, error-output position, duplicate method+path/webhookId, responseMode default note) are WARN with tag `n8n rule UNVERIFIED` through one helper `unv()`; `--fail-unverified` makes them FAIL. Tag added to constants, docstring, messages, closing "Not proven", README, REPORT. Selftest FAIL cases run with `--fail-unverified`; 5 new `*_default_is_warn` cases (x all files they apply to) test the default.
4. Self-baseline removed from the take command and from `run_all.sh`; new `--accept-if FILE=NODE:OUT` records the two accepted IF gaps (WARN, counted, listed). `--baseline` documented loudly in README and docstring. 6 `accept_if_*` cases. `raw/pristine-no-baseline.txt` is now written by every `run_all.sh` run (exit 1, 2 FAIL).
5. Stale text: REPORT title and credential/FAIL lists corrected, README rewritten, HEADER narrative with fixed numbers removed (the closing block carries the numbers of the run).

## Also
- Lead decision: `run_all.sh` exit status and last line are real-v5 only; film-v5 in its own block, not gating, not summed; raw files `*-film.txt`. Last line prints "unknown" and exits 1 if the real-v5 run is missing (it printed `0 0` before). The default work folder is `mktemp -d` and removed by trap (no fixed `rm -rf /tmp/fc8`).
- Exit 3: `entry()` wraps `main`; unwritable `--diff-out` returns 3 (case `diff_out_unwritable_is_exit_3`). Python 3.10+ documented and checked at start (`sys.hexversion`, because ruff UP036 rejects a `version_info` test).
- Nit 1 (caller / active / test vs production URL) added to "Not proven"; nit 3 (`--expect-credential` in README take command).

## Mutants of evidence-r3 (own re-run, scratch copies of check_flows.py, full self-test each)
- line 608 `any(p in idv ...)` -> `not in`: killed (575 as expected, 2 not). New: `control_real_ids_pass_when_ids_are_required`.
- line 964 `if not where:` -> `if where:`: killed (2 not). New: `info_line_says_none_when_no_placeholder_and_no_env`, `info_line_lists_placeholders_when_there_are_some`.
- line 1149 `append` -> `extend` on "node CHANGED": killed (1 not). New: `diff_text_exact_line` (checks the exact line on screen and in the `--diff-out` file).

## Evidence
- `bash run_all.sh`: exit 0; self-test `577 as expected, 0 not as expected, 58 skipped` (round 3: 538 / 0 / 52). Last line: `OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s)`. `bash run_all.sh --strict`: exit 1 (placeholder ids), as designed.
- Real-v5: pristine 0 FAIL 18 WARN, 8 known; patched 0 FAIL 20 WARN, 10 known; strict runs exit 1, 4 FAIL each; no-baseline exit 1, 2 FAIL.
- Round-3 checker against the round-4 self-test (shim ignoring `--fail-unverified`): `raw/selftest-oldchecker-r3.txt`: 546 as expected, 31 not (all new round-4 cases). Without the shim 427 fail only because the old checker rejects the new option, which says nothing.
- ruff check: All checks passed. ruff format --check: 23 files already formatted. bandit -ll -r: no Medium or High issue, 0 skipped by nosec. No noqa/nosec/type-ignore/pragma (grep empty).
