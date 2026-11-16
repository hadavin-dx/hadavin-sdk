# citation-r11 (citation checker, read-only; nothing edited except this report)

Scope: every cite in FINDINGS.md (153 lines) and LEDGER-ROWS.md (46 lines, 45 rows). Targets: handover/demo/, handover/flows-audit/ (incl. inputs/), repo-root tools/. Copies under flows-audit/tools/scratch/ and snapshot folders were excluded. No fixer log was used. No secret seen or printed.

How I checked (what is and is not covered):
- Every `file:N`, `file:N-M`, `file line N` cite found by regex: 116 occurrences, about 75 distinct, each opened at the line and read. Every `BM:N` cite (build_mainframe.py, 22 distinct) opened as well.
- Every row id, finding id, order id, question id, GO row, FIX-PLAN item/step, TAKE-CHECKLIST check, RUNBOOK step, EXCEPTIONS/ROLES section name was looked up in its file.
- Lane ids (L1-, L2a-, L2b1-, L2b2-, L2b3-, L3-: 98 distinct rows): every id exists as a row in its lane file; for every FINDINGS row I read the lane row titles against the finding (mapping check, not a full re-read of each lane row).
- Every file name mentioned was tested for existence.
- Not done: cites that exist only inside lane/evidence files themselves (for example the BM/mf.py cites inside lanes/*.findings.md) are outside the brief.

## Counts
- MATCH: all other checked cites (about 190 incl. repeated mentions; about 75 distinct line cites, 22 BM cites, 98 lane ids, about 45 section/step/order/row cites)
- MISMATCH: 0
- SOFT MISMATCH: 3
- CANNOT-CHECK (target absent from this checkout): 2 groups (handover/demo3/kill/RESULTS.md:40-48; handover/ledger.md) plus the scripts the text itself says are absent (n8n_api.py, n8n_drive.py, run_real_check_n8n.py, qualify_stage.py, data/results.jsonl): these are stated as absent and are not cites to check
- NOT A CITE: 2 groups (`mf-recovery.json:2` and `mf-recovery.json:0` in F-008 are grep output examples, not line pointers)

## MISMATCH
None found. (The r10 mismatch "CLAIMS-TABLE.md row B-054 (line 559)" is fixed: F-046 and LEDGER-ROWS.md:46 now say "row B-054" with no line number. Row B-054 exists at CLAIMS-TABLE.md:717 (and summary row at :307). Target quote: "T1 (burst of 10) and K1 (n=5) re-run on film-v5: 0 lost, 0 doubled". MATCH.)

## SOFT MISMATCH
| where | cite | verdict | note |
|---|---|---|---|
| FINDINGS.md:63 (item 32) | `B-136 ('planted fake key in no file')` | SOFT MISMATCH | CLAIMS-TABLE.md:827 row B-136 reads "the planted fake model key and fake SMTP password in no file". The quoted words are a shortened form; meaning is the same, row id exists and the row is rated "SUPPORTED ONLY BY RELAYED NUMBER". |
| FINDINGS.md:130 (F-013) and its ledger row | "PLAN-4-NLITE-FROM-LEAD.md:79 says that is deliberate" | SOFT MISMATCH | Line 79 holds the behaviour ("started" written before the call; started with no label answers unknown; one in-process lock, "single flight"). The word "deliberate" is not there; the rule is stated as decided design, so the paraphrase is fair but not a quote. |
| FINDINGS.md:119 (F-028), source cell `L3-20` | lane row L3-20 listed under "Stale numbers and cross references" | SOFT MISMATCH | L3-20 (lanes/L3.findings.md:26) is about the alert claim window 720 s versus 120+30+600 = 750 s (build_mainframe.py:11 comment). It is a wrong number, so it loosely fits, but it is not a stale cross reference in the page statements or run sheet. Other F-028 ids (L3-15, L3-18, L3-19, L3-21, L3-22) fit. |

## CANNOT-CHECK
| where | cite | note |
|---|---|---|
| FINDINGS.md:63 (item 32) | `handover/demo3/kill/RESULTS.md:40-48` | Not in this checkout; the same sentence says "file not in this checkout". (demo/hang/RESULTS.md also has lines 40-48 but is a different file: wait-times table, not related.) Outside the checkout I saw an unrelated scratch copy that lists n8n write-ahead hits for name, e-mail and key in lines 40-48; I did not count that as a check. |
| FINDINGS.md:35 | `data/results.jsonl`, branch cloud/system-map | Other session's branch; absent here; text says so. |
| LEDGER-ROWS.md:1 | `handover/ledger.md` | "the real ledger is outside this folder"; absent. |

## Special attention items (all MATCH unless noted)
- F-046 (FINDINGS.md:153; LEDGER-ROWS.md:46): PLAN-4-NLITE-FROM-LEAD.md:122 "T1 (burst of 10) and K1 (n=5)..."; CLAIMS-TABLE.md row B-054 (id by name, no line number, exists at :307 and :717); ORDERS.md:32 "F-002 is a Blocker until T1 passes" (flows-audit/ORDERS.md; the demo/ORDERS.md line 32 is empty and not the target); N7-A4 and N7-A5 exist in lanes7/N7-verdicts.md:53-54; mf.py:358 id list referenced there exists as TESTS line. MATCH.
- F-002 (FINDINGS.md:109): build_mainframe.py:17 "def pg(name, q, repl, pos, always=True"; :82-83 Claim INSERT ... ON CONFLICT DO NOTHING RETURNING; :84 `iff("Claimed"...)`; :114 comment "returns ONE item {success: true}"; PLAN-4:47 resend rule (1 post + 3 resends); PLAN-4:66 and :77 key regex `^L[0-9a-f]{16}$` (bad_key); PLAN-4:94 post_lead tries=4. MATCH. Patch F-002-take-key-check-and-claim-error-path.patch exists.
- F-008 (FINDINGS.md:114): build_mainframe.py:44 `ST = {... "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none"...}` MATCH; N8N-START.md:15-27 ("## Execution saving: all four settings are REQUIRED") MATCH; DESIGN-A-README.md line 23 "Execution saving off for success and error runs" MATCH; `mf-recovery.json:2` / `:0` NOT A CITE.
- F-010 (FINDINGS.md:129): FIX-PLAN.md:135 "F-010 three database roles (plus n8n's own: four)" MATCH; ROLES-PROPOSAL.md section 3 "Proposed logins" ("Four flow logins plus one table-owner login") MATCH.
- F-011 (FINDINGS.md:115): N8N-START.md:4 "SQLite inside n8n ... Postgres 16 for the lead table (separate...)"; N8N-START.md:38 "What the scan test (T7b) showed"; lead decision item 10 (ORDERS.md:96 summary "(10) wording 'one Postgres server, two databases'") MATCH.
- CLAIMS-TABLE.md and RUNSHEET-WORDING.md: the only cites into them are row B-054 and row B-136 (both exist) plus a list of unread files at FINDINGS.md:58 (not a cite). No cite points at a RUNSHEET-WORDING rule or row, so nothing there can have drifted.

DESIGN-A-README.md line 23 (FINDINGS.md:114; LEDGER-ROWS.md:11): re-checked, MATCH. The long line 23 contains "Execution saving off for success and error runs in the w..." (as well as the N8N_BLOCK_ENV_ACCESS_IN_NODE text).

## Full table of line cites (target text, max 15 words)
| source | cite | verdict | target text |
|---|---|---|---|
| FINDINGS:60 | PLAN-4:106 | MATCH | "up to 3 HubSpot contacts archived at the end" |
| FINDINGS:66 | mf.py:119-138 (M0 :119, M1 :129) | MATCH | "def m0():" / "def m1():" |
| FINDINGS:71 | BM:51; mf.py:77-78; :339-357 (T17 :339-347, T18 :348-357) | MATCH | `pg("SetCrmId", ...)`; "def t17():" / "def t18():" |
| FINDINGS:72 | n8n-owns-vs-desk-owns.md line 12 | MATCH | 'n8n marked the run "crashed" after the restart and did not run it again' (double quotes in target) |
| FINDINGS:72 | BM:56-58, :103, :105 | MATCH | SendMail / MarkUnknownA; MarkFailed; AlertClaim SELECT ... state IN ('unknown','failed') |
| FINDINGS:70 | BM:3, :54, :56, :68-69, :82-83, :99, :26-30 | MATCH | "The insert IS the claim"; MailClaim; SendMail; links to OutStage; Claim INSERT; ClaimStuck; HubSpot upsert comment |
| FINDINGS:73-80 | BM:11, :12-14, :20-23, :25-30, :30, :50, :75, :77-95, :87, :97-100, :100, :102, :106, :110-111, :113, :116, :120-121 | MATCH | V4 comment 720 s; REAL/STAGE_ENV; def http retry; hubspot; call_sub; main_flow; Every30s; RunSub onError |
| FINDINGS:74,81,151 | CUT-LIST.md:18 | MATCH | "KEEP n8n-flows/desk-error-notifier.json: it is the only Er..." |
| FINDINGS:76 | VIDEO-RUNSHEET:39, :50 | MATCH | "Fallback (keep it): a plain picture of the rows taken in rehearsal" / "(a) a picture of the rows taken" |
| FINDINGS:76 | README v1 :3; v2 README :3, :49, :51 | MATCH | "Status: NOT RUN"; "NOT run in n8n" (lines 3 and 51 both contain it); "The page is public to anyone" (:49) |
| FINDINGS:82 | stage_server.py:3-5, :16, :48-52, :54; PLAN-4:40, :78 | MATCH | per-lead journal docstring; LiveQualifier; lock/journal; `Q.qualify(k, o.get("email", ""))` |
| FINDINGS:109 | PLAN-4:47, :77, :94; BM:17, :82-83, :114 | MATCH | see special attention |
| FINDINGS:110,111 | VIDEO-RUNSHEET:24, :33, :36, :90; PAGE-STATEMENTS:150, :153; mf.py:153, :158, :159, :164; REPORT:49 | MATCH | "Two different tests are both called K3"; "def k3b():"; "NAMING (lead, final)"; "K3B (n=5) and K3 (n=3)" |
| FINDINGS:112 | BM:105 | MATCH | AlertClaim SELECT |
| FINDINGS:113 | REPORT.md:695; dn1_common.py:16 | MATCH | "n8n 2.46.6 blocks environment variables in nodes by default"; `"N8N_BLOCK_ENV_ACCESS_IN_NODE": "false"` |
| FINDINGS:114 | BM:44; N8N-START:15-27; mf-recovery.json 2/0 | MATCH / NOT A CITE | see above |
| FINDINGS:115,118 | N8N-START:4; REPORT.md:622 | MATCH | "SQLite inside n8n"; "so they do NOT share one Postgres here" |
| FINDINGS:116 | ORDERS.md line 138; mf-recovery.json line 177 (real-v5) | MATCH | "4 DESK_ALERT_TO: set by the lead at take prep"; `"fromEmail": "FROM_ADDRESS_PLACEHOLDER"` |
| FINDINGS:119 | PAGE-STATEMENTS:130 | MATCH | "Total: 18 statements." (script check: numbered statements 20, Total line 18, as stated) |
| FINDINGS:120 | PAGE-STATEMENTS:120 vs :149-157 | MATCH | statement 17 "Recovery within 60 s was measured only at the 20 s test lease"; statement 20 at :149 |
| FINDINGS:121,122 | BM:109; VIDEO-RUNSHEET:38, :41; RUN-ON-LAPTOP:58 | MATCH | "A person decides." (in :38 and :41 and :58 "a person decides; 1 alert") |
| FINDINGS:123 | mf.py:44-47, :45 | MATCH | DROP TABLE / CREATE TABLE mf_leads with alert columns |
| FINDINGS:124 | VIDEO-RUNSHEET:35; smtp_catcher.py:40 before :44-47 | MATCH | "6. Doubtful case, step 1"; stores mail, then `.drop` fault at :44-47 |
| FINDINGS:125 | VIDEO-RUNSHEET:4, :11, :12, :34 | MATCH | "scenes 1 to 5"; "Scenes 1 to 4"; "Scene 5 (CRM refuses) needs a switch"; scene 5 row |
| FINDINGS:126 | n8n-table-screen/README:3; v2 README:3; DOUBTFUL-SCENE:13 | MATCH | "Status: NOT RUN"; "NOT run in n8n"; "5. The person shows the table row" |
| FINDINGS:127 | BM:27 | MATCH | "The node has NO timeout option" |
| FINDINGS:130 | stage_server.py:50, :51; PLAN-4:79 | MATCH / SOFT | `if j.get("label")` ; `if j.get("started")` |
| FINDINGS:136 | PLAN-4:64, :78; mf.py:12 | MATCH | `stage.journal`; "three idempotency layers"; `"stage-journal.jsonl"` |
| FINDINGS:146 | dn1_common.py:7, :59-61; mf.py:8; RUN-ON-LAPTOP:45; PLAN-4:47 | MATCH | `ROOT = os.environ.get("DN1_DESK_REPO"...)`; shutil.rmtree/os.remove loop; `from dn1_common import *` |
| FINDINGS:152 | stage_server.py:54; PLAN-4:76-79 | MATCH | `Q.qualify(k, o.get("email", ""))`; Behaviour/Concurrency lines |
| FINDINGS:153 | PLAN-4:122; ORDERS.md:32 | MATCH | "T1 (burst of 10) and K1 (n=5) re-run on film-v5"; "F-002 is a Blocker until T1 passes" |
| LEDGER-ROWS | every cite above repeated in rows F-002, F-003, F-004, F-007, F-008, F-011, F-013, F-018, F-020, F-023, F-031, F-037, F-041, F-042, F-044, F-046 | MATCH | same targets, same verdicts |

## Other checks done
- LEDGER-ROWS.md has 45 rows, ids equal the 45 FINDINGS ids (no extra, none missing); severity first word and status first word match FINDINGS for every row (script). F-040 is named only as "merged into F-014" and has no row of its own, as stated.
- Named files all exist (flows-audit/ and demo/), except those the text itself says are absent from this tree.
- Order ids ORDER 002, 003, 004, 007, 012, 013, 037 exist in flows-audit/ORDERS.md; ORDERS answer blocks 10:23Z (Q13), 10:58Z (Q14, Q17), 11:20Z (Q19, Q20), 11:25Z (Q21), 14:15Z (Q27), 14:35Z exist; Q27 item 9 (F-011 and F-041 take path, before Tue 14:00Z) and Q30 item 2 (F-031 and F-007 text fixes) match; QUESTIONS.md row Q20 says "line 138 (item 4)".
- FIX-PLAN items 1 to 9 and 8b exist; item 3 steps 5, 7, 9, 10, 10b, 14, 17 exist; TAKE-CHECKLIST checks 1, 3, 7, 13 and GO rows 4 to 7 exist with the content the cites assume; RUNBOOK step 18 and the section "One filled flow set, the real trial-account credential in every phase" exist (RUNBOOK.md:229); EXCEPTIONS.md section "One-database wording" exists (:13).
- tools/scan_repo.py exists at the repo root (`/home/user/hadavin-sdk/tools/scan_repo.py`), not under flows-audit/tools; the cite in FINDINGS.md:42 gives the relative path "tools/scan_repo.py", which is correct from the repo root.
