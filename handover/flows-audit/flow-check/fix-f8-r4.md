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

---
# f8 round 4 fixer log (review f8-r3 findings: M1 reviewer line, M2 lock), 2026-11-16 (UTC; IST = UTC + 5:30)
(The text above is the older checker round-4 log with the same file name; this part is the take-check scripts fix. Old copies of the three scripts, README and this file: scratchpad `old4/`. No commit by me; note that an automatic "board" commit (b3a17ae7d, 12:35 UTC) already picked up my edits to the scripts.)

## NOT DONE / UNCERTAIN (first)
- A script cannot know who read the pin. A made-up human-looking name with a valid date still gives exit 0 (test `M1 (honesty check)` proves it on purpose). A real person whose name has a listed word (for example "Ai") is refused. Said in README.
- Date-too-old rule against a FIXED date: rejected (a hardcoded date goes stale). Used instead: reviewer date must not be older than the pin's own `# date (UTC)` line (cheap, no constant). A forged pin date defeats it; it only stops the `2000-01-01` and "read before the pin existed" cases.
- No "two words" rule (a one-word name like "Zed" passes); only the repeated-letter rule (Aaa) was added. `Pat O.L.L.M.` (letters separated by dots) is NOT caught: split on non-letters gives single letters; I dropped my own test for it rather than claim it.
- A2: after repinning, 12 `tcfail` cases are exit 4 from the planted fault alone, but some still add "THE WARN SET CHANGED" (no-table-file, old-table, zero-queries, recovery-accept-idle, new-warn-changes-the-pin): changing the table or flows changes the WARN lines, so that second cause cannot be removed without a pin per case. There is no separate negative test for the A2 repin; evidence is before/after output (old run_all: 14 take-check outputs contain the flows-sha mismatch line; new: 2, both are cases that do not assert exit 4: disabled-send expects exit 1, keyok-gone checks a text).
- Not changed (below Major, still open): tests control, b1a, q2c weaker than their names; SQL-count lines read with `head -n 1` (adversarial newline in a node name). Not checked: other filesystems (flock on a folder needs Linux/util-linux; NFS not tried); macOS not tried.

## M1 changes (take_check.sh)
- `reviewer_ok NAMELINE PINDATE`: name cut into words at every non-letter (tr), lower-cased; refused if ANY word is in `REVIEWER_STANDINS` (tbd todo name placeholder unknown nobody someone anonymous claude agent session bot assistant gpt model lead person xxx abc standin stand test reviewer runall dummy example sample fake sonnet opus haiku gemini llm ai code user admin, plus `testonly`), or a word is one letter repeated, or the date is older than the pin date line. The list is in the script (one variable), not a separate file: a names file would be one more unprotected file.
- Test-only path: `Testonly ...` as first word skips the list ONLY when `TAKE_CHECK_TEST=1` and `TAKE_CHECK_WARN_PIN` are both set; a run with an override is exit 5 at best, so no stand-in gives exit 0. run_all.sh now uses `Testonly Runall`, test_take_check.sh `Testonly Reviewer` (was `Runall Standin`, `Test Reviewer`, which gave exit 0 when copied in with the sha lines).
- New tests (test_take_check.sh): 12 bypass cases `M1: reviewer line ...` (TBD., Claude-Code, Agent., Unknown-, Sonnet Opus, Aaa, Runall Standin, Test Reviewer, Testonly Reviewer without the flag, Jane Gemini, date 2000-01-01, date before the pin date); the allowance case; 5 mirror cases that put the stand-in pin in the REAL pin place (copy of the scripts in a scratch folder, no override, no flag) and require exit 4; one honesty case (human-looking name = exit 0).

## M2 changes (run_all.sh)
- Lock is now `flock` on the raw FOLDER itself (opened read-only on `pwd -P` after `mkdir -p`): independent of TMPDIR, relative path, symbolic link, `..`; no lock file is left. `RUN_ALL_LOCKFILE` hook removed (also from the refused-hook list).
- New tests: free run acquires and leaves nothing in TMPDIR; held lock refuses with the same path, a different TMPDIR, a symbolic link, a relative path from another folder, a path with `//`, link and `..`; a different raw folder is not blocked; no lock file left in either TMPDIR.

## A2 changes (run_all.sh)
- `tcfail` repeats each case with a copy of the stand-in pin whose `# flows sha256` line holds the sha of the folder that was run, so exit 4 must come from the planted fault, and it adds a miss if the sha-mismatch line is still printed. `noquery` is now built from the patched folder; `warn-pin-file-missing`, `no-table-file`, `old-table` now run on the patched folder (they ran on the unpatched committed folder, so run saving off / missing key check gave exit 4 too). `recovery-accept-idle` now wants its own line ("THE RECOVERY FLOW IS NOT PRINTED AS ACCEPTED") instead of the generic "excused nothing".

## Proof the new tests fail on the old scripts
Old take_check.sh/run_all.sh (scratchpad `old4/`) in a mirror folder with the NEW test_take_check.sh: `test_take_check: 70 of 94 cases as expected, 24 not as expected` (rc 1): 12 M1 bypass lines, 5 mirror cases (got exit 0), 1 B4 free case (lock file left), 5 M2 lock cases, 1 no-lock-file case. New scripts: `94 of 94 cases as expected, 0 not as expected` (rc 0).

## Commands and exit codes (from handover/flows-audit, rc read straight after)
- patched copy built as in evidence-f8-final.md: apply F-002 rc=0, F-008 rc=0, gen rc=0
- `bash flow-check/test_take_check.sh <patched> <fresh>`: rc=0, 94 of 94
- `RUN_ALL_RAW=<fresh> bash flow-check/run_all.sh <fresh>`: rc=0 (selftest 682 as expected, 0 not, 62 skipped; take_check.sh exit=5 "missing lines: none"; its inner test_take_check 94 of 94); 1 min 30 s
- ruff check . rc=0; ruff format --check flow-check rc=0 (48 files); bandit -ll -r flow-check rc=0 (no issues); tools/check_secrets.py rc=0 (0 hits in 1790 files); tools/check_refs.py rc=0 (5146 references)
- raw/ and selftest-output restored with `git checkout --`; status clean for both.
