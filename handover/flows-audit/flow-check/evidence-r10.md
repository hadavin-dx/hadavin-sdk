# Evidence r10 (raw, no judgement)

## (1) `bash run_all.sh /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work` (cwd /home/user/hadavin-sdk/handover/flows-audit/flow-check)
exit code: 1
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd1.log (54 lines)
```
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 8 s
==== real-v5 (THE TAKE) ====
---- default mode must be exit 0; strict mode shows what the owner's two open decisions would do ----
[pristine]
######## pristine real
RESULT: 0 FAIL, 23 WARN
Known open problems: 17
exit=0
[patched]
######## patched real
RESULT: 0 FAIL, 22 WARN
Known open problems: 16
exit=0
[pristine-strict]
######## pristine-strict real
RESULT: 4 FAIL, 19 WARN
Known open problems: 13
exit=1
[patched-strict]
######## patched-strict real
RESULT: 4 FAIL, 18 WARN
Known open problems: 12
exit=1
[pristine-no-baseline] (information only: no excuse for the 2 IF gaps; exit 1 with 2 FAIL is expected)
RESULT: 2 FAIL, 23 WARN
exit=1
==== film-v5 (NOT FOR THE TAKE; shown only, not gating, not added to the real-v5 numbers) ====
[pristine-film]
######## pristine film
RESULT: 0 FAIL, 21 WARN
Known open problems: 15
exit=0
[patched-film]
######## patched film
RESULT: 0 FAIL, 20 WARN
Known open problems: 14
exit=0
[pristine-strict-film]
######## pristine-strict film
RESULT: 4 FAIL, 17 WARN
Known open problems: 11
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=0] missing lines: [take_check new-warn-changes-the-pin: want exit 4, the FINAL line with 4 and 'THE WARN SET CHANGED against take-warns.pin', got exit 4]
run_all exit status (real-v5 default runs + self-test): 1
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```

## (2) `bash test_take_check.sh` (cwd /home/user/hadavin-sdk/handover/flows-audit/flow-check)
exit code: 2
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd2.log (1 lines)
```
usage: bash test_take_check.sh PATCHED_REAL_DIR [SCRATCH_DIR]
```

## (3) `ruff check .` (cwd /home/user/hadavin-sdk/handover/flows-audit/flow-check/..)
exit code: 0
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd3.log (1 lines)
```
All checks passed!
```

## (4) `ruff format --check .` (cwd /home/user/hadavin-sdk/handover/flows-audit/flow-check/..)
exit code: 1
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd4.log (48 lines)
```
unformatted: File would be reformatted
   --> inputs/plan-wp6-resmoke-v5.md:193:1
    |
192 | import collections, re, sys
    - ours = {x.strip() for x in open(sys.argv[2]) if x.strip()}; ino = {}; out = collections.Counter(); dns = collections.Counter()
193 +
194 + ours = {x.strip() for x in open(sys.argv[2]) if x.strip()}
195 + ino = {}
196 + out = collections.Counter()
197 + dns = collections.Counter()
198 | LOOP = re.compile(r"^(127\.|\[::1\]|\[::ffff:127\.)")
199 | for line in open(sys.argv[1]):
200 |     if line.startswith("fd "):
    -         f = line.split() + [""]; ours.add(f[1]); ino.update({i: f[1] for i in f[2].split(",") if i}); continue
201 +         f = line.split() + [""]
202 +         ours.add(f[1])
203 +         ino.update({i: f[1] for i in f[2].split(",") if i})
204 +         continue
205 |     f = line.split()
    -     if line.startswith("@") or len(f) < 6: continue
206 +     if line.startswith("@") or len(f) < 6:
207 +         continue
208 |     peer = f[5]
    -     if peer.endswith(":*"): continue  # an unconnected UDP socket has no peer
    -     pids = set(re.findall(r"pid=(\d+)", line)); i = re.findall(r"ino:(\d+)", line)
    -     if i and i[0] in ino: pids.add(ino[i[0]])
209 +     if peer.endswith(":*"):
210 +         continue  # an unconnected UDP socket has no peer
211 +     pids = set(re.findall(r"pid=(\d+)", line))
212 +     i = re.findall(r"ino:(\d+)", line)
213 +     if i and i[0] in ino:
214 +         pids.add(ino[i[0]])
215 |     who = "ours" if pids & ours else ("other" if pids else "no-process")
216 |     k = (who, f[0], f[1], peer, ",".join(sorted(pids)))
    -     if peer.rsplit(":", 1)[-1] == "53": dns[k] += 1
    -     elif not LOOP.match(peer): out[k] += 1
217 +     if peer.rsplit(":", 1)[-1] == "53":
218 +         dns[k] += 1
219 +     elif not LOOP.match(peer):
220 +         out[k] += 1
221 | for name, cnt in (("NONLOOP", out), ("DNS", dns)):
    -     for k, n in sorted(cnt.items()): print(name, n, *k)
222 +     for k, n in sorted(cnt.items()):
223 +         print(name, n, *k)
224 | ```
    |

