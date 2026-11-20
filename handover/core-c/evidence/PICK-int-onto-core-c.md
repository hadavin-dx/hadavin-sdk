# PICK-int-onto-core-c (worktree /tmp/core-c-pick, branch wip-pick, cut from cloud/core-c bd4446c)

## Progress note 1 (pick complete, batch NOT yet run)
55ed2c4 code G: integration step 5: mutants A3, A3b follow the moved code, A11 killed by a tag-split-only row, A43 by the undefang row
ea8d615 code G: integration step 4: clean re-reads once through one shared function with a fixed note past the bound, no check pass when nothing changed (channel.py / slack_channel.py, SPINE-owned)
14b582a code G: integration step 3: bound the glued-address search (M1), the e-mail test asserts no leak (M2), tail check M7, tag-split row N3, stale N4 exemption
651ab9e code G: integration step 2: A43 row test, clean() re-read cap test, glued e-mail regression and the glued-rest probe of the other value kinds
af7d8d1 code G: integration step 1: redact.py imports and is ruff-clean (G7 second pass + P1d-a _sub_glued + G3 fold scan); typography tests, text-parts test (draft)
1739322 code G: integration of G2 + G3 with G7, INTERRUPTED by the model limit, NOT verified
6ddd053 code G: G3 step 6: adapt the fold scan to fold5 after the first batch; fold-head record tests updated
880a204 code G: G3 step 5: the redactor counts its own actions (RedactionResult.actions) and the test of review finding cb-1-1
604d184 code G: G3 step 4: re-pin after the port (manifest hash of textnorm.py, CHANGELOG re-copy list and entry)
651bd16 code G: G3 step 3: P2d-1's fold-scan tests brought over (six new files, the fuzz row) and shared test files adapted
4fe639e code G: G3 step 2: port the fold scan of P2d-1 (76adadb) into guard/redact.py; runmap views and CPU-time deadline
5be932c code G: G3 step 1: textnorm names for the fold scan (fold_view, without_spacing_marks, SPACING_CATEGORIES; weight memo)
46060cd code G: G2 fix: mutant list follows the moved snippets (A2, A11, A3d), new mutant A2s, one more undefang assertion
a97b91d code G: G2 fix (channel.py, SPINE-owned file): clean re-reads its result until it is stable, FakeChannel.send undefangs
34e14bb code G: G2 fix: defang every dot of a host token, glued e-mail addresses masked in one pass
9e14e71 code G: G2 path tests: redact then defang on every approval text path, stored request, SECRET pattern timing
0806565 code G: G2 P1d-a defang after the redactor, SECRET pattern fixes (INFO-K41)

Skipped (already on cloud/core-c): 29cc926 (T1 tests, identical files already there), 4a8406a (cherry-pick of G7 4864984, the base).
Conflicts: 181ab0c -> 4fe639e redact.py (_decide: None for leave-alone, hardened _OWN_OUTPUT rule kept, _ESCAPED_LOOKALIKE block dropped), runmap.py (took cloud/core-c file, re-applied: import without_spacing_marks, two extra views, _decoded_masks deadline, thread_time + _deadline in redact_text; enforce_map/snapshot/nfkc/undo untouched; is_masked/_scan stay deleted); 56c876c -> 880a204 redact.py (settle([text],[sweep]) + actions=r.actions). redact.py diff vs integration tip is only the hardened own-output rule.
