# fix-f8-r10 (answers review-f8-r10.md), 2026-11-16, EGM skipped for the review step: the lead runs it (no EGM agent available from here)

## What failed or is not as the review said (first)
- The review-f8-r10 claim "ruff format --check exits 1" was NOT reproduced here: at the start `ruff format --check check_flows.py selftest.py` said "2 files already formatted" (exit 0). After my edits I ran `ruff format` on both and the check is exit 0 again.
- F-008 content check in the take (M5, "where it does not break the planted cases"): NOT added. `--patch-checks F008` would turn the planted run-saving cases (form-off, sub-off, rec-saves, which must be exit 4) into exit 1. The exact run-saving check in take_check.sh (all / all / True per flow, recovery flow excepted) already judges F-008. Documented in take_check.sh header. The F002 content check was extended instead.
- M6 "use the right error output index": the code at check_flows.py (the `normal` variable, IF = 2, switch = rules + fallback) already used the right index; only the docstring (line 31) was wrong (said main[1], said FAIL). Docstring fixed. No code change.
- Nothing ran in n8n or Postgres. Python 3.10 itself: not run here. The "git checkout -- raw selftest-output" at the end changed nothing: the folder was already committed by the board commit 7522f4190 (11:38Z) with my run outputs, so raw/ is at that state, not the pre-run state.

## Per item
- B1 (take_check.sh): `--write-warn-pin NEWFILE` refuses a file that exists or is the pin in use (exit 2, before the run); writes only after the comparison, only when the checker exit is 0 and a RESULT line exists; writes with noclobber; prints the difference; ALWAYS exits 4 ("writing a pin is never a pass"). README says how a person installs the pin (cp by hand, then a plain run must exit 0).
- M1: top block and FINAL line print `OVERRIDES: none` or `ACTIVE ENVIRONMENT OVERRIDES: ...`; TAKE_CHECK_CK/WARN_PIN/FLOWS/DDL/FORM_EXPECT are exit 4 unless `TAKE_CHECK_TEST=1` (documented test flag; run_all.sh and test_take_check.sh set it). New documented option `--flows DIR` (printed, not an override) replaces the old env var for the patched copy. The fixed ddl path text now prints the real path used.
- M2: explicit responseMode other than responseNode on mf-form.json / mf-hook.json is a FAIL (check_flows.py webhook_paths).
- M3: a listed flow that exists but is not a regular file (folder, dangling link) is a FAIL. A missing file keeps its existing file-list FAIL (adding a second FAIL broke the selftest case `missing_file`, so it is only raised when the name is in the folder listing).
- M4: pin header gets `# date (UTC)` and `# sha256 of the WARN lines below`; both checked (missing or mismatch = exit 4); the top block prints the pinned count and says they are known, unfixed defects.
- M5: F-002 content check now asserts ReplyBadKey and ReplyStoreFail are respondToWebhook and that Valid sets lead_key exactly once with a non-empty value (assert, not print).
- M6: docstring corrected (error output is the last output, WARN unless --fail-unverified).
- M7: a query with no readable table (for example only a `{{ }}` expression) is no longer counted as compared: WARN + counter; new closing line `SQL NOT COMPARED: ...` (not compared, compared with blanked `{{ }}` parts, ddl columns named like an SQL word); the take treats "not compared > 0" like the other not-compared counts (exit 4) and prints "compared" and "not compared" separately. On the real files: 0 not compared, 0 blanked-name conflicts, so the pin set did not change.
- N1 LC_ALL=C for sort and the pin hash; N2 exit statuses of both python helpers checked (exit 4 with a loud line); N3 the closing-block lines must appear exactly once; N4 relative paths made absolute before the cd, one temp folder (mktemp -d under TMPDIR) removed by one trap (also `.pin`/`.now` files); N5 ACCEPTED text no longer says "fires every 30 s" as a fact ("the lead says ... not read from the file"); N6 README latest log now fix-f8-r10.md; N7 README marks `--baseline` as PARKED.
- Coordinator item: plant case "form node count differs without an orphan" (extra wired noOp, 16 nodes vs 15) in test_take_check.sh for mf-form.json and mf-hook.json: exit 1, FAIL "node count 16 != expected 15", no orphan FAIL.

## Files changed (flow-check/ only)
check_flows.py, take_check.sh, take-warns.pin (header date + sha256, same 20 WARN lines), selftest.py (+13 cases, r10_*), run_all.sh (uses --flows and the test flag; calls the new test), test_take_check.sh (new, 22 cases), README.md, fix-f8-r10.md.

## Evidence (real exit codes)
- `bash run_all.sh <new work dir>`: exit 0. selftest 682 as expected, 0 not as expected, 62 skipped (was 668 + 62 before; +14 new cases). take_check.sh on patched copy: exit 0, missing lines: none. test_take_check.sh: 22 of 22.
- Old code, new tests (old files saved in scratchpad `bak-f8r10/`): new selftest against the old check_flows.py (FC_CK): 7 of the new cases NOT as expected (M2 x2, M3 x2, M5 x2, M7 x1), 675 others as expected. New test_take_check.sh against the old take_check.sh (with a small shim mapping --flows to the old env var): 18 of 22 not as expected (control, B1a-B1e, six M1, M3 x2, M4 x4); 4 pass on old code: the two count plants (regression guard, not a fix), 'written pin gives exit 0' and 'pin unchanged' (the old script never overwrote a pin in this sequence).
- `ruff check check_flows.py selftest.py`: exit 0. `ruff format --check check_flows.py selftest.py`: exit 0. `bandit -ll check_flows.py selftest.py`: exit 0. `bash -n` on the three shell scripts: exit 0. shellcheck: not installed, not run.

## Not checked
n8n import; shellcheck; the checks behave the same on Python 3.10 (run here with the machine's python3); real-database behaviour.
