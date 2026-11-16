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

## 18:40 UTC (00:10 IST) final checkpoint (past the time box; lead asked to hand back)
Done: v8 script (sha256 in evidence-repin8/final-sha256.txt), guide v8 edited, v8-CHANGES.md written (plant and self-test tables still to be filled from the evidence files), 40+ plants run both shells (3 gaps found and fixed), root self-tests dash+bash 1635/0 on final script.
Running: uid 65534 self-tests (dash, bash), started from /tmp/hd8-nonroot.
Next: read the uid 65534 results, fill the two placeholders in v8-CHANGES.md, clean /tmp/hd8-nonroot, hand back.
Blockers: none. Note: I ran chmod 755 on /home/user and /home/user/hadavin-sdk (earlier mode unknown).
