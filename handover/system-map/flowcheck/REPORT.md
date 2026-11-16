# FLOWCHECK REPORT (ORDER 011 item 1): patch and flow-graph check of the flows audit
Written by system-map, 2026-11-16. STATUS: round 1 of review fixed; round 2 pending (see section 8). Read-only on cloud/flows-audit (commit 7fd00a7a at the time of the first fetch); nothing there was edited. Words used: a *flow* is one n8n workflow file; *webhook* is the address a sender posts a lead to; *onError* is what a step does when it fails (default: the whole run stops); *the generator* is the program `build_mainframe.py` that writes the flow files.

## 1. Failures first
| # | what | where | how sure |
|---|---|---|---|
| 1 | Anyone who can reach the form address can send a lead: the webhook step `Receive` in the form flow and the e-mail-style flow asks for no password or key (no `authentication` setting). This is true in real-v5 and film-v5, before and after the patches. Patch F-002 adds a check that the lead key has a valid shape; that is not a login. None of the five patches adds a password or key. Same hole as L7-FD-005 in SWEEP.md (fix-plan row 19). | mf-form.json, mf-hook.json, step `Receive` | CONFIRMED by the checker on all 32 built files |
| 2 | NOT TESTED: whether n8n accepts what patch F-002 adds (a key check, and replies with error codes 422 and 503), and what n8n does on a database write that matches no row. With `Claim` set to not output on an empty result, a lead sent twice relies on n8n returning one item for an insert that stored nothing; the generator comment says it does, the graph check cannot show it, and the patch itself names test T-F002b for it. n8n is not installed here and the program's own tests (mf.py T17, T18 and the ones the patches imply) were not run. Next step: import the patched files into a throwaway n8n and run those tests. | F-002 | NOT VERIFIED |
| 3 | Two fixes proposed by the audit (F-002 key check and error replies; F-008 keep run records for the take) are written as edits to the generator, not to the flow files. The flow files that n8n imports (`n8n-flows-real-v5`, `n8n-flows-film-v5`) do not change until someone runs the generator again and commits the result. I checked by applying the edits to a copy and running the generator; the committed files are unchanged by the patches themselves. ("n8n imports the JSON files, not the generator" is from the V5-README, which I read but is not part of the saved evidence.) | F-002, F-008 | CONFIRMED (evidence/dry-run.txt, build.txt) |
| 4 | The F-002 reply fix covers one step only. In the patched form flow `Claim` gets an error reply (503). `Stored` (database read) and `RunSub` (call of the sub-workflow) keep the default stop and no reply: a failure there leaves the sender without an answer, the same gap F-002 closes for `Claim`. The new WARN line of the checker shows it (2 warnings per patched entry flow, 3 before). Read from the file, not run in n8n. | patched mf-form, mf-hook | CONFIRMED in the file |
| 5 | Path note. The order says `handover/demo/n8n-flows-real-v5` and `film-v5`; the second folder is really `handover/demo/n8n-flows-film-v5`. Both exist only on origin/cloud/flows-audit (and origin/demo/handover), not on cloud/system-map. The older folder `handover/demo3/kill/flows-go1/` in this checkout is a different version: byte comparison of its four flow files with real-v5 and film-v5 says "differs" for all 8 pairs (evidence/go1.txt). | paths | CONFIRMED |

What passed: all five patches apply without a rejected hunk and none leaves a broken graph (evidence/dry-run.txt); the unpatched generator reproduces the committed v5 folders byte for byte (evidence/repro.txt); parse, duplicate names, connection targets, orphans, unreachable steps and `$('Name')` references show no failure in any of the 32 built files (the only failure line is item 1).

