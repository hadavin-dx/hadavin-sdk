# From core-a-merge: g2-p1d-a / g3-p2d-port onto core-c head (origin/cloud/core-c)

Result: all 4 non-patch-equivalent commits are SUPERSEDED. Nothing applied, nothing pushed (wip/core-a-merge-c == origin/cloud/core-c, no diff).
Conflicts in redact.py/runmap.py come from add/add of already cherry-picked commits; there is nothing left to merge.

## Per commit
- 73d624c12 (G2 fix: defang every dot, glued e-mails): SUPERSEDED. gate.py: _DOMAIN_LAST :257, _DOTTED_TOKEN :260, _NAME_DOT :261,
  _whole_token :265, fixed-point loop :278, _outside_code(certain=) :296-306, defang_text certain=True :315, _PLACEHOLDER_DEFANGED :318,
  _undefang_prose :321. redact.py: _NOT_ADDRESS :1115, _GLUED_WINDOW :1116, _Redactor._sub_glued :1406 (used :1314; core-c's version
  also bounds the end search by the window). Integrated by af7d8d1b3 ("G7 second pass + P1d-a _sub_glued + G3 fold scan"), tests in
  tests/test_redact_glued_rest.py, tests/test_p1d_a_*.py.
- 7de1c4f86 (G3 step 2: fold scan port, runmap views, CPU deadline): SUPERSEDED. redact.py _fold_scan :1480, _folded_line :1674,
  _aligned_fold :1574, deadline via time.thread_time() :1442/:1490 with defaults.REDACT_BUDGET_S; runmap._views :465, _decoded_masks
  deadline :509-522, one deadline shared :851/:911/:934; pyproject TID251 row for guard/redact.py :94. (Core-c is further: fold5, wall-clock M3.)
- 2be153143 (G3 step 4: re-pin manifest/CHANGELOG): SUPERSEDED, and re-applying would be WRONG: the pinned textnorm.py hash is stale since
  G10/M3. Head's manifest and CHANGELOG already hold the current hash 928a4247...c036945 (grep: 1 hit in each).
- 7d6b5fbff (G3 step 5: RedactionResult.actions + test): SUPERSEDED. redact.py RedactionResult.actions :1058, _Redactor.actions :1240,
  journal rollback :1743/:1761, increments :1665/:1778/:1787/:2095/:2536/:2713, redact() returns actions :1105;
  CHANGELOG.md:15 entry; tests/test_redact_g3_port.py exists at head.

## Final diff vs origin/cloud/core-c
Empty (no files).

## Tests (head only, since nothing changed)
pytest -n 2 -m 'not perf and not live' tests/test_redact_g3_port.py test_redact_glued_rest.py test_p1d_a*.py test_textnorm_meta.py:
682 passed, 46 xfailed, 2 failed = tests/test_p1d_a_rows.py::test_row_PU1_card and ::test_row_PU1_model (core-c's own; G4 view
holds extra entries, 54c461ff8 re-pinned the mutant but the rows still fail; not touched). Before/after identical (no change).
Mutant scripts not run: no code changed, so the summaries cannot differ.

## What core-c should delete or stop carrying
- wip/cloud-core-c/g2-p1d-a and wip/cloud-core-c/g3-p2d-port are redundant: do not merge them, do not carry them; delete after
  confirming. Merging either would regress core-c (stale textnorm hash, pre-G4..G13 redact.py/runmap.py).
- Separate, still open on core-c: PU1 row failures above.
