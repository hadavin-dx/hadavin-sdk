# patch-copies README lines 330-663 round 22b stranger read (egm-comprehension), security path, uncapped. Saved by flows-audit, condensed; unverified; static; nothing run. NOT read: 1-329, 664+. 0 Blockers (no path found to PASSED after a failed step; no write/delete outside $W or keep folder). 7 Majors, minors.
M1 L358/357/364/412 instructions mixed with pass history; L364 "verdict never ran in one complete run; (e) may print false FAILED on first real run" (also L557, 658) should be one up-front warning.
M2 cleanup mark-file rule contradicts: L415 "mark file setup wrote", L416 need_w tests setup.ok, L426/632 recipe.mark or patch.sha256.all, L427 keep_delete needs keep.mark; hand-set W: L416 "would also accept" vs L602 "not allowed" vs L582 keep_logs/cleanup only.
M3 L605-648 pasteable fence of OLD scrub/keep_logs/cleanup/keep_delete in history; old cleanup deletes logs unchecked, uses undefined $P. Mark do-not-paste or delete.
M4 L557 "13 new tests fail on old code" (earlier version) vs L380/396/439 13 of 32 current.
M5 L417 helper block position "between first and second block" vs history L588/604 (definitions used to sit in Cleanup); confirm.
M6 Undefined terms in range: RUNG, CODE-LAST, decision table row N, RV-A1/A3/A6/C3/C4/C6/C8/X2/X5/X6/G1, ORDER 009, G2-G5, HIGHENTROPY, WARDEN, K1bAudit, studio head, lead, fixer pass, round-10 citation check; "words box" (L504) vs "words table" (L535).
M7 $PY, $C, E, need_w, sg used in proof/final: confirm defined before L380 (L598 says gd and sg before verdict_run).
Minors: L663 times UTC only (19:12-19:50Z = 00:42-01:20 IST on 11-17); DISCARD_LOGS=yes stays set, add unset; "do NOT run verdict again after proof" four times; L354/356 "the diff"/"the table above" referents; "10 problems" L373 counts killswitch pyproject as 2; L392 uv run --locked vs earlier --offline; keep_logs folder K outside $W by design, say once.
Counts held: 24+6=30, 26+6=32, 12+18=30, 13+19=32, 9364+30=9394, 9364+32=9396, 7 and 8 files, 41=39-1+3.
