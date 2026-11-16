# REPORT from flows-audit (newest on top, UTC and IST)

## Status 2026-11-16 07:57 UTC / 13:27 IST - ORDER 005: plan v2 done, 5 review lanes running
Agents running: 5 sonnet (R5-B 20 Blockers, R5-M1 and R5-M2 Major sample, R5-D table owners/decisions/bands, R5-Z missed items/cut list). Closed: plan reviewers (NOT READY, 1+3 Blockers, 12 Majors; all fixed in PLAN-005 v2) and EV5. EV5 raw result: 56 of 56 Blocker citations and 209 of 209 citations of every 3rd Major exist on the exact line (shows the quotes exist, not that they support the claims); table counts match the claim (59 = 49+10, 7 Owner lines). Next: save lane reports, resolve, write REVIEW/CORRECTIONS/LEDGER-ROWS.

## Status 2026-11-16 07:53 UTC / 13:23 IST - ORDER 005 started (cross-review of system-map)
Agents running: 0 at write time; 4 sonnet agents + plan review start next (register below). Target exported read-only to /tmp/sm and /tmp/smfull (git archive of origin/cloud/system-map). Plan: PLAN-005.md. Not visible: take repo, n8n runtime, HubSpot, SMTP.
Agent register for ORDER 005 (id | purpose | started UTC/IST | expected end | last checked | state | next):
| EV5 | EVIDENCE RUNNER: citation + caller checks, raw output | 07:53 / 13:23 | 08:00 | 07:54 | CLOSED (reported; evidence-5.md) | read by lanes |
| PR5-design, PR5-impl | plan review r1 | 07:53 | | 07:54 | CLOSED (reported; NOT READY, fixed in PLAN-005 v2) | none |
| R5-B | codebase-details: 20 Blockers vs source | 07:56 / 13:26 | 08:36 | - | running | save report |
| R5-M1, R5-M2 | codebase-details: Major sample halves | 07:56 | 08:36 | - | running | save reports |
| R5-D | design: table owners, 4 decisions, bands | 07:56 | 08:36 | - | running | save report |
| R5-Z | zoom-out: missed items, cut list | 07:56 | 08:36 | - | running | save report |

