# fix-q18 (2026-11-16): F-008 manual runs ON, recovery "none" accepted, three extra items

## Failures and unverified (first)
- Nothing ran in n8n. All of this is file checks only.
- UNVERIFIED: "system-map checks the run list" (lead's statement, not checked by me). UNVERIFIED: that n8n really saves manual runs when saveManualExecutions is True.
- The first full run_all failed twice on my own mistakes, fixed: (a) two new selftest cases expected the wrong WARN text; (b) the exit-3 stub for take_check was a shell script run by python (got exit 1), now a python stub.
- Consequence to know: take_check.sh on the committed UNPATCHED real-v5 now exits 4 (run saving is off there). The take must run on the patched copy; run_all.sh does that (exit 0 required) and also requires exit 4 on the unpatched folder.
- Not checked: the F-008 patch applied to the real tree (only to scratch copies); n8n import.

## What changed
- patches/F-008...patch: saveManualExecutions True in ST (3 flows); recovery ST_NONE unchanged (none, manual False). Reason is a Python comment line in the patch. check_patches.sh: PASS 4 patches, rc 0.
- check_flows.py: new option --accept-no-save FILE (exact file name). Smaller than extending --accept-if (that one is keyed on IF nodes). Honoured only for a flow whose triggers are all schedule triggers (no hard-coded name inside the checker); other flow: WARN stays plus a second WARN "accept refused". Unused accept: WARN. Prints "ACCEPTED: recovery flow not part of the take (decision 4): ... reason". F008 patch check now also requires manual True (False for recovery); diff allow-list includes saveManualExecutions.
- take_check.sh: passes --accept-no-save mf-recovery.json only; any remaining run-saving WARN or idle accept gives "!!!" line and exit 4; INFO line per flow with saving ON stating it is on purpose (item 3); KeyOk check reads the node list as JSON (item 1); env TAKE_CHECK_FORM_EXPECT and TAKE_CHECK_CK (tests only).
- run_all.sh: accept added to the checker runs; take_check run on the patched copy; new exit-4 cases (unpatched, form off, sub off, idle recovery accept), key-check-by-node-list case (item 1), checker exit 2 (non-UTF8 --ddl) and exit 3 (stub) cases (item 2), 3 INFO lines required (item 3).
- selftest.py: 7 new q18 cases. README.md, REGENERATED-NOTE.md, FIX-PLAN.md updated.

## Gates (rc from the command, no pipe)
- bash run_all.sh: rc 0. selftest 659 as expected, 0 not; take_check missing lines: none. (before: 657 + 2 failures of my own, fixed.)
- sh handover/flows-audit/tools/check_patches.sh: PASS 4 patches, rc 0.
- ruff check rc 0; ruff format --check rc 0; bandit -ll -r flow-check rc 0 (0 medium/high); noqa|nosec|type: ignore count 0 in all four files.

## Proof the new cases fail on the old code
- New selftest vs backup of the old check_flows.py: 637 as expected, 22 not. 6 of the 7 q18 cases fail (rc 2, unknown option); the 7th (no accept = WARN) is a control and passes on both. The other 16 are the patched-folder cases: the patched folder now has manual True, which the old checker flags.
- New selftest vs new checker: 659 as expected, 0 not.
- Mutants of take_check.sh in a scratch copy (both killed, run_all exit 1 with a named missing line): M5 `-ge 2` to `-ge 5` (caught by the exit 2 and exit 3 cases); KeyOk check back to a text match (caught by the keyok-gone case).

## Hostile cases
- accept names a file that does not exist: WARN "excused nothing" (selftest case; take_check exit 4 when it is the recovery name).
- accept given for the form flow (and the sub-workflow) with saving off: its WARN stays, plus an "accept refused" WARN, no ACCEPTED line for it.
- patch applied twice: git apply --check on the already patched copy: rc 1, "patch does not apply".
- non-UTF8 --ddl through take_check: exit 2 with the no-verdict line.
- Bad value (path with a slash): usage error, exit 2.

Raw: raw/ (this run), scratchpad q18-selftest-oldchecker.txt and q18-selftest-new.txt. Backups: scratchpad bak-q18/.