1 file would be reformatted, 418 files already formatted
```

## (5) `bandit -ll -r check_flows.py selftest.py` (cwd /home/user/hadavin-sdk/handover/flows-audit/flow-check)
exit code: 0
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd5.log (27 lines)
```
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.18
Run started:2026-11-16 11:40:07.523919+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 4423
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 1
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 1
		High: 0
Files skipped (0):
```

## (6) `python3 -I ../tools/check_secrets.py` (cwd /home/user/hadavin-sdk/handover/flows-audit/flow-check)
exit code: 0
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd6.log (1 lines)
```
PASS 0 hits in 1701 files
```

## (7) `sh handover/flows-audit/tools/check_patches.sh` (cwd /home/user/hadavin-sdk)
exit code: 0
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd7.log (1 lines)
```
PASS 4 patches
```

## (8) `bash take_check.sh` (cwd /home/user/hadavin-sdk/handover/flows-audit/flow-check)
exit code: 4
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd8.log (180 lines)
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
OVERRIDES: none
Flows folder checked: demo/n8n-flows-real-v5
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs demo/n8n-flows-v4/mf_leads.sql, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read AND compared: 14. Query strings read but NOT compared (no table name, only {{ }}): 0. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none saveManual=False
WARN demo/n8n-flows-real-v5/mf-form.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started wi
WARN demo/n8n-flows-real-v5/mf-hook.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started wi
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run st
ACCEPTED: recovery flow not part of the take (decision 4): demo/n8n-flows-real-v5/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (the lead says it fires every 30 s, which this check did not read from the file; 
!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4.
!!! RUN SAVING IS NOT EXACTLY all / all / True (successful runs, failed runs, runs started by hand) ON EVERY FLOW EXCEPT THE RECOVERY FLOW: the run list in n8n would be empty or undefined. Only the recovery flow (mf-recovery.json, ACCEPTED below) may differ. This script exits 4.
    mf-form.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=False
    mf-hook.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=False
    mf-sub-crm-mail.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=False
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - demo/n8n-flows-real-v5/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - demo/n8n-flows-real-v5/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - demo/n8n-flows-real-v5/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
[... cut ...]
  - demo/n8n-flows-real-v5/mf-form.json: webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - demo/n8n-flows-real-v5/mf-form.json: 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-form.json: this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
  - demo/n8n-flows-real-v5/mf-hook.json: webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - demo/n8n-flows-real-v5/mf-hook.json: webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - demo/n8n-flows-real-v5/mf-hook.json: 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-hook.json: this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
  - demo/n8n-flows-real-v5/mf-recovery.json: node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
  - demo/n8n-flows-real-v5/mf-recovery.json: 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL_ID; ClaimStuck credential postgres id PG_CREDENTIAL_ID; MarkFailed credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-recovery.json: 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-recovery.json: IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
  - demo/n8n-flows-real-v5/mf-recovery.json: IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json: node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json: 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id PG_CREDENTIAL_ID; MarkUnknownB credential postgres id PG_CREDENTIAL_ID; SendMail credential smtp id SMTP_CREDENTIAL_ID; SetCrmId credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json: 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json: this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
Not proven: that n8n accepts these files on import; what n8n really does when a step fails (for example whether a repeated lead key still gets its answer, and whether a failed step reaches the failure line: only a test run in n8n can show it); whether the SQL inside the postgres nodes is correct (only the column names are compared, and only with --ddl); who calls a web address, whether the flow is active, and test versus production web address; expression syntax beyond node names; secrets in a shape this scan does not list; every rule marked 'n8n rule UNVERIFIED' (webhook authentication values, credential kinds, retry limits, onError values, position of the error output, default responseMode, duplicate method+path or webhookId).
Passing this check does NOT mean the flows are ready to film.
Open items counted: checker known open problems 17 + psql gate 1 + problems of this script 4 (entry flows without the key check: 2, counted inside the problems).
FINAL: take_check exit status 4. RESULT: 0 FAIL, 23 WARN. 22 pinned WARN lines stand for known defects that are not fixed. OVERRIDES: none. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 22. (1 = fault in a file, 4 = table check missing or failed, or a check of this script failed.) This is not a pass for filming.
```

