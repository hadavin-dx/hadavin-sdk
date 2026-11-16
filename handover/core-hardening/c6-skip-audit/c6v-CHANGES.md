# c6v changes (round 2 for c6u). Failures and open items first.

## Open items and failures (mine)
1. No EGM reviewer has read REPORT-c6v.md. The result review is the lead's step.
2. C-1 and C-1b are DONE on the scratchpad copy only and are UNVERIFIED against the real files. Nothing was applied to the real tree. No n8n run.
3. The older verifiers (c6r, c6s, c6t) were not re-run on c6v; their controls were ported into neg_ported_c6r.py, neg_new_c6s.py and neg_new_c6u.py (retargeted to c6v text). Some controls stayed PORT-SKIPPED (they are listed in neg-output.txt lines that say PORT-SKIPPED).
4. The five OPEN items and the two OPEN (OWNER ONLY) questions stay open: they need the owner or the studio lead.
5. Moving target: another session rewrote the owner sheets (now v34) and the release note (now v18) during my work. Release note lines 33 and 150 equal v14; lines 8 and 149 differ (line 8 drops the lease wording from the conflict list, line 149 ban item 11 drops "unless approved in writing"). The report states this and keeps G12 as an open gate; I did not read it as a decision. The build now stops with a clear message if lines 33 or 150 change.
6. My own slip: the c6v build asserted v14 equality and aborted after the v34/v18 files appeared (second run). Fixed in build_base.py. Also a row text kept "v30" as the newest sheet; fixed to the live version.
7. Heavy runs used: 3 full run_all.sh runs (the last one through heavy-slot.sh, slot wait in checkpoint-c6v.md).

## Finding to fix to check
| Finding | Fix | Check (verify_c6v_part3.py / part2) | Proof it fails on c6u |
|---|---|---|---|
| Design M1 G12 hold on carve-out rows | G12 hold added to the carve-out rows and L-LEASE row | class 1 must-exist phrases, L-LEASE No + G12 hold | verify-c6v-on-c6u.txt |
| Design M2 stale counts/versions | all counts/versions regenerated from the live folder | class 2: any count or version quoted twice is equal | c6u: "36 rows", v32 fail |
| Design M3 newest-sheet claim | conditional wording, check time regenerated last | part2 L-SHEET and check-time checks | c6u fails |
| Design M4 row 96 anchor | unique anchor, row 96 placed before row 12 (same line), pipe escaped | row rules (old text once, same-line order) plus W-row96 mutants | W- mutants |
| Design M5 box step 1 names tree; C-1 label | step 1 names the tree; C-1/C-1b labelled DONE on scratchpad copy, UNVERIFIED | UNVERIFIED label count check | class 2 |
| m1 to m4 | row 76 tag, row 96 time 35 s, stale run-sheet rows (row 94 anchor lengthened), L-APP2 listed unchecked in section 9 | class 6 (short old text occurs once) found row 94 | c6u class 6 fails |
| Naive M1 to M7, m1 to m12 | one status per open question, branch stated, counts and TASK numbers unified, G12 quoted one way with answer form, terms defined once, routes A/B, card words | class 2 wording checks, class 4 card-line copies | class 2 and 6 fail on c6u; class 4 only by changed copies |
| Box at most 2,500 words | body 2478 counted by script, whole box with heading under 2,500 | N5 box check, stated equals counted | T-E15/T-E16 mutants |
| Evidence: 24 of 103 mutations missed | classes 1, 2, 4, 6 added; about 50 W- mutants in neg_new_c6v.py | neg-output.txt | see verify-c6v-on-c6u.txt |
| Evidence: stale check time vs sheet | check time regenerated last by the build | check-time vs sheet-time check | by design |
| Evidence: symlinked steps-edits crash | run_all.sh and static-checks.sh exit 2 with MISSING INPUT message | tested by hand | n/a |
| Evidence: box word method | the box says body without heading is counted; whole also under 2,500 | verifier counts both | n/a |
| Banned strings | scan_c6v.py reads BANNED at run time | scan-c6v-output.txt | n/a |

Files: REPORT-c6v.md, c6v-CHANGES.md, checkpoint-c6v.md, evidence-c6v/ (all scripts and raw outputs).
