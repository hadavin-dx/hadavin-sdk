# FLOWCHECK REPORT (ORDER 011 item 1): patch and flow-graph check of the flows audit
Written by system-map, 2026-11-16. STATUS: reviews of round 1 and round 2 fixed (section 8); round 2 findings were Majors only, no Blocker; no third review round (cap 2, not a security path). Read-only on cloud/flows-audit (commit 7fd00a7a at the time of the first fetch); nothing there was edited. Words used: a *flow* is one n8n workflow file; *webhook* is the address a sender posts a lead to; *onError* is what a step does when it fails (default: the whole run stops); *the generator* is the program `build_mainframe.py` that writes the flow files. *real-v5* and *film-v5* are the two sets of flow files, one for the real build and one for the film recording (the take = the demo that will be recorded). The *form flow* takes a lead from a web form; the *e-mail-style flow* takes a lead from a forwarded e-mail message; the *sub-workflow* is the shared flow that writes to the CRM (the customer database) and sends the mail; the *lead key* is the unique id of one lead, used to spot a lead sent twice. *WARN* is a line the checker prints for a risk that does not stop the flow from loading. 422 and 503 are web reply codes meaning "rejected, do not resend" and "not stored, resend".

## 1. Failures first
| # | what | where | how sure |
|---|---|---|---|
| 1 | Anyone who knows the form address can send a lead. The first step of the form flow and of the e-mail-style flow (`Receive`) asks for no password or key. This is true in both file sets, before and after the patches. Patch F-002 adds a check that the lead key looks valid; that is not a password check. None of the five patches adds one. Already listed as L7-FD-005 in SWEEP.md (fix-plan row 19). | mf-form.json, mf-hook.json, step `Receive` | CONFIRMED by the checker in all 16 built files that have a `Receive` step (form and e-mail-style flow, 2 file sets, 4 patch states). The other 16 files have no webhook. |
| 2 | Two fixes proposed by the audit (F-002 key check and error replies; F-008 keep run records for the take) are written as edits to the generator, not to the flow files. The flow files that n8n imports (`n8n-flows-real-v5`, `n8n-flows-film-v5`) do not change until someone runs the generator again and commits the result. I checked by applying the edits to a copy and running the generator; the committed files are unchanged by the patches themselves. ("n8n imports the JSON files, not the generator" is from the V5-README, which I read but is not part of the saved evidence.) | F-002, F-008 | CONFIRMED (evidence/dry-run.txt, build.txt) |
| 3 | NOT TESTED. I did not run any of this in n8n (the workflow program): n8n is not installed here and its container program has no running daemon (section 2). Two things are untested: (a) whether n8n accepts what patch F-002 adds (a key check, replies 422 and 503); (b) what n8n does when a database insert stores nothing because the lead was sent twice: with `Claim` set to give no output on an empty result, patch F-002 relies on n8n still handing on one item. The generator comment says it does; the checker cannot show it. The patch names test T-F002b for this (mf.py T17 and T18 are tests of the CRM reply, not of the key check). Next step: import the patched files into a throw-away n8n and run T-F002b. | F-002 | NOT VERIFIED |
| 4 | The F-002 reply fix covers one step only. In the patched form flow `Claim` gets an error reply (503). `Stored` (database read) and `RunSub` (call of the sub-workflow) keep the default stop and no reply: a failure there leaves the sender without an answer, the same gap F-002 closes for `Claim`. The new WARN line of the checker shows it (2 warnings per patched entry flow, 3 before). Read from the file, not run in n8n. | patched mf-form, mf-hook | CONFIRMED in the file |

Not a failure, a path note: the order says `handover/demo/n8n-flows-real-v5` and `film-v5`; the second folder is really `handover/demo/n8n-flows-film-v5`. Both exist only on origin/cloud/flows-audit (and origin/demo/handover), not on cloud/system-map. The older folder `handover/demo3/kill/flows-go1/` in this checkout is a different version: byte comparison of its four flow files with real-v5 and film-v5 says "differs" for all 8 pairs (evidence/go1.txt).

