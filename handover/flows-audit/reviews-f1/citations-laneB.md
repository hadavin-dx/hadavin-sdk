# Citation check, lane B (B-001 to B-216), second sample

Checker: static, read-only. Snapshot of the table copied to the scratchpad before reading; CLAIMS-TABLE.md not edited. Nothing was run (no n8n, no tests).

## Result first
- Rows checked: 127 of 226 B rows (every row that is SUPPORTED, plus every third other row, leaving out B-051, B-054, B-108, B-182 and B-213 to B-216, which earlier reviewers sampled). RELAYED-ONLY rows were included when they fell on the every-third step.
- OK: 123. WRONG: 4 (B-184 quote wording, B-107 and B-155 trace for the real-v5 CrmUpsert node, B-114 row count). ABSENT: 0 (every cited file, line and node exists).
- Method: for each row I read the cited line(s) of the real file and compared the quoted words (automatic word match, 100% for 126 rows, 8 of 9 for B-184). I then checked every trace statement that names a node, SQL text, file line or number by parsing the flow JSON (real-v5, film-v5, v4, n8n-flows) and reading the named line. UNTRACED rows: I confirmed the quote and that the named file is absent from the checkout (searched for take scripts, qualify_stage.py, run_real_check*); I cannot prove absence outside this checkout.
- Not checked: relayed raw numbers (raw files absent), n8n/HubSpot/Gmail behaviour, verdict judgment (UNTRACED vs UNSUPPORTED) beyond what the lines show, whether PASS lines in tests are true.
- Key letters: file keys are those of CLAIMS-TABLE Part 2 (CM = demo/CLEAN-MACHINE-1.md, RERUN = demo/RERUN-RUNBOOK.md, SKIP = demo/n8n-skip-on-conflict.md; not listed in the table key, I resolved them by content).

## Failures

| id | cite | what the file really says | verdict |
|---|---|---|---|
| B-114 | RERUN:88 | Mean idle 90.1 percent is right (N8N-ENV-PROBE.md:194 `id=90.1395`), but that line says `rows=129` after the first row; RERUN:88 and the table say "130 rows". Off by one (RERUN counts the first row or the count is stale). | WRONG (number 130 vs 129; 90.1 holds) |
| B-184 | OWNS:5 | Table quotes "...sit in the coordinator's take harness"; the file says "sit in the lead's take harness (stated, not tested by me)". Meaning the same, quoted words differ (looks like a global rename of "lead" to "coordinator" that also hit a quotation). | WRONG (quote wording only; claim and UNTRACED verdict stand) |
| B-107 | RUN:78 / trace column | Quote and the n8n-flows half are right (timeout 15000, maxTries 3). The trace says "v5 uses 10 s, 2 tries" for Qualify AND CrmUpsert. In n8n-flows-real-v5/mf-sub-crm-mail.json CrmUpsert is the HubSpot node with `options: {}` (no timeout; maxTries 2). Only Qualify (10 s default) and film-v5 CrmUpsert (timeout 10000) have 10 s. | WRONG in the trace for real-v5 CrmUpsert |
| B-155 | DESIGN:20 / trace column | Quote right (DESIGN:20). Trace "Qualify and CrmUpsert maxTries 2, timeout 10 s" is false for real-v5 CrmUpsert (HubSpot node, no timeout option; BM:25-30 comment says "no timeout option"). True for Qualify in both and for film-v5 CrmUpsert. It also weakens B-156/B-060 wording that the HubSpot node has no timeout, which stays correct. | WRONG in the trace for real-v5 CrmUpsert |

## All other checked rows

