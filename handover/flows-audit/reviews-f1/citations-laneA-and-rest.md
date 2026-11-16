# Citation check, lane A (all 97 rows) and the lane B rows not yet checked (103 rows)

Checker: static, read-only. The table was copied to the scratchpad first (CT-snap.md); CLAIMS-TABLE.md was not edited and nothing was committed. Nothing was run (no n8n, no tests, no Postgres, no HubSpot).

## Result first
- Rows checked: all 97 lane A rows (A-001 to A-098; A-056 is unused) and the 103 rows that citations-laneB.md did not cover (99 lane B rows plus X-1 to X-4; this includes B-051, B-054, B-108, B-182 and B-213 to B-216, which that report left to earlier reviewers). Together 200 rows.
- OK: 198. WRONG: 2 (A-097 trace swaps the two table-screen READMEs; A-068 cite is one line off). ABSENT: 0 (every cited file and line exists; no cited line is past the end of its file).
- Method for every row: (1) took the quoted words out of the row, removed table-cell joins and "..." gaps, and compared them with the cited line(s) of the real file (automatic, after whitespace and backtick cleaning). Rows that do not match word for word were then read by hand; all mismatches turned out to be quote formatting (a quote that joins several table cells with " / ", brackets, single versus double quotes, a dropped parenthesis), except where listed under Failures. (2) For every trace statement that names a node, SQL text, setting, file line or number I parsed the flow JSON (n8n-flows-real-v5, n8n-flows-film-v5, n8n-flows, n8n-flows-v4, real-v4, both table screens) and read the named lines of mf.py, build_mainframe.py, smtp_catcher.py, crm_stub.py, stage_server.py, PAGE-STATEMENTS-V4.md, VIDEO-RUNSHEET.md, V7-NUMBERS-lead-read.md, RUN-ON-LAPTOP.md, PLAN-4, the READMEs and the probe files.
- Not checked: relayed raw numbers (raw files absent; only those that V7-NUMBERS-lead-read.md or the probe files carry were compared), what n8n, HubSpot or a mail server really does, whether PASS lines are true, the verdict judgments beyond what the lines show, and (for the desk repo, Finding 3) the content of run_real_check.py beyond the lines named below.

## Findings (read these)