What passed (each line says whether the check was seen to fire in the self-test): all five patches apply without a rejected hunk and none leaves a broken graph (evidence/dry-run.txt); the unpatched generator reproduces the committed v5 folders byte for byte (evidence/repro.txt); parse, duplicate names, connection targets, orphans, unreachable steps and `$('Name')` references show no failure in any of the 32 built files (the only failure line is item 1). All of these checks, and the `$env`, credential and save-setting readers, now have a self-test case and a mutant that the self-test catches (evidence/mutants-r2.txt); before round 2 unreachable steps, `$env`, credentials and save settings were never exercised.

## 2. Rung table (rule 20, CODE-LAST)
Order of events, stated plainly: the script was written first and this table was added after review round 1 (the order wanted it before). Evidence for the linter rows is ONE web search on 2026-11-16 read from its result summaries (no URLs saved, no per-tool date); no linter was opened, installed or run, no licence read. Rung 1 (this repository): `grep -ril "n8n.*lint\|workflow.*lint" handover` matched only handover/demo3/ORDERS.md and nine .patch files there; the one matched line I read (ORDERS.md:37) is not about an n8n linter; the patch files were not opened and the output was not saved; the core package and templates were not searched. A generic JSON parse and a schema check cover only "parses" (done here by `json.load`). n8n's own import check is the real test and is not available (below).
| component | need | rung tried | evidence (source, date) | what only our code gives | verdict |
|---|---|---|---|---|---|
| orphan, dead node, open webhook, missing retry | list failures | rung 1: nothing found in handover. Rung 3/4: third-party linters lorenzespinosa/n8n-lint, Waqas-Ai-Engineer/n8n-workflow-doctor, SMillerDev/n8n-workflow-linter, vladosskins178/n8n-workflow-lint, tachyurgy/n8n-workflow-lint, ubie-oss/n8n-cli | UNVERIFIED: search summary 2026-11-16, not run | nothing proven | KEEP-CODE for this order. The test "does a linter cover 80 percent" was not made: running unvetted third-party code on the 32 files needs a licence and trust check first. Next step: read one licence, run it offline on the 32 files, compare. |
| `$('Name')` references, error output wired, the F-002 combination, upstream calls of a mail or CRM write, default stop on a reply path, pristine against patched | list failures and warnings | same tools | UNVERIFIED claim from the summaries that they lack these | the pristine-against-patched comparison for this audit | KEEP-CODE as one thin script (`tools/flowcheck.py`, 171 lines, standard library, no network); re-decide after the linter run above |
| real validity (does n8n import and run it) | prove the patch works | rung 3: n8n itself in a throw-away container (owner rule 5b allows it) | `docker info` and `docker pull n8nio/n8n` on 2026-11-16: the Docker program is installed but no daemon runs (no /var/run/docker.sock); output in evidence/n8n-try.txt | nothing | KEEP-CODE (the graph check stays; n8n acceptance stays NOT TESTED). Blocker: no container daemon in this cloud session. Next step: the laptop lead imports the patched files into n8n on the laptop and runs T-F002b. |

## 3. What was done
1. Copied the 4 flow files of each v5 folder and the 5 patches from origin/cloud/flows-audit into `in/`.
2. F-002 and F-008 edit the generator, so the patched flow files were produced by applying the patch to a scratch copy and running the generator with the commands of the V5-README. F-001 (SQL), F-003 and F-004 (Markdown) change no flow file; they were only checked to apply, and their text was not judged. The graph check says nothing about whether the SQL columns of F-001 match the queries in the steps.
3. `run_all.sh OUTDIR` (OUTDIR under /tmp) rebuilds everything from git in one run. Evidence was produced by that script (author). A separate evidence runner (`evidence-runner.md`) ran the script as it was BEFORE round 1: 6 comparisons empty, 8 of 8 hostile inputs run (2 crashes found, fixed in section 8), 4 of 4 mutants caught. The current script (crash fix, two WARN checks, new self-test cases) was NOT re-run by that runner. Instead, after round 2: the author re-ran `run_all.sh` (`evidence/md/` regenerated byte-identical to the saved copies; `selftest ok`) and ran 7 mutants of the new code against the self-test (evidence/mutants-r2.txt; 2 survived at first and got new test cases, then were caught). That is the author's own check, not an independent one. `run_all.sh` does not produce summary-table.md and error-tables-real-v5-pristine.md; those were derived by hand from evidence/md/.

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

