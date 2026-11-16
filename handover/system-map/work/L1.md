# Lane L1

<!-- LANE-KEY -->
> KEY (inline, added 16 Nov 2026, so this page can be read alone)
> - take = the one recorded run of the lead-intake demo (made-up data, run through n8n), planned for 23 Nov 2026.
> - lane = one read-only audit pass over a set of files by one agent. L1c, L3c, L4c, L5ac are continuation lanes that read what the first lane left. Findings are cited by id (for example L1c-FD-003 = finding 3 of lane L1c), not by line number; the merged list is merged-findings.md.
> - Size columns are bytes unless the header says otherwise.
> - Status words (only three exist; the note column gives the extent): READ = opened whole, apart from any cut named in the note (long lines cut at a stated length still count as READ). SKIMMED = only part of the file looked at: headers, search hits, a first and last slice, or only a listing and checksum; the note says which. NOT-READ = no part of the contents looked at, and the note says why or leaves it open. Draw no conclusion about a file from a lane that did not read it.
> - UNVERIFIED = no source file states it and nobody checked. NOT FOUND = searched, none found. N/A = does not apply (the reason follows).
> - Job keys (what a component does): COUNTER counts events; FILTER refuses input; RETRY repeats a failed step; LOG records output; STORE holds data; NOTICE alerts a person; OTHER none of these.
> - DECISION line N = line N of DECISION-one-store.md (decision 10 of inputs/DECISIONS-2026-11-16.md names that file and its line 14; two copies exist and which one is meant is not recorded). The sentence on line N is NOT RECORDED here, so every finding citing one is UNVERIFIED.
> - The lead / lead session = the Claude session giving orders. Studio lead = the Claude session doing the technical steps. Other terms: GLOSSARY.md.



> PAGE SCOPE (statuses are defined only in the KEY above): the scope is the part of the demo that decision 1 keeps: scenes 1 to 4 of the run sheet of the version called real-v5 (its one claim: a lead sent twice with the same id is processed once). Scenes 5 to 11 (version film-v5) are not in the video. Plain words: real-v5 = the plan version with scenes 1 to 4 that is filmed; film-v5 = the longer plan version with scenes 5 to 11 that is not filmed; run sheet = the numbered list of scenes for the take (its location is NOT RECORDED here). Old rows that say SKIMMED with a note "not opened" mean LISTED-ONLY (file name and size only); old rows that say NOT-READ with a note "partly read" mean PARTIAL (the note says how much); a status READ with a note "cut" means READ-TRUNCATED. The first number column is the file size in bytes. Source: inputs/DECISIONS-2026-11-16.md, decision 1. Owner and date of each continuation lane: not yet assigned; the studio lead names them when it starts each one.
> PURPOSE: this page records which files the lane opened, how far it read each, and which findings it raised, so the lead can decide what to fix. It states no result about the system itself beyond the findings cited by id.

