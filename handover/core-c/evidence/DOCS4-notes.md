# DOCS4 notes (style review 3 fixes)

Branch wip/cloud-core-c/docs4 from origin/cloud/core-c. Edited SECURITY.md, CHANGELOG.md, README.md.

Done: all 9 Majors and the cheap Nits in new material. Term "secret finder" in SECURITY part 1 (note at part 1 start kept true; README and CHANGELOG keep "redactor"). 2.9 dangling pointer reworded; K46/K84 pointer for the correction; stated order is STATED not NONE; lead-ins fixed in 2.3 and 2.7; internal artifact names replaced by kind and date; `k1b` explained once as a real config key; product config values covered by one stated exception in the CHANGELOG top note; four-step upgrade item numbered; long sentences split; PINNED and OPEN defined; ledger test labelled PINNED; "refused" lower case; second OPEN notes moved to their own OPEN line (K70, K74, K36); K82 and K85 wording; METADATA_ENDPOINTS duplicate removed; TID251 dropped from new text; blank line before Upgrade steps; pointer from "256 values" to K64 (256 is MAX_DECODED_MASKS in runmap, a different limit from the gate's K64 limits).
The 19 in 28/7/19 is explained from handover/core-c/SECURITY-README-v7.md (19 host-name strict expected failures); the 28-7=21 gap of two rows is marked UNVERIFIED.

Left alone: old entries of CHANGELOG (lines about slack and bedrock_guardrail in earlier sections, TID251 in the fold ban rule entry which tests pin), SECURITY table row 577 (table cell). Owner questions stay OPEN.

Tests: docs/brand selection 71 passed, 1 failed (vendor-brand test: handover/BRIEF-PREAMBLE.md, and handover/core-c/evidence/DOCS3-notes.md which quotes vendor strings; the second is a file of the earlier docs round, not changed here). CHANGELOG pin tests selected by name (5) and test_textnorm_meta.py (15) passed.
