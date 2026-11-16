# evidence-5 (EVIDENCE RUNNER; raw output only, no judging)

Run date: 2026-11-16 07:54 UTC. Targets read-only: /tmp/sm/handover/system-map/{SWEEP,ONE-PLACE-TABLE,MASTER-MAP}.md, tree /tmp/smfull/.
Scripts: /tmp/ev5/cit.py (tasks 1-2), /tmp/ev5/t3.py (task 3), task 4 inline python (output /tmp/ev5/t4.txt). Run as: python3 -I <script>.
Method notes: citation regex = backticked `path:line "quote"`; quoted text is matched as a plain substring of the line (exact) or of lines n-3..n+3. SWEEP finding rows = table rows whose first cell matches L<n>[a-z]?[c]-<KIND>-<n> between lines 39 and 355 (314 rows, equal to the REPORT.md raw count of 314). Severity cell = third cell. ONE-PLACE-TABLE has no severity column; rows were selected where the word Blocker appears anywhere in the row. MASTER-MAP.md was not an input of any task and was not read.

## Tasks 1 and 2: citation check
```
SWEEP finding rows 314 Blocker rows 20 Major rows 209
Major sampled (every 3rd, 3rd,6th,..): ['L1-FD-003', 'L1-FD-006', 'L1-FD-010', 'L1-FD-013', 'L1-FD-017', 'L1-FD-023', 'L1-FD-032', 'L1c-FD-002', 'L1c-FD-005', 'L1c-FD-008', 'L1c-FD-011', 'L1c-FD-015', 'L1c-FD-018', 'L1c-FD-024', 'L2-FD-004', 'L2-FD-009', 'L2-FD-012', 'L2-FD-015', 'L2-FD-019', 'L2c-FD-001', 'L2c-FD-004', 'L2c-FD-007', 'L2c-FD-010', 'L3-FD-001', 'L3-FD-007', 'L3-FD-010', 'L3-FD-013', 'L3-FD-016', 'L3-FD-023', 'L3-FD-032', 'L3-FD-038', 'L3c-FD-001', 'L3c-FD-005', 'L3c-FD-008', 'L3c-FD-011', 'L3c-FD-015', 'L3c-FD-018', 'L3c-FD-021', 'L3c-FD-024', 'L3c-FD-029', 'L3c-FD-032', 'L4-FD-001', 'L4-FD-004', 'L4-FD-008', 'L4-FD-011', 'L4-FD-014', 'L4-FD-017', 'L4c-FD-004', 'L4c-FD-007', 'L4c-FD-010', 'L4c-FD-013', 'L4c-FD-016', 'L4c-FD-019', 'L5a-FD-001', 'L5a-FD-004', 'L5a-FD-007', 'L5a-FD-010', 'L5a-FD-013', 'L5ac-FD-002', 'L5ac-FD-006', 'L5ac-FD-010', 'L5b-FD-001', 'L5b-FD-004', 'L6-FD-007', 'L6-FD-010', 'L6-FD-013', 'L6-FD-016', 'L6-FD-020', 'L6-FD-025'] 69

### SWEEP Blocker
finding id | citation | result
L1-FD-021 | handover/CLOUD-EGM-SETUP-2026-11-12.md:3 "You are a cloud Claude Code session" | line-exact
L1-FD-021 | handover/demo/speed/RUNBOOK-SPEED-3.md:48 "set PYTHONDONTWRITEBYTECODE=1" | line-exact
L1c-FD-001 | handover/demo/pr-stack/evidence-ab-workflows.txt:160 "the SONAR_TOKEN secret is NOT in the environment of the install and te" | line-exact
L1c-FD-001 | handover/demo/pr-stack/evidence-ab-workflows.txt:165 "is an open owner decision" | line-exact
L1c-FD-001 | handover/demo/pr-text/proposed/pr4-user-description-v5.md:41 "Splitting them into two jobs is still an open owner decision." | line-exact
L1c-FD-021 | handover/demo/pr-text/github-current/pr3-body.md:5 "(checked: the final tree is identical)" | line-exact
L1c-FD-021 | handover/demo/pr-text/github-current/pr2-body.md:5 "(checked: the final tree is identical)" | line-exact
L1c-FD-021 | handover/demo/pr-text/proposed/VERIFY.md:25 "95 files changed, 5513 insertions(+), 271 deletions(-)" | line-exact
L1c-FD-021 | handover/demo/pr-text/REVIEW-pr2-4.md:3 "is FALSE now" | line-exact
L2-FD-001 | handover/demo3/kill/harness.py:34 "N8N_USER_FOLDER=home" | line-exact
L2-FD-001 | handover/demo3/kill/RESULTS.md:40 "n8n_folder:email=n8nhome/.n8n/database.sqlite-wal" | line-exact
L2-FD-001 | handover/demo3/REPORT.md:55 "GREP on Postgres-backed n8n" | line-exact
L2-FD-002 | handover/demo3/kill/harness.py:315 "api_key" | line-exact
L2-FD-002 | handover/demo3/kill/RESULTS.md:44 "n8n_folder:key=n8nhome/.n8n/database.sqlite-wal" | line-exact
L2-FD-003 | handover/demo3/kill/flows-go1/mf-form.json:424 "saveDataSuccessExecution" | line-exact
L2-FD-003 | handover/demo3/kill/run_h.sh:9 "EXECUTIONS_DATA_SAVE_ON_SUCCESS=none" | line-exact
L2-FD-003 | handover/demo3/questions-for-lead.md:11 "executions are not saved" | line-exact
L2-FD-007 | handover/demo3/kill/flows-go1/mf-form.json:97 "ELSE 'review' END" | line-exact
L2-FD-007 | handover/demo3/kill/flows-go1/mf-recovery.json:124 "'unknown','failed')" | line-exact
L2-FD-008 | handover/demo3/kill/RESULTS.md:13 "lead_alerts=0" | line-exact
L2-FD-008 | handover/demo3/questions-for-lead.md:13 "one open design question" | line-exact
L2-FD-008 | handover/demo3/kill/COMPARE-demo.md:12 "Not compared" | line-exact
L2-FD-008 | handover/demo3/ORDERS.md:197 "no second alert channel now" | line-exact
L2-FD-018 | handover/demo3/REPORT.md:3 "encryption key n8n generated" | line-exact
L2-FD-018 | handover/demo3/REPORT.md:5 "NOT FIXED, needs the lead/owner" | line-exact
L4c-FD-001 | handover/demo/real-run/REVIEW-v4-fresh.md:5 "towards the vendor's default address with a made-up key" | line-exact
L4c-FD-001 | handover/demo/real-run/NOTES-desk-address-required.md:8 "a default address that is the vendor's own" | line-exact
L4c-FD-002 | handover/demo/triage/SUMMARY-codeant2-sec.md:24 "on the old code the second server receives the key" | line-exact
L4c-FD-002 | handover/demo/triage/SUMMARY-codeant5-sec.md:4 "r4 code printed a traceback ending" | line-exact
L4c-FD-003 | handover/demo/real-run/NOTES-start-prompt.md:32 "its explicit numeric flag is the deliberate consent" | line-exact
L4c-FD-003 | handover/demo/real-run/REVIEW-real-run-v6-fresh.md:75 "confirms a real spend by a flag" | line-exact
L6-FD-001 | handover/demo3/kill/harness.py:34 "N8N_USER_FOLDER=home" | line-exact
L6-FD-001 | handover/demo3/kill/RESULTS.md:40 "n8n_folder:email=n8nhome/.n8n/database.sqlite-wal" | line-exact
L6-FD-001 | handover/demo3/kill/harness.py:315 "api_key" | line-exact
L6-FD-001 | handover/system-map/DECISION-one-store.md:14 "ONE database for everything we own" | line-exact
L6-FD-002 | handover/demo3/kill/flows-go1/mf-form.json:424 "saveDataSuccessExecution" | line-exact
L6-FD-002 | handover/demo3/kill/run_h.sh:9 "EXECUTIONS_DATA_SAVE_ON_SUCCESS=none" | line-exact
L6-FD-002 | handover/demo3/questions-for-lead.md:11 "executions are not saved" | line-exact
L6-FD-002 | handover/system-map/DECISION-one-store.md:16 "Logs: one place = Postgres" | line-exact
L6-FD-003 | handover/demo/reuse/CORE-TO-DEMO.md:92 "is one JSON-lines file with an OS lock file" | line-exact
L6-FD-003 | demos/ask-your-data/askdata/meter.py:211 "def reserve(self, worst_case: Decimal" | line-exact
L6-FD-003 | src/hadavin_sdk/limits.py:17 "def charge(self, agent_id: str, usd: Decimal)" | line-exact
L6-FD-003 | src/hadavin_sdk/k1b/loop.py:41 "A total USD cap for the whole invocation" | line-exact
L6-FD-003 | handover/system-map/DECISION-one-store.md:17 "stays a small file for the take" | line-exact
L6-FD-004 | handover/demo3/kill/fakes.py:137 "requests, model_calls, journal, lock" | line-exact
L6-FD-004 | handover/demo3/kill/RESULTS.md:8 "model_calls=1" | line-exact
L6-FD-004 | handover/system-map/DECISION-one-store.md:9 "file in the take folder (qualify_stage.py)" | line-exact
L6-FD-005 | handover/demo3/kill/RESULTS.md:13 "lead_alerts=0" | line-exact
L6-FD-005 | handover/demo3/kill/flows-go1/mf-recovery.json:196 "mf-mail-smtp" | line-exact
L6-FD-005 | handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:227 "mf-mail-smtp" | line-exact
L6-FD-005 | handover/demo3/ORDERS.md:197 "no second alert channel now" | line-exact
L6-FD-006 | handover/demo3/kill/flows-go1/mf-form.json:112 "n8n-publish-pg" | line-exact
L6-FD-006 | handover/system-map/DECISION-one-store.md:14 "three least-privilege roles" | line-exact
L6-FD-017 | handover/demo3/kill/flows-go1/mf-form.json:97 "ELSE 'review' END" | line-exact
L6-FD-017 | handover/demo3/kill/flows-go1/mf-recovery.json:124 "'unknown','failed')" | line-exact
L6-FD-026 | handover/demo3/kill/flows-go1/mf-recovery.json:43 "continueRegularOutput" | line-exact
TOTALS {'line-exact': 56}

ONE-PLACE rows 59 rows containing "Blocker": ['L6-J-051', 'L6-J-059']
### ONE-PLACE Blocker
finding id | citation | result
L6-J-051 | handover/demo3/kill/flows-go1/mf-recovery.json:196 "mf-mail-smtp" | line-exact
L6-J-051 | handover/demo3/kill/RESULTS.md:13 "lead_alerts=0" | line-exact
L6-J-059 | handover/demo3/evidence/resolve-round2-lane3-fix-1.md:1 "round 2 of cap 2" | line-exact
L6-J-059 | handover/demo3/evidence/review-lane3-fix-5-r8-codedetails.md:2 "Result: 1 Blocker / 2 Major" | line-exact
TOTALS {'line-exact': 4}

### SWEEP Major sample
finding id | citation | result
L1-FD-003 | handover/demo/followup/followup-ab-v2-DO-NOT-USE-has-type-ignore.patch:1567 "type: ignore" | line-exact
L1-FD-003 | handover/demo/pr-text/github-current/pr4-body.md:5 "each pull request has 100 files or fewer" | line-exact
L1-FD-006 | handover/demo/ORDERS.md:84 "BATCH 1 APPLIED" | line-exact
L1-FD-006 | handover/demo/APPLY-LIST.md:32 "BATCH 1: APPLIED by the lead on pr-3-tests" | line-exact
L1-FD-006 | handover/demo/REPORT.md:5 "READY (unchanged, all from CLEAN fresh reads" | line-exact
L1-FD-010 | handover/demo/drift/DRIFT-REPORT-1.md:34 "collects 2465 tests, one more than the claimed 2464" | line-exact
L1-FD-010 | handover/demo/ORDERS.md:41 "2329/135" | line-exact
L1-FD-010 | handover/demo/speed/run-demo-linux.sh:3 "~119 browser tests skip" | line-exact
L1-FD-010 | handover/demo/ORDERS.md:164 "3096 passed, 45 skipped, 0 failed" | line-exact
L1-FD-013 | handover/demo/merge-ready/REVIEW-1.md:1 "Saved by the session lead (condensed)" | line-exact
L1-FD-013 | handover/EGM-CHILD-HOWTO.md:13 "NOT yet tested: a full review run" | line-exact
L1-FD-013 | handover/demo/drift/DRIFT-REPORT-1.md:4 "No reviewer agents were dispatched" | line-exact
L1-FD-017 | handover/tools/egm_model_patch.py:25 "def find_roots" | line-exact
L1-FD-017 | handover/tools/egm_setup.sh:33 "def find_roots" | line-exact
L1-FD-023 | handover/demo/pr-text/REVIEW-pr2-4.md:3 "is FALSE now" | line-exact
L1-FD-023 | handover/demo/pr-text/github-current/pr4-body.md:5 "each pull request has 100 files or fewer" | line-exact
L1-FD-032 | handover/system-map/DECISION-one-store.md:14 "NOT in the re-smoke" | line-exact
L1c-FD-002 | handover/demo/pr-text/proposed/pr4-user-description-v5.md:21 "From the workflow files: SonarQube starts for every pull request." | line-exact
L1c-FD-002 | handover/demo/pr-stack/AB-PAPER.md:17 "is false for #4 today" | line-exact
L1c-FD-002 | handover/demo/pr-stack/evidence-ab-checks.txt:157 ".github/workflows/sonar.yml" | line-exact
L1c-FD-005 | handover/demo/followup/followup-ab-v3-review-fresh3.md:1 "CLEAN (no Blocker, no Major)" | line-exact
L1c-FD-005 | handover/demo/followup/followup-ab-review-fresh2.md:1 "NOT CLEAN" | line-exact
L1c-FD-005 | handover/demo/followup/followup-a-review-fresh.md:1 "NOT CLEAN" | line-exact
L1c-FD-005 | handover/demo/followup/followup-ab-v2-DO-NOT-USE-has-type-ignore.patch:1567 "type: ignore[call-overload]" | line-exact
L1c-FD-008 | handover/demo/pr-text/semgrep-pr-body-v6.md:7 "db54e13" | line-exact
L1c-FD-008 | handover/demo/semgrep/main-61ded9e-v9/semgrep-pr-body-v9.md:9 "The diff of this PR is the patch with sha256" | line-exact
L1c-FD-008 | handover/demo/triage/SUMMARY-codeant2-sec.md:8 "does not apply on 0841f36" | line-exact
L1c-FD-008 | handover/demo/semgrep-pr-diff-lead.patch:5 "+++ b/.github/workflows/semgrep.yml" | line-exact
L1c-FD-011 | handover/demo/pr-text/semgrep-pr-body-v6.md:52 "The text of that licence was not downloaded or read" | line-exact
L1c-FD-011 | handover/demo/pr-text/semgrep-pr-body-v6.md:53 "The repository owner has given a yes to using" | line-exact
L1c-FD-015 | handover/demo/speed/evidence-phase4.md:34 "Class sweep not done" | line-exact
L1c-FD-015 | handover/demo/pr-text/REVIEW-MAP-PR4.md:125 "fake_imap.py and fake_smtp_tls.py: drop" | line-exact
L1c-FD-015 | handover/demo/pr-text/proposed/VERIFY.md:129 "body over 1 MiB or bad length: not read" | line-exact
L1c-FD-015 | handover/demo/speed/fake-hubspot-read-body-before-answer.patch:16 "self.rfile.read(n)" | line-exact
L1c-FD-018 | handover/demo/followup/REVIEW-nodemo-v5-fresh.md:3 "VERDICT: NOT CLEAN (0 Blocker, 2 Major, 5 Minor)" | line-exact
L1c-FD-018 | handover/demo/followup/REVIEW-nodemo-v5-fresh.md:9 "turns ANY ModuleNotFoundError named demo_only" | line-exact
L1c-FD-018 | handover/demo/followup/REVIEW-nodemo-v5-fresh.md:16 "280 of 1228 test functions use no demo name" | line-exact
L1c-FD-024 | handover/demo/reuse/CORE-TO-DEMO.md:129 "Not done: no EGM, no tests, no adoption trial" | line-exact
L1c-FD-024 | handover/demo/reuse/REVIEW-4.md:13 "Not recomputable: core_ci-scan-config-guard-fix1 is not exported" | line-exact
L1c-FD-024 | handover/demo/reuse/CORE-TO-DEMO.md:17 "not in either repo" | line-exact
L1c-FD-024 | handover/demo/reuse/RESOLVE-1.md:38 "no PR number in the single commit 61cf2bea" | line-exact
L2-FD-004 | handover/demo3/kill/flows-go1/mf-form.json:7 "mf-form" | line-exact
L2-FD-004 | handover/demo3/kill/flows-go1/mf-hook.json:7 "mf-hook" | line-exact
L2-FD-004 | handover/demo3/kill/flows-go1/mf-form.json:27 "submission_id" | line-exact
L2-FD-004 | handover/demo3/kill/flows-go1/mf-hook.json:27 "message_id" | line-exact
L2-FD-004 | handover/demo3/kill/harness.py:26 "FLOWS = " | line-exact
L2-FD-004 | handover/demo3/kill/flows-go1/mf_leads.sql:5 "lead_key" | line-exact
L2-FD-009 | handover/demo3/kill/make_all.sh:6 "Flow sets" | line-exact
L2-FD-009 | handover/demo3/kill/flows-go1/V4-README.md:1 "BUILT, NOT RUN" | line-exact
L2-FD-009 | handover/demo3/kill/RESULTS.md:72 "v3B780" | line-exact
L2-FD-009 | handover/demo3/kill/flows-go1/mf_leads.sql:1 "NOTE (v3 table" | line-exact
L2-FD-009 | handover/demo3/kill/flows-go1/mf_leads.sql:2 "OLDER NOTE" | line-exact
L2-FD-009 | handover/demo3/REPORT.md:11 "NOT reviewed" | line-exact
L2-FD-012 | handover/demo3/kill/run_b.sh:5 "while pgrep" | line-exact
L2-FD-012 | handover/demo3/kill/run_f.sh:4 "while ! grep" | line-exact
L2-FD-012 | handover/demo3/kill/run_h.sh:5 "while ! grep" | line-exact
L2-FD-012 | handover/demo3/kill/run_k.sh:5 "while ! grep" | line-exact
L2-FD-012 | handover/demo3/kill/run_l.sh:5 "while ! grep" | line-exact
L2-FD-012 | handover/demo3/kill/run_m.sh:5 "while pgrep" | line-exact
L2-FD-012 | handover/demo3/kill/run_n.sh:5 "while pgrep" | line-exact
L2-FD-012 | handover/demo3/kill/run_p.sh:6 "while pgrep" | line-exact
L2-FD-015 | handover/demo3/kill/fakes.py:137 "journal, lock" | line-exact
L2-FD-015 | handover/demo3/kill/RESULTS.md:8 "model_calls=1" | line-exact
L2-FD-019 | handover/demo3/kill/flows-go1/mf-form.json:97 "ON CONFLICT" | line-exact
L2-FD-019 | handover/demo3/kill/fakes.py:103 "hit = next((r for r in rows.values() if r[" | line-exact
L2-FD-019 | handover/demo3/kill/harness.py:161 "one e-mail per lead" | line-exact
L2c-FD-001 | handover/demo3/register.md:205 "AWS_*/ANTHROPIC_BASE_URL set in shell" | line-exact
L2c-FD-001 | handover/demo3/register.md:217 "shell had AWS_*/ANTHROPIC_* vars" | line-exact
L2c-FD-001 | .claude/rules/verify-tests-and-evals.md:1 "Run tests with no cloud configuration in the environment" | line-exact
L2c-FD-004 | handover/demo3/register.md:4 "check progress-C.txt" | line-exact
L2c-FD-004 | handover/demo3/register.md:9 "my shell: tests/test_real_check_dry.py alone on main" | line-exact
L2c-FD-004 | handover/demo3/register.md:357 "egm-design, egm-codebase-details on fix-2 r9" | line-exact
L2c-FD-004 | handover/demo3/register.md:392 "egm-design / egm-codebase-details on fix-2 r12" | line-exact
L2c-FD-004 | handover/demo3/register.md:399 "PAUSED by lead order L3-STOP 10:50Z" | line-exact
L2c-FD-004 | handover/demo3/register.md:222 "0 agents running, 0 monitors" | line-exact
L2c-FD-004 | handover/demo3/REPORT.md:47 "rows for runs e to l are stale" | line-exact
L2c-FD-007 | handover/demo3/register.md:233 "a person must delete it" | line-exact
L2c-FD-007 | handover/demo3/register.md:216 "Throwaway system user b2dtest left in the sandbox" | line-exact
L2c-FD-007 | handover/demo3/register.md:401 "stop Postgres and the script before saying done" | line-exact
L2c-FD-010 | handover/demo3/register.md:400 "n8n 2.46.6 install in /home/user/work/kill-n8n" | line-exact
L3-FD-001 | handover/demo3/evidence/m6-report.md:10 "113 passed, 0 skipped" | line-exact
L3-FD-001 | handover/demo3/evidence/crash-soak-b.md:13 "5 follow-ups in state" | line-exact
L3-FD-001 | handover/system-map/DECISION-one-store.md:15 "The desk SQLite and its portal are retired from the take" | line-exact
L3-FD-007 | handover/demo3/evidence/crosscheck-demo-numbers.md:3 "I ran no test, only" | line-exact
L3-FD-007 | handover/demo3/evidence/crosscheck-demo-numbers.md:10 "One real behaviour change in a test." | line-exact
L3-FD-007 | handover/demo3/evidence/claims-stack-tests.md:2 "Stack: base + claims-stack-on-f3c39cf8.patch" | line-exact
L3-FD-010 | handover/demo3/evidence/cold-reader-n8n-limits.md:3 "no workflow was imported into or run in a real n8n" | line-exact
L3-FD-013 | handover/demo3/evidence/trace-b90-report.md:36 "Suggested fix (not applied)" | line-exact
L3-FD-013 | handover/demo3/evidence/go1/sql-review.out:6 "interval '720 seconds'" | line-exact
L3-FD-013 | handover/demo3/REPORT.md:18 "B90 (hold 90 s, no kill) on fixed flows: 1 alert at 120 s" | line-exact
L3-FD-013 | handover/demo3/evidence/trace-b90-report.md:28 "Not 'exactly once' anywhere" | line-exact
L3-FD-016 | handover/demo3/tools/q3b-soak.py:2 "Q3b crash soak (copy of q3-soak.py, second seed" | line-exact
L3-FD-016 | handover/demo3/tools/q3c-soak.py:2 "Q3c (copy of Q3 soak, BLIND mail mode default" | line-exact
L3-FD-016 | handover/demo3/tools/q2b-fuzz.py:2 "Q2b copy of q2-fuzz.py (campaigns a-c unchanged" | line-exact
L3-FD-023 | handover/demo3/evidence/lane3-fix-10-r6-notes.md:38 "ONE full run on a one-commit scratch repo" | line-exact
L3-FD-023 | handover/demo3/evidence/checkpoint-b17.md:8 "Full run: 2 failed (own test hygiene" | line-exact
L3-FD-032 | handover/demo3/evidence/raw/summary.txt:9 "e rc=1 wall=1146s" | line-exact
L3-FD-032 | handover/demo3/evidence/raw/e.log:178 "assert not <re.Match object; span=(4501, 4504)" | line-exact
L3-FD-038 | handover/demo3/evidence/identity-fuzz.md:3 "Target: public main f3c39cf8" | line-exact
L3c-FD-001 | handover/demo3/evidence/failures.md:4 "The 56 F on main 61ded9e" | line-exact
L3c-FD-001 | handover/demo3/evidence/e10-fix-5-r4-report.md:3 "itself is at 61ded9e (main)" | line-exact
L3c-FD-001 | handover/demo3/evidence/hang-hunt.md:41 "collected 3605" | line-exact
L3c-FD-001 | handover/demo3/evidence/crash-soak.md:3 "Public main f3c39cf89ec989f032ea48a23cfd824b88da9c68" | line-exact
L3c-FD-001 | handover/demo3/evidence/suite-pr14-6b1fe49.md:9 "3683 + 200 = 3883 = collected items" | line-exact
L3c-FD-005 | handover/demo3/evidence/hang-hunt.md:8 "lost after the first 22 KB" | line-exact
L3c-FD-005 | handover/demo3/evidence/hang-hunt.md:8 "test_429_uses_the_backoff_without_retry_after_and_gives_up_busy" | line-exact
L3c-FD-005 | handover/demo3/evidence/reader-e3b.md:14 "test_429_uses_the_backoff_without_retry_after_and_gives_up_busy" | line-exact
L3c-FD-005 | handover/demo3/evidence/suite-pr14.md:4 "the log stops at 7 percent, 290 PASSED lines" | line-exact
L3c-FD-008 | handover/demo3/evidence/resolve-lane3-fix-2-r7.md:11 "No st_uid check (container secret mounts are owned by others" | line-exact
L3c-FD-008 | handover/demo3/evidence/resolve-lane3-fix-2-r8.md:14 "ESCALATE (lead; owner-level security choice)" | line-exact
L3c-FD-008 | handover/demo3/evidence/resolve-lane3-fix-2-r12.md:16 "refuse a key file whose st_uid is not geteuid() on POSIX" | line-exact
L3c-FD-011 | handover/demo3/evidence/paused-b22-2026-11-14.md:14 "R2 (O_NONBLOCK removed from open_regular_file): SURVIVED" | line-exact
L3c-FD-011 | handover/demo3/evidence/paused-b22-2026-11-14.md:39 "NOT DONE (no full runs on the final tree)" | line-exact
L3c-FD-011 | handover/demo3/evidence/paused-b23-2026-11-14.md:5 "Row 6 (the 179 skips itemised) not done." | line-exact
L3c-FD-011 | handover/demo3/evidence/checkpoint-b23.md:27 "Round 7 checkpoint 1 (about 10:45 UTC)" | line-exact
L3c-FD-011 | handover/demo3/evidence/resolve-lane3-fix-10-r6.md:2 "NO new builder rounds, stack builder stopped" | line-exact
L3c-FD-015 | handover/demo3/evidence/resolve-round1-lane3-fix-2.md:13 "is FALSE. It exits 1 with a Python traceback" | line-exact
L3c-FD-015 | handover/demo3/evidence/resolve-lane3-fix-10-r5.md:21 "not backed by logs" | line-exact
L3c-FD-015 | handover/demo3/evidence/resolve-lane3-fix-5-r8.md:33 "48 stress runs read it correctly" | line-exact
L3c-FD-018 | handover/demo3/evidence/cold-reader-n8n-limits.md:63 "2462 passed" | line-exact
L3c-FD-018 | handover/demo3/evidence/cold-reader-tests-realservices.md:8 "2513 passed, 3 skipped on 2ce1f98" | line-exact
L3c-FD-018 | handover/demo3/evidence/review-lane3-needed-check-1.md:22 "full suite counts 2449/2462, no log" | line-exact
L3c-FD-018 | handover/demo3/evidence/skipped-on-purpose.md:3 "3683 passed, 200 skipped, 1188.75 s" | line-exact
L3c-FD-021 | handover/demo3/evidence/reader-xdist-flake.md:37 "The fix (held_port) touches only tests/test_reset_scripts.py" | line-exact
L3c-FD-021 | handover/demo3/evidence/resolve-lane3-fix-5-r6.md:11 "port block overlap on restart" | line-exact
L3c-FD-021 | handover/demo3/evidence/resolve-lane3-fix-5-r7.md:4 "ip_local_port_range and fails on overlap" | line-exact
L3c-FD-021 | handover/demo3/evidence/reader-xdist-flake.md:43 "Which process listened on 43217" | line-exact
L3c-FD-024 | handover/demo3/evidence/reader-pr12-e-marks.md:24 "equals the naive count that includes those two stderr text lines" | line-exact
L3c-FD-024 | handover/demo3/evidence/reader-pr12-e-marks.md:8 "run 2: 2488 / 57 F / 188 s / 2 E" | line-exact
L3c-FD-029 | handover/demo3/evidence/e9-fix-6-r2-report.md:22 "I did not unset them, so the" | line-exact
L3c-FD-032 | handover/demo3/evidence/resolve-round1-lane3-fix-2.md:36 "KEEP-CODE or CUT-TO-DOC for the key and password check at start" | line-exact
L3c-FD-032 | handover/demo3/evidence/resolve-lane3-fix-2-r12.md:15 "one envnum.read_plain_file" | line-exact
L4-FD-001 | handover/demo/hang/RESULTS.md:52 "SQLite busy handling lives in db.py/gate.py" | line-exact
L4-FD-004 | handover/demo/real-run/DRY-RUN-CHECKS.md:4 "224 case results" | line-exact
L4-FD-004 | handover/demo/real-run/DRY-RUN-CHECKS.md:40 "Counts: rrc 124" | line-exact
L4-FD-008 | (no citation of form path:line "quote" found) | n/a
L4-FD-011 | handover/demo/integration/INT-1.md:11 "Heads verified" | line-exact
L4-FD-011 | handover/demo/scans/SCAN-TABLE.md:14 "2db392650e8b" | line-exact
L4-FD-014 | handover/demo/skips/NEVER-RAN.md:8 "Nothing in section 1 has ever run on Windows" | line-exact
L4-FD-014 | handover/demo/integration/INT-2b.md:10 "Not run: PowerShell" | line-exact
L4-FD-017 | handover/demo/real-run/NOTES-start-prompt-v2.md:17 "A program that drives a pseudo-terminal" | line-exact
L4c-FD-004 | handover/demo/gitleaks/REVIEW-2.md:13 "REAL HOLE worth telling the owner" | line-exact
L4c-FD-004 | handover/demo/gitleaks/SUMMARY.md:8 "sonar-project.properties line 4" | line-exact
L4c-FD-007 | handover/demo/real-run/REVIEW-v5-fresh.md:9 "the FIXES.md v5 claim" | line-exact
L4c-FD-010 | handover/demo/triage/SUMMARY-codeant2-runtime.md:7 "CONTRADICTS lane 8 evidence-d6" | line-exact
L4c-FD-010 | handover/demo/gitleaks/REVIEW-2.md:5 "evidence out of date" | line-exact
L4c-FD-013 | handover/demo/sonar/NOTES-p2-v23.md:10 "other busy errors are tried LOCK_RETRIES (3) times" | line-exact
L4c-FD-013 | handover/demo/triage/SUMMARY-codeant3-rt.md:11 "Mirror busy wait escalates on repeated refusals" | line-exact
L4c-FD-016 | handover/demo/coverage/REVIEW-1.md:2 "Real sonar-scanner acceptance of coverage.xml is UNVERIFIED" | line-exact
L4c-FD-016 | handover/demo/semgrep/SUMMARY-14c.md:2 "NOT run: docker lock command, any GitHub run, the full suite" | line-exact
L4c-FD-019 | handover/demo/real-run/REVIEW-v2-fresh.md:65 "without being sure the process was mine" | line-exact
L4c-FD-019 | handover/demo/real-run/REVIEW-v3-fresh.md:20 "Please remove by hand" | line-exact
L4c-FD-019 | handover/demo/real-run/REVIEW-v5-fresh.md:69 "folders on this machine are from earlier runs of other agents" | line-exact
L5a-FD-001 | demos/ask-your-data/README.md:31 "Not in the spike: the language-model pipeline, retries, audit ledger" | line-exact
L5a-FD-001 | demos/ask-your-data/README.md:60 "Dataset, ledger, meter and evaluation harness (phase P3)" | line-exact
L5a-FD-001 | demos/ask-your-data/askdata/pipeline.py:1 "The pipeline: GATES, GENERATE, VALIDATE" | line-exact
L5a-FD-001 | demos/ask-your-data/README.md:68 "The agreement check is not built." | line-exact
L5a-FD-004 | demos/ask-your-data/askdata/meter.py:254 "A flag file: present = the tool is off." | line-exact
L5a-FD-004 | demos/ask-your-data/askdata/meter.py:211 "def reserve(self, worst_case: Decimal" | line-exact
L5a-FD-004 | src/hadavin_sdk/limits.py:17 "def charge(self, agent_id: str, usd: Decimal)" | line-exact
L5a-FD-004 | src/hadavin_sdk/limits.py:22 "if self.store.get_kill_switch().on:" | line-exact
L5a-FD-004 | demos/ask-your-data/askdata/evalset.py:129 "test_runs: int = 0" | line-exact
L5a-FD-004 | .claude/rules/core-modules-one-source-of-truth.md:11 "must be the SAME and consistent" | line-exact
L5a-FD-007 | demos/ask-your-data/data/goldcheck.py:5 "is a later phase" | line-exact
L5a-FD-007 | demos/ask-your-data/askdata/evalset.py:163 "def freeze(eval_dir: Path, names: list[str]" | line-exact
L5a-FD-007 | demos/ask-your-data/askdata/compare.py:127 "def result_hash(rows: list[tuple]" | line-exact
L5a-FD-007 | demos/ask-your-data/data/goldcheck.py:464 "def result_hash(rows: list[tuple]" | line-exact
L5a-FD-010 | README.md:34 "Per-run fairness is not implemented (waiver)" | line-exact
L5a-FD-010 | README.md:33 "agent runtime and approvals recorder are one process today" | line-exact
L5a-FD-010 | SECURITY.md:9 "Stated limits of redaction (reviewed, not bugs)" | line-exact
L5a-FD-010 | .claude/rules/fix-dont-defer-be-honest.md:11 "A problem found is a problem fixed" | line-exact
L5a-FD-010 | .claude/rules/least-privilege-hard-rule.md:16 "One identity per function" | line-exact
L5a-FD-013 | .claude/rules/false-abstain-reporting.md:8 "Set the ceiling in eval-contract before the build" | line-exact
L5a-FD-013 | demos/ask-your-data/askdata/evalrun.py:399 "should_abstain = [r for r in gold if r.kind in (" | line-exact
L5a-FD-013 | .claude/rules/false-abstain-reporting.md:8 "Never write" | line-exact
L5ac-FD-002 | demos/ask-your-data/data/gold.jsonl:60 "fl_cd is explained only in the column comment: N normal, R flagged for" | line-exact
L5ac-FD-002 | demos/ask-your-data/data/dataset_contract.json:164 "flagged for manual review" | line-exact
L5ac-FD-002 | demos/ask-your-data/db/lumen_schema.sql:38 "Fulfilment flag: N normal, R rush, F fraud-review hold" | line-exact
L5ac-FD-002 | demos/ask-your-data/data/goldcheck.py:132 "Sealed items are frozen." | line-exact
L5ac-FD-006 | CHANGELOG.md:378 "handover/reviews/P1m-fix1-junction-probe.txt" | line-exact
L5ac-FD-010 | demos/ask-your-data/data/gold.jsonl:1 "two formulations, one session; see notes" | line-exact
L5ac-FD-010 | demos/ask-your-data/data/goldcheck.py:210 "order_matters, exemplar and second_author_checked must be booleans" | line-exact
L5b-FD-001 | src/hadavin_sdk/extract.py:1 "one retry with the validator's errors, then a dead letter" | line-exact
L5b-FD-001 | tests/test_s4_llm_guard.py:8 "from hadavin_sdk.extract import Valid, extract" | line-exact
L5b-FD-001 | src/hadavin_sdk/store/protocol.py:104 "def add_dead_letter(self, dl: DeadLetter)" | line-exact
L5b-FD-004 | src/hadavin_sdk/audit/chain.py:1 "an append-only hash chain in the store's database" | line-exact
L5b-FD-004 | src/hadavin_sdk/audit/local_dir.py:1 "Local-folder audit sink for slice 1" | line-exact
L5b-FD-004 | src/hadavin_sdk/k1b/audit_sink.py:1 "events go to the configured sink" | line-exact
L6-FD-007 | handover/demo3/kill/flows-go1/mf-form.json:97 "ON CONFLICT" | line-exact
L6-FD-007 | handover/demo3/kill/fakes.py:103 "hit = next((r for r in rows.values()" | line-exact
L6-FD-007 | handover/demo3/kill/flows-go1/mf-hook.json:7 "mf-hook" | line-exact
L6-FD-007 | handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:326 "UnknownNewA" | line-exact
L6-FD-010 | handover/demo/REPORT.md:2838 "TWO UNBOUNDED LOOPS in the reaper" | line-exact
L6-FD-010 | handover/demo/sonar/NOTES-p2-v23.md:10 "other busy errors are tried LOCK_RETRIES (3) times" | line-exact
L6-FD-010 | handover/demo/triage/SUMMARY-codeant3-rt.md:11 "Mirror busy wait escalates on repeated refusals" | line-exact
L6-FD-013 | demos/ask-your-data/askdata/pipeline.py:365 "sha = self.ledger.append(line)" | line-exact
L6-FD-013 | demos/ask-your-data/askdata/cli.py:99 "result: RunResult = source.run(ok.canonical_sql, sql_sha256=ok.sha256)" | line-exact
L6-FD-013 | src/hadavin_sdk/audit/chain.py:1 "an append-only hash chain in the store's database" | line-exact
L6-FD-013 | src/hadavin_sdk/audit/local_dir.py:1 "Local-folder audit sink for slice 1" | line-exact
L6-FD-013 | handover/system-map/DECISION-one-store.md:16 "Audit = the lifecycle rows of" | line-exact
L6-FD-016 | src/hadavin_sdk/extract.py:1 "one retry with the validator's errors, then a dead letter" | line-exact
L6-FD-016 | src/hadavin_sdk/store/protocol.py:104 "def add_dead_letter(self, dl: DeadLetter)" | line-exact
L6-FD-016 | tests/test_s4_llm_guard.py:8 "from hadavin_sdk.extract import Valid, extract" | line-exact
L6-FD-020 | handover/CLOUD-EGM-SETUP-2026-11-12.md:10 "at most 3 heavy test runs at once" | line-exact
L6-FD-020 | handover/demo/speed/RUNBOOK-SPEED-3.md:45 "max 4 slots, use 2 per run" | line-exact
L6-FD-020 | .claude/rules/review-loop-speed-rules.md:18 "Max 4 heavy jobs" | line-exact
L6-FD-020 | .claude/rules/parallel-agents-and-build-now.md:16 "There is no fixed agent cap" | line-exact
L6-FD-025 | handover/demo3/kill/fakes.py:103 "hit = next((r for r in rows.values()" | line-exact
L6-FD-025 | handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:230 "retryOnFail" | line-exact
L6-FD-025 | handover/system-map/DECISION-one-store.md:11 "HubSpot (CRM) and Gmail" | line-exact
TOTALS {'line-exact': 209}

```

