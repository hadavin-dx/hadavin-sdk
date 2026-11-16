# R5-M2 (egm-codebase-details, sonnet): Major sample, SWEEP.md lines 201-355
Saved by the lead 2026-11-16 ~07:59 UTC. Condensed; every row kept. Scope: 69 Major rows in this range (lines 201-269; 270-279 hold only Nit rows; rows after 279 not opened); sample = every 2nd = 35 rows. Verdicts: 0 whole-row WRONG, 2 defective/partly wrong (L4-FD-021, L5a-FD-008), 1 UNVERIFIABLE (L6-FD-025), rest CONFIRMED. Severity: agree Major on 17, Nit on 17, plus L4-FD-021 meta; no Blocker.
| id | verdict | severity | evidence read (under handover/demo unless full path) | note |
|---|---|---|---|---|
| L4-FD-017 | CONFIRMED | AGREE | real-run/NOTES-start-prompt-v2.md:17-18 | "approval file not built" |
| L4-FD-021 | WRONG (citation) | Nit/meta | hang/RESULTS.md:1-10 | line 6 "NOT REPRODUCED"; no READ 1/SKIMMED 1521/NOT-READ 137 counts there; row records lane coverage, not a defect |
| L4c-FD-005 | CONFIRMED | AGREE | triage/SUMMARY-codeant4-sec.md:13; fixes/REVIEW-3.md:15 | dependency on codeant3-gitleaks stated at semgrep/REVIEW-3.md:7 (not cited) |
| L4c-FD-007 | CONFIRMED | AGREE | real-run/REVIEW-v5-fresh.md:9 | reviewer's differential test found risk low |
| L4c-FD-009 | CONFIRMED | Nit | triage/SUMMARY-codeant3-rt.md:1; SUMMARY-codeant5-sec.md:1 | superseded patch copies = leftovers |
| L4c-FD-011 | CONFIRMED | AGREE | fixes/REVIEW-1.md:7; REVIEW-3.md:18; triage/SUMMARY-codeant2-runtime.md:6; skips/SKIP-TABLE.md:9 | SKIP-TABLE:9 is a loose fit (Windows 252/29) |
| L4c-FD-013 | CONFIRMED | AGREE (borderline: desk retired) | sonar/NOTES-p2-v23.md:10; triage/SUMMARY-codeant3-rt.md:11; system-map/DECISION-one-store.md:14-15 | reaper stop guard not cited |
| L4c-FD-015 | CONFIRMED (real n8n run UNVERIFIABLE) | AGREE | triage/SUMMARY-codeant2-sec.md:6,:26 | "real n8n not run", "checked in node only" |
| L4c-FD-017 | CONFIRMED | AGREE | semgrep/SUMMARY-14b.md:8,:10; semgrep/REVIEW-3.md:8; semgrep/SUMMARY.md:3 | lead's run omitted --strict; lead-registry-run.txt not opened |
| L4c-FD-019 | CONFIRMED (partly) | Nit | real-run/REVIEW-v2-fresh.md:65; v3:20; v5:69 | "real outbound attempts with a made-up key" not on any cited line; hygiene slips |
| L4c-FD-021 | CONFIRMED | AGREE (weak) | sonar/REVIEW-p2v23-fresh.md:8 | fails 3 of 15 runs idle machine |
| L5a-FD-002 | CONFIRMED | AGREE | demos/ask-your-data/askdata/cli.py:87-109,197-278; evalcli.py:87; pipeline.py:3 | every ask path via cmd_ask, no ledger/audit/meter; PgSource not read |
| L5a-FD-004 | CONFIRMED | AGREE | askdata/meter.py:254,:211; src/hadavin_sdk/limits.py:17,:22; evalset.py:129 | "UNVERIFIED whether Limits can express the shared cap" honest |
| L5a-FD-006 | CONFIRMED (temp-folder part UNVERIFIABLE) | AGREE | data/goldcheck.py:3-5; evalset.py:45-53; evalcli.py:44-47; README.md:76-79 | loader fields differ from data; no gold.dev/test jsonl or lock.json |
| L5a-FD-008 | PARTLY WRONG | Nit | opscli.py:153-154; evalset.py:120,:130; meter.py:35; evalrun.py:36 | meter.py:35 is a unit constant (1_000_000), evalrun.py:36 an e-mail regex: not money/thresholds; opscli caps are real |
| L5a-FD-010 | CONFIRMED | AGREE | README.md:33-34; SECURITY.md:9 | "the owner's to accept" |
| L5a-FD-012 | CONFIRMED | Nit | .claude/rules/review-loop-speed-rules.md:18; faster-builds...:17,:22; whole-project-speed-planning.md:11 | five different limits; private rule text, not a take defect; no heavy_slot file |
| L5a-FD-014 | CONFIRMED | Nit | README.md:8; demos/README.md:3 | stale table |
| L5ac-FD-002 | CONFIRMED | AGREE | data/gold.jsonl:60; db/lumen_schema.sql:38; data/dataset_contract.json:162-165; goldcheck.py:132 | R = "flagged for manual review" vs "rush"/"fraud-review hold" |
| L5ac-FD-004 | CONFIRMED | AGREE | trust/verify_readonly.psql:56-67; data/goldcheck.py:80 | pins 4 views vs VIEWS list (7 not counted fully) |
| L5ac-FD-007 | CONFIRMED | AGREE (borderline Nit) | CHANGELOG.md:377,:338; .github/workflows/ci.yml:87-94 | CI runs only stage_mutants.py |
| L5ac-FD-010 | CONFIRMED | AGREE | data/gold.jsonl:60; goldcheck.py:208-210; grep second_author_checked true = 0 | gold.jsonl:1 not opened |
| L5ac-FD-013 | CONFIRMED | Nit | .claude/rules/long-jobs-run-detached.md:12; tools/mutation_runner.py:541,:30-33 | scripts/mutation_check.py does not exist: stale rule pointer |
| L5b-FD-002 | CONFIRMED | Nit | src/hadavin_sdk/store/migration_numbers.py:1-20; tools/mutation_runner.py:69 | unused dev modules in runtime package |
| L5b-FD-004 | CONFIRMED | Nit | src/hadavin_sdk/audit/chain.py:1; local_dir.py:1; k1b/audit_sink.py:1 | by design per the row |
| L5b-FD-007 | CONFIRMED (35 tracked files count not run) | Nit | tests/demo_askdata/attackrun.py:9; conftest.py:25-26 | no core src imports the demo; placement only |
| L6-FD-008 | CONFIRMED (n8nTrigger cite weak) | AGREE | demo3/kill/flows-go1/mf-recovery.json:26,:256; mf-sub-crm-mail.json:35-37 | :256 shows no alert backoff/start-clear; "3 x 3" plausible |
| L6-FD-010 | CONFIRMED | Nit (retired desk) | demo/REPORT.md:2838; sonar/NOTES-p2-v23.md:10 | report says no evidence it ever fired |
| L6-FD-012 | CONFIRMED (partly) | AGREE (weak) | demo3/REPORT.md:47-48; kill/make_results.py:29-32 | results.jsonl never called "the truth" at those lines; "20 of 126" not computed |
| L6-FD-014 | CONFIRMED | AGREE | same cites as L5a-FD-004 | duplicate row of L5a-FD-004 |
| L6-FD-016 | CONFIRMED | Nit (idle code) | src/hadavin_sdk/guard/producers.py:36,:57-58 | only tests import extract/add_dead_letter |
| L6-FD-019 | CONFIRMED | AGREE | demo/ORDERS.md:41; integration/INT-1.md:9; demo3/evidence/skipped-on-purpose.md:3; real-run/DRY-RUN-CHECKS.md:4,:40 | 124+22+38+8+34 = 226 not 224 |
| L6-FD-021 | CONFIRMED (part) | Nit | demo3/kill/run_b.sh:5; run_h.sh:5; .claude/rules/agent-and-shell-sprawl-incident-2026-11-04.md:5 | rule line 5 is about the register row; unbounded-loop rule is item 3; "eight queue scripts" not counted |
| L6-FD-025 | UNVERIFIABLE | AGREE (weak) | demo3/kill/fakes.py:103; mf-sub-crm-mail.json:230 | absence of a dated vendor source needs a search of every lane |
| L6-FD-028 | CONFIRMED | Nit | demo3/kill/flows-go1/mf_leads.sql:4-20 | no tenant/source column; row says one client, isolation N/A |
Not checked (reviewer): cited lines in other files (e.g. 35 tracked files in tests/demo_askdata); 70-row/40-item counts in gold.jsonl; exactly 7 VIEWS; views.sql/registry quotes of L5ac-FD-004; whether any test builds the missing eval gold files; PgSource kill-switch; the 34 unsampled Major rows; anything needing n8n/HubSpot/SMTP/take repo.
