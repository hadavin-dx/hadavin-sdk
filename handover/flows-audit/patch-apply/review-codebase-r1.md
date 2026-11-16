# F4 result review round 1, codebase-details (egm:egm-codebase-details, sonnet; saved by the main session; condensed, every finding kept)
Reviewer verdict: evidence mostly supports the claims; no false pass in the numbers it re-derived (mf-form 15 nodes 14 connections after F-002 with the right links, Claim has onError continueErrorOutput, saveData settings all; baseline mf-recovery 10 nodes, mf-sub-crm-mail 20). Read-only, re-ran nothing.
| id | sev | where | finding | fix |
|---|---|---|---|---|
| R1 | Major | check_flows.py trig() lines 36-38 | orphan exemption is any type containing "webhook" or "trigger"; respondToWebhook contains "webhook", so every Reply* node (new ReplyBadKey, ReplyStoreFail and ReplyRan, ReplyReview, ReplyStored) is exempt; an unwired reply node would still print orphans=[]. | exempt exact types only (webhook, *Trigger, executeWorkflowTrigger, formTrigger) |
| R2 | Major | orphan logic 22-39 | orphan = never a target; not reachability; a node targeted only by itself or by another orphan passes; no check that a trigger exists. | compute reachability from triggers; assert at least one trigger |
| R3 | Major | main 45-51 and report | checker only prints: no assertions, expected counts, exit code; F-002 names/links and F-008 settings not checked by the script; the report's "Extra checks" has no command or output. | add --expect assertions and non-zero exit; save the F-002 and F-008 check commands and output |
| R4 | Major | main | a missing file is silently skipped (glob *.json); nothing asserts 4 files per directory. | assert the exact file list |
| R5 | Major | lines 8-15, 39 | parse failure printed and function returns early, exit still 0; n["name"] KeyError crashes the run. | non-zero exit; name-present check |
| R6 | Nit | dangling logic | counting is correct (all outputs incl. error outputs); no check that the output index exists on the source node. | optional |
| R7 | Major | REPORT.md | no "not tested" section. Not tested: import into n8n; parameters of new nodes (KeyOk IF, ReplyBadKey/ReplyStoreFail status and body); F-001 columns in other SQL, whether flow SQL uses alert_* columns; F-003/F-004 content correctness; mf-recovery equality shown without a script. | add the section; add SQL, parameter and content checks |
| R8 | Nit | REPORT.md | "200 / 200" diff lines unlabeled; "diff -r" lines without hunks. | labeled counts, changed node names |
| R9 | Nit | REPORT.md | F-001 columns stated without the grep command and output. | show it |
| R10 | Nit | REPORT.md | apply status adequately evidenced; film generator run without the HS_CRED placeholder so film vs real not compared. | none |
Not checked by reviewer: ran nothing; did not diff generator output vs saved JSON; baseline mf-form/mf-hook counts and sub-crm-mail 26 connections not hand-counted; mf-hook patched links, F-008 sub-crm-mail, film outputs; patch correctness beyond grep.
