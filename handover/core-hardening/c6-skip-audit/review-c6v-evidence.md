# c6v independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: c6-skip-audit/evidence-c6v-independent/ (00-TABLE.md). Run 19:06:49Z to about 19:28Z. Recorded, not judged. REPORT-c6v.md and c6v-CHANGES.md unchanged (md5 same before and after); build_base.py and build_c6v.py not run (they overwrite the report).

## Failures and deviations first
1. Live tree fails verify: verify-c6v.py gives 238 checks, 4 FAILED at 19:25Z. OWNER-SHEET-v34-A, -B and LEAD-RELEASE-NOTE-v18 have file times 19:14:05Z, after the report check time 19:04:44Z; content byte-identical to the 19:07Z copy (cmp); release note lines 8, 33, 149, 150 the same. "0 FAILED" holds for 19:04Z and the 19:07Z snapshot, not for the live tree (the builder's own staleness rule fires).
2. Neg run: 267 copies, 1 wrong, caused by the runner (deleted contact-grep-output.txt from its copy; V0-control-unchanged failed). With the file regenerated the unchanged report on the 19:07Z snapshot gives 238 checks, 0 FAILED. All 267 copies not re-run (slot wait 16.5 min); 0 SKIPPED lines.
3. verify-c6v.py on REPORT-c6u.md: exit 1 with 32 FAILs at 19:07Z (as claimed); 34 at 19:25Z (two extras are the file-time checks).
4. Builder's scan_c6v.py inside the runner folder gave mail 39 on 416 files on its second run, all in the runner's own copy of the sheets (example.com, example.net, single-character local parts at gmail.com); first run before the copy: 0/0/0 on 45 files.
5. Slot wait for the neg run: queued 19:07:12Z, slot 3 at 19:23:43Z (other agents held all three); the run took about 90 s.

## Builder claims vs seen
static-checks exit 0: confirmed twice (v34, note v18). verify 238 checks, 0 FAILED: 0 FAILED on the snapshot, 4 FAILED live. neg 267 copies, 0 wrong: 267, 1 wrong (runner-caused). scan 315 files 0/0/0: confirmed on its own files. verify on c6u 32 FAILs: confirmed at 19:07Z, 34 at 19:25Z.

## Scans (counts only)
BANNED (10 read at run time) and key-shape over 109 files: banned 0, key-shape 0. 28 mail-shaped hits, none real (pytest decorators, a version number, example.test/example.com/evil.test); 54 more on example domains excluded.

## Fresh mutations of REPORT-c6v.md: 19 written, 12 caught, 7 missed
Missed: I05 check time 19:04:44Z to 19:04:45Z in one of two places; I08 v34-A to v33-A in one sentence; I13 "Five items are OPEN" to "Four"; I14 release note "line 33" to "line 34"; I15 newest release note v18 to v17 in one sentence; I19 G12 hold removed from the L-LEASE row with word count kept; I20 G12 gate wording flipped from "cannot be filmed" to "can be filmed". Caught: row counts I01, I02, I12, I16; time pairs I03, I04, I21; card word count I07; dropped and duplicated row I09, I10; box word count I11; I06 (G12 removed with changed word count) only incidentally by the box word count (no G12 check fired). Forged numbers in c6v-CHANGES.md (I17 267 to 300; I18 6 runs to 3): no verifier parses CHANGES numbers.

## Not checked
Old texts vs the real files outside the copy (report says UNVERIFIED); EGM review; any n8n run; correctness of each of the 267 copies beyond OK/WRONG.
