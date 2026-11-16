# Codebase-details reviewer (egm:egm-codebase-details), round 1 — condensed copy saved by core-hardening
Verdict: PARTLY SOUND, NOT CLEAN. Every cite openable in the source tree was real and said what the table claims (no wrong cite). Most take-side evidence (handover/demo*, flows, harness, fakes, CI tools) cannot be opened in either tree, so it is UNVERIFIED here.

## Could not open (UNVERIFIED)
Snapshot holds only handover/system-map/*; this repo has no handover/demo3, no tools/ folder, no tests/stage_mutants.py. Not verified: rows citing mf-*.json, harness.py, fakes.py, run_*.sh, RESULTS.md, REPORT.md; every cite into handover/demo and demo3 (L6-J-004,005,016-019,023,028,029,036,039,040,042-044,049,054,055,059); tools/scan_repo.py, tools/mutation_runner.py; pyproject "askdata extra"; n8n_start.sh:115. Long L6-FD-026/003/004/006 rows not opened. QUESTIONS, STATUS-BOARD, README, REPORT not read.

## Verified correct
limits.py:17; k1b/loop.py:41; store/protocol.py:104; guard/producers.py:36,63,68; tick.py:4,:123; executor.py:153; channel.py:75; many module line-1 cites; signer_aws.py:53; migrations 0001-0005; tests/test_k5_round9.py; demo cites pipeline.py:105,140,365, audit.py:17, ledger.py:3, evalset.py:129, validate.py:47, meter.py, pgsource.py:167, roles.sql:43,63, dependabot.yml:10, .coderabbit.yaml:16. Job-block counts 11+9+9+5+8+6+1=49, appendix 10. SWEEP counts: 322 FD rows; 18/218/86 consistent. DECISION line cites right.

## Findings (worst first)
C-1 Major. "Shared Postgres superuser" / "rig runs as superuser" (J-058, OTHER block, Fix plan row 6, Decisions D) rests on a credential NAME (mf-form.json:112), DECISION:14, and register.md:401 (an OS uid). None shows the database role is a superuser; DECISION:20 itself says unverified. Fix: say "one shared credential, privilege level unverified". J-058 verdict NOT-NEEDED with proposal CHANGE and state UNDECIDED is incoherent.
C-2 Major. Decisions B / row 5a: video recommendation "option 3 plus heartbeat" names no channel; if heartbeat uses the same SMTP credential (mf-mail-smtp) it repeats the shared-fate flaw; row 5a verification covers "n8n stopped" only, not "SMTP down".
C-3 Major. Decisions A / row 2 arithmetic inconsistent: "10 requests make at most 10 calls" contradicts the proof (1 new lead, 9 duplicates); "x 3 for retries" unsupported by DECISION:17; limit about 10-30x too high; "___" still blank; option 2 cost cell holds finding ids.
C-4 Nit. J-043 and J-025 both cite mf-recovery.json:124 for different quotes; J-043 cites :256 node-type name as evidence of a clear; J-025 "Valid node regex" quotes only the CASE line.
C-5 Nit. J-046 cites signer_aws.py:53 (off-topic); better llm/bedrock.py:49-51 (`total_max_attempts: 1`, "llm/retry.py decides").
C-6 Nit. CI cites J-022, J-050, J-033 do not match this checkout: ci.yml:94 stage_mutants and :228 do not exist (file is 144 lines); cron at line 15 not 16; timeout-minutes at 35 not 36; curl at 128/140 without --retry. Branch ci.yml may differ; re-check on that branch.
C-7 Nit. State columns contradict the Seed check (J-003, J-014 UNVERIFIED vs stage.journal CONSISTENT; J-026 OK; J-001 CONFLICT vs CONSISTENT; J-034 OWNER with state UNVERIFIED — an owner whose code is unseen is a plan, not a place; broken grammar in the COUNTER line).
C-8 Nit. L6-EX-06 cites "DECISION line 7" for a shape check (line 7 lists only table and writers); L6-EX-07 thin.
C-9 Nit. Row 7 verification "each old key is refused" does not fit stand-ins or n8n encryption keys; gitleaks question still unanswered; "about one agent-day" history rewrite is an estimate.
C-10 Nit. Claims check first row quotes saved pr3-body.md:5 as CONTRADICTED; live PR pages unchecked — status should say "saved copy contradicted, live state unchecked".
DECISION-one-store: claims plausible; line 17 "deliberately independent" lacks the UNVERIFIED caveat (row 22 plans it); "1.5 to 2 agent-days" is an estimate.

## Lead's review-1 asks
Made: L1c-FD-001 and L1c-FD-021 and L6-FD-004 lowered to Major; counts 322/315 with superseded numbers explained (recounted 322); scope honest; fix step for the owner's name (row 13).
Not made / partly: superuser claim (C-1); "line 7" cites (C-8); gitleaks (C-9); L4c-FD-001..003 unconfirmed locally; L6-FD-026 correction not checkable; J-001..J-059 take files not line-checked.
Recommendation: a laptop reader re-runs the take-file cites against the real branch; fix C-1..C-3 before the studio head decides A, B or D.
