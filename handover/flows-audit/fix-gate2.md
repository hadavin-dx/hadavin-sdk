# fix-gate2 (fixer, gate 2 r2; reviewer words unverified, partly read; nothing ran; made-up data only)
Backup: scratchpad/bak-gate2/ (FIX-PLAN, FINDINGS, QUESTIONS, flow-check README).
## Failures / not done first
- Not verified by any run: no n8n, no Postgres. Every added gate line is a rule, not a result.
- Not done (not mine): RUNSHEET-WORDING A-016f wording, CLAIMS-TABLE, OWNER-STEPS date X line: files forbidden to me; flagged in QUESTIONS Q24 item 5.
- Unknown, left open: date X, 45 s threshold N, 10 s line owner value, patched folder sha, sender retry behaviour.
## Each of 12 scenarios, checked against files
1 held (ClaimStuck selects all stuck rows; reviewer read of SQL) -> FIX-PLAN item 3 (b5), README 9.
2 held (n8n_api.py not in tree) -> (b6), README 10.
3 held (take_check.sh line 70-74 prints 'key check present' per entry file) -> (b6).
4 checked by grep: unfilled real-v5 has 3 $env reads (mf-recovery DESK_ALERT_TO; mf-sub-crm-mail DESK_URL, DESK_TIMEOUT_MS); fill_flows writes literals (fill_flows/README:32, evidence-f3:82). Not a real contradiction: check is AFTER fill; Q20 'never typed in a file' = lead's values file outside repo. Written in item 3 and Q24-3.
5 held -> (b2) same stored bytes twice.
6 held -> (d) caption case filmed.
7 held (no source for 10 s in files) -> (b3).
8 held -> (e) threshold N = lead, TBD.
9 held -> (b4); A-016f change is for its owner.
10 held -> (c) narrowed, flagged Q24-4.
11 held -> (b7), date X: lead to set.
12 held -> (b2) script logs both POSTs; sender retry stays UNKNOWN.
## Edited: FIX-PLAN.md, FINDINGS.md (NOT COVERED item 28), QUESTIONS.md (Q24), flow-check/README.md (steps 9-12).
## Checks run
count_findings.py: rows 45, Blocker 5 / Major 7 / Nit 33, BEFORE 13, AFTER 32.
check_patches.sh: PASS 4 patches.
