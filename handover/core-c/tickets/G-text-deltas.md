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