## 2. Rung table (rule 20, CODE-LAST)
Evidence for the linter rows is ONE web search on 2026-11-16 read from its result summaries; no linter was opened, installed or run, no licence read. Repository search for rung 1: `grep -ril "n8n.*lint\|workflow.*lint" handover` found nothing relevant (command not saved as evidence).
| component | need | rung tried | evidence (source, date) | what only our code gives | verdict |
|---|---|---|---|---|---|
| orphan, dead node, open webhook, missing retry | list failures | rung 1 (this repository): nothing found. Rung 3/4: third-party linters lorenzespinosa/n8n-lint, Waqas-Ai-Engineer/n8n-workflow-doctor, SMillerDev/n8n-workflow-linter, vladosskins178/n8n-workflow-lint, tachyurgy/n8n-workflow-lint, ubie-oss/n8n-cli | UNVERIFIED: search summary 2026-11-16, not run | nothing proven | CUT-TO-CONFIG+GLUE once one of them is run offline on the 32 files and passes; until then our script does it |
| `$('Name')` references, error output wired, the F-002 combination, upstream calls of a mail or CRM write, default stop on a reply path, pristine against patched | list failures and warnings | same tools | UNVERIFIED claim from the summaries that they lack these | the pristine-against-patched comparison for this audit | KEEP-CODE as one thin script (`tools/flowcheck.py`, 152 lines, standard library, no network); re-decide after one linter is run on the 32 files |
| real validity (does n8n import and run it) | prove the patch works | rung 3: n8n itself | none: n8n not installed | nothing | NOT DONE (item 2 of section 1) |
Why not install one now: not tried, not forbidden; a licence and a run on made-up data come first.

## 3. What was done
1. Copied the 4 flow files of each v5 folder and the 5 patches from origin/cloud/flows-audit into `in/`.
2. F-002 and F-008 edit the generator, so the patched flow files were produced by applying the patch to a scratch copy and running the generator with the commands of the V5-README. F-001 (SQL), F-003 and F-004 (Markdown) change no flow file; they were only checked to apply, and their text was not judged. The graph check says nothing about whether the SQL columns of F-001 match the queries in the steps.
3. `run_all.sh OUTDIR` (OUTDIR under /tmp) rebuilds everything from git in one run. Evidence was produced by that script (author) and re-run by a separate evidence runner (`evidence-runner.md`): all 7 comparisons were empty, 8 of 8 hostile inputs ran (2 crashes found, fixed in section 8), 4 of 4 mutants of the checker were caught by its self-test.

## 4. Results
- Patch dry run, each patch alone against the unpatched files: all 5 print "checking file", rc=0, no rejected hunk. In the order F-002 then F-008, F-008 hunk 2 moves by 4 lines; in the order F-008 then F-002, F-002 hunks 1 and 2 move by 3 lines; no failure either way and the generator file is identical.
- 32 flow files were built and checked (4 files x 2 sets x 4 states: unpatched, F-002 only, F-008 only, both); the table shows the unpatched and the both-patches state (16 rows); the others are in evidence/md/. The checker exits 1 on every set because of item 1.

### Table per flow file
| file | state | nodes | connections | save ok/error | failures | warnings |
|---|---|---|---|---|---|---|
| real-v5/mf-form | before | 12 | 11 | none/none | Receive: no password or key on the form entry point | 3 |
| real-v5/mf-form | after F-002 + F-008 | 15 | 14 | all/all | Receive: no password or key on the form entry point | 2 |
| real-v5/mf-hook | before | 12 | 11 | none/none | Receive: no password or key on the form entry point | 3 |
| real-v5/mf-hook | after F-002 + F-008 | 15 | 14 | all/all | Receive: no password or key on the form entry point | 2 |
| real-v5/mf-recovery | before | 10 | 9 | none/none | none | 1 |
| real-v5/mf-recovery | after F-002 + F-008 | 10 | 9 | none/none | none | 1 |
| real-v5/mf-sub-crm-mail | before | 20 | 26 | none/none | none | 0 |
| real-v5/mf-sub-crm-mail | after F-002 + F-008 | 20 | 26 | all/all | none | 0 |
| film-v5/mf-form | before | 12 | 11 | none/none | Receive: no password or key on the form entry point | 3 |
| film-v5/mf-form | after F-002 + F-008 | 15 | 14 | all/all | Receive: no password or key on the form entry point | 2 |
| film-v5/mf-hook | before | 12 | 11 | none/none | Receive: no password or key on the form entry point | 3 |
| film-v5/mf-hook | after F-002 + F-008 | 15 | 14 | all/all | Receive: no password or key on the form entry point | 2 |
| film-v5/mf-recovery | before | 10 | 9 | none/none | none | 1 |
| film-v5/mf-recovery | after F-002 + F-008 | 10 | 9 | none/none | none | 1 |
| film-v5/mf-sub-crm-mail | before | 20 | 26 | none/none | none | 0 |
| film-v5/mf-sub-crm-mail | after F-002 + F-008 | 20 | 26 | all/all | none | 0 |

Real-v5 and film-v5 give the same result in every row (they differ in the HubSpot step and in the names of the environment settings).

