# DOCS2 notes (style fixes of the root docs, after DOCS-style-review-1)

Branch wip/cloud-core-c/docs2 from origin/cloud/core-c (217846238). Docs only; no code or test changed.

## Done
- CHANGELOG Unreleased: new "Breaking changes" subsection first (stage rename, client-profile refusals, upgrade steps for an existing database with the Store API change, the removed public name, a pointer to the new required pilot/prod settings). Long bullets split into one sub-bullet per behaviour. Ticket and phase codes (E14, E9(2), P1d-a, P2d-1, G3, GAP-1, P1B-1, VARIANT-1, K5-core, K1b-lite, K7) replaced by descriptions. SonarCloud, the vault licence research note and the model name in the replay smoke-run entry removed. "round 5 of the call" now reads 5 rounds in total, refused if still changing in round 5.
- README: Python-version section rewritten (pin stated once, CHANGELOG pointer made precise, unwired DENY side moved to its own section), Limits and trust rewritten in sub-bullets with labels linked to SECURITY.md, no Kn, K7 and R365 and K5-ITO described in words.
- SECURITY.md: glossary moved to an appendix ("Words used here", anchor kept); block above the date line; unlabelled 2.0 lines labelled; the two contradicting lines on failures fixed (2 failed: vendor-string test and a re-keyed recording); missing "4.2" replaced by a real table, section 2.10; K35 now OPEN (acceptance order not found); K80 split into K80 (STATED), K80a (FIXED), K80b (PINNED); K85 split into K85 (PINNED) and K85a (OPEN decisions); "the lead" became "the owner"; "Slack" and "chat service" strings removed; 4 sentences over 30 words fixed.

## Numbers checked
- 960 MB / 9 s vs 956 MB: tickets/E14-finder-memory-cap.md section 2.2 table (MEASURED, redact_many, 8 x 260,000): 960 MB peak, 9.17 s, "E14's 956 MB traced: same". evidence/G7-1.md line 671 printed 956.0 MB (and 37.7 s on a loaded run, a different harness). Docs now say about 960 MB and 9 s, with 956 MB named as the other recorded run.
- Base64 depth: defaults.B64_MAX_DEPTH = 3 (runmap.py 776 stops at depth >= 3). K37 now states 3 levels; README and CHANGELOG already did.
- Rounds: redact.py `_SETTLE_ROUNDS` = 4 repeat rounds after the first pass: 5 in total.

## Not done / left
- Older CHANGELOG entries by other sessions (e.g. line "Changed (G10 ... ORDER 023 ...)", slice headings P3/P9, HashiCorp Vault in an older kind entry) were left as written.
- K3/K6/K8 in the older "pilot build path" entry (about 119) left; the meaning of those codes is not defined in the shipped text and should be rewritten by whoever owns that entry.
- Tests: "Tests:" tails not shortened. Glossary bullets were split mechanically at "Term:" boundaries.
- Whole-suite not run (cheap doc tests only).

## OPEN (owner decisions, not decided here)
- K35 acceptance (find or confirm the order), K85a (letter-only minimum, own refusal code, cap of 4,096), the finder memory limits, the K70/K71 defaults, whether a host-name note goes to clients, the runtime-role waiver, K14, K26, K29, K31, K55, K69, K83 (all with their existing dates).

## Test results
- `pytest -k "changelog or security or readme or brand or docs"`: 71 passed, 1 failed (vendor-brand test, only handover/BRIEF-PREAMBLE.md, the lead's file).
- CHANGELOG pin tests in test_textnorm.py, test_mutation_runner.py, test_textnorm_meta.py, test_k5_fixes4.py, test_k1b_cli.py, test_stage_names.py: 107 passed.
