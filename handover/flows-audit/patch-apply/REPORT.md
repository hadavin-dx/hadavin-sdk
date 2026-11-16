Mon Nov 16 09:01:17 UTC 2026

# F4 patch-apply evidence (raw, no judgement)
Scratch: /tmp/pa13 (work = all patches in check_patches.sh order; base = unpatched; p-<name> = one patch alone). Checker: check_flows.py (stdlib, read-only).

## Commands
- mk copy of handover/demo/{n8n-flows/*.json,mf_leads.sql,PAGE-STATEMENTS-V4.md,VIDEO-RUNSHEET.md,n8n-mainframe/build_mainframe.py}; cd copy; git apply --check PATCH; git apply PATCH
- real: MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py OUT PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
- film: MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py OUT PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
- python3 -I check_flows.py DIR

## Apply and generator exit codes
```
## Baseline generator (unpatched)
gen real rc=0
gen film rc=0
## Combined, order of check_patches.sh
F-001-one-ddl check=0 apply=0
F-002-take-key-check-and-claim-error-path check=0 apply=0
F-003-runsheet-claims check=0 apply=0
F-004-page-statement-17 check=0 apply=0
F-008-save-runs-for-the-take check=0 apply=0
gen real rc=0
gen film rc=0
## Each alone
F-001-one-ddl check=0 apply=0
F-002-take-key-check-and-claim-error-path check=0 apply=0
gen real rc=0
gen film rc=0
F-003-runsheet-claims check=0 apply=0
F-004-page-statement-17 check=0 apply=0
F-008-save-runs-for-the-take check=0 apply=0
gen real rc=0
gen film rc=0
```

## Checker output and comparisons
```
### base/real
gen/base/real |mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/real |mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/real |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/real |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### base/film
gen/base/film |mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/film |mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/film |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/film |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### all/real
gen/all/real |mf-form.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/all/real |mf-hook.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/all/real |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/all/real |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
### all/film
gen/all/film |mf-form.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/all/film |mf-hook.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/all/film |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/all/film |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
### F-002-take-key-check-and-claim-error-path/real
gen/F-002-take-key-check-and-claim-error-path/real |mf-form.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/real |mf-hook.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/real |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/real |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### F-002-take-key-check-and-claim-error-path/film
gen/F-002-take-key-check-and-claim-error-path/film |mf-form.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/film |mf-hook.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/film |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/film |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### F-008-save-runs-for-the-take/real
gen/F-008-save-runs-for-the-take/real |mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/F-008-save-runs-for-the-take/real |mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/F-008-save-runs-for-the-take/real |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-008-save-runs-for-the-take/real |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
### F-008-save-runs-for-the-take/film
gen/F-008-save-runs-for-the-take/film |mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/F-008-save-runs-for-the-take/film |mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/F-008-save-runs-for-the-take/film |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-008-save-runs-for-the-take/film |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
### saved real-v5
/home/user/hadavin-sdk/handover/demo/n8n-flows-real-v5 | file=mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-real-v5 | file=mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-real-v5 | file=mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-real-v5 | file=mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### saved film-v5
/home/user/hadavin-sdk/handover/demo/n8n-flows-film-v5 | file=mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-film-v5 | file=mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-film-v5 | file=mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-film-v5 | file=mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### diff base vs saved
real/mf-form identical
real/mf-hook identical
real/mf-recovery identical
real/mf-sub-crm-mail identical
film/mf-form identical
film/mf-hook identical
film/mf-recovery identical
film/mf-sub-crm-mail identical
### diff base vs all (lines)
200
200
### patched generator diffs
-- all/real
diff -r gen/base/real/mf-form.json gen/all/real/mf-form.json
diff -r gen/base/real/mf-hook.json gen/all/real/mf-hook.json
diff -r gen/base/real/mf-sub-crm-mail.json gen/all/real/mf-sub-crm-mail.json
-- all/film
diff -r gen/base/film/mf-form.json gen/all/film/mf-form.json
diff -r gen/base/film/mf-hook.json gen/all/film/mf-hook.json
diff -r gen/base/film/mf-sub-crm-mail.json gen/all/film/mf-sub-crm-mail.json
-- F-002-take-key-check-and-claim-error-path/real
diff -r gen/base/real/mf-form.json gen/F-002-take-key-check-and-claim-error-path/real/mf-form.json
diff -r gen/base/real/mf-hook.json gen/F-002-take-key-check-and-claim-error-path/real/mf-hook.json
-- F-002-take-key-check-and-claim-error-path/film
diff -r gen/base/film/mf-form.json gen/F-002-take-key-check-and-claim-error-path/film/mf-form.json
diff -r gen/base/film/mf-hook.json gen/F-002-take-key-check-and-claim-error-path/film/mf-hook.json
-- F-008-save-runs-for-the-take/real
diff -r gen/base/real/mf-form.json gen/F-008-save-runs-for-the-take/real/mf-form.json
diff -r gen/base/real/mf-hook.json gen/F-008-save-runs-for-the-take/real/mf-hook.json
diff -r gen/base/real/mf-sub-crm-mail.json gen/F-008-save-runs-for-the-take/real/mf-sub-crm-mail.json
-- F-008-save-runs-for-the-take/film
diff -r gen/base/film/mf-form.json gen/F-008-save-runs-for-the-take/film/mf-form.json
diff -r gen/base/film/mf-hook.json gen/F-008-save-runs-for-the-take/film/mf-hook.json
diff -r gen/base/film/mf-sub-crm-mail.json gen/F-008-save-runs-for-the-take/film/mf-sub-crm-mail.json
```

## Extra checks (raw results)
- F-002 (all and alone, real and film): KeyOk, ReplyBadKey, ReplyStoreFail exist in mf-form and mf-hook. Links: Valid->KeyOk; KeyOk out0->Claim, out1->ReplyBadKey; Claim out0->Claimed, out1->ReplyStoreFail. Nodes 12 -> 15, connections 11 -> 14. mf-recovery and mf-sub-crm-mail byte-identical to baseline.
- F-008 (all and alone): saveDataSuccessExecution and saveDataErrorExecution = all in mf-form, mf-hook, mf-sub-crm-mail; mf-recovery = none, and equals the saved real-v5 recovery as parsed JSON. Node and connection counts unchanged (12/12/10/20).
- Unpatched generator output is byte-identical (cmp) to saved real-v5 and film-v5 for all 4 files each (8 of 8). No difference.
- F-001: CREATE TABLE text in patched mf_leads.sql contains alert_sent, alert_token, alert_until, alert_attempts (lines 14-17 of the table block).
- F-003, F-004, F-001, build_mainframe.py: 0 conflict markers, strict UTF-8 read ok, no .orig/.rej files; patched build_mainframe.py py_compile ok.
- Orphan rule in checker: node never targeted by a connection and whose type does not contain "trigger" or "webhook".


---
# Round 2 (09:05 UTC, Mon Nov 16 2026, from `date -u`)
Fixes the defects in review-codebase-r1.md (R1 to R10) and the design review (R1 to R11). Nothing was run in n8n. Scratch: /tmp/pa13b (fresh copies per order). Full raw output of the run: `raw-round2.txt` (679 lines). The script that made it: `run-round2.sh`. Negative tests of the checker: `checker-negative-tests.py` and `negative-output/`.
Honest notes first: the F-002-alone and F-008-alone rows below reuse the round-1 generator output in /tmp/pa13/gen (same patches, not regenerated). The old "diff base vs all: 200 / 200" line cannot be re-derived: the command was not saved; it was a line count of some diff output, so it proved nothing and is replaced by the labelled counts in section 8.

## 1 to 3 Checker rewritten (check_flows.py, run with `python3 -I`, exit code taken directly)
Changes: trigger = exact types (webhook, executeWorkflowTrigger, formTrigger, any type ending in `Trigger`); respondToWebhook is no longer exempt (R1 fixed). Reachability from the triggers over all connection outputs (R2). At least one trigger per file. Exit 1 on: parse failure, missing name or type, duplicate name, dangling source or target, orphan, unreachable node, count mismatch, wrong file list (exactly the four mf-*.json), onError=continueErrorOutput without a target on main[1], IF node without both outputs (WARN only when the baseline lacks the same output, with `--baseline`), `$('X')` or `$node["X"]` naming no node of the same file. Prints the node types with typeVersion counts and every placeholder or `$env.*` token per file with the nodes that hold it. The docstring now describes what the code does (R10).
Expected counts are given by the caller: `--expect mf-form.json=12:11` (nodes:connections). Baseline numbers were checked by the checker on the generated unpatched output, not trusted from the brief: mf-form 12/11, mf-hook 12/11, mf-recovery 10/9, mf-sub-crm-mail 20/26 (brief was right); after F-002 mf-form and mf-hook 15/14 (right).
Negative tests (15 mutants of the patched mf-form.json plus a missing file etc., run through the same command): every one exits 1. Cases: unwired ReplyStored (respondToWebhook orphan), self-loop, two nodes that only point at each other (cycle_only: "unreachable from any trigger ['CycA','CycB']"), missing error link, IF with one branch, `$('Nope')`, no trigger, dangling target, missing name, wrong count, unparsable file, missing file, wrong saveData value, an unexplained change of node Stored. See `negative-output/*.out`. (One mutant, unreach_pair, is not really unreachable; it was caught only by the count and diff checks. The cycle_only case is the true test.)

## 4 F-002 and F-008 assertions (`--patch-checks F002,F008`) and the real node diff
In every patched directory (real and film, all four orders): KeyOk, ReplyBadKey, ReplyStoreFail exist in mf-form and mf-hook only; links Valid->KeyOk, KeyOk out0->Claim, out1->ReplyBadKey, Claim out0->Claimed, out1->ReplyStoreFail all hold; Claim onError=continueErrorOutput, alwaysOutputData=False; saveData success and error = all in mf-form, mf-hook, mf-sub-crm-mail and none in mf-recovery. Printed values (identical in mf-form and mf-hook):
- KeyOk IF condition: `={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}` (boolean, true)
- ReplyBadKey: status 422, body `{ n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 letters, digits, - or _)' }`
- ReplyStoreFail: status 503, body `{ n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' }`
- Valid lead_key assignment: `String($json.lead_key || '')`
Diff of patched vs unpatched generator output, `--diff-base ... --allow F002,F008` exit 0, saved in `diff-base-vs-patched.txt`: ADDED KeyOk, ReplyBadKey, ReplyStoreFail (mf-form, mf-hook); CHANGED Claim (keys alwaysOutputData, onError); CHANGED Valid (only parameters.assignments.assignments[lead_key].value); connections CHANGED for sources Valid, KeyOk, Claim; settings saveDataSuccessExecution and saveDataErrorExecution none -> all (mf-form, mf-hook, mf-sub-crm-mail). mf-recovery: no difference. Anything else makes the script exit 1 (negative test extra_change proves it).
NEW FINDING (read it): in the UNPATCHED generator output Claim has alwaysOutputData=True (baseline and Stored both True). The F-002 patch turns Claim to False. So the patch removes the mechanism the unpatched flow used to give a repeat key an (empty) item that goes to Claimed -> false -> Stored -> ReplyStored. See section 7.

## 5 Other patch orders (each on a fresh copy; git apply --check then git apply; generator real + film)
Where the plan's order is written: FIX-PLAN.md (parent folder) numbers the fixes F-001 (item 1), F-002 (item 2), F-008 (item 4), F-003 and F-004 (item 7). tools/check_patches.sh applies `"$P"/*.patch` in shell glob (alphabetical) order, each on its own scratch copy, never combined: F-001, F-002, F-003, F-004, F-008. Round 1 used the glob order; the FIX-PLAN item order (F-001, F-002, F-008, F-003, F-004) was not run; the four orders below were.
| order | apply (check, apply) | generator real, film | checker real, film |
|---|---|---|---|
| plan/glob: F-001, 002, 003, 004, 008 | all 0, 0 | 0, 0 | exit 0, exit 0 |
| reverse: 008, 004, 003, 002, 001 | all 0, 0 | 0, 0 | exit 0, exit 0 |
| F-002 then F-008 | 0, 0 | 0, 0 | exit 0, exit 0 |
| F-008 then F-002 | 0, 0 | 0, 0 | exit 0, exit 0 |
| F-002 alone (round-1 output) | 0, 0 | 0, 0 | exit 0 (real), exit 0 (film) |
| F-008 alone (round-1 output) | 0, 0 | 0, 0 | exit 0 (real), exit 0 (film) |
No .orig or .rej file left. `cmp` of the generated JSON: reverse order equals plan order for all 8 files (real and film); F-002+F-008 and F-008+F-002 equal the plan order for mf-form and mf-hook (real, film). Unpatched generator output equals the saved real-v5 and film-v5 byte for byte: 8 of 8 identical (cmp). Checker WARNs in every run (same in the baseline, so not caused by a patch): IF nodes StuckRow and AlertRow in mf-recovery have no output 1 (the false branch). By design they look like "no work, stop"; nobody wired the false branch. Not a defect found in the patches; flagged as asked.

## 6 F-001 SQL (text check only)
Command: `grep -n "alert_sent\|alert_token\|alert_until\|alert_attempts" mf_leads.sql` on the patched file: line 1 (note), line 15 (comment), lines 16 to 19 are the four column definitions in CREATE TABLE mf_leads: alert_sent boolean NOT NULL DEFAULT false, alert_token text, alert_until timestamptz, alert_attempts int NOT NULL DEFAULT 0.
Flow SQL that names alert columns (patched generator output, real and film identical): mf-recovery nodes AlertClaim (alert_sent, alert_token, alert_until, alert_attempts), AlertBackoff (all four), AlertMark (alert_sent, alert_token). mf-form, mf-hook, mf-sub-crm-mail: none. Every alert column those statements mention is declared in the patched CREATE TABLE. This is a text comparison only; no SQL parser, no Postgres. Column types and the DEFAULTs were not compared with the statements' casts.
The ALTER statement in the patch comment (extracted, NOT run, not parsed by Postgres): `ALTER TABLE mf_leads ADD COLUMN alert_sent boolean NOT NULL DEFAULT false, ADD COLUMN alert_token text, ADD COLUMN alert_until timestamptz, ADD COLUMN alert_attempts int NOT NULL DEFAULT 0`.

## 7 NOT TESTED (said plainly)
- Running or importing any file into n8n: NOT done. Parameters of the new nodes are only read as text.
- Credentials and ids: PG_CREDENTIAL_ID, SMTP_CREDENTIAL_ID, SUB_WORKFLOW_ID (and HS_CRED in the real variant, `$env.DESK_ALERT_TO`, `$env.DESK_URL`, `$env.DESK_TIMEOUT_MS`) are still placeholders in the generated files; the lead must replace them at import. Per-file lists are in raw-round2.txt. The film variant has no HS placeholder because it was generated without the sixth argument (the film flows use an HTTP call, not the HubSpot node); film vs real were not compared node by node.
- Error-output semantics and alwaysOutputData in n8n: NOT tested. F-002 repeat-key reply NOT tested. The unpatched flow has Claim alwaysOutputData=True; the F-002 patch sets it to False together with onError=continueErrorOutput. If n8n emits no item for an `INSERT ... ON CONFLICT DO NOTHING RETURNING` that matches no row (the generator comment says the Postgres node returns one {success: true} item for a non-SELECT that matches no row, from the n8n source, but that was not run), a REPEAT lead key gets NO reply and the webhook call hangs. The patch comment says test T19 must show a repeat key still gets its answer. This is UNPROVEN either way; the patch must not be relied on before T19 passes.
- Postgres execution of the DDL and of the ALTER: NOT done.
- F-003 and F-004 content (run sheet claims, page statement 17): only applied (git apply exit 0, no conflict markers, UTF-8 reads); the new text was not compared with the audit findings.
- F-008 side effects, not examined or not fixed by this patch: (a) failures of the recovery flow are not saved (mf-recovery stays none); (b) runs of the sub-workflow started by RunSub are saved with "all" and carry e-mail and lead keys (made-up data only); (c) the saved folders n8n-flows-real-v5 and n8n-flows-film-v5 stay at "none" because only the generator changes: the lead must regenerate and import from the new output; (d) an n8n server environment override of the save settings was not examined.
- Canvas layout: KeyOk at [550, 0] sits 110 px from Claim at [660, 0]; cramped (the patch did not move Claim). Not rendered or looked at.
- Patch order from FIX-PLAN item order (F-001, F-002, F-008, F-003, F-004) was not run; four other orders were.

## 8 Labelled diff numbers (replaces "200 / 200")
`diff -r base plan` (unpatched generator output vs all five patches, plan order), normal diff format line counts, same for real and film:
- mf-form.json: differs, 108 lines. mf-hook.json: differs, 108 lines. mf-sub-crm-mail.json: differs, 6 lines (the two saveData settings). mf-recovery.json: identical. Whole `diff -r`: 225 lines (includes the 3 "diff -r" header lines).
- Node-level meaning of these lines: section 4 and diff-base-vs-patched.txt.
