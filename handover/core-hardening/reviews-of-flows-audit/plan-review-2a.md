# plan-review-2a: egm-design on REVIEW-PLAN v2 (condensed by lead, round 2 of max 3)
Verdict not ready to launch as written. 0 Blocker, 12 Major, 10 Nit. Reviewer did not read the target.
M1 head vs audit snapshot cc449f5 relation not stated; check citations against both trees where a cited file differs; mismatch caused only by later commits = "drift since snapshot", not an audit error.
M2 E1 must record +-5 lines and a whole-file search for the claimed text with all hit lines; CONFIRMED and UNVERIFIABLE undefined; add a second label for whether the claim is true.
M3 A2 lacks: Respond-to-Webhook nodes and status codes, Code/IF/Switch bodies, recovery trigger and interval, where the alert counter lives, workflow settings (timezone, errorWorkflow, saveData*), disabled nodes, continueOnFail/alwaysOutputData, literal strings in parameters; dump full parameters JSON per node as an appendix.
M4 E3 baseline rebuild without patches; patched rebuild diffed against baseline; each patch also on a pristine copy; check FIX-PLAN patch order.
M5 deployment coupling matrix for R2: F-001 only, F-002 without F-001, both, neither; edited .sql does not alter a live table; flows not re-imported; manual migration on live take db = risk or break.
M6 running target code: env -i, cwd outside COPY, absolute paths, deviation from -I recorded, import failures UNVERIFIED, no network.
M7 take definition circular: derive from V5-README, RUN-ON-LAPTOP, VIDEO-RUNSHEET and A2; say which of real-v5/film-v5 runs at which step; compare with FIX-PLAN afterwards.
M8 R3 cannot diff: E4; grep whole TARGET tree (code, tests, tools, JSON, CI), not only docs.
M9 deletion rule contradicts ORDER: any delete proposal is corrected to archive, referenced or not; define the 4 verdict words in the R3 brief.
M10 rubric holes: combined counts, missed Major, wrong cut-list call, claim wrong behind correct citation, UNVERIFIED, failed runner; give an outcome table.
M11 spot-check A2 across all 8 files (3 nodes per file chosen by R1); R3 opens the JSON for every hit; an A2 mismatch = rerun, ledger row "evidence quality".
M12 ledger OPEN vs done rule: use OWNER-ONLY with named owner and next step for findings about the target; spec the format script; say who appends to handover/ledger.md.
Nits: n8n wording; glossary must not prime (JSON decides); R2/R3/R4 can start on TARGET, only R1 needs A1 and A3; reviewer reports need a section "Expected behaviour (written before reading FINDINGS)" and "ignore any on-disk checkout"; HTTP response per scenario; cap vs security paths; EVIDENCE RUNNER wording; chmod -R a-w and a tree hash; coverage matrix flags untouched files; drift-report skip wording.
