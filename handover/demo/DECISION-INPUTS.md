# DECISION-INPUTS (Design A decision rule): rows for the lead to fill. No judgement here, only: criterion, test, where the number will be, status, value.
Status words: NOT RUN (no raw file exists to me), MEASURED (a raw file exists AND the lead gave it to me; the value column then quotes it with its file name). The lead has not given me any raw file as of this writing, so the value column is empty in every row. All numbers will be: my flows or the film/real variants, one machine (laptop runner), made-up data, stand-ins, not independent.
Raw file path pattern (written by n8n-mainframe/run_chain.py, summarised by count_table.py): `raw-designA-laptop/<tag>-<TEST>-<time>/mf_result_<TEST>.json` (per-lead rows under `per_lead`, the pass text under `why`) and `.../driver.out`. The lead side folder name is the lead's; fix the prefix when the files are pushed.

| # | Criterion | Test(s) | Number to read (field) | Raw file (pattern) | Status | Value (only from a raw file the lead gave me) |
|---|---|---|---|---|---|---|
| 1 | 0 lost (per kill point, with sample size) | K1 K2 K3B K3 K4 K5, T10, T11, T13, T15 | `why` text: "sample N: lost X"; `per_lead[].lost` | .../mf_result_K1.json ... K5, T10, T11, T13, T15 | NOT RUN | |
| 2 | 0 doubled (CRM row, mail, model call, alert, per lead id) | same set + M1, T12 | `why`: "doubled X"; `per_lead[].doubled`; REC "sets" extras | same | NOT RUN | |
| 3 | UNKNOWN counted (how many, and how many had the mail delivered) | K3B K3 T10 T12 | `why`: "unknown X (mail delivered in Y of them)" | .../mf_result_K3B.json, K3, T10, T12 | NOT RUN (T12 passed earlier on my Linux machine, sample 5, block 11:01Z of REPORT.md; the raw file was not kept: disk) | |
| 4 | Recovery <= 60 s | K1 K2 K3B K3 K4 K5 (kill to final), T15 | `why`: "recovery reached a final state in min/median/max s after the kill"; `per_lead[].seconds_kill_to_final` | same | NOT RUN. Fact for reading it: time from kill to recovery start is up to the lease (the lease is counted from the claim) plus one 30 s tick; the tests use lease 20 s, the design flows 120 s, the film flows 45 s. With lease 120 a kill-to-final under 60 s is not possible by construction for a kill soon after the claim. Per-lease table requested (K1 K2 K3B K3 K4 at --lease 20, 45, 120). | |
| 5 | Model calls = 1 per lead id | every test | REC "money": model_calls_total, model_lead_ids, max_calls_per_lead_id; `money.ok` | every mf_result_*.json | NOT RUN | |
| 6 | Ledger rows = 1 per lead id | every test | REC "money": ledger_reserve_rows; `money.ok` | every mf_result_*.json | NOT RUN | |
| 7 | T8: cap stage refuses / errors / times out: fail closed (0 mails to intake, 0 CRM writes, 0 model calls, state failed, 1 alert per lead, SMTP connections = alerts) | T8 | `pass`, `why` | .../mf_result_T8.json | NOT RUN (V4 includes T8 per the lead; file not given to me) | |
| 8 | T9: no input field changes the recipient; no injected header | T9 | `pass`, `why`, REC rows per case | .../mf_result_T9.json | MEASURED earlier by me on one Linux machine (sample: 5 cases, block 10:53Z of REPORT.md); raw file not kept (disk). NOT RUN on the laptop. Known: a lead id with a line break and header text was ACCEPTED as a lead id (no harm); no pattern check yet. | |
| 9 | Take-side change <= 16 agent-hours | not a test | (nothing I measured) What the desk side needs, as I know it: ONE new endpoint, POST qualify (lead id in, label out, per-lead journal, unknown on a started-but-unanswered call); my stage_server.py (about 45 lines) is the prototype on top of the desk's own LiveQualifier and SpendLedger. I have no hours estimate. | n/a | NOT MEASURED (an estimate is the lead's) | |

## Related checks that sit next to the rule (not in your list; rows added so nothing is lost)
| # | Item | Test | Raw file (pattern) | Status | Value |
|---|---|---|---|---|---|
| 10 | Idle stack fires nothing (F-REC-EMPTY) | T14 | .../mf_result_T14.json | NOT RUN by me (laptop ran T14 old/fixed; counts not given to me) | |
| 11 | CRM refuses every call: failed + exactly 1 alert + 0 mails | T15 | .../mf_result_T15.json | NOT RUN by me (laptop queued) | |
| 12 | Planted secrets / lead data in n8n's files | T7b | .../mf_result_T7b.json (hits per file), REC after_stop_and_checkpoint (extended version) | first version: lead's relayed result only (name 3, e-mail 2 in the write-ahead file; key and SMTP password none); NOT given to me as a file | |
| 13 | Lease table per lease value | K1 K2 K3B K3 K4 at lease 20/45/120 | count_table.py output per run | NOT RUN | |
| 14 | Real-node flows | none possible without a HubSpot account and mailbox | n/a | BUILT, NOT RUN (n8n-flows-real/) | |

## V7 v3 values (update 16:40Z). Status = MEASURED-ON-LAPTOP: the lead read these from the laptop raw files (V7-NUMBERS-lead-read.md, runner abefbabd, v3 flows 6ebb7f62e, lease 20 s). I did NOT read the raw files. Independent harness = lane3 only.
| Row | Test | Value (n; lost / doubled / unknown) | Open |
|---|---|---|---|
| 1,2 | K1 | n=20; 0 / 0 / 0 | |
| 1,2 | K2 | n=20; 0 / 0 / 0 | |
| 1,2,3 | K3B | n=20; 0 / 0 / 20 (1 alert each, no intake mail) | |
| 1,2,3 | K3 | n=20; 0 / 0 / 20 (mail delivered, not re-mailed, 1 alert each) | |
| 1,2 | K4, K5 | not in the file: NOT RUN on v3 | |
| 3 | T10, T11, T13 | not in the file given to me: status unknown to me | ask the lead |
| 7 | T8 | n=3; pass true; failed, exactly 1 alert, 0 CRM writes, 0 model calls | |
| 11 | T15 | n=3; pass true; failed, alerts 1 each, 0 mails, 0 CRM rows, 91+ s to final | |
| 10 | T14 | pass true; all counts 0 over 120 s idle | |
| 4 | Recovery seconds | NOT READ (the lead says: see mf_result recovery seconds) | open |
| 13 | Lease 45/120 table | NOT RUN | open |
| 5,6 | model calls / ledger | the file shows model calls per lead 1 where a lead reached the model; ledger rows not in the file | open |
Known v3 flaw (lane3 B90, 3 of 3 runs): two alerts when the alert send outlasts the 60 s first claim. v4 in lane3 runs: B90 n=2, exactly 1 alert; v4 is not in the V7 file.
