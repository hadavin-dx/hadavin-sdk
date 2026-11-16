# FLOWCHECK REPORT (ORDER 011 item 1): patch and flow-graph check of the flows audit
Written by system-map, 2026-11-16. STATUS: DRAFT, evidence runner and two reviewers pending (see the last section). Read-only on cloud/flows-audit (commit 7fd00a7a when fetched); nothing there was edited.

## 1. Failures first
| # | what | where | how sure |
|---|---|---|---|
| 1 | No patch fails to apply and no patch leaves a broken graph. (Nothing to list here.) | all 5 patches | checked: evidence/dry-run.txt, evidence/build.txt |
| 2 | Every webhook in the take flows has NO authentication: `parameters.authentication` is absent on node `Receive` in mf-form and mf-hook, in real-v5, film-v5, pristine AND patched. None of the 5 patches adds it. This is the same hole as L7-FD-005 in SWEEP.md (fix-plan row 19). | mf-form.json, mf-hook.json, node `Receive` | CONFIRMED mechanically (evidence/md/*.md) |
| 3 | F-002 and F-008 do not change the flows by themselves: the flow JSON only changes after the generator is run again (`build_mainframe.py`, commands in the V5-README). The committed folders `n8n-flows-real-v5` and `n8n-flows-film-v5` stay unpatched until someone regenerates and commits them. The take imports JSON, not the generator. | patches F-002, F-008 | CONFIRMED: patches touch only build_mainframe.py |
| 4 | The folder names in ORDER 011 (`handover/demo/n8n-flows-real-v5`, `n8n-flows-film-v5`) are right, but they exist only on origin/cloud/flows-audit and origin/demo/handover, not on cloud/system-map. The order said `handover/demo/n8n-flows-real-v5` and `film-v5`; the second folder is really `n8n-flows-film-v5`. The older copy `handover/demo3/kill/flows-go1/` in this checkout is NOT the same file set as v5 (all 4 files differ from both v5 folders by byte comparison). | paths | CONFIRMED |
| 5 | Not checked at all: whether n8n accepts the new nodes (`KeyOk` if node with a boolean expression, `respondToWebhook` 1.4 with `responseCode` 422/503), because n8n is not installed here. The stand-in tests (mf.py T17, T18 and the new tests the patches imply) were NOT run. | F-002 | NOT VERIFIED |

## 2. Rung and tool (CODE-LAST)
Rung 1 to 4 question: does a free offline n8n linter already do this? Searched 2026-11-16 (one web search, results not opened beyond the summary): yes, several exist, all third-party and young, none vetted here: lorenzespinosa/n8n-lint (16 rules, orphaned connections), Waqas-Ai-Engineer/n8n-workflow-doctor (open webhooks, retries, dead nodes), SMillerDev/n8n-workflow-linter (zero-dependency Python, dead nodes), vladosskins178/n8n-workflow-lint, tachyurgy/n8n-workflow-lint, ubie-oss/n8n-cli. They cover orphan nodes, open webhooks and missing retries. From their descriptions they do NOT cover: `$('Name')` references to a missing node, alwaysOutputData together with continueErrorOutput, an error output left unwired, or the list of external calls upstream of a mail or CRM write (not verified by running them; licences and maintenance not checked). Decision: a 150-line standard-library script, `tools/flowcheck.py`, with a self-test (`--selftest`, passes); installing a young third-party tool from the network was not allowed under the studio rules without a licence check. If the laptop lead prefers one of the tools, it can replace the orphan and webhook checks; the other checks stay ours.

## 3. What was done
1. Copied the 4 flow files of each v5 folder and the 5 patches from origin/cloud/flows-audit into `in/` (read only copies).
2. The two patches that change flows (F-002, F-008) edit the generator, so the patched JSON was produced by applying the patch to a scratch copy of the generator and running it with the exact commands of V5-README. The other three patches change an SQL file and two Markdown files (no JSON).
3. `run_all.sh` rebuilds everything from git in one run (output folder given as argument).

## 4. Results
- Patch dry run, each patch alone, against the pristine files: all 5 print "checking file" with rc=0, no rejected hunk (evidence/dry-run.txt).
- F-002 then F-008 and F-008 then F-002 give the same generator file (F-008 hunk 2 moves by 3 or 4 lines, no failure).
- Pristine generator reproduces the committed real-v5 and film-v5 folders byte for byte (evidence/repro.txt). So the check on rebuilt JSON is a check of the committed JSON.
- Parse, duplicate names, connection targets, orphans, unreachable nodes, `$('Name')` references: no failure in any of the 16 pristine and patched files. The only failure line of the checker is the webhook one (item 2 above).

### Table per flow file (pristine = committed; both = F-002 and F-008 applied)
| file | state | nodes | connections | save ok/error | failures |
|---|---|---|---|---|---|
| real-v5/mf-form | pristine | 12 | 11 | none/none | Receive: webhook without authentication |
| real-v5/mf-form | both | 15 | 14 | all/all | Receive: webhook without authentication |
| real-v5/mf-hook | pristine | 12 | 11 | none/none | Receive: webhook without authentication |
| real-v5/mf-hook | both | 15 | 14 | all/all | Receive: webhook without authentication |
| real-v5/mf-recovery | pristine | 10 | 9 | none/none | none |
| real-v5/mf-recovery | both | 10 | 9 | none/none | none |
| real-v5/mf-sub-crm-mail | pristine | 20 | 26 | none/none | none |
| real-v5/mf-sub-crm-mail | both | 20 | 26 | all/all | none |
| film-v5/mf-form | pristine | 12 | 11 | none/none | Receive: webhook without authentication |
| film-v5/mf-form | both | 15 | 14 | all/all | Receive: webhook without authentication |
| film-v5/mf-hook | pristine | 12 | 11 | none/none | Receive: webhook without authentication |
| film-v5/mf-hook | both | 15 | 14 | all/all | Receive: webhook without authentication |
| film-v5/mf-recovery | pristine | 10 | 9 | none/none | none |
| film-v5/mf-recovery | both | 10 | 9 | none/none | none |
| film-v5/mf-sub-crm-mail | pristine | 20 | 26 | none/none | none |
| film-v5/mf-sub-crm-mail | both | 20 | 26 | all/all | none |

Same result for real-v5 and film-v5 in every row (they differ in the HubSpot node and the environment names only).

### What the patches change in the graph (F-002, F-008)
- mf-form and mf-hook, +3 nodes (12 to 15), +3 connections (11 to 14): new `KeyOk` (if), `ReplyBadKey` (answer 422), `ReplyStoreFail` (answer 503). `Claim` changes from alwaysOutputData=true with default error behaviour to alwaysOutputData=false with continueErrorOutput, and its error output (index 1) is wired to `ReplyStoreFail`. The checker confirms the F-002 pattern (alwaysOutputData together with continueErrorOutput) does NOT appear in the patched file, and that the error output is wired. In the pristine file `Claim` has alwaysOutputData=true and the default (stop): a failing store call stops the run and the caller of the `responseNode` webhook gets no answer from the flow itself (stated by the audit; the stop behaviour is read from the file, n8n behaviour not run here).
- F-008: saveDataSuccessExecution and saveDataErrorExecution go from none to all in mf-form, mf-hook and mf-sub-crm-mail; mf-recovery stays none. A saved run holds the lead key, e-mail and name (made-up data only in the take). saveManualExecutions stays false.

### Error settings of the nodes
Full per-node tables (onError, retryOnFail, alwaysOutputData, flags) for every file and variant are in `evidence/md/<variant>-<set>.md`. Summary of real-v5, pristine:
- External calls with continueErrorOutput and retry x2: `Qualify` (HTTP to the desk), `CrmUpsert` (HubSpot). Error outputs are wired in all files (no "not wired" flag).
- `SendMail`: continueErrorOutput, no retry (by design).
- Postgres nodes in the sub-workflow and in mf-form (`SetCrmId`, `MailClaim`, `MarkDone`, `MarkUnknownA/B`, `Stored`, `Claim`): default stop, alwaysOutputData yes. Default stop means a store error stops the run (fail closed before the mail).
- mf-recovery: five Postgres or call nodes are continueRegularOutput (`ClaimStuck`, `RunSub`, `MarkFailed`, `AlertClaim`, `AlertBackoff`, `AlertMark`); `AlertSend` is continueErrorOutput with error output wired to `AlertBackoff`. No node has alwaysOutputData together with continueErrorOutput in any of the 16 files.
- Upstream of each mail or CRM write (table `write nodes` in each md): `SendMail` has `CrmUpsert`, `Qualify` (both continueErrorOutput, wired) and `MailClaim`, `SetCrmId` (stop) upstream; `CrmUpsert` has `Qualify` upstream; the recovery `AlertSend` has `AlertClaim` (continueRegularOutput) upstream, guarded by the `AlertRow` if node (the guard is read from the generator comment, not run).
- No write node has a bare continueRegularOutput on a path where its upstream failure is silently dropped, except the recovery alert path above.

### $env, credentials, save settings
- $env: real-v5: DESK_URL, DESK_TIMEOUT_MS (Qualify), DESK_ALERT_TO (AlertSend). film-v5: MF_STAGE_URL, MF_STAGE_TIMEOUT_MS (Qualify), MF_CRM_URL (CrmUpsert). No secret is read through $env.
- Credentials by node type: postgres name `n8n-publish-pg` on 6 to 7 nodes per file (one shared identity for reads and writes, flagged in SWEEP.md fix-plan row 20); smtp name `mf-mail-smtp` on SendMail and AlertSend; hubspotAppToken name `hubspot-app-token` on CrmUpsert (real-v5 only). Ids are placeholders (PG_CREDENTIAL_ID and others).
- errorWorkflow: not set in any of the 16 files (no n8n-side error workflow).

## 5. Patches that do not apply or leave a broken graph
None. Caveats that are not failures: (a) the three non-JSON patches (F-001 SQL, F-003 and F-004 Markdown) were only checked to apply; their text was not judged; (b) a clean graph does not prove n8n runs it (section 1, item 5).

## 6. Process (EGM)
| step | state |
|---|---|
| plan and rung | done (sections 2 and 3) |
| build | done: tools/flowcheck.py (self-test passes), run_all.sh |
| evidence runner (separate agent) | pending |
| review 1 egm-codebase-details | pending |
| review 2 egm-design | pending |
| egm-resolve | pending |
