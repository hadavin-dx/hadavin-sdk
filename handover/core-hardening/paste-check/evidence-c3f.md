# evidence-c3f (raw, 2026-11-16). Builder output, no verdicts. Test copies live in the scratchpad; the real inputs/ file was not edited.
## 1 patch apply order, fresh copy of inputs/ (patch -p1)
$ patch -p1 --dry-run < paste-check/plan-v5-fixes.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ real apply fixes
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 --dry-run < paste-check/plan-v5-repin-v3.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ real apply v3
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ cmp result vs build copy v3
cmp rc=0
$ order check: v3 dry-run on the ORIGINAL plan (fixes not applied), expected to fail
Hunk #13 succeeded at 489 (offset -2 lines).
Hunk #14 succeeded at 509 (offset -2 lines).
Hunk #15 FAILED at 559.
5 out of 15 hunks FAILED
rc=1
$ real inputs/ untouched (sha256 vs ap2 copy)
67a0a195537de875  /home/user/hadavin-sdk/handover/core-hardening/inputs/plan-wp6-resmoke-v5.md
67a0a195537de875  ../ap2/inputs/plan-wp6-resmoke-v5.md
$ grep -c placeholders on patched plan
FINAL lines: 24
LEAD-FILL lines: 10
$ lines with FINAL placeholders
      3 2;      3 121;      3 236;      1 517;      1 519;      1 520;      1 521;      1 522;      1 523;      1 524;      1 525;      1 526;      1 527;      1 528;      1 529;      1 530;      1 531;      1 532;      1 533;      1 534;      1 535;      1 536;      1 537;      1 538;
$ stray blank between UNVERIFIED 11 and 12?
563-11. Round 5 (`nlite-fix5`, branch `take/nlite-int-r5`): 
564:12. That the installed Docker CLI accepts `docker run --
$ names check command
2 2 2 2 3 3 3 3 3 3 77 77 121 236 495 515 515 563 563 566 566 568 
