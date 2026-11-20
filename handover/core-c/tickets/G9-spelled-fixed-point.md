# G9: the sweep to a fixed point over the text read with its placeholders put back, at most 4 passes, refused past them (ORDER 023, escalation E10)

Status: DRAFT v1 (complete; every section measured unless section 14 says otherwise) for plan review, core-c drafter, 2026-11-20. Nothing is built. Base of every measurement: cloud/core-c e8ff6de2b
(G7 fix round 6 9d8bc580a and E9 `_OWN_OUTPUT` e8ff6de2b merged). Measured on clean `git archive` copies of e8ff6de2b in the drafter's
scratchpad (`g9d/head`, the base as is; `g9d/proto`, this design applied by the script `g9d/scripts/make_proto.py`). The shared tree was not
edited; no test was run in it. Scripts (scratch, not in the repo; the builder commits the ones named in section 8 under evidence/):
`g9d/scripts/{naive,cases,corpus_diff,check_cases,fuzz,cost,curl,hostile,mut}.py`, `g9d/proto/tests/test_g9_new.py`.
Machine: 4 cores, load 3 to 6 from other sessions during the runs (timings are best-of-2 thread CPU, not a quiet box).

## 0. The finding that shapes the design (measured)
THE PLAIN LOOP DOES NOT CLOSE E10. Iterating today's `_Redactor.sweep` (or `_spelled_sweep`) on its own output reaches a fixed point at
the SECOND pass in all three reproduced cases, with the leak intact (`naive.py` on `head`, exact outputs):
| case | input | pass 1 | passes 2, 3, 4 |
|---|---|---|---|
| (a2) plain values `<SECRET_1>`=`abcdefgh`, `<SECRET_2>`=`efghijkl` | `abcdefghijkl` | `<SECRET_1>ijkl` | unchanged |
| (a1) V=`ab9x`, F1 `<BEARER_1>`=V+`ab` (written `<SECRET_1>ab`), F2 `<BEARER_2>`=`xyz`+V (written `xyz<SECRET_1>`) | `see xyzab9xab end` | `see <BEARER_2>ab end` | unchanged |
| (b) F1 registered; `xyz<SECRET_1>ab` swept (round 2); then F2 registered | `xyz<BEARER_1>` | `xyz<BEARER_1>` | unchanged |
The swallowed characters are hidden by a placeholder, so no pass that reads the text as it stands can see them. A pass that can change these
texts must read the text WITH THE PLACEHOLDERS PUT BACK. In G9 a PASS is therefore: the sweep as today, then an OVERLAP CHECK on the
text read back; the loop iterates that to a fixed point (a pass whose check finds nothing) and is bounded by 4 passes, refused past them.
This keeps the lead's frame (fixed point, bound 4, refuse, no derived-form registration, no new quadratic cap) and adds the one thing that
makes the iteration see the leak. It also answers the lead's question on the literal sweep: YES, the same loop covers it (the check is
defined over stored values, not over written forms), and it must, because case (a2) needs no compound value at all.

A NATURAL input reproduces (a2) through every entry point with no seeded map (`cases.py`, base output):
`redact("password=abcdefgh\ntoken=efghijkl\nsee abcdefghijkl")` -> `password=<SECRET_1>\ntoken=<SECRET_2>\nsee <SECRET_1>ijkl`
(`ijkl`, the tail of a secret the map holds, readable; `redact_many` and `runmap.redact_text` give the same last line). The gate does the same:
`runmap.enforce_map("x abcdefghijkl y", {...both...})` -> `x <SECRET_1>ijkl y` (already a stated limit of the gate, pinned:
tests/test_runmap_enforce_map.py::test_stated_limit_partial_overlap_leaves_a_tail, tests/test_model_gate.py::test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent).
Case (b) has still no natural input through a call (as G7 round 6 said); it is reproduced at the `_Redactor` level as in g7r6_overlaps.py.
Random search (`fuzz.py`, 20,000 inputs, 2 to 5 SECRET values of 4 to 7 letters over `abc`, text of 1 to 4 words, seeded map, seed 7):
base 190 leak (an independent oracle: a stored value whose occurrence in the read-back output covers a readable character and part of a
placeholder), 19,810 clean. Three of the base leaks: map {cabb, bbabaca, bbaca, aaabba, babb}, text `bcaabbcbcbabbab acbabbacaccaaac` ->
`bcaabbcbc<SECRET_5>ab acba<SECRET_3>ccaaac`; map {cbcaa, ccbab, bcaa, bbaabbc, babaaa}, `ccbabaaaccbb abbaabb` -> `cc<SECRET_5>ccbb abbaabb`.

