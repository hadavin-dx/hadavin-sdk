# EVIDENCE RUNNER A1 (citations): raw record, no judgement

- Target sha (from brief): 35235ace26a516d932e73542c235875f390f333d (git archive of branch cloud/flows-audit; archive dir is not a git repo, sha not re-checked here)
- Date UTC: 2026-11-16 07:58
- sha256 FINDINGS.md: 44b507a4e6304f47afcf7fce6325b52791e225987ecc62eba487d7e7fa5506c0
- sha256 of other files read (relative to fa/handover):
  - demo/PLAN-4-NLITE-FROM-LEAD.md  4894f7dc67884645a0176dab32dce0aed89111f66dbd0e2d9e52e76a43be0790
  - demo/VIDEO-RUNSHEET.md  5eff2ed7d2838f2e3df70f0646ec727d7577c2f8425f748ea513cd10934eed40
  - demo/n8n-flows-film-v5/mf-form.json  74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
  - demo/n8n-flows-film-v5/mf-hook.json  305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
  - demo/n8n-flows-film-v5/mf-recovery.json  42d853ac8528c2699a3deac54725d6c4c2672258bf048e6fa88deb3783cb4c79
  - demo/n8n-flows-film-v5/mf-sub-crm-mail.json  a0215012962e2e22e3923ed9ecb14bae472e0857636b7356f61e87190968918b
  - demo/n8n-flows-real-v5/mf-form.json  74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
  - demo/n8n-flows-real-v5/mf-hook.json  305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
  - demo/n8n-flows-real-v5/mf-recovery.json  03c566bba549524b7bed0e787fdd46c4a01653450ef97691d14f4614357b0759
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json  b3277363ae04b365459d902e5b5be099f1957126e3d48dbe42c47332cf53ff36
  - demo/n8n-flows-v3/mf_leads.sql  91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
  - demo/n8n-flows-v4/mf_leads.sql  91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
  - demo/n8n-flows/N8N-START.md  178359bf5c474c1cc16fc7c5d2f36115cdd7aa8f7668e56ea14b06e3aba9989a
  - demo/n8n-flows/PAGE-STATEMENTS-V4.md  031554c115ed36b911622a873cc891c9ec833e89cfccd2505057af3bfbe5abb3
  - demo/n8n-flows/desk-form-door.json  e23f7cff7b30a6f24b79bf7cbb5124e401a6e28a86b385501f9139711db15776
  - demo/n8n-flows/desk-webhook-door.json  afecd6fd75af1b0ac7b74a1820ed09a59c36b5d05886ff81a488b13c492675b4
  - demo/n8n-flows/mf_leads.sql  7a18c922a1228d0f7517322cf00fd4be282d164cdaad2ce831ad33e7f92aa6ee
  - demo/n8n-mainframe/build_mainframe.py  2987ff2308c495cf1c7ee59ced59f1c4b119cbe1500cd0443f1825c934cbc50b
  - demo/n8n-mainframe/mf.py  d761734467347d4d022d6784ba55b781e6664bb47b38b59aec899421582a2339
  - demo/n8n-mainframe/stage_server.py  b8785e822e86126274f2389ceaf9a6a5e96a63a7ae87a214f268a6e0c23f566f
  - demo/n8n-table-screen-v2/README.md  f039140f88834e53c677ca9ba6a0459f680cc2f575302a403eb0dfa64d59bb97
  - demo/n8n-table-screen-v2/mf-table-screen-v2.json  f7ea97e308af1c6dcc98b59ab946352c1d47e2f3c760deac43a69999f6d8fbd1
  - demo/n8n-table-screen/README.md  41ffd14017aec93973ea4f99fc27bf7ef7e5739a609b15574abe6f6fe5d06461
  - demo/n8n-tests/smtp_catcher.py  40577941b10941640b0f92eda5dc3e460b79d807f80e78b7a6d9dd694e0e4eef

Notes: line numbers are 1-based in the archived files. 'probe' = a text quoted from the claim, searched at the cited place and in the whole file. Long lines are cut to 300 chars. Credential-like strings are masked by pattern.


## F-001
- CLAIM (row title, quoted): "One table definition: the file named for the current flows has no alert columns, so alerts silently never send."
- row cited-path cell (quoted): handover/demo/n8n-flows/mf_leads.sql; n8n-flows-real-v5/mf-recovery.json:AlertClaim; n8n-mainframe/mf.py:44-47
- Row claim detail (quoted): "n8n-flows/mf_leads.sql has 0 alert columns, n8n-flows-v3 and -v4 copies (byte-identical, checked with cmp by the lead) have them, the v5 folders ship no SQL, mf.py holds a fourth inline copy."
- CITE `n8n-flows/mf_leads.sql` whole file (15 lines), full text:
```
1: -- NOTE: this table matches the CURRENT flows (mf-*.json in this folder, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two s ...[+4 chars]
2: -- Design A lead table (Postgres). The insert is the claim. Created before the flows run.
3: CREATE TABLE mf_leads(
4:   lead_key      text PRIMARY KEY,
5:   email         text,
6:   name          text,
7:   state         text NOT NULL DEFAULT 'new' CHECK (state IN ('new','processing','done','review','unknown','failed')),
8:   claimed_until timestamptz,
9:   claim_token   text,
10:   attempts      int  NOT NULL DEFAULT 0,
11:   crm_id        text,
12:   mail_sent     boolean NOT NULL DEFAULT false,
13:   created_at    timestamptz NOT NULL DEFAULT now(),
14:   updated_at    timestamptz NOT NULL DEFAULT now());
15: 
```
  - lines containing 'alert' (case-insens) in n8n-flows/mf_leads.sql: none
  - n8n-flows-v3/mf_leads.sql exists, 21 lines, lines with 'alert': [1, 16, 17, 18, 19, 20]; sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
  - n8n-flows-v4/mf_leads.sql exists, 21 lines, lines with 'alert': [1, 16, 17, 18, 19, 20]; sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
  - sha256 n8n-flows/mf_leads.sql = 7a18c922a1228d0f7517322cf00fd4be282d164cdaad2ce831ad33e7f92aa6ee
  - *.sql files in n8n-flows-real-v5/: []; in n8n-flows-film-v5/: []