## Coverage
PARTIAL: stopped for size and time; every file listed as NOT-READ below was not opened in full and nothing may be concluded from its absence of findings. A continuation lane is needed for the NOT-READ list.
| path | bytes | status | note |
|---|---|---|---|
| handover/BRIEF-PREAMBLE.md | 10950 | READ | whole file; identical to BRIEF-LANE lines 1 to 23 (diff empty) |
| handover/CLOUD-EGM-SETUP-2026-11-12.md | 5243 | READ | whole file |
| handover/EGM-CHILD-HOWTO.md | 2219 | READ | whole file |
| handover/MODEL-ROUTING.md | 6379 | READ | whole file |
| handover/RULE-R456-WORK-CONDUCT.md | 3374 | READ | whole file |
| handover/demo/APPLY-LIST.md | 27360 | READ | all 102 lines; tails of the 26 long lines read capped at 900 characters each |
| handover/demo/ORDERS.md | 88250 | READ | lines 1 to 360, long lines read in two passes (first 520 to 900 characters, then the rest) |
| handover/demo/REPORT.md | 664750 | SKIMMED | over 200 KB: top block (lines 4 to 15), section headers (153), slices 1685 to 1860 and 2834 to 2838 by key grep (restart, memory, heartbeat, unverified, limitation=0); NOT read in full |
| handover/demo/drift/DRIFT-REPORT-1.md | 9850 | READ | whole file, long lines read in two passes |
| handover/demo/drift/REVIEW-1.md | 3198 | READ | whole file, long lines read in two passes |
| handover/demo/drift/docs-fixes.patch | 6724 | NOT-READ | partly read: first 60 lines (cut at 300) |
| handover/demo/followup/REVIEW-nodemo-v5-fresh.md | 9878 | NOT-READ | partly read: first 6 lines |
| handover/demo/followup/followup-a-fails-before.txt | 1005 | READ | whole file |
| handover/demo/followup/followup-a-review-fresh.md | 5336 | NOT-READ | partly read: first 6 lines |
| handover/demo/followup/followup-a.patch | 21783 | NOT-READ | not opened (size and time) |
| handover/demo/followup/followup-ab-review-fresh2.md | 11002 | NOT-READ | partly read: first 6 lines |
| handover/demo/followup/followup-ab-v2-DO-NOT-USE-has-type-ignore.patch | 84353 | NOT-READ | not opened (size and time) |
| handover/demo/followup/followup-ab-v3-review-fresh3.md | 6811 | NOT-READ | partly read: first 6 lines |
| handover/demo/followup/followup-ab-v3.patch | 85164 | NOT-READ | not opened (size and time) |
| handover/demo/followup/followup-ab.patch | 54154 | NOT-READ | not opened (size and time) |
| handover/demo/followup/followup-b-fails-before.txt | 1865 | READ | whole file |
| handover/demo/followup/followup-b.patch | 30024 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/MERGE-READINESS-2-4.md | 17727 | NOT-READ | partly read: lines 1 to 60 (cut at 380 characters) |
| handover/demo/merge-ready/REVIEW-1.md | 5057 | READ | whole file, long lines read in two passes |
| handover/demo/merge-ready/REVIEW-3.md | 3060 | READ | whole file, long lines read in two passes |
| handover/demo/merge-ready/REVIEW-sonar-crlf-fresh.md | 7671 | NOT-READ | partly read: first 6 lines |
| handover/demo/merge-ready/SONAR-YAML-DELTA-V2-NOTES.md | 1133 | READ | whole file |
| handover/demo/merge-ready/SONAR-YAML-FIX-V2-NOTES.md | 666 | READ | whole file |
| handover/demo/merge-ready/SONAR-YAML-TRIMMED-V2-NOTES.md | 2187 | READ | whole file |
| handover/demo/merge-ready/evidence-b10-7-yaml-trimmed-mutants.txt | 8213 | SKIMMED | run log: head, tail and survivor grep |
| handover/demo/merge-ready/evidence-b10-9-yaml-gates.txt | 224 | READ | whole file |
| handover/demo/merge-ready/evidence-b3-3-apply-matrix.txt | 1296 | READ | whole file |
| handover/demo/merge-ready/evidence-b3-5-sonar-v2-mutants-gates.txt | 2874 | SKIMMED | run log: head, tail |
| handover/demo/merge-ready/evidence-b7-2-sonar-delta-mutants.txt | 6172 | SKIMMED | run log: head, tail |
| handover/demo/merge-ready/evidence-b7-4-apply-matrix.txt | 621 | READ | whole file |
| handover/demo/merge-ready/evidence-m-1-cheap-f5fe824.txt | 7554 | SKIMMED | run log: head, tail and survivor grep only |
| handover/demo/merge-ready/evidence-m-2-hygiene-f5fe824.txt | 144 | READ | whole file |
| handover/demo/merge-ready/evidence-m-3-branch-heads.txt | 1521 | READ | whole file |
| handover/demo/merge-ready/evidence-m-4-mutants.txt | 3432 | SKIMMED | run log: head, tail and survivor grep only |
| handover/demo/merge-ready/evidence-m-5-detector-gap.txt | 746 | READ | whole file |
| handover/demo/merge-ready/evidence-m-6-gates-patched.txt | 664 | READ | whole file |
| handover/demo/merge-ready/evidence-m-7-skip-require.txt | 661 | READ | whole file |
| handover/demo/merge-ready/evidence-m-8-apply-orders.txt | 464 | READ | whole file |
| handover/demo/merge-ready/evidence-m-9-combined-tree.txt | 450 | READ | whole file |
| handover/demo/merge-ready/evidence-m2-1-measure.txt | 21878 | SKIMMED | run log: head and tail only (217 lines) |
| handover/demo/merge-ready/evidence-m2-2-mutants.txt | 9373 | SKIMMED | run log: head, tail and survivor line |
| handover/demo/merge-ready/evidence-m2-3-gates.txt | 2099 | SKIMMED | run log: head and tail |
| handover/demo/merge-ready/evidence-m2-4-apply-and-clean-tree.txt | 1140 | READ | whole file |
| handover/demo/merge-ready/evidence-m3-3-gates.txt | 947 | READ | whole file |
| handover/demo/merge-ready/evidence-m3-4-apply-and-clean-tree.txt | 491 | READ | whole file |
| handover/demo/merge-ready/evidence-m3-5-workflow-triggers.txt | 2110 | READ | whole file |
| handover/demo/merge-ready/evidence-m3-mutants.txt | 8860 | SKIMMED | run log: head, tail and survivor lines |
| handover/demo/merge-ready/merge-ready-hygiene-v2.patch | 11476 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/merge-ready-hygiene-v3.patch | 12804 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/merge-ready-hygiene.patch | 8155 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/sonar-yaml-fix-v2.patch | 6394 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/sonar-yaml-fix.patch | 2942 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/sonar-yaml-test-delta-on-db54e13.patch | 5803 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/sonar-yaml-test-delta-v2.patch | 8291 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/sonar-yaml-test-trimmed-v2-after-p1v3.patch | 5499 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/sonar-yaml-test-trimmed-v2.patch | 5465 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/sonar-yaml-test-trimmed.patch | 5430 | NOT-READ | not opened (size and time) |
| handover/demo/merge-ready/versions-md-allowance.patch | 2566 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/AB-PAPER.md | 14142 | NOT-READ | partly read: first 45 lines (cut at 420 characters) |
| handover/demo/pr-stack/CARRY-OVER-CHECKLIST.md | 48064 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/checklist.py | 5164 | NOT-READ | partly read: first 70 lines |
| handover/demo/pr-stack/evidence-ab-ancestry-browser.txt | 8313 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/evidence-ab-api-counts.txt | 234 | READ | whole file |
| handover/demo/pr-stack/evidence-ab-api-summary.txt | 2207 | SKIMMED | scan output: first 14 lines |
| handover/demo/pr-stack/evidence-ab-checklist-stats.txt | 929 | NOT-READ | first 12 lines |
| handover/demo/pr-stack/evidence-ab-checks.txt | 8249 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/evidence-ab-ci-durations.txt | 5462 | SKIMMED | scan output: first 14 lines |
| handover/demo/pr-stack/evidence-ab-diffstat.txt | 3454 | SKIMMED | scan output: first 14 lines |
| handover/demo/pr-stack/evidence-ab-findings-breakdown.txt | 2304 | SKIMMED | scan output: first 14 lines |
| handover/demo/pr-stack/evidence-ab-sonar-run.txt | 779 | NOT-READ | first 12 lines |
| handover/demo/pr-stack/evidence-ab-sonar-yaml.txt | 456 | NOT-READ | first 12 lines |
| handover/demo/pr-stack/evidence-ab-workflows.txt | 14193 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-issues-1-comments.json | 31018 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-issues-2-comments.json | 58490 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-issues-3-comments.json | 68655 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-issues-4-comments.json | 75701 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-pull-1.json | 21824 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-pull-2.json | 24689 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-pull-3.json | 24677 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-pull-4.json | 24480 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-pulls-1-comments.json | 56816 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-pulls-1-reviews.json | 4475 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-pulls-2-comments.json | 358200 | SKIMMED | over 200 KB: only searched for e-mail and key patterns (none real) |
| handover/demo/pr-stack/raw-pulls-2-reviews.json | 22919 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-pulls-3-comments.json | 291178 | SKIMMED | over 200 KB: only searched for e-mail and key patterns (none real) |
| handover/demo/pr-stack/raw-pulls-3-reviews.json | 4171 | NOT-READ | not opened (size and time) |
| handover/demo/pr-stack/raw-pulls-4-comments.json | 3793943 | SKIMMED | over 200 KB: only searched for e-mail and key patterns (1015 matches, all made-up test addresses or decorators) |
| handover/demo/pr-stack/raw-pulls-4-reviews.json | 25131 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/REVIEW-MAP-PR4.md | 24608 | NOT-READ | partly read: first 6 lines |
| handover/demo/pr-text/REVIEW-pr2-4.md | 6929 | READ | whole file, long lines read in two passes |
| handover/demo/pr-text/github-current/pr2-body.md | 3473 | READ | whole file |
| handover/demo/pr-text/github-current/pr3-body.md | 3452 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/github-current/pr4-body.md | 3219 | READ | whole file |
| handover/demo/pr-text/list-rows.tsv | 10089 | NOT-READ | partly read: first 5 lines |
| handover/demo/pr-text/proposed/QUESTIONS-FOR-LEAD.md | 4303 | READ | whole file, long lines read in two passes |
| handover/demo/pr-text/proposed/VERIFY.md | 21571 | NOT-READ | partly read: lines 1 to 25 |
| handover/demo/pr-text/proposed/pr2-user-description-v2.md | 3411 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr2-user-description-v3.md | 3819 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr2-user-description-v4.md | 3766 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr2-user-description-v5.md | 3574 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr2-user-description.md | 4377 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr3-user-description-v2.md | 3498 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr3-user-description-v3.md | 3915 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr3-user-description-v4.md | 3862 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr3-user-description-v5.md | 3670 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr3-user-description.md | 3848 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr4-A-user-description.md | 8596 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr4-user-description-v2.md | 9817 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr4-user-description-v3.md | 10418 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr4-user-description-v4.md | 10353 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr4-user-description-v5.md | 10539 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/proposed/pr4-user-description.md | 10590 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/semgrep-pr-body-v2.md | 13414 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/semgrep-pr-body-v3.md | 14007 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/semgrep-pr-body-v4.md | 15243 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/semgrep-pr-body-v5.md | 15951 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/semgrep-pr-body-v6.md | 20538 | NOT-READ | partly read: first 6 lines; versions diffed by line count |
| handover/demo/pr-text/semgrep-pr-body.md | 10892 | NOT-READ | not opened (size and time) |
| handover/demo/pr-text/semgrep-pr-claims-v6.md | 14124 | NOT-READ | partly read: first 6 lines |
| handover/demo/pr-text/semgrep-pr-claims.md | 26082 | NOT-READ | not opened (size and time) |
| handover/demo/reuse/CORE-TO-DEMO.md | 52671 | NOT-READ | read lines 1 to 160 with long lines cut at 520 to 650 characters; tails of those lines and the rest not read |
| handover/demo/reuse/RESOLVE-1.md | 9421 | NOT-READ | not opened (size and time) |
| handover/demo/reuse/RESOLVE-2.md | 6275 | NOT-READ | not opened (size and time) |
| handover/demo/reuse/RESOLVE-3.md | 6484 | NOT-READ | partly read: first 6 lines |
| handover/demo/reuse/REVIEW-1.md | 5176 | NOT-READ | not opened (size and time) |
| handover/demo/reuse/REVIEW-2.md | 8949 | NOT-READ | not opened (size and time) |
| handover/demo/reuse/REVIEW-3.md | 7854 | NOT-READ | not opened (size and time) |
| handover/demo/reuse/REVIEW-4.md | 4336 | NOT-READ | partly read: first 6 lines |
| handover/demo/semgrep-pr-diff-lead.patch | 99235 | NOT-READ | not opened (size and time) |
| handover/demo/speed/RUNBOOK-INPUTS.md | 4079 | READ | whole file, long lines read in two passes |
| handover/demo/speed/RUNBOOK-SPEED-3.md | 16412 | NOT-READ | not opened (size and time) |
| handover/demo/speed/SHA256SUMS | 705 | READ | whole file |
| handover/demo/speed/ci-xdist-demo-b29bb1f.patch | 6428 | NOT-READ | not opened (size and time) |
| handover/demo/speed/compare-norm.py | 1737 | READ | first 50 lines = whole file |
| handover/demo/speed/evidence-phase4.md | 7773 | NOT-READ | partly read: lines 1 to 16 |
| handover/demo/speed/fake-hubspot-read-body-before-answer.patch | 3165 | NOT-READ | not opened (size and time) |
| handover/demo/speed/quiet-check.sh | 700 | READ | whole file |
| handover/demo/speed/run-demo-linux.sh | 2227 | READ | whole file |
| handover/demo/speed/run-ledger.tsv | 572 | READ | whole file |
| handover/demo/speed/run-sdk-linux.sh | 2278 | READ | whole file (diffed against run-demo-linux.sh) |
| handover/demo/speed/xdist-overlay-hashes.txt | 375 | READ | whole file |
| handover/tools/egm_model_patch.py | 3283 | READ | whole file |
| handover/tools/egm_setup.sh | 3937 | READ | whole file |

