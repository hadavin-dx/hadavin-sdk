Status: resolved (applied to `handover/tickets/P1-rev2.md` rev 4, 2026-11-09T07:34Z start, headless egm-resolve, Opus 5.5)

# P1-rev2 rev 3, plan review round 2: resolution (last plan round, cap 3)

**Inputs:** `round2-p1rev2-design.md` (0B 2M 5N), `round2-p1rev2-codebase.md` (0B 3M 5N); binding lead ORDER 179 (q390: Q-L1, Q-L2, T6-5 noqa).
**Checked against:** snapshot `/home/user/build/snap/63-bf955e9` (P1a head), the on-disk `handover/`, and ruff 0.17.1 run in the scratchpad (`r179/`, 2026-11-09).
**Counts:** 15 findings. 15 PROPOSE FIX (all applied in rev 4), one of them with a contested sub-claim (design M2, the ci.yml part). 0 DECLINE. 1 NEEDS LEAD, a new question that came out of design M1 (Q-L3 below).

Merged groups, most severe first. "Applied" means it is written into rev 4.

## G1 (Major): an unknown character that replaces a letter (design M1; also F-R8)
- **Finding:** D5 says that dropping a character assigned after Unicode 15.1.0 is an over-match. That is true only when the character is INSERTED. When it REPLACES a letter (`al` + new look-alike + `ce`), the fold drops it and the check name loses a letter (`alce`). Then `alce` does not equal `alice`, so the DENY check misses: the unsafe side.
- **Check:** confirmed on the snapshot. `_DROP_CATEGORIES` (textnorm.py:263) holds Cn (unassigned), Co (private use) and Cs (surrogate), so all three are dropped. Private use has the same problem: its glyph depends on the font, so it can be drawn as any letter.
- **AI suggestion: PROPOSE FIX (applied). Decision: FAIL CLOSED for the DENY check.**
  - New fix **F6-5**: `could_be_same_person(a, b)` returns True when `a != b` and either text holds a code point of category Cn, Co or Cs. `allow_equal` follows (LOOKALIKE). Identical strings stay EQUAL.
  - Why fail closed instead of a one-character wildcard: the wildcard needs a regex per pair, and it is still wrong when the replacement folds to two letters. Failing closed is one line, easy to test, and on the safe side.
  - Cost, stated plainly in D5 and the docstring: a name that holds an emoji newer than Unicode 15.1, or a private-use character, is "could be the same person" with EVERY other name, so a person must look. ORDER 179 keeps `could_be_same_person` out of every approval check, so today this cost falls only on the deny and check-name path.
  - New test **T6-6**. New behaviour mutant **(i)**. F-R8 also counts the characters assigned after 15.1.0 that `confusables.txt` 18.0.0 maps to Latin, Cyrillic or Greek letters.
- **NEEDS LEAD (Q-L3, new):** the scan side has the same miss. `fold_views` and `squeeze_views` drop the character, so `passw` + unknown character + `rd` does not hold `password`. Scans are owned by P1b `scan_holds` and PR 77 `redact.py`, not by P1a. Recommendation: P1b's `scan_holds` treats a text with Cn, Co or Cs as "holds" (fail closed, a person must look), with its own test. The lead names the package. P1a's docstring states the limit and names the owner.

## G2 (Major): F6-1b would break script views (codebase M2; design N3)
- **Check:** confirmed on the snapshot. In `_view_pairs` (textnorm.py:545-548) script views are made only in the marks-dropped pass (`if scripts and marks:`), and `marks_only` depends on that pass. If the marks-dropped pass were skipped for a text without marks, a Chinese, Hindi or Thai text without marks would lose its script view.
- **AI suggestion: PROPOSE FIX (applied).** F6-1b is moved into `_keys` ONLY: `marks_dropped=_without_spacing_marks(raw) != raw`. `_view_pairs`, `_views`, `fold_views`, `squeeze_views` and `scan_needles` do not change. This also leaves the fix5 mutant at `tests/textnorm_mutants.py:336` untouched.
- Design N3: a new test checks, for every single code point and for every name in `textnorm_names.json`, that the gated `_keys` gives the same result as the ungated one. A new test checks that a text without marks still gets its script view in `fold_views`. New mutant **(h)** turns the gate the wrong way and is killed by T6-1.

## G3 (Major): `identity_key` is banned but documented as the check name to keep and index (codebase M3; design N2)
- **Check:** confirmed. The `identity_key` docstring (textnorm.py:754) and the module docstring (:57-58) say "the check name to keep and to index" and "use identity_key equality there". Grep of the snapshot: no file in `src/`, `demos/` or `tools/` other than `textnorm.py` imports or calls `identity_key` (or any textnorm name).
- **AI suggestion: PROPOSE FIX (applied). Decision: KEEP `identity_key` in the ban, with its own message and a documented exemption route. The indexing use stays documented.** Why: outside tests there are only two possible uses. One is a lookup or match, which is exactly the bug class this ban targets. The other is a unique index or dedupe, which is legitimate but has no caller today. A ban with an exemption route fails closed on a security path and costs nothing now. Dropping `identity_key` from the ban would leave the commonest form of the bug open.
- Wording: the `identity_key` message reads "identity_key is ONE reading: only for a unique index or dedupe, through an exemption row; a match uses identity_keys or could_be_same_person". The docstrings at :57-58 and :754 add "outside tests only through an exemption (pyproject ban, T6-5 list)".
- Design N2: T6-5(2) now also fails when any file under `src/`, `demos/` or `tools/` other than `guard/textnorm.py` names `identity_keys`, so the D4 rule "nothing may store identity_keys" is enforced, not only written. Why punctuation is not in the dropped class: a person writes it on purpose and it is visible ("O'Brien", "a-b"), so dropping it would merge different ids. A spacing mark inside a Latin word has no use except to hide. The four punctuation cases stay pinned as strict expected failures (r114-r117).

