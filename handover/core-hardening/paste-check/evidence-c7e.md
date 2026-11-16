# evidence-c7e (raw, 2026-11-16). Evidence runner output, no verdicts.
Scratch dir: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c7e (a = real path, b = second copy for the v3-after-v4 try). Inputs copied from core-hardening/inputs/. Patches taken from paste-check/.
Step 6 note: the earlier extract_spans.py (C3) reads inline backtick spans, not fenced blocks, and was not rerun; instead /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c7e/tools/blocks.py extracts fenced blocks and runs bash -n and dash -n on the sh/bash ones. The powershell (and python) fenced blocks were not syntax-checked.
Step 5 note: patch residue in copy b: plan-wp6-resmoke-v5.md.orig and .rej (listed below).
```
## START sha256/mtime
9e8d06ddb5bb5b57e6a81c0493e2a449a918cfc2dfc13e988f82d32ce96584b8  plan-v5-fixes.patch
f65f2dbae2e50775f69fc19b2e2f676eb73fa243b3ab4a1ed521f7476e8be450  plan-v5-repin-v4.patch
8cf6bb2340b144c2c04ff6904999a7f41caaa0d1380f4bcf57e9015a80cd167b  plan-v5-repin-v3.patch
plan-v5-fixes.patch 1794820632
plan-v5-repin-v4.patch 1794823049
plan-v5-repin-v3.patch 1794822472
$ patch --dry-run -p1 < plan-v5-fixes.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 < plan-v5-fixes.patch
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch --dry-run -p1 < plan-v5-repin-v4.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 < plan-v5-repin-v4.patch
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
(b: fixes applied rc=0)
(b: v4 applied rc=0)
$ (b) patch -p1 < plan-v5-repin-v3.patch  AFTER v4
patching file inputs/plan-wp6-resmoke-v5.md
Hunk #1 FAILED at 1.
Hunk #2 FAILED at 16.
Hunk #3 FAILED at 69.
Hunk #4 FAILED at 106.
Hunk #5 FAILED at 117.
Hunk #6 FAILED at 149.
Hunk #7 FAILED at 223.
Hunk #8 FAILED at 252.
Hunk #9 FAILED at 410.
Hunk #10 FAILED at 427.
Hunk #11 FAILED at 440.
Hunk #12 FAILED at 463.
Hunk #13 FAILED at 488.
Hunk #14 FAILED at 508.
Hunk #15 FAILED at 556.
15 out of 15 hunks FAILED -- saving rejects to file inputs/plan-wp6-resmoke-v5.md.rej
rc=1
AGENT-SCOPE-DO-AND-DONT.md
DECISION-one-store.md
DECISIONS-2026-11-16.md
FACTS-ALREADY-DONE.md
OWNER-STEPS-realrun-v3.md
plan-wp6-resmoke-v5.md
plan-wp6-resmoke-v5.md.orig
plan-wp6-resmoke-v5.md.rej
## final plan sha256
33220b1517015d7824256c079362990a271836501ac60c98b24ce3978d416c7a  /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c7e/final.md
## counts
<pid>: 10 occurrences, 3 lines
<folder>: 7 occurrences, 3 lines
LEAD-FILL: 23 occurrences, 11 lines
$ python3 -I blocks.py final.md
fenced blocks total: 14 langs: ['bash', 'powershell', 'python', 'sh']
line 134 lang=sh lines=28: bash -n rc=0; dash -n rc=0
line 167 lang=sh lines=5: bash -n rc=0; dash -n rc=0
line 176 lang=sh lines=13: bash -n rc=0; dash -n rc=0
line 215 lang=bash lines=5: bash -n rc=0; dash -n rc=0
line 248 lang=sh lines=8: bash -n rc=0; dash -n rc=0
line 285 lang=sh lines=2: bash -n rc=0; dash -n rc=0
line 291 lang=sh lines=5: bash -n rc=0; dash -n rc=0
line 331 lang=sh lines=1: bash -n rc=0; dash -n rc=0
line 352 lang=sh lines=4: bash -n rc=0; dash -n rc=0
line 360 lang=sh lines=15: bash -n rc=0; dash -n rc=0
line 385 lang=sh lines=15: bash -n rc=0; dash -n rc=0
line 419 lang=sh lines=1: bash -n rc=0; dash -n rc=0
## END sha256/mtime
9e8d06ddb5bb5b57e6a81c0493e2a449a918cfc2dfc13e988f82d32ce96584b8  plan-v5-fixes.patch
f65f2dbae2e50775f69fc19b2e2f676eb73fa243b3ab4a1ed521f7476e8be450  plan-v5-repin-v4.patch
8cf6bb2340b144c2c04ff6904999a7f41caaa0d1380f4bcf57e9015a80cd167b  plan-v5-repin-v3.patch
plan-v5-fixes.patch 1794820632
plan-v5-repin-v4.patch 1794823049
plan-v5-repin-v3.patch 1794822472
```
banned-word scan of evidence-c7e.md: 0 hits (list read from tests/test_no_reference_material.py BANNED; word not printed)
