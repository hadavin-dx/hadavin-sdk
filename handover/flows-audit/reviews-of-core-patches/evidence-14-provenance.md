# evidence-14-provenance (round 22 fixer, raw output; run 2026-11-16 14:50:05 UTC at repo root; static commands only)

$ git rev-parse --is-shallow-repository
true
exit=0

$ git cat-file -t b4cce5b
commit
exit=0

$ git cat-file -t 176a0cbe0
commit
exit=0

$ git rev-parse HEAD
76c01f662fcddff71e3b96b2dcbe5d601725edfc
exit=0

$ git rev-parse --short=9 HEAD
76c01f662
exit=0

$ git diff --stat 176a0cbe0 HEAD -- src tests
exit=0

$ git log -1 --format=%H%n%cI HEAD
76c01f662fcddff71e3b96b2dcbe5d601725edfc
2026-11-16T14:49:22+00:00
exit=0

$ cat .git/shallow
fda633bbb3fc2427cf68f97ec6b4037f73736539
exit=0

$ git merge-base --is-ancestor 176a0cbe0 HEAD
exit=0

$ git reflog --format=%h | grep -c b4cce5b
0

$ git merge-base --is-ancestor b4cce5b HEAD
exit=1

$ git merge-base --is-ancestor b4cce5b 176a0cbe0
exit=1

$ git rev-parse b4cce5b
b4cce5b6ae80b45125604b8295ebb35bd2ea1c2c