## Components
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L1-C-001 | desk (lead desk app, package src/lead_desk) | receives leads, stops duplicates, copies to CRM, sends follow-up mail; the "Mode A" product | `handover/system-map/DECISION-one-store.md:6 "desk SQLite + portal (Mode A"`; `handover/demo/drift/DRIFT-REPORT-1.md:17 "Code: src/lead_desk/portal_api.py:311-314"` | STORE; FILTER; RETRY; NOTICE; COUNTER |
| L1-C-002 | portal (browser pages of the desk) | read pages and buttons over the desk records (leads, review, overview) | `handover/system-map/DECISION-one-store.md:15 "The desk SQLite and its portal are retired from the take"` | STORE; NOTICE |
| L1-C-003 | n8n take flows (film-v5 and real-v5) | the video take: n8n nodes claim, store and mark each lead in Postgres | `handover/system-map/DECISION-one-store.md:7 "written by the n8n Postgres nodes Claim, Stored"` | STORE; FILTER; RETRY |
| L1-C-004 | n8n workflow files shipped in the public demo repo | three nodes each (desk-form, desk-webhook, proof-run) that post to the desk | `handover/demo/drift/DRIFT-REPORT-1.md:44 "paths desk-form / desk-webhook / proof-run"` | FILTER |
| L1-C-005 | demo_only fakes (fake_hubspot, fake_smtp_tls, fake_imap, fake_model_server, portal_demo) | stand-in CRM, mail, AI and portal servers for tests and the video | `handover/demo/ORDERS.md:89 "answered 401/404 and closed with the request body unread"`; `handover/demo/ORDERS.md:230 "With demo_only/ DELETED, 6 tests fail"` | OTHER |
| L1-C-006 | load_tools (check_invariants, load_driver, feed) and scripts (run_real_check, n8n_api, reset) | checks after a load run, real-run start path, n8n API helper | `handover/demo/ORDERS.md:203 "load_tools/check_invariants.py L63,82,597,605,614 and more"` | COUNTER; LOG |
| L1-C-007 | tools/scrub_n8n_export.py | removes private values from an n8n export before it is shown | `handover/demo/ORDERS.md:203 "tools/scrub_n8n_export.py L102"` | FILTER |
| L1-C-008 | public-repo CI workflows lint.yml, codeql.yml, sonar.yml (and semgrep.yml as its own later PR) | scans and tests on GitHub | `handover/demo/merge-ready/MERGE-READINESS-2-4.md:12 "with the SAME triggers"` | LOG; NOTICE |
| L1-C-009 | review bots (CodeAnt, DeepSource, CodeRabbit, SonarCloud, CodeQL) | outside reviewers that comment on pull requests | `handover/demo/pr-stack/AB-PAPER.md:41 "No human review thread exists on any of the four pull requests"` | NOTICE |
| L1-C-010 | EGM plugin egm@egm (skills and reviewer agent types) | the studio review workflow, installed per session | `handover/CLOUD-EGM-SETUP-2026-11-12.md:5 "/plugin install egm@egm"` | OTHER |
| L1-C-011 | speed harness (xdist patch, quiet check, compare script, run ledger) | proves tests run faster in parallel without changing results | `handover/demo/speed/RUNBOOK-SPEED-3.md:3 "Not reviewed"` | COUNTER; LOG |
| L1-C-012 | core modules compared against the demo (text fold, mutation runner, scan guard, client-profile check, spend meter) | the shared core that the demo partly re-implements | `handover/demo/reuse/CORE-TO-DEMO.md:23 "text fold vs email/name keys"` | COUNTER; FILTER |
| L1-C-013 | heavy_slot.py and heavy.sh (queue for heavy test runs) | limits how many heavy runs run at once | NOT VISIBLE: tools/heavy_slot.py; NOT VISIBLE: /home/user/build/heavy.sh | COUNTER |

## Stores
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1-S-001 | desk SQLite database (desk.sqlite3 plus schema, followups and nudges tables) | receipts, claims, counts, portal rows of the Mode A product | desk (src/lead_desk); retired from the take by DECISION | lead submissions, CRM and mail results | portal pages, counts | lock file refuses a second desk (exit 2) | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | DRIFT-REPORT-1 matched schema triggers and columns to contract.md | desk, portal | `handover/demo/ORDERS.md:227 "the desk does NOT store the sent mail"`; `handover/demo/drift/DRIFT-REPORT-1.md:48 "db_path ./data/desk.sqlite3"` | STORE; COUNTER |
| L1-S-002 | Postgres table mf_leads (take) | one row per lead: state, CRM id, mail claim, alert state | n8n Postgres nodes of the take (DECISION) | n8n nodes Claim, Stored, SetCrmId, MailClaim, MarkDone and the recovery flow | lead state rows | UNVERIFIED | recovery flow (UNVERIFIED how often) | UNVERIFIED | unique key per lead id | n8n execution history | UNVERIFIED | WP6 smoke P11 (NOT VISIBLE: wp6 evidence) | n8n take flows | `handover/system-map/DECISION-one-store.md:7 "written by the n8n Postgres nodes Claim, Stored"` | STORE; FILTER; LOG |
| L1-S-003 | n8n internal data (workflows, credentials, execution history) | n8n internals and the execution log | n8n | N/A: store | N/A: store | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | itself | UNVERIFIED | NOT VISIBLE: evidence-1 s12.log | n8n | `handover/system-map/DECISION-one-store.md:8 "n8n ran on its DEFAULT SQLITE"` | STORE; LOG |
| L1-S-004 | stage.journal file | write-ahead record of model calls so a kill cannot cause a second call | qualify_stage.py (take) | model call start and finish per lead key | a file in the take folder | UNVERIFIED | N/A: guard | UNVERIFIED | write-ahead per key | itself | UNVERIFIED | WP6 P11 (NOT VISIBLE) | take stage | `handover/system-map/DECISION-one-store.md:9 "file in the take folder (qualify_stage.py)"` | STORE; COUNTER |
| L1-S-005 | SpendLedger (JSON-lines file plus OS lock file) in src/lead_desk/live_claude.py | money guard: reserve worst-case cost, settle after the call, per-run and plan-total caps | demo live-model path (public repo) | model call cost | reserve and settle rows | unreadable or locked ledger refuses to spend | UNVERIFIED | UNVERIFIED | unique reservation ids | itself | UNVERIFIED | demo tests (names NOT VISIBLE here) | demo real run | `handover/demo/reuse/CORE-TO-DEMO.md:92 "is one JSON-lines file with an OS lock file"` | STORE; COUNTER |
| L1-S-006 | handover/demo/REPORT.md | the one report file of the demo session (153 dated blocks) | demo session | status blocks every 5 minutes | read by the lead | UNVERIFIED | N/A: document | N/A: document | N/A: append only | itself | demo cloud session | N/A: document | lead | `handover/demo/REPORT.md:2 "Write a status block at least every 10 minutes"` | LOG; NOTICE |
| L1-S-007 | handover/demo/ORDERS.md | orders and answers from the lead to the demo session (about 60 blocks) | lead | lead decisions | read by the demo session | UNVERIFIED | N/A: document | N/A: document | N/A: append only | itself | lead | N/A: document | demo session | `handover/demo/ORDERS.md:1 "DEMO session orders (the lead writes here"` | LOG; NOTICE |
| L1-S-008 | handover/demo/APPLY-LIST.md | ordered list of patches with review and apply-check status | demo session | patch status | read by the lead | UNVERIFIED | N/A: document | N/A: document | N/A: append only | itself | demo cloud session | N/A: document | lead | `handover/demo/APPLY-LIST.md:1 "Last update 2026-11-12 20:38Z"` | LOG |
| L1-S-009 | handover/demo/speed/run-ledger.tsv | timing ledger of serial and parallel test runs (2 example rows) | speed builder | run results | rows | N/A: file | N/A: file | N/A: file | N/A: append only | itself | laptop builder | N/A: file | speed runbook | `handover/demo/speed/run-ledger.tsv:2 "10033 passed 492 skipped"` | LOG; COUNTER |
| L1-S-010 | cloud-register.md (register of review children) | one row per agent or child process (id, purpose, times) | demo or core cloud session | rows written before each start | read at expected end | UNVERIFIED | N/A: file | N/A: file | N/A: file | itself | cloud session | N/A: file | supervision | `handover/EGM-CHILD-HOWTO.md:11 "Register each child in cloud-register.md"`; NOT VISIBLE: cloud-register.md | LOG |
| L1-S-011 | blocker ledger rows (BL- ids) | every blocker and major, status OPEN or FIXED | lead | review findings | status per finding | N/A: document | N/A: document | N/A: document | N/A: document | itself | lead | NOT VISIBLE: handover/ledger.md | lead | `handover/demo/ORDERS.md:277 "ledger stays OPEN"` | LOG |
| L1-S-012 | pr-stack raw API snapshots (raw-*.json, 16 files, 4.9 MB) | saved GitHub API answers about pull requests 1 to 4 and their comments | demo session (a one-off read) | gh API | JSON files used by checklist.py | N/A: snapshot | N/A: snapshot | N/A: snapshot | N/A: snapshot | N/A: snapshot | none (public API, no token) | checklist.py | carry-over checklist | `handover/demo/pr-stack/AB-PAPER.md:4 "Data fetched 2026-11-13 from the public GitHub API"` | STORE |
| L1-S-013 | desk counts endpoint /counts (received, new, duplicate, replayed) | the count the independent check reads | desk | each submission | HTTP answer | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | README run in DRIFT-REPORT-1 | proof screens | `handover/demo/drift/DRIFT-REPORT-1.md:50 "/counts answered HTTP/1 200"` | COUNTER |
| L1-S-014 | fake outbox (/fake/outbox of the stand-in mail server) | holds mails the fake server accepted | demo_only fake | desk mail sends | count of mails | N/A: fake | N/A: fake | N/A: fake | N/A: fake | N/A: fake | N/A: fake | burst test in limits.md run | demo | `handover/demo/drift/DRIFT-REPORT-1.md:50 "/fake/outbox"` | STORE; COUNTER |

