# Lane L4

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
| path | bytes | status | note |
|---|---|---|---|
| handover/demo/coverage/PLAN.md | 26587 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/coverage/REVIEW-1.md | 11761 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/coverage/REVIEW-2.md | 10480 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/coverage/REVIEW-3.md | 11357 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/coverage/evidence-apply-check.txt | 23 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-coverage.xml | 260948 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-gitleaks.txt | 470 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-lint-checks.txt | 536 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-patch-stat.txt | 438 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-pytest-coverage.txt | 5579 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-apply-check.txt | 611 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-coverage-omit.txt | 1020 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-gitleaks.txt | 1278 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-hygiene-tests.txt | 256 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-lint-checks.txt | 1306 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-literal-scan.txt | 113 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-lock-regen.txt | 130 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-lockdrift-test.txt | 830 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-pip-install.txt | 4512 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r2-ruff-final.txt | 73 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-apply-orders.txt | 5112 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-base-diff.txt | 481 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-checks.txt | 1560 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-coverage.xml | 260948 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-full-run.txt | 1796 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-hygiene-tests.txt | 487 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-lint-checks.txt | 374 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-pip-A.txt | 1075 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-pip-B.txt | 2602 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-pip-C.txt | 1787 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-pip-D.txt | 1795 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-pip-E.txt | 1388 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-r3-xml-check.txt | 209 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-rerun-failed-test.txt | 325 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-uptime-after.txt | 61 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-uptime-before.txt | 61 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/evidence-xml-check.txt | 567 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/coverage/sonar-coverage-v1.patch | 21482 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/coverage/sonar-coverage-v2.patch | 21455 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/coverage/sonar-coverage.patch | 20743 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/fixes/PLAN-v2-pillow-draft.md | 5566 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/fixes/PLAN.md | 14714 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/fixes/REVIEW-1.md | 8967 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/fixes/REVIEW-2.md | 14100 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/fixes/REVIEW-3.md | 8326 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/fixes/docs-and-deps-v1-own-decoder.patch | 14228 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/fixes/docs-and-deps-v2-pillow-draft.patch | 51733 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/fixes/docs-and-deps-v2.patch | 40578 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/fixes/docs-and-deps-v3.patch | 36514 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/fixes/docs-and-deps-v4.patch | 39488 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/fixes/docs-and-deps.patch | 39488 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/fixes/evidence-1-pillow-fresh-venv.txt | 554 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-2-mutation-pixels-read.txt | 486 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-3-lint-hygiene.txt | 487 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-4-skips-node-on-off.txt | 3238 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-5-apply-check.txt | 50 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-6-hygiene-after-docs.txt | 244 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b1-fresh-venv-install.txt | 586 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b2-licences.txt | 633 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b2-mutation-tolerance.txt | 415 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b3-lint-hygiene.txt | 599 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b3-pillow-crosscheck.txt | 571 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b4-full-run.txt | 4388 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b5-lint.txt | 602 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b6-gitleaks.txt | 1013 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b7-final-tree-558d37f.txt | 411 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-b8-apply-check.txt | 147 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c1-css-mutation.txt | 18119 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c10-negatives.txt | 1678 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c11-pipeline-layer.txt | 701 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c12-both-scan-modes.txt | 1762 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c13-final-checks.txt | 984 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c2-browser-revision-node.txt | 1373 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c3-history.txt | 1436 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c4-n2-test-negative.txt | 866 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c5-installs.txt | 4645 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c6-skips.txt | 4037 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c7-full-run.txt | 4836 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c7a-earlier-full-run-558d37f.txt | 4994 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c8-apply-orders.txt | 2100 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-c9-merged-gitleaks.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-d1-measure-8files.txt | 6450 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-d3-mutations.txt | 9757 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-d4a-uv-regeneration.txt | 1305 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-d4c-licences.txt | 1362 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-d4c2-launch-message.txt | 831 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-d5-hygiene.txt | 962 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-d5-lint-gitleaks-sidebar.txt | 1085 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-d6-apply-matrix.txt | 4541 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/fixes/evidence-d7-collect-counts.txt | 1094 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/01-version.txt | 175 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/02-dir.txt | 224 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/02b-findings-detail.txt | 2843 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/03-git.txt | 281 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/04-hygiene.txt | 7478 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/05-neg-fixed.txt | 969 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/05-neg-orig.txt | 1168 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/06-regex-test.txt | 887 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/07-apply-check.txt | 23 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/08-fixed-dir-git.txt | 375 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/09-fixed-hygiene.txt | 100 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/REVIEW-1.md | 9543 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/gitleaks/REVIEW-2.md | 10133 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/gitleaks/SUMMARY.md | 5518 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/gitleaks/SUMMARY2.md | 7948 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/gitleaks/evidence-lead-provenance.txt | 1320 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/evidence-v2-1-v2only.txt | 336 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/evidence-v2-2-merged.txt | 4459 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/evidence-v2-3-exception-narrow.txt | 1150 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/evidence-v2-4-narrowness-matrix.txt | 3993 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/evidence-v2-5-controls-and-multiline.txt | 3209 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/evidence-v2-6-apply-orders.txt | 1709 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/evidence-v2-7-hygiene-extra.txt | 321 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/gitleaks/gitleaks-toml-fix-v2.patch | 888 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/gitleaks/gitleaks-toml-fix.patch | 1246 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/hang/PLAN-v2.md | 7075 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/hang/PLAN.md | 7977 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/hang/RESULTS.md | 9502 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/hang/REVIEW-1.md | 4862 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/hang/REVIEW-2.md | 4953 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/hang/batch-log.txt | 3347 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/dmesg-syn-mid.txt | 483 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-1-old-hangs.txt | 2409 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-2-new-passes.txt | 926 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-3-faulthandler.txt | 1345 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-4-lint.txt | 1366 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-5-gitleaks.txt | 417 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-6-touched.txt | 1221 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-6b-touched-final.txt | 27 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-7-apply.txt | 1397 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-8-portal3.txt | 2171 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h-9-prefix-old.txt | 1394 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h2-1-lint.txt | 537 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h2-2-env-two-stuck.txt | 286 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h2-2-stalled-stop.txt | 602 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h2-3-capture-sys.txt | 318 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h2-4-touched.txt | 1048 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h2-5-apply.txt | 533 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h2-6-gitleaks.txt | 454 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h2-6-hygiene-gitleaks.txt | 233 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/evidence-h2-7-failfast.txt | 425 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/hang-fix-v2.patch | 36805 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/hang/hang-fix.patch | 29732 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/hang/memory-end.txt | 938 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/memory-fullrun.txt | 195 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/memory-lead-session-1.txt | 3105 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/memory-start-b.txt | 4615 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/memory-start.txt | 8934 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-full-serial.txt | 3465 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-01.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-02.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-03.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-04.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-05.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-06.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-07.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-08.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-09.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-10.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-11.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-12.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-13.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-14.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-15.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-16.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-17.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-18.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-19.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-20.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-21.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-22.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-23.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-24.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-25.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-26.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-27.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-28.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-29.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-alone-30.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-together-1.txt | 1747 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-together-2.txt | 1728 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-together-3.txt | 1737 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-together-4.txt | 1714 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-load-together-5.txt | 1724 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-nl-alone-1.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-nl-alone-2.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-nl-alone-3.txt | 761 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-nl-together-1.txt | 1747 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/hang/run-nl-together-2.txt | 1737 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/INT-1.md | 5777 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/integration/INT-2b.md | 3687 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/integration/INT-3-2db3926.md | 3135 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/integration/evidence-int1-fullsuite.txt | 4307 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int1-gitleaks.txt | 619 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int1-hygiene.txt | 508 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int1-lint.txt | 1177 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int1-order.txt | 625 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int1-placement.txt | 3794 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2-1-venv.txt | 1770 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2-2-gitleaks.txt | 771 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2-2-hygiene-rs.txt | 597 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2-2-lint.txt | 8994 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2-3-collect.txt | 194 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2-3-run1-KILLED-at-8min-label-HUNG-was-WRONG.txt | 1385 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2-3-run2-fullsuite.txt | 129341 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2-3b-portal-api.txt | 176 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2-HANG-pyspy-dump.txt | 2797 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-A-0-collect.txt | 207 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-A-fullsuite.PARTIAL-REPLACED-0308.txt | 17313 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-A-fullsuite.txt | 324093 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-A-progress.txt | 1067 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-A-run.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-A-run.meta | 88 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-A-stall-dump1.txt | 2816 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-A-stall-dump2.txt | 1572 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-A-uptime-after.txt | 62 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-B-0-apply.txt | 1302 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-B-0-collect.txt | 30 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-B-failures-extract.txt | 957 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-B-fullsuite.txt | 360747 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-B-progress.txt | 708 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-B-run.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-B-run.meta | 89 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-B-uptime-after.txt | 62 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C-0-apply.txt | 1302 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C-fullsuite.txt | 169414 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C-progress.txt | 94 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C-run.meta | 119 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-0.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-0.txt | 11785 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-1.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-1.txt | 72235 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-2.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-2.txt | 30450 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-3.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-3.txt | 10971 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-4.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-4.txt | 32056 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-5.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-5.txt | 35643 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-6.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-6.txt | 44417 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-7.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-7.txt | 24387 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-8.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-8.txt | 55411 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-9.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-chunk-9.txt | 22380 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int2b-C2-driver.sh | 879 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-SINGLE-PROCESS-full.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-SINGLE-PROCESS-full.txt | 341648 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-0.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-0.txt | 11780 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-1.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-1.txt | 72230 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-2.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-2.txt | 33124 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-3.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-3.txt | 13597 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-4.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-4.txt | 31872 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-5.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-5.txt | 36619 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-6.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-6.txt | 44321 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-7.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-7.txt | 22419 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-8.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-8.txt | 51383 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-9.exit | 28 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-chunk-9.txt | 28629 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-driver.sh | 874 | SKIMMED | first 3 to 40 lines opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-1-ruff-check.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-1-ruff-check.txt | 79 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-10-nodeoff.txt | 412 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-2-ruff-format.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-2-ruff-format.txt | 97 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-3-mypy-linux.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-3-mypy-linux.txt | 113 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-4-mypy-win32.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-4-mypy-win32.txt | 113 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-5-bandit.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-5-bandit.txt | 1316 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-6-hygiene-gitleaks.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-6-hygiene-gitleaks.txt | 250 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-7-gitleaks-dir.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-7-gitleaks-dir.txt | 358 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-8-gitleaks-git.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-8-gitleaks-git.txt | 293 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-1.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-1.txt | 562 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-2.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-2.txt | 562 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-3.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-3.txt | 562 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-4.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-4.txt | 562 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-5.exit | 7 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-h3post-9-restart-test-5.txt | 562 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/integration/evidence-int3-2db3926-post-steps.sh | 1802 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/REVIEW-1.md | 12731 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/layout/REVIEW-2.md | 4235 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/layout/REVIEW-3.md | 4788 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/layout/SUMMARY.md | 7712 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/layout/SUMMARY2.md | 6204 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/layout/after-dark-1280-long.png | 189890 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after-dark-1280-normal.png | 202611 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after-dark-390-long.png | 37144 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after-dark-390-normal.png | 63464 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after-light-1280-long.png | 217359 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after-light-1280-normal.png | 229581 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after-light-390-long.png | 36669 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after-light-390-normal.png | 62064 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-confirm-dark-1280.png | 233529 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-confirm-dark-390.png | 68417 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-confirm-light-1280.png | 276494 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-confirm-light-390.png | 78106 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-data-dark-1280.png | 212824 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-data-dark-390.png | 84522 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-data-light-1280.png | 216638 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-data-light-390.png | 85369 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-demo-dark-1280.png | 238374 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-demo-dark-390.png | 90407 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-demo-light-1280.png | 240795 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-demo-light-390.png | 90106 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-drawer-later-dark-1280.png | 192194 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-drawer-later-dark-390.png | 24465 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-drawer-later-light-1280.png | 214006 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-drawer-later-light-390.png | 24193 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-leads-dark-1280.png | 231437 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-leads-dark-390.png | 90548 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-leads-light-1280.png | 234725 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-leads-light-390.png | 90628 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-log-dark-1280.png | 202320 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-log-dark-390.png | 90401 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-log-light-1280.png | 206079 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-log-light-390.png | 91063 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-log-long-dark-1280.png | 209711 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-log-long-dark-390.png | 90401 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-log-long-light-1280.png | 213836 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-log-long-light-390.png | 91032 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-needs-dark-1280.png | 285083 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-needs-dark-390.png | 89329 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-needs-info-dark-1280.png | 238592 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-needs-info-dark-390.png | 83889 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-needs-info-light-1280.png | 240695 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-needs-info-light-390.png | 83137 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-needs-light-1280.png | 288999 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-needs-light-390.png | 90065 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-overview-dark-1280.png | 337719 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-overview-dark-390.png | 100667 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-overview-light-1280.png | 328602 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-overview-light-390.png | 100929 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-toast-dark-1280.png | 211554 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-toast-dark-390.png | 61721 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-toast-light-1280.png | 207982 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/after1-toast-light-390.png | 64401 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-confirm-dialog-light-390.png | 117089 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-confirm-dialog-light-900.png | 195319 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-data-light-390.png | 117229 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-data-light-900.png | 189887 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-demo-light-390.png | 128122 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-demo-light-900.png | 194535 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-lead-panel-light-390.png | 57559 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-lead-panel-light-900.png | 144485 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-leads-light-390.png | 125769 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-leads-light-900.png | 196710 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-log-light-390.png | 123966 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-log-light-900.png | 182331 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-needs-light-390.png | 136929 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-needs-light-900.png | 226971 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-overview-light-390.png | 135455 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB-overview-light-900.png | 253805 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-confirm-dialog-light-390.png | 117096 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-confirm-dialog-light-900.png | 195326 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-data-light-390.png | 117229 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-data-light-900.png | 189876 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-demo-light-390.png | 128122 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-demo-light-900.png | 194532 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-lead-panel-light-390.png | 57515 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-lead-panel-light-900.png | 147615 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-leads-light-390.png | 125773 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-leads-light-900.png | 196725 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-log-light-390.png | 124530 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-log-light-900.png | 182877 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-needs-light-390.png | 136923 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-needs-light-900.png | 226969 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-overview-light-390.png | 135493 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/afterB2-overview-light-900.png | 253837 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-confirm-dark-1280.png | 219732 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-confirm-dark-390.png | 68139 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-confirm-light-1280.png | 262578 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-confirm-light-390.png | 82388 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-dark-1280-long.png | 130979 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-dark-1280-normal.png | 202480 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-dark-390-long.png | 6538 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-dark-390-normal.png | 63448 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-data-dark-1280.png | 212804 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-data-dark-390.png | 84522 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-data-light-1280.png | 216640 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-data-light-390.png | 85382 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-demo-dark-1280.png | 238420 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-demo-dark-390.png | 90410 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-demo-light-1280.png | 240792 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-demo-light-390.png | 90121 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-drawer-later-dark-1280.png | 115534 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-drawer-later-dark-390.png | 6538 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-drawer-later-light-1280.png | 136085 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-drawer-later-light-390.png | 6505 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-leads-dark-1280.png | 198067 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-leads-dark-390.png | 90557 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-leads-light-1280.png | 201954 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-leads-light-390.png | 90622 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-light-1280-long.png | 157493 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-light-1280-normal.png | 229577 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-light-390-long.png | 6505 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-light-390-normal.png | 62065 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-log-dark-1280.png | 202573 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-log-dark-390.png | 90401 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-log-light-1280.png | 206544 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-log-light-390.png | 91063 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-log-long-dark-1280.png | 209717 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-log-long-dark-390.png | 90401 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-log-long-light-1280.png | 213824 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-log-long-light-390.png | 91049 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-needs-dark-1280.png | 285082 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-needs-dark-390.png | 89332 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-needs-info-dark-1280.png | 223490 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-needs-info-dark-390.png | 84220 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-needs-info-light-1280.png | 227073 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-needs-info-light-390.png | 83376 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-needs-light-1280.png | 288992 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-needs-light-390.png | 90081 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-overview-dark-1280.png | 352188 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-overview-dark-390.png | 100794 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-overview-light-1280.png | 328742 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-overview-light-390.png | 100938 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-toast-dark-1280.png | 197459 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-toast-dark-390.png | 71748 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-toast-light-1280.png | 192327 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/before-toast-light-390.png | 72365 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-confirm-dialog-light-390.png | 94252 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-confirm-dialog-light-900.png | 195326 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-data-light-390.png | 85384 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-data-light-900.png | 189887 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-demo-light-390.png | 89765 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-demo-light-900.png | 194543 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-lead-panel-light-390.png | 57671 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-lead-panel-light-900.png | 147791 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-leads-light-390.png | 90428 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-leads-light-900.png | 197018 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-log-light-390.png | 91062 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-log-light-900.png | 182898 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-needs-light-390.png | 90089 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-needs-light-900.png | 226971 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-overview-light-390.png | 100556 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/beforeB-overview-light-900.png | 253831 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/dbgB-confirm-dialog-light-390.png | 117089 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/dbgB-data-light-390.png | 117237 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/dbgB-demo-light-390.png | 128119 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/dbgB-lead-panel-light-390.png | 57559 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/dbgB-leads-light-390.png | 125760 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/dbgB-log-light-390.png | 123972 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/dbgB-needs-light-390.png | 136932 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/dbgB-overview-light-390.png | 135462 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/drawer-long-name.patch | 3873 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/layout/drawer-long-name2-r2.patch | 15320 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/layout/drawer-long-name2.patch | 16060 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/layout/evidence-1-before-measure.txt | 2800 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-2-test-OLD-css.txt | 1658 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-3-test-NEW-css.txt | 238 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-4-after-measure.txt | 2780 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-5-normal-name-same-row.txt | 1080 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-6a-portal-files-OLD-css.txt | 1406 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-6b-portal-files-NEW-css.txt | 1444 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-7-mutation-fix-reverted.txt | 1675 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-8-lint-hygiene.txt | 394 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-9-apply-check.txt | 2231 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b-apply-matrix.txt | 5035 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b-pages-pg-base.txt | 7170 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b-pages-pg-both.txt | 6372 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b-pages-pg-p1.txt | 7170 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b-sweep-sw-base.txt | 10256 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b-sweep-sw-both.txt | 4164 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b-sweep-sw-p1.txt | 6470 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b1-new-tests-on-HEAD-css.txt | 4481 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b2-patch1-tests-on-P1-css.txt | 293 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b3-phone-tests-on-P1-css-only.txt | 2447 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b4-all-new-tests-on-P1+P2-css.txt | 330 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b5-phone-tests-on-P2-css-only.txt | 261 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-b6-portal-files-P1+P2.txt | 328 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-c1-new-tests-on-HEAD-css.txt | 8620 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-c2-phone-tests-on-afterB2-stale-css.txt | 6057 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-c3-half-pixel-tests-on-old-gap-css.txt | 1124 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-c4-new-tests-on-final-css.txt | 318 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-c5-final-screenshot-measures.txt | 1393 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-c6-portal-full-regression.txt | 59723 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-c7-apply-matrix.txt | 6472 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-c8-lint-mypy-gitleaks.txt | 1257 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/evidence-c9-desktop-1100-1280-computed-compare.txt | 8339 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/final-leads-dark-390.png | 126742 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-leads-dark-700.png | 169154 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-leads-light-390.png | 127790 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-leads-light-700.png | 171042 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-needs-dark-390.png | 136134 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-needs-dark-700.png | 197754 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-needs-light-390.png | 136526 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-needs-light-700.png | 199321 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-overview-dark-390.png | 134703 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-overview-dark-700.png | 180608 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-overview-light-390.png | 134148 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/final-overview-light-700.png | 181762 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/lt-base-later-only-dark-1280.png | 187084 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/lt-base-later-only-dark-390.png | 62199 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/lt-base-later-only-light-1280.png | 207823 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/lt-base-later-only-light-390.png | 60903 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/lt-both-later-only-dark-1280.png | 193490 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/lt-both-later-only-dark-390.png | 61877 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/lt-both-later-only-light-1280.png | 217590 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/lt-both-later-only-light-390.png | 60600 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/mobile-cascade-r2.patch | 8233 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/layout/mobile-cascade.patch | 18262 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/layout/pages-pg-base.json | 47042 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/pages-pg-both.json | 13822 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/pages-pg-p1.json | 47042 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/pg-base-confirm-dialog-light-390.png | 94252 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-confirm-dialog-light-900.png | 195323 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-data-light-390.png | 85383 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-data-light-900.png | 189883 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-demo-light-390.png | 89765 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-demo-light-900.png | 194536 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-lead-panel-light-390.png | 57539 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-lead-panel-light-900.png | 147651 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-leads-light-390.png | 90411 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-leads-light-900.png | 197019 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-log-light-390.png | 91069 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-log-light-900.png | 182679 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-needs-light-390.png | 90075 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-needs-light-900.png | 226970 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-overview-light-390.png | 100524 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-base-overview-light-900.png | 253880 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-confirm-dialog-light-390.png | 111490 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-confirm-dialog-light-900.png | 195326 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-data-light-390.png | 117229 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-data-light-900.png | 189884 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-demo-light-390.png | 128124 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-demo-light-900.png | 194543 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-lead-panel-light-390.png | 57475 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-lead-panel-light-900.png | 147627 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-leads-light-390.png | 127788 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-leads-light-900.png | 197015 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-log-light-390.png | 125071 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-log-light-900.png | 183537 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-needs-light-390.png | 133662 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-needs-light-900.png | 226971 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-overview-light-390.png | 134147 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-both-overview-light-900.png | 253863 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-confirm-dialog-light-390.png | 94252 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-confirm-dialog-light-900.png | 195319 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-data-light-390.png | 85381 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-data-light-900.png | 189884 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-demo-light-390.png | 89768 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-demo-light-900.png | 194535 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-lead-panel-light-390.png | 57692 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-lead-panel-light-900.png | 144626 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-leads-light-390.png | 90413 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-leads-light-900.png | 196710 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-log-light-390.png | 91069 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-log-light-900.png | 183146 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-needs-light-390.png | 90075 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-needs-light-900.png | 226971 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-overview-light-390.png | 100524 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/pg-p1-overview-light-900.png | 253822 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/probe-after.json | 2653 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/probe-before.json | 2671 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/sw-base-confirm-dark-1280.png | 219747 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-confirm-dark-390.png | 68148 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-confirm-light-1280.png | 262578 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-confirm-light-390.png | 82386 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-data-dark-1280.png | 212830 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-data-dark-390.png | 84519 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-data-light-1280.png | 216635 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-data-light-390.png | 85353 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-demo-dark-1280.png | 238376 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-demo-dark-390.png | 90407 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-demo-light-1280.png | 240806 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-demo-light-390.png | 90104 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-drawer-later-dark-1280.png | 115534 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-drawer-later-dark-390.png | 6538 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-drawer-later-light-1280.png | 136085 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-drawer-later-light-390.png | 6505 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-later-only-dark-1280.png | 115534 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-later-only-dark-390.png | 6538 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-later-only-light-1280.png | 136085 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-later-only-light-390.png | 6505 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-leads-dark-1280.png | 198063 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-leads-dark-390.png | 90548 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-leads-light-1280.png | 201924 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-leads-light-390.png | 90636 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-log-dark-1280.png | 201862 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-log-dark-390.png | 90410 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-log-light-1280.png | 205491 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-log-light-390.png | 91049 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-log-long-dark-1280.png | 209717 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-log-long-dark-390.png | 90401 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-log-long-light-1280.png | 213833 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-log-long-light-390.png | 91046 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-needs-dark-1280.png | 285079 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-needs-dark-390.png | 89334 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-needs-info-dark-1280.png | 223481 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-needs-info-dark-390.png | 84225 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-needs-info-light-1280.png | 226997 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-needs-info-light-390.png | 83390 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-needs-light-1280.png | 288999 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-needs-light-390.png | 90068 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-overview-dark-1280.png | 337901 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-overview-dark-390.png | 100678 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-overview-light-1280.png | 328810 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-overview-light-390.png | 100929 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-toast-dark-1280.png | 197560 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-toast-dark-390.png | 71738 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-toast-light-1280.png | 192266 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-base-toast-light-390.png | 72350 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-confirm-dark-1280.png | 272257 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-confirm-dark-390.png | 76368 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-confirm-light-1280.png | 276521 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-confirm-light-390.png | 87955 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-data-dark-1280.png | 212836 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-data-dark-390.png | 116496 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-data-light-1280.png | 216639 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-data-light-390.png | 117220 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-demo-dark-1280.png | 238387 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-demo-dark-390.png | 129973 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-demo-light-1280.png | 240795 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-demo-light-390.png | 128550 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-drawer-later-dark-1280.png | 175874 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-drawer-later-dark-390.png | 26036 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-drawer-later-light-1280.png | 199610 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-drawer-later-light-390.png | 26103 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-later-only-dark-1280.png | 179025 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-later-only-dark-390.png | 33530 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-later-only-light-1280.png | 203619 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-later-only-light-390.png | 33407 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-leads-dark-1280.png | 231966 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-leads-dark-390.png | 124648 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-leads-light-1280.png | 234497 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-leads-light-390.png | 125473 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-log-dark-1280.png | 201972 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-log-dark-390.png | 125388 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-log-light-1280.png | 205840 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-log-light-390.png | 127742 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-log-long-dark-1280.png | 209726 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-log-long-dark-390.png | 125959 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-log-long-light-1280.png | 213836 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-log-long-light-390.png | 127230 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-needs-dark-1280.png | 285079 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-needs-dark-390.png | 134685 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-needs-info-dark-1280.png | 238569 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-needs-info-dark-390.png | 112390 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-needs-info-light-1280.png | 240706 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-needs-info-light-390.png | 113086 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-needs-light-1280.png | 288998 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-needs-light-390.png | 135321 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-overview-dark-1280.png | 337946 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-overview-dark-390.png | 135009 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-overview-light-1280.png | 328867 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-overview-light-390.png | 134481 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-toast-dark-1280.png | 211611 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-toast-dark-390.png | 64894 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-toast-light-1280.png | 207931 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-both-toast-light-390.png | 66599 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-confirm-dark-1280.png | 233522 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-confirm-dark-390.png | 68411 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-confirm-light-1280.png | 276434 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-confirm-light-390.png | 78059 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-data-dark-1280.png | 212827 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-data-dark-390.png | 84522 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-data-light-1280.png | 216643 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-data-light-390.png | 85369 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-demo-dark-1280.png | 238402 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-demo-dark-390.png | 90366 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-demo-light-1280.png | 240791 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-demo-light-390.png | 90105 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-drawer-later-dark-1280.png | 192133 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-drawer-later-dark-390.png | 24465 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-drawer-later-light-1280.png | 214155 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-drawer-later-light-390.png | 24193 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-later-only-dark-1280.png | 193457 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-later-only-dark-390.png | 61877 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-later-only-light-1280.png | 217541 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-later-only-light-390.png | 60600 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-leads-dark-1280.png | 231951 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-leads-dark-390.png | 90554 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-leads-light-1280.png | 234888 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-leads-light-390.png | 90622 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-log-dark-1280.png | 202759 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-log-dark-390.png | 90401 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-log-light-1280.png | 206426 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-log-light-390.png | 91052 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-log-long-dark-1280.png | 209710 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-log-long-dark-390.png | 90410 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-log-long-light-1280.png | 213824 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-log-long-light-390.png | 91049 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-needs-dark-1280.png | 285077 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-needs-dark-390.png | 89333 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-needs-info-dark-1280.png | 238583 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-needs-info-dark-390.png | 83894 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-needs-info-light-1280.png | 240695 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-needs-info-light-390.png | 83136 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-needs-light-1280.png | 288997 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-needs-light-390.png | 90068 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-overview-dark-1280.png | 337808 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-overview-dark-390.png | 100673 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-overview-light-1280.png | 328718 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-overview-light-390.png | 100929 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-toast-dark-1280.png | 211595 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-toast-dark-390.png | 61821 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-toast-light-1280.png | 207813 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sw-p1-toast-light-390.png | 64401 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/sweep-sw-base.json | 62662 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/sweep-sw-both.json | 11344 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/sweep-sw-p1.json | 44254 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/layout/tall-leads-390.png | 136528 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/tall-needs-390.png | 185610 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/tall-overview-390.png | 198456 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/tryB-leads-light-390.png | 127789 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/tryB-needs-light-390.png | 133659 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/layout/tryB-overview-light-390.png | 134151 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/outsider/00-clone.txt | 178 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/01-setup.txt | 5325 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/02-unit.txt | 4937 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/03-bandit.txt | 1965 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/03-mypy-linux.txt | 83 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/03-mypy-win32.txt | 83 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/03-ruff-check.txt | 49 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/03-ruff-format.txt | 67 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/03-schema.txt | 6527 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/04-hygiene.txt | 387 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/05-playwright-install.txt | 898 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/06-full-with-playwright.txt | 1109 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/07-hung-file-rerun.txt | 4002 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/08-full-with-playwright-rerun.txt | 254712 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/09-pillow-rerun.txt | 128 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider/SUMMARY.md | 6536 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/outsider2/01-diffnames.txt | 5506 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/01-diffstat.txt | 12522 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/02-docker-ps.txt | 194 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/03-uv-venv.txt | 315 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/04-uv-install.txt | 588 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/05-ruff-check.txt | 52 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/06-ruff-format.txt | 70 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/07-mypy-linux.txt | 86 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/08-mypy-win32.txt | 86 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/09-bandit.txt | 1968 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/10-check-schema.txt | 6530 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/11-hygiene.txt | 342 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/12-pytest-full.txt | 2447 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/13-collect.txt | 211378 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/14-reaper-slow-v.txt | 6821 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/15-pytest-full-v.txt | 252411 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/16-playwright-install.txt | 85 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/17-pytest-browser.txt | 25366 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/18-pillow-install.txt | 45 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/19-pillow-rerun.txt | 621 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/outsider2/SUMMARY.md | 5639 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/real-run/DRY-RUN-CHECKS.md | 17415 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/real-run/FIXES.md | 26576 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/real-run/NOTES-desk-address-required.md | 7660 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/NOTES-start-prompt-v2.md | 14564 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/real-run/NOTES-start-prompt.md | 9676 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/REVIEW-core-hunks-v6-fresh.md | 15022 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/REVIEW-real-run-v6-fresh.md | 16342 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/REVIEW-start-prompt-fresh.md | 19359 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/REVIEW-v2-fresh.md | 7144 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/REVIEW-v3-fresh.md | 9964 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/REVIEW-v4-fresh-copy.md | 10885 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/REVIEW-v4-fresh.md | 10885 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/REVIEW-v5-fresh.md | 18354 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/real-run/desk-address-required-after-v2.patch | 33399 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/desk-address-required.patch | 35514 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/evidence-q4-dsk.txt | 2404 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4-hsp.txt | 19712 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4-rlc.txt | 15832 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4-rrc.txt | 61626 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4-rst.txt | 10044 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-apply-check-v2.txt | 1338 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-apply-check.txt | 134 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-gitleaks-v2.txt | 104 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-gitleaks.txt | 356 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-lint-mypy-bandit.txt | 184 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-results-v2-quick.tsv | 16802 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-results.tsv | 18029 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-run-dry-checks-v2-quick.log | 7405 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-run-dry-checks.log | 8029 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4b-tests-on-old-code.txt | 24484 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4c-apply-check-v3.txt | 14838 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4c-fail-before-and-mutants.txt | 6568 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4c-gitleaks-v3.txt | 470 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4c-lint-mypy-bandit.txt | 388 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4c-results-v3-quick.tsv | 16802 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4c-run-dry-checks-v3-quick.log | 7403 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4c-tests-v3.txt | 523 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-apply-matrix.txt | 5071 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-apply-v4-alone.txt | 56 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-fail-before.txt | 2515 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-gitleaks-v4.txt | 246 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-lint-mypy-bandit.txt | 965 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-mutants.txt | 1237 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-on-2db3926.txt | 277 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-tests-v4-part1.txt | 191 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-tests-v4-part2.txt | 352 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4d-tests-v4-part3.txt | 110 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4e-apply-matrix.txt | 1057 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4e-fail-before.txt | 4060 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4e-gitleaks.txt | 248 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4e-lint-mypy-bandit.txt | 460 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4e-mutants-scan.txt | 946 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4e-mutants.txt | 2029 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4e-tests.txt | 961 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4f-apply-matrix.txt | 4316 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4f-fail-before-reasons.txt | 5274 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4f-fail-before.txt | 4616 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4f-harness.txt | 2746 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4f-hygiene-gitleaks.txt | 191 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4f-lint-mypy-bandit.txt | 1449 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4f-mutants.txt | 1383 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4f-tests-after.txt | 1148 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-apply-matrix-final.txt | 508 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-apply-matrix-p2.txt | 1329 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-apply-matrix.txt | 443 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-fail-before-v2.txt | 7129 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-harness.txt | 3562 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-hygiene-gitleaks.txt | 156 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-lint-mypy-bandit.txt | 671 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-merged-with-v4-tests.txt | 592 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-mutants-v2.txt | 1492 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-on-2db3926.txt | 380 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-p2-fail-before.txt | 1520 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-p2-hygiene-gitleaks.txt | 352 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-p2-lint-mypy-bandit.txt | 317 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-p2-mutants.txt | 967 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-p2-tests-combined-v2-p2.txt | 1152 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-tests-affected.txt | 912 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-v4-merge-conflicts.txt | 701 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/evidence-q4g-v4-v2-p2-tests.txt | 260 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/lo_up-q4g.py | 310 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/make_synthetic_config-q4f.py | 2574 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/make_synthetic_config.py | 2309 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/probe_stub.py | 2487 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/pty_ans-q4g.py | 669 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/real-run-fixes-v2.patch | 46408 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/real-run-fixes-v3.patch | 58738 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/real-run-fixes-v4-after-sonar-p3.patch | 81975 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/real-run-fixes-v4.patch | 81851 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/real-run-fixes-v5-after-sonar-p3.patch | 113048 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/real-run-fixes-v5.patch | 110920 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/real-run-fixes.patch | 39483 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/results.tsv | 35404 | SKIMMED | first 3 to 40 lines opened |
| handover/demo/real-run/run-dry-checks.sh | 25267 | SKIMMED | first 3 to 40 lines opened |
| handover/demo/real-run/sitecustomize-q4g.py | 1383 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/real-run/start-prompt-hardening-v1-to-v2.diff | 75315 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/start-prompt-hardening-v2-on-top-of-v4.patch | 98520 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/start-prompt-hardening-v2.patch | 88857 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/real-run/start-prompt-hardening.patch | 47132 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/scans/SCAN-TABLE.md | 3681 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/scans/evidence-q6-HEAD.txt | 515 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/evidence-q6-branches-end.txt | 243 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/evidence-q6-branches-start.txt | 905 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/evidence-q6-cfg-review-tools.txt | 666 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/evidence-q6-cfg-sonar.txt | 673 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/evidence-q6-initial-code.txt | 8599 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/evidence-q6-main.txt | 668 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/evidence-q6-pr-1-code.txt | 1008 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/evidence-q6-pr-2-demo-folder.txt | 1015 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/evidence-q6-pr-3-tests.txt | 1167 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/scans/scan-heads.sh | 3952 | SKIMMED | first 3 to 40 lines opened |
| handover/demo/scans/scan-rows.tsv | 954 | SKIMMED | first 3 to 40 lines opened |
| handover/demo/semgrep/NOTES-semgrep-v5.md | 7064 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/REVIEW-1.md | 18832 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/REVIEW-2.md | 4518 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/REVIEW-3.md | 4077 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/REVIEW-4.md | 4316 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/REVIEW-5-delta.md | 3131 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/REVIEW-6-v5-fresh.md | 9531 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/SUMMARY-14b.md | 3327 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/SUMMARY-14c.md | 2501 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/SUMMARY.md | 5633 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/semgrep/evidence-sg-1-install.txt | 445 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-10-full-pytest.txt | 3090 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-11-apply-matrix.txt | 1166 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-12-with-codeant2-gitleaks.txt | 514 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-13-nosem-short-form-real-semgrep.txt | 4949 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-13b-test-old-vs-new-nosem.txt | 2039 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-14-gitleaks-allowance-tests-and-mutants.txt | 1848 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-15-standalone-gates.txt | 707 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-16-merged-tree-gates.txt | 825 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-17-gates.txt | 2624 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-17-nosem-tab-unicode.txt | 5472 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-17-uv-lock-identical.txt | 900 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-18-gates-on-head.txt | 568 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-19-gates-on-2db3926.txt | 954 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-19-v2-gates.txt | 714 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-2-repro-gitleaks-dir.txt | 739 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-2-repro-gitleaks-git.txt | 436 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-2-repro-hygiene.txt | 1087 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-20-v3-gates.txt | 2664 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-21-unparsable-files.txt | 6355 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-22-real-folders-strict-2db3926.txt | 1923 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-22b-s3-real-folders-strict.txt | 1366 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-3-registry.txt | 1081 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-4-local-rule-nosemgrep-forms.txt | 753 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-5-test-old-vs-new.txt | 1319 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-6-exit-codes-local.txt | 952 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-7-fixed-gitleaks-dir.txt | 323 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-7-fixed-gitleaks-git.txt | 255 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-7-fixed-hygiene.txt | 295 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-8-negative-gitleaks.txt | 2253 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-8b-negative-hygiene-nested.txt | 197 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg-9-lint-steps.txt | 679 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg5-1-lint-mypy-bandit.txt | 709 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg5-2-semgrep-tests-hygiene-gitleaks.txt | 1800 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg5-3-p1-tripwire-old-vs-new.txt | 1009 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg5-4-combined-tree-gates.txt | 1439 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg5-5-exit-codes-old-vs-new-stub.txt | 2308 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg5-6-lock-and-files.txt | 144 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/evidence-sg5-7-apply-matrix.txt | 421 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/lead-registry-run.txt | 864 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v8/REVIEW-semgrep-v8-fresh.md | 12029 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/main-61ded9e-v8/evidence-1-gates.txt | 445 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v8/evidence-10-committed-gitleaks-and-apply.txt | 1083 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v8/evidence-10b.txt | 433 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v8/evidence-11-syntax-exit3.txt | 2131 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v8/evidence-2-tests.txt | 572 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v8/evidence-4-otel-and-nodemo.txt | 1961 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v8/evidence-6-workflow-mutants.txt | 3019 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v8/semgrep-on-main-61ded9e-v8.patch | 136419 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/main-61ded9e-v8/semgrep-pr-body-v8.md | 27169 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/main-61ded9e-v8/semgrep-pr-claims-v8.md | 22689 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/main-61ded9e-v9/evidence-1-gates-and-tests.txt | 725 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v9/evidence-10-committed-gitleaks-apply.txt | 442 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v9/evidence-4-nodemo.txt | 290 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v9/evidence-6-workflow-mutants.txt | 2188 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v9/mutate.py | 1791 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e-v9/semgrep-on-main-61ded9e-v9.patch | 138395 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/main-61ded9e-v9/semgrep-pr-body-v9.md | 28260 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/main-61ded9e-v9/semgrep-pr-claims-v9.md | 23531 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/semgrep/main-61ded9e/REVIEW-semgrep-v7-fresh.md | 9564 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/main-61ded9e/evidence-1-gates.txt | 1393 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/evidence-10-committed-gitleaks.txt | 950 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/evidence-2-tests-with-demo.txt | 699 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/evidence-3-extra-tests.txt | 500 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/evidence-4-nodemo.txt | 572 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/evidence-5-claim-measurements.txt | 5871 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/evidence-6-workflow-mutants.txt | 476 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/evidence-7-standin-scan-step.txt | 2399 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/evidence-8-docsfix-gates.txt | 401 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/evidence-9-real-semgrep-main-folders.txt | 775 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/semgrep/main-61ded9e/semgrep-on-main-61ded9e-docsfix.patch | 124658 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/main-61ded9e/semgrep-on-main-61ded9e.patch | 124316 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/main-61ded9e/semgrep-pr-body-v7.md | 22066 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/main-61ded9e/semgrep-pr-claims-v7.md | 19116 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/semgrep/semgrep-on-2db3926-v2.patch | 123335 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-on-2db3926-v3.patch | 123128 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-on-2db3926-v4.patch | 123927 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-on-2db3926.patch | 122066 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-on-db54e13-v5.1.patch | 124316 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-on-db54e13-v5.patch | 124188 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-on-head.patch | 120641 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-on-v4-r3.patch | 117792 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-on-v4.patch | 120649 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-rebased-r2.patch | 106251 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-rebased-r3.patch | 117145 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/semgrep/semgrep-rebased.patch | 120828 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/CRLF-EMULATION.md | 4276 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/CRLF-GUARD-NOTES.md | 2290 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/CRLF-GUARD-V3-NOTES.md | 965 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/CRLF-GUARD-V4-NOTES.md | 1464 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/CRLF-GUARD-V5-NOTES.md | 3823 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/CRLF-GUARD-V6-NOTES.md | 13154 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/CRLF-GUARD-V7-NOTES.md | 12920 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/skips/NEVER-RAN.md | 15630 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/skips/REVIEW-crlf-sonaryaml-v3-fresh.md | 9245 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/REVIEW-crlf-v4-yaml-delta-fresh.md | 11756 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/REVIEW-crlf-v5-yaml-trimmed-fresh.md | 11405 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/REVIEW-crlf-v6-fresh.md | 15051 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/REVIEW-crlf-v7-fresh.md | 13890 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/SKIP-TABLE.md | 18255 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/skips/crlf-guard-min-reviewer.patch | 10849 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard-v2.patch | 9118 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard-v3.patch | 12573 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard-v4-autocrlf-fix.patch | 19230 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard-v4.patch | 19077 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard-v5.patch | 21032 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard-v6.patch | 12615 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard-v7-keepgit.patch | 15916 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard-v7.1.patch | 16194 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard-v7.patch | 16080 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/crlf-guard.patch | 8722 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/skips/evidence-b10-1-hygiene-autocrlf.txt | 1150 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b10-2-gates-stack.txt | 7799 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b10-3-apply-matrix.txt | 1106 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b10-4-real-clone-autocrlf.txt | 1564 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b10-5-mutants-with-gitleaks.txt | 13802 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b10-6-mutants-without-gitleaks-and-autocrlf.txt | 13330 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b10-8-mutant-table.md | 5075 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/evidence-b13-1-verify.txt | 810 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-1b-real-clone-cures.txt | 2379 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-1c-no-gitleaks.txt | 762 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-2-fake-gitleaks-rc.txt | 837 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-3-scope.txt | 2147 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-4-mutant-table.md | 7974 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/evidence-b13-4-mutants-v6.txt | 6672 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-4b-min-patch-before.txt | 612 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-5-apply-matrix.txt | 5099 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-6-reusable-after.txt | 289 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-6-reusable-before.txt | 1939 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-6-reusable-mutants.txt | 603 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-7-gates-stack.txt | 419 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b13-8-stack-tests.txt | 1855 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b15-1-real-clone-cures.txt | 3892 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b15-2-hygiene-autocrlf.txt | 2692 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b15-3-gates.txt | 996 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b15-4-harness-mut15.py.txt | 13276 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b15-4-mutant-table.md | 10829 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/skips/evidence-b15-4-mutants-raw.txt | 13068 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b15-5-apply-matrix.txt | 4085 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b15-6-stack-gates-and-tests.txt | 1821 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b3-1-gates.txt | 462 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b3-2-mutants.txt | 2952 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b3-3-apply-matrix.txt | 1296 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b3-4-real-gitleaks-and-combined.txt | 1304 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b7-1-crlf-v4-mutants.txt | 8910 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b7-3-gates.txt | 1358 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b7-4-apply-matrix.txt | 621 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-b7-5-cure-measure.txt | 536 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-1-pass-lf.txt | 100 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-10-apply-fresh.txt | 291 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-2-fail-crlf-new.txt | 2562 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-3-old-message-crlf.txt | 457 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-4-gates.txt | 374 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-5-clean-apply.txt | 868 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-6-combined-semgrep.txt | 100 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-7-cure-measure.txt | 314 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-8-gates-v2.txt | 235 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-c1-9-fail-crlf-v2.txt | 581 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-crlf-1-eol.A.txt | 15491 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-crlf-1-eol.B.txt | 15424 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-crlf-2-bytes.txt | 506 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-crlf-3-gitleaks-dir.txt | 382 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-crlf-4-test_gitleaks_exceptions.txt | 107 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-crlf-5-test_hygiene.txt | 7820 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-crlf-6-test_codeant_hygiene.txt | 105 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-crlf-7-gitleaks-A-B.txt | 124 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-q5-ci-emulation-noplaywright-nogitleaks.txt | 2086 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-q5-collect-per-file.txt | 2685 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-q5-emulation-attempt1-INVALID-importerror-stub.txt | 469184 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-q5-h3-linux-skips.txt | 1215 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-q5-inventory-grep.txt | 8007 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/skips/evidence-q5-nodeoff-subset.txt | 1853 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/BRIEF-COMMON.txt | 2013 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/NOTES-flaky413.md | 5268 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/sonar/NOTES-nodemo-ci-v4.md | 13013 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-nodemo-ci-v5.md | 584 | READ | whole file (584 bytes) |
| handover/demo/sonar/NOTES-nodemo-v2.md | 6891 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-nodemo-v3.md | 12176 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-nodemo-v4.md | 6490 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-nodemo.md | 5280 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p1-quickwins-v2.md | 7828 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p1-quickwins-v3.md | 9616 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p1-quickwins-v31.md | 10017 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p1-quickwins-v32.md | 10951 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p1-quickwins-v321.md | 9192 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p1-quickwins.md | 5310 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p2-feed-constants.md | 2110 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p2-optional-gaps.md | 5751 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p2-v2.md | 11525 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p2-v21.md | 6023 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p2-v22.md | 3488 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p2-v23.md | 4017 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p2.md | 7961 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p3-final-v2.md | 8245 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p3-final.md | 13136 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p3-path-helper-v2.md | 10668 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p3-path-helper-v3.md | 8694 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p3-path-helper.md | 6644 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/NOTES-p3-probes.md | 3218 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/PROBE-AB-NOTE.md | 5955 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/PROBE-AB-V2-NOTE.md | 13864 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/PROBE-AB-V3-NOTE.md | 22433 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/PROBE-V3-MAPPING.md | 6068 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/sonar/REVIEW-flaky413-fresh.md | 6596 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-nodemo-ci-v4-fresh4.md | 17636 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-nodemo-fresh.md | 9285 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-nodemo-optional-v4-partial.md | 5340 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-nodemo2-fresh.md | 10890 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-nodemo3-fresh.md | 11925 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p1-fresh.md | 9397 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p1v2-fresh.md | 9564 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p1v3-fresh.md | 11838 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p1v31-fresh.md | 9025 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p1v32-fresh.md | 7317 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p1v321-fresh.md | 7239 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p2-fresh.md | 18947 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p2-optional-gaps-fresh.md | 8676 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p2-optional-pair-fresh.md | 7420 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p2v2-fresh.md | 10698 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p2v21-fresh.md | 9820 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p2v22-fresh.md | 6471 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p2v23-fresh.md | 8667 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p3-fresh.md | 16445 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p3-minors-risky-fresh.md | 17487 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p3-v21-fresh.md | 13158 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p3final-fresh.md | 10620 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-p3v3-fresh.md | 14956 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-probe-p3v2-fresh.md | 16924 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-probe2-fresh.md | 13836 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/REVIEW-probe3-fresh.md | 8596 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/sonar/evidence-P3-after.txt | 134 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-P3-fails-before.txt | 724 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-P3-lint.txt | 438 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-flaky413-1-before-30runs.txt | 2642 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-flaky413-2-deterministic-reproducer.txt | 1618 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-flaky413-3-after-100-idle-and-load.txt | 255 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-flaky413-4-sibling-sweep.txt | 2126 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-flaky413-5-mutants.txt | 709 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-flaky413-6-gates-and-apply.txt | 1293 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo-1-before.txt | 1663 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo-2-apply-check.txt | 325 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo-3-demo-present-after.txt | 1290 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo-4-mutants.txt | 887 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo-5-gates.txt | 494 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo-6-chunked-before.txt | 2327 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo-7-chunked-after-A.txt | 2787 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo-7-chunked-after-B.txt | 3036 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo-8-stack-hygiene-p2-literals-full.txt | 8605 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo2-1-narrow-guard.txt | 2832 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo2-3-ruff-isort.txt | 625 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo2-4-optional-hygiene.txt | 2002 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo2-5-ci-job.txt | 3862 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo2-6-apply-matrix.txt | 2272 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo2-7-final-stack-nodemo-chunked.txt | 3003 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-1-guard-mutants.txt | 1577 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-2-optional-mutants.txt | 1298 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-3-demo-present-final-stack.txt | 346 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-4-final-stack-nodemo-chunked.txt | 121782 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-5-ci-gate-unit.txt | 2717 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-6-ci-job-mutants.txt | 3092 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-7-gates-and-apply.txt | 1753 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-8-baselines-optional-and-guard.txt | 1742 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-drivers/ci_mut.py | 3901 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-drivers/gate_unit.py | 3457 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-drivers/mut.py | 3575 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-drivers/run_step.py | 819 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo3-drivers/shim-python.sh | 822 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo4-1-apply-matrix.txt | 767 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo4-2-baselines.txt | 590 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo4-3-optional-mutants.txt | 1372 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo4-4-demo-present-planted.txt | 681 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo4-5-gates.txt | 192 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo4-6-nodemo-job.txt | 2016 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo4-drivers/matrix.py | 2002 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo4-drivers/mut4.py | 1684 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo5-1-job-cases-shipped-py312.txt | 20402 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo5-2-job-cases-py313.txt | 5438 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo5-3-job-cases-with-optional-v4-py312.txt | 3838 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo5-4-apply-matrix.txt | 539 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo5-5-gates.txt | 1085 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo5-drivers/cases.py | 7084 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo5-drivers/gates.sh | 961 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo5-drivers/job.py | 1525 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-nodemo5-drivers/matrix.py | 2005 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1-1-affected-tests-after.txt | 203 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1-2-new-tests-on-old-code.txt | 1241 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1-3-lint-mypy.txt | 338 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1-4-smtp-mutant-new-test.txt | 546 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1-5-actionlint.txt | 114 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1-6-curl-flags-real-download.txt | 41 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1-7-apply-check.txt | 559 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v2-1-affected-tests-after.txt | 112 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v2-2-start-all-mutants.txt | 2598 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v2-3-lint-mypy-bandit.txt | 301 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v2-4-apply-check.txt | 268 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v2-5-new-tests-on-old-code.txt | 714 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v2-6-dash-guard.txt | 1288 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v3-1-affected-tests-after.txt | 990 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v3-2-dash-bypass.txt | 909 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v3-3-lint-mypy-bandit.txt | 360 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v3-4-guard-shell-matrix.txt | 2037 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v3-5-new-tests-on-v2.txt | 2112 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v3-6-mutants.txt | 1538 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v3-7-apply-check.txt | 4133 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v31-1-tests.txt | 1149 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v31-2-lint.txt | 339 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v31-3-new-tests-on-v3-scanner.txt | 2951 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v31-4-mutants.txt | 3470 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v31-5-scan-timing.txt | 437 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v31-6-apply-matrix.txt | 1330 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v31-7-diffstat.txt | 546 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v32-1-tests.txt | 475 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v32-2-lint.txt | 588 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v32-3-scan-timing.txt | 2698 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v32-4-mutants.txt | 2198 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v32-5-new-tests-on-base.txt | 944 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v32-6-apply-matrix.txt | 1453 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v32-7-combined-tree.txt | 261 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v32-8-cmp-diffstat.txt | 1384 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v321-1-tests.txt | 271 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v321-2-lint-gates.txt | 549 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v321-3-fails-before-on-v32.txt | 656 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v321-4-mutants.txt | 3817 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v321-5-real-file-mutants.txt | 849 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v321-6-timing-probes.txt | 948 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v321-7-apply-matrix.txt | 943 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p1v321-8-combined-tree.txt | 471 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2-equivalence-fuzz.py | 2483 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2-fails-before.txt | 12786 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2-lint-mypy.txt | 777 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2-pytest-affected.txt | 1404 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2feedconst-1-fails-before.txt | 2680 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2feedconst-2-behaviour-old-vs-new.txt | 4705 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2feedconst-3-mutants.txt | 596 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2feedconst-4-30runs.txt | 18 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2feedconst-5-gates.txt | 505 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2feedconst-6-apply-matrix.txt | 4508 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2feedconst-7-apply-head.txt | 9 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-1-30runs.txt | 570 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-2-on-base.txt | 944 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-3-apply-matrix.txt | 5196 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-4-mutants-regex.txt | 4560 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-5-mutants-feed.txt | 1401 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-6-equivalent-mutants.txt | 789 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-7-gates.txt | 381 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-driver-eqm.py | 1229 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-driver-fmut.py | 2715 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2optgaps-driver-mut.py | 5122 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v2-1-equivalence.txt | 2033 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v2-2-fails-before.txt | 1102 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v2-3-stage-mutants.txt | 691 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v2-4-lint-mypy-bandit.txt | 401 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v2-5-apply-matrix.txt | 927 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v2-6-pytest-affected.txt | 1484 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v2-7-hygiene-gitleaks.txt | 307 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v2-equivalence.py | 4232 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v21-1-fails-before-and-mutant.txt | 1759 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v21-2-bind-behaviour.txt | 873 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v21-3-pytest-affected.txt | 153 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v21-4-lint-mypy-bandit.txt | 342 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v21-5-apply-matrix.txt | 284 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v21-6-hygiene-gitleaks.txt | 625 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v21-bindprobe.py | 2097 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v22-1-mutants.txt | 1295 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v22-2-lint.txt | 988 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v22-3-pytest-affected.txt | 1607 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v22-4-hygiene-gitleaks.txt | 355 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v22-5-flaky-reserve.txt | 340 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v22-6-apply-matrix.txt | 490 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v22-mutant-runner.py | 1039 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v23-1-mutants.txt | 3566 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v23-2-stability.txt | 170 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v23-3-gates.txt | 563 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v23-4-lint.txt | 80 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v23-5-apply-matrix.txt | 755 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p2v23-mutant-runner.py | 949 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final-1-fails-before.txt | 4803 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final-2-mutants.txt | 9815 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final-3-lint.txt | 713 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final-4-apply-matrix.txt | 1654 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final-4b-stack.txt | 1124 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final-5-final-state-tests.txt | 576 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final-mutant-runner.py | 9504 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final2-1-fails-before.txt | 1115 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final2-2-mutants.txt | 11843 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final2-3-lint.txt | 522 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final2-4-apply-matrix.txt | 371 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final2-5-final-state-tests.txt | 1119 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final2-6-realrun-unshare.txt | 251 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final2-matrix-runner.py | 3009 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final2-mutant-runner-risky.py | 1891 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3final2-mutant-runner.py | 10908 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v2-1-probes-a-b-fails-before.txt | 1662 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v2-2-probes-a-b-after-mutants-lint-apply.txt | 2200 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v2-3-v2-fails-before.txt | 2671 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v2-4-v2-mutants.txt | 1686 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v2-5-v2-gates-tests.txt | 1051 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v2-6-v2-apply-check.txt | 329 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v2-7-probe-ab.txt | 1743 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v3-1-fails-before.txt | 13523 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v3-2-mutants.txt | 4948 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v3-3-gates-tests.txt | 794 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v3-4-apply-matrix.txt | 1072 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-p3v3-5-stack.txt | 653 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe2-1-fails-before-on-base.txt | 1328 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe2-2-affected-tests-after.txt | 1204 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe2-3-lint-mypy-bandit.txt | 314 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe2-4-mutants-and-help.txt | 931 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe2-6-apply-check.txt | 255 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe3-1-fails-before-on-base.txt | 1551 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe3-2-affected-tests-after.txt | 1550 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe3-3-lint-mypy-bandit.txt | 760 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe3-4-mutants.txt | 1973 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-probe3-6-apply-check.txt | 700 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/evidence-rv15-flow-tests.py | 5170 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/flaky413-fix.patch | 2438 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/flows-s8707-s8706.json | 35493 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/issues-pr4-0253.json | 15112 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/issues-pr4-9c53207-0615.json | 5827 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/nodemo-ci-job-v3.patch | 8270 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-ci-job-v4.patch | 12978 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-ci-job-v5.patch | 23474 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-ci-job.patch | 4813 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-ci-v5-evidence/batch1.out | 3830 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/nodemo-ci-v5-evidence/batch2.out | 7783 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/nodemo-ci-v5-evidence/batch3.out | 7178 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/nodemo-ci-v5-evidence/batch4.out | 5250 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/nodemo-ci-v5-evidence/batch5.out | 1348 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/nodemo-ci-v5-evidence/mycases.py | 4459 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/nodemo-ci-v5-evidence/nodemo-v4.yml | 12587 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/nodemo-ci-v5-evidence/runjob2.py | 1396 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/nodemo-feed-test-skip-v1.patch | 742 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-fix-v2.patch | 3029 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-fix-v3.patch | 5631 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-fix.patch | 2703 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-narrow-guard-reviewer.diff | 3029 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-optional-hygiene-repo-v2.patch | 2077 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-optional-hygiene-repo-v3.patch | 4507 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-optional-hygiene-repo-v4.patch | 5407 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-optional-hygiene-repo.patch | 952 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/nodemo-ruff-isort.patch | 702 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/probe-ab-v2.patch | 38887 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/probe-ab-v3-writes2-full.patch | 50872 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/probe-ab-v3-writes2.patch | 5606 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/probe-ab-v3.patch | 49218 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/probe-ab.patch | 25130 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/rv40-real-mutants.py | 4839 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/rv40-synthetic-cases.py | 8335 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/sonar/sonar-p1-quickwins-v2.patch | 28355 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p1-quickwins-v3.1.patch | 44830 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p1-quickwins-v3.2.1-delta.patch | 19907 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p1-quickwins-v3.2.2-delta.patch | 1751 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p1-quickwins-v3.2.patch | 41892 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p1-quickwins-v3.patch | 36086 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p1-quickwins.patch | 14496 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p2-feed-constants-delta.patch | 10496 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p2-feed-optional.patch | 5134 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p2-optional-gaps-delta.patch | 10043 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p2-regex-http-bug-v2.1.patch | 26858 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p2-regex-http-bug-v2.2-delta.patch | 6956 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p2-regex-http-bug-v2.3-delta.patch | 5891 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p2-regex-http-bug-v2.patch | 21427 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p2-regex-http-bug.patch | 29431 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p2-regex-optional.patch | 7286 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p3-final-v2-minors.patch | 30304 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p3-final-v2-risky.patch | 23732 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p3-final.patch | 95724 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p3-path-helper-v2.patch | 53156 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p3-path-helper-v3.patch | 69035 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p3-path-helper.patch | 27777 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p3-probe-a.patch | 6731 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/sonar/sonar-p3-probe-b.patch | 7442 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/stranger/01-venv.txt | 186 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/02-start.txt | 236 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/03-counts0.txt | 1246 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/04-feed-form1.txt | 162 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/05-feed-form1-again.txt | 186 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/06-feed-webhook1.txt | 198 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/07-counts.txt | 772 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/08-outbox.txt | 537 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/09-duplicate-lookalikes.txt | 1974 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/10-burst10.txt | 1235 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/11-burst100.txt | 806 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/12-portal.txt | 10082 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/13-hostile.txt | 7258 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/13a-counts-before-hostile.txt | 409 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/14-bigbody-curl.txt | 372 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/15-portal-hostile-json.txt | 2486 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/16-api-limit-and-outbox.txt | 750 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/17-parallel50-valid.txt | 1406 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/18-parallel50-idle.txt | 1024 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/19-desk-log.txt | 295 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/20-reset.txt | 122 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/stranger/SUMMARY.md | 10904 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/stranger/limits-burst-doc.patch | 3330 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/CODEANT-COVERAGE.md | 41750 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/triage/CODEANT-COVERAGE.r2.md | 40551 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/DEEPSOURCE-COVERAGE.md | 22496 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/triage/PATCH-NOTES.md | 6843 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/RESOLVE-js.md | 7747 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/RESOLVE-py.md | 8952 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/triage/REVIEW-codeant-A.md | 14587 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant-B.md | 11803 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant-C.md | 14048 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant2-rt-A.md | 4240 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant2-rt-B.md | 4644 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant2-sec.md | 20555 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant3-rt-A.md | 5877 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant3-rt-B.md | 5001 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant3-sec.md | 3699 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant4-rt.md | 4143 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant4-sec.md | 4951 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant5-rt-delta.md | 3349 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant5-sec.md | 5739 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-codeant6-sec-nits.md | 3840 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-extra.md | 7899 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-js-2.md | 6559 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-js.md | 5181 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-py-2.md | 7063 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/REVIEW-py.md | 6436 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/SUMMARY-codeant2-runtime.md | 4071 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/SUMMARY-codeant2-sec.md | 8449 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/SUMMARY-codeant3-rt.md | 9083 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/SUMMARY-codeant3-sec.md | 3341 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/SUMMARY-codeant4-sec.md | 3644 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/SUMMARY-codeant5-sec.md | 3530 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/SUMMARY-codeant6-sec-nits.md | 4169 | NOT-READ | md report not opened (continuation lane needed) |
| handover/demo/triage/SUMMARY.md | 21947 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/triage/astscan.py | 3295 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/codeant-comments-lead.txt | 57076 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/codeant-demo-only.patch | 21274 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant-desk.patch | 4702 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant-docs.patch | 4179 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant-gitleaks-after-docs-and-deps.patch | 703 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant-gitleaks-after-sonar-coverage.patch | 696 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant-gitleaks.patch | 674 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant-n8n-proof.patch | 2975 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant-portal-log.patch | 8283 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant-scripts.patch | 9787 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant-tests-hardening.patch | 9621 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-demo-only-r1.patch | 36878 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-demo-only-r2.patch | 41093 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-demo-only.patch | 45197 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-desk-r1.patch | 15190 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-desk-r2.patch | 23871 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-desk-r3.patch | 24961 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-desk.patch | 27723 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-docs.patch | 13363 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-fakes-body-r1.patch | 10757 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-fakes-body-r2.patch | 10757 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-fakes-body.patch | 10757 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-gitleaks.patch | 4600 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-n8n-proof.patch | 4602 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-portal-log-r1.patch | 10330 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-portal-log-r2.patch | 10432 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-portal-log.patch | 10432 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-scripts.patch | 27014 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-standins-body-r2.patch | 4643 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-standins-body.patch | 4643 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-tests-hardening-r1.patch | 17590 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-tests-hardening-r2.patch | 23425 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant2-tests-hardening.patch | 23818 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-docs-r3.patch | 14662 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-docs-r4.patch | 16358 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-docs.patch | 17653 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-gitleaks-r3.patch | 6598 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-gitleaks-r4.patch | 9268 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-gitleaks.patch | 10198 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-n8n-proof-r3.patch | 4602 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-n8n-proof-r4.patch | 4602 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-n8n-proof.patch | 4602 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-scripts-r3.patch | 37674 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-scripts-r4.patch | 56182 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-scripts.patch | 70821 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/codeant3-sec-nits.patch | 48686 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/deepsource-comments-lead.txt | 73030 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/deepsource-comments-plain.txt | 8725 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/equiv-overview-real.js | 6808 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/eslint.config.mjs | 1371 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-after-full.txt | 3979 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-baseline-full.txt | 3979 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-apply-check.txt | 1447 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-demo-only.txt | 648 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-desk.txt | 1882 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-fakes-after.txt | 212 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-fakes-before.txt | 1564 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-gitleaks.txt | 278 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-lint.txt | 397 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-n8n-proof.txt | 358 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-portal-log.txt | 606 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-reset-ps1.txt | 291 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-scripts-after.txt | 168 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-scripts-before.txt | 1470 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-tests-after-2.txt | 917 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-tests-after.txt | 1427 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-tests-hardening.txt | 977 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant-tests-mutants.txt | 712 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-rt-apply-matrix.txt | 6572 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-rt-burst-n0.txt | 405 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-rt-desk.txt | 2048 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-rt-fakes-body.txt | 1763 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-rt-fakes-mutants.txt | 2366 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-rt-hygiene-gitleaks.txt | 613 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-rt-portal-log.txt | 3117 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-rt-pytest-focused.txt | 1550 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-rt-pytest-full.txt | 7912 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-0-baseline-hygiene.txt | 352 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-1a-old-anchor-hygiene-FAILS.txt | 558 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-1a-old-gitleaks-hygiene-FAILS.txt | 810 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-1b-regression-on-OLD-config-FAILS.txt | 672 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-1c-new-config-hygiene-PASSES.txt | 386 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-2a-tracked-tree-gitleaks-dir.txt | 432 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-2b-tracked-tree-gitleaks-git.txt | 599 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-3-combined-pytest.txt | 1109 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-4-new-tests-on-OLD-code-FAIL.txt | 7205 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-5-lint.txt | 719 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant2-sec-6-apply-matrix.txt | 4475 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-1-old-code-FAILS.txt | 1984 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-10-gitleaks.txt | 598 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-11-core-touches-fail-on-old.txt | 1151 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-12-pytest-full.txt | 1906 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-12a-pytest-full-HUNG-at-38pct-playwright.txt | 3010 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-12b-hung-region.txt | 439 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-13-standins-body-mutants.txt | 1284 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-14-rebase-on-40d5668.txt | 954 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-4-skip-test-old-FAILS.txt | 1248 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-5-fakes-new-tests-old-code.txt | 1512 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-6a-fifo-mutants.txt | 967 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-6b-n4-01-03-old-helpers-FAIL.txt | 1046 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-6c-eslint.txt | 4477 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-7-lint-mypy-bandit.txt | 630 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-8-pytest-focused.txt | 2109 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-8a-pytest-focused-FIRST-RUN-1-failed.txt | 2109 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-8b-pytest-after-rename.txt | 344 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-rt-9-apply-matrix.txt | 5665 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-1-prefix-table-new-vs-old.txt | 6755 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-10-with-docs-and-deps-v4-and-semgrep-gitleaks.txt | 714 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-2-linearity-timing.txt | 1732 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-3-final-pytest-FIRST-RUN-1-failed.txt | 4903 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-3b-final-pytest.txt | 2341 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-3c-fresh-tree-final-pytest.txt | 2429 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-4a-gitleaks-dir.txt | 641 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-4b-gitleaks-git.txt | 485 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-5-lint.txt | 604 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-6-new-tests-on-PREVIOUS-state-FAIL.txt | 8277 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-7-strengthened-tests-vs-mutants.txt | 1272 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-8-linearity-test-on-quadratic-MUTANT-FAILS.txt | 1360 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant3-sec-9-apply-matrix.txt | 19260 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-rt-1-file-uri.txt | 1296 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-rt-3-main-guard.txt | 785 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-rt-4-content-length.txt | 625 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-rt-5-redundant-hunk.txt | 922 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-rt-6-apply-order.txt | 347 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-rt-7-gates.txt | 307 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-rt-8-pytest-focused.txt | 1174 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-rt-9-apply-matrix.txt | 810 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-10-cross-lane.txt | 2127 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-1a-prefix-table-and-localhost-rows-r3-vs-r4.txt | 9235 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-1b-linearity-timing.txt | 1543 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-3-final-pytest-FIRST-RUN-1-failed.txt | 3395 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-3-final-pytest.txt | 2446 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-4a-gitleaks-dir.txt | 445 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-4b-gitleaks-git.txt | 462 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-5-lint.txt | 841 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-6-new-tests-on-R3-state-FAIL.txt | 6415 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-7a-hygiene-helper-mutant.txt | 562 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-7b-reset-alias-mutant.txt | 1054 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-8-activelink-quadratic-mutant-FAILS.txt | 1021 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant4-sec-9-apply-matrix.txt | 19533 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-rt-1-fails-before.txt | 2151 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-rt-2-passes-after.txt | 98 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-rt-3-gates.txt | 782 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-rt-4-pytest.txt | 3171 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-rt-5-apply.txt | 807 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-sec-1-key-leak-r4-vs-fix.txt | 2339 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-sec-1b-linearity-timing.txt | 4289 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-sec-2-new-tests-on-R4-state-FAIL.txt | 4636 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-sec-3-final-pytest.txt | 1848 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-sec-3-mutants.txt | 5389 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-sec-4a-gitleaks-dir.txt | 412 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-sec-4b-gitleaks-git.txt | 566 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-sec-5-lint.txt | 579 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant5-sec-9-apply-matrix.txt | 7166 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant6-sec-1-linearity-timing.txt | 1819 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant6-sec-2-new-tests-on-REVIEWED-state-FAIL.txt | 12558 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant6-sec-3-mutants-scrub.txt | 4609 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant6-sec-4-mutants-n8n-api.txt | 2850 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant6-sec-5-nit2-vacuous-old-form-vs-fixed.txt | 1420 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant6-sec-6-mutants-docs-phrases.txt | 3105 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-codeant6-sec-7-gates-on-40d5668.txt | 2203 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-eslint-after.txt | 8127 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-eslint-before.txt | 10412 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-after-full-CUT-by-timeout.txt | 2878 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-after-full.txt | 3979 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-after-targeted.txt | 836 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-astscan-tests.txt | 5485 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-baseline-full.txt | 3979 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-demo-unpack-proof.txt | 923 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-eslint-demo-js.txt | 5887 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-eslint-tests-js.txt | 1530 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-mypy-base.txt | 1241 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-mypy-extra.txt | 1241 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-pylint-demo-after.txt | 550 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-pylint-demo-before.txt | 737 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-pylint-tests.txt | 92438 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-ruff-tests.txt | 5292 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-sql-callsites.txt | 380 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-extra-sqlscan.txt | 3834 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-hierarchy-test.txt | 274 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-confirm-log-mutants.txt | 2147 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-apply-check.txt | 1457 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-equiv-overview.txt | 3355 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-eslint-full.txt | 9518 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-lint-hygiene.txt | 507 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-log-probe.txt | 1766 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-log-test-mutants.txt | 2822 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-nit2-moved-decls.txt | 955 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-original-js-portal-patch.txt | 4488 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-portal-tests-after.txt | 2037 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-portal-tests-before.txt | 1926 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-js-resolve-var-count.txt | 1496 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-py-resolve-00-setup.txt | 1998 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-py-resolve-01-fails-before.txt | 17021 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-py-resolve-02-mutation.txt | 6772 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-py-resolve-03-full-base.txt | 4917 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-py-resolve-04-full-patched.txt | 5355 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-py-resolve-05-lint.txt | 2851 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-py-resolve-06-original-py-retry-patch.txt | 12211 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/evidence-py-resolve-07-patch-apply.txt | 2508 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/extra-demo-only.patch | 748 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/extra-tests.patch.NOT-NEEDED.txt | 144 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/extra-tools/callsites.py | 611 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/extra-tools/eslint-demo.config.mjs | 1210 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/extra-tools/eslint-tests.mjs | 582 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/extra-tools/prove_unpack.py | 661 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/extra-tools/scan2.py | 1716 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/extra-tools/sqlscan.py | 926 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/extra-tools/unpack.py | 659 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/triage/js-portal.patch | 13082 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/triage/py-retry.patch | 23549 | SKIMMED | patch chain; name, size and md5 only; whether applied is in APPLY-LIST.md (L1) |
| handover/demo/xss/01-start.txt | 1057 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/02-post-leads.txt | 1015 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/03-outbox.json | 3513 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/04-post-more.txt | 1092 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/05-browser-results.json | 28650 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/05-browser-run.txt | 31 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/06-overflow-probe.json | 1051 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/07-outbox-subjects.txt | 2558 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/08-headers.txt | 4480 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/09-js-sinks-grep.txt | 2126 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/10-js-href-src-grep.txt | 2010 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/SUMMARY.md | 12499 | SKIMMED | md opened: first lines or chars only, long lines cut at 400-700 chars; rest NOT-READ |
| handover/demo/xss/drawer-dark-masked-0.png | 199976 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/drawer-dark-unmasked-0.png | 140199 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/drawer-dark-unmasked-len100.png | 140200 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/drawer-dark-unmasked-len200.png | 140147 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/drawer-light-masked-0.png | 226917 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/drawer-light-unmasked-0.png | 168220 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/drawer-light-unmasked-len100.png | 168213 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/drawer-light-unmasked-len200.png | 168174 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/leads-dark-masked-390.png | 192565 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/leads-dark-masked.png | 334763 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/leads-dark-unmasked-390.png | 190845 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/leads-dark-unmasked.png | 338872 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/leads-light-masked-390.png | 190340 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/leads-light-masked.png | 339847 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/leads-light-unmasked-390.png | 188514 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/leads-light-unmasked.png | 339481 | SKIMMED | screenshot family; listed and md5 compared, not viewed |
| handover/demo/xss/overflow_probe.py | 1872 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/post_leads.py | 1219 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/post_more.py | 1397 | SKIMMED | scan or run output family; listed and md5 compared, not opened |
| handover/demo/xss/run_browser.py | 5350 | SKIMMED | scan or run output family; listed and md5 compared, not opened |