## G4 (Major): T6-5 durable ban test, the noqa forms, and ORDER 179 (c) (design M2; design N4 and codebase N1 on the number of reports)
- **Check:** ruff 0.17.1 in the scratchpad (`r179/`). `--ignore-noqa` reports a ban hidden by a bare `# noqa` AND by a file-level `# ruff: noqa`. `--config 'lint.per-file-ignores = {}'` lifts the `tests/**` exemption for one run. S603 does not flag an argument list made only of string literals, but S607 then flags the partial path (`["ruff", ...]`). So a pytest subprocess call to ruff always needs a suppression. The repo has no general tested command wrapper: `tools/mutation_runner.py` has only `_pytest`, and `tools/scan_repo.py:75` carries its own `noqa`.
- **AI suggestion: PROPOSE FIX (applied). There is NO subprocess in pytest and NO new `noqa`.** The two ruff runs become two steps of the lint job in `.github/workflows/ci.yml`, written in shell, with no Python call at all:
  - (A) `ruff check --select TID251 --ignore-noqa src demos tools` must pass. The only allowed exemptions are `per-file-ignores` rows, which `--ignore-noqa` does not lift.
  - (B) Six planted forms in `tests/fixtures/tid251_forms/`, run with `--select TID251 --ignore-noqa --config 'lint.per-file-ignores = {}'`, must give exactly 6 reports.
  - T6-5 in pytest keeps (1) the `tomllib` config check. It gets a new (2), a pure-Python scan with no subprocess: no `noqa` that could mute TID251 (bare, `TID251`, file-level) under `src/`, `demos/` or `tools/`, plus the `identity_keys` check from G3. It gets a new (3): `ci.yml` holds steps A and B word for word, so deleting a step fails a test.
  - `.github/workflows/ci.yml` and the fixture folder are added to Files. This is a CI file change only, with no GitHub settings change.
- **Count fixed:** 6 forms; the "8 reports" were the 6 forms plus the from-import planted again in `demos/` and in `tools/`.
- **CONTEST (sub-claim only): "the P1a head's ci.yml does not lint tools".** The snapshot `63-bf955e9/.github/workflows/ci.yml:80` reads `ruff check src tests demos tools`. The on-disk `ci.yml:79` the design reviewer read is not the P1a tree (the codebase reviewer confirmed :80). No change for this part beyond naming ci.yml in Files, which G4 needs anyway.

## G5 (Major): existing mutants and meta-tests that F6-1, F6-2 and the new mutants break (codebase M1)
- **Check:** confirmed on the snapshot. `tests/textnorm_mutants.py:149-151` ("mixed script never true": `if latin and other:` / `return True`) and :158-165 (invisible, micro sign, Cherokee: the `kept` filter lines and the `_NON_LATIN_SCRIPTS` prefix) target the body of `has_mixed_script` that F6-2 rewrites. In `tests/test_textnorm_meta.py`, :88 is the test name with 128, :90 has `len(names) == 128`, :95 has `len(names[28:]) == 100`, :158 has `len(rows) == 128`. Appending the new mutants changes all of these. The positional slices :96-:106 stay valid because the new mutants are appended at the end.
- **AI suggestion: PROPOSE FIX (applied).** Item 7 of the rewrite list: re-point the four `has_mixed_script` mutants to the new text, with killers MIXED, INVISIBLE, MICRO and INVISIBLE (re-checked by the mutant run). Change 128 to 138 at :88, :90 and :158, and 100 to 110 at :95. Item 6 already covers TAGKEYS. The `:336` mutant is untouched (G2).

## Nits (all PROPOSE FIX, applied)
- design N1: DEVANAGARI is NOT in `_NON_LATIN_SCRIPTS` (snapshot :860-862), so "Ramesh"+"जी" is False under rule (a) and rule (b). Stated in F6-2. New mutant **(j)**: Mc not in the word class, killed by T6-3.
- design N4 and codebase N2: T6-4 uses `uv tool run --from ruff==0.17.1` (no project sync, no re-lock) and fetches `8b2b716` first.
- design N5: the D9 test name is written out in full.
- codebase N3: docstring sites `:143` ("pins the insertion rule": now also the DENY check) and `:797` (the LOOKALIKE comment adds "spacing marks") are added.
- codebase N4: B1 item 2 cites `:1714`.
- codebase N5: F-R3 covers both `:58` and `:176` ("checked first").
- codebase N6: the F6-2 counts (54 of 56 groups; 0 misses over 452) are labelled as prototype results, re-measured by T6-3 inside the real function.

## Mutant total
128 + 10 = **138**: behaviour 8, (a)-(e) and (h)-(j); wording-only 2, (f) and (g).

## ORDER 179, applied
(a) `could_be_same_person` is wired into NO approval check. It is a library primitive for the deny and check-name path only, and no approval compares people's names. Any future approval use is a new ticket with its own plan review (money and permission path, no round cap). Written in the ticket and in the module and function docstrings (F-R9). Q-L1 is closed.
(b) The separate demo repos get the same TID251 ban table at the re-pin sweep after P1a merges, not before. Q-L2 is closed.
(c) T6-5 has no new `# noqa: S603` (G4).