## Workflows
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1-W-001 | n8n take flows film-v5 and real-v5 plus recovery flow | claim, store, copy to CRM, send mail, mark done, recover stuck rows | n8n | lead submission | mf_leads rows, CRM record, mail | UNVERIFIED | recovery flow | UNVERIFIED | unique key on lead id | n8n execution history | UNVERIFIED | NOT VISIBLE: WP6 smoke | video take | `handover/system-map/DECISION-one-store.md:7 "written by the n8n Postgres nodes Claim, Stored"` | STORE; FILTER; RETRY |
| L1-W-002 | n8n flows in the public demo repo | form and webhook paths into the desk plus a proof run | n8n | form or webhook post | post to desk on port 8765 | retry on fail | 3 tries 1000 ms | 15000 ms | UNVERIFIED | n8n | UNVERIFIED | DRIFT-REPORT-1 compared files only | demo | `handover/demo/drift/DRIFT-REPORT-1.md:44 "retry on fail 3 tries 1000 ms, timeout 15000 ms"` | FILTER; RETRY |
| L1-W-003 | lint.yml (GitHub) | gitleaks, ruff, format, mypy x2, bandit, schema check, literal scan, canary guard, tests | GitHub | pull request into main, push to main | pass or fail | step fails the run | N/A: CI | UNVERIFIED | N/A: CI | GitHub run log | GitHub Actions | itself | public repo | `handover/demo/merge-ready/MERGE-READINESS-2-4.md:12 "with the SAME triggers"` | LOG |
| L1-W-004 | codeql.yml (GitHub) | code scanning for python, actions, javascript | GitHub | pull request into main, push, weekly | alerts | UNVERIFIED | N/A: CI | UNVERIFIED | N/A: CI | GitHub | GitHub Actions | itself | public repo | `handover/demo/merge-ready/MERGE-READINESS-2-4.md:12 "with the SAME triggers"` | LOG |
| L1-W-005 | sonar.yml (GitHub) | full tests with coverage then SonarQube scan | GitHub | every pull request, push to main | quality gate | tests fail then scan stops | N/A: CI | 60 minutes in patch | N/A: CI | GitHub and SonarCloud | repository secret SONAR_TOKEN | itself | public repo | `handover/demo/merge-ready/MERGE-READINESS-2-4.md:10 "the repository secret"` | LOG; COUNTER |
| L1-W-006 | semgrep.yml (own later pull request) | Semgrep ERROR-level scan with packs p/python and p/javascript | GitHub | pull request and push to main | findings | UNVERIFIED | N/A: CI | UNVERIFIED | N/A: CI | GitHub log | GitHub Actions | tests/test_nosemgrep_form.py | demo repo (not merged) | `handover/demo/pr-text/semgrep-pr-body-v6.md:1 "Semgrep is a code scanner that looks for known risky code patterns"` | LOG |
| L1-W-007 | EGM review step run as a child process (claude -p) | one review per child, report to a file | cloud session | snapshot, ticket, evidence | review file | headless run blocked shell commands, no report | UNVERIFIED | 1800 s | N/A: review | child log file | cloud session | not yet tested (see HOWTO) | demo and core cloud sessions | `handover/EGM-CHILD-HOWTO.md:13 "NOT yet tested: a full review run"` | OTHER |

## Workflow walk
| id | flow | node | type | trigger or branch | error path | retry or timeout | on kill or restart | on duplicate | on out-of-order | on empty or huge input | writes where | person sees | identity | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1-WK-001 | L1-W-001 | Claim | Postgres node | new lead | UNVERIFIED | UNVERIFIED | UNVERIFIED | unique key refuses a second row | UNVERIFIED | UNVERIFIED | mf_leads | UNVERIFIED | UNVERIFIED | `handover/system-map/DECISION-one-store.md:7 "unique key = no double work"` |
| L1-WK-002 | L1-W-001 | Stored | Postgres node | after Claim | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | mf_leads | UNVERIFIED | UNVERIFIED | `handover/system-map/DECISION-one-store.md:7 "written by the n8n Postgres nodes Claim, Stored"` |
| L1-WK-003 | L1-W-001 | SetCrmId | Postgres node | after CRM create | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | mf_leads | UNVERIFIED | UNVERIFIED | `handover/system-map/DECISION-one-store.md:7 "SetCrmId, MailClaim, MarkDone"` |
| L1-WK-004 | L1-W-001 | MailClaim | Postgres node | before mail | UNVERIFIED | UNVERIFIED | UNVERIFIED | mail claim column prevents second mail | UNVERIFIED | UNVERIFIED | mf_leads | UNVERIFIED | UNVERIFIED | `handover/system-map/DECISION-one-store.md:7 "SetCrmId, MailClaim, MarkDone"` |
| L1-WK-005 | L1-W-001 | recovery flow | n8n flow | stuck rows | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | mf_leads | UNVERIFIED | UNVERIFIED | `handover/system-map/DECISION-one-store.md:7 "and the recovery flow"` |
| L1-WK-006 | L1-W-002 | desk-form | n8n node chain (3 nodes) | form submission | retry on fail | 3 tries 1000 ms, timeout 15000 ms | UNVERIFIED | desk answers replayed true on a repeat | UNVERIFIED | UNVERIFIED | desk database | UNVERIFIED | UNVERIFIED | `handover/demo/drift/DRIFT-REPORT-1.md:44 "paths desk-form / desk-webhook / proof-run"` |
| L1-WK-007 | L1-W-002 | desk-webhook | n8n node chain (3 nodes) | webhook post | retry on fail | 3 tries 1000 ms, timeout 15000 ms | UNVERIFIED | answer duplicate | UNVERIFIED | UNVERIFIED | desk database | UNVERIFIED | UNVERIFIED | `handover/demo/drift/DRIFT-REPORT-1.md:50 "webhook 1 gave 200 duplicate"` |
| L1-WK-008 | L1-W-003 | gitleaks tree and history | CI step | pull request into main | step fails | N/A: CI | N/A: CI | N/A: CI | order matters, runs first | UNVERIFIED | GitHub log | red check | GitHub Actions | `handover/demo/merge-ready/MERGE-READINESS-2-4.md:37 "Order matters in CI: step 1 and 2 run first"` |
| L1-WK-009 | L1-W-003 | ruff, format, mypy linux and win32, bandit | CI steps | after install | step fails | N/A: CI | N/A: CI | N/A: CI | N/A: CI | N/A: CI | GitHub log | red check | GitHub Actions | `handover/demo/merge-ready/MERGE-READINESS-2-4.md:30 "canary guard"` |
| L1-WK-010 | L1-W-003 | tests (everything) | CI step | after the checks | step fails | N/A: CI | N/A: CI | N/A: CI | N/A: CI | skips hide browser and gitleaks tests | GitHub log | red check | GitHub Actions | `handover/demo/ORDERS.md:164 "3096 passed, 45 skipped, 0 failed"` |
| L1-WK-011 | L1-W-005 | tests then scan | CI steps | every pull request | tests fail so scan stops | UNVERIFIED | cancel-in-progress cancels an older run | N/A: CI | N/A: CI | N/A: CI | SonarCloud | gate result | repository secret SONAR_TOKEN | `handover/demo/APPLY-LIST.md:102 "STATUS 02:08Z (session lead): URGENT FIX"` |

