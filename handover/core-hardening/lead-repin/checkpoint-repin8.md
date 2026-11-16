# Checkpoint repin8 (see date in file mtime)
Done: v8 script copied from v7; env hygiene, control/bidi strip (pre and final stage), raw-< conversion, bare NAME VALUE, positional, entities, CDATA, double-escaped quotes, mask.fail, git status opt-in; 35 new value cases + machinery cases written. Canary (no meta) 1534/0 in dash and bash.
Running: full self-test (dash) in background.
Next: read result, counts, plants (24, dash + bash), non-root run, guide v8, v8-CHANGES.md.
Blockers: none yet.

## 17:55 UTC (23:25 IST)
Done: full self-test dash 1567/0 (seen as m04 survivor line). Guide v8 edited. Plant runner evidence-repin8/mutate8.py (40 plants: m01-m24 + n01-n16) running under dash and bash (two jobs at once to fit the time box).
Found: m04 survives (requirepass etc. now doubly covered by the new bare-name rule): to prove equivalent or kill. m10 plant made the start check refuse (exit 3): classified KILLED-startcheck.
Next: non-root runs (uid 65534), v8-CHANGES.md, banned-string scan, hand-back. Expect to run past 60 min by about 20 min; will say so.
Blockers: none.
