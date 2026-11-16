# fix-f8-r7 (fixer, round 7). Input: evidence-q18.md. Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-f8r7/

## Failures and what is not fully resolved (first)
1. `ruff format --check` failure: NOT reproducible. The backed-up check_flows.py and selftest.py (before any edit of mine) pass `ruff format --check` with the repo settings (/home/user/hadavin-sdk/pyproject.toml, line-length 100). They fail only with ruff defaults (line length 88, `--isolated`), so the evidence runner most likely ran ruff on a copy without the repo pyproject.toml. check_flows.py is byte-identical to its backup (nothing to reformat); selftest.py was reformatted by ruff only for my new lines. Next step for the evidence runner: run ruff from inside the repo.
2. M10 is equivalent (not a gap): see below.
3. README.md needs no change from me. Optional README note for the other fixer: run_all.sh now accepts RUN_ALL_RAW, RUN_ALL_TAKE_FLOWS, RUN_ALL_NESTED (test hooks, described in a comment at the top of the script); run_all.sh now runs a second copy of itself (about 8 s more).

## Fixes
- run_all.sh: `TCMISS=""` now set right after the take check runs, before its first use. Old behaviour: line 76 `TCMISS: unbound variable` crash when the take script failed on the patched copy, and the first two checks were also thrown away by the later `TCMISS=""`.
- run_all.sh new check A (kills M12): the FINAL line of take_check.sh must print the real exit status (patched take, every exit-4 case, and the exit 2/3 no-verdict cases).
- run_all.sh new check B (nested failure test): a second run of run_all.sh with the form flow's run saving off must end exit 1, show `[take_check.sh exit=4] missing lines: ...` and not contain "unbound variable". Raw copy: raw/nested-take-failure.txt.
- selftest.py +3 cases (659 -> 662, 0 not as expected, 62 skipped unchanged): patchonly_f008_manual_off_form (kills M7), patchonly_f008_manual_missing_sub, q18_other_schedule_only_flow_is_not_excused_by_the_recovery_name (a copy of the recovery flow named mf-recovery2.json, saving off, only mf-recovery.json accepted: must WARN, must not print ACCEPTED for it; kills M2 and M3).
- take_check.sh and check_flows.py: no edit needed.

## M10 decision
M10 removes the alternative `^WARN accept-no-save` from the grep that sets "run saving off". The idle-accept WARN line is `WARN accept-no-save --accept-no-save X excused nothing: ... run-saving settings are not off ...`, so the first alternative `^WARN .*run-saving settings` already matches it. For the current wording the removed alternative never changes an outcome: equivalent mutant. Kept the alternative as a guard against a future wording change. Not testable without changing the warning text.

## Mutant proof (copy in /tmp/f8r7mut, live files untouched; each run = bash run_all.sh)
| mutant | run_all rc | what caught it |
|---|---|---|
| M2 blanket accept | 1 | selftest 661 ok / 1 not (new q18_other_schedule... case) |
| M3 mf- prefix accept | 1 | same new case |
| M7 F008 manual check off | 1 | selftest 660 ok / 2 not (both new patchonly_f008 cases) |
| M12 FINAL always 0 | 1 | run_all take_check lines: "want exit 4, the FINAL line with 4" for every exit-4 case |
| M13 old bug (TCMISS init removed) | 1 | crash `line 151: TCMISS: unbound variable` seen by the new test |
| M10 | 0 | survives: equivalent (above) |
Fixed code: all pass.

## Gates on the live files (own rc lines)
- bash run_all.sh: rc=0; `SELFTEST: 662 as expected, 0 not as expected, 62 skipped`; take_check.sh exit=0 missing lines: none; run_all exit status 0.
- ruff check handover/flows-audit/flow-check/: rc=0 All checks passed. ruff format --check: rc=0 (32 files already formatted). bandit -ll check_flows.py selftest.py: rc=0, no findings. sh handover/flows-audit/tools/check_patches.sh (from repo root): rc=0 PASS 4 patches. No noqa/nosec/type: ignore added.
Not checked: nothing ran in n8n; the full-folder mutation set M1-M12 was not re-run beyond the six above.
