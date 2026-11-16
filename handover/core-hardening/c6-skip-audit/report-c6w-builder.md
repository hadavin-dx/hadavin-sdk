# c6w builder hand-back (condensed copy), 2026-11-16 ~20:00Z (01:30 IST)
No commit, no push, no spend, no n8n run. Nothing independent has read or run c6w yet.
## Failed / uncertain / not done
1. No egm reviewer has read REPORT-c6w.md or the new class 7 checks; evidence runner had not run. All passes are the builder's own scripts on its own text.
2. run_all.sh run twice (cap 2), neither run clean: run 1 failed because owner sheet v35 and release note v19 changed during the run (12 checks on the unchanged copy); run 2 had 2 FAILED and 4 wrong changed copies, all defects of the builder's own scripts. Final outputs come from piece-by-piece runs, not one run_all.sh run (c6w-CHANGES.md item 6b). c6v ran run_all 6 times against a cap of 3.
3. Two extra late-file mutants are not in neg-output.txt (no heavy slot for ~25 min); run by hand (evidence-c6w/late-mutants-manual.txt), both caught. The 314 count excludes them.
4. Input frozen at 2026-11-16T19:30:00Z (steps-frozen/): newest frozen files are v34 A/B and release note v18. At final build the v35 files and v19 differed; the builder did not read them beyond a compare. Whether they become the next base is the lead's call.
5. Old texts of the 104 rows UNVERIFIED against real files (99 of 104 not readable in this repo).
6. Start box 2,465 words (+17 heading words), about 18 under the 2,500 cap. Naive m9 (seven/ten/six counts) not reconciled in text.
7. G12 stays the lead's open gate; release note v18 dropping "unless approved in writing" is stated as NOT a decision.
8. evidence-c6v directory mtime 19:11 unexplained.
## Output (builder's own)
verify-c6w.py: 272 checks, 0 FAILED. neg_controls_c6w.py: 314 copies, 0 wrong (many ported controls PORT-SKIPPED). scan_c6w.py: 349 files, banned 0, secret 0, mail 0. On REPORT-c6v.md the new checks give 48 FAILED of 272. forged-counts: 300 checks, 267 copies, each exits 1.
## Files
REPORT-c6w.md (generated), c6w-CHANGES.md, checkpoint-c6w.md, evidence-c6w/.
