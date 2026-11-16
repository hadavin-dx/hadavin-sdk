# evidence-r10b (raw output, no judgement)

## Failures first: none of the commands below returned an unexpected exit; hostile inputs h1/h2 exit 1, h3 exit 4 (values recorded, not judged).

HEAD before: 2a0db27a39176ca79e7672f8205e91b23f497fe5; initial status: '?? fix-f8-r10b.md'
Note: a rm -rf of fresh dirs was blocked by the harness; dirs did not exist so it was skipped. Logs were kept in /tmp/ev10b-logs (not inside the run dirs).

### run_a
```
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 7 s
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
[take_check.sh exit=0] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
exit=0
```
### run_b
```
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 7 s
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
[take_check.sh exit=0] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
exit=0
```
### run_c
```
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 6 s
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
[take_check.sh exit=0] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
exit=0
```
### ttc
```
ok   control: exit 0, OVERRIDES line says none, pinned WARN count and the words 'known defects' are printed (got exit 0)
ok   B1a: --write-warn-pin on the pin in use is refused (exit 2) and leaves it unchanged (got exit 2)
ok   B1b: a clean run writes a NEW pin with date and sha256 and exits 4, not 0 (got exit 4)
ok   M-3: the written pin says it is not yet read and holds the placeholder line
ok   M-3: a pin whose header still has the placeholder is exit 4 (got exit 4)
ok   M-3: a pin with no 'reviewed by' line is exit 4 (got exit 4)
ok   B1b: the written pin, used as the pin, gives exit 0 (got exit 0)
ok   B1c: --write-warn-pin on an existing file is refused (exit 2) and leaves it unchanged (got exit 2)
ok   B1d: a run with a FAIL writes no pin and keeps exit 1 (got exit 1)
ok   B1e: a changed WARN set prints the difference, writes the new file, exits 4 (got exit 4)
ok   B1: the pin in use (take-warns.pin) is byte for byte unchanged by all cases above
ok   M-3: run saving off (unpatched folder) writes no pin, exit 4 (got exit 4)
ok   M-3: table file missing writes no pin, exit 4 (got exit 4)
ok   M-3: an environment override without the test flag writes no pin, exit 4 (got exit 4)
ok   M-3: key check absent writes no pin, exit 4 or 1 (got exit 1)
ok   M-2: the top block and the FINAL line print the combined sha256 of the four flow files (and one per file) (got exit 0)
ok   M-1: the output does not say 'deleted at clean-up'
ok   M1: TAKE_CHECK_WARN_PIN without the test flag is exit 4 and is named in the top block and the FINAL line (got exit 4)
ok   M1: TAKE_CHECK_FLOWS without the test flag is exit 4 and is printed (got exit 4)
ok   M1: TAKE_CHECK_DDL without the test flag is exit 4 and is printed (got exit 4)
ok   M1: TAKE_CHECK_CK without the test flag is exit 4 and is printed (got exit 4)
ok   M1: TAKE_CHECK_FORM_EXPECT without the test flag is exit 4 and is printed (got exit 4)
ok   M1: with the test flag the override is allowed but still printed (got exit 0)
ok   M3: a folder named mf-hook.json is a FAIL, exit 1 (got exit 1)
ok   M3: a dangling link named mf-recovery.json is a FAIL, exit 1 (got exit 1)
ok   M4: a pin header with a broken sha256 line is exit 4 (got exit 4)
ok   M4: a pin whose lines do not match its sha256 is exit 4 (got exit 4)
ok   M4: a pin without a date is exit 4 (got exit 4)
ok   M4: a pin with lines removed by hand is caught twice (hash and set) (got exit 4)
ok   count: mf-form.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
ok   count: mf-hook.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
test_take_check: 31 of 31 cases as expected, 0 not as expected
exit=0
```
### ruff
```
All checks passed!
ruff_check=0
```
### fmt
```
42 files already formatted
ruff_format=0
```
### bandit
```
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.18
Run started:2026-11-16 11:50:32.787064+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 4541
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
bandit=0
```
### secrets
```
PASS 0 hits in 1717 files
secrets=0
```
### h1
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
OVERRIDES: none
Flows folder checked: /tmp/ev10b/nonexistent (given with --flows)
sha256 of the four flow files checked (compare with the sha written down at re-pin; it is the sha256 of the four lines below, without the two leading spaces):
  combined: 7ad0374c9ea0cbccfa493d48d440c90c16d1c8a00736a5a95f900553703510d9 (at least one of the four files is MISSING)
  MISSING  mf-form.json
  MISSING  mf-hook.json
  MISSING  mf-recovery.json
  MISSING  mf-sub-crm-mail.json
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
Pinned WARN lines: 22 (pin dated 2026-11-16, reviewed by: flows-audit session, 2026-11-16, content read by that session only, lead to confirm, sha256 378e11212191edcb...). They stand for KNOWN DEFECTS and open decisions that a person read and accepted (for example: a missing answer to the caller when a step fails, steps that turn an error into normal-looking data, IF branches that lead nowhere, ids still to be filled). They are NOT fixed; exit 0 hides none of them.
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
  - WARN mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
  - WARN mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
  - WARN mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make thi
  - WARN mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIA
  - WARN mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
  - WARN-LEAD-DECISION mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - WARN-LEAD-DECISION mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - WARN-LEAD-DECISION mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make
  - WARN-LEAD-DECISION mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block
  + WARN accept-if --accept-if mf-recovery.json=AlertRow matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)
  + WARN accept-if --accept-if mf-recovery.json=StuckRow matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)
  + WARN accept-no-save --accept-no-save mf-recovery.json excused nothing: that flow was not found, or its run-saving settings are not off, or it is not a schedule-only flow, so this decision does nothing (file name wrong, or the settings changed)
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### /tmp/ev10b/nonexistent
FAIL /tmp/ev10b/nonexistent not a directory
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
Open items counted: checker known open problems 3 + psql gate 1 + problems of this script 5 (entry flows without the key check: 2, counted inside the problems).
FINAL: take_check exit status 1. Flow files sha256 (four files, combined): 7ad0374c9ea0cbccfa493d48d440c90c16d1c8a00736a5a95f900553703510d9 (at least one of the four files is MISSING). RESULT: 1 FAIL, 3 WARN. 22 pinned WARN lines stand for known defects that are not fixed. OVERRIDES: none. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 9. (1 = fault in a file, 4 = table check missing or failed, or a check of this script failed.) This is not a pass for filming.
h1=1
```
### h2
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_FLOWS=/tmp/x (NOT allowed outside tests: this script exits 4)
Flows folder checked: /tmp/x
sha256 of the four flow files checked (compare with the sha written down at re-pin; it is the sha256 of the four lines below, without the two leading spaces):
  combined: 7ad0374c9ea0cbccfa493d48d440c90c16d1c8a00736a5a95f900553703510d9 (at least one of the four files is MISSING)
  MISSING  mf-form.json
  MISSING  mf-hook.json
  MISSING  mf-recovery.json
  MISSING  mf-sub-crm-mail.json
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
Pinned WARN lines: 22 (pin dated 2026-11-16, reviewed by: flows-audit session, 2026-11-16, content read by that session only, lead to confirm, sha256 378e11212191edcb...). They stand for KNOWN DEFECTS and open decisions that a person read and accepted (for example: a missing answer to the caller when a step fails, steps that turn an error into normal-looking data, IF branches that lead nowhere, ids still to be filled). They are NOT fixed; exit 0 hides none of them.
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
  - WARN mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
  - WARN mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
  - WARN mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make thi
  - WARN mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIA
  - WARN mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
  - WARN-LEAD-DECISION mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - WARN-LEAD-DECISION mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - WARN-LEAD-DECISION mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make
  - WARN-LEAD-DECISION mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block
  + WARN accept-if --accept-if mf-recovery.json=AlertRow matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)
  + WARN accept-if --accept-if mf-recovery.json=StuckRow matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)
  + WARN accept-no-save --accept-no-save mf-recovery.json excused nothing: that flow was not found, or its run-saving settings are not off, or it is not a schedule-only flow, so this decision does nothing (file name wrong, or the settings changed)
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
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
FINAL: take_check exit status 1. Flow files sha256 (four files, combined): 7ad0374c9ea0cbccfa493d48d440c90c16d1c8a00736a5a95f900553703510d9 (at least one of the four files is MISSING). RESULT: 1 FAIL, 3 WARN. 22 pinned WARN lines stand for known defects that are not fixed. ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_FLOWS=/tmp/x (NOT allowed outside tests: this script exits 4). exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 10. (1 = fault in a file, 4 = table check missing or failed, or a check of this script failed.) This is not a pass for filming.
h2=1
```
### h3
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
OVERRIDES: none
Flows folder checked: demo/n8n-flows-real-v5
sha256 of the four flow files checked (compare with the sha written down at re-pin; it is the sha256 of the four lines below, without the two leading spaces):
  combined: b967e9d7cf2f4c636dda1f6d56cd9087fd61af1465a087c157ed79803649acb9
  74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8  mf-form.json
  305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de  mf-hook.json
  03c566bba549524b7bed0e787fdd46c4a01653450ef97691d14f4614357b0759  mf-recovery.json
  b3277363ae04b365459d902e5b5be099f1957126e3d48dbe42c47332cf53ff36  mf-sub-crm-mail.json
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
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
mf-hook.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 0 FAIL, 23 WARN. WARN lines that rest on an n8n rule nobody verified: 2.
Pinned WARN lines: 22 (pin dated 2026-11-16, reviewed by: flows-audit session, 2026-11-16, content read by that session only, lead to confirm, sha256 378e11212191edcb...). They stand for KNOWN DEFECTS and open decisions that a person read and accepted (for example: a missing answer to the caller when a step fails, steps that turn an error into normal-looking data, IF branches that lead nowhere, ids still to be filled). They are NOT fixed; exit 0 hides none of them.
!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a NEW pin file with: bash take_check.sh --write-warn-pin NEWFILE (the run then exits 4 on purpose; install the file by hand, see README). This script exits 4.
  - WARN mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-form.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' 
  + WARN mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - WARN mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-hook.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' 
  + WARN mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test wo
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### demo/n8n-flows-real-v5
WARN-LEAD-DECISION demo/n8n-flows-real-v5/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN demo/n8n-flows-real-v5/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [demo/n8n-flows-real-v5/mf-form.json] webhook Receive: 3 respondToWebhook node(s) reachable ['ReplyRan', 'ReplyReview', 'ReplyStored']; paths without a reply: none
WARN demo/n8n-flows-real-v5/mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN demo/n8n-flows-real-v5/mf-form.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION demo/n8n-flows-real-v5/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN demo/n8n-flows-real-v5/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [demo/n8n-flows-real-v5/mf-hook.json] webhook Receive: 3 respondToWebhook node(s) reachable ['ReplyRan', 'ReplyReview', 'ReplyStored']; paths without a reply: none
WARN demo/n8n-flows-real-v5/mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN demo/n8n-flows-real-v5/mf-hook.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION demo/n8n-flows-real-v5/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN demo/n8n-flows-real-v5/mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL_ID; ClaimStuck credential postgres id PG_CREDENTIAL_ID; MarkFailed credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN demo/n8n-flows-real-v5/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN demo/n8n-flows-real-v5/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
ACCEPTED: recovery flow not part of the take (decision 4): demo/n8n-flows-real-v5/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (the lead says it fires every 30 s, which this check did not read from the file; saved runs would pile up with lead keys and e-mails; the one video makes no recovery claim)
WARN demo/n8n-flows-real-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
WARN demo/n8n-flows-real-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): ClaimStuck postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkFailed postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertSend smtp mf-mail-smtp SMTP_CREDENTIAL_ID; AlertBackoff postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertMark postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION demo/n8n-flows-real-v5/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id PG_CREDENTIAL_ID; MarkUnknownB credential postgres id PG_CREDENTIAL_ID; SendMail credential smtp id SMTP_CREDENTIAL_ID; SetCrmId credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): CrmUpsert hubspotAppToken hubspot-app-token HS_CRED_PLACEHOLDER; SetCrmId postgres n8n-publish-pg PG_CREDENTIAL_ID; MailClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; SendMail smtp mf-mail-smtp SMTP_CREDENTIAL_ID; MarkDone postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownA postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownB postgres n8n-publish-pg PG_CREDENTIAL_ID
RESULT: 0 FAIL, 23 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
  - demo/n8n-flows-real-v5/mf-recovery.json: IF node StuckRow output(s) [1]
  - demo/n8n-flows-real-v5/mf-recovery.json: IF node AlertRow output(s) [1]