## Components
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L4-C-001 | Lead desk server and SQLite book (Mode A, src/lead_desk) | the product these folders test: takes lead requests, decides new or repeat, keeps a database file; per DECISION it is retired from the take | `handover/demo/hang/RESULTS.md:52 "SQLite busy handling lives in db.py/gate.py"` | STORE |
| L4-C-002 | Portal (pages under /ui/ plus JSON read calls) | screens for leads, requests to check, request log, data page, demo controls | `handover/demo/xss/SUMMARY.md:4 "No script executed"` | NOTICE |
| L4-C-003 | Reaper (background thread of the desk) | re-sends stuck follow-up mail and CRM writes | `handover/demo/hang/RESULTS.md:48 "a new reaper waits for older reapers"` | RETRY |
| L4-C-004 | Fake services server (port 8766: outbox, fake CRM) | stands in for mail and CRM in demo and test runs | `handover/demo/xss/SUMMARY.md:38 "GET http://127.0.0.1:8766/fake/outbox"` | NOTICE |
| L4-C-005 | Burst tool demo_only.burst | sends N identical requests to prove one lead and one mail | `handover/demo/stranger/SUMMARY.md:6 "the lead count and the follow-up count should each be 1"` | COUNTER |
| L4-C-006 | Take scripts (run_real_check.py, run_live_check.py, hubspot_probe.py, start_all, reset) | real-service check scripts of the desk repo, dry-run only here | `handover/demo/real-run/DRY-RUN-CHECKS.md:12 "NOT run, on purpose"` | OTHER |
| L4-C-007 | Adapters crm_hubspot.py, live_claude.py, smtp_outbox.py, smtp_provider.py | HubSpot CRM, model call and mail adapters inside the desk | `handover/demo/triage/SUMMARY.md:11 "crm_hubspot.py, live_claude.py, smtp_outbox.py, smtp_provider.py"` | NOTICE |
| L4-C-008 | tools/hygiene.py plus gitleaks config | repo scan for secrets and hard-coded values, run by a test and by CI | `handover/demo/scans/SCAN-TABLE.md:18 "tools/hygiene.py has no command-line entry point"` | FILTER |
| L4-C-009 | CI workflows lint.yml and sonar.yml (and proposed nodemo.yml, semgrep.yml) | GitHub checks on the demo repo | `handover/demo/skips/SKIP-TABLE.md:16 "The CI picture"`; `handover/demo/sonar/NOTES-nodemo-ci-v5.md:2 "new file .github/workflows/nodemo.yml"` | OTHER |
| L4-C-010 | Review-fix patch stack on branch pr-3-tests | about 180 patch files proposing fixes, applied in batches by the lead | `handover/demo/integration/INT-1.md:34 "First stack branch where the whole patch applies"` | OTHER |
| L4-C-011 | n8n workflows | the flows the take runs; no workflow file and no n8n run appears in these folders | `handover/demo/integration/INT-2b.md:10 "a real n8n"` | OTHER |

