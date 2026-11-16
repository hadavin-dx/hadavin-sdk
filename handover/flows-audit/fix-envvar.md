# fix-envvar (static edit, nothing was run)

FAILED / UNCERTAIN FIRST
- Nothing was run. take_check.sh was read (header, lines about overrides and --flows / --write-warn-pin); the claim "env forms exit 4" rests on that text, not on a run.
- flow-check/README.md has no command line using the env forms (only the exit-code text); aa10943 is still editing flow-check/, so this was read by text only.
- RUNBOOK.md was read, not edited. It already names the same two failures; its own list (line 131) still names these forms in FIX-PLAN, TAKE-CHECKLIST and flow-check/README.md: the lead can now strike the first two.

CHANGED (backup in scratchpad bak-env/)
- TAKE-CHECKLIST.md row 1: new-pin route is now: --write-warn-pin to a NEW file, a person copies it over flow-check/take-warns.pin, lead commits (second sha; lead decides, RUNBOOK I24), same --flows command again. Last cell: lead checks the script header still lists --flows / --write-warn-pin; exit 4 "environment override" means unset TAKE_CHECK_ variables.
- FIX-PLAN.md step 4: `--flows` form; step 9: `--flows` form for both runs, `--write-warn-pin` with --flows, copy-over-and-commit route, second sha note; step 15: refers to the --flows command.
- Remaining TAKE_CHECK_* mentions in both files are only warnings that they exit 4 (and TAKE_CHECK_FORM_EXPECT as test override).