Real-v5 and film-v5 give the same result in every row of this table (they differ in the HubSpot step and in the names of the environment settings).

### What the patches change in the graph
- Entry flows (form and e-mail-style): +3 steps (12 to 15), +3 connections (11 to 14): `KeyOk` (a yes/no step), `ReplyBadKey` (answer 422), `ReplyStoreFail` (answer 503). `Claim` changes from "always output, default stop" to "no output on an empty result, continue on error" and its error output is wired to `ReplyStoreFail`. The F-002 combination (always output together with continue-on-error) is clean in all 32 files, the unpatched ones too, so that flag only shows the patch does not introduce it; the real defect the patch fixes (no error path and no reply on `Claim`) is not what that flag looks for, and is shown by the WARN line instead.
- F-008: saved runs go from none to all in the form flow, the e-mail-style flow and the sub-workflow; the recovery flow stays at none (it fires every 30 s). A saved run holds the lead key, e-mail and name (made-up data only in the take). Manual runs stay unsaved.

### Error settings of the steps
Real-v5, committed files, one table per file: 4 of the 8 files are shown here (the same tables for all states and for film-v5 are in evidence/md/). Columns: what the step does on error, retry, whether it outputs an item on an empty result, and the checker's flag.

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
- `SendMail`: continue-on-error, no retry (per the generator comment).
- Several database steps (`Claim` before the patch, `Stored`, `SetCrmId`, `MailClaim`, `MarkDone`, `MarkUnknownA`, `MarkUnknownB`) stop the run on error (default) and output an item on an empty result. Default stop means an error stops the run before the mail (read from the file, not run in n8n).
- Recovery flow: six steps continue on error: `ClaimStuck`, `RunSub`, `MarkFailed`, `AlertClaim`, `AlertBackoff`, `AlertMark`. `AlertSend` continues on its error output, wired to `AlertBackoff`.
- No step has "always output" together with "continue on error output" in any of the 32 files.

### Steps with no safe error path before a mail or CRM write (computed by the checker, WARN lines)
Mail or CRM write, as the checker decides it by a name rule: a step of type e-mail or HubSpot, or an HTTP call whose address text contains "crm" and whose method is not GET (here `SendMail`, `AlertSend`, `CrmUpsert`; the plain HTTP call `Qualify` to the desk is not a write). In film-v5 `CrmUpsert` is found only because its address reads `$env.MF_CRM_URL`; an address without "crm" would not be seen (self-test case added).
- The 8 recovery files all carry one WARN: `AlertSend` has `AlertClaim` upstream, which continues on error. The `AlertRow` yes/no step guards it (read from the generator comment, not run).
- The 8 sub-workflow files carry no WARN. `SendMail` has `MailClaim` and `SetCrmId` upstream with no error path (default stop: an error stops the whole run before the mail goes out, read from the file, not run in n8n), and `Qualify` and `CrmUpsert` upstream with wired error outputs. `CrmUpsert` has `Qualify` upstream (wired).
- The 16 entry-flow files carry 3 (before) or 2 (after F-002) WARN lines of the other kind: a database or sub-workflow step with default stop on the reply path (`Claim`, `RunSub`, `Stored`).
- The checker flags upstream steps that continue on error; it does not flag default-stop steps before a write (they are listed in the table above and in the text).

