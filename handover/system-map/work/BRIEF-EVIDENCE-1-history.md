

## Removed 16 Nov 2026 14:20 UTC (stacked lane rules, ADDED paragraph, cold-read r3 and r4 lists)
LANE MUST-NOT LIST (system-map ORDER 002): write ONLY your own work/<lane>.md file (rewrite it incrementally, never leave it unreadable); no git; no network; do not run or import any repo file; no secret, key, token, password or personal e-mail VALUE ever in your file (record path:line and TYPE only); no deletion; no merging; no "known limitation" or deferral (fix it or write the exact blocker in the Findings table); no claim without a citation `path:line "quote"` copied from the file; anything that needs a runtime is UNVERIFIED; sources not in this box are `NOT VISIBLE: <name>`, never guessed. You are a read-only auditor: you may not change any file except your lane file.

EVIDENCE RUNNER. You run commands and record raw output. You never judge, never fix, never edit any file except work/evidence-1.md. Use only Bash and Write. Repo root: /home/user/hadavin-sdk, folder handover/system-map. Run from that folder, each command exactly, and paste the command, the exit code and the raw output (cut to the last 40 lines if longer) into work/evidence-1.md under one heading per command:
1. python3 tools/partition.py ../.. /tmp/manifests ; echo rc=$?
2. python3 -m unittest discover tests 2>&1 | tail -5
3. python3 tools/scan_outputs.py . ; echo rc=$?
4. python3 tools/check_citations.py ../.. /tmp/cit-lanes.tsv work/L1.md work/L1c.md work/L2.md work/L2c.md work/L3.md work/L3c.md work/L4.md work/L4c.md work/L5a.md work/L5ac.md work/L5b.md work/L6.md ; echo rc=$?
5. python3 tools/check_citations.py ../.. /tmp/cit-out.tsv MASTER-MAP.md SWEEP.md ONE-PLACE-TABLE.md ; echo rc=$?
6. cut -f4 /tmp/cit-lanes.tsv | sort | uniq -c ; cut -f4 /tmp/cit-out.tsv | sort | uniq -c
7. grep -c '^| ' MASTER-MAP.md ; grep -c '^Owner:' ONE-PLACE-TABLE.md ; grep -n '^## ' SWEEP.md ONE-PLACE-TABLE.md
8. git status --short | head -20 ; git diff --stat HEAD~3 -- ../../src ../../tests | tail -3
MUST-NOT: edit any file other than work/evidence-1.md; run network commands; run git commit, push, checkout or reset; start any background process; write any secret. Report: one line per command with the exit code. Write EVIDENCE RUNNER in your first line of work/evidence-1.md.



ADDED 16 Nov 2026 (second cold read, this is the only ADDED paragraph): Before any command, run `cat work/OWNER-ONLY.txt`. Its paths are relative to /home/user/hadavin-sdk, one per line; a path is listed if it equals a line or starts with a line plus a slash. If the file is missing or empty, write that in your evidence file and stop. Never open a listed path. If any output line names a listed path, or a command prints content from a listed path, replace that line or output with `<PATH>: NOT READ`. Run the eight commands listed in this brief, each exactly; where one has no exit code capture add `; echo rc=$?`. If a command fails, record it and go on. Exceptions to the lines above: read-only git status and git diff --stat are allowed; the only repo file you write is your evidence file; rule 8 (tests only through uv pytest) and preamble rules 1, 3 and 12 do not apply. Write masked values as <MASKED:secret>, <MASKED:address> or <MASKED:key>. Decision 1 (the video is real-v5 scenes 1 to 4) and decision 3 (the roles proposal is parked) are context only: take no action on them.
Also: running the tools under tools/ and the unit tests is allowed (the earlier 'run no repo file' line does not apply to them). The only file you write is your evidence file. For a pipe, the exit code is the last command's unless you use ${PIPESTATUS[0]}; write which one you used. If git has no history for a command (for example HEAD~3), record the failure and continue.

RULES FOR THIS TASK (16 Nov 2026, cold read r3; this list wins and every earlier rule that differs is void): You are an evidence runner; you never judge. You may run the eight listed commands, the scripts under tools/ and the unit tests in tests/. For git you may run only `git status` and `git diff --stat`. You may write only work/evidence-1.md (the studio lead reads it; do not report elsewhere). Paths are Linux paths under /home/user/hadavin-sdk/handover/system-map/; Windows paths and egm\<topic>\ folders do not exist here. Masking: in the evidence file use <MASKED:secret|address|key> for values; for any path listed in work/OWNER-ONLY.txt write `<PATH>: NOT READ`. Undefined labels (ORDER 002, lane, bible, R-numbers, decision 1 real-v5, roles proposal) do not apply to you: ignore them.

RULES ADDED (cold read r4, wins): Command 0 is `cat work/OWNER-ONLY.txt`; if the file is missing or empty, record that and stop. Give each command with `; echo rc=$?`; for commands 2, 6 and 7 (pipes) record ${PIPESTATUS[0]} and label it. Writes by the tools under /tmp are allowed. After writing work/evidence-1.md, return one line per command with its exit code to the caller. Ignore preamble lines 1-23 except the masking rules.

