# Ticket G: text deltas (fold, check-only mask function, P1d-a, P2d-1, P1c, G5 wording)

Written by core-c (session role TEXT), 2026-11-20. Status: DRAFT for one EGM plan-review round. No source code until the lead writes "GO BUILD G".
Step type (RIGHT-SIZE): shipping code on the redaction path (guarantee class). G6 (wording) is a docstring edit.
Sources: inputs/plan-v4-final.md B1 row G (line 14), B2, B3, B5; the two surveys beside this file (G-survey-P1a-P1b.md, G-survey-P2d-P1d-P1c.md: every head fact below comes from them, read with git only, NOTHING was executed on any head). Line numbers are main 51c9fc4 unless a head is named.
This ticket is over the usual length because step G is six parts that land as one PR group; each part is small on its own.

- Package id and name: G, "text deltas". Path class: redaction. Extended review: the lead decides (ORDER 004 allows one ticket round here).
- Depends on (merged first): nothing for G0. G1 to G5 depend on the lead's answers marked LEAD below. Step F (gate wrapper) depends on G0 only.

## Problem in plain words
The redactor finds secrets by patterns. Three kinds of work that make it harder to hide a secret from those patterns sit on side branches and were never landed: text folding (look-alike letters, hidden characters: branches P1a and P1b), scanning the folded text inside the redactor (P2d-1), and a fix where approval cards showed e-mail addresses and host names unmasked (P1d-a). A fourth piece, P1c (base64 view, whole host names), was planned and never started. The new model gate (step F) also needs a way to ASK "is this text already masked?" without changing the run's map, and no such function exists. Last, two docstrings promise a second leak check ("G5") that has no code.

## Parts, in build order
| part | what | size (from the surveys) | state of the input |
|---|---|---|---|
| G0 | check-only mask function in guard/runmap.py | about 40 lines + tests, on main | new code, no input head |
| G1 | fold P1a + P1b into ONE head on main | src +3,549 -11 (7 files), tests +8,505 (17 files), data +14,683 | rebase/P1b-o140 (851ad92) + two fix commits from core/P1b-fixwip |
| G2 | P1d-a on top | src +96 -35 (4 files), tests and fixtures +1,227 | core/P1d-a (6875f27), one commit, merges clean into o140 |
| G3 | P2d-1 on top ("on" = no off switch) | own change 14 files, +2,642 -43 | core/P2d-1 (76adadb): sits on an OLD P1a, 18 conflicts against the fold: a PORT, not a merge |
| G4 | P1c redactor gaps | unknown | NO branch, NO ticket file, NO corpus in this repository |
| G5 | "pattern redactor kind" and "put-back" | 0 lines | proposed CUT |
| G6 | G5 wording in approvals/gate.py and guard/redact.py | docstrings only | text proposed below |