## (9) `bash take_check.sh --flows /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real` (cwd /home/user/hadavin-sdk/handover/flows-audit/flow-check)
exit code: 0
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd9.log (174 lines)
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
OVERRIDES: none
Flows folder checked: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real (given with --flows)
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs demo/n8n-flows-v4/mf_leads.sql, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read AND compared: 14. Query strings read but NOT compared (no table name, only {{ }}): 0. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (the lead says
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
[... cut ...]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-form.json: webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-form.json: webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-form.json: 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-form.json: patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-hook.json: webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-hook.json: webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-hook.json: 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-hook.json: patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json: node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json: 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL_ID; ClaimStuck credential postgres id PG_CREDENTIAL_ID; MarkFailed credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID [run with --require-real-credential-ids to make this a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json: 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json: IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-recovery.json: IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-sub-crm-mail.json: node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-sub-crm-mail.json: 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id PG_CREDENTIAL_ID; MarkUnknownB credential postgres id PG_CREDENTIAL_ID; SendMail credential smtp id SMTP_CREDENTIAL_ID; SetCrmId credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/work/g/real/mf-sub-crm-mail.json: 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
Not proven: that n8n accepts these files on import; what n8n really does when a step fails (for example whether a repeated lead key still gets its answer, and whether a failed step reaches the failure line: only a test run in n8n can show it); whether the SQL inside the postgres nodes is correct (only the column names are compared, and only with --ddl); who calls a web address, whether the flow is active, and test versus production web address; expression syntax beyond node names; secrets in a shape this scan does not list; every rule marked 'n8n rule UNVERIFIED' (webhook authentication values, credential kinds, retry limits, onError values, position of the error output, default responseMode, duplicate method+path or webhookId).
Passing this check does NOT mean the flows are ready to film.
Open items counted: checker known open problems 16 + psql gate 1 + problems of this script 0 (entry flows without the key check: 0, counted inside the problems).
FINAL: take_check exit status 0. RESULT: 0 FAIL, 22 WARN. 22 pinned WARN lines stand for known defects that are not fixed. OVERRIDES: none. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 17. (1 = fault in a file, 4 = table check missing or failed, or a check of this script failed.) This is not a pass for filming.
```

## (10) `TAKE_CHECK_FLOWS=/tmp/x bash take_check.sh` (cwd /home/user/hadavin-sdk/handover/flows-audit/flow-check)
exit code: 1
full output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev10/cmd10.log (84 lines)
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_FLOWS=/tmp/x (NOT allowed outside tests: this script exits 4)
Flows folder checked: /tmp/x
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs demo/n8n-flows-v4/mf_leads.sql, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read AND compared: 0. Query strings read but NOT compared (no table name, only {{ }}): 0. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
!!! 0 QUERY STRINGS WERE READ (or the count line is missing): NO column was compared. This script exits 4.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
WARN accept-no-save --accept-no-save mf-recovery.json excused nothing: that flow was not found, or its run-saving settings are not off, or it is not a schedule-only flow, so this decision does nothing (file name wrong, or the settings changed)
WARN accept-no-save --accept-no-save mf-recovery.json excused nothing: that flow was not found, or its run-saving settings are not off, or it is not a schedule-only flow, so this decision does nothing (file name wrong, or the settings changed)
!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4.
!!! RUN SAVING IS NOT EXACTLY all / all / True (successful runs, failed runs, runs started by hand) ON EVERY FLOW EXCEPT THE RECOVERY FLOW: the run list in n8n would be empty or undefined. Only the recovery flow (mf-recovery.json, ACCEPTED below) may differ. This script exits 4.
    no flow file found
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
mf-hook.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 0 webhook(s) without auth, 0 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 1 FAIL, 3 WARN. WARN lines that rest on an n8n rule nobody verified: 0.
Pinned WARN lines: 22 (pin dated 2026-11-16, sha256 378e11212191edcb...). They stand for KNOWN DEFECTS and open decisions that a person read and accepted (for example: a missing answer to the caller when a step fails, steps that turn an error into normal-looking data, IF branches that lead nowhere, ids still to be filled). They are NOT fixed; exit 0 hides none of them.
!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a NEW pin file with: bash take_check.sh --write-warn-pin NEWFILE (the run then exits 4 on purpose; install the file by hand, see README). This script exits 4.
  - WARN mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-crede
  - WARN mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
  - WARN mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - WARN mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-crede
  - WARN mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
  - WARN mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - WARN mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
  - WARN mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; Ale
  - WARN mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every
  - WARN mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every
  - WARN mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
[... cut ...]
### /tmp/x
FAIL /tmp/x file list [] != expected ['mf-form.json', 'mf-hook.json', 'mf-recovery.json', 'mf-sub-crm-mail.json']
WARN accept-if --accept-if mf-recovery.json=AlertRow matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)
WARN accept-if --accept-if mf-recovery.json=StuckRow matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)
WARN accept-no-save --accept-no-save mf-recovery.json excused nothing: that flow was not found, or its run-saving settings are not off, or it is not a schedule-only flow, so this decision does nothing (file name wrong, or the settings changed)
RESULT: 1 FAIL, 3 WARN
OPEN LEAD DECISIONS: 0 webhook(s) without auth, 0 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
SQL columns compared with the --ddl file: 0 query string(s) read.
SQL NOT COMPARED: query strings read but not compared (no table name could be read, for example only a {{ }} expression)=0; compared query strings whose {{ }} parts were blanked=0; table-file columns named like an SQL word (never compared)=0
SQL WARNS: column WARNs=0 table WARNs=0 postgres steps with no query text (not compared)=0
SQL COLUMNS NOT CHECKED: a --ddl file was given but 0 query strings were read, so NO column was compared (the checker reads only the 'query' setting of postgres steps).
Known open problems: 3
  - accept-if: --accept-if mf-recovery.json=AlertRow matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)
  - accept-if: --accept-if mf-recovery.json=StuckRow matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)
  - accept-no-save: --accept-no-save mf-recovery.json excused nothing: that flow was not found, or its run-saving settings are not off, or it is not a schedule-only flow, so this decision does nothing (file name wrong, or the settings changed)
Not proven: that n8n accepts these files on import; what n8n really does when a step fails (for example whether a repeated lead key still gets its answer, and whether a failed step reaches the failure line: only a test run in n8n can show it); whether the SQL inside the postgres nodes is correct (only the column names are compared, and only with --ddl); who calls a web address, whether the flow is active, and test versus production web address; expression syntax beyond node names; secrets in a shape this scan does not list; every rule marked 'n8n rule UNVERIFIED' (webhook authentication values, credential kinds, retry limits, onError values, position of the error output, default responseMode, duplicate method+path or webhookId).
Passing this check does NOT mean the flows are ready to film.
Open items counted: checker known open problems 3 + psql gate 1 + problems of this script 6 (entry flows without the key check: 2, counted inside the problems).
FINAL: take_check exit status 1. RESULT: 1 FAIL, 3 WARN. 22 pinned WARN lines stand for known defects that are not fixed. ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_FLOWS=/tmp/x (NOT allowed outside tests: this script exits 4). exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 10. (1 = fault in a file, 4 = table check missing or failed, or a check of this script failed.) This is not a pass for filming.
```

## cleanup + git status --short flow-check
```
 M flow-check/evidence-r10.md
 D flow-check/raw/take-check-bad-ddl.txt
 D flow-check/raw/take-check-disabled-send.txt
 D flow-check/raw/take-check-exit3.txt
 D flow-check/raw/take-check-filled.txt
 D flow-check/raw/take-check-form-run-saving-odd-word.txt
 D flow-check/raw/take-check-form-run-saving-off.txt
 D flow-check/raw/take-check-hook-run-saving-block-empty.txt
 D flow-check/raw/take-check-key-check-absent-is-exit-4.txt
 D flow-check/raw/take-check-keyok-gone.txt
 D flow-check/raw/take-check-new-warn-changes-the-pin.txt
 D flow-check/raw/take-check-no-table-file.txt
 D flow-check/raw/take-check-old-table.txt
 D flow-check/raw/take-check-recovery-accept-idle.txt
 D flow-check/raw/take-check-sub-run-saving-key-missing.txt
 D flow-check/raw/take-check-sub-run-saving-off.txt
 D flow-check/raw/take-check-unpatched-run-saving.txt
 D flow-check/raw/take-check-warn-pin-file-missing.txt
 D flow-check/raw/take-check-zero-queries.txt
```