## FINAL 2026-11-16 07:43 UTC / 13:13 IST: ORDER 004 applied (Reading A), waiting for the lead
Agents running: 0 (I started none for this order). No helper shells left.
Applied: Q2 answered Reading A. F-011 kept at full size and rewritten (n8n's own state moves into the take's Postgres with its own role; no script under handover/demo sets DB_TYPE or DB_POSTGRESDB_*, grep 0 hits; fix is a laptop change plus re-smoke, not patched). The owner's "save runs ON for the take only, delete at clean-up" is now patch F-008-save-runs-for-the-take.patch (build_mainframe.py:44, no node changes). EXCEPTIONS.md, QUESTIONS.md (Q2 answered), FIX-PLAN.md step 6 and FINDINGS short answer item 4 updated. Counts unchanged: 34 findings = 2 Blocker, 23 Major, 9 Nit.
Checks after the edits: check_counts PASS 52/655, check_names PASS 655, check_refs PASS 5118, check_secrets PASS 0 hits in 174 files, test_dump_nodes PASS 8/8, check_patches PASS 5 patches, `git apply --check` ok for each of the 5. Rebuild with patches F-002 and F-008 together (real-v5 build into a scratch folder): mf-form 15, mf-hook 15, mf-recovery 10, mf-sub-crm-mail 20 nodes, all four with saveDataSuccessExecution and saveDataErrorExecution "all". I did this check myself in a scratch folder (no separate evidence runner and no new review round, as ORDER 004 says: bounded to the changed rows).
Not verified: nothing was run in n8n, so that n8n 2.x starts on DB_POSTGRESDB_* with a separate role, and that the T7b scan still passes on Postgres, are UNVERIFIED (re-smoke). The clean-up step (delete the take's executions) is not written into any script yet; it is listed in F-008 and FIX-PLAN. evidence-1.md and evidence-2.md describe the earlier four-patch state and are not rewritten.
Next: the lead applies the patches and the n8n Postgres switch on the laptop. I stop here.

## FINAL 2026-11-16 07:34 UTC / 13:04 IST: ORDER 002 (with ORDER 003) finished, waiting for the lead
Agents running: 0. All register rows are CLOSED (EV1, EV2, RV-cb, RV-d, RV-z, RV2-d, RV2-cb, six builder lanes). No helper shells or background processes are left. Only tools/scratch/ is untracked on purpose (scripts and scratch builds, never committed).

What failed, in order of weight:
1. Round 1 of the result review found real faults in my work (patches left the sheets contradicting each other, a false "not_stored" reply, a cut list that could archive the only correct table definition, wrong severity order, duplicated text). Fixed and recorded in reviews/result-r1-resolve.md.
2. Round 2 found more: my scene 4 caption pooled four kill points and hid that the runs were on older stand-in flows; patch F-004 moved a contradiction instead of removing it; the cut list wanted to archive dn1_common.py (which mf.py imports) and other files that live documents still name; F-013 proposed a fix the stand-in already has; F-002 (empty lead_key) can lose a lead, so it is now a Blocker. All fixed in text and patches (reviews/result-r2-resolve.md).
3. Clock slip: some earlier status blocks carry times later than the real `date -u`; use the commit times. I also wrote reviewer report times before checking the clock and corrected them to "before 07:32".

Result: FINDINGS.md has 34 findings = 2 Blocker (F-001 table definition without alert columns; F-002 missing lead key can lose a lead), 23 Major, 9 Nit. Four patches (F-001 to F-004) apply cleanly and are text or generator changes only; nothing outside handover/flows-audit changed (evidence-2.md (p)). Rebuild with patch F-002: 3 new nodes (KeyOk, ReplyBadKey, ReplyStoreFail), Valid changed, recovery and sub flows unchanged, no dangling edge (evidence-2.md (m)); the generator without the patch reproduces the saved real-v5 and film-v5 node sets.

Reports in EGM order: PLAN-002.md and reviews/plan-r1..r3 (plan review, resolve); evidence-1.md and evidence-2.md (EVIDENCE RUNNER, raw); reviews/result-r1-*.md and result-r2-*.md (egm-design, egm-codebase-details, egm-zoom-out, fresh each round); result-r1-resolve.md and result-r2-resolve.md; reviews/drift-report.md. Checks I re-ran after the last edit: check_counts PASS 52 files / 655 nodes, check_names PASS 655 rows, check_refs PASS 5118, check_secrets PASS 0 hits in 173 files, check_patches PASS 4, test_dump_nodes PASS 8/8.

Not done and why:
- Nothing was run in n8n, HubSpot or SMTP (the order forbids it): the 422/503 replies, item pairing on the Claim error output, the sender retry and every lane3 number are UNVERIFIED (raw lane3 files are not in this repository).
- Escalated to the lead: QUESTIONS.md Q2 (does "one database = n8n Postgres" also cover n8n's own SQLite? F-011). Owner decisions are listed in FIX-PLAN.md (O).
- Result review is at its 2-round cap for non-mail paths. F-002 touches intake; if you want a round 3 on F-002 only, say so. The round-2 fixes to the cut list and F-013 have no third independent read.
- The studio ledger tool (ledger_check) is not in this repository; LEDGER-ROWS.md rows are all OPEN because applying the patches happens on the laptop.
- Duplicate notes and DRAFT page statements are my reading of names and first lines, not a line-by-line diff (UNVERIFIED).

Token use (sub-agents, from the harness): EV2 about 103k, RV2-d about 159k, RV2-cb about 177k; earlier rounds are in their earlier blocks. Main session: not measurable from here.
Next: the lead reads FINDINGS.md (short answer first), FIX-PLAN.md and CUT-LIST.md, answers Q2, and orders the apply steps on the laptop. I stop here.

## STATUS 2026-11-16 07:32 UTC / 13:02 IST: round 2 running
Agents running: 3 (EV2 evidence runner, RV2-d design reviewer, RV2-cb codebase reviewer), all started 07:30 UTC. Nothing failed since the last block. Not yet checked: any round-2 result. Next: read reports, save to reviews/result-r2-*.md, resolve, drift report, FINAL block.

## STATUS 07:47 UTC / 13:17 IST: result review round 1 resolved, evidence-2 and round 2 next
Done: three fresh reviewers (codebase-details, design, zoom-out; all sonnet) reported; reports saved in reviews/ and resolved with egm:egm-resolve (reviews/result-r1-resolve.md). Fixes applied: patches F-001 to F-004 regenerated (all four pass git apply --check), FINDINGS.md now 34 findings (1 Blocker, 27 Major, 6 Nit) with a plain short answer and a glossary, CUT-LIST has the order of work and the missing candidates, claims tally corrected (28 / 4 / 15 / 36), store counts corrected (14 rows), FLOWS-AUDIT.md deduplicated (125 lines of repeated lane text removed).
Failures and slips: the reviewers found that my patches F-003 and F-004 left the sheets contradicting themselves, that my F-002 reply said "not_stored" when the write may have succeeded, that the cut list could have moved the only correct table definition, that two of my claim verdicts were mislabelled, and that F-012 and F-014 had wrong wording. All fixed in text; none of the patched behaviour has run in n8n.
Not verified: everything needing n8n, HubSpot, SMTP, the desk repo or the lane3 raw files; the new 422/503 replies have no test yet; the three check scripts and apply checks must be re-run by the independent evidence runner on the new head (evidence-2.md).
Agents running: 0 now. Next: register and start EV2 (evidence runner) and two round-2 reviewers (egm-design, egm-codebase-details) on the changed files.

## STATUS 07:15 UTC / 12:45 IST: ORDER 002 result review running. Head a29e8a8 (+ note commit)
Done: 6 builder lanes reported and were spot-checked (SetCrmId grep, alert columns per mf_leads.sql, saveData settings, 10-of-12 identical nodes, desk door URLs, v3==v4 schema). Merge written: FLOWS-AUDIT.md (52 files, 655 nodes, every node a row; check_counts PASS 52/655, check_names PASS 655 rows), FINDINGS.md (28 merged from 98 lane findings: 1 Blocker, 24 Major, 3 Nit; the first version of this line said 21 and 6, which was my miscount), 4 patches (apply-check PASS), CUT-LIST, EXCEPTIONS, FIX-PLAN, LESSONS, LEDGER-ROWS. check_secrets PASS 0 hits; check_refs PASS 5087 refs.
Failures and slips found by me: plan said 54 files (52); first masking test could not fail (fixed, mutant now fails); check_secrets skipped a prefix-named file (fixed); check_refs swallowed refs after "and" and could not resolve short names (fixed, probe now fails as expected). Builder counts off by one in one report (L2b-3: 6 vs 7 Majors; counted by lead).
Not verified: everything needing n8n, HubSpot, SMTP, the desk repo or the lane3 raw files (UNVERIFIED in the findings). Patch F-002 behaviour in n8n untested; patches F-003/F-004 insert relayed numbers (60.1 to 61.9 s).
Agents running: 4 language-model agents (1 evidence runner, 3 result reviewers: codebase-details, design, zoom-out), all sonnet, all started 07:15. 0 script lanes. Open decisions for the lead: F-001 severity raised to Blocker by me; owner items F-005..F-011, F-020, F-023, CUT-LIST yes.
## AGENT REGISTER (id | purpose | started UTC/IST | expected end | last checked | state | next)
| EV1 (a57ea181769a9537f) | EVIDENCE RUNNER checks a-k into evidence-1.md | 07:15/12:45 | +10 min | 07:47 | CLOSED (reported, evidence-1.md read) | none |
| RV-cb (a52c620d686a34950) | result review codebase-details | 07:15/12:45 | +15 min | 07:47 | CLOSED (reported, saved to reviews/, resolved) | none |
| RV-d (a737211799b7fc972) | result review design | 07:15/12:45 | +15 min | 07:47 | CLOSED (reported, saved to reviews/, resolved) | none |
| RV-z (a7518d3448ebfabf1) | result review zoom-out | 07:15/12:45 | +15 min | 07:47 | CLOSED (reported, saved to reviews/, resolved) | none |
| EV2 (a026774cb604af485) | EVIDENCE RUNNER checks a-k plus F-002 rebuild and cmp into evidence-2.md | 07:30/13:00 | +15 min | - | CLOSED (reported (clock time not recorded; before 07:32), evidence-2.md read: all checks exit 0; patched rebuild adds KeyOk, ReplyBadKey, ReplyStoreFail to mf-form and mf-hook, no dangling edges) | none |
| RV2-d (ad46b354c5fb12696) | result review round 2 design (fresh) | 07:30/13:00 | +15 min | - | CLOSED (reported (before 07:32), saved to reviews/result-r2-design.md; 7 Majors) | resolve after RV2-cb |
| RV2-cb (a33d32a4f58af3185) | result review round 2 codebase-details (fresh) | 07:30/13:00 | +15 min | - | CLOSED (reported (before 07:32), saved to reviews/result-r2-codebase.md; 4 Majors, 7 Nits; resolved) | none |
Builders L1, L2a, L2b-1, L2b-2, L2b-3, L3: closed (reported, files read, no helper shells).

## STATUS 06:47 UTC / 12:17 IST: ORDER 002 started, plan written (PLAN-002.md), plan review next
Agents running: 0 language-model agents, 0 script lanes. Next: egm:egm-review-loop on PLAN-002.md.

## STATUS 2026-11-16 06:56 UTC / 12:26 IST: ORDER 001 done, waiting for GO
Agents running: 0 language-model agents, 0 script lanes (both reviewers finished). Nothing else started: order says proof only.
What failed / uncertain: nothing failed. Not checked: I ran one review round only (dry run), no resolve step. The order's grep path (~/.claude/plugins/*/egm*) matched; I did not separately verify the plugin cache under /root/.claude/plugins/cache/egm.

## ORDER 001 PROOF: EGM IS VISIBLE
Skills in my Skill tool (exact): egm:egm-bootstrap, egm:egm-brainstorm, egm:egm-draft, egm:egm-drift-report, egm:egm-resolve, egm:egm-review, egm:egm-review-loop.
Agents in my Agent tool (exact): egm:egm-bootstrap-orchestrator, egm:egm-codebase-details, egm:egm-comprehension, egm:egm-design, egm:egm-implementation-readiness, egm:egm-inventive-catalyst, egm:egm-structural, egm:egm-style, egm:egm-synthesizer, egm:egm-zoom-out.
Command: grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c
Output:
      6 model: claude-opus-5-5
     64 model: claude-sonnet-5-5
Matches the expected 6 opus-5-5 and 64 sonnet-5-5.
Dry run: egm:egm-review-loop via the Skill tool on a 3-line paragraph; two reviewers (egm:egm-design, egm:egm-implementation-readiness) on sonnet. Both returned FAIL with specific findings. Result in handover/flows-audit/egm-dryrun.md.
Files read: handover/BRIEF-PREAMBLE.md, MODEL-ROUTING.md, RULE-R456-WORK-CONDUCT.md (first part only, head of each).