## Task 3: referrers of basenames (ARCHIVE proposals)
Method: paths taken from the row's evidence cell plus the evidence cells of lane rows in work/L*.md whose ids appear in the row's reason cell (ranges written as 'X to Y' expanded by hand to L1c-FD-006 and L3c-D-002..004 for L6-J-012 and L6-J-019). Command per basename: grep -rnIF --exclude-dir=.git -- <basename> /tmp/smfull ; hits in the file itself and in handover/system-map/ (the audit's own outputs, count shown) removed. Basenames such as ORDERS.md, REPORT.md, PLAN.md, SUMMARY.md, register.md are shared by many unrelated files, so their hit counts are plain-name matches, not proven references to that exact path.
```
===== L6-J-019 merged ids: ['L3-D-001', 'L3-D-002', 'L3-S-004', 'L3c-D-001'] | lane rows found: ['L3-D-001', 'L3-D-002', 'L3-S-004', 'L3c-D-001'] | missing: []
paths named: 4 basenames: 4
-- REPORT-archive-2026-11-14.md (paths: handover/demo3/evidence/REPORT-archive-2026-11-14.md) referrers (excl. self and handover/system-map/*, which had 15 hits): 2
    /tmp/smfull/handover/demo3/register.md:327:| LAYOUT | 05:57Z | lead layout order applied: REPORT.md newest first (HB102 on top, HB99 below), old blocks in evidence/REPORT-archive-2026-11-14.md, 24 lines | closed |
    /tmp/smfull/handover/demo3/REPORT.md:46:- REPORT.md: this block. evidence/REPORT-archive-2026-11-14.md: all older blocks (HB1 to HB193).
-- note.sh (paths: handover/demo3/scratch/note.sh) referrers (excl. self and handover/system-map/*, which had 19 hits): 0
-- review-lane3-fix-3-r4.md (paths: handover/demo3/evidence/review-lane3-fix-3-r4.md) referrers (excl. self and handover/system-map/*, which had 8 hits): 0
-- summary.md (paths: handover/demo3/evidence/summary.md) referrers (excl. self and handover/system-map/*, which had 13 hits): 67
    /tmp/smfull/handover/demo3/ORDERS.md:15:## LEAD ANSWERS 09:48Z (all your ASK defaults confirmed unless stated): 1 python3.12 yes; 2 browser tests skipped, record the skip count, yes; 3 container clock ok; 4 two runs at once ok. Ad
    /tmp/smfull/handover/demo3/ORDERS.md:21:## 2026-11-13 10:31Z ORDER 3 (lead): PR #12 is closed; its content is now PR #14 (branch followup-final, head d5b4451, one commit on main 61ded9e). When agent A has finished its run 2: start
    /tmp/smfull/handover/demo3/ORDERS.md:25:## 2026-11-13 10:29Z ORDER 4 (lead, PRIORITY over C2 tail): summary.md shows 56 F on MAIN 61ded9e (and 57 on PR 8d65577) and pytest ending at 71-72 percent with exit 1 and no summary line. T
    /tmp/smfull/handover/demo3/ORDERS.md:27:## 2026-11-13 10:38Z LEAD ANSWER to heartbeat 9 / ORDER 4: thank you, clear. ASK1 yes, default: C2 full -v on main and D runs on PR 14 are the clean runs; no extra rerun. ASK2: I fix it (doc
    /tmp/smfull/handover/demo3/ORDERS.md:29:## 2026-11-13 10:44Z ORDER 5 (lead): PR 14 head is now edadd00 (ruff fix + path nits inside it). The D runs on d5b4451 are stale. When D run 1 ends, do NOT start run 2 on d5b4451: start agen
    /tmp/smfull/handover/demo3/ORDERS.md:31:## 2026-11-13 11:22Z ORDER 6 (lead): PR 14 head is now 6b1fe49 (review fixes: URI built from the checked text; surrogate refusal; Windows-safe test). When E reports, start agent F: full suit
    /tmp/smfull/handover/demo3/evidence/reader-pr12-e-marks.md:8:- Recorded numbers: `evidence/summary.md:61-62` (run 1: 2489 / 57 F / 182 s / 0 E; run 2: 2488 / 57 F / 188 s / 2 E; both stopped at 72%, exit 1, 1172 s and 1126 s). `RE
    /tmp/smfull/handover/demo3/evidence/reader-pr12-e-marks.md:9:- The progress line positions of any `E` character were never recorded. The position claim "by position ... test_fakes_body_before_answer.py" has no stated line or perce
    /tmp/smfull/handover/demo3/evidence/reader-pr12-e-marks.md:14:- No. The log was `-q` without a summary, so no ERROR names exist. `questions-for-lead.md:2` (12:42Z) repeats "no traceback saved. By position they fall in tests/test_f
    /tmp/smfull/handover/demo3/evidence/reader-pr12-e-marks.md:21:  - run 1: `.` 2489, `F` 57, `s` 182, `E` 0 (matches summary.md:61 exactly)
    ... more than 10 (total 67)
===== L6-J-055 merged ids: ['L4c-FD-022', 'L4c-J-008'] | lane rows found: ['L4c-FD-022', 'L4c-J-008'] | missing: []
paths named: 2 basenames: 2
-- REVIEW-real-run-v6-fresh.md (paths: handover/demo/real-run/REVIEW-real-run-v6-fresh.md) referrers (excl. self and handover/system-map/*, which had 20 hits): 1
    /tmp/smfull/handover/demo/REPORT.md:31:**READY (handover-only per your ruling (c); fresh reads CLEAN: scripts /tmp/work/REVIEW-real-run-v6-fresh.md = handover/demo/real-run/REVIEW-real-run-v6-fresh.md; core hunks REVIEW-core-hunks
-- REVIEW-v4-fresh.md (paths: handover/demo/real-run/REVIEW-v4-fresh.md) referrers (excl. self and handover/system-map/*, which had 25 hits): 2
    /tmp/smfull/handover/demo/REPORT.md:990:1. **Your 04:02Z item 4 (proxy-line evidence): I CANNOT show it.** The sandbox proxy exposes no request log (only counters at $HTTPS_PROXY/__agentproxy/status; no per-request lines; /root/.c
    /tmp/smfull/handover/demo/REPORT.md:1056:1. **BREACH (the reviewer of real-run fixes v4, report sonar... real-run/REVIEW-v4-fresh.md, slip 1):** in its first matrix it answered `y` on five VALID synthetic configs; the desk started
===== L6-J-012 merged ids: ['L1-FD-003', 'L1-S-012', 'L1c-FD-003', 'L1c-FD-005', 'L1c-FD-007', 'L1c-S-003', 'L1c-S-007', 'L3c-FD-033', 'L4-FD-007', 'L4-FD-008', 'L4c-FD-009'] | lane rows found: ['L1-FD-003', 'L1-S-012', 'L1c-FD-003', 'L1c-FD-005', 'L1c-FD-007', 'L1c-S-003', 'L1c-S-007', 'L3c-FD-033', 'L4-FD-007', 'L4-FD-008', 'L4c-FD-009'] | missing: []
paths named: 21 basenames: 21
-- AB-PAPER.md (paths: handover/demo/pr-stack/AB-PAPER.md) referrers (excl. self and handover/system-map/*, which had 50 hits): 5
    /tmp/smfull/handover/demo/REPORT.md:1485:2. A/B paper (pr-stack/AB-PAPER.md, CARRY-OVER-CHECKLIST.md 291 rows, 11 evidence files): measured from the public API: Option A (retarget #4 = full tree) would show 226 files, +58211/-4, 1
    /tmp/smfull/handover/demo/REPORT.md:1524:| P-AB (opus) | A/B PR stack paper + carry-over checklist | 02:01 | running | pr-stack/AB-PAPER.md |
    /tmp/smfull/handover/demo/REPORT.md:1547:1 (PR stack A/B paper): STARTED: drafter P-AB (opus) writes pr-stack/AB-PAPER.md (one page + evidence appendix): evidence of what A shows (diff stat main...pr-3-tests, workflows that would 
    /tmp/smfull/handover/demo/REPORT.md:1559:| P-AB (opus) | A/B PR stack paper + carry-over checklist | 02:01 | running | pr-stack/AB-PAPER.md |
    /tmp/smfull/handover/demo/skips/SKIP-TABLE.md:84:Full suite run once on Windows on pr-3-tests 2db3926 (un-chunked): **3096 passed, 45 skipped, 0 failed, 22 min 30 s**. This replaces the earlier targeted '252 passed / 29 skipped' f
-- CARRY-OVER-CHECKLIST.md (paths: handover/demo/pr-stack/CARRY-OVER-CHECKLIST.md) referrers (excl. self and handover/system-map/*, which had 26 hits): 5
    /tmp/smfull/handover/demo/pr-stack/checklist.py:111:open(f"{D}/CARRY-OVER-CHECKLIST.md", "w").write("\n".join(out) + "\n")
    /tmp/smfull/handover/demo/pr-stack/AB-PAPER.md:50:| CodeAnt (inline and nitpicks) on #2 and #3 | Copy them into #4's description as a checklist that links to the closed PRs; that list is **CARRY-OVER-CHECKLIST.md** (291 rows, one 
    /tmp/smfull/handover/demo/pr-stack/AB-PAPER.md:101:- raw-*.json: raw API answers. CARRY-OVER-CHECKLIST.md is built from them by `checklist.py` in this folder (no network).
    /tmp/smfull/handover/demo/REPORT.md:1485:2. A/B paper (pr-stack/AB-PAPER.md, CARRY-OVER-CHECKLIST.md 291 rows, 11 evidence files): measured from the public API: Option A (retarget #4 = full tree) would show 226 files, +58211/-4, 1
    /tmp/smfull/handover/demo/REPORT.md:1547:1 (PR stack A/B paper): STARTED: drafter P-AB (opus) writes pr-stack/AB-PAPER.md (one page + evidence appendix): evidence of what A shows (diff stat main...pr-3-tests, workflows that would 
-- CRLF-GUARD-V7-NOTES.md (paths: handover/demo/skips/CRLF-GUARD-V7-NOTES.md) referrers (excl. self and handover/system-map/*, which had 8 hits): 0
-- FIXES.md (paths: handover/demo/real-run/FIXES.md) referrers (excl. self and handover/system-map/*, which had 14 hits): 20
    /tmp/smfull/handover/demo/real-run/REVIEW-v3-fresh.md:15:No money, no HubSpot call and no mail happen in these cases (the desk dies at start, the ledger stops spending), so I rate it Minor, not Major. But the person said "y" and a
    /tmp/smfull/handover/demo/real-run/REVIEW-core-hunks-v6-fresh.md:26:* Condition (a): FIXES.md v6 section lists all three with file, function, exact change, why (lines 67-70). Minor: the older v3 line 29 of FIXES.md still says "no 
    /tmp/smfull/handover/demo/real-run/REVIEW-core-hunks-v6-fresh.md:53:3.4 (Minor, record) FIXES.md stale "no logic change" line 29 for the live reader (v6 corrects it in a later bullet).
    /tmp/smfull/handover/demo/real-run/REVIEW-v4-fresh-copy.md:6:2. MAJOR (same class as the Minor v4 claims to close): `REAL_RESULT_FILE` is opened AFTER the question and is not checked. Measured: result file = an existing folder, or
    /tmp/smfull/handover/demo/real-run/REVIEW-v4-fresh-copy.md:34:Core touches (read line by line): `LiveQualifier._read_key`: adds a multi-line refusal and splits the old `len < 8 -> "holds no key"` into `empty -> holds no key`, `sho
    /tmp/smfull/handover/demo/real-run/REVIEW-v5-fresh.md:9:### MAJOR 1: the FIXES.md v5 claim "Core files touched compared with the base: ONE (`LiveQualifier._read_key`)" is false
    /tmp/smfull/handover/demo/real-run/REVIEW-v5-fresh.md:10:`git diff -- src/` on db54e13 + v5 shows THREE core files: `live_claude.py` (`_read_key`), `crm_hubspot.py` (`HubspotCrm._key`: the one "holds no key" message split in three
    /tmp/smfull/handover/demo/real-run/REVIEW-v5-fresh.md:75:- v5-after-sonar-p3 on db54e13 + p3-v3 (UNTESTED by the builder): applies cleanly; ruff/format/mypy linux+win32 clean (27 files); 269 passed + 1 failed (`test_v1_anywhere_re
    /tmp/smfull/handover/demo/real-run/REVIEW-v5-fresh.md:90:NOT CLEAN: Major 1 (core diff is three files, FIXES.md says one) and Minors 2 to 4 (DESK_DB_PATH parent-is-a-file reaches the question; scan holes and wrong "source order"/c
    /tmp/smfull/handover/demo/real-run/REVIEW-v4-fresh.md:6:2. MAJOR (same class as the Minor v4 claims to close): `REAL_RESULT_FILE` is opened AFTER the question and is not checked. Measured: result file = an existing folder, or a pa
    ... more than 10 (total 20)
-- PLAN.md (paths: handover/demo/fixes/PLAN.md) referrers (excl. self and handover/system-map/*, which had 28 hits): 85
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:2467:WHAT I WOULD DO NEXT (ranked): 1) write kill/PLAN.md with my own pass criteria BEFORE running anything; 2) write fakes (CRM search/create, stage qualify, SMTP c
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:2616:| kill/PLAN.md | written and pushed BEFORE any run (8ad6ec4c): kill points K1 stage in flight, K2 CRM stored but not answered, K3 after mail_sent before mail st
    /tmp/smfull/handover/demo3/evidence/numbers-audit.md:34:| 19 | "2349 passed and 116 skipped (... 2465 tests in all)"; "2462 passed and 3 skipped (2465 tests) in 958 s"; "2516 tests: 2513 passed and 3 skipped in 16 minutes 33 secon
    /tmp/smfull/handover/demo3/evidence/numbers-audit.md:59:| "2465 collected" (558d37f), "2516 collected" (2ce1f98), "2994 collected" | fixes/evidence-d7-collect-counts.txt:3-9; outsider/*, outsider2/*; coverage/PLAN.md:37; demo REPO
    /tmp/smfull/handover/demo/fixes/REVIEW-1.md:6:- M2 (docs/tests.md patch lines 47-49): counts labelled 'this commit' and 'measured' were not measured on b29bb1f, and 2462 was never measured on any tree without Pillow. Sources: spee
    /tmp/smfull/handover/demo/fixes/evidence-c12-both-scan-modes.txt:5:## step 2: TIGHTENED form (the one-line change PLAN.md tells to make after codeant2-gitleaks): path regex ^requirements-browser(-win)?\.txt$
    /tmp/smfull/handover/demo/fixes/REVIEW-2.md:5:M1. The new pixel reader has never been shown to fail on two DIFFERENT colours (evidence only breaks the tolerance). Where: tests/test_portal_lead_pages.py:436-459 (patched tree /tmp/w
    /tmp/smfull/handover/demo/fixes/REVIEW-2.md:6:M2. Facts in docs/tests.md stated as measured or verified have no raw evidence in the folder (the first review's N6 asked for exactly this): 'the Playwright 1.65.1 package lists build 
    /tmp/smfull/handover/demo/fixes/REVIEW-2.md:12:N3. `.codeant/configuration.json` (patch lines 1-12): CodeAnt (review bot) config; adds `requirements-browser.txt` and `requirements-browser-win.txt` to `exclude_files` next to the de
    /tmp/smfull/handover/demo/fixes/REVIEW-2.md:13:N4. docs/tests.md: patch lines 85-88 mix bash `export` with 'on Windows: requirements-browser-win.txt' (PowerShell has no `export`; the doc's own Windows block above uses PowerShell):
    ... more than 10 (total 85)
-- SUMMARY-codeant3-rt.md (paths: handover/demo/triage/SUMMARY-codeant3-rt.md) referrers (excl. self and handover/system-map/*, which had 22 hits): 2
    /tmp/smfull/handover/demo/pr-text/proposed/VERIFY.md:11:6. triage/SUMMARY-codeant3-rt.md L8 says the refusal "also refuses `file:` names"; the final code does NOT (desk.py docstring: "A `file:` name is NOT refused"). The text foll
    /tmp/smfull/handover/demo/REPORT.md:2182:4. Stand-in sweep done (your order): every other test/demo stand-in already reads the body before every answer path; none needed a fix; new guard tests (7) + mutants; two stand-ins inside t
-- SUMMARY-codeant5-sec.md (paths: handover/demo/triage/SUMMARY-codeant5-sec.md) referrers (excl. self and handover/system-map/*, which had 14 hits): 1
    /tmp/smfull/handover/demo/triage/REVIEW-codeant5-sec.md:10:(6) cross-lane: patch gitleaks anchors `^requirements-(dev(-win)?|coverage)\.txt$` and `^\.github[/\\]workflows[/\\][a-z]+\.yml$`; scan runs cwd=tree with '.' as lint.yml.
-- VERIFY.md (paths: handover/demo/pr-text/proposed/VERIFY.md) referrers (excl. self and handover/system-map/*, which had 33 hits): 7
    /tmp/smfull/handover/demo/pr-text/proposed/pr2-user-description.md:1:<!-- D-PR proposal for PR #2 (head pr-1-code d23cf8f, base main). Replaces ONLY the "User description" section; the CodeAnt-AI section below it stays. Every fact
    /tmp/smfull/handover/demo/pr-text/proposed/pr4-user-description.md:1:<!-- D-PR proposal for PR #4 (head pr-3-tests 2db3926, base pr-2-demo-folder). Replaces ONLY the "User description" section; the CodeAnt-AI section below it stay
    /tmp/smfull/handover/demo/pr-text/proposed/pr3-user-description.md:1:<!-- D-PR proposal for PR #3 (head pr-2-demo-folder f31e261, base pr-1-code). Replaces ONLY the "User description" section; the CodeAnt-AI section below it stays
    /tmp/smfull/handover/demo/REPORT.md:1715:1. PR TEXTS #2-#4 (verifier D-PR, evidence VERIFY.md 61 rows): things only the LEAD can decide. (a) MORE CORE CODE CHANGED than your approval lists cover: batch 1 (2ce1f98) changed src conf
    /tmp/smfull/handover/demo/REPORT.md:1740:| D-PR verified descriptions | done: pr2/pr3/pr4-user-description.md + VERIFY.md (needs the lead's approvals) |
    /tmp/smfull/handover/demo/REPORT.md:1767:| D-PR (opus) | verified PR #2/#3/#4 descriptions | 01:20 | running | pr-text/proposed/*.md + VERIFY.md |
    /tmp/smfull/handover/demo/REPORT.md:1795:| D-PR (opus) | verified descriptions for PR #2/#3/#4 | 01:36 | running | pr-text/proposed/*.md + VERIFY.md |
-- followup-a-review-fresh.md (paths: handover/demo/followup/followup-a-review-fresh.md) referrers (excl. self and handover/system-map/*, which had 6 hits): 2
    /tmp/smfull/handover/demo/followup/followup-ab-review-fresh2.md:39:7. A's earlier findings (followup-a-review-fresh.md): M1 mixed separators fixed (+ tests), M2 README backslashes fixed, m1 reworded, m4 typo fixed, m5 survivors co
    /tmp/smfull/handover/demo/REPORT.md:119:**FAILURES / UNCERTAINTIES FIRST.** (1) **Follow-up A fresh read NOT CLEAN (2 Majors, folded into the merge):** UNC refusal bypassed by mixed separators (`\/server\share/x.db`, `/\server/sha
-- followup-ab-review-fresh2.md (paths: handover/demo/followup/followup-ab-review-fresh2.md) referrers (excl. self and handover/system-map/*, which had 9 hits): 1
    /tmp/smfull/handover/demo/REPORT.md:73:**FAILURES FIRST.** (1) **Follow-up A+B `fd2adcdb...` NOT CLEAN (fresh read 2, /tmp/work/followup-ab-review-fresh2.md copied to handover/demo/followup/):** **M1: the new UNC refusal escapes a
-- followup-ab-v2-DO-NOT-USE-has-type-ignore.patch (paths: handover/demo/followup/followup-ab-v2-DO-NOT-USE-has-type-ignore.patch) referrers (excl. self and handover/system-map/*, which had 9 hits): 0
-- followup-ab-v3-review-fresh3.md (paths: handover/demo/followup/followup-ab-v3-review-fresh3.md) referrers (excl. self and handover/system-map/*, which had 20 hits): 2
    /tmp/smfull/handover/demo/REPORT.md:5:**READY (unchanged, all from CLEAN fresh reads; their CI-class gate runs in the reads are NOT claims I rely on any more: GitHub CI is authoritative):** (1) FOLLOW-UP PR: `handover/demo/followu
    /tmp/smfull/handover/demo/REPORT.md:17:**READY LINE: `handover/demo/followup/followup-ab-v3.patch` sha256 `f971de8756a6ef20156b86c66b3742ed8d7d96bc9334056bcd6e3819eda43eb2`; applies on main 61ded9e (forward `git apply --check` OK,
-- paused-b21-2026-11-14.md (paths: handover/demo3/evidence/paused-b21-2026-11-14.md) referrers (excl. self and handover/system-map/*, which had 19 hits): 3
    /tmp/smfull/handover/demo3/register.md:397:| b21 | PAUSED by lead order L3-STOP 10:50Z; note evidence/paused-b21-2026-11-14.md | | paused |
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:2473:| B21 fix-5 | PAUSED. Note evidence/paused-b21-2026-11-14.md, tree fc0fe30b (round 11). Mutants 121 of 121: 70 behaviour, 49 text pin, 2 survivors now pinned. I
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:2489:| B21 fix-5 | PAUSED, note evidence/paused-b21-2026-11-14.md written, hand-back received. Tree fc0fe30b7a4e (my git write-tree on its tree gives the same id; I 
-- paused-b22-2026-11-14.md (paths: handover/demo3/evidence/paused-b22-2026-11-14.md) referrers (excl. self and handover/system-map/*, which had 18 hits): 2
    /tmp/smfull/handover/demo3/register.md:398:| b22 | PAUSED by lead order L3-STOP 10:50Z; note evidence/paused-b22-2026-11-14.md | | paused |
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:2474:| B22 fix-2 | PAUSED. Note evidence/paused-b22-2026-11-14.md, tree 682a6969 (round 13 on the r12 tree 5d144259). Open: 4 of 36 mutants not cleanly killed (R2 O_
-- paused-b23-2026-11-14.md (paths: handover/demo3/evidence/paused-b23-2026-11-14.md) referrers (excl. self and handover/system-map/*, which had 17 hits): 2
    /tmp/smfull/handover/demo3/register.md:399:| b23 | PAUSED by lead order L3-STOP 10:50Z; note evidence/paused-b23-2026-11-14.md | | paused |
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:2475:| B23 fix-10 | PAUSED. Note evidence/paused-b23-2026-11-14.md, tree cb8d2e87 (round 7 in progress); last good tree 8a5c446e (round 6, 4 Majors open). Rows 1, 3,
-- pr2-user-description-v5.md (paths: handover/demo/pr-text/proposed/pr2-user-description-v5.md) referrers (excl. self and handover/system-map/*, which had 6 hits): 0
-- pr3-body.md (paths: handover/demo/pr-text/github-current/pr3-body.md) referrers (excl. self and handover/system-map/*, which had 10 hits): 0
-- pr4-A-user-description.md (paths: handover/demo/pr-text/proposed/pr4-A-user-description.md) referrers (excl. self and handover/system-map/*, which had 8 hits): 3
    /tmp/smfull/handover/demo/pr-text/proposed/VERIFY.md:121:Files: pr2/pr3/pr4-user-description-v5.md, pr4-A-user-description.md (older kept). [UNVERIFIED] count in all v5 and pr4-A files: 0 (grep).
    /tmp/smfull/handover/demo/ORDERS.md:181:2. DECISION A DONE: PR #4 is RETARGETED to main (226 files) with your pr4-A-user-description.md (head sha line updated to 7a386bc; now db54e13: update the text: add the sonar fix + new test 
    /tmp/smfull/handover/demo/REPORT.md:1518:4. Descriptions v5 (drafter): 0 [UNVERIFIED], the maintainer's answers applied (five core touches as plain facts; no CodeAnt/142 claim; branch protection and retarget wording dropped; Windo
-- pr4-body.md (paths: handover/demo/pr-text/github-current/pr4-body.md) referrers (excl. self and handover/system-map/*, which had 8 hits): 0
-- resolve-lane3-fix-6-r2.md (paths: handover/demo3/evidence/resolve-lane3-fix-6-r2.md) referrers (excl. self and handover/system-map/*, which had 8 hits): 1
    /tmp/smfull/handover/demo3/register.md:179:| RES-6b | closed 14:4xZ: egm-resolve fix-6 r2: 24 accepted, 1 wording contested (137 'not a kill' is false: os._exit), 0 escalated, 3 declined; saved evidence/resolve-lane3-fix-6-r2.md; 
-- review-lane3-fix-8-r3-delta.md (paths: handover/demo3/evidence/review-lane3-fix-8-r3-delta.md) referrers (excl. self and handover/system-map/*, which had 6 hits): 2
    /tmp/smfull/handover/demo3/register.md:281:| R8c | CLOSED 04:26Z | fix-8 r3 delta review 0/0/0 minors, 2 nits; saved evidence/review-lane3-fix-8-r3-delta.md |
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:265:| R8c | fresh review of fix-8 r3 delta | CLOSED: 0 blocker, 0 major, 0 minor, 2 nit (evidence/review-lane3-fix-8-r3-delta.md). My own slip: the delta file I gave
===== L6-J-039 merged ids: ['L1-FD-010', 'L2c-FD-008', 'L3c-FD-003', 'L3c-FD-018', 'L4-FD-003', 'L4-FD-004'] | lane rows found: ['L1-FD-010', 'L2c-FD-008', 'L3c-FD-003', 'L3c-FD-018', 'L4-FD-003', 'L4-FD-004'] | missing: []
paths named: 16 basenames: 16
-- DRIFT-REPORT-1.md (paths: handover/demo/drift/DRIFT-REPORT-1.md) referrers (excl. self and handover/system-map/*, which had 31 hits): 3
    /tmp/smfull/handover/demo/ORDERS.md:18:LANE 2, DRIFT REPORT (EGM, Sonnet): run `egm:egm-drift-report` through the Skill tool on the public demo clone from lane 1 (branch initial-code): do README.md, docs/*.md and contract.md still
    /tmp/smfull/handover/demo/drift/REVIEW-1.md:1:# REVIEW-1: egm:egm-codebase-details (sonnet) review of DRIFT-REPORT-1.md and docs-fixes.patch
    /tmp/smfull/handover/demo/REPORT.md:3405:- Lane 2 (drift): 3 doc-wrong, 0 code-wrong, 1 both-fine, 4 groups unverified. Files: drift/DRIFT-REPORT-1.md, drift/docs-fixes.patch (3 one-line hunks, git apply --check passed on a scratc
-- DRY-RUN-CHECKS.md (paths: handover/demo/real-run/DRY-RUN-CHECKS.md) referrers (excl. self and handover/system-map/*, which had 32 hits): 8
    /tmp/smfull/handover/demo/real-run/run-dry-checks.sh:29:# Mismatches seen on head 2db3926 (D1 to D6 in DRY-RUN-CHECKS.md) were all fixed by real-run-fixes.patch: the list is empty
    /tmp/smfull/handover/demo/real-run/NOTES-start-prompt-v2.md:57:   (rrc-noargs, rrc-cfg-*, rrc-assume-*, ...) now gets the no-terminal refusal first (Failures 3): run them through a pty driver (see pty_ans-q4g.py in this folder, wh
    /tmp/smfull/handover/demo/REPORT.md:1642:| Q4 dry-run checks | done: D1-D6 (DRY-RUN-CHECKS.md, run-dry-checks.sh) |
    /tmp/smfull/handover/demo/REPORT.md:1667:| Q4 builder | dry-run checks of the real-run scripts | 01:27 | finishing (evidence files written) | real-run/DRY-RUN-CHECKS.md |
    /tmp/smfull/handover/demo/REPORT.md:1697:| Q4 builder | dry-run checks of the real-run scripts | 01:27 | running | real-run/DRY-RUN-CHECKS.md |
    /tmp/smfull/handover/demo/REPORT.md:1727:| Q4 builder | dry-run checks of the real-run scripts | 01:27 | running | real-run/DRY-RUN-CHECKS.md |
    /tmp/smfull/handover/demo/REPORT.md:1768:| Q4 builder | dry-run checks of the real-run scripts | 01:27 | running | real-run/DRY-RUN-CHECKS.md |
    /tmp/smfull/handover/demo/REPORT.md:1799:| Q4 builder | dry-run checks of real-run scripts (synthetic) | 01:27 | running | real-run/DRY-RUN-CHECKS.md |
-- INT-1.md (paths: handover/demo/integration/INT-1.md) referrers (excl. self and handover/system-map/*, which had 18 hits): 13
    /tmp/smfull/handover/demo/APPLY-LIST.md:3:All patch paths are relative to handover/demo/ on branch demo/handover of hadavin-sdk. 'Reviewed' = a fresh egm:egm-codebase-details review with no Blocker and no Major (review file cited)
    /tmp/smfull/handover/demo/APPLY-LIST.md:28:INT-1 PARTIAL RESULTS (raw files integration/evidence-int1-*.txt; the INT-1.md summary and the full serial suite are still running; items 1 to 5 only: #6 is independent and was added late
    /tmp/smfull/handover/demo/APPLY-LIST.md:32:- BATCH 1: APPLIED by the lead on pr-3-tests: head 2ce1f98. INT-1 FINAL (integration/INT-1.md, evidence-int1-*.txt): all five patches apply with PLAIN `git apply` in both orders (1 2 3 4 
    /tmp/smfull/handover/demo/REPORT.md:2504:INT-1 (integration/INT-1.md): **batch 1 (items 1-5) applies cleanly in both orders (1 2 3 4 5 and 5 1 2 3 4: identical trees f621866d, 24 files, plain `git apply`) on 558d37f; REAL gitleaks
    /tmp/smfull/handover/demo/REPORT.md:2550:| ad08257c8fb71e8e6 (agent, sonnet evidence runner) | INT-1 integration check (full suite) | 20:37 | 18 min | 21:20 | running | INT-1.md | its pytest |
    /tmp/smfull/handover/demo/REPORT.md:2586:| ad08257c8fb71e8e6 (agent, sonnet evidence runner) | INT-1 integration check (full suite) | 20:37 | 15 min | 21:20 | running | INT-1.md | its pytest |
    /tmp/smfull/handover/demo/REPORT.md:2619:| ad08257c8fb71e8e6 (agent, sonnet evidence runner) | INT-1 integration check (full suite) | 20:37 | 11 min | 21:20 | running | INT-1.md | 5 evidence files; the full run is its long step |
    /tmp/smfull/handover/demo/REPORT.md:2639:**FOR THE LEAD, NOW:** INT-1 partial results (raw files integration/evidence-int1-*.txt, APPLY-LIST.md updated): batch 1 items 1 to 5 apply with PLAIN `git apply` (no --3way) in 3 different
    /tmp/smfull/handover/demo/REPORT.md:2655:| ad08257c8fb71e8e6 (agent, sonnet evidence runner) | INT-1 batch 1 integration check | 20:37 | 9 min | 21:20 | running (the full suite is its long step) | INT-1.md | 5 evidence files, last
    /tmp/smfull/handover/demo/REPORT.md:2693:| ad08257c8fb71e8e6 (agent, sonnet evidence runner) | INT-1 integration check batch 1 | 20:37 | 4 min | 21:20 | running | integration/INT-1.md | no file yet |
    ... more than 10 (total 13)
-- ORDERS.md (paths: handover/demo/ORDERS.md) referrers (excl. self and handover/system-map/*, which had 128 hits): 35
    /tmp/smfull/handover/demo3/ORDERS.md:17:## OWNERSHIP MAP (lead, owner request 09:58Z; no clashes): 3 cloud sessions, 3 branches of hadavin-sdk, none ever merges: core = core/cloud-handover (writes only under handover/core/ and han
    /tmp/smfull/handover/demo3/REPORT.md:47:- questions-for-lead.md: my questions and answers (Q-1 to Q-20). register.md: live register (rows for runs e to l are stale; the truth is kill/data/run_all.progress). ORDERS.md, FREEZE.md, M
    /tmp/smfull/handover/demo3/evidence/claims-stack-tests.md:15:Lint/gitleaks: skipped (no lead note newer than 11:40Z in demo3/ORDERS.md; ORDER 8 at 11:40Z is the latest). Studio backslash files not in this checkout.
    /tmp/smfull/handover/demo3/evidence/reader-e3b.md:3:Read on 2026-11-14. Nothing was run (no pytest). Sources: FREEZE.md:24, register.md:170 (E3b row), REPORT.md (E3b rows), ORDERS.md (12:58Z order, lines 73-77), evidence/lane3-fix
    /tmp/smfull/handover/demo3/evidence/review-lane3-needed-check-1.md:31:## Same-file edits (not same job): README.md (fix-1, fix-5 hard conflict at the "You need Linux or Windows" line; claims hunk carries fix-5's reset-paragraph as
    /tmp/smfull/handover/demo3/evidence/patch-status.md:14:LEAD DECISIONS 04:30Z (ORDERS.md): frozen claims series = claims-stack-on-f3c39cf8.patch; demo doc patches 0001/0002/0003 are three drafts of one job, NONE is applied; a singl
    /tmp/smfull/handover/demo3/evidence/reader-pr12-e-marks.md:30:- Yes. ORDERS.md:73-74 (12:58Z order item 1): "Your 4 earlier full runs on main/PR #12 are INVALID as pass/fail evidence (basetemp outside TMPDIR: 56 F; logs cut by git
    /tmp/smfull/handover/demo3/evidence/reader-pr12-e-marks.md:35:- None. PR #12 was closed; its content became PR #14 (ORDERS.md:21, ORDER 3: branch followup-final, head d5b4451). No full run on 8d65577 was repeated (flake-chase-fake
    /tmp/smfull/handover/demo3/evidence/resolve-lane3-fix-5-r10.md:11:(LEAD RULING 09:5xZ: NO exception; build literals from parts, chr(92) joins; do not touch the existing 0.0.0.0 exception; see ORDERS.md)
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:676:NEW ORDER (ORDERS.md 02:49Z): second-Python matrix. Facts so far: the repo says requires-python >=3.12, so 3.11 is NOT a supported version (I will only record th
    ... more than 10 (total 35)
-- PLAN.md (paths: handover/demo/fixes/PLAN.md) referrers (excl. self and handover/system-map/*, which had 28 hits): 85
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:2467:WHAT I WOULD DO NEXT (ranked): 1) write kill/PLAN.md with my own pass criteria BEFORE running anything; 2) write fakes (CRM search/create, stage qualify, SMTP c
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:2616:| kill/PLAN.md | written and pushed BEFORE any run (8ad6ec4c): kill points K1 stage in flight, K2 CRM stored but not answered, K3 after mail_sent before mail st
    /tmp/smfull/handover/demo3/evidence/numbers-audit.md:34:| 19 | "2349 passed and 116 skipped (... 2465 tests in all)"; "2462 passed and 3 skipped (2465 tests) in 958 s"; "2516 tests: 2513 passed and 3 skipped in 16 minutes 33 secon
    /tmp/smfull/handover/demo3/evidence/numbers-audit.md:59:| "2465 collected" (558d37f), "2516 collected" (2ce1f98), "2994 collected" | fixes/evidence-d7-collect-counts.txt:3-9; outsider/*, outsider2/*; coverage/PLAN.md:37; demo REPO
    /tmp/smfull/handover/demo/fixes/REVIEW-1.md:6:- M2 (docs/tests.md patch lines 47-49): counts labelled 'this commit' and 'measured' were not measured on b29bb1f, and 2462 was never measured on any tree without Pillow. Sources: spee
    /tmp/smfull/handover/demo/fixes/evidence-c12-both-scan-modes.txt:5:## step 2: TIGHTENED form (the one-line change PLAN.md tells to make after codeant2-gitleaks): path regex ^requirements-browser(-win)?\.txt$
    /tmp/smfull/handover/demo/fixes/REVIEW-2.md:5:M1. The new pixel reader has never been shown to fail on two DIFFERENT colours (evidence only breaks the tolerance). Where: tests/test_portal_lead_pages.py:436-459 (patched tree /tmp/w
    /tmp/smfull/handover/demo/fixes/REVIEW-2.md:6:M2. Facts in docs/tests.md stated as measured or verified have no raw evidence in the folder (the first review's N6 asked for exactly this): 'the Playwright 1.65.1 package lists build 
    /tmp/smfull/handover/demo/fixes/REVIEW-2.md:12:N3. `.codeant/configuration.json` (patch lines 1-12): CodeAnt (review bot) config; adds `requirements-browser.txt` and `requirements-browser-win.txt` to `exclude_files` next to the de
    /tmp/smfull/handover/demo/fixes/REVIEW-2.md:13:N4. docs/tests.md: patch lines 85-88 mix bash `export` with 'on Windows: requirements-browser-win.txt' (PowerShell has no `export`; the doc's own Windows block above uses PowerShell):
    ... more than 10 (total 85)
-- SKIP-TABLE.md (paths: handover/demo/skips/SKIP-TABLE.md) referrers (excl. self and handover/system-map/*, which had 18 hits): 7
    /tmp/smfull/handover/demo/pr-text/proposed/VERIFY.md:13:8. skips/ has no SKIP-TABLE.md (Q5 not finished): only two evidence files, one marked INVALID. Not cited.
    /tmp/smfull/handover/demo/pr-stack/AB-PAPER.md:69:So the **166 browser tests are skipped in both jobs**, and the **27 gitleaks and hygiene tests are skipped in the Sonar job** (skips/SKIP-TABLE.md lines 24 and 33). Neither job ins
    /tmp/smfull/handover/demo/integration/INT-3-2db3926.md:12:Fresh clone /tmp/work/h4 of public pr-3-tests 2db3926 (verified), no git operations in it, `python -u -m pytest tests -v -o faulthandler_timeout=300 -p no:cacheprovider -rs
    /tmp/smfull/handover/demo/REPORT.md:1550:4 (your Windows full run): USED as the Windows column of the skip table (skips/SKIP-TABLE.md, pushed): 3096 passed, 45 skipped, 0 failed, 22:30; 24+4+3+10+4 = 45 adds up. I treat the 252/29
    /tmp/smfull/handover/demo/REPORT.md:1756:2. Q5 (skips/SKIP-TABLE.md, pushed next): the lead's Windows '252 passed / 29 skipped' is a TARGETED run (not the full suite): the builder can name only 11 platform skips (reset.sh 4, /proc
    /tmp/smfull/handover/demo/REPORT.md:1779:| Q5 skip table | done (SKIP-TABLE.md + 6 evidence files) |
    /tmp/smfull/handover/demo/REPORT.md:1798:| Q5 builder | skip table (Linux/Windows) | 01:27 | running | skips/SKIP-TABLE.md |
-- SUMMARY.md (paths: handover/demo/outsider/SUMMARY.md) referrers (excl. self and handover/system-map/*, which had 93 hits): 58
    /tmp/smfull/handover/demo3/evidence/numbers-audit.md:34:| 19 | "2349 passed and 116 skipped (... 2465 tests in all)"; "2462 passed and 3 skipped (2465 tests) in 958 s"; "2516 tests: 2513 passed and 3 skipped in 16 minutes 33 secon
    /tmp/smfull/handover/demo/pr-text/semgrep-pr-claims.md:14:| 8 | tests/ and demo_only/ not scanned, decided without a scan result; reasons | Patch, docs/tests.md "What is scanned, and what is not"; SUMMARY.md N5 and lead decision 5
    /tmp/smfull/handover/demo/pr-text/semgrep-pr-claims.md:20:| 14 | v1: "Not a required check unless the owner makes it one"; v2: "intended not to be a required check" | Patch workflow comment "Keep it OUT of the required checks"; SU
    /tmp/smfull/handover/demo/pr-text/semgrep-pr-claims.md:27:| 21 | Owner's written yes covers p/python and p/javascript, this repo only; public log with rule ids/messages accepted under it | SUMMARY.md last line ("Licence yes covers
    /tmp/smfull/handover/demo/pr-text/semgrep-pr-claims.md:43:| 37 | Hash allowance root-only `^requirements-semgrep\.txt$`; nested copy still reported; tightened from looser pattern | Patch .gitleaks.toml hunk; SUMMARY.md item 4 (old
    /tmp/smfull/handover/demo/pr-text/semgrep-pr-claims.md:55:| 49 | Full suite NOT run on this PR; earlier version on 0841f36: 2426 passed, 115 skipped | evidence-sg-10-full-pytest.txt; SUMMARY.md BLOCKER 1 | Read |
    /tmp/smfull/handover/demo/outsider2/SUMMARY.md:41:/tmp/demo-wt/handover/demo/outsider/SUMMARY.md was still marked 'in progress' when I read it (branch initial-code, head 43110e7, python3.12 venv + pip). It lists ruff, mypy (linux,
    /tmp/smfull/handover/demo/fixes/REVIEW-1.md:7:- M3 (rule 6/14): the 'why' for the two lead numbers is stated as fact, but the raw evidence shows a hypothesis, and one source contradicts the log. The doc says the 2329/135 count 'is
    /tmp/smfull/handover/demo/fixes/REVIEW-3.md:18:Verified: 1.65.1 names chromium 1254 and 1.63.0 names 1243 (c2); node v22.23.4 (c2); the --require-hashes installs (c5); `git diff --stat b29bb1f 558d37f` .gitleaks.toml +7 (c3); all 
    /tmp/smfull/handover/demo/fixes/PLAN.md:22:| Nit: "Executable doesn't exist" message came only from outsider/SUMMARY.md | fixed | Message reproduced with Playwright 1.65.1 and only build 1243 present | evidence-d4c2 |
    ... more than 10 (total 58)
-- cold-reader-n8n-limits.md (paths: handover/demo3/evidence/cold-reader-n8n-limits.md) referrers (excl. self and handover/system-map/*, which had 18 hits): 3
    /tmp/smfull/handover/demo3/evidence/review-lane3-fix-1-r2-technical.md:12:## Checked and correct (18): /counts fields (desk.py:2437-2455; all numbers 0 on a fresh desk, _COUNTS_SQL desk.py:271-281); `hung_workers` has exactly four
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:1364:| Q5 / Q6 cold readers | docs steps, not tests | Q5: 0 failures; Q6: 4 documentation mismatches (n8n not installable here; workflow ports hardcoded vs settings.
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:1392:**Q6 RESULT (cold reader on docs/n8n-recipe.md and docs/limits.md; full report evidence/cold-reader-n8n-limits.md):** FAILS: (1) n8n is not installed, there is 
-- cold-reader-tests-realservices.md (paths: handover/demo3/evidence/cold-reader-tests-realservices.md) referrers (excl. self and handover/system-map/*, which had 20 hits): 1
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:932:**Q6b RESULT (evidence/cold-reader-tests-realservices.md): REAL DOC DEFECTS.** (1) docs/tests.md crash-desk command fails without `PYTHONPATH=src:.` (exit 1 Modu
-- e8-fix-6-report.md (paths: handover/demo3/evidence/e8-fix-6-report.md) referrers (excl. self and handover/system-map/*, which had 8 hits): 3
    /tmp/smfull/handover/demo3/register.md:172:| E8 | closed 14:21Z: fix-6 r1 evidence. Full serial on final tree (valid): 3689 passed 200 skipped rc 0 20m22s. Fails-before: 6 failed on base, 6 passed patched. Documented commands (src
    /tmp/smfull/handover/demo3/evidence/lane3-fix-6-r2-notes.md:17:| A4 counts | sum written 166+30+1+1+1+1=200 with the four named; 196 derived; 241 (113+128, ten files named from a grep: ten found) and 72 (24+44+4) as whole-file tot
    /tmp/smfull/handover/demo3/evidence/lane3-fix-6-r2-notes.md:43:- E8 (`e8-fix-6-report.md`) confirms for the r1 patch: 3689 passed, 200 skipped, 20 min 22 s, exit 0. Added to docs/tests.md as "A full run with the first version of t
-- register.md (paths: handover/demo3/register.md) referrers (excl. self and handover/system-map/*, which had 188 hits): 20
    /tmp/smfull/handover/demo3/MATRIX-1.md:133:- M5 control run: 5 other files made no `data/`. The other files were not run one by one, so other creators are not ruled out. There is no m5-report.md on disk (not present); the M5 facts
    /tmp/smfull/handover/demo3/MATRIX-1.md:180:| m5-report.md | file absent; facts from the lead's hand-back | ask for it to be saved, or rely on register.md row |
    /tmp/smfull/handover/demo3/REPORT.md:47:- questions-for-lead.md: my questions and answers (Q-1 to Q-20). register.md: live register (rows for runs e to l are stale; the truth is kill/data/run_all.progress). ORDERS.md, FREEZE.md, M
    /tmp/smfull/handover/demo3/FREEZE.md:3:All agents of this lane have reported and are closed (register.md). Nothing was pushed to the demo repo or merged. All patches are under `handover/demo3/evidence/`. Tests are full serial runs
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:2:Sources read: evidence/xdist-proof.md, xdist-root-cause.md, raw/b-n2-1.log, raw/progress-E7.txt, raw/E7-a1.log, E7-a2.log, lane3-fix-5-r4-notes.md, lane3-fix-5-r4.patch, 
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:12:- Siblings: b-n2-2, b-n2-3 (-n 2): 60 passed; b-n4-1..3 (-n 4): 60 passed (tails of logs). E7-a1/a2: 226 passed, 4 skipped, both rc 0. The original full-suite failure of
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:15:- E7 closed (register.md:169): "1 flake, cause not investigated".
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:17:- The same notes say: "The old failure itself was not reproduced here (it is rare); the cause is by reading plus the unit test." (lane3-fix-5-r4-notes.md "Not done or un
    /tmp/smfull/handover/demo3/evidence/reader-e3b.md:3:Read on 2026-11-14. Nothing was run (no pytest). Sources: FREEZE.md:24, register.md:170 (E3b row), REPORT.md (E3b rows), ORDERS.md (12:58Z order, lines 73-77), evidence/lane3-fix
    /tmp/smfull/handover/demo3/evidence/reader-e3b.md:48:| G. the signal came from the crash-soak tools (Q3b/Q3c) killing a stale or reused pid | SILENT | Q3b ran 12:49Z-~13:40Z, Q3c 13:03Z-~14:00Z (register.md:60, :85), overlapping r
    ... more than 10 (total 20)
-- review-lane3-needed-check-1.md (paths: handover/demo3/evidence/review-lane3-needed-check-1.md) referrers (excl. self and handover/system-map/*, which had 16 hits): 3
    /tmp/smfull/handover/demo3/register.md:286:| NC1 | CLOSED 04:32Z | report saved evidence/review-lane3-needed-check-1.md; tables folded into patch-status.md |
    /tmp/smfull/handover/demo3/evidence/patch-status.md:30:## NEEDED-CHECK 1 (lead order 04:23Z): what each patch changes and where two change the same job (full tables: evidence/review-lane3-needed-check-1.md; reader's own limits: no
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:238:| NC1 | NEEDED-CHECK duplicate check (lead order 04:23Z) | CLOSED. Saved evidence/review-lane3-needed-check-1.md and a table in evidence/patch-status.md. Reader'
-- run-demo-linux.sh (paths: handover/demo/speed/run-demo-linux.sh) referrers (excl. self and handover/system-map/*, which had 8 hits): 7
    /tmp/smfull/handover/demo/speed/RUNBOOK-SPEED-3.md:20:Carrier: sdk repo `hadavin-dx/hadavin-sdk`, branch `demo/handover`, folder `handover/demo/speed/`. The lead pushes the files below (copied from `C:\Users\rakes\Downloads\Hadavi
    /tmp/smfull/handover/demo/speed/RUNBOOK-SPEED-3.md:22:Files to push (exact sha256 at 2026-11-12, also in `runbook-files\SHA256SUMS`; the cloud side checks with `sha256sum -c SHA256SUMS`). Hashes: ci-xdist-demo-b29bb1f.patch 5680b7
    /tmp/smfull/handover/demo/speed/RUNBOOK-SPEED-3.md:29:| `run-demo-linux.sh`, `run-sdk-linux.sh`, `quiet-check.sh` | the commands below, as scripts |
    /tmp/smfull/handover/demo/speed/RUNBOOK-SPEED-3.md:38:bash $HERE/run-demo-linux.sh serial 1      # then: serial 2
    /tmp/smfull/handover/demo/speed/RUNBOOK-SPEED-3.md:39:bash $HERE/run-demo-linux.sh par 1 3       # then: par 2, par 3   (3 = workers; nproc is 4, 3 leaves one core for the OS)
    /tmp/smfull/handover/demo/speed/SHA256SUMS:5:1da3ac4f7e84eab032000c200254e24c4157c8c28d5f5aa60de5e52dd077a7c5 *run-demo-linux.sh
    /tmp/smfull/handover/demo/speed/evidence-phase4.md:37:`egm\speedup-repos\RUNBOOK-SPEED-3.md`, `run-ledger.tsv`, `evidence-phase4.md`, `phase4-checkpoint.md`, `runbook-files\` (ci-xdist-demo-b29bb1f.patch, fake-hubspot-read-body-be
-- skipped-on-purpose.md (paths: handover/demo3/evidence/skipped-on-purpose.md) referrers (excl. self and handover/system-map/*, which had 15 hits): 6
    /tmp/smfull/handover/demo3/evidence/lane3-fix-6-notes.md:6:- Not checked: Windows commands in the docs (`;` form only copied from the existing text); the browser/gitleaks/3.13 numbers were NOT reproduced by me, quoted from `unskip
    /tmp/smfull/handover/demo3/evidence/lane3-fix-6-notes.md:7:- Number conflict: the brief says 29 gitleaks skips and the cold reader says about 29 and 163 browser skips; `skipped-on-purpose.md` (read from the log) says 30 gitleaks (
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:1538:| M | Agent (read-only): classify the 200 skips | tells which skips can never run here | 12:00Z / 17:30 | ended 12:00Z | first try | reported, closed (evidence/
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:1544:M RESULT (nothing was run; read from the log and sources): 200 = 166 Playwright + 30 gitleaks + 4 others, as ordered. The 4 others: (1) `tests/test_stall_evicti
    /tmp/smfull/handover/demo3/evidence/summary.md:21:Reading: 196 of the 200 skipped tests now run and **all pass on both heads** (exit 0 on every run): Playwright 1.63.0 with Chromium build 1243 (pre-installed in /opt/pw-browsers, m
    /tmp/smfull/handover/demo3/evidence/numbers-audit.md:41:| "3683 passed, 0 failed, 200 skipped, 1189 s" BASE f3c39cf8, Python 3.12.3 | evidence/summary.md:2 and :24-26; py313-vs-py312.md:7; claims-stack-tests.md:7; skipped-on-purpo
-- unskip-gitleaks.md (paths: handover/demo3/evidence/unskip-gitleaks.md) referrers (excl. self and handover/system-map/*, which had 6 hits): 5
    /tmp/smfull/handover/demo3/evidence/lane3-fix-6-notes.md:6:- Not checked: Windows commands in the docs (`;` form only copied from the existing text); the browser/gitleaks/3.13 numbers were NOT reproduced by me, quoted from `unskip
    /tmp/smfull/handover/demo3/evidence/py313-unskip.md:17:Command (script /home/user/work/q7-run.sh <base|stack> <worktree>): `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers TMPDIR=/home/user/work/q7-tmp/<group>-<head> timeout 1500 python
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:1533:L RESULT (I read both raw logs): the 30 gitleaks-skipped tests now run and pass. BASE f3c39cf8: **72 passed, 0 failed, 0 skipped**, exit 0, 76 s; STACK (f3c39cf
    /tmp/smfull/handover/demo3/evidence/summary.md:21:Reading: 196 of the 200 skipped tests now run and **all pass on both heads** (exit 0 on every run): Playwright 1.63.0 with Chromium build 1243 (pre-installed in /opt/pw-browsers, m
    /tmp/smfull/handover/demo3/evidence/numbers-audit.md:49:| 196 of 200 skips now run and pass (113+128 browser, 72 gitleaks+hygiene) | summary.md:12-21; unskip-browser.md; unskip-gitleaks.md; py313-unskip.md | agents K, L, M, whole 
-- xdist-proof.md (paths: handover/demo3/evidence/xdist-proof.md) referrers (excl. self and handover/system-map/*, which had 6 hits): 6
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:2:Sources read: evidence/xdist-proof.md, xdist-root-cause.md, raw/b-n2-1.log, raw/progress-E7.txt, raw/E7-a1.log, E7-a2.log, lane3-fix-5-r4-notes.md, lane3-fix-5-r4.patch, 
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:5:- A. Q1/Q11: deterministic exit 6 ("is not the desk") under xdist. Cause PROVEN (COLUMNS=80 makes `ps` cut the line; scripts/reset.sh:34). Has nothing to do with port 432
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:27:- No fails-before run of the xdist flake: not done. The pre-fix code was run xdist at -n 2 x3 and -n 4 x3 (E7 b runs): 1 failure in 6 runs, 5 passes; no larger pre-fix s
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:28:- Q1 (xdist-proof.md:27) saw no flake across 2 full runs at -n 3.
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:48:6. Machine load effect: E7 ran with other agents loading the machine (load figures in xdist-proof.md:20 for Q1; E7 load not recorded).
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:1051:**Q1 RESULT (xdist proof; evidence/xdist-proof.md; pytest-xdist 3.8.0 + pytest 9.2.0 + execnet 2.1.2 in a THROWAWAY venv only, nothing entered the repo):** seri
===== L6-J-049 merged ids: ['L1-J-001', 'L1-J-005', 'L2-FD-012', 'L2c-J-001'] | lane rows found: ['L1-J-001', 'L1-J-005', 'L2-FD-012', 'L2c-J-001'] | missing: []
paths named: 10 basenames: 10
-- REPORT.md (paths: handover/demo/REPORT.md) referrers (excl. self and handover/system-map/*, which had 146 hits): 64
    /tmp/smfull/handover/demo3/register.md:327:| LAYOUT | 05:57Z | lead layout order applied: REPORT.md newest first (HB102 on top, HB99 below), old blocks in evidence/REPORT-archive-2026-11-14.md, 24 lines | closed |
    /tmp/smfull/handover/demo3/ORDERS.md:8:Outputs: `handover/demo3/evidence/<name>.md` + raw logs under `handover/demo3/evidence/raw/`, committed and pushed to YOUR branch `demo/lane3` of hadavin-dx/hadavin-sdk only. Heartbeat: appen
    /tmp/smfull/handover/demo3/ORDERS.md:60:1. `git fetch origin core/cloud-handover demo/handover demo/lane3` (your own branch is the one you push; read the other two read-only) and read the newest block of the two sibling REPORT fil
    /tmp/smfull/handover/demo3/ORDERS.md:149:## 2026-11-14 05:54Z LEAD ORDER (lane3) REPORT LAYOUT: your REPORT.md is 1900+ lines and HB100/HB101 are at the BOTTOM (line 1900+); I read the top and took you for silent. Rule: the NEWEST
    /tmp/smfull/handover/demo3/REPORT.md:10:EVERYTHING FOR THE LEAD IS IN THE REPO (branch demo/lane3): REPORT.md (this block and the STOP-2 closeout below it), kill/PLAN-GO1.md, kill/make_go1.py, kill/flows-go1/ (fixed recovery flow,
    /tmp/smfull/handover/demo3/REPORT.md:46:- REPORT.md: this block. evidence/REPORT-archive-2026-11-14.md: all older blocks (HB1 to HB193).
    /tmp/smfull/handover/demo3/REPORT.md:63: M handover/demo3/REPORT.md
    /tmp/smfull/handover/demo3/REPORT.md:65: M REPORT.md
    /tmp/smfull/handover/demo3/REPORT.md:78: handover/demo3/REPORT.md | 44 ++++++++++++++++++++++++++++++++------------
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:2:Sources read: evidence/xdist-proof.md, xdist-root-cause.md, raw/b-n2-1.log, raw/progress-E7.txt, raw/E7-a1.log, E7-a2.log, lane3-fix-5-r4-notes.md, lane3-fix-5-r4.patch, 
    ... more than 10 (total 64)
-- register.md (paths: handover/demo3/register.md) referrers (excl. self and handover/system-map/*, which had 188 hits): 20
    /tmp/smfull/handover/demo3/MATRIX-1.md:133:- M5 control run: 5 other files made no `data/`. The other files were not run one by one, so other creators are not ruled out. There is no m5-report.md on disk (not present); the M5 facts
    /tmp/smfull/handover/demo3/MATRIX-1.md:180:| m5-report.md | file absent; facts from the lead's hand-back | ask for it to be saved, or rely on register.md row |
    /tmp/smfull/handover/demo3/REPORT.md:47:- questions-for-lead.md: my questions and answers (Q-1 to Q-20). register.md: live register (rows for runs e to l are stale; the truth is kill/data/run_all.progress). ORDERS.md, FREEZE.md, M
    /tmp/smfull/handover/demo3/FREEZE.md:3:All agents of this lane have reported and are closed (register.md). Nothing was pushed to the demo repo or merged. All patches are under `handover/demo3/evidence/`. Tests are full serial runs
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:2:Sources read: evidence/xdist-proof.md, xdist-root-cause.md, raw/b-n2-1.log, raw/progress-E7.txt, raw/E7-a1.log, E7-a2.log, lane3-fix-5-r4-notes.md, lane3-fix-5-r4.patch, 
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:12:- Siblings: b-n2-2, b-n2-3 (-n 2): 60 passed; b-n4-1..3 (-n 4): 60 passed (tails of logs). E7-a1/a2: 226 passed, 4 skipped, both rc 0. The original full-suite failure of
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:15:- E7 closed (register.md:169): "1 flake, cause not investigated".
    /tmp/smfull/handover/demo3/evidence/reader-xdist-flake.md:17:- The same notes say: "The old failure itself was not reproduced here (it is rare); the cause is by reading plus the unit test." (lane3-fix-5-r4-notes.md "Not done or un
    /tmp/smfull/handover/demo3/evidence/reader-e3b.md:3:Read on 2026-11-14. Nothing was run (no pytest). Sources: FREEZE.md:24, register.md:170 (E3b row), REPORT.md (E3b rows), ORDERS.md (12:58Z order, lines 73-77), evidence/lane3-fix
    /tmp/smfull/handover/demo3/evidence/reader-e3b.md:48:| G. the signal came from the crash-soak tools (Q3b/Q3c) killing a stale or reused pid | SILENT | Q3b ran 12:49Z-~13:40Z, Q3c 13:03Z-~14:00Z (register.md:60, :85), overlapping r
    ... more than 10 (total 20)
-- run_b.sh (paths: handover/demo3/kill/run_b.sh) referrers (excl. self and handover/system-map/*, which had 23 hits): 3
    /tmp/smfull/handover/demo3/kill/run_c.sh:2:# lane3 kill script, third batch: two more runs of each fault mode (sample size 3 each) on the 11:05Z flows. Starts after run_b.sh.
    /tmp/smfull/handover/demo3/register.md:402:| KILL-RUN-B | queued 12:38Z: kill/run_b.sh (waits for run_all.sh, then BURST x3, ERROR x2, GREP x3 on the 11:05Z flows, then T14 idle 120 s x3 on the FIXED flows 8e2b6960); same progress
    /tmp/smfull/handover/demo3/evidence/REPORT-archive-2026-11-14.md:2736:| ERROR (CRM refuses every call, expect failed + exactly 1 alert), GREP (planted address, name and fake key), T14 (idle 120 s on the FIXED flows 8e2b6960, 3 run
-- run_f.sh (paths: handover/demo3/kill/run_f.sh) referrers (excl. self and handover/system-map/*, which had 10 hits): 0
-- run_h.sh (paths: handover/demo3/kill/run_h.sh) referrers (excl. self and handover/system-map/*, which had 19 hits): 0
-- run_k.sh (paths: handover/demo3/kill/run_k.sh) referrers (excl. self and handover/system-map/*, which had 7 hits): 0
-- run_l.sh (paths: handover/demo3/kill/run_l.sh) referrers (excl. self and handover/system-map/*, which had 10 hits): 0
-- run_m.sh (paths: handover/demo3/kill/run_m.sh) referrers (excl. self and handover/system-map/*, which had 7 hits): 0
-- run_n.sh (paths: handover/demo3/kill/run_n.sh) referrers (excl. self and handover/system-map/*, which had 7 hits): 0
-- run_p.sh (paths: handover/demo3/kill/run_p.sh) referrers (excl. self and handover/system-map/*, which had 9 hits): 3
    /tmp/smfull/handover/demo3/REPORT.md:10:EVERYTHING FOR THE LEAD IS IN THE REPO (branch demo/lane3): REPORT.md (this block and the STOP-2 closeout below it), kill/PLAN-GO1.md, kill/make_go1.py, kill/flows-go1/ (fixed recovery flow,
    /tmp/smfull/handover/demo3/REPORT.md:21:FILES: kill/make_go1.py, kill/flows-go1/, kill/PLAN-GO1.md, kill/run_p.sh (version 5), evidence/go1/.
    /tmp/smfull/handover/demo3/REPORT.md:50:- kill/harness.py (kill points, GREP, ERROR; env LANE for parallel lanes), kill/fakes.py (fake CRM, stage, SMTP with hold/refuse/dead switches), kill/v3.py (alert cases A, B20, B90, B780, C,
```

## Task 4: counts in ONE-PLACE-TABLE.md
```
rows per block (line-start L6-J- rows): {'Job: STORE': 11, 'Job: LOG': 9, 'Job: FILTER': 9, 'Job: COUNTER': 5, 'Job: RETRY': 8, 'Job: NOTICE': 6, 'Job: OTHER': 1, 'Appendix: build-process rows (not places of a take job)': 10} total 59
Owner: lines (start of line "Owner:"): 7
Open owner: lines: 3
lines containing "Owner:" anywhere: 8
verdict column counts (col 3): {'OWNER': 6, 'NEEDED': 11, 'DUPLICATE': 12, 'KEEP-CORE': 17, 'NOT-NEEDED': 12, 'CRM-COULD-DO': 1}
DUPLICATE exact verdict: 12 | rows where cell startswith: 12 | per block: {'Job: STORE': 2, 'Job: LOG': 1, 'Job: FILTER': 2, 'Job: COUNTER': 2, 'Job: RETRY': 2, 'Job: NOTICE': 1, 'Appendix: build-process rows (not places of a take job)': 2}
NEEDED exact verdict: 11 | rows where cell startswith: 11 | per block: {'Job: STORE': 3, 'Job: LOG': 2, 'Job: FILTER': 2, 'Job: COUNTER': 1, 'Job: RETRY': 1, 'Job: NOTICE': 2}
OWNER exact verdict: 6 | rows where cell startswith: 6 | per block: {'Job: STORE': 1, 'Job: LOG': 1, 'Job: FILTER': 1, 'Job: COUNTER': 1, 'Job: RETRY': 1, 'Job: NOTICE': 1}
KEEP-CORE exact verdict: 17 | rows where cell startswith: 17 | per block: {'Job: STORE': 4, 'Job: LOG': 2, 'Job: FILTER': 3, 'Job: COUNTER': 1, 'Job: RETRY': 4, 'Job: NOTICE': 1, 'Appendix: build-process rows (not places of a take job)': 2}
NOT-NEEDED exact verdict: 12 | rows where cell startswith: 12 | per block: {'Job: STORE': 1, 'Job: LOG': 3, 'Job: NOTICE': 1, 'Job: OTHER': 1, 'Appendix: build-process rows (not places of a take job)': 6}
CRM-COULD-DO exact verdict: 1 | rows where cell startswith: 1 | per block: {'Job: FILTER': 1}
proposal cell contains ARCHIVE: 11 ['L6-J-004', 'L6-J-016', 'L6-J-019', 'L6-J-029', 'L6-J-036', 'L6-J-044', 'L6-J-054', 'L6-J-055', 'L6-J-012', 'L6-J-039', 'L6-J-049']
whole row contains ARCHIVE: 11
proposal values: {'AFTER THE VIDEO: n8n Retry On Fail cannot filter by error type (UNVERIFIED), so the trim is not implementable as written; removing it also makes recovery wait for the 120 s lease': 1, 'ARCHIVE (after the studio head says yes)': 5, 'ARCHIVE BLOCKED until the laptop lead shows which counter the take proof reads, and the desk security patches are applied (L6-EX-11)': 6, 'CHANGE (keep the weekly cron and tools/mutation_runner.py, which tests use; bound the curl retry at ci.yml line 228 and add a failure notice)': 1, 'CHANGE (replace by three least-privilege roles plus a migrations identity, see Fix plan)': 1, 'FIX THE HARNESS (it recreates the empty files every run); no archive': 1, 'KEEP (CI)': 2, 'KEEP (dependabot.yml and .coderabbit.yaml are live gates; CLAUDE.md lists CodeRabbit as a required pull request gate)': 1, 'KEEP (test evidence)': 1, 'KEEP (test evidence; Fix plan rows need the rig)': 1, 'KEEP until a dated source shows the CRM does this; the keyed upsert keeps crm_rows=1 under retries': 1, 'KEEP-CORE (callers: guard/producers.py lines 63 and 68, the askdata extra in pyproject.toml, tests/demo_askdata/); archive only after those references move': 5, 'KEEP-CORE (out of take scope; no move)': 10, 'MERGE-INTO core Limits, only after the place that holds the dollar cap is named; keep until then': 2, 'MERGE-INTO mf-form AFTER THE VIDEO; the key must become source plus id (L2-FD-004: ids from two sources can collide and a request is dropped as a duplicate). The dead if-nodes UnknownNewA and UnknownNew are in mf-sub-crm-mail.json (lines 326 and 358, reviewer-read); both branches go to OutUnknown so they decide nothing: remove them in that file, a separate CHANGE after the video': 1, 'MERGE-INTO one register': 1, 'MERGE-INTO one rule file': 1, 'STOP (process waste, not a file)': 1, 'keep': 17}

REPORT.md claim (line 5): '7 keys, 7 Owner lines, 59 rows = 49 + 10 appendix'; ONE-PLACE-TABLE line 3: '49 rows are in the job blocks and 10 build-process rows are in the appendix'.
Extra: lines containing 'Owner:' anywhere = 8 (7 block lines + one in the how-to-read text at line 10).
```
