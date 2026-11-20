# G1 fold: evidence (ticket G, part G1)

Written by the G1 builder agent of core-c (role TEXT), 2026-11-20. Nothing was pushed. No head was checked out; every head was read with git only.

## 1. Where the work is

- Worktree: `/home/user/hadavin-sdk/.claude/worktrees/agent-a7a352c633faf6b63` (its own `.venv`).
- Branch: local `wip-g1-fold`, cut from main = refs/inputs/main (51c9fc4). Linear, 5 commits, no merge commit.

| # | SHA | message (first line) |
|---|---|---|
| 1 | 71e5cf4720d2cd5e0dabb5170c14abc16c1be724 | code G: G1 step 1: bring rebase/P1b-o140 (851ad92, P1a fix8 + P1b) onto main as one commit |
| 2 | 098e898b583402e0100d6e5142e8c843389ce85e | code G: G1 step 2a: port fix batch round 1 (2034512) from core/P1b-fixwip |
| 3 | e8cc1368a9c96cfb8c01cdd46dd970b04b49330f | code G: G1 step 2b: port fix batch round 2 (4bf610e) from core/P1b-fixwip |
| 4 | fcfb35721e5d9cc4fae4376d5a061c4703923792 | code G: G1 step 3: re-pin from measured values (manifest hash, mutant counts, CHANGELOG) |
| 5 | 8e4d2349ed76a0fc9c456efc7def9b95c364bb11 | code G: G1 step 4: test for invariant G1-I2 (evidence answers as main for composed and decomposed spellings) |

Whole change against main: 49 files, +28,912 -22 (`git diff --shortstat refs/inputs/main HEAD`).

## 2. FAILURES (1 test, NEW in the sense "caused by the fold"; the heads were not run, so INHERITED is UNVERIFIED)

| test | first error line | label | cause |
|---|---|---|---|
| `tests/test_textnorm_round1.py::test_m16_a_spacing_mark_or_modifier_symbol_does_not_split_a_mixed_script_word` | `E       AssertionError: assert (True is False)` / `+  where True = has_mixed_script('ab' + U+0903 + 'cd')` (line 428) | NEW (a real disagreement of two inputs; on core/P1b-fixwip alone: UNVERIFIED, not run) | P1a fix8 (only in o140) and round 1 M16 (only in fixwip) both changed `has_mixed_script`, with different rules. fix8 rule (b), accepted by ORDER 177 per the CHANGELOG ("`ali` + U+0903 + `ce` ... are flagged"), flags a Latin word that holds a spacing mark of another script. Round 1's test wants `"ab" + U+0903 + "cd"` NOT flagged. Both cannot hold. The fold keeps fix8's code (the task says keep `_words`, `_word_is_mixed`). The first three assertions of the same test (Latin + mark + Cyrillic is flagged; a space still splits) PASS on the fold. The test was NOT edited, skipped or xfailed. |

Decision needed from the lead: (a) keep fix8's rule and change that one clause of the round 1 test to expect True for Latin + Devanagari mark + Latin (what fix8's own tests pin), or (b) take round 1's rule and drop fix8 rule (b) (then fix8's tests fail). I recommend (a): fix8 is the stricter deny signal and has an order behind it.

Everything else in the batch passed: `1 failed, 8616 passed, 17 skipped in 244.75s`. The 17 skips were not listed by reason (the run had no `-rs`; see section 8).

## 3. Source commit -> where it went (invariant G1-I1)