### What the patches change in the graph
- Entry flows (form and e-mail-style): +3 steps (12 to 15), +3 connections (11 to 14): `KeyOk` (a yes/no step), `ReplyBadKey` (answer 422), `ReplyStoreFail` (answer 503). `Claim` changes from "always output, default stop" to "no output on an empty result, continue on error" and its error output is wired to `ReplyStoreFail`. The F-002 combination (always output together with continue-on-error) is clean in all 32 files, the unpatched ones too, so that flag only shows the patch does not introduce it; the real defect the patch fixes (no error path and no reply on `Claim`) is not what that flag looks for, and is shown by the WARN line instead.
- F-008: saved runs go from none to all in the form flow, the e-mail-style flow and the sub-workflow; the recovery flow stays at none (it fires every 30 s). A saved run holds the lead key, e-mail and name (made-up data only in the take). Manual runs stay unsaved.

### Error settings of the steps
Real-v5, committed files, one table per file (the same tables for all states and for film-v5 are in evidence/md/). Columns: what the step does on error, retry, whether it outputs an item on an empty result, and the checker's flag.

**real-v5/mf-form** (committed files, before the patches)

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Receive | webhook | (default: stop) | no | no | - |
| Item | set | (default: stop) | no | no | - |
| Valid | set | (default: stop) | no | no | - |
| Claim | postgres | (default: stop) | no | yes | - |
| Claimed | if | (default: stop) | no | no | - |
| IsProcessing | if | (default: stop) | no | no | - |
| SubInput | set | (default: stop) | no | no | - |
| RunSub | executeWorkflow | (default: stop) | no | no | - |
| ReplyRan | respondToWebhook | (default: stop) | no | no | - |
| ReplyReview | respondToWebhook | (default: stop) | no | no | - |
| Stored | postgres | (default: stop) | no | yes | - |
| ReplyStored | respondToWebhook | (default: stop) | no | no | - |

**real-v5/mf-hook** (committed files, before the patches)

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Receive | webhook | (default: stop) | no | no | - |
| Item | set | (default: stop) | no | no | - |
| Valid | set | (default: stop) | no | no | - |
| Claim | postgres | (default: stop) | no | yes | - |
| Claimed | if | (default: stop) | no | no | - |
| IsProcessing | if | (default: stop) | no | no | - |
| SubInput | set | (default: stop) | no | no | - |
| RunSub | executeWorkflow | (default: stop) | no | no | - |
| ReplyRan | respondToWebhook | (default: stop) | no | no | - |
| ReplyReview | respondToWebhook | (default: stop) | no | no | - |
| Stored | postgres | (default: stop) | no | yes | - |
| ReplyStored | respondToWebhook | (default: stop) | no | no | - |

**real-v5/mf-recovery** (committed files, before the patches)

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Every30s | scheduleTrigger | (default: stop) | no | no | - |
| ClaimStuck | postgres | continueRegularOutput | no | no | - |
| StuckRow | if | (default: stop) | no | no | - |
| RunSub | executeWorkflow | continueRegularOutput | no | no | - |
| MarkFailed | postgres | continueRegularOutput | no | no | - |
| AlertClaim | postgres | continueRegularOutput | no | no | - |
| AlertRow | if | (default: stop) | no | no | - |
| AlertSend | emailSend | continueErrorOutput | no | no | - |
| AlertBackoff | postgres | continueRegularOutput | no | no | - |
| AlertMark | postgres | continueRegularOutput | no | no | - |

**real-v5/mf-sub-crm-mail** (committed files, before the patches)

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| SubIn | executeWorkflowTrigger | (default: stop) | no | no | - |
| Qualify | httpRequest | continueErrorOutput | yes x2 | no | - |
| LabelOk | if | (default: stop) | no | no | - |
| CrmUpsert | hubspot | continueErrorOutput | yes x2 | no | - |
| SetCrmId | postgres | (default: stop) | no | yes | - |
| CrmIdOk | if | (default: stop) | no | no | - |
| OwnsClaim1 | if | (default: stop) | no | no | - |
| MailClaim | postgres | (default: stop) | no | yes | - |
| MailRowBack | if | (default: stop) | no | no | - |
| SendMail | emailSend | continueErrorOutput | no | no | - |
| MarkDone | postgres | (default: stop) | no | yes | - |
| MarkUnknownA | postgres | (default: stop) | no | yes | - |
| MarkUnknownB | postgres | (default: stop) | no | yes | - |
| UnknownNewA | if | (default: stop) | no | no | - |
| UnknownNew | if | (default: stop) | no | no | - |
| DoneOwned | if | (default: stop) | no | no | - |
| OutDone | set | (default: stop) | no | no | - |
| OutUnknown | set | (default: stop) | no | no | - |
| OutStage | set | (default: stop) | no | no | - |
| OutLost | set | (default: stop) | no | no | - |

