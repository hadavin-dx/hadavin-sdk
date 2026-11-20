# G12 build notes (trailing prose punctuation of a SECRET value)

Branch wip-g12 on cloud/core-c e75871df3 (G9, E14, G8, G10 merged). Code commits: 33f237201 (red tests), 9868c98b9 (fix in
`_Redactor._place` + `_TRAIL`), 24583be78 (tests/g12_mutants.py).

## Measured on THIS tree
- Leak before: `password=hunter22, hunter22` -> `password=<SECRET_1> hunter22` {SECRET_1: "hunter22,"}; same for `.` `)`; `authorization: hunter22hunter; hunter22hunter`.
  After: `password=<SECRET_1> <SECRET_2>` {SECRET_1: "hunter22,", SECRET_2: "hunter22"}; controls (`;`, space) unchanged.
- Phase 1: 20 failed / 4 passed (each red has its `G12-n ` id). Phase 2: 24 passed. Mutants: 7 of 7 KILLED.
- Property corpus (tests/test_redact_idempotent_property.py CORPUS): 1,836 inputs, `runmap.redact_text` outputs byte-identical before/after (same sha256 prefix a4318429872782f3).
- ruff check / format --check clean on src and tests; bandit -ll: no findings.
- Test run (-n 0): g12 + property + fold + g3_port + glued_rest + context_after_sweep + own_output_hardening + runmap_enforce_map: 2632 passed, 47 xfailed.
- tests/test_k5_perf.py -m perf: 8 passed (113 s under load). Per-shape base/G12 ratios NOT measured here (ticket's own table: <= 1.1x).
- Second batch (settle_loop, own_output, finder_cap, fold_seams, marks, k5_round7/8/12, e15, k1b, mutants_meta): one earlier run 320 passed
  (partly overlapped with a src checkout used for the before/after probe, so not authoritative); the clean re-run was SIGSTOPped by the lead's load cap: NOT RUN.
- Not run: tests/test_redact_mutants / redact_mutants.py, g8/G9 mutant files (Phase 6), full batch (Phase 7).

## Deviations
- Ticket Phase 4 names tests/test_p1c*.py and tests/test_b64*.py: no such files on this tree (p1c_builders.py is a helper).
- `​` escaped in the zero-width test case (ruff PLE2515); same string.
- Mutant runner `only_test` takes the bare function name, the parametrized id stays in `pinned`.

## Lead decisions 6.1-6.7: defaults built
6.1 reclassify E18 G7-F4 (probe built with a different value). 6.2 `_TRAIL = ".,;:!?)]}"`. 6.3 floor 3. 6.4 leading bracket not stripped
(`password=(hunter22), hunter22` still leaves `hunter22`: registers `(hunter22`; limit L-G12a). 6.5 small-capital fold to textnorm owner.
6.6 B-N4 widening accepted. 6.7 reverse direction stays P2d-2 open hole.
Interplay: only `_place` and `_TRAIL` (after `_PIECE`) touched in redact.py; E14 cap lives elsewhere (no `_place` check seen).

## G12b (result review round 1: M-1, M-2, N-1, N-3, N-4) - branch wip-g12b, code commit 36dfce4f3
- Design: ONE rule `_bare` (redact.py, replaces `_TRAIL`): at both ends strip non-alphanumeric characters (`str.isalnum`, Unicode too), markup tags
  (`<b>` leading, `</b>` trailing) and escaped `\n` `\r` `\t`; index based, last 64 characters only (linear). `_place` core = `_bare(full)`
  (guards unchanged: secret kinds, derived=True, core != full, len >= 3); `_decide` exempts `_bare(original).lower() in _NOT_A_VALUE`.
- Measured (scratch copies, `runmap.redact_text` + `redact().mapping`, 2,185 rows: property corpus 1,836 + g8 CASES and their `after` texts +
  the 5 k5 perf units at 16 KiB; sha256 over the property outputs, sorted ids; NOT the G12 hash method, so before = cc991f487cb13af3, after =
  c76c1c4f59c619c3): 20 rows differ, 16 of them only by a shifted placeholder number (a core took the number between two values); NO text lost or gained a
  mask except 4 perf units (`password= password= ...`: the value was the next key `password=`; now exempt because `_bare("password=")` is a listed
  word. Fewer masks, not more; the e2e perf test still scans them).
- Map entries before/after: 2,055 -> 2,141 (+86, +4.2%) over 96 changed rows, at most +1 per row; 5 rows -1 (2 fuzz rows where the value and its
  dot-wrapped copy now share one core; 3 perf units). Floor re-measured: 3 vs 4 differs in 2 fuzz rows only by a placeholder number (`k.8`); 3 stays.
- Not on the corpora: the over-mask of the both-ends rule is nil. Notes of G12 L-G12a (leading bracket) is CLOSED: `password=(hunter22), hunter22` masks both.
- Widening to know: the exemption now also reads `*none*`, `(null),`, `<b>true</b>`, `none\n` as "no value" (same rule as the core).