1. A-097 is WRONG in its trace column. It says "the v2 README says NOT run; the v1 README says it was run live and works (F-023)". The files say the opposite way round: n8n-table-screen/README.md (v1) line 3 says "Status: NOT RUN ... was never executed" and line 22 "Never executed". n8n-table-screen-v2/README.md line 3 says "Version 1 ... was run live on n8n 2.46.6 and works" and "built, sample rendered with node, NOT run in n8n" for v2. FINDINGS F-023 states it correctly. Verdict OVERSTATED and the safe wording are unaffected; fix the trace sentence.
2. A-068 cite P:93 is off by one: the words "Alerts: 0 each" are on P:94.
3. The "desk repository is absent" statements in the table (A-004, B-014, B-016, B-017, B-019, B-020, B-038, B-064 to B-069, B-088 to B-092, B-158, B-215 and the Start-here text) are true for the hadavin-sdk checkout only. A copy of the public desk repo (head f3c39cf, the same sha RERUN-RUNBOOK.md:115 names) is on this machine at /home/user/duplicate-proof-lead-desk-n8n, with scripts/run_real_check.py (1113 lines), src/lead_desk/imap_count.py (228), crm_hubspot.py (509), live_claude.py (544), load_tools/. Consequences, each read in those files: (a) B-067 (hadavin_lead_id, prefix "L"), B-069 (prints worst case, asks y/N), B-088, B-090, B-091 (exit codes 1/2/3 and --cleanup archive) can be traced there and are currently marked UNTRACED; (b) the PLAN-4 line cites "run_real_check.py 2292-2298, 870-880, 761-833" do not fit that 1113-line file, and the names `ask_yes`, `probe_mailbox`, `probe_hubspot`, `refuse_tls_environment`, `parse_end_utc`, `utc_now`, `wait_for_enter_or_flag`, `refuse_names`, `check_formats`, `check_clock_and_dates` are not in it, so PLAN-4 was written against another code version (not here); (c) AGENT-SCOPE-DO-AND-DONT.md:20 cites `crm_hubspot.py:504-509` for the DELETE call; in this copy the DELETE is in `HubspotCrm.archive` at 492-500 and 504-509 is `make_crm`. I did not change any verdict; the lead decides whether to re-trace those rows against this copy. The n8n take scripts (qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh), WP6-RUNBOOK.md, review-codebase-1.md and end.flag are absent from the whole machine (find over /).
4. Every other claim in the sampled 200 rows holds against the real files: the 45 s lease (one per mf-form, mf-hook, mf-recovery in each v5 folder), 720 s alert window, backoff `60 seconds * LEAST(alert_attempts, 5)`, saving "none" in all 8 files, no errorWorkflow, no Slack, no KeyOk, six-column v2 table screen versus seven-column v1, MailClaim before SendMail, MarkUnknownA/B and MarkFailed SQL, CrmIdOk regex and its links, mf.py K3B/K3 definitions, smtp_catcher `.drop` and `.rcptfail`, crm_stub `fail_status` and `upsert_answer`, and the V7 numbers where V7-NUMBERS-lead-read.md carries them.
5. Already-known failures from citations-laneB.md (B-107, B-155 real-v5 CrmUpsert has no timeout option and maxTries 2; B-114 129 vs 130 rows; B-184 "coordinator's" vs "lead's") are not repeated; I re-saw the real-v5 CrmUpsert (HubSpot node, `options: {}`, maxTries 2) while checking A-001, B-145 and agree with that report.


## Failures

| id | cite | what the file really says | OK/WRONG/ABSENT |
|---|---|---|---|
| A-068 | P:93 (statement 12) | Cite P:93 holds statement 12 (59.6 s K1, 59.4 s K2, n=20). The quoted tail "Alerts: 0 each" is on P:94 (the "Detail:" line); the Tag line is P:95. Numbers and claim are right; cite should read P:93-94. | WRONG (cite off by one line) |
| A-097 | R:88 (and R:39) | Trace swaps the two READMEs. n8n-table-screen/README.md:3 (v1) says "NOT RUN ... never executed" (line 22 too). It is n8n-table-screen-v2/README.md:3 that says "Version 1 ... was run live on n8n 2.46.6 and works" and "v2 ... NOT run in n8n". The verdict OVERSTATED and the safe wording stand; only the trace sentence "the v1 README says it was run live" is false (FINDINGS F-023 has it right). | WRONG |

## Lane A, all other rows