## Scripts
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1-X-001 | handover/demo/speed/run-demo-linux.sh | clone the public demo, apply patches, run serial or parallel tests, write results | speed builder | mode, run number, workers | out/<mode><run>/ files | exit 2 on setup failure, exit 3 if the machine is not quiet | N/A: script | 2700 s (timeout) | clones once into dpld | files under out/ | the cloud shell user | NOT FOUND | laptop or cloud session | `handover/demo/speed/run-demo-linux.sh:3 "~119 browser tests skip"` | COUNTER; LOG |
| L1-X-002 | handover/demo/speed/run-sdk-linux.sh | same for hadavin-sdk with xdist overlay | speed builder | mode, run number | out/sdk-<mode><run>/ | exit 2 on setup, exit 3 if not quiet | N/A: script | none set for sdk modes | N/A: script | files under out/ | shell user | NOT FOUND | laptop or cloud | `handover/demo/speed/run-sdk-linux.sh:2 "hadavin-sdk, Linux, no docker"` | COUNTER; LOG |
| L1-X-003 | handover/demo/speed/quiet-check.sh | refuses a timed run when another test process runs or load is 1.0 or more | speed builder | output file | exit 0 quiet, exit 3 not quiet | exit 3 | N/A: script | N/A: script | N/A: script | sample file | shell user | NOT FOUND | both run scripts | `handover/demo/speed/quiet-check.sh:2 "Exit 0 = quiet, exit 3 = another lane is running"` | COUNTER |
| L1-X-004 | handover/demo/speed/compare-norm.py | compares test ids and outcomes of junit files | speed builder | junit xml files | IDENTICAL or DIFFERENT, exit code | exit 1 on mismatch | N/A: script | N/A: script | N/A: script | stdout | shell user | NOT FOUND | speed runbook | `handover/demo/speed/compare-norm.py:1 "throwaway: compare.py A.xml B.xml"` | OTHER |
| L1-X-005 | handover/demo/pr-stack/checklist.py | builds the carry-over checklist from saved API JSON and a clone | demo session | raw-*.json, a read-only clone | CARRY-OVER-CHECKLIST.md | UNVERIFIED | N/A: script | N/A: script | N/A: script | stdout | shell user | NOT FOUND | pr-stack | `handover/demo/pr-stack/checklist.py:1 "Build the carry-over checklist from the saved API JSON"` | OTHER |
| L1-X-006 | handover/tools/egm_model_patch.py | sets the model line of every EGM skill and agent file, removes the flag that blocks model calls | lead | plugin folders under ~/.claude/plugins | changed files, printed list | exit 1 if no plugin found | idempotent | N/A: script | idempotent | stdout | session user | NOT FOUND | cloud sessions | `handover/tools/egm_model_patch.py:25 "def find_roots"` | OTHER |
| L1-X-007 | handover/tools/egm_setup.sh | environment setup: install EGM, run the model patch (embedded copy), print the check | lead | none | patched plugins | exit 1 if install refused | idempotent | none | idempotent | stdout | setup script identity | NOT FOUND | claude.ai environment setup field | `handover/tools/egm_setup.sh:33 "def find_roots"` | OTHER |
| L1-X-008 | the child pattern `claude -p` with timeout | run one EGM step as a fresh process | cloud session | snapshot, ticket, evidence | report file and log | blocked shell commands gave NOT DETERMINED | UNVERIFIED | 1800 s | N/A: review | log file next to the report | session user | not yet tested | cloud sessions | `handover/EGM-CHILD-HOWTO.md:7 "timeout 1800 claude -p"` | OTHER |

## Jobs
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1-J-001 | heartbeat loop of the demo session | guarantees a new report block every 5 minutes | demo session | clock | a block in REPORT.md | UNVERIFIED | N/A: loop | UNVERIFIED | N/A: loop | REPORT.md | demo cloud session | NOT FOUND | lead | `handover/demo/REPORT.md:13 "heartbeat loop"` | NOTICE; LOG |
| L1-J-002 | 5-minute report cadence | a block at the top of REPORT.md with three tables | demo session | clock | REPORT.md | breach if block older than 5 minutes | N/A: cadence | N/A: cadence | N/A: cadence | REPORT.md | demo session | NOT FOUND | lead, owner | `handover/demo/ORDERS.md:150 "EVERY 5 MINUTES by the clock"` | NOTICE |
| L1-J-003 | 6-minute lead command cadence | the lead writes answers and orders at the bottom of ORDERS.md | lead | demo reports | ORDERS.md blocks | blocks were pushed empty once | N/A: cadence | N/A: cadence | N/A: cadence | ORDERS.md | lead | NOT FOUND | demo session | `handover/demo/ORDERS.md:160 "pushed EMPTY"` | NOTICE |
| L1-J-004 | desk reaper (background thread of the desk) | re-runs stuck sends and copies | desk | stuck rows | retried sends | two unbounded waits in the loop (not run to failure) | backoff 1, 2, 4, 8 s (5 tries) | stuck grace 30 s | UNVERIFIED | desk log | desk process | tests/test_hung_adapter_calls.py ran 30 times without a hang | desk | `handover/demo/REPORT.md:2838 "TWO UNBOUNDED LOOPS in the reaper"`; `handover/demo/drift/DRIFT-REPORT-1.md:49 "5 tries"` | RETRY |
| L1-J-005 | chunked full-run driver | runs the suite in 10 resumable chunks because the container restarted | demo session | test files | counts per chunk | container restart kills a chunk | resume at chunk granularity | 1 to 7 minutes per chunk | resumable | chunk output files | shell user | itself | lead gate | `handover/demo/REPORT.md:1785 "resumable scripts"` | RETRY; COUNTER |
| L1-J-006 | un-chunked full run on the final head | single-process proof the lead requires | demo session or lead laptop | final head | counts | restart kills it | rerun | about 22 minutes | N/A: run | log file | shell user | N/A: run | lead | `handover/demo/ORDERS.md:131 "UN-CHUNKED full run"` | COUNTER |
| L1-J-007 | bounded Sonar waiter (lead side) | reads SonarCloud for a pushed head | lead | pushed head | issue lists in ORDERS | 403 for the cloud session | N/A: waiter | bounded | N/A: waiter | ORDERS.md | lead | NOT FOUND | lead | `handover/demo/ORDERS.md:301 "bounded waiter reads Sonar"` | NOTICE |
| L1-J-008 | supervision register check | every started agent is registered and checked at its end | each cloud session | register rows | closed rows | UNVERIFIED | N/A: check | expected end per row | N/A: check | register | cloud session | NOT FOUND | lead | `handover/CLOUD-EGM-SETUP-2026-11-12.md:9 "keep a register file"` | LOG |

## Credentials
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1-K-001 | SONAR_TOKEN (repository secret) | lets sonar.yml upload the scan | repository owner | N/A: credential | N/A: credential | scan step fails without it | N/A: credential | N/A: credential | N/A: credential | GitHub | GitHub Actions | NOT FOUND | sonar.yml | `handover/demo/merge-ready/MERGE-READINESS-2-4.md:10 "the repository secret"` | OTHER |
| L1-K-002 | GH_TOKEN of the cloud session (reported invalid) | GitHub API reads | cloud session | N/A: credential | N/A: credential | API calls had to go unauthenticated | N/A: credential | N/A: credential | N/A: credential | none | cloud session | NOT FOUND | pr-stack data | `handover/demo/pr-stack/AB-PAPER.md:4 "the session's GH_TOKEN is invalid"` | OTHER |
| L1-K-003 | live model key file (read by LiveQualifier._read_key) | key for the live AI step in a real run | owner on the laptop | N/A: credential | N/A: credential | refuse at start (D1 order) | N/A: credential | N/A: credential | N/A: credential | none | desk process | planned fail-before tests | real run | `handover/demo/ORDERS.md:239 "LiveQualifier._read_key"` | OTHER |
| L1-K-004 | HubSpot key (crm_hubspot._key) | CRM access in a real run | owner | N/A: credential | N/A: credential | refuse with a message | N/A: credential | N/A: credential | N/A: credential | none | desk process | planned | real run | `handover/demo/ORDERS.md:310 "crm_hubspot.py _key"` | OTHER |
| L1-K-005 | SMTP secret file (smtp_provider.read_secret_file) | mail send in a real run | owner | N/A: credential | N/A: credential | refuse with a message | N/A: credential | N/A: credential | N/A: credential | none | desk process | planned | real run | `handover/demo/ORDERS.md:310 "smtp_provider.py read_secret_file"` | OTHER |
| L1-K-006 | n8n credentials and mailbox logins (placed by the owner in the n8n credentials page) | the take's real accounts | owner only | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | n8n | n8n | NOT FOUND | take | `handover/RULE-R456-WORK-CONDUCT.md:19 "Real keys, accounts, mailboxes: only the owner places them"` | OTHER |
| L1-K-007 | DeepSource login (owner account) | per-finding export | owner | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | none | owner | NOT FOUND | triage | `handover/demo/ORDERS.md:31 "needs the owner's login"` | OTHER |