## NEEDED-CHECK (R454), ONE-PLACE-PER-JOB
| part | what I read | verdict |
|---|---|---|
| G0 | runmap.py:464-526 (redact_text always writes the map at 524-525); has_placeholder 617 (finds `<KIND_n>` only); storable_original 244 (one stored value); redact.redact 862 (returns masked text, no views, no cap; a bare call outside runmap is forbidden by runmap.py:483-484); callers with a throw-away `{}` (judge.py:71, bedrock_guardrail.py:98, evals.py:63, tools.py:1005) redact, they do not check | NEEDED; lives in runmap.py next to redact_text and shares its scan code (one place for "how text is read") |
| G1 | main has four small normalisers (runmap.nfkc/canonical, gate.normalise/strip_controls, egress.normalise_host, redact.strip_ansi; LANE-MAP.md); none folds look-alike letters; no guard/textnorm* on main | NEEDED as already written on the heads; whether the four normalisers overlap textnorm is UNVERIFIED and is reported, not changed, in this step |
| G2 | approvals/gate.py sanitise_text; channel.py clean; the order "defang then redact" | NEEDED (bug fix in existing code) |
| G3 | _Redactor.find on main (redact.py:919) scans the written text only | NEEDED |
| G4 | old-plan-v4-3.md:194, 377, 546-547 | NEEDED per plan, but NOT BUILDABLE from this repository (see G4) |
| G5 | backends/table.py:386, 570-578 (no redactor capability; SPINE's file); runmap.restore_text 601, restore_value 607 with five callers | redactor kind: NOT-NEEDED now (one backend only; a registry row with one entry is ceremony). Put-back: DUPLICATE of 601 and 607 |
| G6 | approvals/gate.py:5-7, 42-44, 58-63; redact.py:15-17; no `enforce`, `for_terminal`, `outbound_data`, `hedge`, `leaked_kinds` in src (grep) | NEEDED: the text promises a control that does not exist |

## RUNG TABLE (CODE-LAST v1, scale of 2026-11-06)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| check-only function | yes/no "already masked" without a map write | 2: none exists (rows above, read 2026-11-20) | this ticket | the same reading rules as the one choke point | KEEP-CODE, about 40 lines |
| text folding (G1, G3) | find secrets written with look-alike or hidden characters | 4: Unicode UTS #39 data is vendored (tools/data/confusables.txt 15.1.0); library comparison ("Presidio missed 13 of 30", plan-v2.md:18) as cited by the plan, UNVERIFIED by me | plan-v2.md:18 | fold tied to the redactor's own patterns and map | KEEP-CODE (already written; this step lands it) |
| redactor kind | pluggable redactor | 2: no second backend exists | survey 2 section 4 | nothing today | CUT |
| put-back | restore masked values | 2: runmap.py:601, 607 | survey 2 section 4 | nothing new | CUT (duplicate) |

## G0. Check-only mask function (build first; step F needs it)
Signature (new, public, in guard/runmap.py; the five frozen signatures at 464, 568, 601, 607, 617 do not change):
```python
def is_masked(text: str, mapping: Mapping[str, str]) -> bool:
    """True when redacting `text` with `mapping` would mask nothing more. Never writes `mapping`.
    Raises InputTooLarge / TooDeep / RedactionError exactly as redact_text does: the caller treats any raise as NOT masked."""
```
How: the body of redact_text between line 485 and line 523 moves unchanged into a private `_scan(text, mapping, neutralise, cache) -> tuple[str, dict[str, str]]` that returns `(out, current)`. `redact_text` = `_scan(...)` then the two map lines (524-525) and `return out`. `is_masked` = `_scan(text, dict(mapping), None, None)` and returns `current == dict(mapping) and _held(out) <= _held(_clean(text))`.
Invariants:
- G0-I1 `is_masked` never changes `mapping` (equal before and after, same object identity of values) and never touches `mapping.redact_cache` (it passes no cache: one pattern rebuild per call is the price; BEST-FIRST: the safe option is the default).
- G0-I2 Decision rule = the rule of runmap.py:517: not masked when the map would grow OR the result holds more placeholders than the input. It never compares `out != text` (cleaning and NFKC change text without masking).
- G0-I3 For every text t and map m: after `x = redact_text(t, m)`, `is_masked(x, m)` is True (round trip), and when `is_masked(t, m)` is True, `redact_text(t, m)` leaves m equal.
- G0-I4 `redact_text` behaviour is byte-for-byte unchanged (the existing suite is the proof; no existing test is edited).
- G0-I5 It returns a bool only: no masked text, no found value, no kind leaves the function or reaches a log.
- G0-I6 Same caps and budget as redact_text; any failure raises (fail closed is the caller's `except`).
Tests (new file tests/test_runmap_is_masked.py): plain clean text True; a secret False; a secret behind full-width letters, a zero-width space, a backslash-u escape, percent-encoding False; a second copy of a value already in the map False; text holding only placeholders of m True; over MAX_REDACT_CHARS raises InputTooLarge; map equality and `redact_cache` untouched in every case; property test (hypothesis is in the test group: UNVERIFIED, else a seeded random loop) for G0-I3 over the fixtures tests already use for redact_text; FAIL-BEFORE: the same assertions against `redact_text` show the map changed.
Mutants: drop the `_held` clause (killed by the second-copy test); write the map (killed by equality); pass the cache (killed by the cache test); return True on exception (killed by the cap test).

## G1. Fold P1a + P1b into one head
Base: rebase/P1b-o140 (851ad92). It is the only head with P1a complete (fix8) and P1b; it conflicts with main in CHANGELOG.md only. On top: the two fix commits that exist only on core/P1b-fixwip, 2034512 (round 1) and 4bf610e (round 2), ported by hand (the two textnorm.py files are 172/224 lines apart), plus fixwip's tests test_textnorm_round1.py, test_textnorm_round2.py and commit b48630d (tests and mutants only).
Why the fix commits are part of G1 and not a follow-up: o140 changes `runmap.canonical` (main line 276) to stop composing a letter and its accent, and only fixwip changes runtime/evidence.py (lines 57, 87, 88, 151 on main) to call the new `runmap.composed`. Without that port, evidence grounding would treat decomposed text differently from main. This was read from the diffs, not executed.
Method: one linear series cut from main: (1) o140's tree as one commit; (2) round 1 port; (3) round 2 port; (4) re-pin. Not a merge of five heads.
Invariants:
- G1-I1 The fold contains every src change of rebase/P1b-o140 and of 2034512 and 4bf610e; a table in the PR lists each source commit and where it went, or why it was dropped.
- G1-I2 `runtime/evidence.py` normalise / contains / grounded give the same answers as main for composed AND decomposed spellings of the same value (new test; this is the risk named above).
- G1-I3 The pins are recomputed, never hand-edited to pass: mutant count in tests/test_textnorm_meta.py (138 / 226 / 231 on the heads; the fold's number is UNVERIFIED until run), sha256 of textnorm.py in tests/fixtures/textnorm_manifest.json, `alg` fold5 in textnorm_golden.json.
- G1-I4 `scan_holds` is keyword-only (`scan_holds(*, text, value)`, fixwip's form: two same-typed strings cannot be swapped silently). LEAD may overrule.
- G1-I5 `TEXTNORM_INSERTION_MIN_CHARS` = 12 (fixwip round 1) unless the lead says 8.
- G1-I6 Files outside TEXT's ownership that the fold must touch are delivered as commits the lead can pick AND listed for their owner: app.py +4 (`require_pinned_unidata` in `build()`, SPINE), guard/injection.py (SPINE edits it in step F), runtime/evidence.py, defaults.py, pyproject.toml (TID251 rule), ci.yml, tests/conftest.py, CHANGELOG. LEAD: confirm TEXT may carry these in the G commits, else they become patch files in handover/core-c/requests/.
- G1-I7 The start-up check refuses pilot and prod on a Python without Unicode 15.1.0 data. This box has Python 3.13.18 and 3.12.3; which Unicode version each carries is UNVERIFIED. The ticket's build notes record `unicodedata.unidata_version` for both.
Tests: the heads bring 306 (o140) to 326 (fixwip) test functions; the fold runs all of them; the perf file runs in its own serial step as on main CI (ci.yml:92, 100).

## G2. P1d-a
Take core/P1d-a's one commit on top of G1 (git reports a clean merge into o140; not executed). Changes approvals/gate.py (+62 -21), approvals/channel.py, approvals/slack_channel.py, guard/redact.py (+25 -6). approvals/channel.py and slack_channel.py are not TEXT's files: same rule as G1-I6.
Invariants: G2-I1 on every approval card path the redactor runs BEFORE `[.]` is written (defang last). G2-I2 a request stored before the change still renders (`undefang_text`). G2-I3 the three SECRET pattern changes (unbounded key prefix, `&` inside a value, query form) each keep their P1d-a row tests green and add no new false "must keep" failure in the existing redactor suites.
Out: "P1d rest" (inventory-gap.md:13 NOT STARTED) is not in step G.

## G3. P2d-1 on top of the fold
A port of P2d-1's own 14 files (+2,642 -43), not a merge: P2d-1 sits on P1a "fix5" and conflicts with the fold in 18 files. Needs three public names in textnorm that the fold head has only as private ones (`fold_view`, `without_spacing_marks`, `SPACING_CATEGORIES`; o140 has `_without_spacing_marks` 576, `_SPACING_CATEGORIES` 383, `fold_views` 798).
Invariants: G3-I1 no off switch: `_Redactor.find` runs the fold scan on every text that is not plain ASCII ("P2d stays on in v1", old-plan-v4-3.md:97). G3-I2 a value written with look-alike letters is masked in the written text, or the whole line is withheld with the fixed note; it is never shown. G3-I3 the budget is CPU time per call as on P2d-1; over budget raises InputTooLarge (nothing shown). G3-I4 `redact()`'s public signature gains only the private `_deadline`; `redact_text`'s signature is unchanged. G3-I5 G0's `_scan` split is kept (P2d-1 moves the map write to its lines 543-544: the port puts the fold scan inside `_scan`, so `is_masked` sees it too). G3-I6 P1d-a and P2d-1 both edit guard/redact.py: after both, every P1d-a row test and every P2d-1 fold test passes on the same tree.
Tests: P2d-1's six test files absent from the fold (test_redact_fold.py, _fold_budget, _fold_property, _fold_seams, test_redact_marks.py, redact_mutants.py) come along; a new test that `is_masked` returns False for a look-alike spelling of a known value.

## G4. P1c redactor gaps: BLOCKED on inputs
What the old plan says P1c is (old-plan-v4-3.md:194, 377, 546-547): (1) a base64 decoded view (3 hostile rows); (2) whole internal host names (2 partial lines); (3) the bare number pinned as an accepted property, NOT masked (order 64 item 4); (4) a permanent corpus test (30 hostile inputs, 48 must-mask and 14 must-keep lines).
What is missing here: `tickets/P1c.md` (revision 7, FROZEN), the hostile corpus and `score_common.py` are not in this repository; no branch or commit holds P1c code.
Proposal: (a) the lead copies the frozen P1c ticket and the corpus into handover/core-c/inputs/, then P1c gets its own short ticket G4 and one review round; (b) until then only item 3 is done inside G6 (the accepted property written in the redact.py docstring with its pin test), because it needs no corpus. I do NOT rebuild a 30-row corpus from memory of a plan line.

## G5. "Pattern redactor kind" and "put-back": CUT
Plan row G: "only as a named delta against `_Redactor` (guard/redact.py:890) and runmap restore functions (601, 607), else cut". No delta found (NEEDED-CHECK above; review-plan-3-zoom-out.md:16 says the same). Both are cut; nothing is written. A redactor capability in backends/table.py returns when a second redactor backend is ordered.

## G6. G5 wording (docstrings only)
The plan gives no replacement text (plan is silent; the bound is plan-v4-final.md:31). Proposed text for the lead's OK:
- approvals/gate.py:42-44, replace the "G5, leaks" bullet by: "- **G5, leaks: NOT in this module.** WARDEN blocked a message that still held anything the redactor classes as secret. That second check was not ported. Here, text is masked once, by `guard.runmap.redact_text`, before it reaches this module; nothing re-checks it on the way out."
- approvals/gate.py:59, replace "chat sinks: `enforce`, with G5 also over the text as built, before notify re-redacts it;" by a line that names what exists today (`sanitise_text` and `channel.clean`), and gate.py:63 "Verdicts: PASS ..., BLOCK (G5)" by "Verdicts: not ported (see the list at the top of this file)."
- guard/redact.py:15-17, replace "the outbound gate's G5 re-runs them, independently, on everything that leaves" by: "there is no second, independent pass on what leaves: model input is checked once more by the model gate's mask check (`runmap.is_masked`), which uses these same patterns and therefore cannot see what they miss."
- Also stale in the same block and proposed for the same edit: gate.py:46-50 (G2 `hedge`), 58-61 (functions that do not exist in src).
Invariant G6-I1: no docstring in these two files names a function or control that grep cannot find in src (new test: parse the two docstrings for back-quoted names and resolve each).
Second sentence of G6 depends on step F landing; if G lands first the sentence says "will be", LEAD decides the landing order.

## Files (TEXT-owned unless marked)
Create: guard/textnorm.py, guard/_confusables.py, guard/_scripts.py (generated), the textnorm, fold and P1d-a test files and fixtures listed in the surveys, tests/test_runmap_is_masked.py, tools/gen_confusables.py and tools/data/* (vendored Unicode files), tools/p1d_corpus.py.
Modify: guard/runmap.py, guard/redact.py, approvals/gate.py; NOT TEXT's: defaults.py, app.py, guard/injection.py, runtime/evidence.py, approvals/channel.py, approvals/slack_channel.py, pyproject.toml, .github/workflows/ci.yml, tests/conftest.py, README, CHANGELOG, THIRD-PARTY-NOTICES.md, .gitattributes (G1-I6).
Delete: none. Migration need: none.

## Interfaces
Offered: `runmap.is_masked(text, mapping) -> bool` (to step F and SPINE); `runmap.composed(text) -> str`; the textnorm public names of the fold head (survey 1 section 2). Frozen and unchanged: runmap 464, 568, 601, 607, 617.
Needed: from the lead, the LEAD decisions below and the P1c inputs; from SPINE, agreement on G1-I6 files; the baselines of the input heads (the lead runs them): until they exist no failure can be labelled INHERITED.

## Security and least privilege
No identity, credential or network. Test secrets are built from parts (the P1d fixtures say so; not verified by reading every fixture). Vendored Unicode data: licence text in THIRD-PARTY-NOTICES.md comes with P1a; R450 licence check is recorded there, not re-done by me (UNVERIFIED).

## Evidence commands
Per part, on the files just written: `uv run --all-extras --group test ruff check <files>`, `... ruff format --check <files>`, `uv run --all-extras --group test pytest <the part's test files> -q`, `bandit -ll src/hadavin_sdk/guard`. ONE full pytest when all parts are coded, each failure listed INHERITED or NEW. Raw output to handover/core-c/evidence/G-<part>.md. Mutant runs and Python 3.12 runs: the lead's evidence campaign.

## What stays out
P1c items 1, 2, 4 until inputs arrive; "P1d rest"; any merge of the four existing normalisers into textnorm (reported as a finding, AUDIT-GATE); a redactor capability; put-back changes; any change to the five frozen runmap signatures.

## Done and rollback
Done per part = its invariants each have a passing test, ruff and bandit clean, pins recomputed, lead verdict. Rollback: each part is its own commit ("code G: G0 ...", "code G: G1 ..."); reverting a part's commit removes it; G0 can stand alone on main.

## LEAD decisions needed (recommended answer first)
1. Fold base = rebase/P1b-o140 + port of 2034512 and 4bf610e from core/P1b-fixwip. Are those two fix rounds approved changes (round 2's own message says its full runs were not finished)?
2. May TEXT's G commits carry the files of other owners listed in G1-I6 (recommended: yes, as separate commits per owner so the lead can pick), or patch files?
3. `scan_holds` keyword-only and insertion minimum 12 (recommended), or o140's forms?
4. P1c: supply `tickets/P1c.md` revision 7 and the corpus, or cut P1c from this round (recommended: supply; else cut with a ledger row, item 3 only).
5. G5 wording text above: OK or changed.
6. Order: G0, then F body, then G1, G2, G3, G6 (recommended).
7. Is every pilot image on a Python with Unicode 15.1.0 (G1-I7)? Otherwise the start-up check stops pilots.

## NOT CHECKED
Nothing was executed on any head or merged tree: no test, lint, import or mutant run. textnorm.py was compared by function names and signatures only. Whether o140's "WIP snapshot, UNVERIFIED" tests pass. Whether hypothesis is in the test group. Indirect use of `runmap.canonical` by redact.py. The baselines (lead). CI state of #63, #70, #77. Whether refs/inputs/* still equal the remote heads.

## AMENDMENT 1 (ORDER 010)
Written 2026-11-20 after the lead's ORDER 010 and lead note 05:59Z. Nothing above is rewritten; where this section and the text above differ, this section holds.

1. REQUIREMENT (answers LEAD decision 7 above; G1-I7): pilot and prod need a Python whose Unicode data is 15.1.0 (3.13). Otherwise the start-up check `textnorm.require_pinned_unidata`, which `app.build` calls for pilot and prod (src/hadavin_sdk/app.py:134), refuses to start: it raises `UnidataMismatch` and nothing runs. Python 3.12.3 carries Unicode 15.0.0 (measured on the build box), so every pilot and prod image must be on 3.13. The check is NOT loosened. The same sentence is in README.md ("Python version") and in the fold's CHANGELOG entry.
2. E4 DECISION (ORDER 010 item 1, option a): the stricter rule (b) of P1a fix8 (rebase/P1b-o140) stays: a Latin word carrying a spacing mark (Mc) of a script that no letter of the word owns IS flagged by `has_mixed_script`. Round 1 item M16 (core/P1b-fixwip) wanted it not flagged. One clause of `tests/test_textnorm_round1.py::test_m16_a_spacing_mark_or_modifier_symbol_does_not_split_a_mixed_script_word` changed from `has_mixed_script("ab" + U+0903 + "cd") is False` to `is True`, with a comment naming both heads; the Cyrillic clause of the same assert (Cyrillic + U+0903 + Cyrillic is False) does not depend on the decision (both rules need a Latin letter) and is unchanged. New test pinning the case by name: `test_order010_a_latin_word_carrying_a_foreign_spacing_mark_is_flagged_as_mixed_script`. No other test was edited.
3. MUTANTS: none added, counts unchanged (240; 228 behaviour, 12 wording). P1a fix8's own mutants "mixed: rule (b) is never true" and "mixed: a spacing mark splits the word" cover the flagged case; both were run through the runner on the fold after the test change and both are KILLED by `test_a_spacing_mark_or_symbol_cannot_hide_a_mixed_word_and_a_mark_of_the_words_own_script_does_not_flag` (raw tail in evidence/G1-fold.md, "ORDER 010 fixes"). The other 238 mutants were not run.
4. `contains` (ORDER 010 item 3): `evidence.contains` finds MORE than main when an invisible character (U+200B, U+00AD, U+2060) sits between a letter and its accent. ACCEPTED by the lead as the stricter side; `runmap.composed` keeps its order (invisible characters removed first) and the named test in tests/test_evidence_decomposed.py stays as the pin.
5. WHAT THE PYTHON 3.12 CI JOB DOES AFTER THE FOLD (read, NOT run: no test was executed on 3.12 here). pyproject.toml has `requires-python = ">=3.12"`; .github/workflows/ci.yml job `tests-py312` runs `pytest -q -n 3 -m "not live and not perf" -rs` on Python 3.12, so it collects every `tests/test_textnorm*.py` file. On 3.12 (Unicode 15.0.0) the autouse fixture `_pilot_builds_on_an_interpreter_with_other_unicode_data` in tests/conftest.py replaces `textnorm.require_pinned_unidata` by a no-op for every test module whose name does NOT start with `test_textnorm`, so tests of other things that build a pilot app still start. For the `test_textnorm*` modules the guard stays real: they are not skipped and not marked 3.13-only; they run on 15.0.0, where every check name carries the tag `alg=fold5|ud=15.0.0`, the tests that need a given version stub `unicodedata.unidata_version`, and the golden test reads the 15.0.0 section of the golden file. So the job is expected to run the textnorm tests and stay green, but that is UNVERIFIED until the lead's 3.12 run on the fold. So `requires-python >=3.12` now means "demo and tests"; pilot and prod are 3.13 only. pyproject and CI were not changed.
6. LEAD NOTE 05:59Z, the 3.12 failure on input head core/P1a (`tests/test_textnorm.py::test_the_deny_check_false_matches_on_the_names_lists_are_exactly_the_listed_pairs`, keys stamped `ud=15.0.0`).
   - What is true in the code: the stamp is the design, not a fault. `key_tag()` returns `""` on the pinned Unicode version and U+E000 + `alg=fold5|ud=<interpreter version>` + U+E000 on any other; `identity_key` and `_keys` (behind `identity_keys`) put it in front of every check name, so a check name made on 3.12 NEVER equals one made on 3.13. Measured on the fold with the version stubbed to 15.0.0: `identity_key("Alice")` = tag + `alice`; `identity_keys(U+0903)` = (tag + U+0903, tag).
   - Why the test fails on core/P1a: a slip in the TEST of that head. core/P1a (27ae996) line 2964 asserts `"" in textnorm.identity_keys("ः")`; on 3.12 the empty check name is the tag alone, so `""` is not in the tuple. rebase/P1a (8ca324e), rebase/P1b-o140 and the fold (tests/test_textnorm.py:3023) assert `textnorm.key_tag() in textnorm.identity_keys(...)` instead, which holds on both versions (measured with the stub: True, True; `could_be_same_person(U+0903, U+200B)` True). So the failure is INHERITED on core/P1a and is already repaired in the fold; core/P1a is not the fold's base.
   - How conftest treats it today: the pin-guard fixture leaves `test_textnorm.py` alone (guard real, no skip), so the test runs on 3.12 in the `tests-py312` job; nothing marks it 3.13-only.
   - Recommendation, stricter first: (1) keep the tag and keep the test on both interpreters, no marker (the fold's form of the assert already passes with the tag). The fold must NOT give the same key on both: its results depend on the interpreter's normalisation, categories and case folding, so an untagged key from 15.0.0 could silently equal or miss a 15.1.0 key; the tag makes the difference loud. (2) Not recommended: mark it 3.13-only; that would drop the only coverage of the tagged path of this check on 3.12. (3) Not recommended: drop the tag so keys are equal; that loosens the pin the start-up check protects. No test and no code was changed for this point. UNVERIFIED: the test was not run on a real 3.12 on the fold (only with the stubbed version on 3.13).
7. LOOK-ALIKE TABLES (ORDER 010 item 2, reading only, nothing built): the shipped tables `guard/_confusables.py` and `guard/_scripts.py` do NOT remove the dependency on the interpreter's Unicode version. They cover only the look-alike mapping and the Script property of rule (a). textnorm.py still asks the interpreter at run time for `unicodedata.normalize` (NFKD and NFKC, in every fold), `unicodedata.category` (which characters are dropped, Mc, Lm, Sk, Pd, Cn), `unicodedata.name` (`_script_of`, `_is_greek_letter`: the script groups of the script views and of rule (b)), and the `str` methods `casefold`, `isalpha`, `isalnum`, `isspace`, `isdigit`. Removing the dependency would mean shipping normalisation, General_Category, names and case folding data too (a full pinned Unicode library), not these two tables.