| id | cite | what the file really says | OK/WRONG/ABSENT |
|---|---|---|---|
| A-001 | R:4 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-002 | R:4 | R:4 has the words in double quotes ("a lead sent twice with the same id is processed once"); table shows single quotes. FORM Claim `ON CONFLICT (lead_key) DO NOTHING`, Claimed -> Stored -> ReplyStored confirmed in both v5 folders. | OK |
| A-003 | R:5 and R:13 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-004 | R:13 | stage_server.py:11 `from lead_desk.live_claude import LiveQualifier` and :16 `Q = LiveQualifier(config._live_from_env(os.environ))` confirmed. Caveat: the desk repo main IS on this machine (see Finding 3) and has live_claude.py, so "the desk code is absent" is true only for this checkout. | OK |
| A-005 | R:8 | film SendMail toEmail intake@example.test; film AlertSend alerts@example.test; real-v5 SendMail INTAKE_ADDRESS_PLACEHOLDER and AlertSend $env.DESK_ALERT_TO. Confirmed. | OK |
| A-006 | R:14 and R:22 and R:85 | `interval '45 seconds'` count 1 in mf-form, mf-hook, mf-recovery in both v5 folders, 0 in the sub flow; n8n-flows 120 (1 each in 3 files); n8n-flows-v4 120. | OK |
| A-007 | R:30 | All 8 v5 JSON files: saveDataSuccessExecution none, saveDataErrorExecution none; errorWorkflow 0 hits. | OK |
| A-008 | R:30 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-009 | R:30 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-010 | R:30, R:39, R:52 | Quote found at the cited line(s). The proving file or node is not in the checkout (re-searched). | OK |
| A-011 | R:31 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-012 | R:31 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-013 | R:32 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-014 | R:32 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-015 | R:32 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-016 | R:32 | mf.py:119 `def m0()` and :138 `summarize("M1", "3 bursts of 10 identical requests ...")` confirmed. | OK |
| A-017 | R:33 (file as it stands) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-018 | R:33 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-019 | R:90 (FINAL caption) | P:161 and R:90 quote "60.1 to 61.9 s", "18 kill runs"; P:151-153 give n=5+5+5+3 = 18; K3B (5) and K3 (3) end unknown, so 8 of 18 are not "done". Raw HB194 absent. | OK |
| A-020 | R:33, R:90, R:41 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-021 | R:90 | mf.py:158 K3B "mail NOT yet delivered", mf.py:164 K3 "mail was delivered"; V7-NUMBERS lines 8 (K3) and 9 (K3B); RUN-ON-LAPTOP.md:67 and P:150/P:153 confirmed. | OK |
| A-022 | R:24 vs P:20 and P:150 | R:24 "Lane3 K3 = killed after the CRM write" and P:20/P:150 "lane3 K3 = this page's K3B" both present; the two do conflict as the row says. | OK |
| A-023 | R:90 and R:82 and P:134 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-024 | R:34 | CrmUpsert error output -> OutStage; CrmIdOk false -> OutStage; MailClaim only after OwnsClaim1 after CrmIdOk; MarkFailed CASE; AlertSend text "could not be finished after 3 tries. A person decides."; crm_stub.py:22 fail_status. All confirmed. | OK |
| A-025 | R:34 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-026 | R:86 (approved caption) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-027 | R:34 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-028 | R:34 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-029 | R:35 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-030 | R:35 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-031 | R:36 | smtp_catcher.py:40 stores the mail, :44-47 `if drop > 0: ... return` with no "250 queued". Confirmed. | OK |
| A-032 | R:36 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-033 | R:36 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-034 | R:37 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-035 | R:37 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-036 | R:38 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-037 | R:38 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-038 | R:38 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-039 | R:38 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-040 | R:39 | mf-table-screen-v2.json ReadLeads selects 6 columns (lead_key, state, attempts, mail_sent, alert_sent, updated_at); v1 mf-table-screen.json selects 7 (adds alert_attempts). Confirmed. | OK |
| A-041 | R:50 | Same check as A-040: v2 has no alert_attempts, v1 has it. | OK |
| A-042 | R:62 | Same check as A-040. | OK |
| A-043 | R:39 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-044 | R:39 | MailClaim sets mail_sent=true before SendMail (links MailClaim -> MailRowBack -> SendMail). Confirmed. | OK |
| A-045 | R:39 and R:52 | Quote found at the cited line(s). The proving file or node is not in the checkout (re-searched). | OK |
| A-046 | R:40 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-047 | R:40 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-048 | R:40 and R:59 | R:40 "A second channel: there is none." and R:59 item 10 "...the Slack alert are NOT BUILT" both present. Slack: 0 hits in all 8 v5 JSON files; AlertSend and SendMail both emailSend, credential mf-mail-smtp. | OK |
| A-049 | R:41 line 1 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-050 | R:41 line 2 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-051 | R:41 line 3 (file as it stands) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-052 | R:41 line 4 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-053 | R:41 line 5 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-054 | R:82 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-055 | R:57 | real-v4/mf-recovery.json:26, real-v5/mf-recovery.json:26 and real-v4/mf-form.json:97 all hold `interval '45 seconds'`; DESIGN-A-README.md:10 says "built with lease 120 (older copy ...)". Confirmed. | OK |
| A-057 | P:33 (statement 1) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-058 | P:38 (statement 2) | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-059 | P:44 (statement 3) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-060 | P:49 (statement 4) | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-061 | P:54 (statement 5) | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-062 | P:59 (statement 6) | Every30s scheduleTrigger secondsInterval 30; links to MarkFailed, ClaimStuck, AlertClaim in that order. Confirmed. | OK |
| A-063 | P:65 (statement 7) | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-064 | P:73 (statement 8) | Quote found at the cited line(s). The proving file or node is not in the checkout (re-searched). | OK |
| A-065 | P:78 (statement 9) | AlertClaim 720 s and AlertBackoff `60 seconds * LEAST(alert_attempts, 5)` on AlertSend output 1 (AlertMark on output 0) confirmed in both v5 folders. | OK |
| A-066 | P:83 (statement 10) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-067 | P:88 (statement 11) | No `alert_attempts <` test in AlertClaim (0 hits); AlertSend and SendMail both use credential mf-mail-smtp. | OK |
| A-069 | P:100 (statement 13) | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-070 | P:105 (statement 14) | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-071 | P:110 (statement 15) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-072 | P:115 (statement 16) | Quote found at the cited line(s). The proving file or node is not in the checkout (re-searched). | OK |
| A-073 | P:120 (statement 17, file as it stands) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-074 | P:125 (statement 18) | Quote found at the cited line(s). The proving file or node is not in the checkout (re-searched). | OK |
| A-075 | P:134 (statement 19) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-076 | P:149 (statement 20) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-077 | P:150 and P:153 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-078 | P:153 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-079 | P:154 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-080 | P:155 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-081 | P:159 and P:161 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-082 | P:11 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-083 | P:130-131 | P:130 "Total: 18 statements." while numbered statements run 1 to 20 (P:149 is 20). Claim confirmed. | OK |
| A-084 | R:30 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-085 | P:151 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-086 | P:152 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-087 | R:23 (last sentence) and R:33 (time cell) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-088 | P:156 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-089 | R:39 | AlertMark SQL `SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false` does not touch state. Confirmed. | OK |
| A-090 | R:40 | smtp_catcher.py:26-28 `.rcptfail` "N/text", answers "451 try later" to the next N matching recipients, nothing stored. Confirmed. | OK |
| A-091 | R:41 line 6 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-092 | R:87 item (5) | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-093 | P:51 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-094 | P:56 | Quote found at the cited line(s). Trace names a mechanism that matches the v5 JSON; the figure itself is relayed (raw files absent). Where V7-NUMBERS-lead-read.md carries it, the figure matches (lines 4-12). | OK |
| A-095 | P:111 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |
| A-096 | R:31 | mf-form.json Item sets lead_key = $json.body.submission_id; Valid tests only e-mail shape; Claimed tests notEmpty; no L+16-hex check anywhere in the flows. Confirmed. | OK |
| A-098 | P:134 | Quote found at the cited line(s). Trace statements about nodes, SQL, mf.py, smtp_catcher.py, crm_stub.py and the cited P/R lines checked against the files: match. | OK |

