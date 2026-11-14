# checkpoint b17 (fix-10 r2)
- 05:33Z (real date -u): tree /home/user/work/b17-tree = r1 patch + r2 edits. Done: formatter+scrub (rows 1,5), server 8 sites on one formatter, exit-code table (lead override: desk 4, scripts 8), start_all.sh/.ps1 bounded wait (row 3), rows 7,9,10,11,13,14, guard (6), ps1 reader split + pins (8), contract/settings docs. Tests written first; base-tree before-run saved (raw/b17-behaviour-before.log). 391+3+18 new tests green on 3.13.
- Next: mutation run (raw/b17-mutation.log), ONE full run on final head, patch + notes.
- Commit SHA: none (not committed, git add -A only).
- 05:41Z full run started on final head (3.13), log raw/b17-full-final.log; no edits to the tree while it runs

## 05:59Z final
Patch re-cut from the final tree (sha256 0d762d13), notes written, no processes of mine running. Full run: 2 failed (own test hygiene, fixed), 4125 passed, 171 skipped; targeted re-run 456 passed. Row 15 (ps1 never run) escalated. Handing back.