## Stores
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4-S-001 | desk.db (SQLite book plus .lock, -wal, -shm) | receipts, claims, counts, portal screens | desk (src/lead_desk/db.py, gate.py) | validated lead requests | rows read by portal and /counts | busy handling by gate and db timeouts, not read in full | UNVERIFIED | UNVERIFIED | same request number gives replayed true, same email gives duplicate | desk.log | desk process | tests in these folders ran with fakes only | desk, portal, reaper | `handover/demo/real-run/DRY-RUN-CHECKS.md:32 "desk.db, desk.db.lock, desk.db-wal/-shm"` | STORE |
| L4-S-002 | fake outbox (in the fakes server) | records demo mails: key, to, subject only | fakes server | mails the desk sends | JSON at /fake/outbox | UNVERIFIED | N/A: demo store | UNVERIFIED | UNVERIFIED | fakes.log | fakes process | xss and stranger runs | demo and test runs | `handover/demo/xss/SUMMARY.md:13 "The demo outbox entries hold only key, to, subject"` | STORE |
| L4-S-003 | result.json and run folder real-dry-XXXX | record of one real-check or self-test run | run_real_check.py | run settings | result.json, desk logs, *.hubspot.json, *.smtp.json | folder was left behind before fix D6 | N/A: file | UNVERIFIED | new folder each run | run folder logs | script user | tests/test_take_script_refusals.py (new, pending patch) | take scripts | `handover/demo/real-run/DRY-RUN-CHECKS.md:32 "never removed by the script"` | STORE |
| L4-S-004 | scans/scan-rows.tsv and per-head evidence-q6 files | one line per branch head: gitleaks, hygiene, ruff results | scan-heads.sh | branch heads | table in SCAN-TABLE.md | script exit codes recorded | N/A: rerun by hand | UNVERIFIED | file is rewritten each run | evidence-q6-<branch>.txt | evidence runner | not tested | lead | `handover/demo/scans/SCAN-TABLE.md:4 "Re-run: ./scan-heads.sh"` | LOG |
| L4-S-005 | Live-model ledger and SMTP stats files (DESK_LIVE_LEDGER_PATH, DESK_SMTPP_STATS_FILE) | spend and send counts of real runs | desk | calls made | counts for caps | UNVERIFIED | N/A: file | UNVERIFIED | UNVERIFIED | file itself | desk process | UNVERIFIED | real-run | `handover/demo/real-run/REVIEW-v4-fresh-copy.md:30 "DESK_LIVE_LEDGER_PATH"` | COUNTER |

