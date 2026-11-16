# fix-f003-r5 (F-003 patch, round 5)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-f003r5/F-003-runsheet-claims.patch
Edits (in place, line count unchanged, hunk @@ -1,90 +1,108 @@ recounted with awk: old 90, new 108):
1. Rehearsal item 11: no literal 10 s; "note the reply time; any limit is set by the studio lead at rehearsal (QUESTIONS.md Q25 item 3); it is not part of the claim".
2. Scene 1, 3 and the line-18 bullet: "last producer note" now names the note "Where the older numbers came from".
3. That note: "V7 FINAL first table T14" is now "first table of V7-NUMBERS-lead-read.md, T14".
4. Scene 4 bullet: lease counts from the start-marker row (first INSERT, mf-form.json:97, checked), not from the stop.
5. Residue-section line: lists what changed (est., studio-lead-read, "= 22:20 IST" in row 9, owner's clock wording).
Not reproduced: doubled full stop after a closing quote (no such text found in the patch).
FINDINGS.md F-003 and LEDGER-ROWS.md row 4: no changed statement repeated; not edited.
Checks: check_patches PASS 4 patches; check_secrets PASS; check_refs PASS 5146; ruff All checks passed; check_counts PASS 52 files / 655 nodes.