## Docs and tests and folders
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L1-D-001 | handover/BRIEF-PREAMBLE.md | the studio rules that start every agent brief (rules 1 to 21); identical to lines 1 to 23 of work/BRIEF-LANE.md | `handover/BRIEF-PREAMBLE.md:21 "never spawn sub-agents unless your brief says so"` | N/A: no job key |
| L1-D-002 | handover/MODEL-ROUTING.md | which model does which job, with two overrides and a revert kept in the same file | `handover/MODEL-ROUTING.md:45 "REVERT 2026-11-11"` | N/A: no job key |
| L1-D-003 | handover/CLOUD-EGM-SETUP-2026-11-12.md | setup text for one named cloud session | `handover/CLOUD-EGM-SETUP-2026-11-12.md:1 "# EGM setup for session_014pRo39s7uVZzyUdigisB8j"` | N/A: no job key |
| L1-D-004 | handover/EGM-CHILD-HOWTO.md | how to run one EGM step as a child claude -p process | `handover/EGM-CHILD-HOWTO.md:13 "NOT yet tested: a full review run"` | N/A: no job key |
| L1-D-005 | handover/RULE-R456-WORK-CONDUCT.md | owner rule: never idle, parallel by default, n8n first, no side projects | `handover/RULE-R456-WORK-CONDUCT.md:13 "NEVER IDLE"` | N/A: no job key |
| L1-D-006 | handover/demo/ORDERS.md | the lead orders log (88 KB) | `handover/demo/ORDERS.md:354 "STOP GOLD-PLATING"` | LOG |
| L1-D-007 | handover/demo/REPORT.md | the demo session report (660 KB, 153 blocks, newest on top) | `handover/demo/REPORT.md:4 "10:20Z OWNER ORDER APPLIED"` | LOG |
| L1-D-008 | handover/demo/APPLY-LIST.md | apply order of the patches | `handover/demo/APPLY-LIST.md:32 "BATCH 1: APPLIED by the lead on pr-3-tests"` | LOG |
| L1-D-009 | handover/demo/drift/DRIFT-REPORT-1.md and REVIEW-1.md | docs against code: 3 doc-wrong, 0 code-wrong | `handover/demo/drift/DRIFT-REPORT-1.md:56 "FULL RUN: NOT COMPLETED"` | N/A: no job key |
| L1-D-010 | handover/demo/merge-ready/MERGE-READINESS-2-4.md plus REVIEW-1 and REVIEW-3 | checklist for merging pull requests 2 to 4 | `handover/demo/merge-ready/MERGE-READINESS-2-4.md:3 "Head commits measured: #2 d23cf8f, #3 f31e261, #4 f5fe824"` | N/A: no job key |
| L1-D-011 | handover/demo/pr-stack/AB-PAPER.md and CARRY-OVER-CHECKLIST.md | decision paper A or B and the list of bot comments | `handover/demo/pr-stack/CARRY-OVER-CHECKLIST.md:1 "Carry-over checklist: inline bot review comments"` | N/A: no job key |
| L1-D-012 | handover/demo/pr-text (proposed descriptions v1 to v5 for #2, #3, #4, pr4-A, VERIFY, REVIEW-MAP, Semgrep bodies v1 to v6, claims, github-current copies) | text for pull requests | `handover/demo/pr-text/proposed/VERIFY.md:5 "Corrections to the brief and to REVIEW-pr2-4.md"` | N/A: no job key |
| L1-D-013 | handover/demo/reuse (CORE-TO-DEMO plus 3 resolves, 4 reviews) | where the demo re-implements the core | `handover/demo/reuse/CORE-TO-DEMO.md:6 "NOT RUN: no test of either side was run"` | N/A: no job key |
| L1-D-014 | handover/demo/speed (RUNBOOK-INPUTS, RUNBOOK-SPEED-3, evidence-phase4) | machine facts and the rule for proving test speed | `handover/demo/speed/RUNBOOK-SPEED-3.md:7 "Nothing in this runbook has been run on the cloud container"` | N/A: no job key |
| L1-D-015 | handover/system-map/DECISION-one-store.md (outside lane, baseline) | one database for the take | `handover/system-map/DECISION-one-store.md:14 "ONE database for everything we own"` | STORE |
| L1-T-001 | tests/test_hygiene.py (public demo repo) | secret scan, pinned workflows, literal scan | `handover/demo/merge-ready/MERGE-READINESS-2-4.md:31 "15 passed, 17 s"` | FILTER |
| L1-T-002 | tests/test_gitleaks_exceptions.py (patch, 44 tests) | pins that the one allowed key line stays narrow | `handover/demo/merge-ready/REVIEW-3.md:2 "no Blocker, no Major found by reading"` | FILTER |
| L1-T-003 | tests/test_workflow_files_parse.py | every workflow file parses; trimmed version has 19 mutants killed | `handover/demo/merge-ready/SONAR-YAML-TRIMMED-V2-NOTES.md:1 "reviewer's trimmed test, 84 lines after ruff format"` | OTHER |
| L1-T-004 | tests/test_except_clause_hierarchy.py (49 cases) | pins the cleaned retry-path except lists; reads demo_only files directly | `handover/demo/ORDERS.md:230 "With demo_only/ DELETED, 6 tests fail"` | RETRY |
| L1-T-005 | tests/test_hung_adapter_calls.py | tests of the reaper with hung adapters (never reproduced a hang) | `handover/demo/REPORT.md:2838 "THERE IS NO EVIDENCE for it"` | RETRY |
| L1-T-006 | tools/tests/test_core_sync_check_r2.py (studio side) | studio tools test that fails and was not root-caused | NOT VISIBLE: tools/tests/test_core_sync_check_r2.py; `handover/demo/speed/evidence-phase4.md:4 "NOT root-caused"` | OTHER |
| L1-F-001 | handover/demo/drift, followup, merge-ready, pr-stack, pr-text, reuse, speed | seven work folders of the demo session (patches, reviews, evidence) | `handover/demo/APPLY-LIST.md:3 "All patch paths are relative to handover/demo/"` | N/A: no job key |
| L1-F-002 | handover/tools | two scripts for EGM model routing | `handover/MODEL-ROUTING.md:25 "python3 handover/tools/egm_model_patch.py"` | N/A: no job key |
| L1-F-003 | other handover/demo folders named in ORDERS (triage, gitleaks, coverage, fixes, hang, integration, layout, outsider, real-run, semgrep, sonar, stranger, skips) | belong to lane L4 | N/A: other lane (L4) | N/A: no job key |

## Findings
| id | claim type | severity | evidence | conflicts with | job key |
|---|---|---|---|---|---|
| L1-FD-001 | inconsistent | Major | A second money counter exists as a JSON-lines file with a lock file; DECISION allows one database plus one named file exception and does not mention it; CORE-TO-DEMO says take-mode code was not read, so whether the take uses it is UNVERIFIED. `handover/demo/reuse/CORE-TO-DEMO.md:92 "is one JSON-lines file with an OS lock file"`; `handover/demo/reuse/CORE-TO-DEMO.md:97 "keep the demo ledger"` | `DECISION line 17` | COUNTER |
| L1-FD-002 | duplicate | Major | The demo re-implements five generic jobs that core already holds (text fold, mutation runner, scan guard, client-profile check, spend meter) and the report recommends keeping the local copies; the studio rule says demos consume core and promote generic code. `handover/demo/reuse/CORE-TO-DEMO.md:23 "text fold vs email/name keys"`; `handover/demo/reuse/CORE-TO-DEMO.md:24 "mutation runner vs mutant tests"`; `handover/demo/reuse/CORE-TO-DEMO.md:27 "client-profile check vs mode/real-service refusal"` | none | COUNTER |
| L1-FD-003 | dead | Major | About 600 KB of superseded patch and text versions sit next to the current ones (followup-ab v2 DO-NOT-USE 84 KB, v3 and v1; hygiene v1 v2 v3; five sonar-yaml test variants; five PR texts per pull request; Semgrep bodies v1 to v6 and two claims files; github-current copies of closed pull requests). Readers can pick the wrong one. `handover/demo/followup/followup-ab-v2-DO-NOT-USE-has-type-ignore.patch:1567 "type: ignore"`; `handover/demo/pr-text/github-current/pr4-body.md:5 "each pull request has 100 files or fewer"` | none | OTHER |
| L1-FD-004 | dead | Major | Pull request 4 was retargeted and merged and 2 and 3 were closed, yet MERGE-READINESS, AB-PAPER, CARRY-OVER-CHECKLIST and the pr-text proposals still describe the open stack with old heads. `handover/demo/merge-ready/MERGE-READINESS-2-4.md:3 "Head commits measured: #2 d23cf8f, #3 f31e261, #4 f5fe824"`; `handover/demo/ORDERS.md:348 "PR #4 MERGED as 61ded9eb on main"` | none | OTHER |
| L1-FD-005 | inconsistent | Major | APPLY-LIST header says last update 2026-11-12 20:38Z but the file holds status blocks up to 02:08Z the next day; the table numbers two different patches as item 6; Batch 2 rows still say patches are not produced that later were applied. `handover/demo/APPLY-LIST.md:1 "Last update 2026-11-12 20:38Z"`; `handover/demo/APPLY-LIST.md:13 "stranger/limits-burst-doc.patch"`; `handover/demo/APPLY-LIST.md:18 "fixes/docs-and-deps.patch"` | none | LOG |
| L1-FD-006 | duplicate | Major | One job (what patch is in what state) is logged in three places: lead notes in ORDERS, status blocks in APPLY-LIST, READY lines in REPORT. `handover/demo/ORDERS.md:84 "BATCH 1 APPLIED"`; `handover/demo/APPLY-LIST.md:32 "BATCH 1: APPLIED by the lead on pr-3-tests"`; `handover/demo/REPORT.md:5 "READY (unchanged, all from CLEAN fresh reads"` | none | LOG |
| L1-FD-007 | inconsistent | Major | ORDERS blocks are out of time order and several are mislabelled by the lead, so the newest order cannot be found by position: D2 (19:15Z) after D1 (19:45Z), D8 (20:10Z) after D7 (20:25Z); a 03:45Z block admitted to be a 03:33Z block; three blocks pushed empty. `handover/demo/ORDERS.md:5 "## ORDER D1 (lead, 2026-11-12 ~19:45Z"`; `handover/demo/ORDERS.md:14 "## ORDER D2 (lead, 2026-11-12 ~19:15Z"`; `handover/demo/ORDERS.md:246 "mislabelled by the lead"`; `handover/demo/ORDERS.md:160 "pushed EMPTY"` | none | LOG |
| L1-FD-008 | inconsistent | Nit | Report cadence differs by file: REPORT says every 10 minutes, ORDERS says every 5 minutes; agent targets differ by order (2, 5). `handover/demo/REPORT.md:2 "Write a status block at least every 10 minutes"`; `handover/demo/ORDERS.md:150 "EVERY 5 MINUTES by the clock"`; `handover/demo/ORDERS.md:14 "Keep AT LEAST 2 agents running at all times"`; `handover/demo/ORDERS.md:185 "Keep >= 5 agents running"` | none | NOTICE |
| L1-FD-009 | ops | Major | The report file is one 660 KB store with 153 blocks and lines up to 4831 characters, each block with three tables, written every 5 minutes; reading it costs far more than the status it gives, and the lead had to ask twice for newest-on-top. `handover/demo/REPORT.md:13 "heartbeat loop"`; `handover/demo/ORDERS.md:97 "put the newest block at the very top"` | none | LOG |
| L1-FD-010 | inconsistent | Major | Test counts disagree and are not reconciled: 2465 collected against 2464 claimed; 2349 passed and 116 skipped measured against 2329 and 135 expected (cause not explained); run script says about 119 skips; later heads give 3138 and 3, 3096 and 45, 3094 and 3, 2988 and 6. `handover/demo/drift/DRIFT-REPORT-1.md:34 "collects 2465 tests, one more than the claimed 2464"`; `handover/demo/ORDERS.md:41 "2329/135"`; `handover/demo/speed/run-demo-linux.sh:3 "~119 browser tests skip"`; `handover/demo/ORDERS.md:164 "3096 passed, 45 skipped, 0 failed"` | none | COUNTER |
| L1-FD-011 | unverified | Major | The cause of the one stalled and one early-ended run is unknown: no memory evidence, no reproduction in 51 runs; two unbounded waits remain in the reaper and the report leaves the change to the lead (a deferral). `handover/demo/REPORT.md:2836 "oom_kill 0, failcnt 0"`; `handover/demo/REPORT.md:2838 "THERE IS NO EVIDENCE for it"`; `handover/demo/APPLY-LIST.md:25 "Two unbounded loops in the reaper"` | none | RETRY |
| L1-FD-012 | unverified | Major | The cloud container restarted at least 7 times; the order to find the cause was given, the measured memory numbers do not support out-of-memory, and no cause is written; the cloud was then barred from full suites. `handover/demo/REPORT.md:1839 "container restarts every 5-30 min (7 so far)"`; `handover/demo/ORDERS.md:175 "Full suites of FINAL heads go to the LAPTOP"` | none | OTHER |
| L1-FD-013 | unverified | Major | Reviews are labelled fresh egm reviewers but are second-hand: reviewers are read-only and the lead saved condensed text; the child-process route is documented as not yet tested; the drift report states no reviewer agents were dispatched. `handover/demo/merge-ready/REVIEW-1.md:1 "Saved by the session lead (condensed)"`; `handover/EGM-CHILD-HOWTO.md:13 "NOT yet tested: a full review run"`; `handover/demo/drift/DRIFT-REPORT-1.md:4 "No reviewer agents were dispatched"` | none | OTHER |
| L1-FD-014 | unverified | Major | A failing studio test was found while measuring speed and left unexplained, and the load sample before each run is empty so the stated 15 percent rule was not checked for those 6 runs. `handover/demo/speed/evidence-phase4.md:4 "NOT root-caused"`; `handover/demo/speed/evidence-phase4.md:5 "load sample before each run is EMPTY"` | none | OTHER |
| L1-FD-015 | unverified | Major | The speed runbook was never run in the cloud, is marked not reviewed, and one of its two example ledger rows shows the sdk parallel run missed the first 400 s rule; the demo xdist patch it ships is for head b29bb1f while the lead later built v3 on db54e13 in the studio folder. `handover/demo/speed/RUNBOOK-SPEED-3.md:7 "Nothing in this runbook has been run on the cloud container"`; `handover/demo/speed/RUNBOOK-SPEED-3.md:9 "The sdk parallel run MISSED the old 400 s rule"`; `handover/demo/ORDERS.md:252 "ci-xdist-demo-db54e13-v3.patch"` | none | COUNTER |
| L1-FD-016 | inconsistent | Nit | Heavy-run slot limits differ: 3 at once, 4 slots, 2 processes. `handover/CLOUD-EGM-SETUP-2026-11-12.md:10 "at most 3 heavy test runs at once"`; `handover/demo/speed/RUNBOOK-SPEED-3.md:45 "max 4 slots, use 2 per run"`; `handover/demo/ORDERS.md:177 "Never run more than 2 heavy processes"` | none | COUNTER |
| L1-FD-017 | duplicate | Major | egm_setup.sh embeds a full copy of egm_model_patch.py, so the model table lives in two files that must be edited together. `handover/tools/egm_model_patch.py:25 "def find_roots"`; `handover/tools/egm_setup.sh:33 "def find_roots"` | none | OTHER |
| L1-FD-018 | inconsistent | Nit | Expected model counts disagree: 6 opus and 64 sonnet in the setup script, 3 opus per copy and 89 files in 3 folders in the routing file. `handover/tools/egm_setup.sh:85 "expect opus 6, sonnet 64"`; `handover/MODEL-ROUTING.md:31 "(3 per plugin copy)"`; `handover/MODEL-ROUTING.md:46 "it rewrote 89 files in 3 plugin folders"` | none | OTHER |
| L1-FD-019 | dead | Nit | MODEL-ROUTING keeps two superseded Fable overrides above the revert, so a reader can follow the wrong table. `handover/MODEL-ROUTING.md:42 "OVERRIDE 2 2026-11-11"`; `handover/MODEL-ROUTING.md:45 "REVERT 2026-11-11"` | none | OTHER |
| L1-FD-020 | dead | Major | CLOUD-EGM-SETUP is addressed to a session that ORDERS lists as retired, and names the owner in full; setup now lives in egm_setup.sh. `handover/CLOUD-EGM-SETUP-2026-11-12.md:1 "# EGM setup for session_014pRo39s7uVZzyUdigisB8j"`; `handover/demo/ORDERS.md:2 "Retired sessions, ignore anything from them"` | none | OTHER |
| L1-FD-021 | security | Major | Personal data: the owner's full name appears in two files and a Windows login name appears 79 times in file paths across 9 files of this lane (type: personal name and local user name, values not copied). Not an e-mail address. By the severity table this would be a Blocker if the owner counts it as personal data; lead decides. `handover/CLOUD-EGM-SETUP-2026-11-12.md:3 "You are a cloud Claude Code session"`; `handover/demo/speed/RUNBOOK-SPEED-3.md:48 "set PYTHONDONTWRITEBYTECODE=1"` | none | OTHER |
| L1-FD-022 | security | Major | A reviewer answered y to a start prompt and the desk made real network attempts; the fix is a handover-only patch, so the breach class is still open in public code and the ledger row stays OPEN; proxy evidence was not available. `handover/demo/ORDERS.md:267 "a reviewer answered y"`; `handover/demo/ORDERS.md:277 "ledger stays OPEN"`; `handover/demo/ORDERS.md:335 "real-run patches (v6 etc.) are NOT pushed to the public branch now"` | none | NOTICE |
| L1-FD-023 | unverified | Major | Public pull request texts carried false claims (final tree identical to #1; every part has 100 files or fewer) until corrected in proposals; whether the corrected text was pasted is UNVERIFIED. `handover/demo/pr-text/REVIEW-pr2-4.md:3 "is FALSE now"`; `handover/demo/pr-text/github-current/pr4-body.md:5 "each pull request has 100 files or fewer"` | none | NOTICE |
| L1-FD-024 | inconsistent | Nit | Rule 8 of the preamble (uv run with group test) does not work in the demo repo, yet the same preamble heads demo briefs. `handover/demo/merge-ready/REVIEW-sonar-crlf-fresh.md:5 "PREAMBLE rule 8 command does not work in this repo"` | none | OTHER |
| L1-FD-025 | idle | Major | CI hides tests: Playwright and gitleaks tests skip in lint and sonar, so 45 to 116 tests never run on GitHub; the lead asked whether CI should install them and no answer is recorded. `handover/demo/ORDERS.md:165 "Branch protection on the DEMO main: NONE"`; `handover/demo/ORDERS.md:164 "3096 passed, 45 skipped, 0 failed"` | none | COUNTER |
| L1-FD-026 | inconsistent | Nit | quiet-check.sh drops any process line containing the shell number, so a competing test could be hidden from the quiet check. `handover/demo/speed/quiet-check.sh:6 "grep -v grep"` | none | COUNTER |
| L1-FD-027 | ops | Nit | checklist.py hardcodes a /tmp path, a clone path and one full commit id. `handover/demo/pr-stack/checklist.py:6 "FINAL = "` | none | OTHER |
| L1-FD-028 | duplicate | Major | Desk SQLite and portal are retired from the take, yet about 40 patches and four review lanes polish desk and portal code, and a sent-mail panel was planned on them. `handover/system-map/DECISION-one-store.md:15 "The desk SQLite and its portal are retired from the take"`; `handover/demo/ORDERS.md:218 "Sonar quick wins"` | `DECISION line 15` | STORE |
| L1-FD-029 | ops | Nit | A core commit of 3038 files was pushed to the demo branch by mistake and reverted; history keeps both commits. `handover/demo/ORDERS.md:120 "I pushed a core handover commit (483eba53, 3038 files)"` | none | OTHER |
| L1-FD-030 | unverified | Nit | The Windows full-run figure comes from a log on the lead laptop that is not in this box. `handover/demo/ORDERS.md:164 "3096 passed, 45 skipped, 0 failed"`; NOT VISIBLE: win-2db3926.txt | none | COUNTER |
| L1-FD-031 | dead | Nit | One tool, cloud-register.md, is named as the register but is not in this box; supervision of children cannot be checked. `handover/EGM-CHILD-HOWTO.md:11 "Register each child in cloud-register.md"` | none | LOG |
| L1-FD-032 | unverified | Major | The take cannot be mapped: the take repo is not visible; DECISION lists three stores and says the second one, mf_leads in Postgres, is not yet proven (schema, roles and history not in the re-smoke). `handover/system-map/DECISION-one-store.md:14 "NOT in the re-smoke"` | none | STORE |
| L1-FD-033 | security | Major | The demo carries 117 scanner switch-off markers (106 noqa lines, 11 nosec lines) in 46 tracked files, listed nowhere and not pinned to a reviewed list; the studio rule is no suppressions. Also the demo has no acknowledgement that real crm, mail or ai kinds only get made-up data. `handover/demo/reuse/CORE-TO-DEMO.md:64 "117 marker hits in 46 tracked files"`; `handover/demo/reuse/CORE-TO-DEMO.md:71 "listed nowhere"`; `handover/demo/reuse/CORE-TO-DEMO.md:118 "real crm, mail or ai kinds start with no"`; `CLAUDE.md:41 "no suppressions, no weakened tests"` | none | FILTER |
| L1-FD-034 | inconsistent | Nit | The demo has no stage concept, while the preamble says stages are demo, pilot and prod only and core refuses anything else. `handover/demo/reuse/CORE-TO-DEMO.md:84 "no stage concept at all"`; `handover/BRIEF-PREAMBLE.md:23 "the stages are DEMO, PILOT and PROD"` | none | OTHER |
| L1-FD-035 | unverified | Nit | In the evidence for branch heads the line EXIT=0 sits right under a gitleaks run that reports a leak, so the exit code was probably taken from the end of a pipe, not from gitleaks; the studio rule says never gate on a pipe. `handover/demo/merge-ready/evidence-m-3-branch-heads.txt:4 "leaks found: 1"`; `handover/demo/merge-ready/evidence-m-3-branch-heads.txt:5 "EXIT=0"` | none | LOG |
| L1-FD-036 | inconsistent | Nit | The apply order of the sonar yaml test patches depends on the base head: the trimmed test does not apply with P1 v3 and fails on 2db3926 because the test file is missing; five variants of the same test are kept. `handover/demo/merge-ready/SONAR-YAML-TRIMMED-V2-NOTES.md:4 "It does NOT apply together with P1 v3"`; `handover/demo/merge-ready/evidence-b7-4-apply-matrix.txt:11 "S:FAIL"` | none | OTHER |
| L1-FD-037 | idle | Nit | The lint run on pull request 2 failed within 10 seconds on GitHub (the secret scan), which the local checks only reported as local; the stack was never green as separate pull requests. `handover/demo/pr-stack/evidence-ab-ci-durations.txt:6 "lint pull_request pr-1-code@d23cf8f failure 10s"` | none | LOG |
| L1-FD-038 | unverified | Major | The test figures quoted in the public PR texts (3138 passed and 3 skipped in 10 parts and in one process; post-step results) are checked against raw files under /tmp/work on a cloud box that is gone after the session, and the Windows figure against a laptop log; none of them is committed, so nobody can re-check the numbers from the repository. `handover/demo/pr-text/proposed/VERIFY.md:68 "2db3926 in 10 separate parts"`; `handover/demo/pr-text/proposed/VERIFY.md:133 "single-process Linux run of 2db3926"`; `handover/demo/pr-text/proposed/VERIFY.md:128 "Windows figure 3096 passed"` | none | COUNTER |

## Checkpoint
Written after reading 45 files (READ) plus 17 skimmed and 86 NOT-READ (some partly read, see notes). NOT FINISHED, lane marked PARTIAL.
Done: handover top-level docs and tools, ORDERS.md, APPLY-LIST.md, drift, small merge-ready docs and evidence, speed scripts and inputs, pr-text reviews and github-current copies, CORE-TO-DEMO (almost whole), REPORT.md top block plus key grep, secret and e-mail scan over all 148 files (no secret value found; made-up test addresses only; one owner full name and a Windows login name in paths, values not copied).
Next: the NOT-READ list: remaining reuse reviews and resolves, followup reviews and patches, merge-ready patches, pr-stack CARRY-OVER-CHECKLIST and raw JSON under 200 KB, pr-text proposed versions and Semgrep bodies, semgrep-pr-diff-lead.patch, REPORT.md in full by slices.
Blockers: none beyond size. UNVERIFIED everywhere a runtime is needed; the take repo is NOT VISIBLE.