- CITE `n8n-mainframe/mf.py:44-47`  (file lines total 366)
```
41:     spawn("crm", [sys.executable, os.path.join(HERE_MF, "crm_stub.py"), str(CRMP), CRMLOG], os.environ.copy(), "crm.log", cwd=S)
42:     spawn("catcher", [sys.executable, os.path.join(HERE, "smtp_catcher.py"), str(MAILP), MAIL], os.environ.copy(), "catcher.log", cwd=S)
43:     start_stage(); time.sleep(1)
44:     psql("DROP TABLE IF EXISTS mf_leads;")
45:     psql("CREATE TABLE mf_leads(lead_key text PRIMARY KEY, email text, name text, state text NOT NULL DEFAULT 'new' CHECK (state IN ('new','processing','done','review','unknown','failed')), claimed_until timestamptz, claim_token text, "
46:          "attempts int NOT NULL DEFAULT 0, crm_id text, mail_sent boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), "
47:          "alert_sent boolean NOT NULL DEFAULT false, alert_token text, alert_until timestamptz, alert_attempts int NOT NULL DEFAULT 0);")
48: def n8n_prepare_mf(recovery_copies=1):
49:     api.login(); inst = json.load(open(os.path.join(WORK, ".run", "instance.json")))
50:     c = api.call("POST", "/credentials", {"name": "mf-mail-smtp", "type": "smtp", "projectId": inst["project_id"],
```
  - probe `alert_sent`: at cited lines = yes; all lines in file with the text = [47, 228, 233, 234, 236, 238, 245, 248, 252, 254, 260, 261, 263]
  - probe `alert_token`: at cited lines = yes; all lines in file with the text = [47]
  - probe `alert_until`: at cited lines = yes; all lines in file with the text = [47]
  - probe `alert_attempts`: at cited lines = yes; all lines in file with the text = [47, 233, 245, 248, 254, 260]
  - probe `CREATE TABLE mf_leads`: at cited lines = yes; all lines in file with the text = [45]
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertClaim` (node name; JSON line(s) with the name = [127]; nodes in file = 10)
  - key fields: {"name": "AlertClaim", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=***MASKED***, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR aler ...[+125 chars]
  - JSON source lines around name line:
```
124:     "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=***MASKED***, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY  ...[+84 chars]
125:     "options": {}
126:    },
127:    "name": "AlertClaim",
128:    "type": "n8n-nodes-base.postgres",
129:    "typeVersion": 2.5,
130:    "position": [
```
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]
  - probe `alert_sent`: in this node object = yes; all lines in file with the text = [124, 204, 228]
  - README pointer `n8n-table-screen-v2/README.md:27`: 3. The table mf_leads must exist (DDL in n8n-flows-v4, file mf_leads.sql).
  - README pointer `n8n-table-screen/README.md:17`: 3. Make sure the table mf_leads exists (DDL in the n8n-flows-v4 folder, file mf_leads.sql).

## F-002
- CLAIM (row title, quoted): "Intake: a missing lead_key is not rejected and a failed Postgres write answers the sender with a bare 500."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-form.json:Claim; n8n-flows-real-v5/mf-hook.json:Claim; n8n-flows-real-v5/mf-form.json:Valid (film same)
- CITE `n8n-flows-real-v5/mf-form.json:Claim` (node name; JSON line(s) with the name = [102]; nodes in file = 12)
  - key fields: {"name": "Claim", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "alwaysOutputData": true}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON  ...[+170 chars]
  - JSON source lines around name line:
```
99:      "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
100:     }
101:    },
102:    "name": "Claim",
103:    "type": "n8n-nodes-base.postgres",
104:    "typeVersion": 2.5,
105:    "position": [
```
  - probe `onError`: in this node object = no; all lines in file with the text = none
  - probe `retryOnFail`: in this node object = no; all lines in file with the text = none
  - probe `ON CONFLICT (lead_key) DO NOTHING`: in this node object = yes; all lines in file with the text = [97]
- CITE `n8n-flows-real-v5/mf-hook.json:Claim` (node name; JSON line(s) with the name = [102]; nodes in file = 12)
  - key fields: {"name": "Claim", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "alwaysOutputData": true}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON  ...[+170 chars]
  - JSON source lines around name line:
```
99:      "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
100:     }
101:    },
102:    "name": "Claim",
103:    "type": "n8n-nodes-base.postgres",
104:    "typeVersion": 2.5,
105:    "position": [
```
  - probe `onError`: in this node object = no; all lines in file with the text = none
  - probe `retryOnFail`: in this node object = no; all lines in file with the text = none
  - probe `ON CONFLICT (lead_key) DO NOTHING`: in this node object = yes; all lines in file with the text = [97]
- CITE `n8n-flows-real-v5/mf-form.json:Valid` (node name; JSON line(s) with the name = [86]; nodes in file = 12)
  - key fields: {"name": "Valid", "type": "n8n-nodes-base.set", "typeVersion": 3.4}
  - parameters (first 300 chars): {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ $json.lead_key }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "string"}, {"id": "vali ...[+127 chars]
  - JSON source lines around name line:
```
83:     },
84:     "options": {}
85:    },
86:    "name": "Valid",
87:    "type": "n8n-nodes-base.set",
88:    "typeVersion": 3.4,
89:    "position": [
```
  - probe `lead_key`: in this node object = yes; all lines in file with the text = [25, 26, 59, 60, 61, 97, 99, 128, 185, 186, 187, 238, 254, 270, 272]
  - probe `valid`: in this node object = yes; all lines in file with the text = [77, 78, 99]
- CITE `n8n-flows-film-v5/mf-form.json:Claim` (node name; JSON line(s) with the name = [102]; nodes in file = 12)
  - key fields: {"name": "Claim", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "alwaysOutputData": true}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON  ...[+170 chars]
  - JSON source lines around name line:
```
99:      "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
100:     }
101:    },
102:    "name": "Claim",
103:    "type": "n8n-nodes-base.postgres",
104:    "typeVersion": 2.5,
105:    "position": [
```
  - probe `onError`: in this node object = no; all lines in file with the text = none
  - probe `retryOnFail`: in this node object = no; all lines in file with the text = none
  - probe `ON CONFLICT (lead_key) DO NOTHING`: in this node object = yes; all lines in file with the text = [97]
- CITE `n8n-flows-film-v5/mf-form.json:Valid` (node name; JSON line(s) with the name = [86]; nodes in file = 12)
  - key fields: {"name": "Valid", "type": "n8n-nodes-base.set", "typeVersion": 3.4}
  - parameters (first 300 chars): {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ $json.lead_key }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "string"}, {"id": "vali ...[+127 chars]
  - JSON source lines around name line:
```
83:     },
84:     "options": {}
85:    },
86:    "name": "Valid",
87:    "type": "n8n-nodes-base.set",
88:    "typeVersion": 3.4,
89:    "position": [
```
  - probe `lead_key`: in this node object = yes; all lines in file with the text = [25, 26, 59, 60, 61, 97, 99, 128, 185, 186, 187, 238, 254, 270, 272]
  - probe `valid`: in this node object = yes; all lines in file with the text = [77, 78, 99]
- CITE `n8n-mainframe/build_mainframe.py:82-84`  (file lines total 124)
```
79:     n = [N("Receive", "n8n-nodes-base.webhook", 2, {"httpMethod": "POST", "path": path, "responseMode": "responseNode", "options": {}}, [0, 0], webhookId=wid),
80:          setf("Item", {"lead_key": ("={{ $json.body.%s }}" % ref, "string"), "email": ("={{ $json.body.%s }}" % em, "string"), "name": ("={{ $json.body.%s }}" % nm, "string")}, [220, 0]),
81:          setf("Valid", {"lead_key": ("={{ $json.lead_key }}", "string"), "email": ("={{ $json.email }}", "string"), "name": ("={{ $json.name }}", "string"), "valid": ("={{ %s }}" % EMV, "boolean")}, [440, 0]),
82:          pg("Claim", "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '%d seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) "
83:             "ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;" % LEASE, "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}", [660, 0]),
84:          iff("Claimed", "={{ $json.lead_key }}", "string", "notEmpty", None, [880, 0]),
85:          iff("IsProcessing", "={{ $json.state }}", "string", "equals", "processing", [1100, -100]),
86:          setf("SubInput", {"lead_key": ("={{ $json.lead_key }}", "string"), "claim_token": ("={{ $json.claim_token }}", "string"), "email": ("={{ $('Valid').item.json.email }}", "string")}, [1320, -160]),
87:          call_sub("RunSub", [1540, -160]),
```
  - probe `ON CONFLICT (lead_key) DO NOTHING`: at cited lines = yes; all lines in file with the text = [83]
  - probe `INSERT INTO mf_leads`: at cited lines = yes; all lines in file with the text = [82]
- CITE `PLAN-4-NLITE-FROM-LEAD.md:47`  (file lines total 200)
```
44: | Mail polling loop | wait, settle, retry | 2 `poll_mailboxes` (`wanted` is an int, `expected` is list[set]) | run_real_check.py 761-833 | nothing | reuse | NEEDED |
45: | Reusable as written | operator safety | 2 `ask_yes` (but see tty rule), `probe_mailbox`, `probe_hubspot`, `mask_result`, `scrub`, `imap_settings`, `archive_all`, `merge_counts`, `EXIT_*`, `refuse_tls_environment`, `parse_end_utc` (test-time parity only), `utc_now`, `load_env` | codebase review | n ...[+25 chars]
46: | NOT reusable (Mode A names) | — | `refuse_names`, `check_formats`, `check_clock_and_dates`, `--retire-check`, `wait_for_enter_or_flag` (waits for the typed word `end` or an `end.flag`, not Enter), `send_with_retries` (retries only 503 and network errors; lives in load_tools/load_driver.py:111) | c ...[+102 chars]
47: | Send with loss rule | resend when no verdict | 2 port of `dn1_common.take()` (demo repo; no cross-repo import, so a copy): resend on no verdict or `n8n_error`, 1 post + 3 resends = 4 posts, 5 s gap | dn1_common.py 124-132 | the take-repo copy | KEEP-CODE about 40 lines (WP3a) | NEEDED |
48: | Kill and restart of n8n | the crash scene | 2 port of `lib.kill_n8n_confirmed` | mf.py:61 | pid check, process-group kill | KEEP-CODE about 30 lines (WP3a); not guarantee-class | NEEDED |
49: | Table read-back | final state per lead | 3 `docker exec <pg> psql -At -F '|'` | RUN-ON-LAPTOP section 5 | fixed column list | glue (WP3a) | NEEDED |
50: | Pass rule, result file, audit lines | the verdict | 5 | none higher | yes | KEEP-CODE (WP3b) | NEEDED |
```
  - probe `resend on no verdict or `n8n_error``: at cited lines = yes; all lines in file with the text = [47]
  - probe `1 post + 3 resends`: at cited lines = yes; all lines in file with the text = [47]
- CITE `PLAN-4-NLITE-FROM-LEAD.md:77`  (file lines total 200)
```
74: ### WP1: Qualify stage (money). 5.5 h (3.5 build, 2 tests). Uncapped review and mutants.
75: - Owns `scripts/qualify_stage.py`, `tests/test_qualify_stage.py` (new). Real mode only: the harness keeps its own prototype stage_server.py (mf.py asserts `/mail_count` and `/stats`); WP1 does not replace it.
76: - Inputs: the prototype's logic; `lead_desk.live_claude.LiveQualifier`/`SpendLedger`; `lead_desk.identity.check_payload`; `lead_desk.lockfile`. It does NOT import `run_real_check`: it has its own `parse_window_end(text)` (UTC ISO ending in Z, 6 lines) with a test-time parity test against `run_real_c ...[+228 chars]
77: - Behaviour (decided): settings come from `stage.env` and named arguments, all validated (port int 1024-65535, journal under the take folder, no `/mnt/`); binds 127.0.0.1 only, a non-loopback bind is refused (exit 2); `POST /qualify {lead_key, email}`; Content-Length missing -> 411, non-numeric or n ...[+376 chars]
78: - **Why three idempotency layers exist (so a reviewer does not cut one):** the n8n claim row stops a second door/resend from starting the lead twice; the stage journal stops the recovery flow from calling the model again after a kill that came after the model call and before the table update; the ta ...[+72 chars]
79: - **Concurrency.** All model calls run under ONE in-process lock (single flight). A per-call result `(label, network_attempted)` is returned by the wrapper; the shared `calls` comparison of the prototype is dropped (it was racy). Journal (JSON lines, fsync, loaded into memory at start, in-process lo ...[+449 chars]
80: - Fault endpoints only with `--test-faults` (404 otherwise). Logs and journal hold lead key, label and cached flag only, never the e-mail. The model input stays what the desk sends today (lead id plus normalised made-up e-mail); stated, not hidden. On /mnt/ drvfs file locks may not work: the journal ...[+72 chars]
```
  - probe `^L[0-9a-f]{16}$`: at cited lines = yes; all lines in file with the text = [68, 77]
  - probe `lead_key`: at cited lines = yes; all lines in file with the text = [67, 68, 77, 115]

## F-003
- CLAIM (row title, quoted): "Video run sheet: stale and wrong captions (recovery time, seven columns, retention, late alert line)."
- row cited-path cell (quoted): handover/demo/VIDEO-RUNSHEET.md:33, :39, :41, :50, :62
- CITE `VIDEO-RUNSHEET.md:33`  (file lines total 91)
```
30: | 1. Stack at rest | Opens the prepared screen set: the n8n flow list (entry flows and recovery flow switched on, table-screen flow if it exists), the lead table, the CRM list, the intake mailbox view, and the n8n execution list. Types and clicks nothing in the list. Executions older than the take a ...[+689 chars]
31: | 2. One lead goes in | Runs the one prepared send note (saved text, owner pastes it) that posts one made-up lead (made-up person on example.test, key L plus 16 hex, the key is the door id) to the form entry on the LOOPBACK address, path mf-form. | Reply with a verdict (new or done). Then: table row ...[+535 chars]
32: | 3. Same lead sent again | Pastes the same send note again with the same lead key. | The reply gives the stored state, not a new run. CRM list still 1 row, intake still 1 mail. Caption: "a lead sent twice with the same id is processed once". The screen is the evidence. | 25 s EST | NO NUMBER. T13 ( ...[+310 chars]
33: | 4. Kill n8n mid-lead, recovery finishes it | Sends a new made-up lead. At the kill point (after the claim row is written, before the CRM write, as K1) stops n8n with the prepared stop note, then restarts it. Screen shows "setting: lease 45 s". Waits with the stopwatch overlay, then cuts or speeds  ...[+984 chars]
34: | 5. A lead that can never finish (CRM refuses) | Switches the stand-in CRM to refuse every call (prepared note), sends a made-up lead, waits with the stopwatch overlay, then cuts or speeds up. Screen shows "setting: lease 45 s" and "stand-in CRM: a real CRM has no switch to refuse every call". | Af ...[+821 chars]
35: | 6. Doubtful case, step 1: the lead goes in | Sends a made-up lead through the film-flows entry (LOOPBACK address, path mf-form) with the mail stand-in already armed (.drop = 1, see step 2). | The request goes in and n8n answers. Intake list still empty. Label on screen: "test scene on stand-ins".  ...[+155 chars]
36: | 7. Doubtful case, step 2: the mail may or may not have gone | Arms the SMTP stand-in with .drop = 1 before the send (it accepts a mail, then drops the connection without saying queued). Says on screen: "stand-in fault". | Caption exactly: "Test scene on a stand-in mail server: a real mailbox has n ...[+589 chars]
```
  - probe `lease plus 25 to 30 s`: at cited lines = yes; all lines in file with the text = [5, 23, 33, 41, 79]
- CITE `VIDEO-RUNSHEET.md:39`  (file lines total 91)
```
36: | 7. Doubtful case, step 2: the mail may or may not have gone | Arms the SMTP stand-in with .drop = 1 before the send (it accepts a mail, then drops the connection without saying queued). Says on screen: "stand-in fault". | Caption exactly: "Test scene on a stand-in mail server: a real mailbox has n ...[+589 chars]
37: | 8. Doubtful case, step 3: the answer says unknown (UNBACKED, fallback) | Fallback: no typing, no reading aloud; voice says only that the outcome is unknown. Shows the reply only if the rehearsal confirmed a reply exists on these flows and shows its wording. | Fallback: caption "outcome unknown, no ...[+402 chars]
38: | 9. Doubtful case, step 4: one alert, no second mail | Waits with the stopwatch overlay, then cuts or speeds up. Shows "setting: lease 45 s". Opens the alert mail in the stand-in inbox. | Alert mail with subject "[demo] Lead desk: mail outcome unknown for the lead id" and text "the mail may or may  ...[+792 chars]
39: | 10. Doubtful case, step 5: the table row (UNBACKED, fallback) | Fallback (keep it): a plain picture of the rows taken in rehearsal, or a one-time n8n database-node preview selecting only the seven safe columns. The table screen is BUILT, NOT RUN (laptop rehearsal in progress): show it only if it w ...[+581 chars]
40: | 11. OPTIONAL: the alert mail is refused twice (UNDER REVIEW: audit advises cut) | Arms the alert-only refusal on the stand-in (AF1 fault: answers 451 twice), sends a doubtful lead, then jumps. On screen: "sped up, real wait read from the overlay, test setting". | Row shows unknown with alert_sent  ...[+512 chars]
41: | 12. Closing card | No clicks. Voice over one card, six short lines. | Line 1, claim: a lead sent twice with the same id is processed once. Line 2, history (older flow version v3, stand-ins, 20 s test lease): kill series K1, K2, K3, K3B, 80 kills, 0 lost, 0 doubled; 40 of the 80 (K3, K3B) ended UNK ...[+1111 chars]
42: 
```
  - probe `seven`: at cited lines = yes; all lines in file with the text = [39, 62]
- CITE `VIDEO-RUNSHEET.md:41`  (file lines total 91)
```
38: | 9. Doubtful case, step 4: one alert, no second mail | Waits with the stopwatch overlay, then cuts or speeds up. Shows "setting: lease 45 s". Opens the alert mail in the stand-in inbox. | Alert mail with subject "[demo] Lead desk: mail outcome unknown for the lead id" and text "the mail may or may  ...[+792 chars]
39: | 10. Doubtful case, step 5: the table row (UNBACKED, fallback) | Fallback (keep it): a plain picture of the rows taken in rehearsal, or a one-time n8n database-node preview selecting only the seven safe columns. The table screen is BUILT, NOT RUN (laptop rehearsal in progress): show it only if it w ...[+581 chars]
40: | 11. OPTIONAL: the alert mail is refused twice (UNDER REVIEW: audit advises cut) | Arms the alert-only refusal on the stand-in (AF1 fault: answers 451 twice), sends a doubtful lead, then jumps. On screen: "sped up, real wait read from the overlay, test setting". | Row shows unknown with alert_sent  ...[+512 chars]
41: | 12. Closing card | No clicks. Voice over one card, six short lines. | Line 1, claim: a lead sent twice with the same id is processed once. Line 2, history (older flow version v3, stand-ins, 20 s test lease): kill series K1, K2, K3, K3B, 80 kills, 0 lost, 0 doubled; 40 of the 80 (K3, K3B) ended UNK ...[+1111 chars]
42: 
43: ## Total running time (EST)
44: - Core scenes 1 to 10 and 12: 25 + 40 + 25 + 60 + 45 + 20 + 30 + 10 + 40 + 30 + 30 = 355 s, about 5 min 55 s. (Before: 340 s; scene 1 +10 s for the execution list, scene 7 +5 s for the longer caption.)
```
  - probe `lease plus 25 to 30 s`: at cited lines = yes; all lines in file with the text = [5, 23, 33, 41, 79]
- CITE `VIDEO-RUNSHEET.md:50`  (file lines total 91)
```
47: - All times are EST. Real waits behind the sped-up scenes (4, 5, 9, 11) are UNMEASURED at 45 s; read them from the stopwatch in the take. The old measured waits (K1 up to 59.6 s, T15 88.3 to 110.1 s, K3 and K3B about 30 s, AF1 272.1 s) were at lease 20 s on v3 and do not transfer.
48: 
49: ## Risks the owner must see
50: 1. The table screen is BUILT, NOT RUN: the laptop rehearsal is in progress; do not say it works. Keep the screenshot fallback: (a) a picture of the rows taken during rehearsal, columns lead id, state, attempts, mail_sent, alert_sent, alert_attempts, updated at only; or (b) a one-time database-node p ...[+52 chars]
51: 2. The 45 s lease has no measurement: recovery, the failed-lead wait and the alert wait on screen are all unmeasured; no caption number for them. The "plus 25 to 30 s" is an estimate whose basis is one lane3 run at 120 s and 20 s laptop data that does not obviously give 25 to 30 (K1 median is about  ...[+34 chars]
52: 3. The execution list is filmed. It shows made-up data only if every execution in it is from made-up leads; prune old ones first. It must not be presented as privacy proof: the request body stays in n8n data until pruned.
53: 4. Timing of the hand-made kill in scene 4: it must land after the claim row and before the CRM write. A person may miss; the kill can also land after the CRM write. Rehearse; state only what the take shows.
```
  - probe `seven`: at cited lines = no; all lines in file with the text = [39, 62]
  - probe `columns`: at cited lines = yes; all lines in file with the text = [30, 39, 50, 62]
- CITE `VIDEO-RUNSHEET.md:62`  (file lines total 91)
```
59: 10. Step-2 fault for a real mailbox and the Slack alert are NOT BUILT; the take says "stand-in" or cuts.
60: 
61: ## What must be rehearsed on the laptop before the take
62: 1. Import and activate the table screen flow (the rehearsal under way): open it once; confirm seven columns and no name or address column; if it fails, use the fallback picture.
63: 2. The prepared send note: one lead through mf-form on the LOOPBACK address on the real flows; check reply wording for done, for the repeat, and for unknown.
64: 3. The stand-in drop on the film flows with .drop = 1: run it five times; note intake count (0 or 1), alert count, state, real seconds to alert, and whether a reply comes back (scene 8).
65: 4. The hand kill in scene 4: time the stop note, 5 tries, record how often it lands before the CRM write.
```
  - probe `seven columns`: at cited lines = yes; all lines in file with the text = [62]
- Row claims quoted: scene 4 and card line 3 keep "lease plus 25 to 30 s"; run sheet says seven columns; card line 5 omits the lead table that keeps name and e-mail; the 13-minute late-alert line required at :82 is not on the card.
- CITE `VIDEO-RUNSHEET.md:82`  (file lines total 91)
```
79: 5. Whether the recovery estimate "lease plus 25 to 30 s" stays as a caption at all, given it is not backed at 45 s; the safe alternative is no recovery wording on screen and the wording only on the closing card.
80: 6. Closing card retention line: kept (line 5).
81: 
82: Added 17:40Z (lead note, lane3 HB189): closing card and scene 11 must not imply alerts are always quick. History line for the card: on v4, if n8n itself dies while sending the alert, the alert still goes out once but can be about 13 minutes late (780 s, RELAYED-INDEPENDENT, n and raw file not given  ...[+128 chars]
83: 
84: Update 17:08Z (lead answers):
85: - Shipped lease for real and film = 45 s (decided). Recovery caption dropped; scene 4 shows the recovery with the stopwatch overlay and NO number in voice or caption until lane3 lease-45 numbers land (first about 17:10Z, all about 17:45Z).
```
  - probe `13 minutes`: at cited lines = yes; all lines in file with the text = [82]
  - all lines in VIDEO-RUNSHEET.md with 'lease plus 25': [5, 23, 33, 41, 79]; with 'seven': [39, 62]; with '13 minutes' or '780': [82]
- CITE `n8n-table-screen-v2/mf-table-screen-v2.json:ReadLeads` (node name; JSON line(s) with the name = [26]; nodes in file = 4)
  - key fields: {"name": "ReadLeads", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "alwaysOutputData": true}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "SELECT lead_key, state, attempts, mail_sent, alert_sent, updated_at FROM mf_leads ORDER BY updated_at DESC LIMIT 50;", "options": {}}
  - JSON source lines around name line:
```
23:         "query": "SELECT lead_key, state, attempts, mail_sent, alert_sent, updated_at FROM mf_leads ORDER BY updated_at DESC LIMIT 50;",
24:         "options": {}
25:       },
26:       "name": "ReadLeads",
27:       "type": "n8n-nodes-base.postgres",
28:       "typeVersion": 2.5,
29:       "position": [
```
  - probe `lead_key`: in this node object = yes; all lines in file with the text = [23, 48]
  - probe `state`: in this node object = yes; all lines in file with the text = [23, 48]
  - probe `attempts`: in this node object = yes; all lines in file with the text = [23, 48]
  - probe `mail_sent`: in this node object = yes; all lines in file with the text = [23, 48]
  - probe `alert_sent`: in this node object = yes; all lines in file with the text = [23, 48]
  - probe `alert_attempts`: in this node object = no; all lines in file with the text = none
  - probe `updated_at`: in this node object = yes; all lines in file with the text = [23, 48]

## F-004
- CLAIM (row title, quoted): "Page statements 17 and 20 contradict each other (45 s measured vs not measured; shipped lease 120 s vs 45 s)."
- row cited-path cell (quoted): handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md:120 vs :149-157
- Row claim detail (quoted): "Statement 17 says nothing is measured at 45 s and calls 120 s the shipped lease; statement 20 gives 60.1 to 61.9 s at 45 s; the flows use 45 (Claim query, LEASE 45)."
- CITE `n8n-flows/PAGE-STATEMENTS-V4.md:120`  (file lines total 162)
```
117:     Test: AF2, not run.
118:     Raw file: none named.
119: 
120: 17. "Recovery within 60 s was measured only at the 20 s test lease (max 59.6 s, margin 0.4 s, n=20 per kill point, one machine); at the shipped 120 s lease lane3 measured 144.3 s once (n=1, v4 K1); at the 45 s film lease nothing is measured. Rough rule from lane3: about the lease plus 25 s; the 20 s ...[+50 chars]
121:     Tag: 20 s figure MEASURED-ON-LAPTOP (lead-read). 120 s figure RELAYED-INDEPENDENT (one figure, report not seen). 45 s: NOT RUN.
122:     Test: lease table, not run.
123:     Raw file: V7-v3 folder for the 20 s figure; none for the others.
```
  - probe `at the 45 s film lease nothing is measured`: at cited lines = yes; all lines in file with the text = [120]
  - probe `shipped 120 s lease`: at cited lines = yes; all lines in file with the text = [120]
- CITE `n8n-flows/PAGE-STATEMENTS-V4.md:149-157`  (file lines total 162)
```
146: - Stale source note: the V7 numbers file still says v4 B90 n=2; the settled value is n=3 on lane3 plus 1 on the laptop. Fix it at its source (not done here).
147: 
148: ## Statement 20 (FINAL, lead relay of lane3 HB194, lease 45 s, film-v4, n8n 2.46.6, independent harness)
149: 20. "At the film lease of 45 s, a lead interrupted by an n8n crash was finished about a minute after the crash." Seconds from the kill to a final state, all 18 kill runs correct: 60.1 to 61.9 s (K1 5 runs, K2 5, K3B 5, K3 3 in this page's names). Tag RELAYED-INDEPENDENT (one machine, made-up data, s ...[+105 chars]
150: NAMING (lead, final): lane3 K3 = this page's K3B (killed after the mail left: unknown + 1 alert); lane3 K6 = this page's demo K3. Statement 12 naming: use this page's names only.
151: - K1 (killed after the claim): n=5, done. Median 60.8, max 61.9 (from the 17:19Z relay; n unchanged, final per-test medians not re-relayed).
152: - K2 (killed after the CRM write): n=5, done. Median 60.9, max 61.2 (same note).
153: - K3B (n=5) and K3 (n=3): lead ends unknown with 1 alert to the owner, no second mail. Plain wording: "killed after the mail left: the lead ends unknown with one alert to the owner". n small; no timing in a caption.
154: - From n8n coming back up: 52.9 to 54.9 s (about 8 s restart is inside the kill-to-final numbers).
155: - CRM refuses every call (ERROR run), 3 of 3: lead failed, 1 alert, 0 mails, 0 CRM rows, about 4 min.
156: - Alert after a crash DURING the alert send: up to 13 minutes late (KS n=2, 780 s), not lost (statement 19).
157: - Lease 120 s for contrast: 144.2 to 144.4 s.
158: - The spread here (60.1 to 61.9 s) is smaller than my lease-20 laptop runs; the cause is unknown. Do not explain it.
159: Caption rule: only K1 and K2 (done), or the range. NEVER "within 60 s".
160: 
```
  - probe `60.1 to 61.9 s`: at cited lines = yes; all lines in file with the text = [149, 158, 161]
  - probe `45 s`: at cited lines = yes; all lines in file with the text = [93, 120, 121, 132, 139, 148, 149, 161]
  - grep 'LEASE' in build_mainframe.py: [(6, '  python build_mainframe.py OUT_DIR PG_CRED_ID SMTP_CRED_ID SUB_WORKFLOW_ID [LEASE_SECONDS] [HUBSPOT_CREDENTIAL_ID]      (LEASE_SECONDS: design value 120; the t ...[+39 chars]'), (8, 'OUT, PGID, SMTPID, SUBID = sys.argv[1:5]; LEASE = int(sys.argv[5]) if len(sys.argv) > 5 else 120'), (83, '            "ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;" % LEASE, "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}" ...[+12 chars]'), (100, '            "RETURNING lead_key, email, claim_token;" % LEASE, None, [220, -100], always=False, onError="continueRegularOutput"),')]
- CITE `n8n-flows-real-v5/mf-form.json:Claim` (node name; JSON line(s) with the name = [102]; nodes in file = 12)
  - key fields: {"name": "Claim", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "alwaysOutputData": true}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON  ...[+170 chars]
  - JSON source lines around name line:
```
99:      "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
100:     }
101:    },
102:    "name": "Claim",
103:    "type": "n8n-nodes-base.postgres",
104:    "typeVersion": 2.5,
105:    "position": [
```
  - probe `interval '45 seconds'`: in this node object = yes; all lines in file with the text = [97]

## F-005
- CLAIM (row title, quoted): "Scene 6 says the intake list is still empty, but n8n answers only after the mail step."
- row cited-path cell (quoted): handover/demo/VIDEO-RUNSHEET.md:35; n8n-flows-film-v5/mf-form.json:RunSub
- CITE `VIDEO-RUNSHEET.md:35`  (file lines total 91)
```
32: | 3. Same lead sent again | Pastes the same send note again with the same lead key. | The reply gives the stored state, not a new run. CRM list still 1 row, intake still 1 mail. Caption: "a lead sent twice with the same id is processed once". The screen is the evidence. | 25 s EST | NO NUMBER. T13 ( ...[+310 chars]
33: | 4. Kill n8n mid-lead, recovery finishes it | Sends a new made-up lead. At the kill point (after the claim row is written, before the CRM write, as K1) stops n8n with the prepared stop note, then restarts it. Screen shows "setting: lease 45 s". Waits with the stopwatch overlay, then cuts or speeds  ...[+984 chars]
34: | 5. A lead that can never finish (CRM refuses) | Switches the stand-in CRM to refuse every call (prepared note), sends a made-up lead, waits with the stopwatch overlay, then cuts or speeds up. Screen shows "setting: lease 45 s" and "stand-in CRM: a real CRM has no switch to refuse every call". | Af ...[+821 chars]
35: | 6. Doubtful case, step 1: the lead goes in | Sends a made-up lead through the film-flows entry (LOOPBACK address, path mf-form) with the mail stand-in already armed (.drop = 1, see step 2). | The request goes in and n8n answers. Intake list still empty. Label on screen: "test scene on stand-ins".  ...[+155 chars]
36: | 7. Doubtful case, step 2: the mail may or may not have gone | Arms the SMTP stand-in with .drop = 1 before the send (it accepts a mail, then drops the connection without saying queued). Says on screen: "stand-in fault". | Caption exactly: "Test scene on a stand-in mail server: a real mailbox has n ...[+589 chars]
37: | 8. Doubtful case, step 3: the answer says unknown (UNBACKED, fallback) | Fallback: no typing, no reading aloud; voice says only that the outcome is unknown. Shows the reply only if the rehearsal confirmed a reply exists on these flows and shows its wording. | Fallback: caption "outcome unknown, no ...[+402 chars]
38: | 9. Doubtful case, step 4: one alert, no second mail | Waits with the stopwatch overlay, then cuts or speeds up. Shows "setting: lease 45 s". Opens the alert mail in the stand-in inbox. | Alert mail with subject "[demo] Lead desk: mail outcome unknown for the lead id" and text "the mail may or may  ...[+792 chars]
```
  - probe `Intake list still empty`: at cited lines = yes; all lines in file with the text = [35]
- CITE `n8n-flows-film-v5/mf-form.json:RunSub` (node name; JSON line(s) with the name = [227]; nodes in file = 12)
  - key fields: {"name": "RunSub", "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2}
  - parameters (first 300 chars): {"source": "database", "workflowId": {"__rl": true, "value": "SUB_WORKFLOW_ID", "mode": "id"}, "mode": "each", "options": {"waitForSubWorkflow": true}}
  - JSON source lines around name line:
```
224:      "waitForSubWorkflow": true
225:     }
226:    },
227:    "name": "RunSub",
228:    "type": "n8n-nodes-base.executeWorkflow",
229:    "typeVersion": 1.2,
230:    "position": [
```
  - probe `waitForSubWorkflow`: in this node object = yes; all lines in file with the text = [224]
- CITE `n8n-flows-film-v5/mf-form.json:ReplyRan` (node name; JSON line(s) with the name = [243]; nodes in file = 12)
  - key fields: {"name": "ReplyRan", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.4}
  - parameters (first 300 chars): {"respondWith": "json", "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}", "options": {"responseCode": 200}}
  - JSON source lines around name line:
```
240:      "responseCode": 200
241:     }
242:    },
243:    "name": "ReplyRan",
244:    "type": "n8n-nodes-base.respondToWebhook",
245:    "typeVersion": 1.4,
246:    "position": [
```
- CITE `n8n-tests/smtp_catcher.py:40`  (file lines total 54)
```
37:                     if not l or l in (b".\r\n", b".\n"): break
38:                     buf.append(l)
39:                 m = email.message_from_bytes(b"".join(buf)); body = m.get_payload(decode=True) if not m.is_multipart() else b""
40:                 with open(FILE, "a") as f: f.write(json.dumps({"t": time.time(), "to": rcpt, "subject": str(m.get("Subject")), "body": (body or b"").decode(errors="replace"), "headers": [k for k in m.keys()]}) + "\n")
41:                 try: d = float(open(FILE + ".delay").read().strip() or 0)   # optional: seconds to wait AFTER storing, BEFORE the acknowledgement (D-N2 kill tests)
42:                 except (OSError, ValueError): d = 0
43:                 if d > 0: time.sleep(d)
```
  - probe `f.write(json.dumps`: at cited lines = yes; all lines in file with the text = [9, 40]
- CITE `n8n-tests/smtp_catcher.py:44-47`  (file lines total 54)
```
41:                 try: d = float(open(FILE + ".delay").read().strip() or 0)   # optional: seconds to wait AFTER storing, BEFORE the acknowledgement (D-N2 kill tests)
42:                 except (OSError, ValueError): d = 0
43:                 if d > 0: time.sleep(d)
44:                 try: drop = int(open(FILE + ".drop").read().strip() or 0)                          # fault mode: accept the mail (stored above), then drop the connection without the acknowledgement; the number = messages still to drop
45:                 except (OSError, ValueError): drop = 0
46:                 if drop > 0:
47:                     open(FILE + ".drop", "w").write(str(drop - 1)); return
48:                 self.w("250 queued"); rcpt = []
49:             elif u == "QUIT": self.w("221 bye"); return
50:             elif u == "RSET": rcpt = []; self.w("250 ok")
```
  - probe `drop`: at cited lines = yes; all lines in file with the text = [44, 45, 46, 47]
  - probe `return`: at cited lines = yes; all lines in file with the text = [16, 47, 49]

## F-008
- CLAIM (row title, quoted): "No error workflow in any flow; six recovery nodes swallow errors (five database nodes and RunSub); run saving was set to none."
- row cited-path cell (quoted): all 8 files in n8n-flows-real-v5 and n8n-flows-film-v5 (settings); n8n-flows-real-v5/mf-recovery.json:ClaimStuck, RunSub, MarkFailed, AlertClaim, AlertBackoff, AlertMark
- settings `n8n-flows-real-v5/mf-form.json`: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; 'errorWorkflow' key present = False
  - text 'errorWorkflow' occurrences in file: none
- settings `n8n-flows-real-v5/mf-hook.json`: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; 'errorWorkflow' key present = False
  - text 'errorWorkflow' occurrences in file: none
- settings `n8n-flows-real-v5/mf-recovery.json`: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; 'errorWorkflow' key present = False
  - text 'errorWorkflow' occurrences in file: none
- settings `n8n-flows-real-v5/mf-sub-crm-mail.json`: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; 'errorWorkflow' key present = False
  - text 'errorWorkflow' occurrences in file: none
- settings `n8n-flows-film-v5/mf-form.json`: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; 'errorWorkflow' key present = False
  - text 'errorWorkflow' occurrences in file: none
- settings `n8n-flows-film-v5/mf-hook.json`: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; 'errorWorkflow' key present = False
  - text 'errorWorkflow' occurrences in file: none
- settings `n8n-flows-film-v5/mf-recovery.json`: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; 'errorWorkflow' key present = False
  - text 'errorWorkflow' occurrences in file: none
- settings `n8n-flows-film-v5/mf-sub-crm-mail.json`: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; 'errorWorkflow' key present = False
  - text 'errorWorkflow' occurrences in file: none
- CITE `n8n-mainframe/build_mainframe.py:44`  (file lines total 124)
```
41:     con.setdefault(a, {"main": []}); m = con[a]["main"]
42:     while len(m) <= out: m.append([])
43:     m[out].append({"node": b, "type": "main", "index": 0})
44: ST = {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": False}
45: KEY = "$('SubIn').first().json.lead_key"; TOK = "$('SubIn').first().json.claim_token"
46: def sub():
47:     n = [N("SubIn", "n8n-nodes-base.executeWorkflowTrigger", 1.1, {"inputSource": "passthrough"}, [0, 0]),
```
  - probe `saveDataSuccessExecution": "none"`: at cited lines = yes; all lines in file with the text = [44]
  - probe `saveDataErrorExecution": "none"`: at cited lines = yes; all lines in file with the text = [44]
- CITE `n8n-flows-real-v5/mf-recovery.json:ClaimStuck` (node name; JSON line(s) with the name = [29]; nodes in file = 10)
  - key fields: {"name": "ClaimStuck", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=***MASKED***, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now()  ...[+125 chars]
  - JSON source lines around name line:
```
26:     "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=***MASKED***, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY  ...[+84 chars]
27:     "options": {}
28:    },
29:    "name": "ClaimStuck",
30:    "type": "n8n-nodes-base.postgres",
31:    "typeVersion": 2.5,
32:    "position": [
```
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]
- CITE `n8n-flows-real-v5/mf-recovery.json:RunSub` (node name; JSON line(s) with the name = [90]; nodes in file = 10)
  - key fields: {"name": "RunSub", "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2, "onError": "continueRegularOutput"}
  - parameters (first 300 chars): {"source": "database", "workflowId": {"__rl": true, "value": "SUB_WORKFLOW_ID", "mode": "id"}, "mode": "each", "options": {"waitForSubWorkflow": true}}
  - JSON source lines around name line:
```
87:      "waitForSubWorkflow": true
88:     }
89:    },
90:    "name": "RunSub",
91:    "type": "n8n-nodes-base.executeWorkflow",
92:    "typeVersion": 1.2,
93:    "position": [
```
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]
- CITE `n8n-flows-real-v5/mf-recovery.json:MarkFailed` (node name; JSON line(s) with the name = [105]; nodes in file = 10)
  - key fields: {"name": "MarkFailed", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;", "options": {}}
  - JSON source lines around name line:
```
102:     "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;",
103:     "options": {}
104:    },
105:    "name": "MarkFailed",
106:    "type": "n8n-nodes-base.postgres",
107:    "typeVersion": 2.5,
108:    "position": [
```
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertClaim` (node name; JSON line(s) with the name = [127]; nodes in file = 10)
  - key fields: {"name": "AlertClaim", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=***MASKED***, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR aler ...[+125 chars]
  - JSON source lines around name line:
```
124:     "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=***MASKED***, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY  ...[+84 chars]
125:     "options": {}
126:    },
127:    "name": "AlertClaim",
128:    "type": "n8n-nodes-base.postgres",
129:    "typeVersion": 2.5,
130:    "position": [
```
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertBackoff` (node name; JSON line(s) with the name = [209]; nodes in file = 10)
  - key fields: {"name": "AlertBackoff", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;", "options": {"queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item. ...[+23 chars]
  - JSON source lines around name line:
```
206:      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
207:     }
208:    },
209:    "name": "AlertBackoff",
210:    "type": "n8n-nodes-base.postgres",
211:    "typeVersion": 2.5,
212:    "position": [
```
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertMark` (node name; JSON line(s) with the name = [233]; nodes in file = 10)
  - key fields: {"name": "AlertMark", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;", "options": {"queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"}}
  - JSON source lines around name line:
```
230:      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
231:     }
232:    },
233:    "name": "AlertMark",
234:    "type": "n8n-nodes-base.postgres",
235:    "typeVersion": 2.5,
236:    "position": [
```
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]

## F-009
- CLAIM (row title, quoted): "Webhook entries have no authentication."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-form.json:Receive; n8n-flows-real-v5/mf-hook.json:Receive (film, desk doors, older versions same)
- CITE `n8n-flows-real-v5/mf-form.json:Receive` (node name; JSON line(s) with the name = [11]; nodes in file = 12)
  - key fields: {"name": "Receive", "type": "n8n-nodes-base.webhook", "typeVersion": 2}
  - parameters (first 300 chars): {"httpMethod": "POST", "path": "mf-form", "responseMode": "responseNode", "options": {}}
  - JSON source lines around name line:
```
8:     "responseMode": "responseNode",
9:     "options": {}
10:    },
11:    "name": "Receive",
12:    "type": "n8n-nodes-base.webhook",
13:    "typeVersion": 2,
14:    "position": [
```
  - probe `options`: in this node object = yes; all lines in file with the text = [9, 44, 84, 98, 120, 139, 152, 170, 204, 223, 239, 255, 271, 294]
  - probe `authentication`: in this node object = no; all lines in file with the text = none
  - probe `headerAuth`: in this node object = no; all lines in file with the text = none
- CITE `n8n-flows-real-v5/mf-hook.json:Receive` (node name; JSON line(s) with the name = [11]; nodes in file = 12)
  - key fields: {"name": "Receive", "type": "n8n-nodes-base.webhook", "typeVersion": 2}
  - parameters (first 300 chars): {"httpMethod": "POST", "path": "mf-hook", "responseMode": "responseNode", "options": {}}
  - JSON source lines around name line:
```
8:     "responseMode": "responseNode",
9:     "options": {}
10:    },
11:    "name": "Receive",
12:    "type": "n8n-nodes-base.webhook",
13:    "typeVersion": 2,
14:    "position": [
```
  - probe `options`: in this node object = yes; all lines in file with the text = [9, 44, 84, 98, 120, 139, 152, 170, 204, 223, 239, 255, 271, 294]
  - probe `authentication`: in this node object = no; all lines in file with the text = none
  - probe `headerAuth`: in this node object = no; all lines in file with the text = none
- CITE `n8n-flows-film-v5/mf-form.json:Receive` (node name; JSON line(s) with the name = [11]; nodes in file = 12)
  - key fields: {"name": "Receive", "type": "n8n-nodes-base.webhook", "typeVersion": 2}
  - parameters (first 300 chars): {"httpMethod": "POST", "path": "mf-form", "responseMode": "responseNode", "options": {}}
  - JSON source lines around name line:
```
8:     "responseMode": "responseNode",
9:     "options": {}
10:    },
11:    "name": "Receive",
12:    "type": "n8n-nodes-base.webhook",
13:    "typeVersion": 2,
14:    "position": [
```
  - probe `options`: in this node object = yes; all lines in file with the text = [9, 44, 84, 98, 120, 139, 152, 170, 204, 223, 239, 255, 271, 294]
  - probe `authentication`: in this node object = no; all lines in file with the text = none
  - probe `headerAuth`: in this node object = no; all lines in file with the text = none
- CITE `n8n-flows-film-v5/mf-hook.json:Receive` (node name; JSON line(s) with the name = [11]; nodes in file = 12)
  - key fields: {"name": "Receive", "type": "n8n-nodes-base.webhook", "typeVersion": 2}
  - parameters (first 300 chars): {"httpMethod": "POST", "path": "mf-hook", "responseMode": "responseNode", "options": {}}
  - JSON source lines around name line:
```
8:     "responseMode": "responseNode",
9:     "options": {}
10:    },
11:    "name": "Receive",
12:    "type": "n8n-nodes-base.webhook",
13:    "typeVersion": 2,
14:    "position": [
```
  - probe `options`: in this node object = yes; all lines in file with the text = [9, 44, 84, 98, 120, 139, 152, 170, 204, 223, 239, 255, 271, 294]
  - probe `authentication`: in this node object = no; all lines in file with the text = none
  - probe `headerAuth`: in this node object = no; all lines in file with the text = none

## F-012
- CLAIM (row title, quoted): "Recovery: one 45 s lease for up to 5 leads processed one after another; later leads can lose attempts without being tried."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-recovery.json:ClaimStuck, RunSub; n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify, CrmUpsert
- CITE `n8n-flows-real-v5/mf-recovery.json:ClaimStuck` (node name; JSON line(s) with the name = [29]; nodes in file = 10)
  - key fields: {"name": "ClaimStuck", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=***MASKED***, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now()  ...[+125 chars]
  - JSON source lines around name line:
```
26:     "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=***MASKED***, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY  ...[+84 chars]
27:     "options": {}
28:    },
29:    "name": "ClaimStuck",
30:    "type": "n8n-nodes-base.postgres",
31:    "typeVersion": 2.5,
32:    "position": [
```
  - probe `LIMIT`: in this node object = yes; all lines in file with the text = [26, 124]
  - probe `interval`: in this node object = yes; all lines in file with the text = [7, 26, 124, 204]
  - probe `claimed_until`: in this node object = yes; all lines in file with the text = [26, 102]
- CITE `n8n-flows-real-v5/mf-recovery.json:RunSub` (node name; JSON line(s) with the name = [90]; nodes in file = 10)
  - key fields: {"name": "RunSub", "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2, "onError": "continueRegularOutput"}
  - parameters (first 300 chars): {"source": "database", "workflowId": {"__rl": true, "value": "SUB_WORKFLOW_ID", "mode": "id"}, "mode": "each", "options": {"waitForSubWorkflow": true}}
  - JSON source lines around name line:
```
87:      "waitForSubWorkflow": true
88:     }
89:    },
90:    "name": "RunSub",
91:    "type": "n8n-nodes-base.executeWorkflow",
92:    "typeVersion": 1.2,
93:    "position": [
```
  - probe `waitForSubWorkflow`: in this node object = yes; all lines in file with the text = [87]
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify` (node name; JSON line(s) with the name = [28]; nodes in file = 20)
  - key fields: {"name": "Qualify", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 2, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"method": "POST", "url": "={{ $env.DESK_URL }}/qualify", "sendBody": true, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}", "options": {"timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"}}
  - JSON source lines around name line:
```
25:      "timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"
26:     }
27:    },
28:    "name": "Qualify",
29:    "type": "n8n-nodes-base.httpRequest",
30:    "typeVersion": 4.2,
31:    "position": [
```
  - probe `timeout`: in this node object = yes; all lines in file with the text = [25]
  - probe `retryOnFail`: in this node object = yes; all lines in file with the text = [35, 107, 278]
  - probe `maxTries`: in this node object = yes; all lines in file with the text = [36, 108]
  - probe `waitBetweenTries`: in this node object = yes; all lines in file with the text = [37, 109]
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:CrmUpsert` (node name; JSON line(s) with the name = [94]; nodes in file = 20)
  - key fields: {"name": "CrmUpsert", "type": "n8n-nodes-base.hubspot", "typeVersion": 2.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 2, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"authentication": "appToken", "resource": "contact", "operation": "upsert", "email": "={{ $('SubIn').first().json.email }}", "additionalFields": {"customPropertiesUi": {"customPropertiesValues": [{"property": "hadavin_lead_id", "value": "={{ $('SubIn').first().json.lead_key }}"}, {"property": "hada ...[+81 chars]
  - JSON source lines around name line:
```
91:     },
92:     "options": {}
93:    },
94:    "name": "CrmUpsert",
95:    "type": "n8n-nodes-base.hubspot",
96:    "typeVersion": 2.2,
97:    "position": [
```
  - probe `timeout`: in this node object = no; all lines in file with the text = [25]
  - probe `retryOnFail`: in this node object = yes; all lines in file with the text = [35, 107, 278]
  - probe `maxTries`: in this node object = yes; all lines in file with the text = [36, 108]
  - probe `waitBetweenTries`: in this node object = yes; all lines in file with the text = [37, 109]
- CITE `n8n-flows-film-v5/mf-sub-crm-mail.json:CrmUpsert` (node name; JSON line(s) with the name = [84]; nodes in file = 20)
  - key fields: {"name": "CrmUpsert", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 2, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"method": "POST", "url": "={{ $env.MF_CRM_URL }}/upsert", "sendBody": true, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { hadavin_lead_id: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}", "options": {"timeout":  ...[+7 chars]
  - JSON source lines around name line:
```
81:      "timeout": 10000
82:     }
83:    },
84:    "name": "CrmUpsert",
85:    "type": "n8n-nodes-base.httpRequest",
86:    "typeVersion": 4.2,
87:    "position": [
```
  - probe `timeout`: in this node object = yes; all lines in file with the text = [25, 81]
  - probe `retryOnFail`: in this node object = yes; all lines in file with the text = [35, 91, 262]
  - probe `maxTries`: in this node object = yes; all lines in file with the text = [36, 92]
  - probe `waitBetweenTries`: in this node object = yes; all lines in file with the text = [37, 93]
- CITE `n8n-mainframe/build_mainframe.py:27`  (file lines total 124)
```
24:     return d
25: def hubspot(name, pos):
26:     # n8n HubSpot node (n8n-nodes-base.hubspot 2.2, read from the 2.46.6 source): contact / Create or Update ('upsert'), keyed on the E-MAIL (the node calls /contacts/v1/contact/createOrUpdate/email/<email>);
27:     # answer {vid, isNew} (Simplify Output off) -> the contact id is $json.vid. The node has NO timeout option; retry and error output are the generic node settings below.
28:     return N(name, "n8n-nodes-base.hubspot", 2.2, {"authentication": "appToken", "resource": "contact", "operation": "upsert", "email": "={{ $('SubIn').first().json.email }}",
29:              "additionalFields": {"customPropertiesUi": {"customPropertiesValues": [{"property": "hadavin_lead_id", "value": "={{ %s }}" % KEY}, {"property": "hadavin_label", "value": "={{ $('Qualify').first().json.label }}"}]}},
30:              "options": {}}, pos, credentials={"hubspotAppToken": {"id": HSID, "name": "hubspot-app-token"}}, retryOnFail=True, maxTries=TRIES, waitBetweenTries=1000, onError="continueErrorOutput")
```
  - probe `NO timeout option`: at cited lines = yes; all lines in file with the text = [27]
  - 'about 42 s' / '42' text in FINDINGS row 39: True

## F-013
- CLAIM (row title, quoted): "A stage call that never finishes leaves the journal at "started" with no label; every retry then gets unknown_model and the lead ends failed after 3 tries."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify, LabelOk, OutStage; n8n-mainframe/stage_server.py
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify` (node name; JSON line(s) with the name = [28]; nodes in file = 20)
  - key fields: {"name": "Qualify", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 2, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"method": "POST", "url": "={{ $env.DESK_URL }}/qualify", "sendBody": true, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}", "options": {"timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"}}
  - JSON source lines around name line:
```
25:      "timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"
26:     }
27:    },
28:    "name": "Qualify",
29:    "type": "n8n-nodes-base.httpRequest",
30:    "typeVersion": 4.2,
31:    "position": [
```
  - probe `unknown_model`: in this node object = no; all lines in file with the text = [51]
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:LabelOk` (node name; JSON line(s) with the name = [64]; nodes in file = 20)
  - key fields: {"name": "LabelOk", "type": "n8n-nodes-base.if", "typeVersion": 2.2}
  - parameters (first 300 chars): {"conditions": {"options": {"caseSensitive": true, "leftValue": "", "typeValidation": "loose"}, "conditions": [{"id": "c1", "leftValue": "={{ ['hot','warm','cold'].includes($json.label) && !$json.unknown_model }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue ...[+48 chars]
  - JSON source lines around name line:
```
61:     },
62:     "options": {}
63:    },
64:    "name": "LabelOk",
65:    "type": "n8n-nodes-base.if",
66:    "typeVersion": 2.2,
67:    "position": [
```
  - probe `unknown_model`: in this node object = yes; all lines in file with the text = [51]
  - probe `label`: in this node object = yes; all lines in file with the text = [51, 86, 87]
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:OutStage` (node name; JSON line(s) with the name = [522]; nodes in file = 20)
  - key fields: {"name": "OutStage", "type": "n8n-nodes-base.set", "typeVersion": 3.4}
  - parameters (first 300 chars): {"assignments": {"assignments": [{"id": "outcome", "name": "outcome", "value": "stage_failed", "type": "string"}, {"id": "lead_key", "name": "lead_key", "value": "={{ $('SubIn').first().json.lead_key }}", "type": "string"}]}, "options": {}}
  - JSON source lines around name line:
```
519:     },
520:     "options": {}
521:    },
522:    "name": "OutStage",
523:    "type": "n8n-nodes-base.set",
524:    "typeVersion": 3.4,
525:    "position": [
```
  - probe `unknown`: in this node object = no; all lines in file with the text = [51, 307, 330, 481]
  - probe `failed`: in this node object = yes; all lines in file with the text = [509]
- CITE `n8n-mainframe/stage_server.py:50-51`  (file lines total 61)
```
47:         if CTL["mode"] == "timeout": time.sleep(float(CTL.get("sleep", 40))); return self._j(200, {"label": "warm", "late": True})
48:         with LK:
49:             j = journal().get(k, {})
50:             if j.get("label"): return self._j(200, {"label": j["label"], "cached": True})
51:             if j.get("started"): return self._j(200, {"label": "unknown", "unknown_model": True, "cached": True})
52:             jw(lead_key=k, started=True)
53:         c0 = Q.calls
54:         try: lab = Q.qualify(k, o.get("email", ""))
```
  - probe `cached`: at cited lines = yes; all lines in file with the text = [3, 50, 51, 58]
  - probe `unknown_model`: at cited lines = yes; all lines in file with the text = [4, 51]
  - probe `started`: at cited lines = yes; all lines in file with the text = [3, 51, 52, 56]
- CITE `PLAN-4-NLITE-FROM-LEAD.md:78-79`  (file lines total 200)
```
75: - Owns `scripts/qualify_stage.py`, `tests/test_qualify_stage.py` (new). Real mode only: the harness keeps its own prototype stage_server.py (mf.py asserts `/mail_count` and `/stats`); WP1 does not replace it.
76: - Inputs: the prototype's logic; `lead_desk.live_claude.LiveQualifier`/`SpendLedger`; `lead_desk.identity.check_payload`; `lead_desk.lockfile`. It does NOT import `run_real_check`: it has its own `parse_window_end(text)` (UTC ISO ending in Z, 6 lines) with a test-time parity test against `run_real_c ...[+228 chars]
77: - Behaviour (decided): settings come from `stage.env` and named arguments, all validated (port int 1024-65535, journal under the take folder, no `/mnt/`); binds 127.0.0.1 only, a non-loopback bind is refused (exit 2); `POST /qualify {lead_key, email}`; Content-Length missing -> 411, non-numeric or n ...[+376 chars]
78: - **Why three idempotency layers exist (so a reviewer does not cut one):** the n8n claim row stops a second door/resend from starting the lead twice; the stage journal stops the recovery flow from calling the model again after a kill that came after the model call and before the table update; the ta ...[+72 chars]
79: - **Concurrency.** All model calls run under ONE in-process lock (single flight). A per-call result `(label, network_attempted)` is returned by the wrapper; the shared `calls` comparison of the prototype is dropped (it was racy). Journal (JSON lines, fsync, loaded into memory at start, in-process lo ...[+449 chars]
80: - Fault endpoints only with `--test-faults` (404 otherwise). Logs and journal hold lead key, label and cached flag only, never the e-mail. The model input stays what the desk sends today (lead id plus normalised made-up e-mail); stated, not hidden. On /mnt/ drvfs file locks may not work: the journal ...[+72 chars]
81: - Tests (ids `qs_01` ...): 10 concurrent -> 1 call + 9 cached (qs_01); started without label -> unknown, 0 calls (qs_02); `LiveCapReached` -> 502, started=false, next post may call (qs_03); window closed -> 403 (qs_04); bad key shapes (`L`+15 hex, uppercase hex, `X...`) -> 400 (qs_05); bad e-mail -> ...[+252 chars]
82: - Mutants -> killing test: drop started-before-call (qs_02); drop window check (qs_04); drop key shape check (qs_05); treat `unknown_model` as a cached label (qs_02); write the e-mail into the journal (qs_07); remove the single-flight lock (qs_01).
```
  - probe `deliberate`: at cited lines = no; all lines in file with the text = none
  - probe `money-safe`: at cited lines = no; all lines in file with the text = none
  - probe `single-flight`: at cited lines = no; all lines in file with the text = [82]
  - probe `single flight`: at cited lines = yes; all lines in file with the text = [79]

## F-014
- CLAIM (row title, quoted): "Alert loop has no cap and an AlertMark error is swallowed."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-recovery.json:AlertSend, AlertBackoff, AlertMark
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertSend` (node name; JSON line(s) with the name = [186]; nodes in file = 10)
  - key fields: {"name": "AlertSend", "type": "n8n-nodes-base.emailSend", "typeVersion": 2.1, "onError": "continueErrorOutput"}
  - parameters (first 300 chars): {"fromEmail": "FROM_ADDRESS_PLACEHOLDER", "toEmail": "={{ $env.DESK_ALERT_TO }}", "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}", "emailFormat": "text", "text": "={{ $json.state === 'u ...[+237 chars]
  - JSON source lines around name line:
```
183:      "appendAttribution": false
184:     }
185:    },
186:    "name": "AlertSend",
187:    "type": "n8n-nodes-base.emailSend",
188:    "typeVersion": 2.1,
189:    "position": [
```
  - probe `continueRegularOutput`: in this node object = no; all lines in file with the text = [43, 97, 119, 141, 223, 247]
  - probe `DESK_ALERT_TO`: in this node object = yes; all lines in file with the text = [178]
  - probe `60`: in this node object = no; all lines in file with the text = [95, 204]
  - probe `alert_attempts`: in this node object = no; all lines in file with the text = [124, 204]
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertBackoff` (node name; JSON line(s) with the name = [209]; nodes in file = 10)
  - key fields: {"name": "AlertBackoff", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;", "options": {"queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item. ...[+23 chars]
  - JSON source lines around name line:
```
206:      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
207:     }
208:    },
209:    "name": "AlertBackoff",
210:    "type": "n8n-nodes-base.postgres",
211:    "typeVersion": 2.5,
212:    "position": [
```
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]
  - probe `DESK_ALERT_TO`: in this node object = no; all lines in file with the text = [178]
  - probe `60`: in this node object = yes; all lines in file with the text = [95, 204]
  - probe `alert_attempts`: in this node object = yes; all lines in file with the text = [124, 204]
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertMark` (node name; JSON line(s) with the name = [233]; nodes in file = 10)
  - key fields: {"name": "AlertMark", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;", "options": {"queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"}}
  - JSON source lines around name line:
```
230:      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
231:     }
232:    },
233:    "name": "AlertMark",
234:    "type": "n8n-nodes-base.postgres",
235:    "typeVersion": 2.5,
236:    "position": [
```
  - probe `continueRegularOutput`: in this node object = yes; all lines in file with the text = [43, 97, 119, 141, 223, 247]
  - probe `DESK_ALERT_TO`: in this node object = no; all lines in file with the text = [178]
  - probe `60`: in this node object = no; all lines in file with the text = [95, 204]
  - probe `alert_attempts`: in this node object = no; all lines in file with the text = [124, 204]
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertClaim` (node name; JSON line(s) with the name = [127]; nodes in file = 10)
  - key fields: {"name": "AlertClaim", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=***MASKED***, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR aler ...[+125 chars]
  - JSON source lines around name line:
```
124:     "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=***MASKED***, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY  ...[+84 chars]
125:     "options": {}
126:    },
127:    "name": "AlertClaim",
128:    "type": "n8n-nodes-base.postgres",
129:    "typeVersion": 2.5,
130:    "position": [
```
  - probe `720`: in this node object = yes; all lines in file with the text = [124]
  - probe `alert_attempts`: in this node object = yes; all lines in file with the text = [124, 204]
  - probe `interval`: in this node object = yes; all lines in file with the text = [7, 26, 124, 204]

## F-017
- CLAIM (row title, quoted): "mf-form and mf-hook are copies: 10 of 12 nodes identical."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-form.json vs n8n-flows-real-v5/mf-hook.json (film same)
- real-v5: nodes in mf-form = 12, in mf-hook = 12; names only in form []; only in hook []
  - node Claim: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node Claimed: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node IsProcessing: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node Item: parameters equal = False; all fields equal ignoring id/position/webhookId = False
  - node Receive: parameters equal = False; all fields equal ignoring id/position/webhookId = False
  - node ReplyRan: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node ReplyReview: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node ReplyStored: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node RunSub: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node Stored: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node SubInput: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node Valid: parameters equal = True; all fields equal ignoring id/position/webhookId = True
- film-v5: nodes in mf-form = 12, in mf-hook = 12; names only in form []; only in hook []
  - node Claim: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node Claimed: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node IsProcessing: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node Item: parameters equal = False; all fields equal ignoring id/position/webhookId = False
  - node Receive: parameters equal = False; all fields equal ignoring id/position/webhookId = False
  - node ReplyRan: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node ReplyReview: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node ReplyStored: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node RunSub: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node Stored: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node SubInput: parameters equal = True; all fields equal ignoring id/position/webhookId = True
  - node Valid: parameters equal = True; all fields equal ignoring id/position/webhookId = True

## F-018
- CLAIM (row title, quoted): "Runtime-only behaviour is unproven: $env in expressions, HubSpot answer shape, SMTP and stage timeouts, and whether DESK_ALERT_TO is set (AlertSend reads it only from the environment, so a missing value fails every alert)."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify; n8n-flows-real-v5/mf-recovery.json:AlertSend
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify` (node name; JSON line(s) with the name = [28]; nodes in file = 20)
  - key fields: {"name": "Qualify", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 2, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"method": "POST", "url": "={{ $env.DESK_URL }}/qualify", "sendBody": true, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}", "options": {"timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"}}
  - JSON source lines around name line:
```
25:      "timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"
26:     }
27:    },
28:    "name": "Qualify",
29:    "type": "n8n-nodes-base.httpRequest",
30:    "typeVersion": 4.2,
31:    "position": [
```
  - probe `$env`: in this node object = yes; all lines in file with the text = [19, 25]
  - probe `DESK_URL`: in this node object = yes; all lines in file with the text = [19]
  - probe `MF_STAGE_URL`: in this node object = no; all lines in file with the text = none
  - probe `timeout`: in this node object = yes; all lines in file with the text = [25]
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertSend` (node name; JSON line(s) with the name = [186]; nodes in file = 10)
  - key fields: {"name": "AlertSend", "type": "n8n-nodes-base.emailSend", "typeVersion": 2.1, "onError": "continueErrorOutput"}
  - parameters (first 300 chars): {"fromEmail": "FROM_ADDRESS_PLACEHOLDER", "toEmail": "={{ $env.DESK_ALERT_TO }}", "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}", "emailFormat": "text", "text": "={{ $json.state === 'u ...[+237 chars]
  - JSON source lines around name line:
```
183:      "appendAttribution": false
184:     }
185:    },
186:    "name": "AlertSend",
187:    "type": "n8n-nodes-base.emailSend",
188:    "typeVersion": 2.1,
189:    "position": [
```
  - probe `$env`: in this node object = yes; all lines in file with the text = [178]
  - probe `DESK_ALERT_TO`: in this node object = yes; all lines in file with the text = [178]
- CITE `n8n-flows-film-v5/mf-sub-crm-mail.json:Qualify` (node name; JSON line(s) with the name = [28]; nodes in file = 20)
  - key fields: {"name": "Qualify", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 2, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"method": "POST", "url": "={{ $env.MF_STAGE_URL }}/qualify", "sendBody": true, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}", "options": {"timeout": "={{ Number($env.MF_STAGE_TIMEOUT_MS || 1000 ...[+8 chars]
  - JSON source lines around name line:
```
25:      "timeout": "={{ Number($env.MF_STAGE_TIMEOUT_MS || 10000) }}"
26:     }
27:    },
28:    "name": "Qualify",
29:    "type": "n8n-nodes-base.httpRequest",
30:    "typeVersion": 4.2,
31:    "position": [
```
  - probe `$env`: in this node object = yes; all lines in file with the text = [19, 25, 75]
  - probe `DESK_URL`: in this node object = no; all lines in file with the text = none
  - probe `MF_STAGE_URL`: in this node object = yes; all lines in file with the text = [19]
  - real-v5 mf-recovery.json:178:     "toEmail": "={{ $env.DESK_ALERT_TO }}",
  - real-v5 mf-sub-crm-mail.json:19:     "url": "={{ $env.DESK_URL }}/qualify",
  - real-v5 mf-sub-crm-mail.json:25:      "timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"
  - film-v5 mf-sub-crm-mail.json:19:     "url": "={{ $env.MF_STAGE_URL }}/qualify",
  - film-v5 mf-sub-crm-mail.json:25:      "timeout": "={{ Number($env.MF_STAGE_TIMEOUT_MS || 10000) }}"
  - film-v5 mf-sub-crm-mail.json:75:     "url": "={{ $env.MF_CRM_URL }}/upsert",

## F-019
- CLAIM (row title, quoted): "Two stores for one intake job (desk SQLite behind the desk doors vs n8n Postgres mf_leads) plus a spend ledger and three counters (the ledger is a proposed exception in EXCEPTIONS.md; the counters are test-only, L3-stores.md)."
- row cited-path cell (quoted): n8n-flows/desk-form-door.json:Send to the desk; n8n-flows/desk-webhook-door.json:Send to the desk; n8n-mainframe/stage_server.py
- CITE `n8n-flows/desk-form-door.json:Send to the desk` (node name; JSON line(s) with the name = [72]; nodes in file = 8)
  - key fields: {"name": "Send to the desk", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 3, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"method": "POST", "url": "={{ $env.DESK_URL }}/leads", "sendBody": true, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { source: $json.source, source_ref: $json.source_ref, payload: $json.payload } }}", "options": {"timeout": "={{ Number($env.DESK_TIMEOUT_MS) }}", "response": {"res ...[+54 chars]
  - JSON source lines around name line:
```
69:      }
70:     }
71:    },
72:    "name": "Send to the desk",
73:    "type": "n8n-nodes-base.httpRequest",
74:    "typeVersion": 4.2,
75:    "position": [
```
  - probe `$env.DESK_URL`: in this node object = yes; all lines in file with the text = [57]
  - probe `/leads`: in this node object = yes; all lines in file with the text = [57]
- CITE `n8n-flows/desk-webhook-door.json:Send to the desk` (node name; JSON line(s) with the name = [72]; nodes in file = 8)
  - key fields: {"name": "Send to the desk", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 3, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"method": "POST", "url": "={{ $env.DESK_URL }}/leads", "sendBody": true, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { source: $json.source, source_ref: $json.source_ref, payload: $json.payload } }}", "options": {"timeout": "={{ Number($env.DESK_TIMEOUT_MS) }}", "response": {"res ...[+54 chars]
  - JSON source lines around name line:
```
69:      }
70:     }
71:    },
72:    "name": "Send to the desk",
73:    "type": "n8n-nodes-base.httpRequest",
74:    "typeVersion": 4.2,
75:    "position": [
```
  - probe `$env.DESK_URL`: in this node object = yes; all lines in file with the text = [57]
  - probe `/leads`: in this node object = yes; all lines in file with the text = [57]
- CITE `n8n-mainframe/stage_server.py:1-3`  (file lines total 61)
```
1: """The desk STAGE the n8n main frame calls (D-N2, part C). A thin wrapper around the desk's OWN code: it imports lead_desk.live_claude (LiveQualifier, SpendLedger: reserve before the call,
2: settle after, caps) and exposes it over HTTP. NEW code here (the desk has no stage endpoint for this): about 45 lines, in this file only; the desk's source is not touched.
3:   POST /qualify {lead_key, email} -> {label, cached}    per-lead journal so a re-run never calls the model twice: 'started' is written BEFORE the call; a lead with 'started' but no label
4:                                                         (killed mid-call) is NOT called again: answer {label:"unknown", unknown_model:true} (money-safe, a person decides)
5:   GET  /mail_count?key=K -> {count} from the mail stand-in file (the second count, from the receiving side)
6: Run from the desk checkout with the desk's live-model settings in the environment (as dn1_common.denv()).  python stage_server.py PORT JOURNAL_FILE MAIL_FILE"""
```
  - stage_server.py: lines mentioning 'journal': [3, 17, 49]
  - cited files named in the row but outside this evidence scope (not read): lanes/L3-stores.md, EXCEPTIONS.md, CUT-LIST.md
  - exists: flows-audit/lanes/L3-stores.md
  - exists: flows-audit/EXCEPTIONS.md
  - exists: flows-audit/CUT-LIST.md

## F-021
- CLAIM (row title, quoted): "The variable name DESK_URL means the desk (/leads) in the doors and the stage service (/qualify) in the real flows."
- row cited-path cell (quoted): n8n-flows/desk-form-door.json:Send to the desk; n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify
- CITE `n8n-flows/desk-form-door.json:Send to the desk` (node name; JSON line(s) with the name = [72]; nodes in file = 8)
  - key fields: {"name": "Send to the desk", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 3, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"method": "POST", "url": "={{ $env.DESK_URL }}/leads", "sendBody": true, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { source: $json.source, source_ref: $json.source_ref, payload: $json.payload } }}", "options": {"timeout": "={{ Number($env.DESK_TIMEOUT_MS) }}", "response": {"res ...[+54 chars]
  - JSON source lines around name line:
```
69:      }
70:     }
71:    },
72:    "name": "Send to the desk",
73:    "type": "n8n-nodes-base.httpRequest",
74:    "typeVersion": 4.2,
75:    "position": [
```
  - probe `={{ $env.DESK_URL }}/leads`: in this node object = yes; all lines in file with the text = [57]
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify` (node name; JSON line(s) with the name = [28]; nodes in file = 20)
  - key fields: {"name": "Qualify", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "onError": "continueErrorOutput", "retryOnFail": true, "maxTries": 2, "waitBetweenTries": 1000}
  - parameters (first 300 chars): {"method": "POST", "url": "={{ $env.DESK_URL }}/qualify", "sendBody": true, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}", "options": {"timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"}}
  - JSON source lines around name line:
```
25:      "timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"
26:     }
27:    },
28:    "name": "Qualify",
29:    "type": "n8n-nodes-base.httpRequest",
30:    "typeVersion": 4.2,
31:    "position": [
```
  - probe `={{ $env.DESK_URL }}/qualify`: in this node object = yes; all lines in file with the text = [19]
  - 'STAGE_ENV' in build_mainframe.py: [(13, 'STAGE_ENV, TMO_ENV, FROM = ("DESK_URL", "DESK_TIMEOUT_MS", "FROM_ADDRESS_PLACEHOLDER") if REAL else ("MF_STAGE_URL", "MF_STAGE_TIMEOUT_MS", "desk@example.test")'), (48, '         http("Qualify", "={{ $env.%s }}/qualify" % STAGE_ENV, "={{ { lead_key: %s, email: $(\'SubIn\').first().json.email } }}" % KEY, [220, 0], True, errout=True),')]
  - 'DESK_URL' in n8n-flows/N8N-START.md lines: [9]

## F-029
- CLAIM (row title, quoted): "The take flows still contain placeholder values (FROM_ADDRESS_PLACEHOLDER, INTAKE_ADDRESS_PLACEHOLDER, HS_CRED_PLACEHOLDER, SUB_WORKFLOW_ID); if one is left in, mail or the sub-flow call fails and the only trace is an alert sent over the same mail server."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-sub-crm-mail.json:SendMail (lines 256-257), mf-recovery.json:AlertSend (line 177), mf-sub-crm-mail.json:CrmUpsert credential id (line 103), mf-form.json, mf-hook.json, mf-recovery.json:RunSub (SUB_WORKFLOW_ID)
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:256-257`  (file lines total 813)
```
253:   },
254:   {
255:    "parameters": {
256:     "fromEmail": "FROM_ADDRESS_PLACEHOLDER",
257:     "toEmail": "INTAKE_ADDRESS_PLACEHOLDER",
258:     "subject": "={{ '[demo] lead ' + $('SubIn').first().json.lead_key }}",
259:     "emailFormat": "text",
260:     "text": "made-up thank-you text",
```
  - probe `PLACEHOLDER`: at cited lines = yes; all lines in file with the text = [103, 256, 257]
- CITE `n8n-flows-real-v5/mf-recovery.json:177`  (file lines total 341)
```
174:   },
175:   {
176:    "parameters": {
177:     "fromEmail": "FROM_ADDRESS_PLACEHOLDER",
178:     "toEmail": "={{ $env.DESK_ALERT_TO }}",
179:     "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}",
180:     "emailFormat": "text",
```
  - probe `PLACEHOLDER`: at cited lines = yes; all lines in file with the text = [177]
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:103`  (file lines total 813)
```
100:    ],
101:    "credentials": {
102:     "hubspotAppToken": {
103:      "id": "HS_CRED_PLACEHOLDER",
104:      "name": "hubspot-app-token"
105:     }
106:    },
```
  - probe `PLACEHOLDER`: at cited lines = yes; all lines in file with the text = [103, 256, 257]
  - n8n-flows-real-v5/mf-form.json 'PLACEHOLDER': 0 line(s): []
  - n8n-flows-real-v5/mf-form.json 'SUB_WORKFLOW_ID': 1 line(s): [(219, '"value": "SUB_WORKFLOW_ID",')]
  - n8n-flows-real-v5/mf-hook.json 'PLACEHOLDER': 0 line(s): []
  - n8n-flows-real-v5/mf-hook.json 'SUB_WORKFLOW_ID': 1 line(s): [(219, '"value": "SUB_WORKFLOW_ID",')]
  - n8n-flows-real-v5/mf-recovery.json 'PLACEHOLDER': 1 line(s): [(177, '"fromEmail": "FROM_ADDRESS_PLACEHOLDER",')]
  - n8n-flows-real-v5/mf-recovery.json 'SUB_WORKFLOW_ID': 1 line(s): [(82, '"value": "SUB_WORKFLOW_ID",')]
  - n8n-flows-real-v5/mf-sub-crm-mail.json 'PLACEHOLDER': 3 line(s): [(103, '"id": "HS_CRED_PLACEHOLDER",'), (256, '"fromEmail": "FROM_ADDRESS_PLACEHOLDER",'), (257, '"toEmail": "INTAKE_ADDRESS_PLACEHOLDER",')]
  - n8n-flows-real-v5/mf-sub-crm-mail.json 'SUB_WORKFLOW_ID': 0 line(s): []
  - 'FIX-PLAN' files: ['/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/fa/handover/flows-audit/FIX-PLAN.md']

## F-030
- CLAIM (row title, quoted): "The alert mail and the lead mail use the same mail server, so one mail outage stops both and nobody is told."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-recovery.json:AlertSend and mf-sub-crm-mail.json:SendMail (same SMTP credential)
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertSend` (node name; JSON line(s) with the name = [186]; nodes in file = 10)
  - key fields: {"name": "AlertSend", "type": "n8n-nodes-base.emailSend", "typeVersion": 2.1, "onError": "continueErrorOutput"}
  - parameters (first 300 chars): {"fromEmail": "FROM_ADDRESS_PLACEHOLDER", "toEmail": "={{ $env.DESK_ALERT_TO }}", "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}", "emailFormat": "text", "text": "={{ $json.state === 'u ...[+237 chars]
  - JSON source lines around name line:
```
183:      "appendAttribution": false
184:     }
185:    },
186:    "name": "AlertSend",
187:    "type": "n8n-nodes-base.emailSend",
188:    "typeVersion": 2.1,
189:    "position": [
```
  - probe `credentials`: in this node object = yes; all lines in file with the text = [36, 112, 134, 193, 216, 240]
  - probe `smtp`: in this node object = yes; all lines in file with the text = [194, 196]
- CITE `n8n-flows-real-v5/mf-sub-crm-mail.json:SendMail` (node name; JSON line(s) with the name = [265]; nodes in file = 20)
  - key fields: {"name": "SendMail", "type": "n8n-nodes-base.emailSend", "typeVersion": 2.1, "onError": "continueErrorOutput", "retryOnFail": false}
  - parameters (first 300 chars): {"fromEmail": "FROM_ADDRESS_PLACEHOLDER", "toEmail": "INTAKE_ADDRESS_PLACEHOLDER", "subject": "={{ '[demo] lead ' + $('SubIn').first().json.lead_key }}", "emailFormat": "text", "text": "made-up thank-you text", "options": {"appendAttribution": false}}
  - JSON source lines around name line:
```
262:      "appendAttribution": false
263:     }
264:    },
265:    "name": "SendMail",
266:    "type": "n8n-nodes-base.emailSend",
267:    "typeVersion": 2.1,
268:    "position": [
```
  - probe `credentials`: in this node object = yes; all lines in file with the text = [101, 127, 214, 272, 296, 319, 342]
  - probe `smtp`: in this node object = yes; all lines in file with the text = [273, 275]

## F-031
- CLAIM (row title, quoted): "A lead with an invalid e-mail address ends in state review, and nothing alerts on it and nothing reads it again."
- row cited-path cell (quoted): n8n-flows-real-v5/mf-recovery.json:ClaimStuck (state NOT IN done, review, unknown, failed) and AlertClaim (state IN unknown, failed)
- CITE `n8n-flows-real-v5/mf-recovery.json:ClaimStuck` (node name; JSON line(s) with the name = [29]; nodes in file = 10)
  - key fields: {"name": "ClaimStuck", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=***MASKED***, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now()  ...[+125 chars]
  - JSON source lines around name line:
```
26:     "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=***MASKED***, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY  ...[+84 chars]
27:     "options": {}
28:    },
29:    "name": "ClaimStuck",
30:    "type": "n8n-nodes-base.postgres",
31:    "typeVersion": 2.5,
32:    "position": [
```
  - probe `NOT IN`: in this node object = yes; all lines in file with the text = [26, 102]
  - probe `'review'`: in this node object = yes; all lines in file with the text = [26, 102]
  - probe `'done'`: in this node object = yes; all lines in file with the text = [26, 102]
  - probe `'unknown'`: in this node object = yes; all lines in file with the text = [26, 102, 124, 179, 181]
  - probe `'failed'`: in this node object = yes; all lines in file with the text = [26, 102, 124]
- CITE `n8n-flows-real-v5/mf-recovery.json:AlertClaim` (node name; JSON line(s) with the name = [127]; nodes in file = 10)
  - key fields: {"name": "AlertClaim", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "onError": "continueRegularOutput", "alwaysOutputData": false}
  - parameters (first 300 chars): {"operation": "executeQuery", "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=***MASKED***, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR aler ...[+125 chars]
  - JSON source lines around name line:
```
124:     "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=***MASKED***, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY  ...[+84 chars]
125:     "options": {}
126:    },
127:    "name": "AlertClaim",
128:    "type": "n8n-nodes-base.postgres",
129:    "typeVersion": 2.5,
130:    "position": [
```
  - probe `state IN`: in this node object = yes; all lines in file with the text = [124]
  - probe `'unknown'`: in this node object = yes; all lines in file with the text = [26, 102, 124, 179, 181]
  - probe `'failed'`: in this node object = yes; all lines in file with the text = [26, 102, 124]
  - probe `'review'`: in this node object = no; all lines in file with the text = [26, 102]

## SUMMARY: probe results per cite (mechanical count of the probe lines above; probe = text quoted from the claim)

| id | cite | probes yes | probes no (text) |
|---|---|---|---|
| F-001 | n8n-flows/mf_leads.sql | 0/0 | - |
| F-001 | n8n-mainframe/mf.py:44-47 | 5/5 | - |
| F-001 | n8n-flows-real-v5/mf-recovery.json:AlertClaim | 2/2 | - |
| F-002 | n8n-flows-real-v5/mf-form.json:Claim | 1/3 | onError, retryOnFail |
| F-002 | n8n-flows-real-v5/mf-hook.json:Claim | 1/3 | onError, retryOnFail |
| F-002 | n8n-flows-real-v5/mf-form.json:Valid | 2/2 | - |
| F-002 | n8n-flows-film-v5/mf-form.json:Claim | 1/3 | onError, retryOnFail |
| F-002 | n8n-flows-film-v5/mf-form.json:Valid | 2/2 | - |
| F-002 | n8n-mainframe/build_mainframe.py:82-84 | 2/2 | - |
| F-002 | PLAN-4-NLITE-FROM-LEAD.md:47 | 2/2 | - |
| F-002 | PLAN-4-NLITE-FROM-LEAD.md:77 | 2/2 | - |
| F-003 | VIDEO-RUNSHEET.md:33 | 1/1 | - |
| F-003 | VIDEO-RUNSHEET.md:39 | 1/1 | - |
| F-003 | VIDEO-RUNSHEET.md:41 | 1/1 | - |
| F-003 | VIDEO-RUNSHEET.md:50 | 1/2 | seven |
| F-003 | VIDEO-RUNSHEET.md:62 | 1/1 | - |
| F-003 | VIDEO-RUNSHEET.md:82 | 1/1 | - |
| F-003 | n8n-table-screen-v2/mf-table-screen-v2.json:ReadLeads | 6/7 | alert_attempts |
| F-004 | n8n-flows/PAGE-STATEMENTS-V4.md:120 | 2/2 | - |
| F-004 | n8n-flows/PAGE-STATEMENTS-V4.md:149-157 | 2/2 | - |
| F-004 | n8n-flows-real-v5/mf-form.json:Claim | 1/1 | - |
| F-005 | VIDEO-RUNSHEET.md:35 | 1/1 | - |
| F-005 | n8n-flows-film-v5/mf-form.json:RunSub | 1/1 | - |
| F-005 | n8n-flows-film-v5/mf-form.json:ReplyRan | 0/0 | - |
| F-005 | n8n-tests/smtp_catcher.py:40 | 1/1 | - |
| F-005 | n8n-tests/smtp_catcher.py:44-47 | 2/2 | - |
| F-008 | n8n-mainframe/build_mainframe.py:44 | 2/2 | - |
| F-008 | n8n-flows-real-v5/mf-recovery.json:ClaimStuck | 1/1 | - |
| F-008 | n8n-flows-real-v5/mf-recovery.json:RunSub | 1/1 | - |
| F-008 | n8n-flows-real-v5/mf-recovery.json:MarkFailed | 1/1 | - |
| F-008 | n8n-flows-real-v5/mf-recovery.json:AlertClaim | 1/1 | - |
| F-008 | n8n-flows-real-v5/mf-recovery.json:AlertBackoff | 1/1 | - |
| F-008 | n8n-flows-real-v5/mf-recovery.json:AlertMark | 1/1 | - |
| F-009 | n8n-flows-real-v5/mf-form.json:Receive | 1/3 | authentication, headerAuth |
| F-009 | n8n-flows-real-v5/mf-hook.json:Receive | 1/3 | authentication, headerAuth |
| F-009 | n8n-flows-film-v5/mf-form.json:Receive | 1/3 | authentication, headerAuth |
| F-009 | n8n-flows-film-v5/mf-hook.json:Receive | 1/3 | authentication, headerAuth |
| F-012 | n8n-flows-real-v5/mf-recovery.json:ClaimStuck | 3/3 | - |
| F-012 | n8n-flows-real-v5/mf-recovery.json:RunSub | 2/2 | - |
| F-012 | n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify | 4/4 | - |
| F-012 | n8n-flows-real-v5/mf-sub-crm-mail.json:CrmUpsert | 3/4 | timeout |
| F-012 | n8n-flows-film-v5/mf-sub-crm-mail.json:CrmUpsert | 4/4 | - |
| F-012 | n8n-mainframe/build_mainframe.py:27 | 1/1 | - |
| F-013 | n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify | 0/1 | unknown_model |
| F-013 | n8n-flows-real-v5/mf-sub-crm-mail.json:LabelOk | 2/2 | - |
| F-013 | n8n-flows-real-v5/mf-sub-crm-mail.json:OutStage | 1/2 | unknown |
| F-013 | n8n-mainframe/stage_server.py:50-51 | 3/3 | - |
| F-013 | PLAN-4-NLITE-FROM-LEAD.md:78-79 | 1/4 | deliberate, money-safe, single-flight |
| F-014 | n8n-flows-real-v5/mf-recovery.json:AlertSend | 1/4 | continueRegularOutput, 60, alert_attempts |
| F-014 | n8n-flows-real-v5/mf-recovery.json:AlertBackoff | 3/4 | DESK_ALERT_TO |
| F-014 | n8n-flows-real-v5/mf-recovery.json:AlertMark | 1/4 | DESK_ALERT_TO, 60, alert_attempts |
| F-014 | n8n-flows-real-v5/mf-recovery.json:AlertClaim | 3/3 | - |
| F-018 | n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify | 3/4 | MF_STAGE_URL |
| F-018 | n8n-flows-real-v5/mf-recovery.json:AlertSend | 2/2 | - |
| F-018 | n8n-flows-film-v5/mf-sub-crm-mail.json:Qualify | 2/3 | DESK_URL |
| F-019 | n8n-flows/desk-form-door.json:Send to the desk | 2/2 | - |
| F-019 | n8n-flows/desk-webhook-door.json:Send to the desk | 2/2 | - |
| F-019 | n8n-mainframe/stage_server.py:1-3 | 0/0 | - |
| F-021 | n8n-flows/desk-form-door.json:Send to the desk | 1/1 | - |
| F-021 | n8n-flows-real-v5/mf-sub-crm-mail.json:Qualify | 1/1 | - |
| F-029 | n8n-flows-real-v5/mf-sub-crm-mail.json:256-257 | 1/1 | - |
| F-029 | n8n-flows-real-v5/mf-recovery.json:177 | 1/1 | - |
| F-029 | n8n-flows-real-v5/mf-sub-crm-mail.json:103 | 1/1 | - |
| F-030 | n8n-flows-real-v5/mf-recovery.json:AlertSend | 2/2 | - |
| F-030 | n8n-flows-real-v5/mf-sub-crm-mail.json:SendMail | 2/2 | - |
| F-031 | n8n-flows-real-v5/mf-recovery.json:ClaimStuck | 5/5 | - |
| F-031 | n8n-flows-real-v5/mf-recovery.json:AlertClaim | 3/4 | 'review' |