## Lane B rows not covered by citations-laneB.md, and X-1 to X-4

| id | cite | what the file really says | OK/WRONG/ABSENT |
|---|---|---|---|
| B-002 | PLAN:9 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-010 | PLAN:37 | Quote found at the cited line(s). Trace statements checked against the v5 JSON and named files: match. | OK |
| B-011 | PLAN:38 | Quote found at the cited line(s). Trace statements checked against the v5 JSON and named files: match. | OK |
| B-013 | PLAN:39 | PLAN:39 found; V7-NUMBERS rows K1,K2,K3,K3B n=20 each (80 kills), lost 0, doubled 0. Confirmed. | OK |
| B-014 | PLAN:40 | Quote joins table cells; every word is on PLAN:40. Trace confirmed: stage_server.py journal 17-23 and 48-58, `Q.qualify` at :54, loopback bind at :60, no window or spend check of its own. | OK |
| B-016 | PLAN:42 | Quote joins table cells. `imap_count.py` is NOT absent on this machine: desk repo main has src/lead_desk/imap_count.py (228 lines; plan cite 120-189 fits). Not read for "subject mode, exact compare"; the trace "imap_count.py absent" is true only for this checkout. | OK |
| B-017 | PLAN:43 | Quote found (PLAN:43). CAVEAT: desk repo main (head f3c39cf) is on this machine at /home/user/duplicate-proof-lead-desk-n8n (see Finding 3). `HubspotCrm.rows_with_prefix` exists (src/lead_desk/crm_hubspot.py:451) and `archive_all` exists (scripts/run_real_check.py:572), but the PLAN cite "run_real_check.py 2292-2298, 870-880" cannot fit: that file has 1113 lines. So the "none" in the trace column is not strictly true. | OK |
| B-019 | PLAN:45 | Quote found (PLAN:45). In the desk repo main on this machine `mask_result` (run_real_check.py:270), `scrub` (:286), `imap_settings`, `archive_all`, `merge_counts`, `load_env`, `EXIT_*` exist; `ask_yes`, `probe_mailbox`, `probe_hubspot`, `refuse_tls_environment`, `parse_end_utc`, `utc_now` do NOT (grep over src, scripts, load_tools). The plan was written against a different code version; still UNTRACED for those names. | OK |
| B-020 | PLAN:46 | Quote found (PLAN:46). `refuse_names`, `check_formats`, `check_clock_and_dates`, `wait_for_enter_or_flag` not in desk repo main on this machine; `send_with_retries` is in load_tools/load_driver.py (confirms the plan). Stays UNTRACED for the first four. | OK |
| B-022 | PLAN:48 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-023 | PLAN:49 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-025 | PLAN:53 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-029 | PLAN:57 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-031 | PLAN:57 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-032 | PLAN:57 | Quote found at the cited line(s). Trace statements checked against the v5 JSON and named files: match. | OK |
| B-034 | PLAN:57 | PLAN:57 found; V7-NUMBERS K1 max 59.6 s at lease 20 s. Confirmed. | OK |
| B-035 | PLAN:57 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-037 | PLAN:57 | Quote found at the cited line(s). Trace statements checked against the v5 JSON and named files: match. | OK |
| B-038 | PLAN:66 | Quote found (PLAN:66). Flow subject `'[demo] lead ' + lead_key` confirmed. `imap_count.py` exists in desk repo main on this machine but has no SUBJECT_TOKEN_PREFIX (plan says WP2 adds it), so "module absent" is true only for this checkout. | OK |
| B-040 | PLAN:68 | Quote found (PLAN:68). mf_leads.sql (n8n-flows) has no alert columns (ends at updated_at); mf.py:45-47 creates the table with alert_sent, alert_token, alert_until, alert_attempts. Confirmed. | OK |
| B-041 | PLAN:77 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-044 | PLAN:78 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-046 | PLAN:79 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-049 | PLAN:80 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-051 | PLAN:112 | Quote found at the cited line(s). Trace statements checked against the v5 JSON and named files: match. | OK |
| B-054 | PLAN:122 | V5-README.md:17 "No stack here: T17, T18, M1 and K1 on v5 have NOT been run." confirmed. T1 on film-v5 not mentioned in V5-README; no T1 result file in the checkout. | OK |
| B-058 | PLAN:137 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-064 | WATCH:5 | Quote found (WATCH:5). run_real_check.py exists on this machine, not read for "never prints a key/e-mail/text" (not checked). | OK |
| B-066 | WATCH:9 | Quote found (WATCH:9). Same as B-064: not checked against run_real_check.py. | OK |
| B-067 | WATCH:10 | Quote found (WATCH:10). run_real_check.py in desk repo main on this machine: `crm.rows_with_prefix("L")` at :993; crm_hubspot.py:88 LEAD_ID_PROPERTY = "hadavin_lead_id". So the claim can be traced there (text-only); the table calls it UNTRACED ("script absent"). | OK |
| B-069 | WATCH:14 | Quote found (WATCH:14). run_real_check.py docstring lines 34-35: "first prints the worst case of calls, mails and dollars and asks y/N". Traceable on this machine; table says UNTRACED. | OK |
| B-076 | DOUBTFUL:11 | Quote found at the cited line(s). Trace statements checked against the v5 JSON and named files: match. | OK |
| B-081 | DOUBTFUL:12 | DOUBTFUL:12 found; V7-NUMBERS K3 28.5/29.45/30.5 s and K3B 28.4/29.45/31.0 s, n=20, unknown 20, 1 alert each. Confirmed. | OK |
| B-085 | DOUBTFUL:13 | Quote found at the cited line(s). Trace statements checked against the v5 JSON and named files: match. | OK |
| B-087 | DOUBTFUL:13 | DOUBTFUL:13 found; V7-NUMBERS line 4 AF1 n=1, 1 alert. Confirmed. | OK |
| B-088 | FAILED:6 | Quote found (FAILED:6). In desk repo main run_real_check.py:96 `EXIT_REFUSED, EXIT_STOPPED, EXIT_FAILED = 2, 1, 3`; y/N question at the start. Exit 1 = stopped is confirmed there. | OK |
| B-090 | FAILED:8 | Quote found (FAILED:8). EXIT_FAILED = 3 (run_real_check.py:96); returned at :569 and :1109. Confirmed on this machine. | OK |
| B-091 | FAILED:9 | Quote found (FAILED:9). `--cleanup` argument at run_real_check.py:817, clean-up at :1101, `archive_all` :572; only contacts matching this run's lead ids (`lid in lead_ids`, :993). Confirmed on this machine. | OK |
| B-093 | FAILED:16 | Quote found (FAILED:16). PLAN:46 does name `wait_for_enter_or_flag` with `end.flag`. `end.flag` not found in desk repo main. UNSUPPORTED verdict stands (the planned file is absent, the plan explains the flag). | OK |
| B-094 | FAILED:17 | Quote found (FAILED:17). PLAN:114 ("12. `--retire-check <take config>`") and PLAN:154 ("7. run_real_check_n8n.py --retire-check ...") confirmed. | OK |
| B-097 | RUN:22 | RUN:22 quote found; run_chain.py:18-19 copy package.json, package-lock.json and node_modules into the work folder (confirmed). "removes it afterwards" and the harness refusal not checked (harness absent). | OK |
| B-099 | RUN:27 | RUN:27 found; CrmUpsert error -> OutStage and MarkFailed/AlertClaim confirmed; raw numbers relayed. | OK |
| B-100 | RUN:38 | RUN:38 found; n8n-flows/mf-form.json, mf-hook, mf-recovery each have one `interval '120 seconds'`; v5 folders 45. Confirmed. | OK |
| B-102 | RUN:63 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-105 | RUN:66 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-106 | RUN:67-68 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-108 | RUN:82 | RUN:82 found; mf.py:45-47 inline CREATE TABLE has alert_sent, alert_token, alert_until, alert_attempts (four columns). Confirmed. | OK |
| B-109 | RERUN:5 | RERUN:5 found; N8N-ENV-PROBE.md confirms Python 3.13.18, 16 GB, Docker 29.9.2 no daemon (lines 13, 22, 40). Relay is traceable to the probe file. | OK |
| B-110 | RERUN:25 | RERUN:25 found; N8N-ENV-PROBE.md:6 "engines node >=24.0.0 ... default Node is v22.23.4" confirmed. | OK |
| B-112 | RERUN:62 | RERUN:62 found; N8N-ENV-PROBE.md:8 and :225 "Could not initialize the vm expression engine" confirmed. | OK |
| B-113 | RERUN:81 | RERUN:81 found; N8N-ENV-PROBE.md:236-241 readiness 000,000,503,503,200 at t=0,2,4,6,8 s and port 5780 LISTEN from 4 s. Confirmed (Postgres 2 s part not checked). | OK |
| B-115 | RERUN:115 | RERUN:115 found; head f3c39cf equals the HEAD of the desk repo on this machine (git log). N8N-RERUN-1.md:2 also names f3c39cf. "5 passed in 8 s" not re-run. | OK |
| B-116 | CM:5 | CM:5 found; CLEAN-MACHINE-1.md:5 "13 of 13 documented Linux steps rc 0". Confirmed. | OK |
| B-118 | CM:9 | CM:9 found; clean-machine/B-suite.md:37 "3879 passed, 4 skipped, 0 failed = 3883"; 26 + 4 = 30 failures without gitleaks (CM:9). Confirmed. | OK |
| B-119 | CM:14 | CM:14 found; C2-e2e/CM text "Final received 4, new 2, duplicate 2" present. Confirmed. | OK |
| B-125 | START:23-26 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-130 | START:30 | START:30 found; V7-NUMBERS-lead-read.md shows V7 and AF1 results, so "not yet" is out of date. Confirmed. | OK |
| B-131 | START:33 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-134 | START:36 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-136 | START:40 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-137 | START:41 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-139 | START:44 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-140 | START:45 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-145 | DESIGN:15 | DESIGN:15 found; n8n-flows/mf-sub-crm-mail.json has maxTries 3 twice, timeouts 15000; real-v5/film-v5 Qualify maxTries 2, timeout 10000 default. Confirmed. (Same real-v5 CrmUpsert caveat as B-107/B-155: HubSpot node has no timeout option, maxTries 2.) | OK |
| B-151 | DESIGN:15 | DESIGN:15 found; SetCrmId, MailClaim, MarkDone, MarkUnknownA/B all test claim_token; Qualify and CrmUpsert run before any token check (links). Confirmed. | OK |
| B-154 | DESIGN:17 | DESIGN:17 found; film constants intake@example.test and alerts@example.test; real-v5 SendMail INTAKE_ADDRESS_PLACEHOLDER, AlertSend toEmail `$env.DESK_ALERT_TO`. Confirmed. | OK |
| B-157 | DESIGN:23 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-158 | DESIGN:28 | DESIGN:28 found; stage_server.py:11 imports LiveQualifier, :16 builds it; SpendLedger is not imported in stage_server.py (grep). Confirmed. | OK |
| B-169 | DESIGN:44-45 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-172 | V5:4 | V5:4 found; links CrmIdOk -> OwnsClaim1 (output 0) and OutStage (output 1) in both v5 folders. Confirmed. | OK |
| B-173 | V5:4 | V5:4 found; OutStage -> row stays processing -> ClaimStuck (attempts < 3) -> MarkFailed -> AlertClaim. Confirmed in links and SQL. | OK |
| B-182 | OWNS:4 | OWNS:4 found; no "ten-at-once trigger" node in any flow (the flows have Receive webhook only). Confirmed. | OK |
| B-183 | OWNS:5 | OWNS:5 found; `approval` 0 hits in real-v5 JSON. Confirmed. | OK |
| B-185 | OWNS:6-7 | OWNS:6-7 found ("12 of 20", "published 18 of 20", "2 of 5"). Confirmed. | OK |
| B-186 | OWNS:8, :10 | OWNS:8 and :10 found ("20 of 20", "25 of 25", "1 of 50"). Confirmed. | OK |
| B-188 | OWNS:12 | OWNS:12 found (4 s Wait, 5 of 5 kills lost the lead). Raw runs absent. | OK |
| B-189 | OWNS:26-29 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-191 | SKIP:7 | SKIP:7 found; build_mainframe.py:84 `iff("Claimed", ... "notEmpty" ...)` and BM:114 comment confirmed. | OK |
| B-192 | SKIP:63 | SKIP:63 found; n8n-flows/mf_leads.sql:4 `lead_key text PRIMARY KEY` confirmed. | OK |
| B-194 | SKIP:19 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-195 | PUB:3 | PUB:3 found; also says "builder rerun showed 10 of 20". Confirmed. | OK |
| B-197 | PUB:5 | PUB:5 found "kill runs with no effect: 1 of 15". Confirmed. | OK |
| B-198 | PUB:6 | PUB:6 found "4 of 10 (builder rerun 1 of 10)". Confirmed. | OK |
| B-200 | PUB:22 | PUB:22 found: "9 of 10" published, "R2 3 of 10" NOT REPRODUCED. Confirmed (quote joins table cells). | OK |
| B-201 | PUB:15-20, :23-27, :29 | PUB lines 15-20, 23-27, 29 contain b, c, d "20 of 20", "0 of 20 each", kill rows "0 of 15", variant e "(1,1) x5", "10 of 10", "0 of 15". Confirmed. | OK |
| B-204 | ONS:12 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-206 | ONS:23 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-209 | ONS:52 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-210 | ONS:95 | ONS:95 found (quote joins pieces of one line). Take script absent. | OK |
| B-212 | ONS:96-97 | ONS:96-97 found (under 2 seconds, take id once, marker path). Take script absent. | OK |
| B-213 | ONS:99 | Quote found at the cited line(s). Trace statements checked against the v5 JSON and named files: match. | OK |
| B-214 | ONS:103 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-215 | ONS:103, :112 | Quote found (ONS:103, :112). AGENT-SCOPE:20 says the code does a DELETE call at `crm_hubspot.py:504-509`; desk repo main on this machine has `HubspotCrm.archive` doing HTTP DELETE at crm_hubspot.py:492-500 (lines 504-509 there are `make_crm`). So the cite is for a different version, and "crm_hubspot.py (absent)" in the trace is true only for this checkout. Table verdict UNTRACED still reasonable for the take script. | OK |
| B-216 | ONS:108 | ONS:108 found; flow constants example.test (film), placeholders (real). Confirmed. | OK |
| B-217 | ONS:125 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-222 | ONS:154-156 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-223 | ONS:157-158 | Quote found at the cited line(s). Relayed figure; raw file absent, so only the text could be checked. | OK |
| B-225 | ONS:170-172 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| B-226 | ONS:176 | Quote found at the cited line(s). Named script/stage file absent from this checkout (find over / confirms for qualify_stage.py, run_real_check_n8n.py, n8n_drive.py, n8n_kill.py, n8n_start.sh, WP6-RUNBOOK.md, review-codebase-1.md, end.flag). | OK |
| X-1 | AGENT-SCOPE:6 | AGENT-SCOPE:6 found; AlertClaim has no attempts limit (0 hits for `alert_attempts <`), AlertSend body is lead id only (BM:109). Confirmed. | OK |
| X-2 | AGENT-SCOPE:7 | AGENT-SCOPE:7 found; ClaimStuck `attempts < 3` re-runs the same key. Confirmed. | OK |
| X-3 | AGENT-SCOPE:16 | AGENT-SCOPE:16 found (the quote splices two parts of line 16 with the words "(a 502 means ..." — present on the line). Qualify maxTries 2 confirmed in both v5 folders. | OK |
| X-4 | DECISION:16 | DECISION:16 found; mf_leads has updated_at only, no history table (mf_leads.sql, mf.py:45-47). Confirmed. | OK |