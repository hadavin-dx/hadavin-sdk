# DOCS5 notes (fix of root docs style review 4)

Branch wip/cloud-core-c/docs5 from origin/cloud/core-c 579d0815d. Docs only; no heavy tests.

## Applied
- B1: no Kn in CHANGELOG or README; the two mentions now point to SECURITY.md by section and by gap title.
- B2: removed "main line", "progress line", "fix round", "review round", "frozen plan", "the builder's figure", "team note", "the lead" from shipped text. Facts resting on unshipped notes are labelled STATED (kind of source and date) or UNVERIFIED (no result line / no run on file). K19 now names its source: the table of calls kept outside the gate in tests/test_gate_install_callers.py. "main line" became "the released code" (appendix entry renamed).
- B3: CHANGELOG top note narrowed to the wording given. tests/test_no_reference_material.py banned list (domain names and product-UI phrases) does not touch it.
- M4: new gaps K24a, K36a, K67a, K70a, K74a, K82a, each with one Status, Evidence and owner. Every gap block now has exactly one Status line (script check). No "K1-K85" range or 4.x count table exists in the root docs, so nothing else to renumber; the appendix entry for Kn explains the letter suffix.
- M5: section 1 points to K46 and K84 and carries no status.
- M6: sentences over 30 words split in SECURITY.md (2.0, K36, K50, K73, K85, 2.7, appendix), README (decode entry) and CHANGELOG lines 1-117 where cited or found by a scan.
- M7: verified in code: `defaults.MAX_DOCUMENT_BYTES = 262_144` (config `max_document_bytes` default, ceiling `MAX_REDACT_CHARS` = same value); `runmap.MAX_DECODED_MASKS = 256` (pairing across decoded views, secret finder); `ENFORCE_MAX_HELD = 4096` and `ENFORCE_MAX_ENTRIES = 20,480` (gate). CHANGELOG now states the document default once (restored-input hash key entry); the older 1048576 entry points to it. The 256 is named as the finder's pairing limit; K64 says the gate's old cap of 256 is gone and the finder's separate 256 stays.
- M8: UNVERIFIED added where a figure had no run on file; Python 3.13 headline in README labelled; the 5-working-days line labelled STATED target and UNVERIFIED record.
- Nits: appendix no longer claimed unique; K84 pointer in section 1; internal dated deadlines replaced by "Default that applies until the owner decides: ..." for K14, K26, K29, K31, K55, K69 and README waiver (K26 and K29 default text kept: tightened); `k1b` explained; wrong "next entry" pointer fixed; K85a "Evidence: NONE" replaced; README Limits heading widened.

## Not done
- CHANGELOG lines 118-129 and 230-812: sentences over 30 words remain (not cited by the review); "lead" and "review round N" wording remains in older fold entries other than the lines named above.
- Owner questions stay OPEN (K14, K26, K29, K31, K35, K36a, K55, K69, K70a, K74a, K83, K85a).

## Tests
- `-k "changelog or security or readme or brand or docs"`: 71 passed, 1 failed (vendor-string test, only on handover/BRIEF-PREAMBLE.md, the lead's file). The 72 in SECURITY.md 2.0 still holds.
- The 5 tests that read CHANGELOG.md (test_k5_fixes4 merge order; test_mutation_runner and test_textnorm manifest pins; test_textnorm coverage sentences and docstring wording; hindi script view) plus tests/test_textnorm_meta.py: 21 passed.