## Workflows
NONE FOUND: searched all 16 folders for n8n workflow files, mf_leads, stage.journal and Postgres; only mentions are "a real n8n" not run (see Findings L4-FD-010).

## Workflow walk
NONE FOUND: no workflow file in handover/demo; nothing to walk.

## Scripts
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4-X-001 | real-run/run-dry-checks.sh | runs 226 dry cases of the take scripts, two passes | evidence runner | arguments and env | text output and exit code | exit 1 on mismatch, 2 on setup problem | N/A: rerun by hand | UNVERIFIED | temp dir per run | results.tsv and evidence-q4-*.txt | env -i, no real key | self (it is the test) | lead | `handover/demo/real-run/DRY-RUN-CHECKS.md:4 "with 2 passes (224 case results)"` | OTHER |
| L4-X-002 | scans/scan-heads.sh | gitleaks and hygiene scan per branch head | evidence runner | arguments and env | text output and exit code | records exit codes | N/A: rerun by hand | UNVERIFIED | rewrites its output | evidence-q6 files | local only | none | lead | `handover/demo/scans/SCAN-TABLE.md:4 "Re-run: ./scan-heads.sh"` | FILTER |
| L4-X-003 | integration drivers (int2b-C2, int3 chunk driver, post-steps) | run the full suite in 10 chunks after container restarts | evidence runner | arguments and env | text output and exit code | skips chunks with an .exit file | resumable by design | timeout 1500 per chunk | chunk skipped if .exit exists | chunk txt and .exit files | local only | none | lead | `handover/demo/integration/INT-3-2db3926.md:7 "resumable driver"` | RETRY |
| L4-X-004 | xss scripts (post_leads.py, post_more.py, run_browser.py, overflow_probe.py) | post hostile text and open the portal in a browser | evidence runner | arguments and env | text output and exit code | UNVERIFIED | N/A: one-off | UNVERIFIED | not idempotent | xss/*.json and txt | local only | none | lead | `handover/demo/xss/SUMMARY.md:84 "scripts post_leads.py, post_more.py, run_browser.py, overflow_probe.py"` | OTHER |
| L4-X-005 | make_synthetic_config.py, probe_stub.py, lo_up-q4g.py, pty_ans-q4g.py, sitecustomize-q4g.py | build made-up configs, block non-loopback network, drive a pseudo-terminal | evidence runner | arguments and env | text output and exit code | block lines logged | N/A: test helper | UNVERIFIED | UNVERIFIED | evidence files | local only | none | lead | `handover/demo/real-run/NOTES-start-prompt-v2.md:6 "sitecustomize that blocks and logs any non-loopback"` | OTHER |
| L4-X-006 | sonar mutant and equivalence runners (evidence-*-runner.py, rv40-*.py) | plant mistakes in code and check tests catch them | evidence runner | arguments and env | text output and exit code | UNVERIFIED | N/A: one-off | UNVERIFIED | UNVERIFIED | evidence txt | local only | self | lead | `handover/demo/sonar/NOTES-p3-final.md:40 "2 mutants: 59 (40 of the helper"` | OTHER |
| L4-X-007 | triage/extra-tools and astscan.py | search the code for patterns a review bot named | evidence runner | arguments and env | text output and exit code | UNVERIFIED | N/A: one-off | UNVERIFIED | UNVERIFIED | evidence txt | local only | none | lead | `handover/demo/triage/DEEPSOURCE-COVERAGE.md:7 "with the tools listed below"` | OTHER |

## Jobs
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4-J-001 | same-lead filter in the desk | email trimmed of spaces and lower-cased, nothing more, decides repeat | desk | lead request | new or duplicate verdict | Cyrillic look-alike becomes a new lead | N/A: decision | N/A: decision | same request number replays | receipt rows | desk | stranger run | portal and mail | `handover/demo/stranger/SUMMARY.md:7 "trimmed of spaces and lower-cased, nothing more"` | FILTER |
| L4-J-002 | size and stall limits of the desk | 65536 byte cap, 10 second header and body deadline | desk | HTTP request | 413 or 408 | refused with error body | N/A: refusal | 10 s | N/A: refusal | no log line for rejected requests | desk | stranger hostile table | desk | `handover/demo/stranger/SUMMARY.md:72 "the desk logs nothing for the rejected requests"` | FILTER |
| L4-J-003 | desk counters (/counts) | received, new, duplicate, review, rejected_envelopes, pending follow-ups | desk | every request | JSON counts, ok flag | rejected_envelopes makes ok false until restart | N/A: counter | N/A: counter | reconciled flag | none | desk | stranger run | portal overview | `handover/demo/stranger/SUMMARY.md:12 "rejected_envelopes"` | COUNTER |
| L4-J-004 | call caps (DESK_HUBSPOT_MAX_CALLS, DESK_SMTPP_MAX_SENDS, REAL_HUBSPOT_READBACK_MAX_CALLS) | limit real-service calls per run | desk and take scripts | settings | refusal if cap out of range | refused at start, exit 2 | N/A: cap | N/A: cap | N/A: cap | script output | script user | DRY-RUN cases | real-run | `handover/demo/real-run/DRY-RUN-CHECKS.md:34 "caps 0 or above 10000"` | COUNTER |
| L4-J-005 | reaper re-send of stuck follow-ups | retries mail and CRM writes after failure | desk reaper | pending rows | sent or failed rows | hung adapter call cut at a deadline, worker abandoned | pass every 0.05 s in tests | call deadline up to 9 s | UNVERIFIED | desk.log | desk | tests/test_hung_adapter_calls.py | desk | `handover/demo/hang/RESULTS.md:46 "the desk waits for the hung adapter call"` | RETRY |
| L4-J-006 | follow-up mail (demo outbox or provider) | tells the lead a thanks mail; subject holds the name as sent | desk | lead name and email | mail subject | hostile name placed raw in subject | reaper | send timeout | one mail per lead (burst proof) | fakes.log | SMTP identity of provider config | burst N=10 and N=100 | portal and demo | `handover/demo/xss/SUMMARY.md:39 "Thanks for getting in touch"` | NOTICE |
| L4-J-007 | portal screens | shows leads, request log, needs a person | portal | JSON from /api/ui/* | HTML screens | masking default on, company never masked | N/A: screen | N/A: screen | N/A: screen | none | browser user | xss and layout runs | viewer | `handover/demo/xss/SUMMARY.md:10 "COMPANY column is shown unmasked"` | NOTICE |
| L4-J-008 | desk log and request log | execution and request record | desk | events | data/desk.log, portal Request log page | only startup line seen | N/A: log | N/A: log | N/A: log | desk.log | desk | stranger run | portal | `handover/demo/stranger/SUMMARY.md:72 "data/desk.log held 1 line only"` | LOG |
| L4-J-009 | secret and hard-coded value scan (gitleaks plus hygiene test) | blocks keys and literals in the repo | CI and tests | repo files | pass or finding list | allowlist failed on 558d37f | N/A: check | UNVERIFIED | N/A: check | CI log | CI job | tests/test_hygiene.py | CI | `handover/demo/gitleaks/SUMMARY.md:1 "FAILED: gitleaks reports findings"` | FILTER |

## Credentials
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4-K-001 | DESK_HUBSPOT_KEY_FILE (name only) | path of the HubSpot key file | desk | N/A: credential | N/A: credential | refused at start if file missing or shorter than 8 characters (after fix D1, pending patch) | N/A: credential | N/A: credential | N/A: credential | never printed | desk or script | DRY-RUN cases with made-up keys | real-run scripts | `handover/demo/real-run/REVIEW-v3-fresh.md:30 "DESK_HUBSPOT_KEY_FILE"` | OTHER |
| L4-K-002 | DESK_SMTPP_PASSWORD_FILE (name only) | path of the mail password file | desk | N/A: credential | N/A: credential | refused at start if file missing or shorter than 8 characters (after fix D1, pending patch) | N/A: credential | N/A: credential | N/A: credential | never printed | desk or script | DRY-RUN cases with made-up keys | real-run scripts | `handover/demo/real-run/REVIEW-v3-fresh.md:26 "DESK_SMTPP_PASSWORD_FILE"` | OTHER |
| L4-K-003 | DESK_LIVE_KEY_FILE (name only) | path of the live model key file | desk | N/A: credential | N/A: credential | refused at start if file missing or shorter than 8 characters (after fix D1, pending patch) | N/A: credential | N/A: credential | N/A: credential | never printed | desk or script | DRY-RUN cases with made-up keys | real-run scripts | `handover/demo/real-run/REVIEW-v3-fresh.md:32 "DESK_LIVE_KEY_FILE"` | OTHER |
| L4-K-004 | N8N_API_KEY_FILE (name only) | path of the n8n API key file | n8n helper scripts | N/A: credential | N/A: credential | refused at start if file missing or shorter than 8 characters (after fix D1, pending patch) | N/A: credential | N/A: credential | N/A: credential | never printed | desk or script | DRY-RUN cases with made-up keys | real-run scripts | `handover/demo/sonar/REVIEW-p3-fresh.md:23 "N8N_API_KEY_FILE"` | OTHER |
| L4-K-005 | SONAR_TOKEN (name only) | token for SonarCloud scan in CI | CI | N/A: credential | N/A: credential | refused at start if file missing or shorter than 8 characters (after fix D1, pending patch) | N/A: credential | N/A: credential | N/A: credential | never printed | desk or script | DRY-RUN cases with made-up keys | real-run scripts | `handover/demo/coverage/REVIEW-1.md:6 "SONAR_TOKEN"` | OTHER |
| L4-K-006 | GITHUB_TOKEN (name only) | token the CI job and tools use | CI | N/A: credential | N/A: credential | refused at start if file missing or shorter than 8 characters (after fix D1, pending patch) | N/A: credential | N/A: credential | N/A: credential | never printed | desk or script | DRY-RUN cases with made-up keys | real-run scripts | `handover/demo/semgrep/main-61ded9e-v8/semgrep-pr-body-v8.md:103 "GITHUB_TOKEN"` | OTHER |

## Docs and tests and folders
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L4-D-001 | docs/limits.md of the desk repo | load and limits wording | `handover/demo/stranger/SUMMARY.md:6 "MISMATCH (docs/limits.md"` | OTHER |
| L4-D-002 | docs/settings.md and docs/real-services.md | setting and exit-code promises for take scripts | `handover/demo/real-run/DRY-RUN-CHECKS.md:27 "docs/settings.md:3"` | OTHER |
| L4-D-003 | docs/tests.md | how to run tests; lacks Pillow and Playwright pin | `handover/demo/outsider/SUMMARY.md:5 "README, docs/tests.md and requirements-dev.in do not mention Pillow"` | OTHER |
| L4-T-001 | full suite on pr-3-tests 2db3926 | 3138 passed, 3 skipped, 0 failed in one process, 1218 s | `handover/demo/integration/INT-3-2db3926.md:12 "3138 passed, 3 skipped, 0 failed, 0 errors in 1218.48 s"` | OTHER |
| L4-T-002 | full suite on 558d37f batch 1 | 2400 passed, 116 skipped in 914 s | `handover/demo/integration/INT-1.md:1 "2400 passed, 116 skipped"` | OTHER |
| L4-T-003 | tests/test_hung_adapter_calls.py | hung adapter call tests, 42 tests | `handover/demo/hang/RESULTS.md:16 "42 passed each"` | RETRY |
| L4-T-004 | browser portal tests (7 files, Playwright 1.63.0) | portal layout, wording, masking | `handover/demo/outsider2/SUMMARY.md:32 "185 passed, 2 failed (PIL)"` | NOTICE |
| L4-T-005 | tests/test_hygiene.py | secret and literal scan test | `handover/demo/scans/SCAN-TABLE.md:14 "15 passed in 14.92s"` | FILTER |
| L4-T-006 | tests/test_take_script_refusals.py (13 cases, pending patch) | refusals of take scripts before the y/N question | `handover/demo/real-run/FIXES.md:4 "(13 cases)"` | OTHER |
| L4-F-001 | handover/demo/coverage/ | 40 files of evidence for the topic coverage; read as a family | handover/demo/coverage/ (listing, this lane) | OTHER |
| L4-F-002 | handover/demo/fixes/ | 50 files of evidence for the topic fixes; read as a family | handover/demo/fixes/ (listing, this lane) | OTHER |
| L4-F-003 | handover/demo/gitleaks/ | 25 files of evidence for the topic gitleaks; read as a family | handover/demo/gitleaks/ (listing, this lane) | OTHER |
| L4-F-004 | handover/demo/hang/ | 74 files of evidence for the topic hang; read as a family | handover/demo/hang/ (listing, this lane) | OTHER |
| L4-F-005 | handover/demo/integration/ | 111 files of evidence for the topic integration; read as a family | handover/demo/integration/ (listing, this lane) | OTHER |
| L4-F-006 | handover/demo/layout/ | 428 files of evidence for the topic layout; read as a family | handover/demo/layout/ (listing, this lane) | OTHER |
| L4-F-007 | handover/demo/outsider/ | 16 files of evidence for the topic outsider; read as a family | handover/demo/outsider/ (listing, this lane) | OTHER |
| L4-F-008 | handover/demo/outsider2/ | 21 files of evidence for the topic outsider2; read as a family | handover/demo/outsider2/ (listing, this lane) | OTHER |
| L4-F-009 | handover/demo/real-run/ | 99 files of evidence for the topic real-run; read as a family | handover/demo/real-run/ (listing, this lane) | OTHER |
| L4-F-010 | handover/demo/scans/ | 13 files of evidence for the topic scans; read as a family | handover/demo/scans/ (listing, this lane) | OTHER |
| L4-F-011 | handover/demo/semgrep/ | 96 files of evidence for the topic semgrep; read as a family | handover/demo/semgrep/ (listing, this lane) | OTHER |
| L4-F-012 | handover/demo/skips/ | 86 files of evidence for the topic skips; read as a family | handover/demo/skips/ (listing, this lane) | OTHER |
| L4-F-013 | handover/demo/sonar/ | 300 files of evidence for the topic sonar; read as a family | handover/demo/sonar/ (listing, this lane) | OTHER |
| L4-F-014 | handover/demo/stranger/ | 23 files of evidence for the topic stranger; read as a family | handover/demo/stranger/ (listing, this lane) | OTHER |
| L4-F-015 | handover/demo/triage/ | 245 files of evidence for the topic triage; read as a family | handover/demo/triage/ (listing, this lane) | OTHER |
| L4-F-016 | handover/demo/xss/ | 32 files of evidence for the topic xss; read as a family | handover/demo/xss/ (listing, this lane) | OTHER |

## Findings
| id | claim type | severity | evidence | conflicts with | job key |
|---|---|---|---|---|---|
| L4-FD-001 | idle | Major | All 1659 files in this lane test the desk (SQLite book, portal, HubSpot and mail adapters). My search of the 16 folders found no mention of mf_leads, stage.journal or Postgres; nothing proves the take stores. `handover/demo/hang/RESULTS.md:52 "SQLite busy handling lives in db.py/gate.py"` | DECISION line 15 | STORE |
| L4-FD-002 | duplicate | Major | The same missing-Pillow gap is reported three times: `handover/demo/outsider/SUMMARY.md:5 "Undocumented browser-test dependency"`; `handover/demo/outsider2/SUMMARY.md:7 "Browser tests: 2 failed on first run"`; `handover/demo/layout/SUMMARY.md:6 "Pillow is missing in my venv"`; fix only in pending docs-and-deps patch `handover/demo/fixes/PLAN.md:2 "Patch: docs-and-deps.patch"` | none | OTHER |
| L4-FD-003 | inconsistent | Major | Test counts do not reconcile: `handover/demo/integration/INT-1.md:9 "actual 2400 passed (51 more than 2349"`; `handover/demo/outsider/SUMMARY.md:13 "Lead expected about 2329"`; `handover/demo/fixes/PLAN.md:6 "still unreconciled"`; `handover/demo/skips/SKIP-TABLE.md:9 "cannot be reconciled to a test list"` | none | COUNTER |
| L4-FD-004 | inconsistent | Blocker | Dry-run case count is stated as 224 but the same file adds to 226 (124+22+38+8+34) and results.tsv has 226 rows: `handover/demo/real-run/DRY-RUN-CHECKS.md:4 "224 case results"`; `handover/demo/real-run/DRY-RUN-CHECKS.md:40 "Counts: rrc 124"` (Blocker by the severity table: a false number; real impact low) | none | COUNTER |
| L4-FD-005 | unverified | Major | Three runs stalled or ended early with no cause: `handover/demo/outsider/SUMMARY.md:6 "One unexplained hang"`; `handover/demo/outsider2/SUMMARY.md:6 "ENDED EARLY"`; `handover/demo/hang/PLAN-v2.md:8 "THE CAUSE OF THE SUSPECTED STALL IS UNPROVEN"`; `handover/demo/hang/RESULTS.md:6 "NOT REPRODUCED"`; `handover/demo/integration/INT-2b.md:2 "misreading of a block-buffered progress file"`; the hang-fix patch is named a fix but is a guard | none | RETRY |
| L4-FD-006 | inconsistent | Nit | A wrong statement (node not on PATH) is kept next to its correction: `handover/demo/outsider/SUMMARY.md:36 "Correction added by the lead session"` | none | OTHER |
| L4-FD-007 | duplicate | Major | Version chains of patches and notes: sonar 44, triage 48, semgrep 16, skips 11, fixes 6, coverage 3 patch files; many replaced versions are kept: `handover/demo/fixes/PLAN.md:2 "v3 kept as docs-and-deps-v3.patch"`; `handover/demo/skips/CRLF-GUARD-V7-NOTES.md:3 "It REPLACES v6"`; `handover/demo/real-run/FIXES.md:19 "replaces nothing: v1 is kept"`. Proposal: ARCHIVE replaced versions after the owner says yes; which are applied is in APPLY-LIST.md (L1) | none | OTHER |
| L4-FD-008 | duplicate | Major | My md5 compare of all lane files finds 56 groups holding 140 byte-identical files (examples: real-run/REVIEW-v4-fresh.md and REVIEW-v4-fresh-copy.md; four identical codeant n8n-proof patches in triage; 13 identical .exit files; many identical layout PNGs); coverage/evidence-coverage.xml and evidence-r3-coverage.xml are 260948 bytes each but differ. Command: md5sum, read-only | none | OTHER |
| L4-FD-009 | idle | Major | layout holds 378 PNG files, uncurated sweep output: `handover/demo/layout/SUMMARY2.md:7 "raw sweep output (tag names base/after1/tryB...), not curated"` | none | OTHER |
| L4-FD-010 | unverified | Major | No evidence in this lane that n8n was ever run: `handover/demo/integration/INT-2b.md:10 "a real n8n"`; `handover/demo/stranger/SUMMARY.md:75 "n8n workflows"` | none | OTHER |
| L4-FD-011 | inconsistent | Major | Evidence is tied to many heads (558d37f, 0841f36, f5fe824, b29bb1f, bee6fff, 2db3926, db54e13, 9c53207, 61ded9e); no file says which head is current: `handover/demo/integration/INT-1.md:11 "Heads verified"`; `handover/demo/scans/SCAN-TABLE.md:14 "2db392650e8b"` | none | OTHER |
| L4-FD-012 | security | Major | Hostile name text is stored raw and put raw in the mail subject; portal showed no execution but mail clients were not checked: `handover/demo/stranger/SUMMARY.md:11 "SURPRISE: HTML/script"`; `handover/demo/xss/SUMMARY.md:72 "The email rendered in a mail client"` | none | NOTICE |
| L4-FD-013 | security | Major | gitleaks finding TYPE generic-api-key at sonar-project.properties line 4 on branch main and 325 history findings on initial-code (types long-hex-token, hardcoded-hostname); no value recorded: `handover/demo/scans/SCAN-TABLE.md:11 "a0b97a4a6ee7"`; `handover/demo/gitleaks/SUMMARY.md:8 "sonar-project.properties line 4"`; fixed only by pending patch | none | FILTER |
| L4-FD-014 | unverified | Major | Windows and PowerShell scripts never ran: `handover/demo/skips/NEVER-RAN.md:8 "Nothing in section 1 has ever run on Windows"`; `handover/demo/integration/INT-2b.md:10 "Not run: PowerShell"` | none | OTHER |
| L4-FD-015 | inconsistent | Major | Docs and scripts disagree (D1 to D6) and limits.md burst text: `handover/demo/real-run/DRY-RUN-CHECKS.md:23 "Documentation says X but the script does Y"`; `handover/demo/stranger/SUMMARY.md:6 "MISMATCH (docs/limits.md"`; fixed only in pending real-run-fixes patch | none | OTHER |
| L4-FD-016 | unverified | Major | Semgrep claims without raw proof: `handover/demo/semgrep/SUMMARY.md:4 "exists nowhere"`; `handover/demo/semgrep/SUMMARY.md:3 "The Semgrep registry is blocked"` | none | FILTER |
| L4-FD-017 | security | Major | A program that drives a pseudo-terminal can still type the real-service host; approval file not built: `handover/demo/real-run/NOTES-start-prompt-v2.md:17 "A program that drives a pseudo-terminal"` | none | OTHER |
| L4-FD-018 | ops | Major | Desk reaper has unbounded wait loops (idle if desk is retired): `handover/demo/hang/RESULTS.md:48 "S:desk.py:652-654"`; `handover/demo/hang/RESULTS.md:49 "S:desk.py:655"` | DECISION line 15 | RETRY |
| L4-FD-019 | duplicate | Nit | INT-3 ran the same suite chunked then single-process with identical totals (3138 / 3 / 0): `handover/demo/integration/INT-3-2db3926.md:11 "SINGLE-PROCESS RUN"` | none | OTHER |
| L4-FD-020 | unverified | Nit | CI runner Node availability is inferred: `handover/demo/skips/SKIP-TABLE.md:13 "INFERRED, not verified"` | none | OTHER |
| L4-FD-021 | ops | Major | This lane is PARTIAL: READ 1, SKIMMED 1521, NOT-READ 137; patch files and md reports SKIMMED beyond the plan rule; NOT-READ md are reviews, notes and summaries (continuation lane needed): `handover/demo/hang/RESULTS.md:6 "NOT REPRODUCED"` | none | OTHER |
| L4-FD-022 | inconsistent | Nit | Receipt numbers skip without a doc note: `handover/demo/stranger/SUMMARY.md:9 "receipt numbers skip"` | none | COUNTER |

## Checkpoint
done: coverage statuses set (READ 1, SKIMMED 1521, NOT-READ 137) after reading the summary, plan, integration, hang, scans, xss, layout, stranger, outsider files in part; sections filled. next: continuation lane for the NOT-READ md reviews (reviews, notes, triage, sonar, semgrep, skips, real-run) and for opening SKIMMED md in full. blockers: 60 minute box; no runtime; lines cut at 400-700 chars in the files read.