### Environment settings read, credentials, run saving
- Environment settings read with `$env`: real-v5: DESK_URL and DESK_TIMEOUT_MS (`Qualify`), DESK_ALERT_TO (`AlertSend`). film-v5: MF_STAGE_URL and MF_STAGE_TIMEOUT_MS (`Qualify`), MF_CRM_URL (`CrmUpsert`); film-v5 recovery reads none. These are names read from the committed files. No secret is read through `$env`.
- Credentials by step type: postgres name `n8n-publish-pg`: 2 steps in the form flow, 2 in the e-mail-style flow, 5 in the recovery flow, 5 in the sub-workflow, one shared identity everywhere (SWEEP.md fix-plan row 20); smtp name `mf-mail-smtp` on `SendMail` and `AlertSend`; hubspotAppToken name `hubspot-app-token` on `CrmUpsert` (real-v5 only). Ids are placeholders (PG_CREDENTIAL_ID and others).
- No error workflow (`errorWorkflow`) is set in any of the 32 files.

## 5. Patches that do not apply or leave a broken graph
None. See "What passed" in section 1, and item 2 for what is not tested.

## 6. What the checker cannot see (script header)
`$node["X"]` and `$items("X")` references (a search of in/ found none; this search was not saved as evidence), computed `$env` keys, a header-auth setting with no credential attached, disabled steps, trigger types outside its name pattern, and n8n's own parameter rules. The self-test covers 8 failure kinds (including unreachable steps), the three hostile inputs (`[]`, `{}`, a step with no type), all 3 warning messages, the write-name rule (e-mail, "crm" address, GET, no "crm"), `$env` (dot and bracket forms), credentials, save settings and 1 clean case. Not covered: the checker still crashes on a null `parameters`, a null `settings` or a non-object `connections`; main now prints a "checker crashed" failure for that file and goes on with the next one. A write that uses an address without "crm" is not seen as a write.

## 7. Process (EGM)
| step | state |
|---|---|
| plan and rung | rung table written after the build, in round 1 (section 2, section 8) |
| build | done: tools/flowcheck.py, run_all.sh |
| evidence runner (separate agent) | done on the pre-round-1 script: evidence-runner.md; delta re-run by the author only (section 3) |
| review 1 egm-codebase-details | done: work/review-codebase-r1.md |
| review 2 egm-design | done: work/review-design-r1.md |
| egm-resolve round 1 | done: work/resolve-1.md; 8 Majors and 8 Nits accepted, 0 contested |
| fixes of round 1 | applied: this file, tools/flowcheck.py (crash fix, two WARN checks, self-test), run_all.sh |
| round 2 egm-codebase-details and egm-design | done: work/review-codebase-r2.md, work/review-design-r2.md; 0 Blockers, 11 Majors (5 + 6), 14 Nits |
| egm-resolve round 2 | done: work/resolve-2.md; all Majors accepted and fixed, 0 contested |
| round 3 | none: cap of 2 rounds outside security, money and redaction paths; Nits fixed without review |

## 8. Round 1 fixes: what changed
Crash on `{}` and on a step without a `type` fixed (now failure lines; two self-test cases); rung table added; two WARN checks added; the counts (six recovery steps, 2/2/5/5 postgres steps, hunk offsets) corrected; section 1 reordered and reworded.

## 9. Round 2 fixes: what changed
Section 1 reordered (path note moved below "What passed"), terms explained in the header, item 1 reworded and its count corrected to 16 files; evidence-runner claim corrected (section 3); rung table rewritten with one of three verdicts per row and the Docker blocker saved (evidence/n8n-try.txt); self-test extended (unreachable, write-name rule, `$env`, credentials, save settings, write node itself, `stopWorkflow`) with 7 mutants checked; the warn check now treats an explicit `stopWorkflow` as the default stop; `main` no longer stops on one crashing file; the unused `WRITE_T` removed; `run_all.sh` resolves the output path first and refuses `/tmp`, `/tmp/` and `..` paths, tests for a missing go1 file, and exits 1 when a build, the repro or the self-test fails; the write-path section corrected to what the files show.