## 1. Goal
After every `_Redactor.sweep`, no stored value (or alias key) that the sweep's own rule would replace occurs in the text READ BACK (every
placeholder this redactor wrote put back to its value) covering both a readable character and part of a placeholder. A run of such
occurrences is registered whole (the existing `_place_union`, one entry per run actually found) and replaced. A sweep that has not reached
that state after 4 passes is REFUSED (`InputTooLarge("SpelledNotSettled")`), never returned. A redactor that may not register (the gate's)
refuses the first overlap (`InputTooLarge("SpelledOverlap")`). E10 (a) and (b) are closed; the two stated-limit pins are replaced.

## 2. Problem (the code at e8ff6de2b, by name)
- `_Redactor.sweep`: `_spelled_sweep` (written forms, run-merging union inside ONE scan), then the literal sweep per free segment, longest
  value first. Both read only the free text between placeholders.
- (a) literal sweep: `str.replace` of the longer value first; the shorter value that overlaps it no longer matches what is left. Older than G7.
- (b) `_spelled_sweep` in a later round: the earlier form's placeholder covers the part the later form needs.
- `settle` loops "table, then sweep" to a fixed point of TEXT CHANGES (cap `_SETTLE_ROUNDS` 4); a text that stops changing with a leak
  inside is settled by that definition, so settle's own loop cannot see E10 either.

## 3. Files
- src/hadavin_sdk/guard/redact.py: `_Redactor.__init__` (`_written`, `_may_register`, `_longest`), `sweep` (the pass loop),
  new `_sweep_once` (today's body of `sweep`, unchanged but for the shared work count), new `_overlaps`, new `_union_spans`,
  `_spelled_sweep` (takes the shared count), `_build` and the cached-state path (`_longest`), `_place`, `_mask`, the literal replacement
  and the spelled replacement (each adds the placeholder it wrote to `_written`), `redact` and `redact_many` (`r._may_register = True`),
  `_place_union` (kind rule, D-3), docstrings of `_spelled_sweep` (the "two OPEN limits" paragraph replaced) and `settle` (the pass loop and the bounds), module docstring line on overlaps.
- src/hadavin_sdk/defaults.py: `SPELLED_MAX_PASSES = 4` after `SPELLED_MAX_WORK`; the comment of `SPELLED_MAX_WORK` (the count is per sweep CALL,
  shared by every pass, and includes the read-back; the "Two OPEN limits (E10)" sentence replaced).
- tests/test_redact_settle_loop.py: replace `test_an_overlap_completed_only_in_a_later_round_leaves_the_swallowed_part_readable_a_stated_limit`
  and `test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit`; add the G9 block (section 7); edit the controls of
  `test_5000_compound_secrets_at_the_size_cap_the_trie_walk_is_not_dict_misses` and `test_the_scan_does_not_depend_on_how_many_distinct_prefix_lengths_are_registered` (section 8, phase 2).
- tests/test_redact_context_after_sweep.py: no test went red on the prototype (68 + E9's changes, all green); add one overlap row through
  `redact_text` with a seeded map only if the lead wants the pin in both files (default: no edit).
- tests/redact_mutants.py: the mutants of section 10, appended at the END of `M` (after E9's and Q9's rows; anchored by text, not line).
- tests/test_runmap_enforce_map.py and tests/test_model_gate.py: the two gate stated-limit pins (only under L-D1 default; owner core-b/F lane, see L-D1).
- handover/core-c/ESCALATIONS.md: E10 -> RESOLVED (by G9, with the commit), the gate limit noted under L-D1.
- handover/core-c/tickets/G7-context-after-sweep.md: ROUND 6 "M-B (a) ... and M-C / E10 (b)" bullet and "SECURITY wording to add": the two overlap limits replaced by section 13.
- handover/core-c/evidence/G9-1.md (raw output of phases 0-4) and evidence/g9_*.py (the scratch scripts, path-bound fixed).

## 4. Design (exact; the prototype is `make_proto.py`, v1+v2+v3 parts)
### 4.1 The loop (`sweep`)
```
def sweep(self, out, deadline=None):
    work = [0]                                  # ONE count for every pass of this call: spelled scans, read-backs, unions
    for passes in range(1, defaults.SPELLED_MAX_PASSES + 1):      # 4
        out = self._sweep_once(out, deadline, work)                # today's sweep: build if needed, _spelled_sweep, literal sweep
        spans = self._overlaps(out, deadline, work)
        if not spans:
            return out                          # converged: this pass found no overlap and registered nothing
        if not self._may_register:
            raise InputTooLarge("SpelledOverlap")                  # the gate: cannot add to the run map
        out = self._union_spans(out, spans, deadline, work)        # registers each run whole, replaces it
    raise InputTooLarge("SpelledNotSettled")
```
- Where it lives: INSIDE `sweep`, so every caller of `sweep` gets it: the first sweep of `redact`/`redact_many`, every sweep of `settle`, the
  gate (`runmap.enforce_map`'s `first.sweep`) and `held_value_left`'s checker. Not a sub-loop of `settle`: case (a) has no settle round in it
  (`redact` with a seeded map and one string), and the gate has no settle.
- A PASS = `_sweep_once` + `_overlaps` (+ `_union_spans` when it found something). CONVERGED = a pass whose `_overlaps` returns nothing (so
  it changed no text and registered nothing after the body). An honest text costs ONE pass: the body as today plus one read-back.
  (Re-running the body as the convergence test would double every sweep; the check is the convergence test.)
- Refusal text: `SpelledNotSettled` (and `SpelledOverlap` for the gate), both `InputTooLarge` like `SpelledWorkTooMuch`.
### 4.2 The read-back (`_overlaps(out, deadline, work)`)
- Returns [] at once (no clock read, no work) when the map has no rule (`not (self._finders or self._slow)`), `out` has no `<`, or no token of
  `out` is in `self._written` (pinned by `test_the_segment_check_reads_the_clock_at_the_first_free_segment_then_every_32nd`, which went red on a prototype that read the clock first).
- `self._written`: the placeholders THIS redactor wrote (`_place`, `_mask`, the literal and spelled replacements, `_union_spans`). A token
  the redactor only read (in the input, forged or from a model) is NOT read back: it is a NUL separator. So a text of forged tokens costs nothing, and
  the gate's model-written placeholders are read back only when the gate's snapshot redactor has written that name before.
  (Measured: without this filter the property corpus showed 13 read-back hits on entity-encoded inputs in a SECOND `redact_text` of the output, see 9.6; with it, 0.)
- E = `out` split at placeholders; free text as is; a run of consecutive tokens is put back to their values, but only the first and the last
  `self._longest - 1` characters of the run's expansion are kept (a NUL between), on a side that touches free text (a run with no free text
  on a side keeps nothing on that side). `_longest` = the longest rule original (set in `_build` and on the cached path). No occurrence that
  covers a readable character can reach further into a run than that.
- Work: one unit per character of E, ADDED WHILE E IS BUILT (refused past `SPELLED_MAX_WORK` as soon as the running total passes it; the
  prototype adds after building: the builder must count per piece, see 9.5), plus one per occurrence found; deadline read once per
  read-back (after the cheap returns) and in `_union_spans` per span.
- Occurrences: the existing finders over E (`finder.finditer(E)` and each match's `prefixes`), `self._slow` by `str.find`; a word with
  `_STANDALONE` rule counts only when no ASCII letter or digit touches it IN E (the same rule as `_replace_standalone`).
- An occurrence is an OVERLAP when the E segments it covers include at least one readable (free) segment AND at least one placeholder segment.
  (Placeholders only: nothing readable. Readable only: the literal sweep's job; such an occurrence cannot exist after `_sweep_once` for an
  every-copy value, and for a standalone one it fails the same rule: mutant G9-6 is equivalent, section 10.)
- Span in `out` coordinates: a placeholder touched is taken WHOLE; readable text exactly as far as the occurrence reaches. Overlapping spans are merged
  (transitively, sorted by start) so a chain is one run in one pass.
### 4.3 `_union_spans(out, spans, deadline, work)`
For each merged span: `placeholder = self._place_union(out[a:b], first)` (existing: the value is the span with its placeholders put back; a
value already in `reverse` gets its placeholder; else `_place`, which also registers the span's written form via `_spell`), replace,
`self.actions += 1`, `_written.add`. Work: one unit per character of the span. Unions are made with no journal open (as today's unions):
never rolled back.
### 4.4 Numbers
- `defaults.SPELLED_MAX_PASSES = 4`. Measured need: 1 pass for every honest text, 2 for a text with an overlap (section 9). Never 3 or more on
  any input built or searched (20,000 random overlapping inputs: max 2). Argument: a union does not change E (its value IS the run's
  characters), every occurrence that made the run now lies inside one placeholder, and the body of the next pass has only less free text;
  so pass 2's check finds nothing. The bound 4 is a fail-closed margin, as `_SETTLE_ROUNDS` is; passes 3 and 4 are reached only by a stub in the tests.
- Bounds multiply ONLY in time: `settle` makes at most 4 rounds after the first sweep, each sweeping each string once: at most 5 `sweep`
  calls per string per call; each `sweep` at most 4 passes: at most 20 sweep bodies per string. WORK is bounded per `sweep` CALL (one count
  shared by its passes: at most `SPELLED_MAX_WORK` = 4,000,000 units of spelled scan + read-back + unions), so per string per call at most
  5 x 4M units, and the call's deadline (`REDACT_BUDGET_S`) bounds the whole when passed. With no deadline: 4M units per sweep, no total bound (as today, stated).
- Memory: E is transient, at most `len(out)` + 2 x (`_longest` - 1) per run of tokens, and refused past 4,000,000 characters (16 MB worst for a
  4-byte str, about 4 MB for ASCII); a union adds one map entry and its spelled form (trie nodes about its length), as G7's unions do.

## 5. Decisions made (drafter)
- D-1 The loop is in `sweep` (all callers), not in `settle`.
- D-2 The convergence test is the read-back, not a second body run (honest = 1 pass, no doubled sweep).
- D-3 The union's kind: a SECRET kind when any placeholder in the span or any overlapping value is of a SECRET kind, else the kind of the first
  placeholder (today `_place_union` takes the first form's kind; with plain values an IPV4 first token would give a SECRET run an identifier's
  standalone rule). NOT in the prototype (it used the first token's kind; every measured case had SECRET first): unverified, the builder adds the test `test_g9_the_union_of_an_identifier_and_a_secret_is_a_secret`.
- D-4 Only tokens this redactor wrote are read back (`_written`; cost, forged tokens, the gate's model text).
- D-5 No derived-form registration, no new cap by count: unions only of runs actually found; the only new limit is the pass bound.
- D-6 The read-back is counted in the existing `SPELLED_MAX_WORK` (shared per sweep call), not a new limit.

## 6. Decisions for the lead (build default first)
| id | question | default | consequence | fallback | consequence |
|---|---|---|---|---|---|
| L-D1 | the gate (`enforce_map`, `held_value_left`): a redactor that may not register | REFUSE an overlap (`SpelledOverlap`, an `InputTooLarge`) | the gate's Trap 3 stated limit is closed fail-closed: a model call whose text overlaps two known values is refused (availability); two gate pins (`test_stated_limit_partial_overlap_leaves_a_tail`, `test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent`) become "refused" tests: a core-b / gate-lane edit; the two-identifier row of the first stays (no standalone copy, nothing replaced) | the check is skipped when `_may_register` is False | gate unchanged, its Trap 3 stays a stated limit; G9 closes E10 for `redact`/`redact_many`/`redact_text` only |
| L-D2 | the pass bound | 4 (`SPELLED_MAX_PASSES`) | margin of 2 over the measured need | 2 (the measured need) | no margin; a future rule that needs a third pass refuses texts |
| L-D3 | work count | shared per `sweep` call (one 4M for all passes) | the honest worst grows from 305k to 351k units (section 9.3), headroom 11x | per pass | up to 4 x 4M per sweep |
| L-D4 | union kind (D-3) | strongest kind of the run | a run with a SECRET part is swept in every copy | first token's kind (as G7) | an identifier-first run with a secret tail is swept only standalone |
| L-D5 | the entity-encoded neighbour (9.6), a decoded view's overlap | out of G9 (views are G1/G10's) | `&#49;<IPV4_3>` stays as today | read back the views too | cost per view; not designed |

## 7. Acceptance tests (added to tests/test_redact_settle_loop.py; the scratch copy `g9d/proto/tests/test_g9_new.py` holds the measured text)
Helper `_registering(mapping)` = `R._Redactor(mapping)` with `_may_register = True`. SHORT = `"ab" + "9x"` (the file's).
| test | input | expected |
|---|---|---|
| `test_g9_an_overlap_completed_only_in_a_later_round_is_masked_whole` (REPLACES the round3 pin) | map `<SECRET_1>`=SHORT; F1 `_place("BEARER", SHORT+"ab", "<SECRET_1>ab")`; `round2 = r.sweep("xyz<SECRET_1>ab")`; F2 `_place("BEARER", "xyz"+SHORT, "xyz<SECRET_1>")`; `round3 = r.sweep(round2)` | `round2 == f"xyz{f1}"`; round3 is one placeholder, not f1 or f2 (measured `<BEARER_3>`), value `xyzab9xab`; `r.sweep(round3) == round3` |
| `test_g9_two_overlapping_values_in_raw_text_are_masked_whole` (REPLACES the raw pin) | map {`<SECRET_1>`: `abcdefgh`, `<SECRET_2>`: `efghijkl`}, `sweep("abcdefghijkl")`; F1/F2 as above, `sweep("see xyz"+SHORT+"ab end")` | `<SECRET_3>` = `abcdefghijkl`; `see <BEARER_3> end`, value `xyzab9xab` |
| `test_g9_the_raw_overlap_through_redact_redact_many_and_redact_text` | `password=abcdefgh\ntoken=efghijkl\nsee abcdefghijkl`, no map | `redact`: `password=<SECRET_1>\ntoken=<SECRET_2>\nsee <SECRET_3>`, `<SECRET_3>`=`abcdefghijkl`, restore == input; `redact_many(lines)` the same three; `redact_text(...).endswith("see <SECRET_3>")` |
| `test_g9_a_redactor_that_may_not_register_refuses_an_overlap` | bare `_Redactor` with the two plain values, `sweep("abcdefghijkl")` | raises `InputTooLarge`, match `SpelledOverlap` |
| `test_g9_a_sweep_that_settles_in_the_fourth_pass_is_accepted` | `_overlaps` stub reporting `[(0, len(out), out)]` for 3 passes then [], `_union_spans` stub identity; `sweep("x <SECRET_1> y")` | returned unchanged; 4 check calls == `SPELLED_MAX_PASSES` |
| `test_g9_a_sweep_that_has_not_settled_after_four_passes_is_refused` | stub for 4 passes; then a stub that never settles | `InputTooLarge` `SpelledNotSettled` both; exactly 4 check calls each |
| `test_g9_through_redact_a_refusal_is_raised_not_returned` | class-level stub reporting an overlap whenever `<` is in the text; `redact("password="+SHORT+"qrstu")` and `redact_text(...)` | `RedactionError` match `SpelledNotSettled` (InputTooLarge is a RedactionError) |
| `test_g9_an_honest_text_settles_in_one_pass` | `find` then `sweep` of `password=`+SHORT+`qrstu and token=`+SHORT, counted `_overlaps` | 1 call |
| `test_g9_the_check_is_counted_in_the_sweeps_work` | the two plain values, text `"abcdefgh x"` x 2000 joined by space, `SPELLED_MAX_WORK` patched to 1000 | `SpelledWorkTooMuch` |
| `test_g9_the_union_of_an_identifier_and_a_secret_is_a_secret` (D-3, NOT run) | map {`<IPV4_1>`: `10.0.0.5`, `<SECRET_1>`: `0.5xqzw`}, `sweep("10.0.0.5xqzw")` | one placeholder of kind SECRET |
| (gate, L-D1 default) the two gate pins rewritten | `abcdef` with `abcd`/`cdef` | `InputTooLarge("SpelledOverlap")` / the gate's refusal code |
Fail-before (measured, the 9 written tests copied into the `head` archive): 9 failed (the first three on their asserts, e.g.
`assert ('<SECRET_1>ijkl' == '<SECRET_3>')`; the rest on `no attribute '_overlaps'` or `DID NOT RAISE`). On `proto`: 9 passed.

## 8. Build order, phases, commands (prefix `uv run --all-extras --group test`; `-n 3` at most; `uptime` first)
Order: after G7 round 6 (merged) and E9 (merged, e8ff6de2b). Q9's mutants and any E9 follow-up add at the END of tests/redact_mutants.py: G9's rows go after
them; on a textual conflict in `M`, keep both and re-run. G4 / G8 touch PATTERNS and `_replace_standalone`'s neighbours, not `sweep`/`_spelled_sweep`: independent; G8's
G8b edits the literal-sweep call (`_replace_standalone` call in `sweep`'s body): whichever lands second moves that edit into `_sweep_once` (by name).
Phase 0 (no code): base sha; derive every anchor BY NAME (`def sweep`, `def _spelled_sweep`, `def _place_union`, `def _build`, `SPELLED_MAX_WORK =`), not by line.
`python handover/core-c/evidence/g7r6_overlaps.py`: green = the base lines of section 0. Copy section 7's tests in: green = 9 failed as listed.
Phase 1 (redact.py, defaults.py, section 4). `pytest -q -m "not perf" tests/test_redact_settle_loop.py tests/test_redact_context_after_sweep.py tests/test_redact_idempotent_property.py -n 3`.
Expected red, exactly (measured on proto): `test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit` (replaced in phase 2),
`test_5000_compound_secrets_at_the_size_cap_the_trie_walk_is_not_dict_misses` (its control sets `r._spelled = {}`: the read-back now finds
the 5,000 `copy <UUID_n>.k_i` runs itself and the bare redactor refuses `SpelledOverlap`), `test_the_scan_does_not_depend_on_how_many_distinct_prefix_lengths_are_registered`
(with_many 0.185 s vs with_one 0.042 s: the read-back's finder pass over the 300 nested cookie values costs more on `many`; it is not the P x S scan).
The later-round pin stays GREEN in phase 1 (it calls `_spelled_sweep`, not `sweep`) and is replaced in phase 2. Whole measured state: `4 failed, 1992 passed` (the 4th was the clock test before the v3 early return; 3 with it).
Phase 2 (tests): replace the two pins; add section 7; the two controls measure the scan alone: `monkeypatch.setattr(r, "_overlaps", lambda *a: [])` in BOTH runs of each ratio
(the scan's ratio is what those tests pin) plus a new perf test `test_g9_the_read_back_costs_at_most_one_finder_pass` (cookie 300 + copies: read-back time < 1.5 x one `_sweep_once`; NOT measured as a test).
Green: the three files all pass. Then the gate pins (L-D1). Then `pytest -q -m "not perf and not live" -n 3 tests/test_redact*.py tests/test_runmap*.py tests/test_model_gate*.py tests/test_k1b*.py tests/test_s6_approvals.py tests/warden_port`:
measured on proto before the test edits: `5 failed, 3325 passed, 3 skipped, 4 xfailed` (the 3 above + the 2 gate pins); green after = 0 failed.
Phase 3: `ruff format`/`ruff check`; full suite `-m "not perf and not live" -n 3 tests` (NOT run by the drafter); perf files `tests/test_redact_settle_loop.py tests/test_k5_perf.py tests/test_redact_fold_budget.py -m perf -p no:xdist`.
Phase 4: `python tests/redact_mutants.py G9` (section 10); green: all G9 rows good, no new BAD in the rest.
Phase 5: docs (section 13), ESCALATIONS E10 RESOLVED, G7 ticket wording, evidence/G9-1.md.

## 9. Measurements (proto vs head, e8ff6de2b)
9.1 The cases (`cases.py`): (a1) `see <BEARER_3> end` (`<BEARER_3>`=`xyzab9xab`), 2 passes; (a2) `<SECRET_3>`=`abcdefghijkl`, restore `abcdefghijkl`, 2 passes;
(b) round 3 `<BEARER_3>` value `xyzab9xab`, 2 passes; `redact` with the seeded map `x <SECRET_3> y`, restore exact; `redact_many` `['x <SECRET_3> y', 'z <SECRET_2>']`;
`redact_text` `x <SECRET_3> y`; natural input -> `...see <SECRET_3>`; gate `enforce_map` -> `InputTooLarge SpelledOverlap`.
9.2 Pass distribution (instrumented proto, per `sweep` call): property corpus 1,836 inputs through `redact()` + `redact_text()` (`corpus_diff.py`): 7,246 sweep calls, all 1 pass, 0 overlaps;
outputs byte-identical to head for all 1,836 (redact and redact_text), restore failures 63 on both (the corpus' own, unchanged), second redact changes nothing on both.
The property test file run whole (1,842 tests): 11,168 sweep calls, all 1 pass, 0 overlaps. The settle-loop generator (`test_generated_compositions...`, 2,000 compositions): 86,264 sweep calls, all 1 pass, 0 overlaps.
Random overlap search (`fuzz.py` 20,000): head 190 leak; proto 0 leak, 0 refused, 0 restore differences, 0 second-redact changes; passes {1: 20,000, 2: 191}.
9.3 Cost, honest worst shapes, `redact_text` with a fresh RunMap, best of 2, thread CPU, s (head -> proto), max units per sweep on proto (spelled + read-back):
curl -u at cap 2.22 -> 2.19 (0); password= at cap 0.86 -> 0.94 (288,357); jar 330x64 + copies to cap 0.42 -> 0.58 (307,641); jar 275x128 0.37 -> 0.53 (275,274);
cookie 300 prefix lengths + copies 0.22 -> 0.35 (350,609); signed ids 300 + copies 0.43 -> 0.42 (274,878); 5,000 `password=uuid.k_i` 0.99 -> 1.07 (264,998).
Every shape 1 pass. `redact_untrusted` at the cap: curl -u 2.20-2.30 -> 2.21-2.33; password= 0.84-0.86 -> 0.93-0.94. Worst units 350,609 = 8.8 % of 4M (11x headroom).
The defaults.py figure "curl -u 4.5 to 5.4 s" was NOT reproduced on this box (2.2 s here): the ratio, not the absolute, is the result.
9.4 Mutants (`mut.py`, against the section 7 tests): 5 of 6 killed (section 10); G9-6 survived: equivalent by reading.
9.5 Hostile read-back (`hostile.py`): `password=` + a 2,000-character secret, then `x<SECRET_1> ` repeated to the cap (forged copies of a placeholder the
redactor DID write, so `_written` does not filter them): head returns the text (1.46 s, peak 3 MB traced); proto REFUSES `SpelledWorkTooMuch` after 1.68 s,
peak 56 MB traced, because the prototype builds the whole E before counting. Hence the design rule of 4.2: count per piece while E is built and stop at the
limit (E then never exceeds 4M characters). Honest raw copies cannot do this: each written token's read-back is at most the raw characters it replaced, so E is
bounded by the input; only tokens present in the input (forged, or a model's) can inflate it: a fail-closed refusal of that document.
9.6 Found on the way, not G9: with every token read back (prototype v1) the property corpus showed 13 overlaps in a SECOND `redact_text` of
round-trip inputs such as output `ERROR &#49;<IPV4_3>` (`<IPV4_3>`=`0.0.0.5`; a decoded view had `10.0.0.5`, another stored value): the
entity-encoded first digit of a known address stays readable as `&#49;` at the base and after G9 (G9 reads the text as written; L-D5).

## 10. Mutants (append at the END of `M` in tests/redact_mutants.py; killer file tests/test_redact_settle_loop.py)
| name | old | new | expect (killer) |
|---|---|---|---|
| G9-1 the bound removed | `for passes in range(1, defaults.SPELLED_MAX_PASSES + 1):` | `for passes in range(1, 10**6):` | KILLED (`test_g9_a_sweep_that_has_not_settled_after_four_passes_is_refused`; with the never-settling stub it hangs: the runner's timeout counts) measured |
| G9-2 the fixed-point loop removed | `spans = self._overlaps(out, deadline, work)` | `spans = []` | KILLED (`test_g9_an_overlap_completed_only_in_a_later_round_is_masked_whole`) measured |
| G9-3 the refusal returns the text | `raise InputTooLarge("SpelledNotSettled")` | `return out` | KILLED (`..._has_not_settled_...`) measured |
| G9-4 the gate registers | `if not self._may_register:` | `if False:` | KILLED (`test_g9_a_redactor_that_may_not_register_refuses_an_overlap`) measured |
| G9-5 the read-back not counted | `work[0] += len(E)` | `pass` | KILLED (`test_g9_the_check_is_counted_in_the_sweeps_work`) measured |
| G9-6 readable-only occurrence counted | `if all(s[4] ...) or not any(s[4] ...)` | `if all(s[4] ...)` | SURVIVED: equivalent (no readable-only occurrence passes the rule after `_sweep_once`); not added |
| G9-7 every token read back (`_written` filter dropped) | `if tok in self._written else None` | `` | expect KILLED by a test that a forged token costs no read-back (not written, not run) |
The old/new texts must be re-copied from the built code (the prototype's names are the design's).

## 11. Stated limits after G9
- A text that needs more than 4 passes is refused (`SpelledNotSettled`): none found; reachable only by a stub.
- The gate (L-D1 default) refuses an overlap; with the fallback, the gate's Trap 3 stays.
- Overlaps that exist only in a DECODED VIEW (entities, escapes, folds) of the output are not read back (9.6, L-D5).
- A token the redactor did not write (forged, from the input) is a separator: an overlap with a forged token's value is not looked for.
- A refusal loses the whole document (fail closed); a hostile author can force it (as `SpelledWorkTooMuch`).

## 12. Risks
- Cost: +0.07 to +0.16 s at the cap on cookie/jar shapes (+30 to 57 %); a slower machine nearer the budget refuses a little earlier.
- The gate refusal (L-D1) is a behaviour change in a lane that is not core-c's alone.
- Order dependence of placeholder numbers: a union takes the next number of its kind when it is found (as G7's unions); deterministic per input.
- Idempotence: a second `redact` of the output changes nothing (measured on 1,836 + 20,000 inputs).

## 13. For SECURITY wording (replaces the two overlap limits of the G7 text)
"Two stored values that overlap in the text (one ends where the other begins), whether found in the same pass or in a later one, are masked
as ONE value: nothing of either stays readable. The check reads the text with the redactor's own placeholders put back, at most 4 times per
sweep; a text that does not settle is refused (`SpelledNotSettled`) and nothing of it is shown. At the model gate, which cannot add values to
the run's map, such an overlap refuses the call (`SpelledOverlap`). A hostile author can force a refusal of the whole document (fail closed). Not
covered: an overlap visible only in a decoded form of the output (an HTML entity or escape before a placeholder)."

## 14. What is NOT verified / NOT YET MEASURED
- The per-piece count of 4.2 (9.5 shows it is needed: 56 MB peak without it) is NOT in the prototype; its memory and time after the change are not measured.
- D-3 union kind (not in the prototype); G9-7 mutant; the perf test of phase 2; the edited controls of the two ratio tests (by reading).
- Full suite (`-n 3 tests`) on proto: not run (only the 13 redactor/gate files + warden_port, 3,330 tests).
- The gate pins rewritten, k1b replay and approvals behaviour under a `SpelledOverlap` at the gate: only that the existing tests pass (they do, except the 2 pins).
- Python 3.12; Windows timings.
- The memory figure of E (by arithmetic only).
