# checkpoint B19 (lane3 fix-2 round 8)
Written 2026-11-14T06:37:03Z (started 06:06:52Z; 30-minute checkpoint).

Done: tests first (75 failed / 21 passed on the unchanged tree, all behavioural, none function-absent: raw/b19-fails-before.log); read_secret_file (mode, lstat, inode, link text); Retry-After clamp in the three copies; umask fixture; guards rebuilt (src covered, keyed allowances, reader/probe/Retry-After/shell additions); docs in one section of docs/settings.md; older pins re-pointed; mutation check all killed (raw/b19-mutation.log); patches and parts cut and apply-checked (tree eb5e171...); notes written.
Running: the ONE full run on the final head, clone /home/user/work/b19-full, started 06:29:18Z, log /home/user/work/b19-logs/b19-full-final.log (about 35% at 06:36Z).
Next: copy the log to raw/b19-full-final.log, run the wall-clock guard test and the hygiene scan test alone, write raw/b19-patch-sha256.txt, hand back.
Open: 13 lines over 120 by plain awk (pre-existing lines with a pragma tail, not wrapped on purpose; see notes row 4).
Blockers: none.

## 06:50Z update
Full run ended 1 failed / 4348 passed (hygiene scan on 4 lines of r7 test text); fixed; hygiene + wall-clock guards alone rc 0 on tree 812a97a; r7+r8 349 passed; patches, parts, sha file recut and apply-checked (both patches give tree 812a97a). The 13 long lines are base text, evidence per line in notes row 4. Stopping: nothing running.
