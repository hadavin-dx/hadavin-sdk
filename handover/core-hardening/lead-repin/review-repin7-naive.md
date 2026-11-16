# Re-pin v7 stranger-reader review (egm-comprehension, condensed copy of the inline report), 2026-11-16
Read: LEAD-REPIN-VERIFY.v7.md, v7-CHANGES.md, script lines 1-150 (header, usage, exit codes); two greps. Script lines 151 onward not read; nothing run.

## BLOCKER
- B1 Guide (lines 24, 52, 55) says `lead-repin-verify.sh`; the file in the folder is `lead-repin-verify.v7.sh`; v7-CHANGES.md line 3 says the `.sh` is still v6 and the lead promotes v7 with `cp`; the guide never says so. A reader running `lead-repin-verify.sh` gets v6 (self-test count not 1398) and line 57 says stop. Fix: Quick start names the file to use today and who does the `cp`.
- B2 The stop rule (guide line 57: any last line other than the exact one means stop) contradicts `NOT TESTED` (script line 1355, printed when HUP is ignored, e.g. under nohup). `NOT TESTED` is not in the line 73-89 table, the stop list or the glossary; unclear if pass, fail, or counted in passed=1398 (tally code not read). Fix: add a table row with the action (rerun without nohup, or send to the lead).

## MAJOR
- M3 "paste" (guide line 69) vs script: no channel is named for the answer sheet or the masked copy; line 12 says tell the lead only, "not to a chat"; line 19 "typing a secret into a chat"; `--mask` is a different use.
- M4 Exit code 0 plus STOP-SIGNAL (line 89 "do not share the output") vs line 70 (lead gets the masked copy): no channel for "tell the lead the file and line number".
- M5 "Stop" means three things (end the task; skip that search; line 20 "stop; do not run step 3" vs line 57 step 1 = self-test, step 2 = the run: line 20 and line 57 disagree).
- M6 Hand-in under-specified: "which commit (from block R00)" with no sample output; blocks G35, G06, G04, G18 etc. referenced but never listed; no example of BLOCK / RUN-CHECK / STOP-SIGNAL.
- M7 Guide says none of it was checked against the real program and G and R numbers were not re-read against newer files (lines 5, 8); no one is named to recheck.
- M8 Many tasks end "cannot be done with this guide" (lines 155, 178, 200, 206, 220); no single list of things to get from the lead before starting.

## Words with two meanings
take / TAKE_DIR (script usage line 37 still `[TAKE_DIR]`); head vs final commit; stage vs step (script comments lines 125-127 "Stage 1/2", guide says step 0, 1, 2); window / deadline / time limit / lease; block; search; copy / masked copy / COPY-OF-OUTPUT; self-test vs start check (line 28 "same list" vs line 57 1398 vs 1372 cases); mask / hide; end; commit; exit code (`$?` after other commands); agent undefined; UNVERIFIED vs "not shown"; R, G, Q codes unexplained; "canary" undefined.

## Guide and script disagree
File name; step numbering line 20 vs 57; case counts 1398 / 1372 unconfirmed; "Stage"/`TAKE_DIR` vs renamed terms; who reads the output (script line 34 the lead; guide line 139 the reader).

## Minor
Cancel-by "18:19 UTC (23:49 IST)" (line 107) has no date next to it in the same sentence; self-test time (about 2 min) vs mask check (2 s) and normal run time not stated; "error channel" undefined; v7-CHANGES.md uses codes M1-M6, L1-L3 explained only in review-repin6-security.md and has no pass/fail summary; v7 has had no result review and the guide title does not say so; guide lines 125 and 129 are single bullets of dozens of items.

## Could not check
Script lines 151-1900 (filter rules, tally of NOT TESTED, block wording, counts 1398/1372); evidence files; ORDERS.md; owner sheets.
