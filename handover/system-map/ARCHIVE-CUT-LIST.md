# Archive cut list (M8) - ARCHIVE, NEVER DELETE. Nothing here is moved yet.
Status: PROPOSED. Written 2026-11-16 (UTC). Source: a read-only structure audit (work/evidence-m8-structure.txt plus the manifest lists). Not verified: this checkout is not a git repository, so which files are tracked, sizes of the screenshot folder and which patch round is final were NOT checked.
Words: archive = move to archive/<same path> after the studio head says yes; patch = a file of code changes for another repository; round = one review-and-fix pass.
Facts: about 131 of 133 MB in the list sit under handover/. Moving files does not shrink the clone; only a history rewrite would (every commit id changes, needs the studio head's yes). CI fails if files exist under handover/reviews, handover/tickets or handover/evidence directly below handover/ (ci.yml 207-222): archive/handover/evidence/... is safe. No test reads any path below. Files over 1 MB: handover/demo/pr-stack/raw-pulls-4-comments.json (3.79 MB), handover/demo3/evidence/raw/q3c-round-logs.tgz (2.26 MB), q3-round-logs.tgz (1.66 MB).
Decision per row: studio head says yes; for a session's own files the laptop lead confirms no open pull request text points at them. Citations in handover/system-map would then point at a missing path: update or accept archive/.
| Row | What | Size | Why | Check first |
|---|---|---|---|---|
| A | handover/demo3/evidence/lane3-fix-2 r3 to r11 patches (keep r12 and r13) | at least 5.6 MB | replaced by newer rounds | last lines of handover/demo3/register.md say which round is final |
| B | lane3-fix-10 r2 to r5 patches and r3/r4/r5-parts (keep r6 and r6-parts) | at least 1.3 MB | replaced; parts duplicate whole patch | same |
| C | lane3-fix-1 r2 to r5, lane3-fix-5 r8 to r10 (keep fix-1 r6, fix-5 r11) | about 0.9 MB | replaced | same |
| D | handover/demo3/evidence/REPORT-archive-2026-11-14.md | 377 KB | says it is an archive | three session files name it |
| E | raw/q3-round-logs.tgz, q3c-round-logs.tgz | 3.9 MB | largest binaries; summaries in crash-soak*.md carry the findings | the evidence authors confirm nobody re-checks the rounds |
| F | handover/demo/pr-stack/raw-pulls-4-comments.json | 3.79 MB | raw copy of what GitHub holds | AB-PAPER.md not read line by line |
| G | handover/demo/semgrep/main-61ded9e and -v8 (keep -v9), pr-text/semgrep-pr-claims-v6.md | not totalled | replaced by v9 | 15 hits in demo/REPORT.md |
| H | demo/fixes docs-and-deps*.patch except v4, PLAN-v2-pillow-draft.md; demo/followup v2-DO-NOT-USE, followup-ab, -a, -b | not totalled | replaced; one labelled do-not-use | apply-matrix evidence files name them |
| I | demo/pr-text/proposed v1 to v4 | small | v5 replaces | 2 hits |
| J | demo/layout before-*, after-*, after1-*, afterB-* screenshots (keep afterB2, SUMMARY2.md) | tens of MB, not totalled | earlier rounds | names in REVIEW-1.md |
| K | handover/demo3/scratch/ | small | throwaway test inputs; two copies identical | hostile-*.log print these paths |
| L | demo3/evidence/raw *.partial.log, *-interrupted.log, *-invalid-* | a few MB | unfinished runs | summaries cite some |
| M | handover/CLOUD-EGM-SETUP-2026-11-12.md | small | written for a retired session | none found citing it |
Not recommended to move: handover/system-map/DECISION-one-store.md (cited by line from tools/write_outputs.py), tools and tests, handover/BRIEF-PREAMBLE.md, MODEL-ROUTING.md, handover/tools/. The four .pyc files under system-map: add a .gitignore line instead.
Also found: CLAUDE.md step 1 names files that are not in this checkout (handover/README.md, STUDIO-RULES.md, STATUS.md, studio-notes/, ledger.md); handover/evidence/ and promotion-inputs/ are cited but absent. Same-name different-content pairs (demo/ORDERS.md vs demo3/ORDERS.md; the two DECISION-one-store.md) are NOT duplicates.
