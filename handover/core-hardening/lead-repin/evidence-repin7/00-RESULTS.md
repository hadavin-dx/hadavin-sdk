# Results, re-pin v7 evidence (builder; raw files in this folder; no judging here). 16 Nov 2026, finished about 16:52 UTC / 22:22 IST (5 minutes past the 60-minute stop)

## Failures and gaps first
1. `lead-repin-verify.sh` is still v6 (sha256 e419fdeb...2617). The permission system refused my copy of v7 over it; I did not work around it. v7 is `lead-repin-verify.v7.sh` (sha256 in `10-sha256.txt`). The lead promotes it. The guide `LEAD-REPIN-VERIFY.v7.md` is likewise a separate file.
2. Mutant v09 (kill_tree of the kids not called) SURVIVES in dash and bash, for v6 and for v7. Reason: the other kill of the background process already ends everything in my tests, so it is a redundant damage (equivalent). Not proven equivalent by a formal argument.
3. Own slip found and fixed: the self-test case "signal HUP in the main phase" fails (exit 0) when the caller ignores HUP (for example started with nohup; no script can catch a signal ignored at entry). First v7 batch failed on it (both shells). v7 now prints "NOT TESTED" in that situation; the final batch ran without nohup so the case really ran (0 NOT-TESTED lines in 13-*).
4. Mutant v24 first could not be planted (wrong text); I corrected the driver and re-ran it alone: `11c-mutant-v24-rerun.txt` (killed in both shells). The first batch files 11 and 11b still show PLANT-FAILED for v24.
5. Not done: security-review minor 4 (kill_tree PPID list without ps) and minor 8 (fixed second limits; large-tree timing). The guide still tells the reader to paste a command in one place (tension noted by the review). I ran over my stop time by about 5 minutes.
6. Not checked: no independent reviewer ran on v7 (that is the lead's EGM step); v7 was not run on a real Windows or macOS machine.

## Signals (the v6 12 of 16 BAD)
Cause: the launcher, not the script. Valid repro with the OLD launcher under a parent that ignores INT, QUIT and HUP: 12 of 16 BAD (`04b`). Fixed launcher on v6: `02`, `03`. Fixed launcher on v7: `12-signals-v7.txt` = BAD rows: 0 of 16, launcher exit 0. `04a` is an invalid repro (kept, labelled). SCRIPT FAULT: none.

## v7 self-test
- dash: passed=1398 failed=0, exit 0 (`13-selftest-v7-dash.txt`); bash: same (`13-selftest-v7-bash.txt`).
- non-root (uid 65534, setpriv): passed=1398 failed=0, exit 0 (`15-selftest-v7-nonroot.txt`).
- The v7 cases against the v6 filter: passed=1177 failed=192 (`14-...`), so the new cases fail on v6.

## Mutation (v01 to v29, `11-mutants-v7-dash.txt`, `11b-mutants-v7-bash.txt`)
dash and bash: every damage ended with a failing self-test or refused tally except v09 (above); v24 killed in the re-run. v07 and v08 show failed=0 but exit 1 (the count judge refuses the wrong planned number: that is the kill). v6 lanes: `06`, `07`.

## Timing (`timing-1mb.txt`)
1,001,001-character line through --mask: 2.05, 2.11, 2.05 s; tiny input: 2.03, 1.99, 2.06 s. The guide sentence was updated to these numbers.

## Counts and hashes
`10-sha256.txt`. v6-CHANGES.md Counts section already had text, so not edited; counts are here. Banned vendor-name check on all 254 files of lead-repin/: 10 listed words read at run time, 0 hits. __pycache__ deleted.

## Processes
I started and ended my own batches. Old builder's mutate.py pid 21873 and stale processes were left alone (not mine).
