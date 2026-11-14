# checkpoint B22 (lane3 fix-2 round 9)
Written 2026-11-14T07:05Z (started 06:53Z).
Done: tree b22-tree reproduced (812a97a before changes); tests first (79 failed on the r8 tree, 0 function-absent: raw/b22-fails-before.log); rows 1-18 applied; lint on a clean copy of the index all rc 0 (raw/b22-lint-*.log).
Next: changed test files + hygiene + wall-clock guard alone, mutation, patch cut, notes.
Blockers: none. Not run as root-able: the chmod-000 test skips as root (CORRECTION 07:20Z: when this line was written the monkeypatched twin did NOT exist yet; mutant M14 survived and exposed it; the twin test was added afterwards and now kills M14).

07:20Z final: all steps done; see lane3-fix-2-r9-notes.md. Final tree 151f9eff50eb3a4a523cba11fcf1dd811e448719.

r10 (lead's message after the r9 review): done; final tree 1c973634c77ef0ddb214b4f101a1aa405a8cb8b8; see lane3-fix-2-r10-notes.md.