| id | cite | what the file really says | OK/WRONG/ABSENT |
|---|---|---|---|
| B-001 | PLAN:9 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-003 | PLAN:9, :57, :184 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-004 | PLAN:9 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-005 | PLAN:11 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-006 | PLAN:12 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-007 | PLAN:34 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-008 | PLAN:35 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-009 | PLAN:37 | real-v5 CrmUpsert n8n-nodes-base.hubspot typeVersion 2.2, operation upsert, email key; BM:26 comment. | OK |
| B-012 | PLAN:39 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-015 | PLAN:41 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-018 | PLAN:44 | Quoted words found in the cited line(s); table says no file traces it, none found. | OK |
| B-021 | PLAN:47 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-024 | PLAN:50 | Quoted words found in the cited line(s); table says no file traces it, none found. | OK |
| B-026 | PLAN:57 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-027 | PLAN:57 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-028 | PLAN:57 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-030 | PLAN:57 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-033 | PLAN:57 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-036 | PLAN:57 | V7-NUMBERS-lead-read.md:4 AF1 "first alert 272.1 s" confirmed. | OK |
| B-039 | PLAN:67 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-042 | PLAN:78 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-043 | PLAN:78 | stage_server.py:51 returns unknown if started; 52 writes started before the call (54). | OK |
| B-045 | PLAN:79 | stage_server.py:48 `with LK:` then 52 journal write; 54 `Q.qualify` outside the lock. | OK |
| B-047 | PLAN:79 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-048 | PLAN:80 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-050 | PLAN:108 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-052 | PLAN:112 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-053 | PLAN:121 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-055 | PLAN:122 | Same parse as B-175: confirmed. | OK |
| B-056 | PLAN:126 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-057 | PLAN:126 | smtp_catcher.py:44-47 confirmed. | OK |
| B-059 | PLAN:154 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-060 | PLAN:192 | SendMail has no timeout option; MailRowBack false -> MarkUnknownB (`AND mail_sent`); DoneOwned false -> OutLost. | OK |
| B-061 | PLAN:194 | real-v5/film-v5 Claim 45 s; n8n-flows/mf-form.json 120 s. | OK |
| B-062 | PLAN:195 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-063 | PLAN:197 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-065 | WATCH:8 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-068 | WATCH:10 | Quoted words found in the cited line(s); table says no file traces it, none found. | OK |
| B-070 | DOUBTFUL:3 | smtp_catcher.py:40 stores, :44-47 drop counter then return without answer. | OK |
| B-071 | DOUBTFUL:3 | stage_server.py:11 imports lead_desk.live_claude; no fake model server file in checkout. | OK |
| B-072 | DOUBTFUL:4 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-073 | DOUBTFUL:4 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-074 | DOUBTFUL:9 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-075 | DOUBTFUL:10 | smtp_catcher.py:40 stores before :44-47 drop. | OK |
| B-077 | DOUBTFUL:12 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-078 | DOUBTFUL:12 | BM:108-109 text exact ("... may or may not have been sent. A person decides."). | OK |
| B-079 | DOUBTFUL:12 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-080 | DOUBTFUL:12 | same V7-NUMBERS line 4 confirmed. | OK |
| B-082 | DOUBTFUL:12 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-083 | DOUBTFUL:12 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-084 | DOUBTFUL:13 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-086 | DOUBTFUL:13 | N8N-START.md:40-42 confirmed. | OK |
| B-089 | FAILED:7 | Quoted words found in the cited line(s); table says no file traces it, none found. | OK |
| B-092 | FAILED:12 | Quoted words found in the cited line(s); table says no file traces it, none found. | OK |
| B-095 | FAILED:19 | FAILED:19 quote; PLAN-4:137 names "US$189 window cap (ends 2026-11-23 23:59 IST)". | OK |
| B-096 | FAILED:20 | FAILED:20 quote; find for take/run_real_check_n8n*/qualify_stage.py in the checkout: none. | OK |
| B-098 | RUN:26 | mf.py:321 `def t14`; REC StuckRow/AlertRow guard on lead_key notEmpty; BM:114 comment present. | OK |
| B-101 | RUN:56 | mf.py:83 `lost = state not in ("done","unknown","failed") ...` so review counts as lost; RUN:56 says review is final. | OK |
| B-103 | RUN:64 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-104 | RUN:65 | RUN:65 quote; V7-NUMBERS T11 row (8 leads, 0 lost, 0 doubled) present. | OK |
| B-111 | RERUN:42 | RERUN:42 says first two digest pulls failed; DOCKER-PROBE.md:5 says tag pull failed twice, digest worked on third try: the two texts differ (table row already says so). | OK |
| B-117 | CM:5 | CLEAN-MACHINE-1.md:5 contains every number quoted. | OK |
| B-120 | CM:15 | CLEAN-MACHINE-1.md:15 contains every number quoted; C2-e2e-313.md row S4 matches. | OK |
| B-121 | START:4 | grep DB_TYPE / DB_POSTGRESDB under handover/demo: 0 hits; START:4 says SQLite inside n8n. | OK |
| B-122 | START:7, :9-11 | real-v5 `$env` reads: DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO only (film-v5 reads MF_* instead). | OK |
| B-123 | START:13 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-124 | START:13 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-126 | START:27 | Quoted words found in the cited line(s); table says no file traces it, none found. | OK |
| B-127 | START:27 | All 8 JSON files (real-v5 and film-v5) carry saveDataSuccessExecution none, saveDataErrorExecution none, saveManualExecutions false; BM:44 same. | OK |
| B-128 | START:30 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-129 | START:30 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-132 | START:33 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-133 | START:36 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-135 | START:36 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-138 | START:42 | N8N-START.md:42 confirmed. | OK |
| B-141 | START:51 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-142 | DESIGN:6 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-143 | DESIGN:13 | FORM nodes Receive, Item, Valid, Claim, Claimed, IsProcessing, ReplyReview, Stored, ReplyStored exist; Claim sets state review and attempts 0 for invalid e-mail. | OK |
| B-144 | DESIGN:14 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-146 | DESIGN:15 | LabelOk `['hot','warm','cold'].includes($json.label) && !$json.unknown_model`; false -> OutStage. | OK |
| B-147 | DESIGN:15 | crm_stub.py doc lines 2-3: upsert keyed on lead id AND e-mail; real-v5 HubSpot node keyed on e-mail (BM:26). | OK |
| B-148 | DESIGN:15 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-149 | DESIGN:15 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-150 | DESIGN:15, :32 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-152 | DESIGN:16 | REC ClaimStuck SQL matches word for word (LIMIT 5, SKIP LOCKED, attempts < 3). | OK |
| B-153 | DESIGN:16 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-156 | DESIGN:20 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-159 | DESIGN:28 | stage_server.py:17-23 journal() reads file, `except OSError: pass` returns {}; a bad JSON line is not caught. | OK |
| B-160 | DESIGN:28 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-161 | DESIGN:28 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-162 | DESIGN:36 | REC links Every30s -> MarkFailed, ClaimStuck, AlertClaim (in that order); ClaimStuck/RunSub/MarkFailed onError continueRegularOutput; no node AlertFailed. | OK |
| B-163 | DESIGN:39 | REC AlertClaim LIMIT 5; AlertMark connected from AlertSend output 0 only; AlertBackoff from output 1. | OK |
| B-164 | DESIGN:39 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-165 | DESIGN:40 | AlertClaim 720 s; AlertBackoff `60 seconds * LEAST(alert_attempts, 5)`; no cap in AlertClaim. | OK |
| B-166 | DESIGN:41 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-167 | DESIGN:41 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-168 | DESIGN:42 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-170 | DESIGN:45 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-171 | V5:3 | SUB SetCrmId queryReplacement `String($json.id ?? $json.vid ?? '')` in real-v5 and film-v5. | OK |
| B-174 | V5:6 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-175 | V5:14 | Parsed v4 vs v5 sub-flow: added CrmIdOk; changed CrmUpsert and SetCrmId; other 3 files byte-identical (md5). | OK |
| B-176 | V5:17 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-177 | V5:19 | crm_stub.py:9 CTL upsert_answer "id"; :42 reads it. | OK |
| B-178 | V5:20 | mf.py:339 `def t17`, :348 `def t18`. | OK |
| B-179 | V5:22 | CrmIdOk `/^[0-9]+$/.test(String(CrmUpsert.id ?? CrmUpsert.vid ?? ''))`; false -> OutStage. | OK |
| B-180 | V5:22 | n8n-tests/test_crmid_regex.py CASES list (line 5, 22 lines in file); PASS not re-run. | OK |
| B-181 | V5:22 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-187 | OWNS:9 | n8n-skip-on-conflict.md:58 (20 of 20, new 1, duplicate 9) and :63 confirmed. | OK |
| B-190 | OWNS:14 | OWNS:14 quote present. | OK |
| B-193 | SKIP:65 | n8n-skip-on-conflict.md:65 and table row :47 confirmed. | OK |
| B-196 | PUB:4 | n8n-published-numbers.md:4 quote; :30 says NO MATCHING ROW. | OK |
| B-199 | PUB:21 | n8n-published-numbers.md:21 NOT REPRODUCED (1 of 5). | OK |
| B-202 | ONS:11 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-203 | ONS:12 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-205 | ONS:22 | Quoted words found in the cited line(s); table says no file traces it, none found. | OK |
| B-207 | ONS:23 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-208 | ONS:41 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-211 | ONS:95 | Quoted words found in the cited line(s); table says no file traces it, none found. | OK |
| B-218 | ONS:127 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-219 | ONS:131 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-220 | ONS:131 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
| B-221 | ONS:153 | ONS:153 quote matches; source evidence-int-6 not in checkout (as stated). | OK |
| B-224 | ONS:166 | Quoted words found in the cited line(s); trace statement matches the parsed flow/code. | OK |