| source commit | what it is | where it went / why dropped |
|---|---|---|
| rebase/P1b-o140, all 26 commits to 851ad92 (holds rebase/P1a 8ca324e = P1a fix8) | P1a complete + P1b | commit 1 (71e5cf4), one squash. `git diff refs/inputs/rebase/P1b-o140 71e5cf4 --stat` lists 14 files, +1,994 -90, and is line for line the same list and counts as `git diff a8b4d8e refs/inputs/main --stat` (a8b4d8e = o140's base): every remaining difference is main's own newer change (ci.yml 98, CHANGELOG 1, README 7, pyproject 2, ci_security_golden.json 4, timing.py 126, migration_numbers_mutants.py 19, test_ci_guard_wip_lanes.py 697, test_k5_perf.py 51, test_migration_numbers.py 33, test_no_pglast_in_runtime.py 675, test_s1_foundation.py 4, test_timing_fixture.py 343, uv.lock 24). |
| 2034512 round 1 (fixwip) | src: defaults, injection, runmap, textnorm, evidence; tests; 10 mutants | commit 2 (098e898). All src hunks landed except three, each superseded by fix8: (1) `_WORD` / `_WORD_JOINING` and the two lines of `has_mixed_script` that use them (fix8's `_MIXED_REMOVED`, `_words`, `_word_is_mixed` stay); (2) `_PINNED_PYTHON` -> `defaults.TEXTNORM_PINNED_PYTHON` (fix8 already has the constant in defaults); (3) the docstring sentence "NOT equal: a spacing mark ..." of `could_be_same_person` (fix8 made them equal). Checked by comparing the sorted +/- lines of `git diff 2034512^ 2034512 -- textnorm.py` with those of the commit: the 9 lines that differ are exactly these. 1 of the 10 mutants dropped: "mixed script: a spacing mark splits the word" (its search text `_WORD_JOINING` is not in the fold; fix8's mutant on `_words` mutates the same rule). |
| 4bf610e round 2 (fixwip) | src: defaults, injection, evidence; tests; 5 mutants | commit 3 (e8cc136). All src hunks applied with no conflict. After it `runtime/evidence.py`, `guard/injection.py` and `guard/runmap.py` are byte-equal to core/P1b-fixwip (`git diff 4bf610e HEAD` shows none of the three). `defaults.py` differs from fixwip by the 3 lines of `TEXTNORM_PINNED_PYTHON` (fix8). |
| b48630d (fixwip; tests, mutants, CHANGELOG) | "order 140: restore the raw leak check" | NOTHING to bring: tried with `cherry-pick -n`; its 3 mutants and its test_textnorm.py text are already in o140 (o140's acd7895 carries them; the survey's "missing" came from range-diff pairing). The two conflicts (meta counts, one CHANGELOG line) were o140's newer numbers; o140's side kept; resulting diff was empty. |
| d28d2bc, b0f54b1 (fixwip; tests only) | mutant killer tests | already in the fold: `tests/test_textnorm_order137.py` and `tests/test_textnorm_scan.py` are byte-equal to fixwip's tip. |
| 0d843b4, e438411 (fixwip; perf rows, a hash re-pin) | tests | perf rows present (the fold's test_textnorm_perf.py = fixwip's + one fix8 test); the hash re-pin is superseded by commit 4. |
| 71b8379 (fixwip; CHANGELOG, golden note, manifest) | docs and fixtures | not cherry-picked. The fold has o140's CHANGELOG text for those entries plus round 1 and round 2's entries. Whether every sentence of 71b8379's CHANGELOG wording is in o140's was NOT compared (section 8). |
| core/P1a 27ae996, core/P1b e3f946f | older forms of the same work | not used: rebase/P1a is an ancestor of o140; core/P1b is an ancestor of fixwip (survey section 3). |
| new | G1-I2 test | commit 5 (8e4d234), `tests/test_evidence_decomposed.py`, 7 tests, all pass. |

End state asked for by the task, each checked on HEAD:
- `runtime/evidence.py` calls `runmap.composed` (lines 66, 96, 97, 160), as fixwip.
- chunked injection read in `guard/injection.py` (file equal to fixwip).
- `TEXTNORM_INSERTION_MIN_CHARS = 12` (defaults.py:181).
- `scan_holds(*, text: str, value: str)` keyword-only (textnorm.py:1446); grep of `scan_holds(` without `text=` in src, tests, tools finds only docstrings, a local test helper `_scan_holds`, and the one test that proves a positional call raises.
- `_ASCII_OR_ONE` / `_canonical_view` speed-up in runmap.py (file equal to fixwip).
- textnorm.py holds `_holds_spacing`, `_holds_unnamed`, `_untagged`, `_validated_pins`, `_words`, `_word_is_mixed` AND `_CacheScope`, `_lazy_tables`, module `__getattr__`.
- TID251 rule in pyproject.toml, the two CI steps and the six `tests/fixtures/tid251_forms` kept; run by hand: step A "All checks passed!", step B counts 6.

## 4. Conflicts and how each was resolved

| step | file | resolution |
|---|---|---|
| 1 | CHANGELOG.md (1 region) | both sides' lines kept, main's line first |
| 2a | guard/textnorm.py (5 regions) | region 1 (`could_be_same_person` docstring): fix8's text + round 1's LIMIT paragraph, without round 1's "NOT equal" sentence; regions 2 to 5 (`require_pinned_unidata`, `has_mixed_script` and its constants): fix8's side |
| 2a | tests/textnorm_mutants.py (header line) | o140's side then re-written in commit 4; one mutant dropped (above) |
| 2a | tests/test_textnorm_meta.py (3 regions), textnorm_manifest.json (1), CHANGELOG.md (3) | o140's side (pins and fix8 text); re-pinned in commit 4. In CHANGELOG region 1 round 1 had removed two "### Changed" lines (API breaks, plain-words rule) that o140 has: kept. |
| 2b | tests/textnorm_mutants.py (2 regions) | header: o140's side; list: round 2's side (4 new injection mutants, new expect text) minus the dropped mutant |
| 2b | tests/test_textnorm_meta.py (3 regions) | o140's side for the slices that know fix8; counts in commit 4 |

## 5. Pins recomputed (invariant G1-I3)

| pin | old | new | how |
|---|---|---|---|
| sha256 of `src/hadavin_sdk/guard/textnorm.py` in `tests/fixtures/textnorm_manifest.json` and in the CHANGELOG re-copy list | a08f64b07183bd029d49a29f3eca3fd9daf2bd28633b4236af22162c6de35db8 (o140; fixwip had 1f520822...) | 1b923f323822fc4059e0a401851a0abe129aa0bb80e81923d2bb0735f469a174 | computed as `test_the_manifest_pins_the_files_a_demo_copies` computes it (file bytes, CRLF read as LF, sha256). The repository has NO generator for this manifest (grep of tests/ and tools/ for "manifest"): a small script did it. |
| the other 4 files of the manifest (`_confusables.py`, `_scripts.py`, vectors, corpus) and the 2 `tools/data` files | (unchanged) | same | re-hashed the same way: all equal to the manifest |
| mutant count in `tests/test_textnorm_meta.py` (three places) | 226 (o140), 231 (fixwip) | 240 | measured: `len(tests.textnorm_mutants.M)` = 240, all names unique. The pins in the meta-test are HAND-WRITTEN LITERALS; they were set to the measured number. 240 = 226 + 9 (round 1, 10 less the dropped one) + 5 (round 2). |
| `len(names[28:])` | 198 | 212 | 240 - 28 |
| tail slice `names[163:]` ("the P1b fix batch") | 63 | 77 | measured; 63 + 14 |
| test name `test_a_the_list_has_226_..._63_of_the_p1b_fix_batch...` | 226 / 63 | 240 / 77 | the name carries the numbers |
| header of `tests/textnorm_mutants.py`, CHANGELOG count sentence | 226 / 231 | 240 | `test_i_the_changelog_states_the_true_mutant_count...` reads `len(mm.M)` |
| behaviour / wording split | (not pinned as numbers) | 228 / 12 | `split_counts()`; printed only |
| `alg` in `tests/fixtures/textnorm_golden.json` | fold5 | fold5 (unchanged) | already fold5 in o140; the golden test passes on Unicode 15.1.0 with o140's hashes, so nothing was re-made. The 15.0.0 section was NOT exercised (section 8). |

## 6. Files changed that are not TEXT's own (G1-I6), `git diff --numstat refs/inputs/main HEAD`

| file | + | - | owner note |
|---|---|---|---|
| src/hadavin_sdk/app.py | 4 | 0 | `require_pinned_unidata` in `build()` (SPINE) |
| src/hadavin_sdk/guard/injection.py | 130 | 4 | chunked read; SPINE edits this file in step F |
| src/hadavin_sdk/runtime/evidence.py | 14 | 5 | `runmap.composed` |
| src/hadavin_sdk/defaults.py | 80 | 0 | `TEXTNORM_*` constants |
| pyproject.toml | 12 | 2 | license-files, TID251 banned-api |
| .github/workflows/ci.yml | 6 | 0 | two TID251 steps |
| tests/conftest.py | 18 | 0 | autouse fixture for the Unicode pin guard |
| CHANGELOG.md | 241 | 0 | |
| README.md | 8 | 0 | |
| THIRD-PARTY-NOTICES.md | 67 | 0 | |
| .gitattributes | 2 | 0 | |

TEXT's own, for scale: guard/textnorm.py +1,700, guard/runmap.py +43 -10, guard/_confusables.py +871, guard/_scripts.py +933 (both generated). These other-owner files are NOT in separate commits per owner: the series is cut by source (o140, round 1, round 2), as the task ordered. Splitting per owner is a follow-up if the lead wants it.

## 7. G1-I2 (evidence, composed and decomposed) and one finding

`tests/test_evidence_decomposed.py` copies main's `runmap.canonical` body (51c9fc4) into the test as the reference. Passing: `normalise` equals main's for 9 values in both spellings and gives one key per value; `contains` is True in all four text/value spelling combinations (exact and casefold) and False for a missing or different accent; `grounded` accepts a precomposed identifier against a text of either spelling and refuses a decomposed identifier (as main: the value's canonical form is not the value); `runmap.composed(ch) == main canonical(ch)` for every single code point; 5,000 seeded mixtures without invisible characters equal main.

FINDING (a difference from main, pinned by name in the last test, not hidden): an invisible format character (U+200B, U+00AD, U+2060 tried) BETWEEN a letter and its combining accent. Main normalised first and removed the invisible character afterwards, so letter and accent stayed apart and a precomposed value was NOT found in such a text. `runmap.composed` (o140 and fixwip alike) removes the invisible character first, so it IS found: `evidence.contains` finds MORE than on main in this one shape. As an identifier VALUE such a spelling is still refused. So G1-I2 holds for composed and decomposed spellings and does not hold for this third spelling. Lead: accept (the text reads the same to a person) or order `composed` to keep main's order.

Python and Unicode on this box (G1-I7): `3.13.18 (main, Oct 26 2026, 14:08:19) [Clang 23.1.3 ] 15.1.0` (python3.13, also the worktree venv); `3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0] 15.0.0` (python3.12: NOT the pinned Unicode, so the start-up check refuses pilot and prod on it).

## 8. NOT checked

- No head was run, so no failure can be labelled INHERITED: the one failure above is labelled from reading the two inputs.
- Python 3.12 / Unicode 15.0.0: nothing was run on it (the golden file's 15.0.0 section, the conftest fixture path).
- The mutant runner (`uv run python tests/textnorm_mutants.py`) was NOT run: 240 mutants are counted, and `test_g_every_search_string_occurs_exactly_once...` passes, but no mutant was executed. With the failing M16 test in a killer file the runner's baseline is not green until the lead decides section 2.
- The whole repository suite was not run (ordered: one full run later). Run: the 67 files below, not `tests/contracts`, `tests/demo_*`.
- The 17 skips: reasons not listed (no `-rs`); not compared with a baseline.
- `bandit -ll src/hadavin_sdk/guard` (ticket evidence commands): not run. `demos/` was not linted by `ruff check` (the task's command names src tests tools); the TID251 step A did include demos.
- CHANGELOG wording: the round 1 entry still says "`has_mixed_script` treats Mc and Sk as word-joining" and "10 new mutants"; a new fold entry says what the fold really holds, the old sentences were not rewritten. fixwip's CHANGELOG edits before round 1 (71b8379 "P1a text restored") were not compared sentence by sentence with o140's.
- The generated tables were not regenerated from `tools/data` by hand (the generator tests in the batch passed; hashes equal the manifest).
- The `could_be_same_person` LIMIT paragraph (apostrophes) is true on the fold: `test_m16_the_apostrophe_limit_is_pinned_and_named` passed.
- textnorm.py was merged by hunk and checked by the +/- line comparison and by the tests; it was not re-read line by line.
- No credential-shaped text was added; the new test holds names with accents only, built from escapes.

## 9. Commands and raw output (last 30 lines each; long lines cut at 300 characters)

All run in the worktree, on the tree of commit 8e4d234 (the batch and the perf run ran once, on the same file content, just before commits 4 and 5 were made; ruff and sync were re-run after).

### `uv sync --all-extras --group test` (second run; the first run installed the packages)

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Resolved 103 packages in 2ms
Checked 78 packages in 0.90ms
exit=0
```

### `uv run --all-extras --group test ruff check src tests tools`

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
All checks passed!
exit=0
```

### `uv run --all-extras --group test ruff format --check src tests tools`

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
317 files already formatted
exit=0
```

### `uv run --all-extras --group test pytest -q -m "not perf" -p no:cacheprovider <67 files> -n 3` (exit 1)

Files: tests/test_textnorm*.py (13; the perf file is in the list and deselected by the marker), test_third_party_notices.py, test_k5_round9.py, test_no_hardcoded_values.py, test_stage_names.py, test_evidence_decomposed.py and every tests/*.py that holds "evidence", "runmap" or "injection" (61 by grep); 67 after removing doubles. pytest-xdist is installed.

```
........................................................................ [ 95%]
........................................................................ [ 96%]
........................................................................ [ 97%]
.....F.................................................................. [ 98%]
........................................................................ [ 99%]
..................................................................       [100%]
=================================== FAILURES ===================================
_ test_m16_a_spacing_mark_or_modifier_symbol_does_not_split_a_mixed_script_word _
[gw2] linux -- Python 3.13.18 /home/user/hadavin-sdk/.claude/worktrees/agent-a7a352c633faf6b63/.venv/bin/python

    def test_m16_a_spacing_mark_or_modifier_symbol_does_not_split_a_mixed_script_word():
        """FAILS before, by behaviour (the word was cut at the mark, so Latin and Cyrillic never met). Mc: U+0903 and U+093E; Sk: U+02C2."""
        cyr = "\u0430\u0431"
        for mark in ("\u0903", "\u093e", "\u02c2"):
            assert has_mixed_script("ab" + mark + cyr) is True, (
                f"MIXED-SCRIPT-MARK: a joining mark U+{ord(mark):04X} splits a Latin and Cyrillic word"
            )
        assert has_mixed_script("ab \u0903 " + cyr) is False, (
            "a space between the words still splits them"
        )
>       assert (
            has_mixed_script("ab\u0903cd") is False and has_mixed_script(cyr + "\u0903" + cyr) is False
        )
E       AssertionError: assert (True is False)
E        +  where True = has_mixed_script('abःcd')

tests/test_textnorm_round1.py:428: AssertionError
=========================== short test summary info ============================
FAILED tests/test_textnorm_round1.py::test_m16_a_spacing_mark_or_modifier_symbol_does_not_split_a_mixed_script_word
1 failed, 8616 passed, 17 skipped in 244.75s (0:04:04)
```

### `uv run --all-extras --group test pytest -q -m perf tests/test_textnorm_perf.py -p no:cacheprovider` (serial, exit 0; load average after it 1.35)

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
.................                                                        [100%]
17 passed in 42.66s
```

### TID251 CI steps by hand

```
ruff check --select TID251 --ignore-noqa src demos tools  ->  All checks passed!
ruff check --select TID251 --ignore-noqa --config 'lint.per-file-ignores = {}' --output-format concise tests/fixtures/tid251_forms | grep -c ' TID251 '  ->  6
```

## ORDER 010 fixes

Done 2026-11-20 on the fold checkout (branch cloud/core-c), Python 3.13 venv (Unicode 15.1.0). Files written: tests/test_textnorm_round1.py (one clause of the M16 test `is False` -> `is True` with a comment; one new test `test_order010_a_latin_word_carrying_a_foreign_spacing_mark_is_flagged_as_mixed_script`), README.md, CHANGELOG.md (fold entry), tickets/G-text-deltas.md (AMENDMENT 1). tests/textnorm_mutants.py and tests/test_textnorm_meta.py: NOT changed (no mutant added; counts stay 240 / 212 / 77, 228 / 12). Section 2 above is closed by this: the batch is green.

Not checked: nothing was run on Python 3.12; 238 of the 240 mutants were not run; the whole repository suite was not run; the textnorm.py hash pin is untouched because textnorm.py was not edited.

### `uv run --all-extras --group test ruff check tests/test_textnorm_round1.py tests/textnorm_mutants.py tests/test_textnorm_meta.py`
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
All checks passed!
exit 0
```
### `uv run --all-extras --group test ruff format --check` (same three files)
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
3 files already formatted
exit 0
```
### `uv run --all-extras --group test pytest -q -p no:cacheprovider -n 2 -m "not perf" tests/test_textnorm*.py tests/test_third_party_notices.py tests/test_no_hardcoded_values.py`
```
........................................................................ [ 84%]
........................................................................ [ 92%]
........................................................................ [ 99%]
...                                                                      [100%]
939 passed in 217.62s (0:03:37)
exit 0
```
### `uv run --all-extras --group test python tests/textnorm_mutants.py "mixed: rule (b) is never true" "mixed: a spacing mark splits the word"` (after the test change; baseline green, then the two mutants)
```
240 mutants: 228 change behaviour, 12 change only words
ok  KILLED       mixed: rule (b) is never true  [test_a_spacing_mark_or_symbol_cannot_hide_a_mixed_word_and_a]
ok  KILLED       mixed: a spacing mark splits the word  [test_a_spacing_mark_or_symbol_cannot_hide_a_mixed_word_and_a]
2 of 2 good; problems: []

real	6m17.414s
user	6m2.932s
sys	0m4.684s
exit 0
```
### `key_tag` / `identity_keys` with `unicodedata.unidata_version` stubbed to 15.0.0 (venv python 3.13; for AMENDMENT 1 item 6)
```
pinned '' ('\u0903', '') 'alice'
stub 15.0.0 key_tag='\ue000alg=fold5|ud=15.0.0\ue000' identity_keys(U+0903)=(tag+'\u0903', tag) identity_keys(U+200B)=(tag,) identity_key('Alice')=tag+'alice'
key_tag() in identity_keys(U+0903): True; in identity_keys(U+200B): True; could_be_same_person(U+0903, U+200B): True; could_be_same_person(U+0903, 'a'): False
```