Reading these tables (not computed beyond the flags):
- Calls with continue-on-error and retry x2: `Qualify` (HTTP call to the desk), `CrmUpsert` (HubSpot). Their error outputs are wired in every file.
- `SendMail`: continue-on-error, no retry (by design).
- Database steps in the entry flows and the sub-workflow: default stop, output on an empty result (`Claim`, in the unpatched files only). Default stop means an error stops the run before the mail (read from the file, not run in n8n).
- Recovery flow: six steps continue on error: `ClaimStuck`, `RunSub`, `MarkFailed`, `AlertClaim`, `AlertBackoff`, `AlertMark`. `AlertSend` continues on its error output, wired to `AlertBackoff`.
- No step has "always output" together with "continue on error output" in any of the 32 files.

### Steps with no safe error path before a mail or CRM write (computed by the checker, WARN lines)
Mail or CRM write = `SendMail`, `AlertSend`, `CrmUpsert` (the plain HTTP call `Qualify` to the desk is not a write). Result in every one of the 32 files: one WARN, in the recovery flow only: `AlertSend` has `AlertClaim` upstream, which continues on error. The `AlertRow` yes/no step guards it (read from the generator comment, not run). `SendMail` has `CrmUpsert` and `Qualify` upstream (continue on error, error outputs wired) and `MailClaim`, `SetCrmId` (default stop). `CrmUpsert` has `Qualify` upstream.

### Environment settings read, credentials, run saving
- Environment settings read with `$env`: real-v5: DESK_URL and DESK_TIMEOUT_MS (`Qualify`), DESK_ALERT_TO (`AlertSend`). film-v5: MF_STAGE_URL and MF_STAGE_TIMEOUT_MS (`Qualify`), MF_CRM_URL (`CrmUpsert`); film-v5 recovery reads none. These are names read from the committed files. No secret is read through `$env`.
- Credentials by step type: postgres name `n8n-publish-pg`: 2 steps in the form flow, 2 in the e-mail-style flow, 5 in the recovery flow, 5 in the sub-workflow, one shared identity everywhere (SWEEP.md fix-plan row 20); smtp name `mf-mail-smtp` on `SendMail` and `AlertSend`; hubspotAppToken name `hubspot-app-token` on `CrmUpsert` (real-v5 only). Ids are placeholders (PG_CREDENTIAL_ID and others).
- No error workflow (`errorWorkflow`) is set in any of the 32 files.

## 5. Patches that do not apply or leave a broken graph
None. See "What passed" in section 1, and item 2 for what is not tested.

## 6. What the checker cannot see (script header)
`$node["X"]` and `$items("X")` references (a search of in/ finds none), computed `$env` keys, a header-auth setting with no credential attached, disabled steps, trigger types outside its name pattern, and n8n's own parameter rules. The self-test covers 7 failure kinds, the two crash cases, 2 warning kinds and 1 clean case; it does not test unreachable steps, `$env`, credentials or save settings (they were read in the evidence files).

## 7. Process (EGM)
| step | state |
|---|---|
| plan and rung | done (section 2) |
| build | done: tools/flowcheck.py, run_all.sh |
| evidence runner (separate agent) | done: evidence-runner.md |
| review 1 egm-codebase-details | done: work/review-codebase-r1.md |
| review 2 egm-design | done: work/review-design-r1.md |
| egm-resolve round 1 | done: work/resolve-1.md; 8 Majors and 8 Nits accepted, 0 contested |
| fixes of round 1 | applied: this file, tools/flowcheck.py (crash fix, two WARN checks, self-test), run_all.sh |
| round 2 (fresh reviewers) | pending |

## 8. Round 1 fixes: what changed
Crash on `{}` and on a step without a `type` fixed (now failure lines; two self-test cases); rung table added; two WARN checks added; the counts (six recovery steps, 2/2/5/5 postgres steps, hunk offsets) corrected; section 1 reordered and reworded.
