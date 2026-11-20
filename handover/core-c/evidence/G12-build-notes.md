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

### G12b correction (core-c review; supersedes the "Design"/"Widening" lines above)
- `_decide`'s exemption is UNCHANGED (old strip set): widening it unmasked `password=password=` (k5 perf units) and `none!`/`true-`/`null_`: a leak. Pins: those stay masked whole.
- M-1 is fixed in `_place`: no core when `_bare(full).lower()` is in `_NOT_A_VALUE`. Also no core when it is placeholder-like (`EMAIL_1`, `EMA`, from
  `password=<EMA`, `‹EMAIL_1›`): found by tests/test_redact_context_after_sweep.py e9 (4 red), pinned G12-18, mutant M18.
- Re-measured on the same 2,185 rows (scratch copies): rows with FEWER masks after than before: none; text differences beyond placeholder numbering: none (17 raw
  diffs, all renumbering); k5 perf units identical. Entries 2,055 -> 2,145 (+90, +4.4%, 94 rows changed, at most +1 per row; 2 fuzz rows -1).
- Tests: g12 file + property + g3_port + glued_rest + context_after_sweep: 2,760 passed, 41 xfailed (-n 2). One earlier run had glued_rest `underscore digits` linear (timing) red under load; green on the rerun. Mutants: 18 of 18 killed. ruff clean; bandit clean. k5_perf NOT RUN.

## G12c (result review round 2: B1, M1-M4, PRIVKEY/large value, nits) - branch wip-g12c
- B1: `python tests/g12_mutants.py` applies every mutant; NOVAL and PHLIKE `old` are now the two real lines (`core.lower() in _NOT_A_VALUE`, `or _placeholder_like(core, full)`), each once in redact.py. Whole file: 35 of 35 good (final, after the E9 round 3 narrowing).
- M1: PHLIKE is killed by the `<EMA` param (no `‹` in it); separate mutants remove the token guard (`12‹EMAIL_1›34,`), the cut-bracket guard (`‹SECRET_x›`) and widen the guard to any `‹` (interior test).
- M2 (leak, fixed): `_placeholder_like(core, full)` declines only (a) a core that is the text of a REAL placeholder (`_LABEL_TEXT`, built from `_LABELS`: `(?:EMAIL|...)_[0-9]+`) or (b) a core that is a label prefix AND `full` held `<` right before it (`<EMA`, `<EMAIL_`). Measured on the E9 tests by ablation: dropping (b) fails 10 (`<EMA`, `<EMAIL_`, 5 own_output_hardening, 2 context_after_sweep, 3 g12); dropping (a) fails 2 (`<EMAIL_1`, `<IPV4_12`); requiring the `<` in (b) fails none, so it is the minimum. Now registered, plain copy swept: `password=ADMIN_1, ADMIN_1`, `DB_PASS_2!`, `HOST,`, `SEC,`, `JWT,`. `password=API! API`: core registered but `api` is in `_COMMON`, a 3-char standalone copy is not swept (same as the control `password=API API`; B-N4 standing rule). `password=EMAIL_1, EMAIL_1 and a@example.com`: no core (real label), the real `<EMAIL_1>` untouched, idempotent; STATED LIMIT: the plain `EMAIL_1` stays as typed.
- M3 (final, E9 round 3 Major): the guard is a `_LOOKALIKE` token `‹[A-Z][A-Z0-9]*_[0-9]+›` in the value, OR `_bare` cut BOTH brackets off it (`‹x›`), OR cut a `‹` off a look-alike body (`‹SECRET_x`); one stray `‹` or `›` (`hunter22!›`) keeps its core (pin G12-28, mutants M22 token, M23 any cut, M33 both-brackets, M34 opened body, M35 any stray bracket). Earlier text:  DEVIATION from "token only": the existing test_redact_own_output.py::test_only_the_exact_escaped_shape_is_left_alone (`‹SECRET_x›`, `‹SECRET›`, `‹SECRET_1`) pins that these get no second entry, so the cut brackets also decline the core (a password wrapped in `‹ ›` loses its core: rare, stated limit). An interior `‹` keeps its core (pinned).
- M4: `_EDGE_FORM` now holds `</?tag {0,3}/?>`, `\\[nrt]`, `%XX`, `\\uXXXX`, `\\xXX`, `&#n;` / `&name;`; at the END only, closed-list cut-short forms (`<br`, `&quot`: the value class stops at a space or `;`, `hunter22<br />` stores `hunter22<br`). An open list (`<[A-Za-z]...\Z`) was tried and rejected: `<bx` at the end consumed a whole value. Every form is bounded, window 64: `_bare` on 160,000-char runs of each unit 0.2-0.3 s (pinned for correctness on 80,000 repeats). Pins G12-23 (end, 11 forms), G12-24 (start, 5 forms), G12-27 (closed list), each red on HEAD, green now. Mutants M26-M32; at the end the entity / `/>` / `<br/>` whole forms are equivalent (`;`, `>`, `/` are non-alphanumeric and the cut-short forms finish the cut), so M29/M30 use the start test. NOT done (limits): double-encoded `%250A`, a named entity outside the list (`&copy;` at the START), mixed-case `&QUOT;` cut-short, `\\u` escapes of other characters beyond hex digits are covered, any tag longer than 16 characters.
- Measured delta (2,185 rows as in G12b: property corpus 1,836, g8 CASES and `after`, 5 k5 perf units at 16 KiB; baseline = HEAD 007633576 src, same harness): text byte-identical in all 2,185 rows, rows with fewer masks 0, masks 47,306 -> 47,306 (none added: the corpus holds none of the new forms), map entries 2,145 -> 2,141 (-4: three fuzz rows where a core now shares an entry with another value). No renumbering.
- PRIVKEY / large values (direct calls, `runmap.redact_text`, agent-loop `_map_chars` = sum of distinct original lengths; caps MAX_MAP_CHARS 524,288, MAX_FINDER_CHARS 786,432): URLCRED (no core: value is the password), BEARER, BASIC (2 entries: full + piece, core equal to nothing new), HIGHENTROPY `==` (1 entry) unchanged by G12. PRIVKEY 2,054 chars: 2 entries 4,054 chars before, 3 entries 6,098 with the core. A 262,138-char PRIVKEY: 524,222 map chars before the core (under the run cap by 66), 786,350 with it: over MAX_MAP_CHARS (the run would end `document_too_complex` at the next distinct value) and 82 under MAX_FINDER_CHARS: a regression of G12. Fix: no core when `len(full) > 4096 and len(full) - len(core) <= 16` (`_CORE_BIG`, `_CORE_DELTA`; the PRIVKEY dashes differ by 10). After: 524,222, 2 entries. A plain 262,141-char `password=` value: 262,132 chars, one entry (its core would add 262,1xx; the same rule). Pinned G12-26, mutant M25. Not changed: a large value whose core differs by more than 16 characters still doubles (needs a deliberate wrapper of 17+ characters).
- Nits: the vacuous first `PW not in r.text` of the no-value test is replaced by the real assertions; the `endswith(...) or ...` test now pins exact texts per case (`password=password=` -> `<SECRET_1><SECRET_1>`); docstring "at most twice" -> one extra entry per value; the two-placeholders-for-one-secret numbering is documented in the test docstring.
- Not run: tests/test_k5_perf.py -m perf; full suite; mutant files other than g12_mutants. Ran with 3-5 other pytest processes alive (the load cap in the order said fewer than 3): one batch at a time, no `-n` (xdist is not installed in this venv).
