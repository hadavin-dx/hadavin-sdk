## HEARTBEAT 150 (11:22Z) - kill script: n8n imports and runs; first control run in progress; one defect found in the demo's table file

| Item | State at 11:22Z |
|---|---|
| Stack | Postgres 16 up (port 55432), 3 fakes up, n8n 2.46.6 under Node 24.22.3 starts and answers /healthz. Credentials and the four flows import with the n8n command line; the three entry/recovery flows publish. Fixed on the way: isolated-vm was built for Node 22 and refused Node 24 (rebuilt, now loads); n8n needs N8N_LISTEN_ADDRESS=127.0.0.1 (no IPv6 here); its task broker owns port 5679 so my port is 5690. |
| DEFECT FOUND (name: F-DDL, table file does not match the flows) | handover/demo/n8n-flows/mf_leads.sql (commit 59202078) has no column `label`, but mf-form (StoredState, SaveLabel) and mf-recovery (RSaveLabel) read and write `label`. On the pushed DDL every lead stops at the label step with: column "label" of relation "mf_leads" does not exist (7 errors in my first control run; the stage was then called 7 times for one lead, every 30 s, by recovery). My harness adds `label text` before each run so the test can go on; the demo session should add it to mf_leads.sql (tell me if its own run used a different table). |
| First control run (1 lead, no kill) | run c1 started again with the column added; result not in yet. No kill point has run. |
| Disk (your question) | df: 4.3 GB free of the allowance, 89% used. Biggest: kill-n8n 3.0 GB (n8n install), work/priv 9.2 GB (not mine to judge), 4 builder temp folders of about 0.4-0.5 GB each. Not near full; I will delete my own temp folders if free space goes under 2 GB. |

ASK for the lead: none blocking. FYI: F-DDL above affects the demo session's own numbers if it ran with that table file.
FAILURES AND RETRIES: (1) workflow import crashed "Could not initialize the vm expression engine": isolated-vm compiled for Node 22; rebuilt with node-gyp under Node 24: fixed. (2) n8n exit "address '::' is not available": fixed with N8N_LISTEN_ADDRESS. (3) n8n exit "Task Broker's port 5679 is already in use": my own port clash, moved to 5690. (4) first control run: F-DDL above (not a flake: missing column).
NOT DONE / NOT CHECKED: no kill point, no fault mode and no result yet; the SMTP catcher against n8n's SMTP node untested until c1 passes; run results are not compared with anything yet (by order, I compare only after my numbers are saved).
WHAT I WOULD DO NEXT (ranked): 1) read c1 result, fix catcher issues; 2) controls (same lead twice, two at once, bad e-mail); 3) K1, K2, K3, K6 three runs each; 4) F-a, F-b, F-c; 5) save numbers, then compare.

## HEARTBEAT 149 (11:12Z) - kill script: v2 flows copied, PLAN written, fakes written, n8n 2.46.6 runs (needs Node 24)

| Item | State at 11:12Z |
|---|---|
| Flows | NEW Design A v2 (commit 59202078, 11:05Z) copied: mf-sub-crm-mail, mf-form, mf-hook, mf-recovery, mf_leads.sql, DESIGN-A-README.md (read: the README says "no results, no numbers"). The 10:45Z six files are not used. Independence line kept: I read ~40 lines of a different workflow's counts earlier; no other demo result file opened, no numbers used |
| kill/PLAN.md | written and pushed BEFORE any run (8ad6ec4c): kill points K1 stage in flight, K2 CRM stored but not answered, K3 after mail_sent before mail stored, K6 mail stored before state done; faults; counting; my predictions from the README text |
| kill/fakes.py | written (CRM upsert/search/create with ack-delay and blind-search faults; stage qualify with journal and delay; SMTP catcher with pre-greeting delay, store-then-drop, ack delay; events.jsonl fsynced for the driver). Compiles; not yet run |
| Environment | Postgres 16 scratch cluster initialised (not started yet). n8n 2.46.6 installed but refuses Node 22 ("needs >=24"): I fetched Node 24.22.3 from the npm registry (package node@24, no root change) and n8n --help runs with it |
| Not asked of you | T1-T3 and T6 definitions: still my own labels K1-K6 (ASK in HB148 stands, not blocking) |

ASK for the lead: none new.
FAILURES AND RETRIES: first n8n run with Node 22 refused ("Node.js version 22.23.4 is currently not supported"): fixed with Node 24 from npm; not a flake.
NOT DONE / NOT CHECKED: nothing has run end to end yet; credentials import and workflow publish via CLI untested.
WHAT I WOULD DO NEXT (ranked): 1) start Postgres + fakes, import credentials and the five flows with n8n CLI into a fresh user folder, run the control (one lead); 2) write the driver (kill at event, restart, wait, count); 3) K1-K6 three runs each, then faults.