Run-saving left off by a recorded decision (--accept-no-save), recovery flow not part of the take (decision 4): 1
  - demo/n8n-flows-real-v5/mf-recovery.json: ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions']
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
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
SQL columns compared with the --ddl file: 14 query string(s) read.
SQL NOT COMPARED: query strings read but not compared (no table name could be read, for example only a {{ }} expression)=0; compared query strings whose {{ }} parts were blanked=0; table-file columns named like an SQL word (never compared)=0
SQL WARNS: column WARNs=0 table WARNs=0 postgres steps with no query text (not compared)=0
Known open problems: 17
  - demo/n8n-flows-real-v5/mf-form.json: webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
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
FINAL: take_check exit status 4. Flow files sha256 (four files, combined): b967e9d7cf2f4c636dda1f6d56cd9087fd61af1465a087c157ed79803649acb9. RESULT: 0 FAIL, 23 WARN. 22 pinned WARN lines stand for known defects that are not fixed. OVERRIDES: none. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 22. (1 = fault in a file, 4 = table check missing or failed, or a check of this script failed.) This is not a pass for filming.
h3=4
```
### cleanup
git status --short after: (empty for flow-check); git clean -n lists only 'handover/' (an empty untracked dir, not under raw/), so nothing removed; raw/selftest-output unchanged, no checkout needed.

### cleanup (actual)
HEAD at end: 1c49d4c3e7b59bf64029618e7ba6f94d4f76c6df (differs from start 2a0db27; another process committed meanwhile). Before cleanup 8 tracked files under raw/ were modified (nested-take-failure, take-check-form-run-saving-off, take-check-no-table-file, take-check-recovery-accept-idle, take-check-sub-run-saving-off, take-check-zero-queries, test-take-check, timing); restored with git checkout -- raw selftest-output (exit 0). Untracked evidence-r10b.md is this file. flow-check/handover/ (untracked, outside raw/) left alone. The earlier 'git status clean' line in the cleanup section above is superseded by this one.
