# Ticket G4 v7: P1c redactor gaps (base64 view, whole host names, bare numbers written down)

CHANGED in v7: version 7 is v6 with ONLY the findings of plan review round 6 (tickets/G4-review-6-readiness.md: M1, N2-N6;
tickets/G4-review-6-design.md: M1-M3, N1-N5) and the reconciliation, by name, with G9 v2 (tickets/G9-spelled-fixed-point-v2.md,
DRAFT, sections 7-15 still "[filled below]") and G8 v4 (tickets/G8-glued-rest-gap-v4.md, may still change) applied. A table of
every round 6 finding is section H at the end. Every paragraph changed for v7 is marked "CHANGED in v7"; the rest is v6's text
(its "CHANGED in v6" marks kept). Base of the v7 cites: `cloud/core-c` HEAD 75c3480bb, whose last src/tests commit is 944d143db
(header). What the v7 drafter MEASURED (read-only, `uv run python -B` on the repo's src with in-process patches, or stdlib only;
scripts in the drafter's scratch folder `g4v7_r8/`: `r8.py`, `g4c.py`, `wrap.py`, `count.py`, `g9cost.py`, `g9edge.py`,
`g9tie.py`): the fifth TB-2.8 map and an R8 killer map with G4's tie-break patched into `_Redactor._build` and R8 patched into
`snapshot` (4 point 5, 9.3); N1 and N3 with v6's 5.2/5.3 patterns put into `redact.PATTERNS` (5.2, 5.3); the wrap widths of M3
against a stdlib copy of 3.2's decode rules (3.1); the mutant counts by import (13.3); and, on the G9 v2 drafter's PROTOTYPE
(imported read-only from that drafter's scratch `g9v2/proto/src`, ENCODED added to `SECRET_KINDS` in-process), the read-back cost
of a long ENCODED value and the tie-break interplay (0.3b). Nothing was run as a test; the repository was not edited except this file.

CHANGED in v6: version 6 is v5 with ONLY the findings of plan review round 5 (codebase details, tickets/G4-review-5-codebase.md:
M1, M2, M3, N1, N2 and the L8 kind list) and the reconciliation with G8 v3 (tickets/G8-glued-rest-gap-v3.md; G8-review-3
M1/M2 and G8-review-3-codebase M3: PHONE entries 6-8, `python tests/g8_mutants.py` 30 of 30, oracle line 141, docstring
placement; G8-glued-rest-gap-v4.md, in draft while v6 was written, says the same on these four points) applied. A table of
every round 5 finding is section G at the end. Every changed paragraph is marked "CHANGED in v6"; everything else is v5's text. The v6 drafter verified each
changed claim by READING the tree at bff88a7a1 (and by importing the five mutant lists to count their entries); nothing was run
as a test and nothing new was measured. Section F (round 4) stays; round 5's findings are resolved where each is marked.

Version 5, written by the core-c drafter (opus tier), 2026-11-20. It replaces tickets/G4-P1c-redactor-gaps-v4.md. It takes or
contests every finding of plan review round 4 (tickets/G4-review-4.md, both reviewers; section F at the end). It keeps what v4
resolved from rounds 1-3 (sections A, D, E, now written out here, so no earlier version has to be read). A builder with no other
context builds from this file alone: nothing below says "as v3" or "unchanged from v3" without the text. Nothing is built before
plan review round 5 is clean (CHANGED in v6: round 6; CHANGED in v7: round 7).

Base of every claim in this file: `cloud/core-c` at 2e3a081ae+ (09:45Z). Its last commit touching `src/` or `tests/` is e8ff6de2b
("code G: E9 _OWN_OUTPUT restricted to SECRET tokens"); later commits are board and notes only. That tree holds, merged:
- G7 fix rounds 3 (da0f71f), 4 (6783535), 5 (d1384342e) and 6 (9d8bc580a): `settle` is a real fixed point; `redact_text` re-raises
  `RedactionError` as raised; the spelled-form scan is bounded by counted work, `defaults.SPELLED_MAX_WORK = 4_000_000`, refused as
  `InputTooLarge("SpelledWorkTooMuch")`; `SPELLED_MAX_OFFSETS` and `SPELLED_MAX_FORMS` NO LONGER EXIST; G7 r5 deleted the p1c
  parity test (`tests/test_p1c_builders_parity.py`) and there is no `_P1C`, `_p1c_module` or `moved_builders` test anywhere;
- gate round 4 (b83accc) and the flaky-clock fix 833a86b;
- P1d-a rounds 2 (a2dea63) and 3 (61ff6e7);
- E9(2) (e8ff6de2b): `_OWN_OUTPUT` exempts ONLY SECRET tokens (`<SECRET_n>`, `‹SECRET_n›`, cut-off openings of `<SECRET_`); the
  names `_KIND` and `_OPENINGS` are GONE. So nothing in G4 adds ENCODED to an own-output rule (4 point 1, TB-2.2).
CHANGED in v6 (review round 5 M2): the tree now holds, after e8ff6de2b, the following src/tests commits (read: `git log
e8ff6de2b..bff88a7a1 -- src tests`):
- c4d68c6ef (E9(2) fix round 1) and 4fb0b5154 + 6e8bb9820 (ORDER 022 Q9: 30 mutants appended at the END of tests/redact_mutants.py,
  `redact_mutants.M` is 96 = 63 `m(` entries + 3 E9 `Mutant(` entries + 30 Q9 entries; N15 RE-POINTED by 4fb0b5154, its `old` now
  occurs once, in `_build`'s alias loop, redact.py 1958-1960 at bff88a7a1). Review round 5's snapshot was 6e8bb9820;
- bff88a7a1 (G7 fix round 7, landed after that snapshot): redact.py and defaults.py only. It adds `defaults.SPELLED_MAX_CHARS =
  1_000_000` (defaults.py 125, between `SPELLED_MAX_WORK` and `def cut_margin`) and a new refusal `InputTooLarge("SpelledMemoryTooMuch")`
  (the spelled-form registry's memory limit), and drops `redact()`'s second read after a `bank_near` flip. Against e8ff6de2b,
  redact.py lines are +6 from `_OWN_TOKEN` to `redact()` (Q9) and +3 to +42 from `_Redactor` on (Q9 and G7 r7). Every redact.py and defaults.py line of 0.1 is re-derived at bff88a7a1 BY READING; a line is
  a hint, the name is the cite.
CHANGED in v7 (review round 6 readiness N2): after bff88a7a1 the tree holds two more src/tests commits, 1bf4f11ba (Q9 review fixes
F1-F7) and 944d143db (their lint fixes). runmap.py, defaults.py and approvals/ are unchanged (`git diff --quiet bff88a7a1 HEAD`
on them). redact.py loses 3 lines in `_char_class` (around 1000-1030), so every redact.py line from there on is 3 LOWER than v6
said; tests/redact_mutants.py deletes N1 and N14 (`len(M)` = 94: 63 + 3 E9 + 30 Q9 - 2); a new meta test,
tests/test_redact_mutants_meta.py, pins `EXPECTED_COUNT = 94`, checks that every `only_test` exists and that every `old` occurs
exactly once in its file (mutant 21 twice, `OCCURS_TWICE`). Every redact.py line of this file was re-derived by `grep -n` at
944d143db; a line is a hint, the NAME is the cite.
The numbers MEASURED by v5 on its prototype of e8ff6de2b (sections 2-4, 8-10, C) are NOT re-measured on bff88a7a1: Phase 0 (b),
(f), (g) and (h) re-measure them on the builder's base (0.2).
Not in the tree, and handled by the rule of 0.2: CHANGED in v7: G8 (ticket G8-glued-rest-gap-v4, the current draft; order in
0.3), G9 (spelled sweep fixed point, G9-spelled-fixed-point-v2.md, DRAFT v2, with a prototype in its drafter's scratch; order in
0.3b), G10 (text-fold deadline).

guard/runmap.py, approvals/*, tools.py, k1b and agent_loop.py are byte-identical to v4's base cd8d375 (CHANGED in v6: and to
bff88a7a1, `git diff --quiet e8ff6de2b bff88a7a1` on them): every runmap.py and channel.py line of v4 still holds. redact.py and
defaults.py moved (0.1).

How this file was checked (section C lists each item with MEASURED / BY READING / NOT RE-MEASURED). The drafter built a PROTOTYPE of
G4a + G4b (sections 2-4 and 7; no G4c) in a scratch archive of e8ff6de2b (`git archive`, nothing in the repository changed), from
two scratch scripts (`patch_proto.py`, `proto_step.py`), and measured on it, read-only, with `.venv/bin/python -B`:
- the card path of B2 (`channel.clean` of base64 URL and `curl -u` credentials, both neutralise choices), TB-3.13, TB-3.17,
  TB-3.18, TB-3.19 (both numberings), TB-3.20, TB-3.24, TB-3.26 (old and new recipe, with and without its mutant), TB-2.2, TB-2.7,
  TB-2.8 (all four maps, base and prototype), the `SpelledWorkTooMuch` route, the strict-xfail recipes, the TB-3.2 strings;
- the base64 step's own cost on 100,000 characters of snake_case words and paths, and of prose (B6);
- evidence/p1c_probe.py on the base and on the prototype (gap 1: 52 -> 0 leaks; the other 85 base64 rows print the same);
- the snippet-count script of 13.3 at the base and on the prototype;
- a pytest selection of 17 suites on the prototype (section C gives the result).
Box rule kept: one heavy process at a time, `-n 3` at most, `uptime` read before each run (load 3 to 6 on 4 cores during the work).

## 0. Package line
- Package: G4 (plan item P1c, ORDER 006 item 1). Path class: redaction. Extended review: yes (no round cap).
- Lead rule (unchanged): build only a gap that a failing input proves. A gap with no failing input is cut.
- Depends on, all merged: G0, G7 with fix rounds 2-6, gate round 4, P1d-a rounds 2-3, E9(2). The base sha is the first commit of
  `cloud/core-c` that the builder starts from; it is the base sha of the evidence.
- Build order with G8: G8 FIRST, then G4 (0.3, decision L23).
- CHANGED in v6 (review round 5 M3): build order with G9: either side, no dependency (0.3b, decision L25). CHANGED in v7: either
  side still, but the second lander re-pins the rows 0.3b lists as order-dependent (TB-2.8, TB-2.11, test_e5), measured both ways.
- Source of the code: our own (rung 5), with Python stdlib `base64` as the decoder. Nothing is copied from another repository.
- Target files:
  - `src/hadavin_sdk/guard/runmap.py`: the scan refactor and the base64 step; CHANGED in v6 (review round 5 N1): one clause of the
    `enforce_map` docstring (4 point 5).
  - `src/hadavin_sdk/guard/redact.py`: kind ENCODED, `place_encoded`, the host patterns, the `_build` tie-break, the docstring.
  - `src/hadavin_sdk/defaults.py`: 8 constants and 2 comment sentences; SPINE's file, its own commit.
  - `src/hadavin_sdk/approvals/channel.py`: one kind added to `_ASSIGNMENT_KINDS` (L10).
  - `src/hadavin_sdk/approvals/gate.py`: one comment.

### 0.1 Cite table (name, file, line at e8ff6de2b; CHANGED in v7: redact.py lines at 944d143db, defaults.py at bff88a7a1 = 944d143db)
Rule for the builder: a line number is a hint, the NAME is the cite. Before each phase, `grep -n` the name; when the line moved,
go by the name. CHANGED in v6 (review round 5 M2): the runmap.py, channel.py, cards.py, requests.py, gate.py, tools.py, k1b and
agent_loop.py lines are those of e8ff6de2b and still hold at bff88a7a1 (those files did not change); every redact.py and
defaults.py line below was re-derived by `grep -n` at bff88a7a1 (Q9 and G7 r7 moved them; header). CHANGED in v7 (review round 6
readiness N2): those files are also unchanged at 944d143db; every redact.py line of this table and of sections 4 and 5 was
re-derived by `grep -n` at 944d143db (3 lower than v6 from `_Redactor` on; the lines before `_char_class` did not move).
| name | where |
|---|---|
| `redact_text` (def / `_within_cap` / `started =` / `try` / views / `cache =` / first `redact(` / R2 check / pairs / `for view in views:` / except tuple / `mapping.update(current)`) | runmap.py 533 / 554 / 555 / 556 / 560-561 / 562 / 563-565 / 567 / 569-577 / 578-591 / 593-596 / 603-604 |
| `_decoded_masks` (clock read per stored original), `_keep_earlier_masks` | runmap.py 488-521 (502), 524 |
| `_views`, `_held`, `_clean`, `fits_after_nfkc`, `_expanded_len`, `undo` | runmap.py 445, 479, 427, 218, 207, 162 |
| `escape_placeholders`, `neutralise_untrusted`, `redact_untrusted` | runmap.py 354, 372, 377 |
| `_GRAMMAR`, `storable`, runmap `STORED_KINDS`, the import block from redact | runmap.py 233, 286, 44, 25-38 |
| `enforce_map` (overlap sentence of the docstring; `raise RedactionError("NotSettled")`) | runmap.py 688-775 (730-733; 775) |
| `_rules_conflict`, `snapshot` (CHANGED in v7: its `if _rules_conflict(known):` 906, the comment under it 907-909), `held_value_left` | runmap.py 791, 885, 934 |
| HOSTNAME entry of `PATTERNS` (comment above) (CHANGED in v7: the tuple is 407-413) | redact.py 407-413 (400-406) |
| module docstring ("What this is not" paragraph; closing `"""`) | redact.py 1-26 (21-25; 26) |
| `_KEPT_HOST`, `_LABELS`, `_OWN_TOKEN`, `_OWN_OUTPUT`, `strip_ansi` (did not move) | redact.py 861-863, 868, 889, 890, 900 |
| `redact()` (did not move) | redact.py 942 |
| `_Redactor` (counter restore) (CHANGED in v7) | redact.py 1092 (1112-1121, `self.counters: dict[str, int] = dict.fromkeys(_LABELS, 0)` at 1112, `self.counters[kind] = max(` at 1119) |
| `find` (fold-scan call), `settle` (`raise RedactionError("NotSettled")`), `_fold_scan` (`splitlines`) (CHANGED in v7) | redact.py 1163 (1170), 1178 (1258), 1339 (1352) |
| `_decide` (older all-placeholder rule; `_OWN_OUTPUT.fullmatch`), `_place` (CHANGED in v7) | redact.py 1649 (1672-1675; 1680), 1695 |
| spelled scan refusal `raise InputTooLarge("SpelledWorkTooMuch")` inside `_work_refused` (CHANGED in v7) | redact.py 1936 (`_work_refused`, 1933) |
| CHANGED in v6 (G9's names, 0.3b): `_spelled_sweep`, `_place_union`, `sweep` (CHANGED in v7) | redact.py 1791, 1938, 2010 |
| `_build` (alias loop with N15's anchor / sort key / rules loop) (CHANGED in v7) | redact.py 1946 (1955-1957 / 1964 / 1967-1972) |
| `_SETTLE_ROUNDS`, `SECRET_KINDS`, `_kind` / `kind_of`, `_EVERY_COPY`, `_sweep`, `_replace_standalone`, `redact_many` (CHANGED in v7) | redact.py 2082, 2182-2198, 2233 / 2237, 2241, 2246, 2267, 2288 |
| `MAX_MAP_ENTRIES`, `MAX_REDACT_CHARS`, budget comment (first clause / `clean()` clause), `REDACT_BUDGET_S`, `SPELLED_MAX_WORK` (comment), `SPELLED_MAX_CHARS` (comment; G7 r7), `STORED_KINDS` (CHANGED in v6) | defaults.py 24, 45, 52-87 (59-60 / 83-87), 88, 115 (89-114), 125 (116-124), 184 |
| `clean` (first `redact_text` / joined `redact_text`), `_MAX_REREADS`, `SETTLE_NOTE`, `_reread`, `settled`, `_TAGS`, `_ASSIGNMENT_KINDS`, `_neutralise` | channel.py 25-52 (37 / 44), 62, 67, 70, 76-95, 97, 98, 101 |
| `cards._card`, `requests` summary fallback, card text `Plan <12 hex>.` | cards.py 58-63, requests.py 35-51, requests.py 42 |
| `_CONTROL_CHARS`, `strip_controls`, `_PLACEHOLDER_DOT` (comment), `_DOMAIN_LAST`, `_whole_token`, `_outside_code`, `defang_text`, `undefang_text`, `sanitise_text`, `_clean_line`, `withhold_commands` | gate.py 135-146, 172, 241 (239-240), 256, 263, 295, 312, 324, 405, 331-354, 774 |
| `redact_layered` (catches `TooDeep` only) | tools.py 976-983 |
| `redact_bundle` (`redact_untrusted` call / `Counter`) | k1b/redaction.py 172 (188 / 195) |
| agent_loop map ceiling; card None on a raise | agent_loop.py 427, 547; 622-625, 649-654 |
| the patchers of `runmap.redact` (every one must still see each call) | tests/test_k5_round5.py:278; tests/test_k5_tools.py:317 (`broken`) and 339 (`flaky`); tests/test_redact_fold_budget.py:89 (`spy`) and 252; tests/fixtures/p1d_cases.py:261 (`mock.patch.object`, H27's `check_extra`) |
| consumers of `_LABELS` (CHANGED in v7: counters line) | redact.py 868, 1112 (counters); tests/test_redact_context_after_sweep.py:469 (`_place` for every label); tests/test_runmap_enforce_map.py:470 (longest label) |
| property test (`CONSTRUCTED`, `_build`, `p1c.reseed()`, `EXPECTED_INPUTS = 1836`, `P1C_GAP2`/`P1C_GAP3`, count asserts) | tests/test_redact_idempotent_property.py 65-90, 92-122, 114, 285-287, 203-219 |
| neutralise-hook test (`assert len(seen) >= 2`) | tests/test_k5_round11.py 65-74 (74) |
| CHANGED in v6: `test_e5_one_original_under_two_placeholders_follows_the_stronger_rule` (def; docstring; FAIL-BEFORE assert) | tests/test_runmap_enforce_map.py 518 (519-520; 523) |
| CHANGED in v6: gate mutant count pin `MIN_MUTANTS = 105`; gate mutant R8 | tests/test_gate_mutants_picked_up.py 20; tests/gate_mutants.py 190 |
| CHANGED in v7 (tree, header): the redact-mutant meta test (`EXPECTED_COUNT = 94`, `OCCURS_TWICE`, `test_every_search_string_occurs_exactly_once_in_its_file`) | tests/test_redact_mutants_meta.py 16, 17, 67 |

### 0.2 Phase 0 rule for anything merged after the base (by NAME, not by line)
1. `git diff e8ff6de2b <base-sha> -- src/hadavin_sdk/guard/runmap.py src/hadavin_sdk/guard/redact.py src/hadavin_sdk/defaults.py src/hadavin_sdk/approvals tests/fixtures/p1d_cases.py tests/p1d_a_mutants.py tests/redact_mutants.py tests/gate_mutants.py tests/p1c_builders.py tests/test_redact_idempotent_property.py tests/g8_cases.py`.
   An EMPTY diff means go. A NON-EMPTY diff is the normal case (G8 lands first, 0.3; Q9 appends mutants): go on with step 2;
   a non-empty diff alone is never a STOP. CHANGED in v6: at bff88a7a1 the diff is already non-empty (Q9 and G7 r7, header);
   G7 r7's changes to `settle`, `_spell`/`_unspell`, `find`, the union path and the `SPELLED_MAX_CHARS` comment touch no step of
   this ticket and are a line shift for it; G9, when merged, is handled by 0.3b.
   CHANGED in v7: at 944d143db the diff also holds the Q9 review fixes (header): a line shift in redact.py and N1/N14 deleted from
   tests/redact_mutants.py; no step of this ticket is touched. Add tests/test_redact_mutants_meta.py to the diff list of step 1.
2. For each name in 0.1 the diff touches, re-read that function or entry and compare it with the step of this ticket that names it.
   STOP and report only when the change contradicts a numbered step:
   - a new `except` clause in `redact_text`;
   - a second `redact(` call outside `_pass_one`, or a call through a local alias;
   - a change to `_LABELS` or `SECRET_KINDS`, or to the HOSTNAME entry (G8 does not touch it; a change by anyone else is a STOP);
   - a new literal `raise RedactionError("NotSettled")` in runmap.py;
   - a p1d row whose input holds a private host name.
   NOT a stop, but a table update: a change to PHONE, IPV4, IBAN, UUID or CREDITCARD (G8) or to `_spelled_sweep` and its refusal
   text (G9) after the base. Phase 0 (b) then re-runs the probe and TB-3.33's recipe and updates sections 6, 9 and 10 from the run.
   CHANGED in v6 (review round 5 M3): G9 also edits `sweep` (the pass loop; today's body moves to `_sweep_once`), `_build` (its
   `_longest`), `_place_union` (the union kind, D-3), `_place`/`_mask` and the replacements (G9 v1's `_written`), `settle`'s docstring,
   and adds `defaults.SPELLED_MAX_PASSES` and the refusals `InputTooLarge("SpelledNotSettled")` / `("SpelledOverlap")`. None of these
   is a STOP; 0.3b says what the second lander re-checks. A G9 change to the `_build` RULES LOOP (the lines G4 edits, 4 point 5)
   IS a STOP.
   CHANGED in v7 (review round 6 design M1; G9 v2 section 3): G9 v2's names are `sweep` (pass loop), `_sweep_once`,
   `_ensure_built`, `_spend`, `_read_back`, `_overlaps`, `_masked`, `_close`, `_place` (a `derived` parameter), `_place_union`
   (takes a kind), `_spelled_sweep` (a `shared` count), `_longest` (set in `_build` and on the cached path of `__init__`),
   `_may_register` (set by `redact` / `redact_many`), the module constant `_SEP`; the refusals are
   `InputTooLarge("SpelledNotSettled")` and `RedactionError("SpelledOverlap")` (a RedactionError, NOT an InputTooLarge: G9 v2 4.5
   `_close` and L-D1b); runmap.py docstrings of `enforce_map` (the overlap bullet, which holds the clause G4 edits, 4 point 5) and
   `held_value_left`. None is a STOP; the docstring overlap is merged by 0.3b's rule.
   A pure line shift, or a change to a name G4 does not touch, is no stop: re-derive the lines and go on.
3. p1d rows are found by id (`ROW_BY_ID["H27"]`, `["L2"]`, `["L3"]`, `["L11"]`, `["D3b"]`, `["D3c"]`), never by line. Gate rules
   are found by name (`_PLACEHOLDER_DOT`, `_outside_code`, `_per_part`, `_defang_prose`). Section 9.3's three new `after` cells and
   the A4/A5/A38/A6 killers are re-checked in Phase 4 by running them (`python tests/p1d_a_mutants.py A4 A5 A38 A6`). If a killer
   named here no longer kills, STOP and report: no killer is invented.
4. Mutant files: a new mutant appended at the END of tests/redact_mutants.py (Q9, as E9 did) is recorded in Phase 0 (g) like the
   others; G4 edits only R3 and mutant 21's docstring sentence there (13.3). CHANGED in v6: Q9's 30 are in the tree (96 entries),
   and G9's rows, when merged, are appended after them; G4 touches none of them. CHANGED in v7: at 944d143db there are 94 entries
   (N1 and N14 deleted), pinned by tests/test_redact_mutants_meta.py `EXPECTED_COUNT = 94`; G4 adds no entry there, so the pin
   holds; G9's rows raise it (G9's commit edits the pin, not G4's).

### 0.3 Order with G8 (decision L23; review round 4 readiness Major 2 and G8-review-2 Major 1)
The same order is written in G8 v3 (handover core-c reconciles the two tickets).
- Default: G8 merges FIRST, with `G4C_MERGED = False` in tests/g8_cases.py; its rows 64 and 71 (HOSTNAME glued before) are strict
  xfails naming G4c. G4 is built on the tree that holds G8.
- The G4 builder, in the Phase 4 (G4c) commit:
  1. sets `G4C_MERGED = True` in tests/g8_cases.py. That turns rows 64 and 71 into ordinary tests and makes rows 60, 61, 62 and
     66 use their `after_g4c` column;
  2. runs `pytest tests/test_redact_glued_rest.py tests/test_redact_g3_port.py -q -p no:randomly` (the two G8 test files); if an
     `after_g4c` cell differs from the output G4c gives, the cell was measured against an older G4 regex: the builder writes the
     measured output into that cell, records old and new in evidence/G4-1.md, and reports it (a leak in the new output is a STOP);
  3. adds the two G8 files to the run lists of Phases 3, 4 and 5 (12), and CHANGED in v6 (G8 v3 8.1 G4-2, G8-review-3 M1): the
     mutant run `python tests/g8_mutants.py` to Phase 4 step 4 and to Phase 5. CHANGED in v7 (review round 6 readiness M1):
     Expected: `N of N good`, where N is `len(M)` of the MERGED tests/g8_mutants.py, read by import in Phase 0 (g) (G8 v3: 30;
     G8 v4 8.1 G4-2: 32, two mutants added in its 8.2; G8 v4's sections 8-9 and appendix C still print v3's 30 from its last run,
     so the merged file decides); a BAD is a finding (the G4 regex moved a G8 row), reported, not edited away. G8 v4 8.1 G4-2 also
     puts tests/test_redact_glued_rest.py in G4's Phase 4 step 1 run list (12).
- G4a against G8's must-keep rows (G8-review-2 Major 2): Phase 3 runs tests/test_redact_glued_rest.py. A must-keep row that
  changes under G4a (G8 names K60 (base64url) and K66 (base64) as candidates) is a finding: the builder records the old and new
  output; if the new output masks a base64 blob that decodes to text holding a secret, it is intended and the row's expected cell
  is updated; otherwise STOP and report.
- Rebase ownership: the ticket that lands second rebases. Under the default that is G4, so the G4 builder owns:
  - tests/test_redact_idempotent_property.py: G8 changes the oracle (CHANGED in v6: line 141, the `raw_copies` call
    `R._replace_standalone(free, original, "\x00")`, which gains `R._joins(placeholder)`; read at bff88a7a1); G4 adds the `p1c-b64`
    group and the counts. The two edits touch different lines; `EXPECTED_INPUTS` is G4's (G8 does not change it);
  - the redact.py module docstring (CHANGED in v6, placement as G8 v3 4.3 words it): G8 adds a paragraph after the "(A re-scan inside
    redact() ...)" sentence (redact.py 25, the last line of the "What this is not" paragraph), before the closing `"""`; G4's
    bare-number paragraph (6) and base64 sentence go AFTER G8's paragraph, before the closing `"""`;
  - tests/test_redact_g3_port.py: G8 re-points it; G4's "must stay green unchanged" means G8's version.
- If the lead orders G4 first instead (fallback of L23): G4 builds on this base; G8 v3's builder sets `G4C_MERGED = True` from the
  start, re-measures the `after_g4c` column against v5's 5.2/5.3, and owns both rebases. G4 then has no G8 step.
- CHANGED in v7 (review round 6 design N4; G8 v4 L-D3): G8's optional G8c (G8 v4 L-D3 fallback: `(?![^\W\d_]|-)` in place of G4c's
  tail `(?![\w-])`) is NOT taken in either build: G8 v4's default is the stated limit L6, and G8c would edit G4's HOSTNAME entry,
  which 0.2 step 2 makes a STOP. If the lead later wants G8c, it is a new ticket on the tree that holds G4c.
- CHANGED in v7 (G8 v4 read by name): G8 v4 4.1 numbers the new PHONE entries 6-8 (6 `+`-led, 7 contiguous beside `_`, 8 after a
  phone word; entry 5 is CREDITCARD); its oracle edit is still the `raw_copies` line 141 of tests/test_redact_idempotent_property.py;
  its module-docstring paragraph is placed as above (G8 v4 4.3). G8 v4 also edits the `enforce_map` docstring at runmap.py 699 and
  718 (the PHONE `_joins` clauses) and model_gate.py 12-13: different sentences from G4's clause (runmap.py 732), so a textual merge
  only.

### 0.3b Order with G9 (CHANGED in v6, new: review round 5 M3; decision L25; CHANGED in v7: rewritten against G9 v2)
CHANGED in v7 (review round 6 design M1, readiness N3). Source: tickets/G9-spelled-fixed-point-v2.md (DRAFT v2; its sections 1-6
are written, 7-15 are "[filled below]"), read by name, and its drafter's prototype (scratch `g9v2/proto`, imported read-only for the
MEASURED rows below; it is a draft and may still change). v6's "there is NO G9 v2 file" is withdrawn. Where G9 v2 and this
section differ, the second lander follows the merged code and re-measures the rows named here.
- Default: EITHER SIDE. Neither ticket needs the other; the second lander rebases, by name, and owns the checks below.
- What each edits in redact.py (by name; lines 0.1):
  - G9 v2 (its section 3): `_Redactor.__init__` (`_may_register`; `_longest` on the cached path), `_build` (`_longest`, set before
    `self._built_for = ...`), `sweep` (the pass loop), new `_sweep_once` (today's body of `sweep`), `_ensure_built`, `_spend`,
    `_read_back`, `_overlaps`, `_masked`, `_close`, `_place` (`derived`), `_place_union` (takes a kind), `_spelled_sweep`
    (`shared`), `redact` / `redact_many` (`r._may_register = True`), module `_SEP` and `import bisect`; docstrings of
    `_spelled_sweep`, `settle`, `sweep` and the module; defaults.py `SPELLED_MAX_PASSES = 4` after `SPELLED_MAX_WORK` and that
    constant's comment; runmap.py docstrings of `enforce_map` (the overlap bullet is REPLACED) and `held_value_left`.
  - G4: `_LABELS`, `SECRET_KINDS`, `_build`'s RULES LOOP only (1967-1972; 4 point 5), new module-level `place_encoded` (after
    `_replace_standalone`), the HOSTNAME / HOSTKEY entries of PATTERNS, the module docstring (6); defaults.py the eight constants of
    section 7 and two comment sentences; runmap.py the `enforce_map` overlap clause (4 point 5) and the `snapshot` comment (9.3).
  - So in `_build` G4 edits the rules loop and G9 adds the `_longest` line; both keep N15's alias-loop anchor (1955-1957) and the
    sort key line `key=lambda kv: -len(kv[1]),` (the `old` of G4's mutant `b64 tie-break as v3's sort key`). G4 does not edit
    `sweep`, `_place` or `_place_union`. Textual overlaps: the module docstring (second lander after the other's paragraph);
    defaults.py (second lander's block after the other's); tests/redact_mutants.py (G9 appends; G4 edits only R3 and mutant 21's
    sentence; G9's commit raises `EXPECTED_COUNT` of tests/test_redact_mutants_meta.py); and the `enforce_map` overlap bullet
    (runmap.py 730-733): G9 replaces it; G4 edits its clause "(the earlier in the map when equal)". Second lander: when that
    clause survives G9's text, G4's words are added to it as in 4 point 5; when G9's bullet no longer names an order, G4 adds its
    sentence ("Since G4, an original held under a secret kind and an identifier kind follows the secret kind's rule; different
    originals keep the map's order.") after G9's bullet.
- The new refusals, by CLASS (review round 6 design M1). Under G9, either `redact()` of `_pass_one` can raise
  `InputTooLarge("SpelledNotSettled")`. `SpelledOverlap` is a `RedactionError` (G9 v2 1, 4.5 `_close`: `raise
  RedactionError("SpelledOverlap")`), not an `InputTooLarge` as v6 said. It comes only from a redactor that may not register (the
  gate: `enforce_map`, `held_value_left`'s checker; also a bare `_Redactor(m, None).sweep`, which TB-2.8 and test_e5 call), never
  from `redact()` / `redact_many` and so never from `redact_text` or `_pass_one`. The class decides the handler: model_gate maps a
  `RedactionError` to `mask_refused` (`CODE_MASK_REFUSED`) and an `InputTooLarge` to `mask_budget_exceeded` (G9 v2 L-D1b keeps
  that, no new code); `tools.redact_layered` catches only `TooDeep` and `redact_text` re-raises both classes as raised (2.3 step 5).
  `InputTooLarge` is a subclass of `RedactionError` (runmap.py 52, 56), so `except RedactionError` catches both; nothing in G4 adds
  an `except` for either. Listed in 2.6 and 8.
- ENCODED tokens and G9 v2's read-back (D-4: every token that is an EXACT KEY of the redactor's map is read back, whoever wrote
  it). So every `<ENCODED_n>` in T2 (step 9 of 2.5), and every one in a later text (a gate text, an agent message, a tool result
  that quotes it), is read back as its blob, line breaks included, before G9 looks for overlaps. What follows (BY READING G9 v2 4.3
  and 4.4, and MEASURED where marked):
  1. Overlap: a unit's neighbours are never base64 alphabet characters (3.1 point 1's look-behind and look-ahead), so a rule
     original that covers part of the blob and a readable character must hold a non-alphabet character next to blob characters
     (`password=ab!` + blob, the TB-3.33 route, or a model that writes `x<ENCODED_1>y`). Such a union holds an ENCODED token, so its
     kind is a SECRET kind (D-3: the first secret kind met; ENCODED is in `SECRET_KINDS`): swept in every copy, never stored. At the
     gate a free stretch covered only by an identifier refuses that text (`RedactionError("SpelledOverlap")`); a blob never makes
     an identifier rule (ENCODED is a secret kind).
  2. `place_encoded` stays the only writer of an ENCODED entry FOR A BASE64 UNIT. G9 v2's `_close` registers a union through
     `_place_union(..., kind, derived=False)` with the union's kind, which is ENCODED when the first secret kind met in the run is
     an `<ENCODED_n>` token: an ENCODED entry that `place_encoded` did not write (4 point 4).
  3. COST (review round 6 design M1; MEASURED on the G9 v2 prototype, `g9cost.py` / `g9edge.py`, `enforce_map` and `redact`). A
     read-back costs one work unit per character put back, and each finder pass and each slow value adds `len(E)` more (G9 v2 4.3,
     4.4), all inside the one `SPELLED_MAX_WORK` = 4,000,000 count of a `sweep` call. A token touching free text on both sides is
     read back WHOLE when its value is shorter than `2 x (_longest - 1)`, so a long ENCODED value is itself `_longest` and is read
     back whole at every mention. Measured, a text of `step i see <ENCODED_1> now.` lines, map `{"<ENCODED_1>": v}`, v a random
     base64 value wrapped at 32 (an ENCODED original as G4 writes it):
     | value (characters, line breaks included) | largest number of mentions NOT refused | then |
     |---|---|---|
     | 28 | 80 tried, none refused | - |
     | 4,223 | 80 tried, none refused | (about 470 by the same arithmetic, not run) |
     | 16,895 | 118 | `InputTooLarge("SpelledWorkTooMuch")` at 119 |
     | 67,583 (a 65,536-character blob) | 29 | refused at 30, by `enforce_map` and by `redact` alike, in about 0.1-0.2 s |
     | 206,249 | 9 | refused at 10 |
     So about 2,000,000 characters read back (twice that in units: one put, one finder pass) refuse the sweep. v6's "honest text
     cannot reach `SpelledWorkTooMuch` through G4" holds for ONE `redact_text` call of a text G4 reads (its T2 is no longer than
     its input, at most `MAX_REDACT_CHARS`), and is WITHDRAWN for later texts under G9: a gate text or agent message that mentions
     a long `<ENCODED_n>` 10 to 30 times is refused, fail closed (gate: `mask_budget_exceeded`; producer: refused, map not
     written). An ENCODED value longer than 65,536 characters exists: a unit over `B64_MAX_UNIT_CHARS` is masked unread whole (3.4
     point 2), up to `MAX_REDACT_CHARS`. This is not G4's alone (a 64 KiB HIGHENTROPY value costs the same under G9), but G4 makes
     it likelier: a wrapped block that was one short HIGHENTROPY entry per line (or none) becomes ONE long ENCODED entry. Decision
     L26 (14).
- The `_build` first-rule versus G4's tie-break (review round 6 design M1, readiness N3). G9 v2 4.6 says "`_build` keeps the FIRST
  one's rule for its literal sweep (the identifier's, standalone)" for a value under two placeholders. Once G4's tie-break is in,
  `_build` keeps the SECRET kind's rule. MEASURED on the G9 v2 prototype with the tie-break patched into `_build` in-process
  (`g9tie.py`):
  | case | G9 alone | G9 + G4 tie-break |
  |---|---|---|
  | G9 v2's pinned row, `_registering({"<TENANT_1>": A + "ijkl", "<SECRET_1>": A, "<SECRET_2>": B}).sweep("z" + A + "ijkl y")` (`A`, `B` as in G9's tests) | `z<SECRET_3> y` | `z<SECRET_3> y` (the pin holds both ways) |
  | then, the same redactor, `sweep("q" + A + "ijkl" + "r " + A + "ijkl")` | `q<SECRET_3>r <TENANT_1>` (the standalone copy under the identifier, restorable) | `q<SECRET_3>r <SECRET_3>` |
  | test_e5's `_one_sweep(f"a{V}b", {"<TENANT_1>": V, "<SECRET_1>": V})` | `aZq9xLm4wb` | `a<SECRET_1>b` |
  | TB-2.8 map 1 `{"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd"}`, `enforce_map("x ab-cd-ef y", m)` and the bare sweep | `x <SECRET_1><TENANT_1> y` both | the same |
  | TB-2.8 map 2 `{"<SECRET_1>": "ab-cd", "<TENANT_1>": "cd-ef"}` | `RedactionError("SpelledOverlap")` both | the same |
  | TB-2.8 map 3 `{"<TENANT_1>": "ab-cd", "<SECRET_1>": "cd-ef"}` | `x <TENANT_1><SECRET_1> y` both | the same |
  | TB-2.8 map 4 `{"<SECRET_1>": "cd-ef", "<TENANT_1>": "ab-cd"}` | `RedactionError("SpelledOverlap")` both | the same |
  | fifth map (4 point 5) | `enforce_map`: `x <SECRET_1><SECRET_2> y`; bare sweep: `x <SECRET_1><TENANT_1> y` | `x <SECRET_1><SECRET_2> y` both |
  | R8 killer map (9.3, TB-2.11) | `enforce_map`: `RedactionError("SpelledOverlap")`; bare sweep `x <SECRET_1><TENANT_1> y` | the same; with R8 applied `enforce_map` gives `x <SECRET_1><TENANT_1> y` (R8 still killed) |
  Consequences: G9 v2 4.6's sentence is G9's to correct once G4 is in (the tie-break improves G9: a later standalone copy of a
  union value is no longer written under the identifier); G9's pinned `z<SECRET_3> y` does not flip. On G4's side, TB-2.8's four
  map rows, its fifth map, TB-2.11 and test_e5's three asserts are ORDER-DEPENDENT: the values of 4 point 5 and 10.2 hold on a tree
  without G9 (MEASURED at 944d143db, `r8.py`); on a tree with G9 they are the G9 + G4 column above. The second lander writes the
  column of the tree it lands on and records the other in the evidence. A `RedactionError("SpelledOverlap")` row is asserted with
  `pytest.raises(RedactionError, match="SpelledOverlap")`.
- Second lander's checks (G4 second: in G4's Phase 2 and Phase 3; G9 second: in G9's phases, with G4's files):
  1. the 0.2 rule, with G9's names above as table updates (not STOPs), except a change to the `_build` rules loop (STOP);
  2. Phase 2 step 2 and Phase 3 step 2 run tests/test_redact_settle_loop.py (G9's tests live there), tests/test_b64_scan.py,
     tests/test_runmap_enforce_map.py and tests/test_redact_mutants_meta.py; expected red: none once the order-dependent rows above
     are re-pinned; any other red G9 test or TB test is a finding, reported;
  3. `python tests/redact_mutants.py` with G9's rows: each verdict as recorded by G9 (G9 second) or at Phase 0 (g) (G4 second);
     `python tests/gate_mutants.py`: R8 killed (by TB-2.11, either column);
  4. G4's Phase 0 (g) snippet run counts G9's appended mutants with the others (CHANGED in v7: the 144 of 13.3 grows by G9's
     count on runmap.py/redact.py).

## 1. Problem in plain words
A secret that is only written in base64 reaches the model today, because the redactor has no decoded view:
- Short base64 blobs (under 40 characters) pass unchanged, whether alone, in a sentence, in JSON or after `data=`.
- Wrapped base64 passes when the lines are short, or leaves its last line readable.
- Long unbroken blobs are already masked whole by HIGHENTROPY.
- On an approval card, a short blob of a URL credential or of `curl -u user:<pw>` is shown as written (MEASURED at the base,
  `channel.clean`, section 3.4).

Private host names are masked only in part:
- A private host name is masked only up to its private suffix: `db01.corp.example` becomes `<HOSTNAME_1>.example`.
- A bare host label after `host`, a label with an underscore and `[.]` dots are not masked at all.

Bare numbers without a label are not masked. That is an accepted decision (order 64 item 4); G4 writes it down and pins it.

### What the probe proves (handover/core-c/evidence/p1c_probe.py, seed 20261120), RE-MEASURED at e8ff6de2b
Re-run unchanged, in-process, on the HEAD tree (2.4 s wall). Totals and every row list are the same as v4's (cd8d375) and v3's:
| gap | rows | leaked at the base | G4 result |
|---|---|---|---|
| 1 base64 (1b 128 + 1c 14) | 142 | 52 (1b 48, 1c 4); 88 of the rest held by HIGHENTROPY | 52 closed; 85 unchanged; 5 change kind from HIGHENTROPY to ENCODED (no leak before or after). MEASURED on the prototype: 0 leaked, 83 held by HIGHENTROPY, the 85 other rows print the same cells as at the base |
| 2 host names | 44 | 26: 12 whole, 14 part | 19 closed; 3 stay (limits: rows 10, 15, 16); 4 kept on purpose (6, 8, 9, 42); 18 already masked stay |
| 3 bare numbers | 43 | 24 not masked, 2 in part, 17 whole | not a gap: written down and pinned by class |
| 4 hostile corpus | - | - | CUT: the old 30-row corpus is not in this repository |

The gap 2 result was MEASURED by v4 (cd8d375) with the G4c patterns of section 5 put into `redact.PATTERNS` in-process: exactly
rows 6, 8, 9, 10, 15, 16 and 42 stay readable. redact.py changed since in the spelled-form and own-output code only (no PATTERNS
entry), so it is carried, NOT RE-MEASURED at e8ff6de2b (Phase 0 (b) re-measures it). Rows 31 (`dial bücher.internal now`) and 41
(full-width dots) are already masked by the fold scan, so G4 closes 19 host rows.

## 2. Decision D1 and the central refactor
### 2.1 Where the step plugs in, and why not "decode before pass 1"
The base64 step runs on the cleaned, neutralised input AFTER pass 1, because pass 1 tells it which runs are already masked (HELD,
3.3).

Option not taken (round 1's proposal): decode before pass 1 and replace every unit that decodes. It would change the kind of every
blob HIGHENTROPY, BASIC or JWT holds today, cut a JWT with an e-mail in its payload into ENCODED segments, and give up invariant I3.

The chosen design pays one more pass 1, and only on a text with a hit.

### 2.2 The new private names (all in guard/runmap.py)
tests/test_k1b_redaction_layers.py (about line 136) pins that every `redact(` / `redact_many(` call in src is in guard/runmap.py, so no
helper moves out.
```python
@dataclass
class _ScanBudget:
    """The base64 step's budget for ONE redact_text call; the text, every view and every depth share it."""
    started: float           # redact_text's `started`; the deadline is started + defaults.REDACT_BUDGET_S
    units: int = 0           # units decoded or masked unread so far (decodable, not held), all views and depths
    decoded_chars: int = 0   # characters of decoded text read so far (len of each _b64_text result)

    def clock(self) -> None: ...             # ONE time.thread_time() read; past the deadline: InputTooLarge("InputTooLarge")
    def take(self, chars: int) -> None: ...  # units += 1, decoded_chars += chars; over B64_MAX_UNITS or
                                             # B64_MAX_DECODED_CHARS: InputTooLarge("InputTooLarge")

class _B64Unit(NamedTuple):
    start: int               # offset in the ANSI-stripped text (3.1 point 5)
    end: int
    written: str             # the unit as written, line breaks included: the ENCODED original
    joined: str              # its lines, stripped, joined with nothing between: what _b64_text decodes
    lines: tuple[str, ...]   # its lines as written (stripped), for the held rule
    parts: tuple["_B64Unit", ...] = ()   # CHANGED in v7 (M3): a LOOSE block's lines as RUN units (3.1 point 3); () otherwise

def _scan(text, mapping, cache, neutralise, budget, depth) -> tuple[str, dict[str, str]]
def _pass_one(text, mapping, cache, budget, depth) -> RedactionResult
def _b64_units(text: str) -> tuple[str, list[_B64Unit]]     # (the ANSI-stripped text, its units); (text, []) with no run
def _b64_held(unit: _B64Unit, secret: frozenset[str], parts: tuple[str, ...]) -> bool   # 3.3; the sets built once per _pass_one
def _b64_text(joined: str) -> str | None                      # 3.2
def _b64_hits(units, known, budget, depth) -> tuple[list[bool], dict[str, str]]   # 3.4; (hits, kept entries)
def _b64_place(stripped: str, units: list[_B64Unit], placeholders: dict[str, str]) -> str
```
Changed from v4 (review B2): `_pass_one` and `_b64_hits` take NO `neutralise`: a decoded text is always scanned with
`runmap.neutralise_untrusted` (3.4 point 7, L19), whatever the caller's hook is. `_scan` keeps `neutralise` for the text and its views.
- `_scan` is the whole of today's `redact_text` body except the cap, the exception wrapper and the map write. It returns the output
  and the new map and never writes `mapping`.
- `_pass_one` calls the module-level name `redact` (as `redact_text` does today), never a local alias. The patchers of 0.1
  (tests/test_k5_round5.py:278, tests/test_k5_tools.py:317 and 339, tests/test_redact_fold_budget.py:89 and 252,
  tests/fixtures/p1d_cases.py:261) replace `runmap.redact` and must still see every call. (v4 named tests/test_k5_round11.py here: it
  does not patch `runmap.redact`; it counts calls of the neutralise hook, `assert len(seen) >= 2` at line 74.)
- The private signatures are part of the contract. I13 drives a spent deadline and the caps through `_ScanBudget` and `_b64_hits`
  directly, because the public API cannot set a deadline that is already spent at the step.

### 2.3 `redact_text`'s new body (runmap.py; the docstring gains the paragraph of section 11)
1. `_within_cap(text)`: unchanged, before the clock.
2. `started = time.thread_time()`: unchanged line; mutant R1 pins it.
3. `try:` then `cache = getattr(mapping, "redact_cache", None)`. It stays inside the try (tests/test_runmap_map_write.py, `test_m8_*`
   about line 37).
4. `budget = _ScanBudget(started)`, then `out, current = _scan(text, mapping, cache, neutralise, budget, 0)`.
5. The two handlers exactly as at the base (runmap.py 593-596), text and comment unchanged:
   ```python
       except (InputTooLarge, TooDeep, RedactionError):
           raise  # as raised: the text of `NotSettled` (the settle loop's cap) is kept for the caller's log
       except Exception as exc:  # noqa: BLE001 - whatever the redactor raised, nothing is sent
           raise RedactionError(type(exc).__name__) from None
   ```
   So a `RedactionError("NotSettled")` and an `InputTooLarge("SpelledWorkTooMuch")` from either `redact()` call of `_pass_one`
   reach the caller as raised. tests/test_redact_settle_loop.py `test_a_chain_that_still_changes_in_round_four_*` asserts
   `str(err.value) == "NotSettled"` through `runmap.redact_text`, and stays green.
6. The comment block and `mapping.update(current)` / `return out` at four spaces, unchanged. Gate mutants R3, R3b and R3c pin
   `    mapping.update(current)\n    return out\n` exactly once in runmap.py. A raise anywhere in steps 3-4 leaves `mapping`
   unwritten. G4 writes no `raise RedactionError("NotSettled")` in runmap.py: the one in `enforce_map` is pinned by gate mutant R5
   (tests/gate_mutants.py line 175, old text `    raise RedactionError("NotSettled")`), and a second copy would make R5 replace both.

### 2.4 `_scan`, numbered (today's lines 557-592 moved; two `redact(` calls replaced by `_pass_one`)
1. `started = budget.started`: a local of that name, so the existing check lines keep their text.
2. `text = fits_after_nfkc(_clean(text))`; if `neutralise`: `text = fits_after_nfkc(neutralise(text))`. Call this text T.
3. `scan = not T.isascii() or any(c in T for c in "\\%&")`; `views = _views(T) if scan else []`.
   - The views are of T, computed BEFORE pass 1 as today, and NEVER of the replaced text T2.
   - Reason: a view of T2 would hold our own `<ENCODED_n>`, and `neutralise_untrusted` would escape it to the look-alike
     `‹ENCODED_n›` before redaction (and since E9 that look-alike after a key is masked as SECRET).
4. `result = _pass_one(T, mapping, cache, budget, depth)`; `out, current = result.text, result.mapping`.
5. `if views and time.thread_time() - started > defaults.REDACT_BUDGET_S: raise InputTooLarge("InputTooLarge")`. This line is
   unchanged (mutant R2).
6. `pairs = _decoded_masks(current, T, started + defaults.REDACT_BUDGET_S) if views else []`.
   - An ENCODED original is plain ASCII base64 with no `%`, `\` or `&`, so `_decoded_masks` skips it before any decode.
   - `_decoded_masks` reads the clock once per stored original (runmap.py 502). At depth 1 or more, `current` holds the incoming
     map, so a decoded view whose join has views pays up to `len(map)` clock reads (at most `MAX_MAP_ENTRIES`). Harmless, stated.
7. The neutralised pairs, unchanged.
8. `for view in views:` (one occurrence; p1d_a mutant A16 pins it). Inside the loop:
   1. the clock check (R3's condition, as `ruff format` writes it, 13.3);
   2. `neutralise(view)` when a hook is given;
   3. `view = _keep_earlier_masks(view, pairs)`;
   4. `again = _pass_one(view, current, cache, budget, depth)`;
   5. the view rule, unchanged: `if again.mapping != current or _held(again.text) > _held(out): out, current = again.text, again.mapping`.

   In a view, a blob that was a hit on T is swept by pass 1, because ENCODED is a secret kind (every copy from 4 characters), and its
   unit is HELD there (3.3, padding ignored) and not decoded again. A blob readable only in a view (`\/` slashes) is decoded in that
   view. MEASURED (TB-3.13): `%3D` padding gives one ENCODED entry and keeps `%3D` in the output.
9. `return _clean(out), current`.

### 2.5 `_pass_one`, numbered
1. `started = budget.started`.
2. `first = redact(text, mapping=mapping, _cache=cache, _deadline=started + defaults.REDACT_BUDGET_S)`. This is pass 1 with G7's
   settle. Mutant 21's literal `_deadline=started + defaults.REDACT_BUDGET_S` stays in both redact calls of this function, which are
   the only two in runmap.py (two today as well).
3. `stripped, units = _b64_units(text)`. With no run (the gate, 3.1 point 1), return `first` here: no clock read and no other call.
4. Build ONCE `secret = frozenset(original of every placeholder of first.mapping whose kind is in SECRET_KINDS, with trailing "="
   stripped)` and `parts = tuple(originals of the JWT and PRIVKEY placeholders)`; drop held units (`_b64_held(u, secret, parts)`,
   3.3). (The prototype built the set per unit; a builder must not: with 2,000 map entries and 2,600 units that is 5 million steps.)
   For the decision, keep one unit per distinct `written`; every copy is still replaced in step 8. None left: return `first`.
   CHANGED in v7 (review round 6 design M3): the candidates are the units AND the `parts` of every loose block (3.1 point 3), each
   through the same held filter and dedupe; a part costs a unit of the budget like any other.
5. `hits, kept = _b64_hits(distinct_units, first.mapping, budget, depth)`. No hit: return `first`, whose output and map are
   byte-identical to the base commit's for that text.
6. `base = dict(mapping)` (the INCOMING map; pass 1's additions are dropped: they hold junk such as one HIGHENTROPY entry per wrapped
   line of a blob that is now one ENCODED). Then the kept entries are RENUMBERED into `base` (decision L20, review round 4 readiness
   Major 5): for each kept entry in the order of `kept`, its kind `k` gets `<k_{n+1}>` where `n` starts at
   `_Redactor(dict(base)).counters[k]` and grows by one per entry of that kind. A kept placeholder never appears in any text (the
   decoded view's output is thrown away), so renaming it is safe; the numbers in `base` then have no gaps.
7. CHANGED in v7 (M3): `chosen` is built by walking the units of step 3 in order: a unit that is not a loose block, or a loose
   block whose `written` is a hit, is chosen when it is a hit; a loose block that is NOT a hit gives instead its `parts` that are
   hits. So a loose block is replaced whole when its join decodes to a hit, else line by line (as v6 did for those lines); chosen
   units never overlap. `placeholders = dict(zip(runs, place_encoded(base, runs)))`, with `runs` the distinct `written` of the
   chosen units, in order. (A part's kept entries stay kept even when its block wins: an over-mask of a plain copy at most.)
8. `T2 = _b64_place(stripped, copies, placeholders)`, where `copies` are all units of `stripped` (step 3, after the held filter, before
   the dedupe) whose `written` is a key of `placeholders`. Every copy is replaced by position; units do not overlap. CHANGED in v7
   (M3): `copies` are the chosen units of step 7 and their copies (the same `written`, chosen by the same rule), never a part of a
   block that is itself replaced.
9. `return redact(T2, mapping=base, _cache=cache, _deadline=started + defaults.REDACT_BUDGET_S)`. Pass 1 leaves a placeholder
   alone, so the result holds `<ENCODED_n>` where the blob stood. Nothing is mapped back by position.

Numbering (stated; review round 4 readiness Major 5). A value pass 1 numbered is numbered again by step 9 after the kept entries and
the ENCODED entries, so the same text can carry other numbers than without the blob. MEASURED on the prototype (TB-3.19): the chain
`CONSTRUCTED[0]` alone gives `password=<SECRET_1>...`; with a hit blob after it, the decoded secret is kept as `<SECRET_1>` and the
chain's password becomes `<SECRET_2>`. The map has no gap (keys BANKACCT_1, BANKCODE_1, ENCODED_1, SECRET_1, SECRET_2). Without
step 6's renumbering (the L20 fallback) the kept entry is `<SECRET_2>` (numbered against pass 1's map) and the chain `<SECRET_3>`,
so SECRET_1 is a gap. Map numbering gaps are ACCEPTED in general (no consumer reads the numbers as a count; k1b counts entries), but
the default produces none.

Settle and fold interplay:
- Step 9 is a full `redact()`, with its own `_SETTLE_ROUNDS` cap (4) and its own fold scan. It reruns every settle chain of T2; a
  chain in T is still in T2, because only base64 units changed. MEASURED on the prototype (TB-3.19): `CONSTRUCTED[0]` + sep + `SB`
  settles for `" "`, `","`, `"\n"`, no `NotSettled`.
- A `RedactionError("NotSettled")` or an `InputTooLarge` (any text, `SpelledWorkTooMuch` included) raised in step 2 or step 9
  propagates. `redact_text` then refuses the text and does not write the map (I21, TB-3.33).
- Cost: a text with a hit pays two `redact()` calls per scanned spelling (section 8).

### 2.6 Failure behaviour by depth (decision L4)
| raised where | depth 0 (the input, its views) | depth 1 or more (inside a decoded view) |
|---|---|---|
| `TooDeep` from `_views` / `undo` | propagates: refused, as today | caught in `_b64_hits`: every unit of that decoded view is a hit unread (L4) |
| the decoded join over `MAX_REDACT_CHARS` after NFKD (`_expanded_len`) | - | checked before the recursive call: every unit of that view is a hit unread |
| `InputTooLarge("InputTooLarge")` from the clock, `_ScanBudget.take`, `_decoded_masks`, `fits_after_nfkc` of a view, or the redactor's own cap check of a decoded view | propagates: refused | propagates: refused (`_b64_hits` catches only `TooDeep`) |
| `InputTooLarge("SpelledWorkTooMuch")` from the spelled-form scan of either `redact()` of `_pass_one` (new route through G4: a compound SECRET value that holds a blob's `<ENCODED_n>` registers a form under that token in step 9; many copies of the token then cost one unit each, or more; MEASURED, TB-3.33) | propagates: refused, map not written; a card raises (no `SETTLE_NOTE`, as 8) | propagates: refused |
| `RedactionError("NotSettled")` | propagates (as raised, 2.3 step 5) | propagates |
| CHANGED in v6: `InputTooLarge("SpelledMemoryTooMuch")` (G7 r7, in the tree at bff88a7a1: the spelled-form registry past `SPELLED_MAX_CHARS` in either `redact()` of `_pass_one`; BY READING) | propagates: refused, map not written; a card raises (as 8) | propagates: refused |
| CHANGED in v6 (review round 5 M3; only when G9 is merged, 0.3b): `InputTooLarge("SpelledNotSettled")` from either `redact()` of `_pass_one` (a sweep not settled in `SPELLED_MAX_PASSES` passes) | propagates: refused, map not written; a card raises (as 8) | propagates: refused |
| CHANGED in v7 (review round 6 design M1; only when G9 is merged): `RedactionError("SpelledOverlap")` (a RedactionError, not an InputTooLarge: G9 v2 4.5) | never from `redact_text` (`redact()` may register); from `enforce_map` / `held_value_left`'s checker / a bare `_Redactor.sweep` only (the gate: model_gate `mask_refused`; TB-2.8, TB-2.11, TB-3.27 call `enforce_map`, 0.3b) | - |
| CHANGED in v7 (only when G9 is merged; 0.3b point 3): `InputTooLarge("SpelledWorkTooMuch")` from G9's read-back of a long `<ENCODED_n>` mentioned many times in a LATER text (a gate text, an agent message) | refused, map not written (producer); the gate: `mask_budget_exceeded` | propagates: refused |

A decoded view that only grows past the cap through its escapes (a `ﷺ` run) is refused. This is stated, not handled.
CHANGED in v7 (review round 6 design M1): the next sentence holds for ONE `redact_text` call on the tree without G9; with G9 a
later text that mentions a long `<ENCODED_n>` 10 to 30 times is refused (MEASURED on the G9 v2 prototype, 0.3b point 3; L26).
Honest text cannot reach `SpelledWorkTooMuch` through G4: a unit becomes one `<ENCODED_n>` token, and 262,144 characters hold at
most about 22,000 tokens of 12 or more characters, far under 4,000,000 units. MEASURED on the prototype: `password=ab!<SB>` then
3,000 copies of `SB` separated by spaces scans in 0.45 s with the real limit; with `SPELLED_MAX_WORK` patched to 1,000 it is refused
`SpelledWorkTooMuch` in 0.36 s and the caller's map is unchanged. (A route needs a compound value whose blob is NOT a piece of a
secret pass 1 found on T: `password=<SB>.tail` is held, because pass 1 registers the `.`-split piece `SB` as a secret; `ab!<SB>`
is not split by `_PIECE`, so it reaches step 9.)

## 3. G4a: the base64 rules
### 3.1 Units (`_b64_units`)
The alphabet is `[A-Za-z0-9+/_\-]`. One `=`, two `=` or none may end a run.
1. GATE: `_B64_RUN = re.compile(rf"(?<![A-Za-z0-9+/_\-])[A-Za-z0-9+/_\-]{{{defaults.B64_MIN_CHARS},}}={{0,2}}(?![A-Za-z0-9+/_\-=])")`.
   - It is compiled once at import; a test that needs another minimum patches `runmap._B64_RUN`.
   - The gate is ONE `search` on the run text of point 2. No match means no unit, and nothing else runs.
   - A `=` before a run is allowed (`data=<b64>`), because the look-behind excludes the alphabet only.
2. PLACEHOLDERS AND MARKERS ARE NEVER RUNS.
   - When the text holds `<` or U+2039 (otherwise there is no work), every match of
     `_B64_TOKEN_SKIP = re.compile(r"[<‹](?:[A-Za-z][A-Za-z0-9]*_\d+|[A-Z][A-Z0-9_]*)[>›]")` is blanked to the same number of spaces
     before the search, so offsets stay.
   - It blanks genuine placeholders, escaped look-alikes (`‹HIGHENTROPY_7›`), lower-case look-alikes (`<ipv4_2>`) and
     `<SECRET_REDACTED>` (tools.py 766, k1b/redaction.py 86).
   - Stated limit L-B6 (widened, review round 4 codebase nit): a real blob written between `<` (or `‹`) and `>` (or `›`) is taken
     for a marker and is not decoded when it is EITHER made only of `A-Z`, `0-9` and `_` (second alternative) OR is letters and
     digits of any case, one `_`, then only digits (first alternative: `<cGFzc3dvcmQ_12>`). No real secret blob of the first shape
     was found: a scratch search of 3,000,000 url-safe encodings of `pwd=` + 8 random characters found none; the limit is pinned by
     a unit test of the blanking itself (TB-3.3b), not by a strict xfail (UNMEASURED as a leak).
   - CHANGED in v7 (review round 6 design N5): that search covers natural text only. A writer who CHOOSES the text can always
     shape a blob that passes (a marker shape, a glued prefix, L-B1, a split, L-B4): the base64 view finds what honest tools and
     people write; it is not an adversary-proof gate, and SECURITY says so (15).
3. WRAPPED BLOCK. Two or more consecutive lines, split on `\n`; a trailing `\r`, and spaces or tabs at both ends of a line, are
   ignored. A block must meet every rule:
   - every line holds only alphabet characters (the last may end in `=` or `==`);
   - the first line is at least `defaults.B64_WRAP_MIN_CHARS` (16) long (CHANGED in v7, review round 6 design M3: any length;
     v6 also asked for a multiple of 4);
   - every line but the last has the first line's length and no `=`;
   - the last line is 1 to first-length characters, and may end in `=` or `==`.

   CHANGED in v7 (review round 6 design M3). Why: `base64 -w 50/70/90` and other tools wrap at widths that are not a multiple of 4;
   under v6 every such line was its own RUN unit, and a line that starts at an offset not a multiple of 4 decodes to bytes that are
   not text. MEASURED with a stdlib copy of 3.2's rules (`wrap.py`; the blob is `b64("2026-11-20 deploy db_password=" + S12 +
   " applied to the cluster after the review of the change set")`): per line, widths 16, 32, 60, 64 and 76 decode on every line;
   widths 50, 70 and 90 leave line 2 undecodable (so part of the value stayed unread under v6); the joined block decodes and holds
   S12 at every width. A block whose first-line length is NOT a multiple of 4 is LOOSE: its unit carries `parts`, the RUN units
   its lines would be on their own (v6's units). The join is tried first; when it is not a hit, the parts are tried (2.5 steps 4
   and 7). The fallback is needed: two different complete unpadded blobs of the same length on consecutive lines (27 characters
   each, `b64("pwd=" + S12 + "abcd")` and `b64("pwd=" + S12[::-1] + "wxyz")` without `=`) form a loose block whose join does
   NOT decode, while each line does (MEASURED, `wrap.py`). Blocks whose width is a multiple of 4 have no parts: every v6 result
   for them stands. Cost: a loose block costs its join plus at most one decode per line.

   It is one top-to-bottom pass, and each line is in at most one block. A block is maximal: it ends at the first line that breaks a
   rule, and that line is included if it is a valid shorter last line (a full-length line continues the block). It is linear. The
   cases, with the strings TB-3.2 uses (MEASURED on the prototype; `(start, end)` in the joined text):
| # | lines | units |
|---|---|---|
| 1 | `A16` / `B10` | (0, 27) one block |
| 2 | `A16` / `B16` / `C16` | (0, 50) one block (a last line of full length is valid) |
| 3 | `A16` / `B10` / `C16` | (0, 27) block lines 1-2; (28, 44) line 3 a RUN unit |
| 4 | `A16` / `B20` | no block (line 2 longer): (0, 16), (17, 37) two RUN units |
| 5 | `A15` / `B15` | no block (CHANGED in v7: because 15 is under `B64_WRAP_MIN_CHARS`): (0, 15), (16, 31) |
| 6 | `A16` / `B15 + "="` / `C16` | (0, 33) block lines 1-2; (34, 50) line 3 |
| 7 | `A16` / `B8` / `C20` / `D4` | (0, 25) block lines 1-2; (26, 51) block lines 3-4 |
| 8 | `"  " + A16 + "\r"` / `B4` | (2, 24) one block; `written` keeps the `\r` between the lines |
| 9 (CHANGED in v7, new) | `A18` / `B18` | (0, 37) one LOOSE block; parts (0, 18), (19, 37) |
| 10 (CHANGED in v7, new) | `A18` / `B10` | (0, 29) one LOOSE block; parts (0, 18), (19, 29) |

   The strings (TB-3.2, review nit "the table is symbolic"): `A16 = "QUJDREVGR0hJSktM"`, `A15 = "QUJDREVGR0hJSkt"`,
   `B4 = "TU5P"`, `B8 = "TU5PUFFS"`, `B10 = "TU5PUFFSU1"`, `B15 = "TU5PUFFSU1RVVld"`, `B16 = "TU5PUFFSU1RVVldY"`,
   `B20 = "TU5PUFFSU1RVVldYWVph"`, `C16 = "WVphYmNkZWZnaGlq"`, `C20 = "WVphYmNkZWZnaGlqa2xt"`, `D4 = "bm9w"`; each row is
   `"\n".join(row)`. Expected `written` is `text[start:end]`. CHANGED in v7: `A18 = A16 + "TU"` (`"QUJDREVGR0hJSktMTU"`),
   `B18 = "5PUFFSU1RVVldYWVph"`; rows 1-8 have no parts (widths 16), rows 9 and 10 are BY READING (derived from the rule; the v5
   prototype that measured rows 1-8 is not rebuilt).
   Note (MEASURED): identical consecutive lines of one blob (a log that prints the same 28-character blob on 3 lines) form ONE
   block whose join is the three blobs glued; it decodes and is one `<ENCODED_n>`.
4. A unit is a block, or a RUN that does not start inside a block. `written` is the stretch of the stripped text from the unit's first
   character to its last.
5. ANSI: units are found on `strip_ansi(text)`, and T2 is built from that stripped text.
6. Offset 0 only. A run glued to other alphabet characters is one longer run that does not decode: stated limit L-B1, pinned by a
   strict xfail (MEASURED leak, 10.3).
7. Duplicates: units with the same `written` are decoded once and count once against the budget.
8. The card text `Plan <12 hex>.` (requests.py 42) holds a 12-character run on every card: it is a unit (MEASURED) that decodes to
   bytes that are not text, so it is never a hit; it costs one `_b64_text` call per card. TB-3.4's "no run" texts do not include it.

### 3.2 Decode (`_b64_text(joined) -> str | None`)
1. Strip the trailing `=`; the rest is the body.
2. A body with `+` or `/` AND `-` or `_` is mixed: None. A body with `-` or `_` is URL-safe: map `-` to `+` and `_` to `/`.
3. `len(body) % 4 == 1`: None. Otherwise pad with `=` to a multiple of 4 (written padding is ignored), then
   `base64.b64decode(padded, validate=True)`. Non-canonical trailing bits are accepted; any `binascii.Error` / `ValueError` gives None.
4. Bytes to text, by the first rule that applies, each decode strict:
   - a. BOM `FF FE`: UTF-16-LE of the rest; `FE FF`: UTF-16-BE; `EF BB BF`: UTF-8 of the rest.
   - b. Else UTF-8.
   - c. If b fails, or fails rule 5: when the length is even and at least 4, and at least `B64_UTF16_ZERO_SHARE` of the odd-index bytes
     are 0, UTF-16-LE; else that share of the even-index bytes, UTF-16-BE.
5. The printable share of the decoded `str` (`c.isprintable() or c in "\t\n\r"`) must be at least `B64_PRINTABLE_SHARE`, and the
   string must not be empty.
6. Hex, base32, base85, gzip and quoted-printable are not decoded (L-B2).

### 3.3 HELD (`_b64_held`)
`secret` (built once per `_pass_one`, 2.5 step 4) is the set of originals of placeholders in `first.mapping` whose kind is in
`SECRET_KINDS` (ENCODED included), each with its trailing `=` stripped. A unit is HELD when `written.rstrip("=") in secret`
(CHANGED in v5, decision L21: padding is ignored, review round 4 readiness Major 6), or when every line of the unit is in `secret`
or is a substring of the original of a JWT or PRIVKEY placeholder.

Why padding is ignored: in a view, `%3D` becomes `=`, so the unit there is the body plus `=`; the stored ENCODED original is the body
as written in T (the `%` ended the run). With an exact compare the unit is decoded again and becomes a second ENCODED entry, and the
view's output `data=<ENCODED_2>` replaces the text (MEASURED: `data=<ENCODED_2>`, map ENCODED_1 and ENCODED_2). With padding
ignored the view finds nothing new and the output stays `data=<ENCODED_1>%3D` with one ENCODED entry (MEASURED, TB-3.13).

Only SECRET kinds hold (L12). Effect: the 80 HIGHENTROPY rows of 1b, the 3 `data:` rows and the 2 BASIC rows of 1c, JWTs and PEM
blocks are not decoded. 1c rows 2, 3, 6, 7, 10 and 11 become one ENCODED. A blob that is a `_PIECE` of a SECRET value pass 1 found
(split at `.`, `:`, `=`, `;` and the like) is held too, because pass 1 registers that piece as a secret (MEASURED: `password=<SB>.tail`).

CHANGED in v7 (review round 6 design N2, CONTESTED in part). The reviewer asks to apply the substring rule (a line that is a
substring of a JWT or PRIVKEY original) to blocks only. Not taken: units are found on the INPUT T (2.5 step 3), where a JWT is
written whole, and its three `.`-separated segments are single-line RUN units; with the rule limited to blocks, the JWT's own
payload segment would be decoded in place, and a payload holding an e-mail or a secret would cut the JWT into an ENCODED piece
(MUST_KEEP_B64 rows 06 and 07 and the probe's JWT rows would change: the reason the held rule exists, round 1 g4c-B2). What the
reviewer found stays as a stated limit, L-B7: a COPY of one segment of a JWT (or one line of a PEM block) written elsewhere, apart
from its token, is held and not decoded, so a value only inside that copy is not found. Pre-existing (the base decodes nothing);
pinned by the strict xfail `test_limit_jwt_segment_copy` (10.3), BY READING: the builder runs its recipe in Phase 3 before marking
it; when it does not fail, the builder records the output and makes it a plain assert of the measured string instead.

### 3.4 The decoded view and the hit rule (`_b64_hits`), numbered (CHANGED in v5: the decoded view is always neutralised with `neutralise_untrusted`)
1. For each unit, in order: `budget.clock()`.
2. `len(u.joined) > defaults.B64_MAX_UNIT_CHARS`: no decode; `budget.take(0)`; a hit unread.
3. `d = _b64_text(u.joined)`. None: not a hit, not counted.
4. `depth == defaults.B64_MAX_DEPTH`: `budget.take(0)`; a hit unread (L4).
5. Otherwise `budget.take(len(d))`. The unit's piece is `_clean(d)`. A piece that holds `_B64_SEP` is a hit unread (fail closed:
   a decoded text cannot fake the boundaries).
6. No piece: return. `joined = _B64_SEP.join(pieces)` with **`_B64_SEP = "\n\n;\n\n"`**. If `_expanded_len(joined) >
   defaults.MAX_REDACT_CHARS`, every piece's unit is a hit unread; return.
7. `seen` is the pieces as `_scan` will read them: `fits_after_nfkc(neutralise_untrusted(fits_after_nfkc(_clean(joined))))`, split on
   `_B64_SEP`. If `len(seen) != len(pieces)`, every piece's unit is a hit unread; return.
8. `out, scanned_map = _scan(joined, dict(known), None, neutralise_untrusted, budget, depth + 1)`. `known` is `first.mapping`,
   `_cache` is None, the budget is the same, and the hook is ALWAYS `runmap.neutralise_untrusted` (decision L19). On `TooDeep`, every
   piece's unit is a hit unread (2.6).
9. `after = out.split(_B64_SEP)`.
   - If `len(after) != len(pieces)`, every piece's unit is a hit (fail closed).
   - Else piece i is a hit when `_held(after[i]) > _held(seen[i])`.
10. Kept entries (decision L8): `{k: v for k, v in scanned_map.items() if k not in known and kind_of(k) not in runmap.STORED_KINDS and kind_of(k) != "ENCODED"}`.
    These are the decoded view's new values of kinds that are never stored (no secret kind is in `defaults.STORED_KINDS`, and
    config.py 280 rejects a stored kind outside it). Inner ENCODED entries of nested blobs are dropped, so ENCODED numbers do not
    skip. Every other entry of `scanned_map` is thrown away. `_pass_one` renumbers the kept entries (2.5 step 6).
    CHANGED in v6 (review round 5): "never stored" is not only the secret kinds. The kinds of `_LABELS` that are neither in
    `SECRET_KINDS` nor in `defaults.STORED_KINDS` are UUID, BANKCODE, BANKACCT, SSN, AADHAAR and PAN (read at bff88a7a1: the set
    difference of the three; defaults.py 198 says why UUID is not stored). Their decoded finds are KEPT too (L8).

Why the decoded view is not neutralised with the caller's hook (review round 4 codebase B2, MEASURED). On the card path the hook is
`channel._neutralise` = `withhold_commands(sanitise_text(t, defang=False))`; `sanitise_text`'s line cleaning replaces a URL with
`[link removed]` and removes HTML, images, markdown links and mentions BEFORE the scan. The decoded text is never shown, so it needs
only placeholder look-alike and marker safety (`neutralise_untrusted`), not card sanitising. Measured through `channel.clean` with the
fake password `"Kp7" + "rTq" + "2W"`:
| decoded text (short blob, under 40 characters) | base (e8ff6de2b) | prototype, caller's hook (v4) | prototype, `neutralise_untrusted` (v5) |
|---|---|---|---|
| `http://u:<pw>@h.io` (32 characters of base64) | shown | SHOWN (the hook turns the decoded text into `[link removed]`; no pattern fires) | `<ENCODED_1>` |
| `ftp://u:<pw>@db.lan/` (32) | shown | SHOWN | `<ENCODED_1>` |
| `curl -u user:<pw>` (28) and with a trailing newline (32) | shown | `<ENCODED_1>` | `<ENCODED_1>` |
| `password=` + S12 (28) | shown | `<ENCODED_1>` | `<ENCODED_1>` |
| `https://app:<pw>@db.example/p` (44) | `<HIGHENTROPY_1>` (40+ characters, already held) | same | same |
The review's second case is CONTESTED in part: `withhold_commands` does NOT withhold an inline `curl -u user:<pw>` (MEASURED: the plain
text on a card gives `see curl -u user:<SECRET_1> now`, and the hook of the decoded text leaves it as `curl -u user:Kp7rTq2W`), so
the curl blob was masked under v4's hook too. The URL case is real and is the reason for L19. Plain text is safe either way: the same
hook removes a plain URL credential from the card (`see [link removed] now`).

Separator (MEASURED on the prototype): `_B64_SEP` survives `neutralise_untrusted`, `channel._neutralise` and no neutralise; 3 pieces
`["status ok", "hello world", "x"]` stay 3 under each (TB-3.18 now checks `neutralise_untrusted`, the hook the step uses, plus None).
- v3's `"\n\x1e\n"` is withdrawn: `sanitise_text` strips `_CONTROL_CHARS` (gate.py 135-146, `range(0x0B, 0x20)` holds `\x1e`).
- v4 measured 837 joined texts (31 piece ends x 9 piece starts x 3 neutralise choices): 81 lose a separator, exactly the 3 ends
  that open a quoted credential value (`secret="`, `api_key='`, `"password": "`) followed by a piece that closes the quote; the
  quoted-value patterns then take the separator into the value. Those fall back to "every unit a hit" (fail closed, over-masking
  only). NOT RE-RUN for v5's single hook (the matrix included it). MEASURED on the prototype: `['secret="', 'plain words" here',
  'x' * 12]`, `["api_key='", "ok' done", "zz"]` and `['"password": "', 'a" b', 'c']` lose one separator (2 pieces after) and give
  all hits; v4's TB-3.17 input `['secret="', 'plain words here', 'x']` does NOT (no closing quote, 3 pieces, no hit): TB-3.17 is
  corrected.
- With `.:.:.` as the separator, 20 of 42 texts already failed on `password=`-style ends (v4 measurement). `;` is not taken.
- It holds no `\`, `%` or `&` and is ASCII, so it does not turn on `scan` for the joined text. It holds no alphabet character, so it
  is never part of a run.

What a fence or tag split across pieces does: `seen` and `after` are both made by the same neutralise of the same joined text; with
`neutralise_untrusted` no fence or tag is rewritten at all (it escapes markers and placeholder look-alikes only). A rewrite that
changes the number of separators falls back to all hits. Not taken: per-piece `_scan` calls (L15 fallback; v4 measured 300 decoded
pieces that each find a secret, scanned one by one against a 1,000-entry map, 6.4 s, against 0.22 s for one joined scan of 2,000
such pieces).

### 3.5 What stays out of G4a, and the bundle path
- `redact_bundle` calls `runmap.redact_untrusted` for every string (k1b/redaction.py 188), so the bundle path gets the base64 step.
  L-B3: a direct call of `redact()` or `redact_many` (tests, a future caller) gets no base64 step.
- k1b counting: `redact_bundle` returns `Counter(_kind(p) for p in mapping)` (k1b/redaction.py 195). Under L8 the map holds one
  ENCODED entry per distinct hit blob, plus the kept decoded entries (secret and regulated kinds). So the report gains an
  `ENCODED n` row, and `SECRET` (or another non-stored kind) counts a value that was only written encoded. Stated: such a value is a
  distinct value the bundle hid.
- Pass 2 of the bundle sweeps the blob, which is HELD, so it is not decoded again. Pass 2 also sweeps any plain copy of a kept
  decoded secret.
- Not changed: `tools._b64_holds` / `tools._derived` and `k1b.redaction._pair`.
- `tools.redact_layered` catches only `TooDeep` (tools.py 983), so an `InputTooLarge` from the unit cap makes a tool result a tool
  error.

## 4. G4b: the kind ENCODED (guard/redact.py)
1. `_LABELS = tuple(dict.fromkeys([*(label for label, _ in PATTERNS), "ENCODED"]))` (redact.py 868). ENCODED is NOT in `PATTERNS`.
   - What follows from `_LABELS`: the counters (`_Redactor`, 1112). Since E9 nothing else is built from it: `_KIND` and
     `_OPENINGS` are gone and `_OWN_OUTPUT` names `SECRET` only (CHANGED in v7: `_OWN_TOKEN` / `_OWN_OUTPUT`, redact.py 889-890). v4's "`_OWN_OUTPUT` follows" is withdrawn.
   - Own output after E9 (MEASURED on the prototype at e8ff6de2b): `password=<ENCODED_1>` stays as typed with no entry, by the OLDER
     rule of `_decide` (a value that is nothing but genuine placeholders, any kind: CHANGED in v7: redact.py 1672-1675). `password=‹ENCODED_1›`
     (escaped look-alike) is masked as `password=<SECRET_1>` with the entry `‹ENCODED_1›`, exactly as `password=‹EMAIL_1›` is; and
     `password=<ENC` (a cut-off opening) is masked as `password=<SECRET_1>`, as `password=<EMA` is. So the v4 nit "`<ENC` is a
     cut-off own opening left unmasked" no longer applies: E9 limits cut-off openings to `<SECRET_`.
   - The growth-factor test (tests/test_runmap_enforce_map.py:470, longest label) still passes: ENCODED is 7 letters, AZURERESOURCE 13.
   - tests/test_redact_context_after_sweep.py:469 calls `_place` for every label of `_LABELS`, ENCODED included: it is run in Phase 2.
2. `SECRET_KINDS` gains "ENCODED" (CHANGED in v7: redact.py 2182-2198).
3. Counter restoration needs no new code (CHANGED in v7: redact.py 1112-1121: a kind in `self.counters` is restored from the map's numbers).
4. `def place_encoded(mapping: dict[str, str], runs: list[str]) -> list[str]` is the only writer of ENCODED.
   - For each run in order, it returns the placeholder the run gets and adds it to `mapping` IN PLACE: exactly one entry per new run.
     No `_PIECE` pieces, no `_spelled`, no journal.
   - Numbering: the next number is `_Redactor(dict(mapping)).counters["ENCODED"] + 1`. Example: `{"<ENCODED_5>": a, "<ENCODED_2>": b}`
     gives `<ENCODED_7>` (the counter restore takes `max(count + 1, number)` per entry: 5, then max(6, 2) = 6).
   - A run that is already the original of an ENCODED placeholder gets that placeholder. That is the function's contract for direct
     callers; through `_pass_one` it is unreachable, because such a run is HELD.
   - A run that is the original of an identifier-kind placeholder (TENANT) gets a NEW ENCODED entry.
   - CHANGED in v6 (0.3b): once G9 is merged, a G9 union whose first token is `<ENCODED_n>` is registered by `_place_union` /
     `_place` as an ENCODED entry too; "only writer" means the only writer of an ENCODED entry for a base64 unit.
5. `_build` tie-break, restricted to the same original.
   - The sort key (CHANGED in v7: redact.py 1964, `key=lambda kv: -len(kv[1])`) is NOT changed. The rules loop (1967-1972; the
     two lines G4 replaces are 1971-1972) becomes:
     ```python
     rule = _sweep(placeholder, original)
     if rule is not None and (
         original not in self._rules
         or (_kind(placeholder) in SECRET_KINDS and _kind(self._rules[original][1]) not in SECRET_KINDS)
     ):
         self._rules[original] = (n, placeholder, rule)
     ```
   - For one original held by an identifier and by a secret kind, the secret kind's rule wins (as `runmap._rules_conflict` already
     does in `snapshot`). Two DIFFERENT originals keep the order the stable sort gives. CHANGED in v7 (review round 6 design M2):
     that is NOT what `snapshot` does: when `_rules_conflict` is true for ANY original, `snapshot` re-sorts EVERY entry with an
     every-copy rule (`_sweep(*kv) is _EVERY_COPY`: a secret kind of 4 characters or more) before the others, so two different
     overlapping originals follow the secret one at the gate whenever some other original of the map is held twice. The tie-break
     does not do that; so gate mutant R8 is NOT equivalent under G4 (9.3, TB-2.11, MEASURED).
   - CHANGED in v6 (review round 5 N1): the winning secret entry keeps ITS OWN index `n` (the line stores `(n, placeholder, rule)`
     of the later entry), so an original that is also held by a later secret entry moves back in the order the sweep applies
     overlapping values in. v5's "the docstring stays true" is withdrawn: `enforce_map`'s docstring clause "(the earlier in the map
     when equal)" (runmap.py 732) becomes "(the earlier in the map when equal; since G4, an original that is also held under a
     secret kind takes the place of that secret entry)", and `test_e5_...`'s docstring (tests/test_runmap_enforce_map.py 519-520,
     "The redactor keeps the first placeholder's rule for an original held twice. An identifier kind listed first made the copy
     glued to a letter pass although the same value is a secret kind below it.") gains the sentence "Since G4 the redactor's own
     sweep keeps the secret kind's rule (the `_build` tie-break)." Both edits in Phase 2. The fifth map of TB-2.8 pins it.
   - No mutant pins either line (snippet script: no `old` text of the five mutant files holds them).
   - CHANGED in v7 (review round 6 readiness N4): a third stale text. The comment under `if _rules_conflict(known):` in `snapshot`
     (runmap.py 907-909) reads "One original under two placeholders (E5): the redactor keeps the FIRST placeholder's rule, so the
     stronger rule (every copy, a secret kind) goes first. Built fresh: the run's cache holds the map's own order." In Phase 2 it
     becomes: "One original under two placeholders (E5). Since G4 the redactor itself keeps the secret kind's rule for that
     original (the `_build` tie-break); this re-sort is kept because it also puts every every-copy entry before the others, which
     decides the order of DIFFERENT overlapping originals at the gate (test_e5b). Built fresh: the run's cache holds the map's own
     order." (Comment only; R8's `old`, `        if _rules_conflict(known):\n`, is the line above it and is not touched.)
   - MEASURED: `redact("pre"+X+"post and "+X+" alone", mapping=...)` with `X = "QUJD"+"REVG"+"R0hJ"`: at the base with
     `{"<TENANT_1>": X, "<SECRET_1>": X}`: `preQUJDREVGR0hJpost and <TENANT_1> alone`; on the prototype with
     `{"<TENANT_1>": X, "<ENCODED_1>": X}`: `pre<ENCODED_1>post and <ENCODED_1> alone` (TB-2.7).
   - MEASURED at the base AND on the prototype, `enforce_map("x ab-cd-ef y", m)` for the four maps (TB-2.8, review round 4 readiness
     Major 7), identical on both (CHANGED in v7: the values of a tree WITHOUT G9; with G9 they change, 0.3b table):
     | m (in insertion order) | output |
     |---|---|
     | `{"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd"}` | `x ab-<TENANT_1> y` |
     | `{"<SECRET_1>": "ab-cd", "<TENANT_1>": "cd-ef"}` | `x <SECRET_1>-ef y` |
     | `{"<TENANT_1>": "ab-cd", "<SECRET_1>": "cd-ef"}` | `x <TENANT_1>-ef y` |
     | `{"<SECRET_1>": "cd-ef", "<TENANT_1>": "ab-cd"}` | `x ab-<SECRET_1> y` |
     v3's sort key `(-len, kind not in SECRET_KINDS)` would have changed the first to `x <SECRET_1>-ef y` (L16 fallback).
   - CHANGED in v6 (review round 5 N1): a FIFTH map, `{"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd", "<SECRET_2>": "cd-ef"}`, where
     the tie-break moves the rule index. Text `x ab-cd-ef y`. CHANGED in v7: MEASURED at 944d143db (`r8.py`: G4's rules loop
     patched into `_Redactor._build` in-process), equal to review round 5's values read by v6:
     | call | base | after G4 |
     |---|---|---|
     | the redactor's own sweep, `runmap._Redactor(m, None).sweep(t)` (as test_e5's `_one_sweep`) | `x ab-<TENANT_1> y` (cd-ef at index 0, TENANT rule, standalone after `-`) | `x <SECRET_1>-ef y` (cd-ef's rule is SECRET_2's at index 2; ab-cd at index 1 goes first) |
     | `runmap.enforce_map(t, m)` | `x <SECRET_1>-ef y` (`_rules_conflict` is true, so `snapshot` sorts the every-copy entries first) | `x <SECRET_1>-ef y` |
     The builder re-measures both rows in Phase 2 and pins the measured strings; a difference from this table is recorded in the
     evidence (not a STOP unless the after column shows a readable `ab-cd` or `cd-ef`). With G9 merged: the G9 + G4 column of 0.3b.
6. `defaults.STORED_KINDS` does NOT change, and `runmap._GRAMMAR` gets no ENCODED entry.
7. `RedactionResult.actions` does not count ENCODED replacements (it has no reader in src; stated).
8. approvals/channel.py 98 `_ASSIGNMENT_KINDS` gains "ENCODED" (L10). What it does, MEASURED (TB-3.26, review round 4 codebase B3):
   it matters only for a blob whose decoded value is of a STORED kind (e-mail, host, IPv4), which leaves no kept entry. For a
   decoded secret, the kept SECRET/URLCRED entry is itself an assignment kind and the joined path of `channel.clean` already wins.

Fallback if the lead declines the name (L1): `place_encoded` issues `<SECRET_n>`, points 1, 2 and 8 are dropped, and the tests assert
SECRET.

## 5. G4c: whole host names (guard/redact.py, the HOSTNAME entries of PATTERNS)
### 5.1 One place for the suffix list
`_HOST_BARE = "internal|local"` and `_HOST_TAIL = "corp|lan|intranet|intra|localdomain|home" + _HOST_DOT + "arpa"`, beside the pattern.
`defaults.PRIVATE_SUFFIX_LABELS` is a different job and is not used. A `#` comment beside each names the other.

### 5.2 The main pattern (replaces redact.py 407-414; same place; no capture group). MEASURED in-process by v4 (cd8d375).
```
_HOST_LABEL = r"[A-Za-z0-9_-]+"
_HOST_DOT = r"(?:\.|\[\.\])"
HOSTNAME = (
    r"(?i)(?<![\w-])(?<![\w-]\.)(?<![\w-]\[\.\])(?:" + _HOST_LABEL + _HOST_DOT + r")+(?:"
    r"(?:" + _HOST_BARE + r")(?:-[A-Za-z0-9_-]*+(?![\w-])(?:" + _HOST_DOT + _HOST_LABEL + r")*"
    r"|(?![\w-])(?!" + _HOST_DOT + r"\w|\())"
    r"|(?:" + _HOST_TAIL + r")(?:-[A-Za-z0-9_-]*+)?(?![\w-])(?:" + _HOST_DOT + _HOST_LABEL + r")*)"
)
```
1. Start. A match does not start right after a name character or `-`, nor after a dot or a `[.]` that follows a name character. So
   it starts at the first label of a dotted token, as P1d-a round 3's `_DOMAIN` does (gate.py `(?<![\w-]\.)`). Two measured failures
   of the alternatives (v4, in a throw-away worktree):
   - v3's `(?<![\w.\-\]])` failed `tests/test_p1d_a_paths.py::test_property_no_linkable_host_on_the_card_and_the_card_reads_the_same_twice`.
     Its input `(x<HOSTNAME_1>&.]db-7.corp.internalx` was not masked at all (no start after `]`), where the base gave `db-7` masked.
   - A plain `(?<![A-Za-z0-9_-])` made `"a.-_" * 12500` quadratic: 2.2 s for 20,000 characters, and `redact_text` 11.47 s, which
     failed `test_secret_patterns_are_linear_on_a_50000_character_run[name run with dots]`.

   This start masks that input as `(x<HOSTNAME_1>&.]<HOSTNAME_1>` and `x/.db01.corp.example` as `x/.<HOSTNAME_1>`. Measured:
   0.001-0.007 s on 50,000 characters of `a[.]`, `a.-_`, `a-`, `a.`, `ab-cd.` and `a[.]`...`corp`.
   STATED RISK (review round 4 readiness nit, codebase B5): this final start look-behind was NOT run through the suites (the pre-final
   one ran 710 passed, 1 failed: the perf row it was changed for). The p1d property corpora (tests/test_p1d_a_rows.py 68-166, 2,000
   texts through `channel.clean` from the TXT-A / TXT-B / EH alphabets of tests/fixtures/p1d_cases.py 65-153, which hold
   `db01.corp.example.com`, `<HOSTNAME_1>`, `.`, `-`, `_`, `[.]` and `。`) and tests/test_p1d_a_paths.py `_PIECES` (about 268) are
   the guard: a red in any of them in Phase 4 is a STOP (12).
2. Label class ASCII (L11). Non-ASCII labels stay the fold scan's job (it runs first on every non-ASCII line: CHANGED in v7: `find` calls `_fold_scan` at redact.py 1170).
3. Tail: after a `_HOST_TAIL` suffix, the rest of the dotted name is in the match. A trailing dot is not a label
   (`db01.corp.example.` gives `<HOSTNAME_1>.`). A port, a path and `@` end the name.
4. Bare suffix `.internal` / `.local`: a following label or `(` means code (`jdk.internal.reflect`, `threading.local()`), so there is
   no match.
5. Suffix boundary `\b` -> `(?![\w-])`, with a hyphenated rest taken in (decision L14).
   - The base's `\b` matched up to the suffix when a `-` followed it, and left the rest readable. v3's `(?![\w-])` alone would have left
     the whole name unmasked (a fail-open change).
   - v4/v5 take `-` and label characters after the suffix into the name, and, for `.internal`/`.local`, the dotted labels after them
     (code names hold no `-`).
   - MEASURED (base -> v5): `db01.corp-prod`: `<HOSTNAME_1>-prod` -> `<HOSTNAME_1>`; `x.local-dev`: `<HOSTNAME_1>-dev` ->
     `<HOSTNAME_1>`; `x.internal-api`: `<HOSTNAME_1>-api` -> `<HOSTNAME_1>`; `db01.corp-prod.example`:
     `<HOSTNAME_1>-prod.example` -> `<HOSTNAME_1>`; `x.local-dev.foo`: `<HOSTNAME_1>-dev.foo` -> `<HOSTNAME_1>`.
6. `_KEPT_HOST` is unchanged and applied to the whole match in `_decide`. MEASURED unchanged: `x.svc.cluster.local`,
   `x.svc.cluster.local.foo`, `eu-west-1.compute.internal`, `ec2.internal`, `jdk.internal.reflect.Method`, `threading.local()`.
   A defanged `x[.]svc[.]cluster[.]local` is masked (accepted).
   CHANGED in v7 (review round 6 design N1): because `_KEPT_HOST` is searched in the WHOLE match, a private name that goes on into
   a kept suffix is kept whole: `dial db01.corp.example.svc.cluster.local now` is unchanged after G4c, so `db01.corp` stays readable
   (MEASURED with v6's 5.2/5.3 patterns put into `redact.PATTERNS` in-process, `g4c.py`; the base gives the same text, because its
   pattern also matches the whole name up to `.local` and `_KEPT_HOST` keeps it). Stated limit L-H5, pinned by a TB-4.8 row (plain
   assert of the unchanged text) and named in SECURITY. Not changed: testing `_KEPT_HOST` on the part after the private suffix would
   mask in-cluster service names that hold `.corp`, which WARDEN reads and acts on (the reason `_KEPT_HOST` exists).
7. Java packages: `com.acme.corp.billing.Service` was `<HOSTNAME_1>.billing.Service` and becomes `<HOSTNAME_1>` (limit L-H1, an
   over-mask, pinned by TB-4.7 as a plain assert).

### 5.3 The host-key rule (a second ("HOSTNAME", HOSTKEY) entry right after the main one; group 1 is the value). MEASURED in-process by v4.
```
_HOST_ARCH = r"(?:x86(?:[-_]64)?|x64|i[3-6]86|amd64|arm64|aarch64|ppc64|win(?:32|64))"   # CPU and platform names a build log writes after `host`
HOSTKEY = (r"(?i)(?<![\w-])(?:--)?host(?:name)?(?:[\"']?[ \t]*[:=][ \t]*[\"']?|[ \t]+)"
           r"(?!" + _HOST_ARCH + r"(?![\w-]))"
           r"([A-Za-z][A-Za-z0-9_-]{0,60}(?:-[0-9]|[0-9]{2}))(?![\w\-/@])(?!\.\w)")
```
Decision L13. The value is one label of 3 to 63 characters that starts with a letter and ENDS in two digits or in a hyphen and a
digit, and is not a CPU architecture name.
- Kept (each was masked by v3's rule): `host ec2 failed`, `host k8s node`, `host x86 box`, `host http2 on`, `host x86_64`,
  `host eth0 up`, `host arm64 runner`, `host: x86_64-unknown-linux-gnu` (`rustc -vV` prints it), `hostname: Web2`, `host web1 down`.
- `host s3 bucket` is not masked even by v3's rule, because `s3` is 2 characters (contested in round 3, measured).
- CHANGED in v7 (review round 6 design N3): `_HOST_ARCH` gains `x64`, `x86-64` (as `x86(?:[-_]64)?`) and `win32` / `win64`.
  MEASURED (`g4c.py`, patterns in-process): with v6's `_HOST_ARCH`, `host x64 build`, `host win32 target`, `host win64 target` and
  `host x86-64 runner` gave `host <HOSTNAME_1> ...`; with v7's they are unchanged, and `host x86_64`, `host x86 box`, `host arm64
  runner`, `host: x86_64-unknown-linux-gnu` stay unchanged while `host db01 down`, `host py311 image`, `host web-1 down` and
  `hostname=db02 state=down` are still masked. The base masks none of them.
The sweep side effect: a value this rule registers is a HOSTNAME entry, and `_sweep` / `_replace_standalone` (CHANGED in v7: redact.py 2246, 2267)
then replace every later standalone copy in the run.
- MEASURED: v3's rule turned `host ec2 failed; see ec2.internal, k8s.io, s3://b and x86_64 builds` into
  `host <HOSTNAME_1> failed; see <HOSTNAME_1>.internal, ...`. v5 leaves the whole line unchanged.
- For a real host the side effect is intended and stated: `host db01 down; tail db01.log` gives
  `host <HOSTNAME_1> down; tail <HOSTNAME_1>.log`.
Masked on purpose, stated in SECURITY: a label of letters and two or more digits after `host`, also when it is not a host
(`host py311 image`, `host sha256 sum`, measured, masked), and with it every later standalone copy in the run.
Not masked (limit L-H4): a host name with a single trailing digit after a letter (`web1`, `db1`, `node7`).
Must-keep rows, all MEASURED unchanged (v4): `host is down`, `server timed out`, `Server: nginx`, `Server: nginx/1.18.0`,
`Server: AmazonS3`, `server 500 error`, `ghost town db01`, `ghost=ab12`, `Host: api.github.com`, `host: localhost`,
`--host 0.0.0.0` (IPV4 masks the address), `host 1 of 3 failed`, `the hostname is unknown`, `host x-ray`, `host re-election`,
`host 2026-11-20T10:00 started`.
Closed, measured: rows 33 `host <HOSTNAME_1> is down`, 34 `host: <HOSTNAME_1>`, 35 `hostname=<HOSTNAME_1> state=down`,
36 `psql --host <HOSTNAME_1> --port 5432`.

### 5.4 Restorable grammar
`runmap._GRAMMAR["HOSTNAME"]` is unchanged, so an original with `_` or `[.]` is never stored. Fallback (L5): add `_` to the grammar.

## 6. G4d: bare numbers (written down, pinned)
One paragraph in the module docstring of guard/redact.py, placed after the "What this is not" paragraph (redact.py 21-25, ending
with the "(A re-scan inside redact() ...)" sentence) and after G8's paragraph when G8 is merged (0.3; CHANGED in v6: the placement
words of G8 v3 4.3), before the closing `"""` (redact.py 26):

"A bare number with no label or context (for example `ref 55556666 paid`) is not masked, by decision (order 64 item 4). Masked by
shape: 10 to 16 contiguous digits (PHONE; exactly 12 as ACCOUNTID) and 16 digits in four groups of four joined by spaces or hyphens
(CREDITCARD). Other groupings are masked in part or not at all: 16 digits joined by dots lose their first 12 to MAC and keep the last
group; 15 digits in 4-6-5 groups lose the first 10 to PHONE and keep the last 5."

and one sentence after it: "A value only written in base64 is found by the decoded view of `runmap.redact_text` and masked whole as
ENCODED; `redact()` itself does not decode."

If G8 lands first and changes PHONE (CHANGED in v6: G8 v3 4.1 entries 6-8, the three new PHONE entries; its entry 5 is
CREDITCARD, which this paragraph also names), the paragraph's PHONE (and CREDITCARD) sentence is re-derived in Phase 0 (b) from the probe
run, and the class pin below is updated from that run (0.2 step 2: a table update, never a STOP).

The pin, by class, RE-MEASURED at e8ff6de2b (the same rows as v3 and v4):
- 24 not masked: 1-7, 9-12, 14-20, 30, 35, 38-40, 43;
- 2 in part: 29, 32;
- 17 whole: 8, 13, 21-28, 31, 33, 34, 36, 37, 41, 42.
The classifier (I18 and tests/p1c_cases.py `number_class`, 11) is written out in 10.1.

## 7. Constants (defaults.py, one SPINE commit holding only these lines and their comments)
They are placed right after `SPELLED_MAX_WORK = 4_000_000` (CHANGED in v7: defaults.py 115), before `def cut_margin`. (v4's anchor
`SPELLED_MAX_FORMS` no longer exists.) CHANGED in v6 (header, G7 r7): at bff88a7a1 `SPELLED_MAX_CHARS = 1_000_000` and its comment
(defaults.py 116-125) stand between the two; the eight constants go right after `SPELLED_MAX_CHARS`, before `def cut_margin`
(and after G9's `SPELLED_MAX_PASSES` when G9 lands first, 0.3b). Exact comment above each, one line each; no host and no 32-character run in them:
| constant | value | comment text and the source of the number |
|---|---|---|
| `B64_MIN_CHARS` | 12 | "# shortest base64 run (padding not counted) the redactor decodes; 12 characters are 9 bytes". Source: under 15, the shortest leaked probe blob (1b row 83), and a multiple of 4. |
| `B64_WRAP_MIN_CHARS` | 16 | "# shortest first line of a wrapped base64 block; every line but the last has its length". Source: chosen; the probe wraps at 32, 64 and 76. |
| `B64_PRINTABLE_SHARE` | 0.90 | "# share of printable characters a decoded run needs to count as text". Source: chosen; Phase 4 sweeps 0.85 to 0.95. |
| `B64_UTF16_ZERO_SHARE` | 0.90 | "# share of zero bytes at the odd (LE) or even (BE) positions that reads a decoded run as UTF-16". Source: chosen; ASCII in UTF-16 has 1.0. |
| `B64_MAX_UNITS` | `MAX_MAP_ENTRIES` (2000) | "# decodable, not held base64 units per redact_text call (all views, all depths); one more is refused (InputTooLarge)". Source: the run map's default ceiling (L9). |
| `B64_MAX_DECODED_CHARS` | `MAX_REDACT_CHARS` (262,144) | "# decoded characters per redact_text call; past it the call is refused (InputTooLarge)". Source: the redactor's own cap. |
| `B64_MAX_UNIT_CHARS` | `1 << 16` (65,536) | "# longest base64 unit that is decoded; a longer one that pass one did not hold is masked unread". Source: a quarter of the cap. Written `1 << 16`: tests/test_no_hardcoded_values.py (about 164) forbids the literal `= 65536` in the `K5_FILES`. |
| `B64_MAX_DEPTH` | 3 | "# levels of base64 decoded and read; a unit found at this depth is masked unread". Source: the probe's double rows need 2, plus one of slack. |

Two comment sentences (review round 4 nits: new anchors and the "and ..., and" grammar). Each is a NEW SENTENCE, so no list is
extended:
- In the budget comment above `REDACT_BUDGET_S`, the clause at defaults.py 59-60 reads today "... every 32nd free segment (only when
  the map holds a value), every value replaced, and every 1,024th unit of work of the compound-form scan (a placeholder token of the
  text, with or without a form, a step of the backward prefix walk, a step of the forward suffix walk, or an entry looked up at a
  suffix terminal) and the registration of a union (one per character). A spent budget raises InputTooLarge, ...". Insert, between
  "(one per character)." and "A spent budget", the sentence: "Since G4 the budget is also read once before each base64 unit that is
  decoded or masked unread (`runmap._ScanBudget.clock`)."
- The `clean()` clause (defaults.py 83-87) ends "... a 71,179-character card 367 ms -> 655 ms." Append at the end of that line,
  before `REDACT_BUDGET_S = 6.0`, the sentence: "Since G4, a call whose text holds a decodable base64 unit that pass one did not hold
  runs `redact()` a second time per scanned spelling, and one scan of the decoded texts."
  (Line length: wrap at the file's existing width; the comment lines of this block are long already, ruff does not reflow comments.)

Fallback (L7): the eight constants as module constants in runmap.py.

## 8. Cost and map growth
Baseline and the step's own cost, MEASURED on the prototype at e8ff6de2b (B6): this container, `time.thread_time()`, best of 5,
interleaved, a fresh `RunMap` per call, scratch script `m_perf.py`; "step off" = the same build with `runmap._B64_RUN =
re.compile(r"(?!)")` (the I16 baseline). The machine was loaded (load 3 to 6 on 4 cores), so read the ratios.
| text | units found | decode to text | `redact_text` off -> on | `redact_untrusted` off -> on |
|---|---|---|---|---|
| 100,000 characters of snake_case words and paths (seeded generator of `m_perf.py`) | 2,599 | 0 | 0.163 s -> 0.173 s (x 1.058) | 0.164 s -> 0.175 s (x 1.066) |
| 100,000 characters of prose | 0 | 0 | 0.199 s -> 0.200 s (x 1.003) | 0.204 s -> 0.203 s (x 0.994) |
Inside the snake_case cost: `_b64_units` 4.5 ms and `_b64_text` over the 2,599 units 2.2 ms; the rest (held check, one clock read
per unit, the dedupe) about 3-4 ms. About 4 microseconds per unit.

DECISION (B6, L22): no pre-filter. The measured overhead is 6-7 percent against `PLAIN_RATIO = 1.15`, which stays. The cheap
pre-filter "a unit is decoded only if its body holds an upper-case letter or a digit" was measured too: it removes all 2,599
snake_case units (none decodes to text anyway); it is the FALLBACK if I16 fails in Phase 3 (it would leave a blob of only lower-case
letters, `+`, `/`, `_`, `-` undecoded: a stated limit then). Reading the clock every N units instead of every unit was not needed.

v4's table (cd8d375, best of 3) for the record: snake_case 0.164 s, prose 0.164 s, the snake_case text with one planted `password=`
0.263 s, 2,000 base64 secrets (57,999 characters, each base64 of `password=` + 12 characters) 0.086 s. NOT RE-MEASURED on the
prototype: the planted text and the 2,000-secret text (the step's worst case for the cap, CAP_CEILING_S of 13.4, is measured by I16
in Phase 3).

A text with a hit pays `redact()` twice per scanned spelling, plus one recursive `_scan` per spelling with units. Held units are
swept, never decoded twice.

MAX_MAP_ENTRIES: `defaults.MAX_MAP_ENTRIES` = 2000 (defaults.py 24) is `config.evidence.max_map_entries` (config.py 245).
agent_loop.py 427 and 547 end the run `NEEDS_PERSON` / `document_too_complex` when the map is over it.
- Per `redact_text` call, G4 adds one ENCODED entry per hit unit (at most `B64_MAX_UNITS`) plus the kept decoded entries (L8:
  secret and regulated kinds only).
- A run that crosses its ceiling is refused by that existing check (I23).

Refusals G4 can cause, and what each caller does (review M4 of round 3, round 4 B4):
- more than 2,000 distinct decodable, not held runs, or more than 262,144 decoded characters: `InputTooLarge("InputTooLarge")`;
- a spelled-form scan past `SPELLED_MAX_WORK` in either `redact()` of `_pass_one`: `InputTooLarge("SpelledWorkTooMuch")` (2.6;
  hostile text only, MEASURED route in TB-3.33);
- CHANGED in v6: the spelled-form registry past `SPELLED_MAX_CHARS` in either `redact()` of `_pass_one`:
  `InputTooLarge("SpelledMemoryTooMuch")` (G7 r7, in the tree; 2.6, BY READING);
- CHANGED in v6 (review round 5 M3; only when G9 is merged, 0.3b): a sweep of either `redact()` of `_pass_one` not settled in
  `SPELLED_MAX_PASSES` passes: `InputTooLarge("SpelledNotSettled")`; at the gate (`enforce_map`, `held_value_left`'s checker, not
  `redact_text`), an overlap the gate's redactor may not register: `InputTooLarge("SpelledOverlap")` (G9 L-D1);
- then: a document ends `NEEDS_PERSON` `document_too_large`; a tool result becomes a tool error (`redact_layered` catches only
  `TooDeep`); a k1b bundle raises `InputTooLarge`;
- a CARD is NOT shown `SETTLE_NOTE`. The first `redact_text` calls of `channel.clean` (channel.py 37 and 44) and `cards._card`
  (cards.py 58-63) are not wrapped; only `settled`'s re-reads (channel.py 76-95) turn a refusal into `SETTLE_NOTE`. So
  `render_shadow` / `render_abstain` raise, and agent_loop.py 622-625 / 649-654 catch it as an unrenderable card: `card = None`,
  no card is posted, and the event is recorded `abstain_undelivered` or `shadow` with `result="undelivered"`;
- `requests` summary (requests.py 35-51) falls back to its short text with "Inputs: (too large to show here)";
- `FakeChannel.send` / `notify` and `SlackChannel` notify (channel.py 159, 166; slack_channel.py 187) raise to their callers.

This is the same path every card text over the redactor's cap takes today. It is stated, not changed (L17); TB-3.25 pins it.
Masking every further unit unread past the cap was not taken (contested in round 2, M7: it would over-mask benign runs and add
entries past the map ceiling, which refuses the run anyway).

defaults.py's budget comment (52-87) and the `SPELLED_MAX_WORK` comment (89-111) record G7's worst cases (`password=` x N 2.5 to
3.2 s, `curl -u ` 4.5 to 5.4 s against the 6.0 s budget). G4 adds to a text only when it has a hit.

## 9. Expected results per probe row
### 9.1 Base64, 142 rows ("unchanged" = output and map digest equal to the base commit's, through both functions)
| rows | value | expected |
|---|---|---|
| 1b 1-5, 7, 8 | kv secret short | one `<ENCODED_n>` where the blob stood; the map holds the ENCODED entry and the decoded SECRET entry (L8) |
| 1b 6, 9-16 | kv secret | unchanged (HIGHENTROPY holds it) |
| 1b 17-32 | bearer token | unchanged |
| 1b 33-37, 39, 40 | AWS key id short | ENCODED (map kinds APIKEY, ENCODED) |
| 1b 38, 41-48 | AWS key id | unchanged |
| 1b 49-53, 56 | e-mail short | ENCODED (no EMAIL entry kept: EMAIL is a stored kind) |
| 1b 54, 55, 57-64 | e-mail | unchanged |
| 1b 65-72 | host name short (70 UTF-16-LE, 71 double) | ENCODED |
| 1b 73-80 | host name long | unchanged |
| 1b 81-88 | private IPv4 short (83 = 15 characters; 86 UTF-16-LE) | ENCODED |
| 1b 89-96 | private IPv4 long | unchanged |
| 1b 97-101, 104 | connection string short | ENCODED (map kinds ENCODED, URLCRED) |
| 1b 102, 103, 105-112 | connection string | unchanged |
| 1b 113-117, 120 | JSON with password short | ENCODED |
| 1b 118, 119, 121-128 | JSON with password | unchanged |
| 1c 1, 5, 9 | wrapped at 32 | the whole block is one `<ENCODED_1>` |
| 1c 2 | wrapped at 64, last line held 11 of 14 password characters | one `<ENCODED_1>` |
| 1c 3, 6, 7, 10, 11 | wrapped at 64 / 76, no leak today | KIND CHANGE: exactly `<ENCODED_1>`; no HIGHENTROPY entry |
| 1c 4, 8, 12 | `data:` URL | unchanged (HIGHENTROPY) |
| 1c 13, 14 | `Basic <b64>` | unchanged (BASIC) |

MEASURED on the prototype at e8ff6de2b (probe, base vs prototype): exactly the 48 + 9 rows above change; every other row prints the
same output cell and map kinds; the leaked rows at the base are exactly 1b 1-5, 7, 8, 33-37, 39, 40, 49-53, 56, 65-72, 81-88,
97-101, 104, 113-117, 120 and 1c 1, 2, 5, 9; `redact_untrusted` gives the same verdict on every 1b row. 1c has 14 rows: both
`no_digit_line` searches find nothing, and they still consume the generator. (Map DIGESTS of the 85 rows are compared by I2 in
Phase 3; the probe prints outputs and kinds only.)

### 9.2 Host names, 44 rows (G4 column MEASURED by v4 in-process with the patterns of 5.2/5.3; Phase 0 (b) re-measures)
| row | input shape | expected after G4 | class at the base |
|---|---|---|---|
| 1, 2, 17, 19, 24, 26, 29, 37, 38, 44 | `...corp.example` with port, URL, upper case, trailing dot, punycode, `host=`, JSON, two names | whole name one placeholder (`dial <HOSTNAME_1> now`; 17 `dial <HOSTNAME_1>:5432 now`; 19 `GET https://<HOSTNAME_1>/v1/items done`; 26 `dial <HOSTNAME_1>. now`; 37 `host=<HOSTNAME_1> port=5432`; 38 `{"host": "<HOSTNAME_1>", "port": 5432}`; 44 `from <HOSTNAME_1> to <HOSTNAME_2> done`) | part: closed |
| 21 | URL with credentials | `use postgres://app:<URLCRED_1>@<HOSTNAME_1>:5432/orders now` | part: closed |
| 39, 40 | `.`, `%2E` dots | `dial <HOSTNAME_1> now` | part: closed |
| 32 | `db_01.corp.example` | `dial <HOSTNAME_1> now` | whole: closed |
| 43 | `db01[.]corp[.]example` | `dial <HOSTNAME_1> now` | whole: closed |
| 33, 34, 35, 36 | host-key rows | as in 5.3 | whole: closed |
| 3, 4, 5, 7, 11, 12, 13, 14, 18, 20, 22, 23, 25, 27, 28, 30, 31, 41 | already masked | unchanged | masked |
| 6, 8 | `.internal` / `.local` then more labels | unchanged | kept on purpose |
| 9 | `.svc.cluster.local` | unchanged | kept on purpose |
| 42 | `ip-<IPV4_1>.eu-west-1.compute.internal` | unchanged | kept on purpose |
| 10 | `billing.payments.svc` | unchanged | limit L-H2 |
| 15, 16 | `db01.acme.example`, `db01.acme.test` | unchanged | limit L-H3 |

Totals: 19 closed (13 part rows, 6 whole rows); 3 limits, 4 kept, 18 unchanged. (13 part + 6 whole = 19: rows 1, 2, 17, 19, 21, 24,
26, 29, 37, 38, 39, 40, 44 part; rows 32, 33, 34, 35, 36, 43 whole.)

### 9.3 Other literal expectations in the tests tree that the change turns (MEASURED where marked)
| where (by name) | today expected | after G4 (exact) | action |
|---|---|---|---|
| tests/fixtures/p1d_cases.py `ROW_BY_ID["H27"]` card | `host <HOSTNAME_1>[.]example[.]com down` | `host <HOSTNAME_1> down` (MEASURED by v4 through `channel.clean`) | Modify the `after` cell (Phase 4) |
| `ROW_BY_ID["L2"]` card | `SAME` (= base cell ``run `curl <HOSTNAME_1>.example.com` now``) | ``run `curl <HOSTNAME_1>` now`` (MEASURED by v4) | Modify `after` from SAME to this literal; base cell stays |
| `ROW_BY_ID["L3"]` card | `SAME` | ```` ```\nping <HOSTNAME_1>\n```\nthen evil[.]com ```` (MEASURED by v4) | Modify `after` from SAME to this literal |
| tests/warden_port/privacy_corpus.py rows at lines 36, 37 | (kind only) | `db at <HOSTNAME_1>:5432`, `smb://<HOSTNAME_1>/share` (MEASURED by v4, both functions) | stay green (kind assertions); carved out of I4 into I12b |
| tests/test_runmap_enforce_map.py `test_e5_one_original_under_two_placeholders_follows_the_stronger_rule`, its first assert (line 523) `_one_sweep(f"a{value}b", mapping) == f"a{value}b"  # FAIL-BEFORE: the weaker rule won` | the redactor's own sweep keeps the weaker (TENANT) rule | `_one_sweep(...) == "a<SECRET_1>b"`: the `_build` tie-break (4 point 5) makes the redactor's own sweep follow the stronger rule. MEASURED on the prototype: RED as written (`'a<SECRET_1>b' == 'aZq9xLm4wb'`); the other two asserts stay green | Modify that one line (Phase 2) to `assert _one_sweep(f"a{value}b", mapping) == "a<SECRET_1>b"  # since G4 the redactor's own sweep follows the stronger rule (tie-break in _build)`; NEW in v5, found by the prototype run (decision L24) |
| tests/gate_mutants.py `R8 one original under two placeholders keeps the weaker rule (E5)` (old `        if _rules_conflict(known):\n`, killer test_e5) | KILLED | EQUIVALENT under G4: MEASURED in-process, `_rules_conflict` patched to False on the prototype still gives `a<SECRET_1>b <SECRET_1>` and `a<SECRET_1>b` (the tie-break orders the rules); at the base the same patch gives `aZq9xLm4wb <TENANT_1>` | L24 default: remove R8 from `M` in Phase 2 and add a comment line at its place naming it "equivalent since G4 (`_build` tie-break, ticket G4 v6 9.3; CHANGED in v6: v6); `_rules_conflict` stays as defence in depth"; gate_mutants' runmap.py count becomes 23. CHANGED in v6 (review round 5 M1): `len(gate_mutants.M)` goes from 105 to 104, and tests/test_gate_mutants_picked_up.py `MIN_MUTANTS = 105` (line 20; `test_the_gate_mutant_list_imports_and_is_not_shrunk` asserts `len(M) >= MIN_MUTANTS`) would go red: in the same Phase 2 commit it becomes `MIN_MUTANTS = 104  # R8 retired as equivalent since G4 (_build tie-break, ticket G4 v6 9.3)` |
| tests/fixtures/p1d_a_base_rows.json `L2/card`, `L3/card` | base record | not changed | contested in round 2 (the JSON records base 2742c1b and is read only for `BS0` cells) |
| tests/test_p1d_a_paths.py property `_PIECES` (`HOST = "db-7.corp.internal"`, about 26) | no host shown | stays green: with v3's start look-behind it went RED (v4, measured); v5's start (5.2 point 1) masks it | the reason for the start change; Phase 4 STOP if red |
| tests/test_text_parts_together.py about 242 (`db-7.corp`), tests/test_k1b_redaction.py 18 (`db01.corp.local`), tests/test_model_gate.py about 1744 (`db1.corp.example.org` map entry) | masked whole / unchanged | unchanged | stay green (v4's pre-final run: 710 passed, 1 failed, the perf row of 5.2 point 1); NOT RE-RUN on the final look-behind |
| tests/g8_cases.py rows 60-62, 64, 66, 71 (only when G8 is merged, 0.3) | `after` (G4c not merged) | `after_g4c` | `G4C_MERGED = True` in the Phase 4 commit |

`H27`'s `check_extra` (p1d_cases.py about 641-647) stays true. `assert len(ROWS) == 70` is unchanged.

Gate mutants whose killers move (tests/p1d_a_mutants.py, by name). MEASURED by v4 in-process: the G4c patterns installed, the mutant's
replacement applied to the function's source by `exec` (the same text replacement `tools/mutation_runner` makes), and the row
compared with its G4 expected cell:
| mutant | old killer | killed after G4 by | measured |
|---|---|---|---|
| A4 (`_PLACEHOLDER_DOT.sub` removed in `_defang_prose`) | `test_row_H27_card` (no longer kills) | `test_row_D3b_defang` (`mail <EMAIL_1>.org` -> `mail <EMAIL_1>[.]org`) | only D3b fails |
| A5 (`parts = [line]` in `_per_part`) | `test_row_L2_card` (no longer kills) | `test_row_D3c_defang` | only D3c fails |
| A38 (`fix(part) if i % 2 else part`) | `test_row_L2_card` (no longer kills) | `test_row_D3c_defang` (L3, I1, L4, L8, D3b also fail) | D3c fails |
| A6 (`for s, e, ch in []` in `_outside_code`) | `test_row_L3_card` (no longer kills) | `test_row_L11_slack` (``` ```\nping a[.]b\n``` ```: the slack re-read undefangs the fence body) | only L11 fails |

The comment above `_PLACEHOLDER_DOT` (gate.py 239-240) becomes: "# A placeholder (`<EMAIL_1>`, or a host name masked before G4 and
stored) followed by a dot and a name character: what follows the dot would stay linkable. Written `[.]` (P1d-a, D3)." The pattern
itself stays.

## 10. Invariants and the exact test list
Two kinds of test:
- TG tests (tests/test_p1c_gaps.py) use public names only and run on the base (FAIL-BEFORE).
- TB tests use private names reached INSIDE each test (`runmap.<name>`, `redact_mod.<name>`; no module-level import of a G4 name).
  They live in tests/test_b64_scan.py (G4a/G4b) and tests/test_host_names.py (G4c). `redact_mod` is
  `importlib.import_module("hadavin_sdk.guard.redact")` (`from hadavin_sdk.guard import redact` gives the FUNCTION: the package
  re-exports it, MEASURED).
Fixtures a TB test reaches (review round 4 nit): `from tests.k5_support import k5_cfg, build_runtime, handle` (TB-3.28, as
tests/test_k5_round5.py does); `from tests.test_redact_idempotent_property import CONSTRUCTED` (TB-3.19, TB-3.20; importing it builds
that module's corpus once, about 2 s: import it inside the two tests, not at module level).

Shared values, built from parts:
- `S12 = "Zq9" + "xW4" + "mT7" + "pL2"`;
- `SB = b64("password=" + S12)` = `cGFzc3dvcmQ9WnE5eFc0bVQ3cEwy` (28);
- `B1 = b64("this is just a status message")` (40);
- `B2 = b64("ok status 200")` = `b2sgc3RhdHVzIDIwMA==`;
- `X = "QUJD" + "REVG" + "R0hJ"`;
- `PW = "Kp7" + "rTq" + "2W"` (B2 cases);
- `IP = b64("10.20.30.40")` = `MTAuMjAuMzAuNDA=` (TB-3.26).

### 10.1 TG (tests/test_p1c_gaps.py, created in Phase 0)
Rows still open are STRICT XFAILS until the phase that closes them (review round 4 readiness Major 9): the module holds
`OPEN_ROWS: dict[str, str]` mapping each of the 76 ids of 13.1 to `"G4a"` (57 base64 ids) or `"G4c"` (19 host ids), and marks a
param `pytest.mark.xfail(strict=True, reason=f"closed by {phase}")` when its id is in `OPEN_ROWS`. Phase 3 deletes the 57 G4a keys,
Phase 4 the 19 G4c keys, Phase 5 deletes `OPEN_ROWS` itself. Every commit of the branch is then green under CI; FAIL-BEFORE runs with
`--runxfail` (13.1).
- I1 `test_base64_row[b64-1b-NNN|b64-1c-NN]` (the 52 leak rows): `leak_of(protected, out)[0] == "no"` and `"<ENCODED_" in out`,
  through `redact_text(t, {})` and `redact_untrusted(t, {})`.
- I2 the same id for the 85 unchanged rows: `digest(out, mapping) == BASE["rows"][f"{id}/text"]` (and `/untrusted`), the digest of 11.
- I3 the same id for the 5 kind-change rows: the output is exactly `<ENCODED_1>` and no key of the map has kind HIGHENTROPY.
- I4 `test_must_keep_b64[NN]` (the 17 `MUST_KEEP_B64` rows of 11) and `test_must_keep_corpus[masked-NN|kept-NN]` (60 rows: every text
  of `privacy_corpus.MASKED` (48, in dict order, values flattened) and `privacy_corpus.KEPT` (14) of tests/warden_port/privacy_corpus.py,
  minus the two HOSTNAME rows at lines 36 and 37 (`db at ...:5432` and `smb://.../share`, carved out to I12b)): digest equal, both
  functions. 77 ids. Ids number the rows in that order, 1-based, before the two rows are removed (so two numbers are missing).
- I9 `test_idempotent[<id>]` over the 229: `out = redact_text(t, m)`; `redact_text(out, m) == out` and the map did not grow.
- I10 `test_parity` (written out, review round 4 readiness Major 4): for each of the 142 base64 rows,
  `leak_of(p, redact_text(t, {}))[0] == "no"` if and only if `leak_of(p, redact_untrusted(t, {}))[0] == "no"`; for each of the 44 host
  and 43 number rows, `redact_text(t, {}) == redact_untrusted(t, {})` (MEASURED: 87 of 87 equal at the base and on the prototype).
- I11 `test_host_must_keep[...]`: `HOST_MUST_KEEP` (11): the 16 must-keep rows of 5.3, the 10 kept rows of 5.3, the sweep row
  `host ec2 failed; see ec2.internal, k8s.io, s3://b and x86_64 builds`, and `x.svc.cluster.local`, `x.svc.cluster.local.foo`,
  `eu-west-1.compute.internal`, `jdk.internal.reflect.Method`, `threading.local()`: digest equal, both functions (32 ids).
- I12 `test_host_row[host-NN]`: the 19 closed rows: `p1c_cases.host_kept_labels(name, text, redact_text(t, {})) == []`; the other 25
  rows: digest equal. `host_kept_labels` is copied from the probe's `gap2()` (11).
- I18 `test_number_row[num-NN]` (written out): `p1c_cases.number_class(number, redact_text(t, {})) == NUMBER_CLASS[i]`, where
  `NUMBER_CLASS` is the literal tuple of 43 classes of section 6 (`"not"` for rows 1-7, 9-12, 14-20, 30, 35, 38-40, 43; `"part"` for
  29, 32; `"whole"` for the rest). `number_class` is copied from the probe's `gap3()` (11).
- I25 `test_inputs_are_the_probe_inputs`: `sha256("\x00".join(inputs))` equals
  `630d55c4c5fb1cbb8d37cff627a73e64063b071decbe3c4bccf0438c87ebe213`, inputs in `build()` order (142 base64, 44 host, 43 number).
  Computed by v4 from the probe's own run order; NOT RE-COMPUTED at e8ff6de2b (tests/p1c_builders.py changed only in a docstring and
  two lambdas turned into functions with the same bodies; the probe prints the same rows). Phase 0 (c) is the parity proof: there is
  no other test that pins the three p1c groups against the probe (G7 r5 deleted it).

### 10.2 TB, Phase 2 part (tests/test_b64_scan.py, created in Phase 2; G4b only)
| id | name | input recipe | exact expected |
|---|---|---|---|
| TB-2.1 | `test_encoded_kind_is_a_secret_label_never_stored` | - | `"ENCODED" in redact_mod._LABELS`; `in redact_mod.SECRET_KINDS`; `not in defaults.STORED_KINDS`; `not in runmap._GRAMMAR`; `redact_mod._sweep("<ENCODED_1>", "abcd") is redact_mod._EVERY_COPY` |
| TB-2.2 | `test_encoded_kind_after_a_key` (REWRITTEN for E9) | `redact_mod.redact(t)` for `t` in `password=<ENCODED_1>`, `password=‹ENCODED_1›`, `password=<ENC` | `("password=<ENCODED_1>", {})`; `("password=<SECRET_1>", {"<SECRET_1>": "‹ENCODED_1›"})`; `("password=<SECRET_1>", {"<SECRET_1>": "<ENC"})` (MEASURED on the prototype; each the same as the EMAIL analogue `‹EMAIL_1›` / `<EMA`) |
| TB-2.3 | `test_place_encoded_numbering` (I7) | `m={"<ENCODED_5>": "a"*12}`, runs `["b"*12]`; `m={"<ENCODED_5>": "a"*12, "<ENCODED_2>": "c"*12}`, runs `["b"*12]`; `{}`, runs `["a"*12, "b"*12]` | `["<ENCODED_6>"]`; `["<ENCODED_7>"]`; `["<ENCODED_1>", "<ENCODED_2>"]`; each map grows by exactly the new runs |
| TB-2.4 | `test_place_encoded_numbering_is_the_redactor_counter` | the three maps above | the number used == `redact_mod._Redactor(dict(m_before)).counters["ENCODED"] + 1` |
| TB-2.5 | `test_place_encoded_identifier_original_gets_a_new_entry` | `m={"<TENANT_1>": X}`, runs `[X]` | `["<ENCODED_1>"]`; `m == {"<TENANT_1>": X, "<ENCODED_1>": X}` |
| TB-2.6 | `test_place_encoded_reuses_an_encoded_original` | `m={"<ENCODED_3>": X}`, runs `[X]` | `["<ENCODED_3>"]`; `len(m) == 1` |
| TB-2.7 | `test_tie_break_same_original_secret_rule_first` (I7b) | `redact_mod.redact("pre"+X+"post and "+X+" alone", mapping={"<TENANT_1>": X, "<ENCODED_1>": X}).text` | `pre<ENCODED_1>post and <ENCODED_1> alone` (MEASURED; base with SECRET standing in: `preQUJDREVGR0hJpost and <TENANT_1> alone`) |
| TB-2.8 | `test_tie_break_keeps_the_order_of_different_originals` | `runmap.enforce_map("x ab-cd-ef y", m)` for the 4 maps of 4 point 5; CHANGED in v6 (N1): plus the fifth map of 4 point 5 through `runmap._Redactor(m, None).sweep("x ab-cd-ef y")` and through `enforce_map` | the 4 outputs of that table, in order (MEASURED, base = prototype); the fifth map: `x <SECRET_1>-ef y` both ways (BY READING; base of the redactor's own sweep `x ab-<TENANT_1> y`, so that row is FAIL-BEFORE) |
| TB-2.9 | `test_encoded_is_never_restored_or_stored` (I6) | `m={"<ENCODED_1>": SB}` | `runmap.restore_text("x <ENCODED_1>", m) == "x <ENCODED_1>"`; the same with `kinds=frozenset({"ENCODED"})`; `runmap.storable(m) == {}`; `runmap.storable(m, frozenset({"ENCODED"})) == {}` |
| TB-2.10 | `test_assignment_kinds_hold_encoded` | - | `"ENCODED" in channel._ASSIGNMENT_KINDS` |

### 10.3 TB, Phase 3 part (appended to tests/test_b64_scan.py in Phase 3)
Every assertion of a TB or TG test carries a message that starts with its id (`assert out == want, "TB-3.13 percent padding"`):
the mutants of 13.3 use the id as their `expect` text.
| id | name | input recipe | exact expected |
|---|---|---|---|
| TB-3.1 | `test_b64_text_rules` | `_b64_text` of: `b64("status ok here")`; `b64(bytes(range(256)))`; `"QUJD+REVG_R0hJ"`; `"QUJDREVGR0hJS"` (13); `b64("10.20.30.40".encode("utf-16-le"))`; `b64("10.20.30.40".encode("utf-16-be"))` = `ADEAMAAuADIAMAAuADMAMAAuADQAMA==`; `b64(b"\xff\xfe" + "ok".encode("utf-16-le"))`; `b64("unpadded!!")`.rstrip("=") | `"status ok here"`; None; None; None; `"10.20.30.40"`; `"10.20.30.40"`; `"ok"`; `"unpadded!!"` |
| TB-3.2 | `test_b64_units_wrapped_block_table` | the 8 rows of 3.1 point 3, with the strings given there | exactly the `(start, end)` of that table, `written == text[start:end]` (MEASURED on the prototype) |
| TB-3.3 | `test_b64_units_placeholders_are_never_runs` (I19) | `x <HIGHENTROPY_7> y`, `card <CREDITCARD_12> ok`, `<SECRET_REDACTED>`, `‹HIGHENTROPY_7›`, `<GCPRESOURCE_1>`, `<AZURERESOURCE_12>`, `"<SECRET_REDACTED> " * 20_000` | `_b64_units(t)[1] == []`; `redact_text` / `redact_untrusted` output and map equal to the build with `runmap._B64_RUN = re.compile(r"(?!)")` |
| TB-3.3b | `test_marker_shaped_blobs_are_blanked` (L-B6 pin) | `<cGFzc3dvcmQ_12>`, `<ABCDEFGHIJKLMNOP>`, `‹ABCDEFGHIJKLMNOP›`; control `"<" + SB + ">"` | `[]` for the three; `[SB]` for the control (MEASURED) |
| TB-3.4 | `test_no_run_no_extra_work` (I5) | `pw=ab%41 here`, `pw=ab%41 x A` (tests/test_redact_fold_budget.py budget_1b and budget_2 texts), 100,000 characters of prose, a 48-character HIGHENTROPY blob, the rows of TB-3.3 | `runmap.redact` calls (a counting wrapper on `runmap.redact`), `time.thread_time` reads (a counting wrapper on `runmap.time.thread_time`), text and map equal to the step-off build |
| TB-3.5 | `test_short_blob_alone_is_encoded` | `SB` | `<ENCODED_1>`; map `{"<SECRET_1>": S12, "<ENCODED_1>": SB}` (MEASURED; base: `SB` unchanged) |
| TB-3.6 | `test_decoded_secret_entry_kept_and_a_plain_copy_swept` (L8) | `SB + " and later " + S12 + " alone"` | `<ENCODED_1> and later <SECRET_1> alone` (MEASURED) |
| TB-3.7 | `test_four_levels_one_entry` (I8, I14) | `"x " + b64^4("status ok")` = `x V1hwT1UyRkhVa2xXYm5CS1VucHNlUT09` | `x <ENCODED_1>`; exactly one new map entry (MEASURED output; base: unchanged) |
| TB-3.8 | `test_three_levels_read` | `b64^3("pwd=Zq9xW4m")` = `WTBoa2ExQldjSGhQV0doWVRrY3dQUT09` | `<ENCODED_1>`; `leak_of("Zq9xW4m", out)[0] == "no"` (MEASURED: map SECRET `Zq9xW4m` + ENCODED; base: unchanged) |
| TB-3.9 | `test_utf16_be_short` | `ADEAMAAuADIAMAAuADMAMAAuADQAMA==` | `<ENCODED_1>`; map exactly `{"<ENCODED_1>": blob}`, no IPV4 key (IPV4 is a stored kind) (MEASURED) |
| TB-3.10 | `test_too_deep_inside_a_decoded_view_is_masked_unread` (L4) | `b64("%" + "25"*9 + "41")` = `JTI1MjUyNTI1MjUyNTI1MjUyNTQx` | `<ENCODED_1>`; no `TooDeep` raised (MEASURED; base: unchanged) |
| TB-3.11 | `test_tenant_held_blob_becomes_encoded` (L12) | `org_id=cHdkPUtwN3JUcTJX` (base64 of `pwd=Kp7rTq2W`) | `org_id=<ENCODED_1>`; map `{"<SECRET_1>": "Kp7rTq2W", "<ENCODED_1>": blob}`, no TENANT key (MEASURED; base: `org_id=<TENANT_1>`) |
| TB-3.12 | `test_blob_after_an_ansi_escape` | `"\x1b[1m" + SB + "\x1b[0m"` | `<ENCODED_1>` (MEASURED) |
| TB-3.13 | `test_percent_padding` (CHANGED, L21) | `"data=" + b64("password=Zq9xW4mT7pL")[:-1] + "%3D"` = `data=cGFzc3dvcmQ9WnE5eFc0bVQ3cEw%3D` | `data=<ENCODED_1>%3D`; map exactly `{"<SECRET_1>": "Zq9xW4mT7pL", "<ENCODED_1>": "cGFzc3dvcmQ9WnE5eFc0bVQ3cEw"}` (MEASURED; with an exact held compare: `data=<ENCODED_2>` and two ENCODED entries) |
| TB-3.14 | `test_json_escaped_slashes` | `json.dumps({"data": b})` with `/` written `\/`, where `b` = the first base64 of `"pwd=" + 8 characters drawn from letters, digits, `?` and `~`` that holds a `/` (a seeded `random.Random(20261120)`, at most 100,000 draws). CHANGED: v4 drew letters and digits only, and the base64 of ASCII letters and digits NEVER holds `/` (63 needs six one-bits, which no such byte gives at any position): the v4 recipe loops for ever (MEASURED: the drafter's first run hung) | `{"data": "<ENCODED_1>"}` (MEASURED) |
| TB-3.15 | `test_known_value_seen_in_base64` | map `{"<SECRET_1>": S12}`, text `"x " + b64("note " + S12)` | `x <ENCODED_1>` (MEASURED) |
| TB-3.16 | `test_caps_fail_closed` (I13) | (a) `defaults.B64_MAX_UNITS` patched to 3, 4 distinct short blobs; (b) `defaults.B64_MAX_DECODED_CHARS` patched to 10, `SB`; (c) `runmap._b64_hits([runmap._B64Unit(0, 28, SB, SB, (SB,))], {}, runmap._ScanBudget(started=-1e9), 0)` with a spy on `runmap._b64_text`; (d) `B64_MAX_UNITS` patched to 1, `" ".join([SB] * 4)`; (e) `defaults.MAX_REDACT_CHARS` patched to 20 inside the call of `_b64_hits([unit of SB], {}, runmap._ScanBudget(time.thread_time()), 0)` | (a)-(c) each raise `InputTooLarge`; the caller's map is unchanged; (c) before any `_b64_text` call (spy count 0); (d) no raise, `<ENCODED_1> <ENCODED_1> <ENCODED_1> <ENCODED_1>` (MEASURED: the dedupe counts one unit); (e) `([True], {})` (the decoded join of 21 characters is over the patched cap: every unit a hit unread, no raise). All five MEASURED on the prototype |
| TB-3.17 | `test_separator_fallback` (I15, CHANGED input) | `_b64_hits(units, {}, runmap._ScanBudget(time.thread_time()), 0)` with `units = [runmap._B64Unit(0, 0, b, b, (b,)) for b in map(b64, P)]`, for `P = ['secret="', 'plain words" here', "x" * 12]` and the control `P = ['secret="', 'plain words here', "x" * 12]` | `[True, True, True]` (a closing quote in the next piece pulls the separator into the value: 2 pieces after); the control `[False, False, False]` (MEASURED both) |
| TB-3.18 | `test_separator_survives_every_neutralise` | pieces `["status ok", "hello world", "x"]` joined by `runmap._B64_SEP`, through `runmap.neutralise_untrusted` (the step's hook), None, and `channel._neutralise` (the card hook, kept so that a return to it stays safe) | 3 pieces each time (MEASURED) |
| TB-3.19 | `test_settle_chain_beside_a_blob` (I20 a, CHANGED expected, L20) | `CONSTRUCTED[0] + sep + SB` for sep in `" "`, `","`, `"\n"`, a fresh `RunMap` each | exactly `"password=<SECRET_2>\nBSB: <BANKCODE_1><SECRET_2>\npaid <BANKCODE_1>/<BANKACCT_1>" + sep + "<ENCODED_1>"`; `sorted(m) == ["<BANKACCT_1>", "<BANKCODE_1>", "<ENCODED_1>", "<SECRET_1>", "<SECRET_2>"]`; `m["<SECRET_1>"] == S12`; no `NotSettled` (MEASURED on the prototype, all three separators) |
| TB-3.20 | `test_wrapped_chain_settles_inside_the_view` (I20 b) | `"\n".join(textwrap.wrap(b64(CONSTRUCTED[0]), 64))` | `<ENCODED_1>` (MEASURED) |
| TB-3.21 | `test_fold_scan_runs_in_both_passes` (I20 c, d) | `"café " + SB`; `"Ꭺlice@example.com " + SB` | `café <ENCODED_1>`; `[line withheld: look-alike text hid a protected value] <EMAIL_1>` (MEASURED on the prototype; the second is the same at the base, v4) |
| TB-3.22 | `test_errors_of_the_second_pass_propagate` (I21) | a wrapper on `runmap.redact` raising `RedactionError("NotSettled")`, then `InputTooLarge("InputTooLarge")`, on call 2; text `SB` | `pytest.raises(RedactionError)` with `str(err.value) == "NotSettled"` (and an `InputTooLarge`); the caller's `RunMap` is equal to before |
| TB-3.23 | `test_views_are_of_the_input` (I22) | `redact_untrusted(SB + " password%3D" + S12)` | holds `<ENCODED_1>` and a `<SECRET_` and no `‹ENCODED` (MEASURED: `<ENCODED_1> password%3D<SECRET_1>`) |
| TB-3.24 | `test_card_two_benign_runs_and_one_secret` | `channel.clean(f"note {B1} then {B2} and {SB} end")` | exactly `f"note {B1} then {B2} and <ENCODED_1> end"` (MEASURED on the prototype; base: the input unchanged) |
| TB-3.25 | `test_card_cap_refusal_is_a_raise` | `B64_MAX_UNITS` patched to 1; `channel.clean(f"a {B1} b {B2}")`; `cards.render_abstain("r", "x", [f"{B1} {B2}"])` | both raise `InputTooLarge` (no `SETTLE_NOTE`) (MEASURED) |
| TB-3.26 | `test_card_tag_split_blob` (I24, CHANGED recipe) | `channel.clean(IP[:8] + "<i> </i>" + IP[8:])` with `IP = b64("10.20.30.40")` = `MTAuMjAuMzAuNDA=` | `<ENCODED_1>` (MEASURED; with ENCODED removed from `_ASSIGNMENT_KINDS`: `MTAuMjAu MzAuNDA=`, so the mutant is killed; base: `MTAuMjAu MzAuNDA=`) |
| TB-3.27 | `test_encoded_through_enforce_map_and_snapshot` | `W = "\n".join(textwrap.wrap(b64("2026-11-20 deploy db_password=" + S12 + " applied"), 32))`, `m = RunMap({"<ENCODED_1>": W})`; `t = "x " + W + " y"` | `enforce_map(t, m) == "x <ENCODED_1> y"`; `held_value_left("x <ENCODED_1> y", snapshot(m)) is False`; `held_value_left(t, snapshot(m)) is True` (MEASURED) |
| TB-3.28 | `test_map_ceiling` (I23) | `k5_cfg(tmp_path, config={"evidence": {"max_map_entries": 40}})`, `build_runtime`, `handle` (tests/k5_support.py); a document of 15 (then 25) distinct `b64("password=" + rand12)` | 15: not stopped, the map holds 30 entries (ENCODED + SECRET each); 25: `NEEDS_PERSON` / `document_too_complex` (BY READING) |
| TB-3.29 | `test_held_wrapped_original_is_not_decoded_again` | `t = W` (TB-3.27), `m = RunMap()`, `redact_text(t, m)` twice | the second call makes zero `_b64_text` calls (spy); same output (MEASURED: 1 call, then 0) |
| TB-3.30 | `test_perf_step_overhead` (I16, `@pytest.mark.perf`) | 13.4 | 13.4 |
| TB-3.31 | `test_card_url_credential_blob` (NEW, review B2) | `channel.clean(f"see {b64('http://u:' + PW + '@h.io')} now")` | `see <ENCODED_1> now` (MEASURED; base and v4's hook: the blob shown) |
| TB-3.32 | `test_card_curl_credential_blob` (NEW, review B2) | `channel.clean(f"see {b64('curl -u user:' + PW)} now")` | `see <ENCODED_1> now` (MEASURED; base: shown) |
| TB-3.33 | `test_spelled_work_through_a_decoded_blob` (NEW, review B4) | `t = "password=ab!" + SB + "\n" + " ".join([SB] * 3000)`; `m = RunMap({"<IPV4_1>": "10.0.0." + "1"})`; `monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", 1000)` | `pytest.raises(InputTooLarge, match="SpelledWorkTooMuch")`; `dict(m)` equal to before. Without the patch: no raise (MEASURED: refused in 0.36 s with the patch, 0.45 s to scan without) |
| TB-3.34 | `test_url_credential_blob_kept_entry` (NEW) | `redact_text(b64("http://u:" + PW + "@h.io"), m)` | `<ENCODED_1>`; `dict(m) == {"<URLCRED_1>": PW, "<ENCODED_1>": blob}` (MEASURED) |
| TB-3.35 | `test_decoded_text_is_neutralised` (NEW, pins L19's hook) | `redact_text(b64("password=<FOO_1>"), RunMap())` and `redact_untrusted` of it | `<ENCODED_1>` both (MEASURED: the escaped `‹FOO_1›` after a key is masked since E9; with no hook the older all-placeholder rule leaves it, no hit: BY READING) |
| TB-3.36 | `test_decoded_text_gets_its_views` (NEW) | `redact_text(b64("password%3D" + S12), m)` | `<ENCODED_1>`; `m["<SECRET_1>"] == S12` (MEASURED) |
| xfail strict | `test_limit_glued_prefix` (L-B1), `test_limit_split_fields` (L-B4), `test_limit_log_prefixed_lines` (L-B5) | `"/v1/blob/" + SB`; `json.dumps({"a": SB[:14], "b": SB[14:]})`; `"\n".join("2026-11-20 INFO " + w for w in textwrap.wrap(b64("2026-11-20 deploy db_password=" + S12 + " applied"), 16))` | each asserts `leak_of(S12, out)[0] == "no"`. MEASURED on the prototype, both functions: `YES (whole)`; `YES (part, 9 of 12 chars)` (the first half decodes to `password=Z`, becomes `<ENCODED_1>`, the second half stays); `YES (part, 6 of 12 chars)`. All FAIL, so strict xfails hold; an XPASS means the limit closed (report it) |
| xfail strict | `test_limit_base32_hex` (L-B2, CHANGED assertion) | `b = base64.b32encode(("password=" + S12).encode()).decode()`; `h = ("password=" + S12).encode().hex()` | asserts `b not in out and h not in out` for `out = redact_text(b + " " + h, {})`. MEASURED: both shown, the assertion fails. (v4 asserted `leak_of(...) == "no"`, which PASSES because `leak_of` does not decode base32 or hex: that row would XPASS and turn a phase red) |
| (no xfail) | L-B6 | - | pinned by TB-3.3b; no input found that a real secret would produce (3.1 point 2) |

### 10.4 TB, Phase 4 part (tests/test_host_names.py, created in Phase 4)
| id | name | input recipe | exact expected |
|---|---|---|---|
| TB-4.1 | `test_host_key_masks_db01` | the rows 33-36 of 5.3, plus `host web-1 down` | the 5.3 outputs; `host <HOSTNAME_1> down` |
| TB-4.2 | `test_host_key_keeps_tech_words` | the 10 kept rows of 5.3, `host s3 bucket`, `server db01 down` (the `server` key is not a host key) and `host db01.example ok` (a dotted value is not a host-key value) | each unchanged |
| TB-4.3 | `test_host_key_sweep_side_effect` | `host ec2 failed; see ec2.internal, k8s.io, s3://b and x86_64 builds`; `host db01 down; tail db01.log` | unchanged; `host <HOSTNAME_1> down; tail <HOSTNAME_1>.log` |
| TB-4.4 | `test_host_key_two_digit_words_are_masked` (stated) | `host py311 image`, `host sha256 sum` | `host <HOSTNAME_1> image`, `host <HOSTNAME_1> sum` |
| TB-4.5 | `test_host_suffix_hyphen_rest` | the 5 rows of 5.2 point 5 | each `<HOSTNAME_1>` |
| TB-4.6 | `test_host_start_after_a_bracket_or_a_lone_dot` | `(x<HOSTNAME_1>&.]db-7.corp.internalx`, `x/.db01.corp.example`, `..db01.corp` (with `RunMap({"<HOSTNAME_1>": "\0seed"})` for the first) | `db-7` not in the output; `x/.<HOSTNAME_1>`; `..<HOSTNAME_1>` |
| TB-4.7 | `test_host_whole_names` | `db01.corp.example`, `db01.corp.example.`, `com.acme.corp.billing.Service` (L-H1, a plain assert of the over-mask), `db_01.corp.example`, `db01[.]corp[.]example`, `x[.]svc[.]cluster[.]local`, `db01.corp.example.com_x` | `<HOSTNAME_1>`, `<HOSTNAME_1>.`, and `<HOSTNAME_1>` for each of the other five |
| TB-4.8 | `test_host_kept_names` | the 6 rows of 5.2 point 6 | each unchanged |
| TB-4.9 | `test_host_privacy_rows_new_strings` (I12b) | privacy_corpus.py rows at lines 36, 37 | `db at <HOSTNAME_1>:5432`, `smb://<HOSTNAME_1>/share` (both functions) |
| TB-4.10 | `test_host_patterns_are_linear` (`@pytest.mark.perf`) | each of `"a[.]"*12500`, `"a.-_"*12500`, `"a-"*25000+".corp"`, `"a."*25000`, `"ab-cd."*8000` | each HOSTNAME pattern's `findall` under 0.05 s |
| TB-4.11 | `test_host_label_class_is_ascii` (L11) | `"dial dbа" + "01.corp.example now"` (Cyrillic `а` in the first label) | the builder MEASURES the base output in Phase 4 and pins it; if the output equals the one with `_HOST_LABEL = r"[\w-]+"`, the Unicode-class mutant is declared equivalent (the fold scan masks the line first) in the evidence. UNMEASURED |
| xfail strict | `test_limit_host_single_trailing_digit` (L-H4) | `host web1 down` | asserts `"web1" not in out`; MEASURED by v4: `host web1 down` is unchanged after G4c, so the assertion fails: strict xfail (this replaces v4's garbled row; the Java package is TB-4.7) |

## 11. Files
Create:
- `tests/p1c_cases.py` (Phase 0).
  - It IMPORTS `RNG`, `SEED`, `reseed`, `rand`, `gap1_values`, `gap2_cases`, `gap3_cases` and `luhn_number` from tests/p1c_builders.py,
    which are not copied again.
  - It copies from handover/core-c/evidence/p1c_probe.py, bodies unchanged except where named, what tests/p1c_builders.py does not
    hold: `b64`, `ENCODINGS`, `wrap`, `no_digit_line`, the 1c case list, `lcs`, `_decodings`, `readable`, `leak_of`, the probe's
    `B64_RUN` and `PLACEHOLDER`, and two judges (review round 4 readiness Major 4):
    - `host_kept_labels(name: str, text: str, out: str) -> list[str]`: the body of the probe's `gap2()` loop between `residue = ...`
      and `kept = ...` (probe lines 354-359): placeholders replaced by a space, lower-cased, `.`, `%2e`, U+FF0E and `[.]`
      written `.`; the labels of `name` split on `.`, plus `db02` when `name == "db01.corp.example"` and `"db02" in text`; a label is
      kept when it occurs in the residue with no `[a-z0-9_\-ü]` on either side. Returns the kept labels in order, no duplicates.
    - `number_class(number: str, out: str) -> str`: the body of the probe's `gap3()` loop (probe lines 455-466): placeholders
      replaced by `|`; separators `[ .\-()]` (and `) `) between two digits removed; `left = lcs(number, squeezed)`; `"not"` when
      `left >= len(number)`, `"part"` when `left >= 4`, else `"whole"`.
    These draw from `p1c_builders.RNG`, the probe's stream.
  - `build() -> Cases` (`functools.cache`) calls `reseed()` and consumes the stream in the probe's order: gap1 values, the 1b rows,
    the 1c rows (both `no_digit_line` searches), gap2, gap3.
  - `Cases` holds `values` (8 dicts), `b64` (142 (id, protected, text)), `hosts` (44 (id, name, text)), `numbers` (43 (id, number,
    text)) and `plain` (16).
  - `MUST_KEEP_B64`, the 17 rows (written out, review round 4 readiness Major 3), each built in the file from parts, ids 01-17:
    01 `b64("this is just a status message")`; 02 `b64("ok status 200")`; 03 `b64(bytes(range(256)))`; 04 the 9-byte PNG header
    `b64(b"\x89PNG\r\n\x1a\n\x00")`; 05 a Kubernetes `data:` value: `"data:\n  config: " + b64("log_level: info\nretries: 3\n")`;
    06 a JWT with payload `{"sub":"demo","iat":0}` (header `{"alg":"HS256","typ":"JWT"}`, signature `b64url` of 32 made-up bytes,
    all url-safe base64 without padding, joined by `.`); 07 the same with payload `{"sub":"demo","email":"ops@" + "example.com"}`;
    08 a UUID with dashes and 09 one without (from `uuid.UUID(int=...)` of a fixed made-up integer); 10 a SHA-256 hex digest and 11 a
    SHA-1 hex digest (`hashlib` of `b"g4 must keep"`); 12 a 7-character git sha (the first 7 of row 11); 13 `internationalization`;
    14 `redact_text_body_for_views`; 15 `warden-dev-lab-tick-silent`; 16 `/usr/local/lib/python3/site-packages`; 17
    `getImplementationsForKind`.
  - `HOST_MUST_KEEP`: the 32 rows of I11 (5.3's 16 must-keep rows, its 10 kept rows, the sweep row, the 5 rows of 5.2 point 6).
  - Docstring rule: `build()` moves `p1c_builders.RNG`, so a caller of the gap builders calls `reseed()` first (the property test
    does, line 114). It is not imported from handover/.
  - Cost: NOT RE-MEASURED (v3 measured 1.6 s of CPU for `build()`; the whole probe, redaction included, takes 2.4 s wall at e8ff6de2b).
- `tests/test_p1c_gaps.py` (Phase 0): 10.1, public names only, `OPEN_ROWS` as in 10.1.
- `tests/fixtures/p1c_base_digests.json` and `tests/fixtures/make_p1c_base_digests.py` (Phase 0). Schema (written out):
  `{"base": "<base sha, 40 hex>", "python": "<x.y.z>", "rows": {"<key>": "<sha256 hex>", ...}}`. Keys: `<id>/text` and
  `<id>/untrusted`, one pair per input, where `<id>` is the TG test id inside the brackets: `b64-1b-001` .. `b64-1b-128`,
  `b64-1c-01` .. `b64-1c-14`, `host-01` .. `host-44`, `num-01` .. `num-43`, `mustkeep-b64-01` .. `-17`, `masked-NN` / `kept-NN`
  (the 62 privacy rows; the two host rows are written too, they are simply not read by I4), `hostkeep-NN` (the 32 of I11). The
  value is `sha256(json.dumps([out, sorted(mapping.items())], ensure_ascii=True).encode()).hexdigest()` where `out` is
  `redact_text(t, m)` or `redact_untrusted(t, m)` with a fresh `m = {}`. Digests, not outputs: no fake secret value is written.
  The script prints the JSON to stdout (`python tests/fixtures/make_p1c_base_digests.py > tests/fixtures/p1c_base_digests.json`,
  run in the base worktree); it is not collected by pytest.
- `tests/test_b64_scan.py` (Phase 2, extended in Phase 3): 10.2, 10.3.
- `tests/test_host_names.py` (Phase 4): 10.4.
- `tests/b64_mutants.py` (Phase 3; host mutants added in Phase 4): 13.3. Shape and CLI as tests/p1d_a_mutants.py:
  `sys.path.insert(0, <repo root>)`; `from tools.mutation_runner import Mutant, run_mutants`; an entry is
  `m(name, file, old, new, test_file, killer, expect)` returning `Mutant(name, file, old, new, expect, test_file=test_file,
  only_test=killer, pinned=test_file.removesuffix(".py") + "::" + killer)`; `M = [...]`; `__main__` calls `run_mutants(ROOT, M,
  ["tests/test_b64_scan.py", "tests/test_p1c_gaps.py", "tests/test_host_names.py"], extra_dirs=("tests/fixtures", "tools"),
  only=sys.argv[1:], on_result=print)` and exits 1 unless every result is good. `only` selects mutants whose name contains the
  text: every G4a/G4b mutant name starts with `b64 `, every G4c one with `host `, so `python tests/b64_mutants.py b64` and
  `python tests/b64_mutants.py host` select the two halves. Not collected by pytest. (Before Phase 4, tests/test_host_names.py does
  not exist: Phase 3 runs with that path dropped from the list, or the builder creates it empty in Phase 3; state which in the
  evidence.)
- `handover/core-c/evidence/G4-1.md` (Phase 0, appended in each phase): the raw evidence of 13.5.
- `handover/core-c/evidence/g4_snippets.py` (Phase 0): the snippet-count script of 13.3. Usage
  `python handover/core-c/evidence/g4_snippets.py <repo-root> [<tree-root>]`: imports `M` of tests/redact_mutants.py,
  p1d_a_mutants.py, gate_mutants.py, stage_mutants.py and textnorm_mutants.py, keeps the entries whose `file` is guard/runmap.py or
  guard/redact.py, prints `module, name, file, count of old in <tree-root>/<file>` per entry, a SUMMARY line, and the entries not
  found exactly once. (The drafter's scratch copy produced the counts of 13.3.)
- `handover/core-c/evidence/g4_share_sweep.py` (Phase 4): the printable-share sweep. For `share` in 0.85, 0.875, 0.90, 0.925, 0.95
  it sets `defaults.B64_PRINTABLE_SHARE`, clears nothing else, and prints for every probe row of `p1c_cases.build().b64`, every
  `MUST_KEEP_B64` row and every TB-3 input of 10.3 whether the verdict (`leak_of(...)[0]`, or for must-keep rows the digest against
  the fixture) differs from the 0.90 run. Expected: no row changes verdict. Run in-process, read-only.

Modify:
- `src/hadavin_sdk/guard/runmap.py`:
  - add `_ScanBudget`, `_B64Unit`, `_B64_RUN`, `_B64_TOKEN_SKIP`, `_B64_SEP`, `_b64_units`, `_b64_text`, `_b64_held`, `_b64_hits`,
    `_b64_place`, `_pass_one`, `_scan`; import `base64`, `binascii`, `dataclasses.dataclass`, `typing.NamedTuple`;
  - change `redact_text` (2.3), and add this paragraph to its docstring, after the paragraph on the cap (no host, no long run in it):
    "Base64 step (G4): every run of the base64 alphabet that pass one did not mask as a secret and that decodes to text is decoded;
    the decoded texts are scanned as ONE text by this same procedure (escaped with `neutralise_untrusted` whatever the caller's hook
    is, then views, decoded masks and nested base64 to `defaults.B64_MAX_DEPTH`), and a run whose decoded text held anything that
    scan masks is replaced whole by one `<ENCODED_n>` before pass one runs again. ENCODED is a secret kind, never stored or restored.
    At most `defaults.B64_MAX_UNITS` units and `defaults.B64_MAX_DECODED_CHARS` decoded characters per call, the deadline read before
    each unit; past either, `InputTooLarge`; the decoded texts are scanned joined by a line holding `;`, and a decoded value of a kind
    that is never stored stays in the run's map (its plain copies are masked)."
  - CHANGED in v6 (N1): the one clause of `enforce_map`'s docstring (runmap.py 732; text in 4 point 5);
  - import `place_encoded` and `strip_ansi` from redact (the import block, 25-38).
- `src/hadavin_sdk/guard/redact.py`:
  - `_LABELS`, `SECRET_KINDS`, `place_encoded` (module level, after `_replace_standalone`), the `_build` rules loop (4 point 5);
  - `_HOST_LABEL`, `_HOST_DOT`, `_HOST_BARE`, `_HOST_TAIL`, `_HOST_ARCH`, the HOSTNAME pattern and its comment, the HOSTKEY entry;
  - the module docstring (6). Examples go in `#` comments only: tests/test_no_hardcoded_values.py scans every string constant
    including docstrings (its `host` pattern takes `x.internal`, `x.corp`, `x.lan`; `long-secret-shape` any 32-character mixed run)
    and has no ALLOWED entry for redact.py or runmap.py; tests/test_lockin_guard.py (about 519-536) flags AWS region names and vendor
    hosts in string constants the same way.
- `src/hadavin_sdk/defaults.py`: section 7.
- `src/hadavin_sdk/approvals/channel.py`: `_ASSIGNMENT_KINDS`.
- `src/hadavin_sdk/approvals/gate.py`: the comment of 9.3 only.
- `tests/fixtures/p1d_cases.py`: the `after` cells of H27, L2 and L3 (Phase 4).
- `tests/p1d_a_mutants.py`: the killers of A4, A5, A38 and A6 (9.3 table; Phase 4).
- `tests/test_runmap_enforce_map.py`: the one line of `test_e5_...` (9.3; Phase 2, L24); CHANGED in v6 (N1): and the sentence added
  to `test_e5_...`'s docstring (4 point 5).
- `tests/gate_mutants.py`: R8 removed from `M`, with the comment of 9.3 (Phase 2, L24).
- CHANGED in v6 (review round 5 M1): `tests/test_gate_mutants_picked_up.py`: `MIN_MUTANTS = 105` -> `104` with the comment of 9.3
  (Phase 2, same commit as R8's removal; the reason: R8 is retired as equivalent, not lost).
- `tests/redact_mutants.py`:
  - R3's `old` AND `new` re-indented: `old = "            time.thread_time() - started > defaults.REDACT_BUDGET_S\n        ):  # a hostile text"`,
    `new = "            False\n        ):  # a hostile text"`. v4 MEASURED that `ruff format` (line-length 100) writes a loop at the top
    level of a function as `if (` / 12 spaces + condition / 8 spaces + `):  # a hostile text: ...`. The builder re-checks after
    `ruff format` with the snippet script (count 1).
  - Mutant 21's docstring sentence (line 5) becomes "removes both `_deadline=started + defaults.REDACT_BUDGET_S` arguments of
    `runmap._pass_one` (pass one and the pass on the replaced text, used for the input and every view)".
  - Nothing else: mutants appended after the base (Q9, in the tree since 4fb0b5154; CHANGED in v6: and G9's, when merged) are not
    touched.
- `tests/test_redact_idempotent_property.py`:
  - keep the groups `p1c-gap1/2/3` exactly as they are; nothing else pins them against the probe (G7 r5 deleted the parity test:
    Phase 0 (c), the I25 sha256, is the only parity proof);
  - add the group `p1c-b64` (142 texts of `p1c_cases.build().b64`) after `p1c-gap3`;
  - `EXPECTED_INPUTS = 1978` (1836 at the base + 142) and `P1C_B64 = 142` beside `P1C_GAP2`/`P1C_GAP3`, plus
    `assert counts["p1c-b64"] == P1C_B64` in `test_the_corpus_is_what_this_file_says`. If G8 or anyone changed `EXPECTED_INPUTS`
    after the base, it is that number + 142 (Phase 0 (f) reads it);
  - rebase onto G8's oracle edit (0.3; CHANGED in v6: line 141).
- `tests/g8_cases.py` (only when G8 is merged): `G4C_MERGED = True`, and `after_g4c` cells per 0.3 (Phase 4).
- `CHANGELOG.md` and `SECURITY.md`: the text of the "For SECURITY wording" section (Phase 5).

Must stay green UNCHANGED (run, do not edit; a red one is a finding: report it):
- tests/warden_port (test_redaction.py OWN_SHAPES and `test_a_high_entropy_value_after_any_key_is_masked`, test_redaction_classes.py,
  test_redaction_bank.py, test_redaction_review*.py, test_providers.py)
- tests/test_redact_context_after_sweep.py, test_redact_own_output.py, test_redact_own_output_hardening.py, test_redact_settle_loop.py
- tests/test_redact_fold.py, test_redact_fold_budget.py (:78 counts `len(PATTERNS)`, which HOSTKEY grows by one; the CountedClock
  tests), test_redact_fold_seams.py, test_redact_fold_property.py, test_redact_marks.py, test_redact_g3_port.py (G8's version)
- tests/test_k5_round12_fuzz.py, test_k5_round8.py, test_k5_round9.py, test_k5_round9b.py, test_k5_round10.py, test_k5_round6.py,
  test_k5_round7.py, test_k5_round11.py, test_k5_round5.py
- tests/test_k5_fixes1.py, test_k5_fixes2.py, test_k5_fixes3.py, test_k5_fixes5.py, test_k5_fixes7.py, test_k5_fixes9.py
- tests/test_k5_layers.py, test_k5_classes.py, test_k5_producers.py, test_k5_perf.py (`-m perf`), test_k5_tools.py, test_k5_review.py
- tests/test_textnorm_order137.py, test_textnorm_meta.py, test_textnorm_fixbatch.py, test_textnorm_siblings.py
- tests/test_runmap_enforce_map.py (after its one-line edit), test_runmap_map_write.py, test_k1b_redaction.py,
  test_k1b_redaction_layers.py
- tests/test_text_parts_together.py, test_model_gate.py, test_p1d_a_paths.py, test_p1d_link_oracle.py, test_p1d_a_rows.py (after its
  fixture edit)
- tests/test_p7_store.py, test_p7_tick.py
- tests/test_redact_glued_rest.py (G8's, once merged)
- CHANGED in v6 (review round 5 N2): tests/test_g4_parity.py and test_s4_llm_guard.py (call `channel.clean` directly),
  test_s6_approvals.py, test_gate_install_callers.py and test_review_pr3_round2.py (reach it through `FakeChannel` / cards);
  in Phase 3 step 2 and Phase 4 step 2
- tests/test_no_hardcoded_values.py, test_lockin_guard.py, test_gate_mutants_picked_up.py (CHANGED in v6: after its
  `MIN_MUTANTS` edit), and the mutant runs of 13.3.
MEASURED on the prototype (G4a + G4b, no G4c) with `-n 3 -m "not perf"`: tests/test_redact_context_after_sweep.py,
test_redact_own_output.py, test_redact_own_output_hardening.py, test_runmap_map_write.py, test_k5_tools.py, test_redact_fold_budget.py,
test_k5_fixes7.py, test_k5_fixes9.py, test_k5_round11.py, test_k5_round5.py, test_runmap_enforce_map.py, test_k1b_redaction.py,
test_k1b_redaction_layers.py, test_redact_settle_loop.py, test_p1d_a_rows.py, test_text_parts_together.py and tests/warden_port:
3,268 passed, 3 skipped, 2 failed: `test_runmap_enforce_map.py::test_e5_...` (the tie-break, 9.3, L24) and
`test_k5_round11.py::test_the_gitleaks_header_chain_regex_...` (FileNotFoundError: `.gitleaks.toml` is not in the scratch archive,
which held only `src`, `tests` and `pyproject.toml`; not G4's).

Delete: nothing. Migration: none.

## 12. Build order (one commit per phase on the builder's branch; every commit green)
Prefix: `uv run --all-extras --group test`. CI runs `pytest -q -n 3 -m "not live and not perf"` (.github/workflows/ci.yml 98); the
box rule is `-n 3` at most, `uptime` first, one heavy process at a time; perf runs separately with `-p no:xdist`. `-k` is never used
across several files. "Green" = the listed command passes with exactly the listed ids failing; the FULL step of each phase is
`pytest -q -n 3 -m "not live and not perf"` and must show only the failures recorded at the base in Phase 0 (h) (a subset of them is
fine; any new failure is a STOP and report). Because `test_p1c_gaps.py` marks the open rows strict-xfail (10.1), the branch is green
at every commit and may be pushed and CI'd at any phase; it is MERGED only after Phase 5 and the result review.

Phase 0 (no src code):
- (a) Base sha; `uptime`; the 0.2 rule (a non-empty diff is normal: G8 merged first, Q9 mutants appended; follow step 2);
  `git worktree add --detach /tmp/g4-base <base-sha>`.
- (b) Run handover/core-c/evidence/p1c_probe.py in /tmp/g4-base (`cd /tmp/g4-base && uv run python handover/core-c/evidence/p1c_probe.py > /tmp/g4-base-probe.md`).
  Its totals and row lists must equal 1, 6, 9.1 and 9.2.
  - On a difference, UPDATE this ticket's tables and the 76-id list from the new run, record both in the evidence, and go on (a
    moved base, for example G8's PHONE/IPV4 changes, not a defect).
  - STOP only if a host or base64 row that G4 closes now leaks in a NEW way (a new kind of leak, not a count).
- (c) Write tests/p1c_cases.py; `build()`'s sha256 must equal I25's literal. If it differs: STOP (the copy is wrong, not the base).
- (d) Write tests/fixtures/make_p1c_base_digests.py; COPY it and tests/p1c_cases.py into /tmp/g4-base/tests/ (and
  /tmp/g4-base/tests/fixtures/), run it there, keep the JSON in the branch.
- (e) Write tests/test_p1c_gaps.py with `OPEN_ROWS`; copy it, p1c_cases.py and the JSON into /tmp/g4-base; FAIL-BEFORE (13.1).
- (f) Change tests/test_redact_idempotent_property.py (the `p1c-b64` group), copy it and p1c_cases.py into /tmp/g4-base and run it
  there: 1,978 inputs, 0 refused, 0 fail. Red: STOP (a property of the base, not G4's). NOT RE-MEASURED by the drafter.
- (g) Record at the base: `python tests/redact_mutants.py`, `python tests/gate_mutants.py`, `python tests/stage_mutants.py`,
  `python tests/p1d_a_mutants.py`, `python tests/textnorm_mutants.py runmap`, each verdict per mutant, and
  `python handover/core-c/evidence/g4_snippets.py . /tmp/g4-base`. At e8ff6de2b the snippet script MEASURED 116 mutants on
  runmap.py/redact.py (redact_mutants 58 redact.py + 7 runmap.py, p1d_a_mutants 18 + 1, gate_mutants 24, stage_mutants 3,
  textnorm_mutants 5), every `old` exactly once except mutant 21 (2, as intended) and N15 (0). `len(redact_mutants.M)` was 66 (63
  `m(` entries + 3 E9 `Mutant(` entries).
  CHANGED in v6 (review round 5 M2): at bff88a7a1 (Q9 in the tree) the count is 146 mutants on runmap.py/redact.py: redact_mutants
  88 redact.py + 7 runmap.py (`len(M)` = 96: 63 `m(` + 3 E9 + 30 Q9; one entry is on another file), p1d_a_mutants 18 + 1,
  gate_mutants 24 (of 105), stage_mutants 3, textnorm_mutants 5; every `old` exactly once except mutant 21 (2, as intended).
  N15 occurs ONCE (re-pointed by 4fb0b5154 to `_build`'s alias loop, redact.py 1958-1960): it is no longer `ERROR SNIPPET NOT
  FOUND`, and L18 is closed. Counted by the v6 drafter by importing the five `M` lists and counting each `old` in its file (a
  scratch copy of the snippet script's logic); no mutant was run. The builder's Phase 0 (g) record on its base is the reference.
- (h) The full suite at the base: `pytest -q -n 3 -m "not live and not perf"`, recorded (its failures are the allowed set).
Commit: the four new test files, the digest JSON and script, the property-test change, evidence/G4-1.md and g4_snippets.py. On the
branch, the 76 ids of 13.1 are strict xfails. Run `pytest tests/test_p1c_gaps.py -q` on the branch: 76 xfailed, the rest pass.

Phase 1, defaults.py (SPINE commit): the 8 constants and the 2 comment sentences.
- `pytest tests/test_no_hardcoded_values.py tests/test_k5_review.py tests/test_lockin_guard.py -q`. Expected red: none.

Phase 2, G4b (redact.py `_LABELS`, `SECRET_KINDS`, `place_encoded`, the `_build` rules loop; channel.py `_ASSIGNMENT_KINDS`;
tests/test_runmap_enforce_map.py's one line; gate_mutants R8 (L24)). CHANGED in v6: also tests/test_gate_mutants_picked_up.py
`MIN_MUTANTS` 105 -> 104 (M1, 9.3), the runmap.py `enforce_map` docstring clause and test_e5's docstring sentence (N1, 4 point 5).
Create tests/test_b64_scan.py with TB-2.1 .. TB-2.10.
1. `pytest tests/test_b64_scan.py -q`. Expected red: none.
2. `pytest tests/test_runmap_enforce_map.py tests/test_redact_context_after_sweep.py tests/test_redact_own_output.py tests/test_redact_own_output_hardening.py tests/test_k5_classes.py tests/test_redact_settle_loop.py tests/test_redact_idempotent_property.py tests/test_runmap_map_write.py tests/test_redact_fold_budget.py tests/warden_port tests/test_k5_tools.py tests/test_k5_round5.py tests/test_k5_round6.py tests/test_k5_round7.py tests/test_k5_round8.py tests/test_k5_round9.py tests/test_k5_round9b.py tests/test_k5_round10.py tests/test_k5_round11.py tests/test_k5_fixes1.py tests/test_k5_fixes2.py tests/test_k5_fixes3.py tests/test_k5_fixes5.py tests/test_textnorm_order137.py tests/test_textnorm_meta.py tests/test_textnorm_fixbatch.py tests/test_textnorm_siblings.py tests/test_p7_store.py tests/test_p7_tick.py tests/test_model_gate.py -q -n 3 -m "not perf"`.
   CHANGED in v6: plus `tests/test_gate_mutants_picked_up.py` (M1: green only with `MIN_MUTANTS = 104`).
   Expected red: none.
3. `python tests/redact_mutants.py`, `python tests/gate_mutants.py` (R8 gone; CHANGED in v6: 104 mutants), `python tests/stage_mutants.py`. Expected: the Phase 0
   (g) verdict for every mutant.
4. FULL: `pytest -q -n 3 -m "not live and not perf"`.

Phase 3, G4a (runmap.py refactor and step; R3 and mutant 21 text in redact_mutants.py; tests/b64_mutants.py with the `b64 ` mutants;
`OPEN_ROWS` loses its 57 G4a ids). Append TB-3.1 .. TB-3.36 and the strict xfails to tests/test_b64_scan.py.
1. `pytest tests/test_b64_scan.py tests/test_p1c_gaps.py -q -n 3 -m "not perf"`. Expected: no failure; exactly the 19 G4c ids xfail
   (`test_host_row[host-01]`, `[host-02]`, `[host-17]`, `[host-19]`, `[host-21]`, `[host-24]`, `[host-26]`, `[host-29]`, `[host-32]`,
   `[host-33]`, `[host-34]`, `[host-35]`, `[host-36]`, `[host-37]`, `[host-38]`, `[host-39]`, `[host-40]`, `[host-43]`, `[host-44]`);
   the 57 base64 ids pass.
2. `pytest tests/test_redact_fold_budget.py tests/test_redact_fold.py tests/test_redact_fold_seams.py tests/test_redact_fold_property.py tests/test_redact_marks.py tests/test_redact_g3_port.py tests/test_redact_idempotent_property.py tests/test_redact_settle_loop.py tests/test_redact_context_after_sweep.py tests/test_redact_own_output.py tests/test_redact_own_output_hardening.py tests/test_runmap_map_write.py tests/test_runmap_enforce_map.py tests/test_k5_fixes1.py tests/test_k5_fixes2.py tests/test_k5_fixes3.py tests/test_k5_fixes5.py tests/test_k5_fixes7.py tests/test_k5_fixes9.py tests/test_k5_layers.py tests/test_k5_classes.py tests/test_k5_round5.py tests/test_k5_round6.py tests/test_k5_round7.py tests/test_k5_round8.py tests/test_k5_round9.py tests/test_k5_round9b.py tests/test_k5_round10.py tests/test_k5_round11.py tests/test_k5_round12_fuzz.py tests/test_k5_tools.py tests/test_k1b_redaction.py tests/test_k1b_redaction_layers.py tests/test_k5_producers.py tests/test_text_parts_together.py tests/test_model_gate.py tests/test_p1d_a_rows.py tests/test_p1d_a_paths.py tests/test_p1d_link_oracle.py tests/test_gate_mutants_picked_up.py tests/test_textnorm_order137.py tests/test_textnorm_meta.py tests/test_textnorm_fixbatch.py tests/test_textnorm_siblings.py tests/test_p7_store.py tests/test_p7_tick.py tests/warden_port -q -n 3 -m "not perf"`,
   plus, when G8 is merged, `tests/test_redact_glued_rest.py` (a changed must-keep row: 0.3).
   CHANGED in v6 (review round 5 N2): plus `tests/test_g4_parity.py tests/test_s4_llm_guard.py tests/test_s6_approvals.py
   tests/test_gate_install_callers.py tests/test_review_pr3_round2.py` (they reach `channel.clean`, so the base64 step).
   Expected red: none.
3. `pytest tests/test_b64_scan.py -m perf -p no:xdist -q` (I16).
4. `python tests/redact_mutants.py` (CHANGED in v6: 96 mutants at bff88a7a1, `len(M)` by import; 66 at e8ff6de2b), `python tests/b64_mutants.py b64`,
   `python tests/textnorm_mutants.py runmap`, `python tests/gate_mutants.py`, and
   `python handover/core-c/evidence/g4_snippets.py .`. Expected: the Phase 0 (g) verdicts (R3 now found once again under its new
   text), every b64 mutant good, snippet counts equal to the base except R3's text.
5. FULL: `pytest -q -n 3 -m "not live and not perf"`.

Phase 4, G4c (the host patterns, p1d_cases.py, p1d_a_mutants.py, gate.py comment; tests/test_host_names.py; host mutants in
b64_mutants.py; `OPEN_ROWS` loses its 19 G4c ids; tests/g8_cases.py `G4C_MERGED = True` when G8 is merged, 0.3).
1. `pytest tests/test_host_names.py tests/test_p1c_gaps.py tests/test_b64_scan.py -q -n 3 -m "not perf"`. Expected red: none, no xfail
   left in test_p1c_gaps.py.
2. `pytest tests/warden_port tests/test_p1d_a_rows.py tests/test_p1d_a_paths.py tests/test_p1d_link_oracle.py tests/test_text_parts_together.py tests/test_model_gate.py tests/test_k1b_redaction.py tests/test_no_hardcoded_values.py tests/test_lockin_guard.py tests/test_redact_fold_budget.py tests/test_k5_tools.py tests/test_p7_store.py tests/test_p7_tick.py -q -n 3 -m "not perf"`,
   and, when G8 is merged, `tests/test_redact_glued_rest.py tests/test_redact_g3_port.py`.
   CHANGED in v6 (review round 5 N2): plus `tests/test_g4_parity.py tests/test_s4_llm_guard.py tests/test_s6_approvals.py
   tests/test_gate_install_callers.py tests/test_review_pr3_round2.py` (card and channel text: the host patterns reach them).
   The property cases of tests/test_p1d_a_rows.py (`test_no_link_outside_code_on_card`, `test_card_masks_what_model_masks`,
   `test_stored_card_round_trip`, lines 68-166) and of tests/test_p1d_a_paths.py are the guard of the final HOSTNAME start
   look-behind (5.2 point 1): A RED IN ANY OF THEM IS A STOP (review round 4 codebase B5): record the failing input, do not tune the
   pattern in the build; report to the lead with the input.
   Expected red: none.
3. `pytest tests/test_k5_perf.py tests/test_p1d_a_paths.py tests/test_host_names.py -m perf -p no:xdist -q`. Expected red: none.
   `test_secret_patterns_are_linear_on_a_50000_character_run` is the guard of 5.2 point 1.
4. `python tests/p1d_a_mutants.py` (every mutant good; A4, A5, A38 and A6 killed by the 9.3 killers), `python tests/b64_mutants.py host`,
   and `python handover/core-c/evidence/g4_share_sweep.py` (no row changes verdict).
   CHANGED in v6 (0.3 step 3; G8 v3 8.1 G4-2): when G8 is merged, also `python tests/g8_mutants.py`. Expected: `30 of 30 good`.
5. FULL: `pytest -q -n 3 -m "not live and not perf"`.

Phase 5, G4d and documents (the redact.py docstring paragraph and sentence, CHANGELOG.md, SECURITY.md; `OPEN_ROWS` deleted).
- FULL `pytest -q -n 3 -m "not live and not perf"`, `pytest -m perf -p no:xdist -q`, `pytest tests/test_k5_review.py -q`, ruff and
  bandit (13.5), the probe on the G4 head, and CHANGED in v6: when G8 is merged, `python tests/g8_mutants.py` (`30 of 30 good`;
  the run G8 v3 8.1 G4-2 asks of G4's phase 5). Then push; CI on the branch; merge after the result review.
- Green: all. The probe shows 0 base64 leaks, 7 host rows readable (6, 8, 9, 10, 15, 16, 42), and numbers 24 / 2 / 17 (or the
  classes Phase 0 (b) re-derived).

## 13. Tests and evidence
### 13.1 FAIL-BEFORE
`cp tests/p1c_cases.py tests/test_p1c_gaps.py /tmp/g4-base/tests/ && cp tests/fixtures/p1c_base_digests.json /tmp/g4-base/tests/fixtures/ && cd /tmp/g4-base && uv run --all-extras --group test pytest tests/test_p1c_gaps.py -q --runxfail`

tests/p1c_cases.py imports tests/p1c_builders.py, which is in the base. `--runxfail` runs the strict xfails as plain tests.

Expected: exactly these 76 failures. Every other id passes (I4, I9, I10, I11, I18, I25 included).
- 48 1b leaks: `test_base64_row[b64-1b-001]` .. `[b64-1b-005]`, `[b64-1b-007]`, `[b64-1b-008]`, `[b64-1b-033]` .. `[b64-1b-037]`,
  `[b64-1b-039]`, `[b64-1b-040]`, `[b64-1b-049]` .. `[b64-1b-053]`, `[b64-1b-056]`, `[b64-1b-065]` .. `[b64-1b-072]`,
  `[b64-1b-081]` .. `[b64-1b-088]`, `[b64-1b-097]` .. `[b64-1b-101]`, `[b64-1b-104]`, `[b64-1b-113]` .. `[b64-1b-117]`, `[b64-1b-120]`;
- 9 1c rows (4 leaks + 5 kind changes): `test_base64_row[b64-1c-01]`, `[02]`, `[03]`, `[05]`, `[06]`, `[07]`, `[09]`, `[10]`, `[11]`;
- 19 host rows: the ids of Phase 3 step 1.
Without `--runxfail` the same command gives 76 xfailed and no failure. Derived from the re-measured row lists (probe at e8ff6de2b);
the test itself is not written yet. `git worktree remove /tmp/g4-base` after Phase 0.

### 13.2 Parity
I25 is a literal in the test. Phase 0 (c) proves that the probe and the copy build the same inputs; nothing else does (no parity
test exists since G7 r5).

### 13.3 Mutants
Pins that already exist: every `old` text of tests/redact_mutants.py, p1d_a_mutants.py, gate_mutants.py, stage_mutants.py and
textnorm_mutants.py whose file is guard/runmap.py or guard/redact.py occurs after G4 as many times as at the base, except R3 (re-indented,
section 11) and gate R8 (removed, L24). MEASURED at e8ff6de2b by the snippet script: 116 such mutants (13.1 (g)), every `old` once
except mutant 21 (twice, as intended) and N15 (zero: stale at the base, L18). MEASURED on the prototype: the same, plus R3 at 0
(its old text not yet re-indented in the scratch code), as expected.
CHANGED in v6 (review round 5 M2): at bff88a7a1 there are 146 such mutants (Phase 0 (g): the 30 Q9 mutants are on redact.py),
every `old` once except mutant 21 (twice); N15 occurs ONCE (re-pointed; L18 closed). Counted by import, not by the runner. After
G4: 145 (R8 removed), with R3 once under its new text. G4 edits none of the 30 Q9 anchors (they are in `_char_class`, at
`    f = fold(ch)\n    flag = 0\n`).

Literals G4 must keep at their counts:
- `_deadline=started + defaults.REDACT_BUDGET_S` (twice, both in `_pass_one`);
- `started = time.thread_time()` (once);
- R2's line `if views and time.thread_time() - started > defaults.REDACT_BUDGET_S:` (once, in `_scan`);
- `for view in views:` (once);
- `    mapping.update(current)\n    return out\n` (once);
- `raise RedactionError("NotSettled")` in runmap.py (once, in `enforce_map`);
- textnorm mutant `runmap: the canonical view normalises every character`, old `        if piece.isascii():` (8 spaces): G4 must
  NOT write `if piece.isascii():` at 8 spaces anywhere in runmap.py (review round 4 codebase nit): name loop variables of the step
  `unit`, `line`, `body`, never `piece`, in an `isascii()` test. The snippet script checks it.

New mutants in tests/b64_mutants.py, each to be GOOD (KILLED with its `expect`), the raw result in the evidence. The builder writes
the code lines named in `old` VERBATIM (they are the anchors; 2.x and 3.x give them); if `ruff format` rewrites one, the builder
puts the formatted text in `old` and records it. `expect` is the TB/TG id the killer's assertion message starts with. File: RM =
src/hadavin_sdk/guard/runmap.py, RD = src/hadavin_sdk/guard/redact.py, CH = src/hadavin_sdk/approvals/channel.py. Killer file: B =
tests/test_b64_scan.py, G = tests/test_p1c_gaps.py, H = tests/test_host_names.py.
| name | file | old -> new | killer (file::test) | expect |
|---|---|---|---|---|
| `b64 skip the printable rule` | RM | `if s and sum(c.isprintable() or c in "\t\n\r" for c in s) >= defaults.B64_PRINTABLE_SHARE * len(s):` -> `if s:` | B::test_b64_text_rules (`bytes(range(256))`) | TB-3.1 |
| `b64 accept a mixed alphabet run` | RM | `    if std and url:\n        return None\n` -> `    if False:\n        return None\n` | B::test_b64_text_rules | TB-3.1 |
| `b64 drop the UTF-16 rules` | RM | `        if len(raw) % 2 == 0 and len(raw) >= 4:` -> `        if False:` | B::test_b64_text_rules | TB-3.1 |
| `b64 drop the depth limit` | RM | `        if depth >= defaults.B64_MAX_DEPTH:` -> `        if False:` | B::test_four_levels_one_entry | TB-3.7 |
| `b64 drop the unit cap` | RM | `self.units > defaults.B64_MAX_UNITS or ` -> `` | B::test_caps_fail_closed | TB-3.16 |
| `b64 drop the decoded-character cap` | RM | ` or self.decoded_chars > defaults.B64_MAX_DECODED_CHARS` -> `` | B::test_caps_fail_closed | TB-3.16 |
| `b64 no clock read per unit` | RM | `        budget.clock()\n` -> `` | B::test_caps_fail_closed (c) | TB-3.16 |
| `b64 clock read before the gate` | RM | `    stripped, units = _b64_units(text)\n` -> `    budget.clock()\n    stripped, units = _b64_units(text)\n` | B::test_no_run_no_extra_work | TB-3.4 |
| `b64 no placeholder blanking` | RM | `    if "<" in search or "‹" in search:` -> `    if False:` | B::test_b64_units_placeholders_are_never_runs | TB-3.3 |
| `b64 no ANSI strip` | RM | `    stripped = strip_ansi(text)` -> `    stripped = text` | B::test_blob_after_an_ansi_escape | TB-3.12 |
| `b64 no dedupe of identical units` | RM | `    distinct = list({u.written: u for u in units}.values())` -> `    distinct = units` | B::test_caps_fail_closed (d) | TB-3.16 |
| `b64 held by any kind` | RM | `if kind_of(placeholder) in SECRET_KINDS` (the `secret` set of 2.5 step 4) -> `if True` | B::test_tenant_held_blob_becomes_encoded | TB-3.11 |
| `b64 no whole-unit held test` | RM | `    if unit.written.rstrip("=") in secret:\n        return True\n` -> `    if False:\n        return True\n` | B::test_held_wrapped_original_is_not_decoded_again | TB-3.29 |
| `b64 held test compares the padding (L21 fallback)` | RM | `unit.written.rstrip("=") in secret` -> `unit.written in secret` | B::test_percent_padding | TB-3.13 |
| `b64 TooDeep in a decoded view propagates` | RM | `    except TooDeep:\n        return all_hit()` -> `    except ZeroDivisionError:\n        return all_hit()` | B::test_too_deep_inside_a_decoded_view_is_masked_unread | TB-3.10 |
| `b64 no size pre-check of the decoded join` | RM | `    if _expanded_len(joined) > defaults.MAX_REDACT_CHARS:` -> `    if False:` | B::test_caps_fail_closed (e) | TB-3.16 |
| `b64 no held rule` | RM | `    units = [u for u in units if not _b64_held(u, secret, parts)]` -> `    units = list(units)` | G::test_base64_row (I2) | I2 |
| `b64 no wrapped blocks` | RM | `                if len(taken) >= 2:` -> `                if False:` | B::test_b64_units_wrapped_block_table | TB-3.2 |
| `b64 no separator fallback` | RM | `    if len(after) != len(pieces):\n        return all_hit()` -> `    if False:\n        return all_hit()` (the hit loop is `for i, a, s in zip(idx, after, seen):`, so fewer pieces give fewer hits) | B::test_separator_fallback | TB-3.17 |
| `b64 separator of v3` | RM | `_B64_SEP = "\n\n;\n\n"` -> `_B64_SEP = "\n\x1e\n"` | B::test_separator_survives_every_neutralise (the `channel._neutralise` row; MEASURED: `\n\x1e\n` survives `neutralise_untrusted` but not the card hook) | TB-3.18 |
| `b64 decoded view not neutralised (L19)` | RM | `_scan(joined, dict(known), None, neutralise_untrusted, budget, depth + 1)` -> `_scan(joined, dict(known), None, None, budget, depth + 1)` | B::test_decoded_text_is_neutralised | TB-3.35 |
| `b64 decoded view gets no views` | RM | `    views = _views(text) if scan else []` -> `    views = _views(text) if scan and depth == 0 else []` | B::test_decoded_text_gets_its_views | TB-3.36 |
| `b64 kept entries of stored kinds too (L8 fallback b)` | RM | ` and kind_of(k) not in STORED_KINDS` -> `` | B::test_utf16_be_short | TB-3.9 |
| `b64 no kept entries (L8 fallback a)` | RM | `    return hits, kept` -> `    return hits, {}` | B::test_decoded_secret_entry_kept_and_a_plain_copy_swept | TB-3.6 |
| `b64 first pass's map kept` | RM | `    base = dict(mapping)` -> `    base = dict(first.mapping)` | G::test_base64_row (I3) | I3 |
| `b64 kept entries not renumbered (L20 fallback)` | RM | `        base[f"<{kind}_{counters[kind]}>"] = original` -> `        base[placeholder] = original` | B::test_settle_chain_beside_a_blob | TB-3.19 |
| `b64 ENCODED outside SECRET_KINDS` | RD | `        "ENCODED",\n    }\n)\n_COMMON` -> `    }\n)\n_COMMON` | B::test_encoded_kind_is_a_secret_label_never_stored | TB-2.1 |
| `b64 place_encoded own counter` | RD | `    n = _Redactor(dict(mapping)).counters["ENCODED"]` -> `    n = sum(1 for ph in mapping if _kind(ph) == "ENCODED")` | B::test_place_encoded_numbering | TB-2.3 |
| `b64 tie-break removed` | RD | `        or (_kind(placeholder) in SECRET_KINDS and _kind(self._rules[original][1]) not in SECRET_KINDS)` -> `        or False` | B::test_tie_break_same_original_secret_rule_first | TB-2.7 |
| `b64 tie-break as v3's sort key` | RD | `            key=lambda kv: -len(kv[1]),` -> `            key=lambda kv: (-len(kv[1]), _kind(kv[0]) not in SECRET_KINDS),` | B::test_tie_break_keeps_the_order_of_different_originals | TB-2.8 |
| `b64 ENCODED not in _ASSIGNMENT_KINDS` | CH | `"URLCRED", "ENCODED"}` -> `"URLCRED"}` | B::test_card_tag_split_blob (MEASURED killed with the new recipe) | TB-3.26 |
| `host drop the tail` | RD | `+ r")(?:-[A-Za-z0-9_-]*+)?(?![\w-])(?:" + _HOST_DOT + _HOST_LABEL + r")*)"` -> `+ r")(?:-[A-Za-z0-9_-]*+)?(?![\w-]))"` | G::test_host_row (rows 1, 2, 17) | I12 |
| `host underscore not a label character` | RD | `_HOST_LABEL = r"[A-Za-z0-9_-]+"` -> `_HOST_LABEL = r"[A-Za-z0-9-]+"` | G::test_host_row (row 32) | I12 |
| `host no bracket dot` | RD | `_HOST_DOT = r"(?:\.|\[\.\])"` -> `_HOST_DOT = r"(?:\.)"` | G::test_host_row (row 43) | I12 |
| `host no code guard for .internal/.local` | RD | `r"|(?![\w-])(?!" + _HOST_DOT + r"\w|\())"` -> `r"|(?![\w-]))"` | H::test_host_kept_names | TB-4.8 |
| `host .cluster.local not kept` | RD | `(?:\.cluster\.local|` -> `(?:\.never-kept|` | H::test_host_kept_names | TB-4.8 |
| `host v3 start look-behind` | RD | `r"(?i)(?<![\w-])(?<![\w-]\.)(?<![\w-]\[\.\])(?:"` -> `r"(?i)(?<![\w.\-\]])(?:"` | H::test_host_start_after_a_bracket_or_a_lone_dot | TB-4.6 |
| `host plain ASCII look-behind` | RD | the same old -> `r"(?i)(?<![A-Za-z0-9_-])(?:"` | H::test_host_patterns_are_linear (perf; the runner runs the named test whatever its mark) | TB-4.10 |
| `host suffix without the hyphen rest` | RD | `(?:-[A-Za-z0-9_-]*+)?(?![\w-])` -> `(?![\w-])` | H::test_host_suffix_hyphen_rest | TB-4.5 |
| `host Unicode label class` | RD | `_HOST_LABEL = r"[A-Za-z0-9_-]+"` -> `_HOST_LABEL = r"[\w-]+"` | H::test_host_label_class_is_ascii, or declared equivalent (TB-4.11) | TB-4.11 |
| `host key v3 value rule` | RD | `([A-Za-z][A-Za-z0-9_-]{0,60}(?:-[0-9]|[0-9]{2}))` -> `([A-Za-z][A-Za-z0-9_-]{0,60}[0-9][A-Za-z0-9_-]*)` | H::test_host_key_keeps_tech_words (`host ec2 failed`) | TB-4.2 |
| `host key no CPU names` | RD | `r"(?!" + _HOST_ARCH + r"(?![\w-]))"` -> `r""` | H::test_host_key_keeps_tech_words (`host x86_64`) | TB-4.2 |
| `host key server back` | RD | `(?:--)?host(?:name)?` -> `(?:--)?(?:host(?:name)?|server)` | H::test_host_key_keeps_tech_words (`server db01 down`) | TB-4.2 |
| `host key dotted values` | RD | `(?![\w\-/@])(?!\.\w)")` -> `(?![\w\-/@])")` | H::test_host_key_keeps_tech_words (row `host db01.example ok`, unchanged: with the guard removed `db01` is masked; BY READING) | TB-4.2 |
Dropped from v4's list, each with its reason (MEASURED or by reading):
- `drop the len % 4 == 1 rule`: EQUIVALENT, MEASURED: `base64.b64decode(body + "===", validate=True)` already raises "number of
  data characters (13) cannot be 1 more than a multiple of 4". The explicit check stays (it states the rule and saves a call).
- `views of T2 instead of T`: no one-line anchor (the views line is base code pinned by p1d A16); TB-3.23 pins the behaviour.
- `ENCODED in STORED_KINDS or given a grammar`: `storable` needs a `_GRAMMAR` entry too, so adding the kind alone changes nothing
  (by reading); TB-2.9 pins the behaviour.
- `place_encoded splits pieces; original = decoded text` and `mask only the found span`: not one-line edits of the code; TB-3.7,
  TB-3.27 and I1 pin them.

### 13.4 Perf mechanism (I16)
- In tests/test_b64_scan.py, marked `@pytest.mark.perf` and run serially. Clock and repetition: `tests/fixtures/timing.block_seconds`,
  best of `timing.REPEATS`.
- Baseline: the SAME build with `runmap._B64_RUN = re.compile(r"(?!)")`, measured interleaved.
- `PLAIN_RATIO = 1.15` (snake_case words and paths, 100,000 characters; MEASURED 1.058 / 1.066 on the prototype), `PROSE_RATIO = 1.10`
  (MEASURED 1.003 / 0.994), `PLANTED_RATIO = 1.15`, `FLOOR_S = 0.005`, and `CAP_CEILING_S = defaults.REDACT_BUDGET_S` for
  `B64_MAX_UNITS` distinct base64 secrets. The texts are built by the same generator as the drafter's `m_perf.py`: a seeded
  `random.Random(20261120)` choosing among the 23 words `get user by id request handler config value retry count max timeout session
  token cache lookup table index build deploy service worker queue`: half of the items snake_case words of 2-5 words, 30 percent
  paths `/a_b/c/...py` of 2-6 segments of 1-3 words, the rest single words, joined by a space, a newline or `, `, cut at 100,000.
- On a failure: the L22 fallback (pre-filter) is applied and the run repeated; a second failure is a STOP.

### 13.5 Evidence commands (raw output to handover/core-c/evidence/G4-1.md)
- ruff check and `ruff format --check` on the changed files;
- each phase's selections and FULL runs;
- the mutant runs and `python handover/core-c/evidence/g4_snippets.py .`;
- `uv run --group scan bandit -q -r src/hadavin_sdk/guard -ll`;
- the probe on the G4 head;
- `python handover/core-c/evidence/g4_share_sweep.py`.

## 14. Lead decisions (build default first, fallback if declined)
| id | question | build default | fallback |
|---|---|---|---|
| L1 | new kind name | ENCODED | SECRET (section 4 last paragraph) |
| L2 | host keys | `host`, `hostname`, `--host`, `--hostname` with `=`, `:` or space | `=` and `:` only: rows 33 and 36 become limits (17 closed) |
| L3 | rows 15, 16 and row 10 | stay unmasked, stated limits | add `svc` to `_HOST_BARE` |
| L4 | a fourth base64 level, `TooDeep` inside a decoded view | masked unread | `TooDeep` refuses the whole text |
| L5 | restore of underscore host names | not restorable | add `_` to `_GRAMMAR["HOSTNAME"]` |
| L6 | shortest run | 12 characters | 16 (row 83 a stated limit) |
| L7 | where the constants live | defaults.py, a SPINE commit | module constants in runmap.py |
| L8 | decoded finds | the ENCODED entries of the hit units, plus the decoded view's new entries of kinds NOT in `defaults.STORED_KINDS` (the secret kinds, and, CHANGED in v6, the kinds that are neither secret nor stored: UUID, BANKCODE, BANKACCT, SSN, AADHAAR, PAN; never stored, so nothing new is stored at rest); a bare plain copy of a decoded secret is masked (TB-3.6); inner ENCODED and identifier finds are thrown away | (a) only ENCODED entries kept; then "a bare plain copy elsewhere stays unmasked" is stated in SECURITY and TB-3.6 becomes a strict xfail; (b) every decoded entry kept (EMAIL/HOSTNAME/IPV4 then stored at rest) |
| L9 | unit cap | `B64_MAX_UNITS` = `MAX_MAP_ENTRIES`, refusal past it | 4,096, refusal past it |
| L10 | `_ASSIGNMENT_KINDS` | gains ENCODED (it matters for a tag-split blob of a stored-kind value, TB-3.26) | unchanged: a tag-split blob of an e-mail, host or address stays readable on a card |
| L11 | host label class | ASCII | Unicode `\w` |
| L12 | which pass-1 kinds hold a run | SECRET kinds and JWT/PRIVKEY substrings | any kind |
| L13 | host-key value | starts with a letter, ends in two digits or `-digit`, not a CPU architecture name (`_HOST_ARCH`); `web1` is a limit (L-H4), `py311`/`sha256` are masked and their later copies swept (stated) | v3's rule (any digit): `ec2`, `k8s`, `x86`, `http2`, `eth0`, `x86_64`, `Web2` masked and their later standalone copies swept, stated in SECURITY |
| L14 | a private suffix followed by `-rest` | masked whole, the hyphen rest and (for `.internal`/`.local`) the following labels inside the match | v3's `(?![\w-])`: not masked at all, stated |
| L15 | how the decoded texts are scanned | one joined scan with the separator `"\n\n;\n\n"`, every unit a hit when a separator is lost | one `_scan` per decoded text (v4 measured 6.4 s per 300 hitting pieces against a 1,000-entry map) |
| L16 | `_build` tie-break | for the same original only (rules loop) | v3's sort key `(-len, kind not in SECRET_KINDS)`: also reorders different equal-length originals; the `enforce_map` docstring sentence is then changed |
| L17 | a card whose text passes a base64 cap (or `SpelledWorkTooMuch`) | refused as today for any over-cap text: no card posted, the event recorded undelivered (8) | `cards._card` catches `RedactionError` and shows a fixed text (a change to approvals/cards.py) |
| L18 (CHANGED in v6: CLOSED) | redact_mutants N15's stale `old` text | no longer stale: 4fb0b5154 (Q9) re-pointed N15 to `_build`'s alias loop (`            if deadline is not None:\n                self._over_budget(deadline)\n            for key in _alias_keys(original):\n`, redact.py 1958-1960 at bff88a7a1, found once); G4 does not touch those lines and compares N15 with the base verdict like every other mutant | none needed |
| L19 (new, B2) | how a decoded text is neutralised before its scan | always `runmap.neutralise_untrusted` (markers and placeholder look-alikes only), whatever the caller's hook; MEASURED: closes the URL-credential blob on cards (TB-3.31) | the caller's hook (v4): a short blob of a URL credential is shown on a card (MEASURED); stated in SECURITY ("a credential inside a link, written in base64, is not found on an approval card") |
| L20 (new, readiness Major 5) | numbering of kept decoded entries | renumbered against the incoming map in `_pass_one` (2.5 step 6): no gaps; a value numbered before the blob is renumbered after the kept entries (TB-3.19 measured) | inner numbers kept (numbered against pass 1's map): numbering gaps in the map (accepted; TB-3.19 expects `<SECRET_3>` and keys without SECRET_1) |
| L21 (new, readiness Major 6) | held test and `=` padding | the whole-unit test ignores trailing `=` on both sides (TB-3.13 measured: one ENCODED entry, `%3D` kept) | exact compare: TB-3.13 expects `data=<ENCODED_2>` and two ENCODED entries |
| L22 (new, B6) | cost of the step on texts with many non-base64 runs | no pre-filter; `PLAIN_RATIO = 1.15` (MEASURED 1.06-1.07) | pre-filter: decode a unit only if its body holds an upper-case letter or a digit (MEASURED: drops all 2,599 snake_case units); stated limit for an all-lower-case blob |
| L23 (new, order) | order with G8 | G8 first (`G4C_MERGED = False`), then G4; the G4 builder flips the flag, checks rows 60-62/66, runs the two G8 test files, and owns the rebase of the property test and the redact.py docstring (0.3) | G4 first; G8 v3's builder sets `G4C_MERGED = True` from the start and owns both rebases |
| L24 (new, found by the prototype run) | the `_build` tie-break makes gate round 4's `_rules_conflict` reorder in `snapshot` redundant | keep the gate code (defence in depth); change the FAIL-BEFORE line of `test_e5_...` to the new redactor behaviour; remove gate mutant R8 (equivalent, MEASURED) with a comment, and (CHANGED in v6, M1) lower `MIN_MUTANTS` in tests/test_gate_mutants_picked_up.py from 105 to 104 with the reason | delete the redundant `_rules_conflict` branch of `snapshot` and R8 with it (a change to gate round 4's code; needs the gate owner's review) |
| L25 (CHANGED in v6, new: review round 5 M3) | order with G9 | either side (0.3b): no dependency; the second lander rebases by name and runs 0.3b's checks; ENCODED tokens are outside G9 v1's read-back unless the same redactor writes them | G9 first, G4 rebased onto it (the same checks, G4 owns them) |

## 15. Security notes, what stays out, rollback, reviewers, done
- No secret value is logged or put in an exception.
- The decoded text never leaves the redactor. Only `<ENCODED_n>` is written. Its original lives in the run map in memory, is never
  stored (TB-2.9), and is swept in every copy.
- Under L8, decoded values of kinds that are never stored stay in the map (memory only); decoded identifiers do not.
- The decoded text is scanned after `neutralise_untrusted` only (L19): it is never shown, so card sanitising (links, HTML, commands)
  would only hide what it holds.
- A hostile document can now turn a blob into a genuine `<ENCODED_n>` token, and with a compound value force a
  `SpelledWorkTooMuch` refusal of the whole text (fail closed; MEASURED, TB-3.33). Honest text cannot (2.6).
- Stays out: `redact()` / `redact_many` called directly; offsets other than 0; base32, hex, gzip; blobs glued to a prefix, split
  across fields or log prefixes; marker-shaped blobs (L-B6); `tools.py` and `k1b/redaction.py`; HIGHENTROPY in
  `_ASSIGNMENT_KINDS`; a refused card (L17).
- Rollback: tag `pre-G4` on the base commit. No migration.
- Reviewers: one correctness and one adversarial reviewer, fresh, given the diff, this ticket and evidence/G4-1.md only.
- Done:
  - every phase green, FULL suite included;
  - FAIL-BEFORE recorded (76 ids);
  - every mutant of 13.3 good (against the Phase 0 (g) record), R8 retired with its reason (CHANGED in v6: and `MIN_MUTANTS` 104);
  - CHANGED in v6: when G8 is merged, `python tests/g8_mutants.py` 30 of 30 good; when G9 is merged, 0.3b's checks done;
  - snippet counts equal;
  - the must-stay-green list green;
  - ruff, bandit, CodeQL, SonarCloud and CodeRabbit green;
  - the result review clean.

## For SECURITY wording and CHANGELOG (after the build, through the security wording review)
SECURITY.md, "Stated limits of redaction":
- Base64. A value written only in base64 is masked whole as ENCODED by the redactor's decoded view, when it is standard or URL-safe,
  padded or not, UTF-8 or UTF-16, wrapped at a fixed width, and up to three levels deep.
  - An ENCODED value is never stored or restored.
  - A secret found inside it is also masked where it is written plainly elsewhere in the same run.
  - Not found: a blob glued to other base64 characters, split across fields or across lines with a prefix; a blob written between
    `<` and `>` that looks like a marker (all capitals, or ending in `_` and digits); base32; hex.
  - A text with more than 2,000 distinct decodable base64 values is refused; a card with such a text is not posted. A document built
    to make the redactor's compound-value scan too long is refused as a whole.
- Host names.
  - A private host name (under `.corp`, `.lan`, `.intranet`, `.intra`, `.localdomain`, `home.arpa`, or ending in `.internal` /
    `.local`, also with a hyphenated rest such as `.corp-prod`) is masked whole.
  - A single host label after `host`/`hostname` that ends in two digits or in a hyphen and a digit is masked, and so is every later
    standalone copy of it in the run. That includes a non-host word of that shape (`py311`); CPU architecture names are not masked.
  - A label with one trailing digit (`web1`) is not masked.
  - A dotted name with no private suffix is not masked.
  - `.svc` short names, `.cluster.local` and AWS's own names are kept on purpose.
  - A Java package under a private suffix (`com.acme.corp.billing.Service`) is masked whole.

CHANGELOG.md, Unreleased, Upgrade steps: "**Redaction: base64 and host names (G4).** A value hidden in base64 is now masked as
`<ENCODED_n>` (a new kind, never stored or restored), and a secret found inside it is masked in its plain copies too. A private host
name is masked whole (`<HOSTNAME_1>` where `<HOSTNAME_1>.example` was shown), also with `_` in a label, `[.]` dots or a hyphenated
suffix. `host db01` / `hostname=db01` mask `db01`. Texts with more than 2,000 distinct base64 values are refused (`InputTooLarge`).
Cost: <the I16 numbers measured in Phase 3>."

## (A) Round 1 (tickets/G4-review-1.md): every finding, where it is resolved now
| finding | where now | state |
|---|---|---|
| g4r-B1 plug-in point; mapping into `out`; I1 false for held rows | 2.1-2.5, 3.3, 9.1, I1-I3 | resolved |
| g4r-B2 ENCODED creation, counters, `_PIECE`, reuse, label tests, I6 | 4, I6-I8 | resolved |
| g4r-B3 host-key grammar, position, group | 5.3, L2, L13 | resolved; tightened in v4 |
| g4r-B4 rows 10/15/16; keep mechanisms; tail; suffix list; grammar | 5.1-5.4, 9.2, I12, L3, L5 | resolved (19 closed) |
| g4r-M5 decode rules; neutralise; recursion; depth | 3.2, 3.4, L4, L19 | resolved; the decoded view's neutralise changed in v5 (L19) |
| g4r-M6 join rule; candidate cap; budget; placeholders; `redact_many` | 3.1, 3.4, 7, 8, 3.5 | resolved; separator replaced in v4 (L15) |
| g4r-M7 G7 order, sweep, property test, call counts | 0, 2.5, I5, I17, I20, I21 | resolved; re-based on G7 r6 in v5 |
| g4r-M8 build default and fallback; defaults commit | 14, 7 | resolved |
| g4r-M9 builders, per-row table, FAIL-BEFORE, files, must-keep, mutants, `is_masked`, parity | 9-13 | resolved; `is_masked` no longer exists (E9(3)); parity is Phase 0 (c) only |
| readiness nits | whole ticket | resolved |
| g4c-B1 label, `SECRET_KINDS`, public function, counter test; `STORED_KINDS` unchanged | 4, I6, I7 | resolved |
| g4c-B2 the 90 non-leaked rows; JWT split | 3.3, 9.1, I2-I4 | resolved (held rule; v5 measured the 85 unchanged rows on the prototype) |
| g4c-M1 21 of 24; second suffix list | 5.1, 9.2 | resolved |
| g4c-M2 host-key false positives, sweep and restore of words | 5.3, L13 | resolved; `server` dropped in v3 |
| g4c-M3 cost bound; clock per candidate; one view; caps; gate apart from `scan` | 3.4, 7, 8, 3.1 | resolved; v5 measured the cost (B6) |
| g4c-M4 `_clean`, `undo`, `fits_after_nfkc`, printable after decode, LE/BE | 3.2, 3.4 | resolved |
| g4c-M5 glued prefix, padding, row 83, `\/`, `%3D`, views, `Basic` | 3.1, 3.2, 3.3, 9.1, L6, L21 | resolved; `%3D` now one entry (L21) |
| g4c-M6 tail, Java guard, underscore, non-ASCII, `[.]`, `_KEPT_HOST` | 5.2, 5.4, I11 | resolved |
| g4c-M7 prerequisites; G7 pins | 0, 11, I17 | resolved |
| code nits | 6, 4, 9.1 | resolved |

## (B) RUNG TABLE and NEEDED-CHECK (CODE-LAST v1)
NEEDED-CHECK, read at e8ff6de2b: runmap.py `redact_text`, `_views`, `undo`, `_clean`, `fits_after_nfkc`, `_decoded_masks`,
`_keep_earlier_masks`, `_GRAMMAR`, `storable`, `restore_text`, `enforce_map`, `snapshot`, `_rules_conflict`, `neutralise_untrusted`;
redact.py PATTERNS (HOSTNAME), `_KEPT_HOST`, `_LABELS`, `_OWN_TOKEN`/`_OWN_OUTPUT` (E9), `strip_ansi`, `_Redactor.__init__`, `find`,
`_decide`, `_build`, `SECRET_KINDS`, `_sweep`, `redact_many`; defaults.py `MAX_MAP_ENTRIES`, `REDACT_BUDGET_S` and its comment,
`SPELLED_MAX_WORK` and its comment, `STORED_KINDS`; approvals/channel.py `clean`, `_TAGS`, `_ASSIGNMENT_KINDS`, `settled`,
`_neutralise`; approvals/gate.py `_CONTROL_CHARS`, `sanitise_text`, `_PLACEHOLDER_DOT`, `_outside_code`, `_per_part`,
`withhold_commands` (by its effect, measured); cards.py `_card`; agent_loop.py 420-432, 540-552, 610-675; tools.py `redact_layered`;
k1b/redaction.py `redact_bundle`; tests/p1c_builders.py; tests/test_redact_idempotent_property.py; the five mutant files.
Verdict: NEEDED for G4a and G4c; G4d is a docstring and a pin.
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| base64 decoded view | a secret only written in base64 is masked | 2 core: `_views` (no base64), `tools._b64_holds` (known handed-out values only, not on the `redact_text` path), `k1b._pair` (one Kubernetes value); 3 tools: none in-process; 4 library: stdlib `base64` (no new dependency); detect-secrets / gitleaks style scanners UNVERIFIED, not usable in-process on the redaction path | probe; prototype (v5) | decode tied to the redactor's patterns, map, views, caps and deadline | KEEP-CODE, small |
| kind ENCODED | a mask that says "decoded blob", never restorable | 2 core: SECRET exists | section 4 | the label only | KEEP-CODE (fallback SECRET, L1) |
| whole host name, host key | the full dotted name is masked | 2 core: HOSTNAME too narrow; 4 library: a public-suffix list, UNVERIFIED, needs an update path | probe; v4 in-process run | - | KEEP-CODE: a pattern change |
| bare numbers | written down | 2 core: decision order 64 item 4 | probe | - | CUT to a docstring and a pin |

## (C) WHAT WAS MEASURED, AND WHAT NOT (v5)
MEASURED by the v5 drafter (scratch archive of e8ff6de2b plus the prototype; scripts in the drafter's scratch: `patch_proto.py`,
`proto_step.py`, `m_card.py`, `m_tb.py`, `m_perf.py`, `g4_snippets.py`):
- the probe at the base (all totals and row lists equal v4's) and on the prototype (gap 1: 0 leaks; 85 rows print the same);
- B2: the card path, 8 decoded texts x base / v4 hook / v5 `neutralise_untrusted` (3.4 table);
- TB-2.2, TB-2.7, TB-2.8 (4 maps, base and prototype), TB-3.2 (8 rows), TB-3.3b, TB-3.5, TB-3.6, TB-3.7, TB-3.13 (both held
  rules), TB-3.16 (d), TB-3.17 (both inputs), TB-3.18 (3 hooks, and v3's separator), TB-3.19 (both numberings, 3 separators),
  TB-3.20, TB-3.24, TB-3.26 (old and new recipe, with and without the mutant), TB-3.31, TB-3.32, TB-3.33, TB-3.34, TB-3.35,
  TB-3.36, the four strict-xfail recipes of L-B1, L-B2, L-B4, L-B5, and the L-B6 search (3,000,000 tries, none);
- the `SpelledWorkTooMuch` route (2.6) and the held `.`-piece case;
- the step's cost on 100,000 characters of snake_case and of prose (8), and the pre-filter's effect;
- the snippet counts at the base and on the prototype (13.3), `len(redact_mutants.M) == 66`;
- gate mutant R8 with and without the tie-break (9.3), the `len % 4 == 1` equivalence;
- a 17-suite pytest selection on the prototype (11: 3,268 passed, 2 failed, both explained).
Also MEASURED on the prototype: TB-2.9, TB-3.8 to TB-3.12, TB-3.14 (after fixing its recipe), TB-3.15, TB-3.16 (a)-(e), TB-3.21,
TB-3.23, TB-3.25, TB-3.27, TB-3.29.
BY READING (not run): TB-3.1, TB-3.3, TB-3.4, TB-3.22, TB-3.28, every G4c value (v4 measured them in-process at cd8d375; redact.py's PATTERNS are unchanged
since), the TB-3.35 mutant's survival path, the dotted-value host-key mutant.
NOT RE-MEASURED, with the reason:
- the G4c patterns at e8ff6de2b (no PATTERNS change since cd8d375; Phase 0 (b) re-measures);
- the final HOSTNAME start look-behind through the suites (v4's load stop; Phase 4 step 2 is the guard and a STOP);
- the 837-text separator matrix with v5's single hook (v4 ran all three hooks);
- the I25 sha256 (p1c_builders changed in form only; Phase 0 (c));
- `build()`'s 1.6 s; Phase 0 (f), the property test with 1,978 inputs at the base;
- the A4/A5/A38/A6 killers by `tools/mutation_runner` (v4 measured them in-process; Phase 4 runs the runner);
- the planted and 2,000-secret perf texts on the prototype; perf on another machine;
- the b64 mutants by `tools/mutation_runner` (the prototype measured the killer outputs for 6 of them: TB-3.13, TB-3.18, TB-3.19,
  TB-3.26, TB-3.16 (d), R8);
- G8's rows under G4 (G8 is not merged; 0.3 makes it a builder step);
- whether k1b fixtures hold base64 that decodes (they would gain an `ENCODED` count, and possibly a SECRET count under L8).
FOUND by the v5 prototype run, inside G4 (neither reviewer listed them): test_e5's FAIL-BEFORE line goes red and gate R8 becomes
equivalent under the tie-break (9.3, L24); v4's TB-3.14 recipe never terminates (10.3); v4's L-B2 strict xfail would XPASS (10.3);
v4's TB-3.17 input gives no fallback (3.4); identical consecutive blob lines form one wrapped block (3.1 point 3).
FOUND (outside G4): redact_mutants `N15 the alias build asks for no budget` has an `old` text that occurs 0 times at e8ff6de2b
(L18). The scratch archive lacks `.gitleaks.toml`, so test_k5_round11's gitleaks test fails there only.
CHANGED in v6: READ (not measured) by the v6 drafter at bff88a7a1: the 0.1 redact.py/defaults.py lines; the mutant counts of
Phase 0 (g) and 13.3 (146; redact_mutants 96; gate 105; N15 once; by importing the lists and counting each `old`, no runner); the
kinds neither secret nor stored (L8); `MIN_MUTANTS = 105`; runmap.py 732 and test_e5's docstring; the five N2 suites reach
`channel.clean`; G8 v3's entry numbers, oracle line 141 and 8.1; G9 v1's edit list (0.3b). The fifth TB-2.8 map, the G9 /
ENCODED interplay and the `SpelledMemoryTooMuch` / G9 refusal routes are BY READING. v5's MEASURED items were measured on
e8ff6de2b and are not re-measured on bff88a7a1 (header).

## (D) Plan review round 2 (tickets/G4-review-2.md): every finding (carried; all TAKEN, three contested in part)
Readiness: B1 (p1d L2/L3 and JSON; JSON part CONTESTED: the JSON records base 2742c1b and is read only for `BS0` cells) -> 9.3;
B2 (refactor unspecified) -> 2.2-2.5; M1 (build order) -> 12; M2 (RNG; 1,835) -> 11 `build()`, property count (now 1,978); M3 (I4 79
vs two privacy rows) -> I4 = 77; M4 (MAX_MAP_ENTRIES enforced) -> 8, L9, I23; M5 (G7 interplay; NotSettled; rows 31/41) -> 2.5, 2.6,
I20, I21; M6 (views of T2) -> 2.4 step 3, I22; M7 (digest fixture, FAIL-BEFORE copy, sha256 and must-keep literals) -> 11, 13.1, I25;
M8 (`Server: AmazonS3`, `hostname: Web2`) -> 5.3, L2, L13; M9 (perf mechanism) -> 13.4; nits (mutation runner name, must-stay list,
sourced numbers, numbering, comment text, lazy `build()`, `-p no:randomly` dropped, estimates dropped) -> 13.3, 11, 7, 8, 4.
Codebase: B1 -> 9.3; B2 (L-B3, k1b counting) -> 3.5; B3 (map growth) -> 8, L8, L9, I23; M1 (I4 count) -> I4; M2 (recursion) -> 2.2-2.5;
M3 (mutant pins; count CONTESTED: 63 then, 66 now by `len(M)`) -> 13.3; M4 (placeholders as runs) -> 3.1 point 2, I19; M5 (pure
`build()`) -> 11; M6 (no-hardcoded / lockin) -> 11; M7 (caps; cap part CONTESTED: refusal kept) -> 2.6, 8, L4; M8
(`_ASSIGNMENT_KINDS`) -> 4 point 8, L10, I24; nits -> header, 7, 11, 3.4, 4, 3.1, 5.3, L8, I9; forgotten suites -> 11, 12.

## (E) Plan review round 3 (tickets/G4-review-3.md): every finding (carried; all TAKEN, one sub-claim contested)
Readiness: A (stale) -> re-based again in v5; B1 (step 5, stop rule) -> 2.3, 0.2; B2 (`\x1e`) -> 3.4, TB-3.18, TB-3.24; B3 (`-k`)
-> 12; B4 (TB names and outputs) -> 10; B5 (tests per phase) -> 11, 12; B6 (A6 STOP) -> 9.3; B7 (baselines) -> 8, 12 Phase 0 (b);
B8 (must-stay; `enforce_map`; property guard) -> 11, TB-3.27; N1 (sha256 recomputed; 1.6 s not re-measured); N2 (wrapped table)
-> 3.1, TB-3.2; N3 (mutant count by `len(M)`); N4 (`x86_64`, `eth0`) -> 5.3.
Codebase: B1 -> 2.3; M1 (cites) -> 0.1; M2 (HOSTKEY; `host s3 bucket` CONTESTED: `s3` is 2 characters) -> 5.3, L13; M3 (suffix
boundary) -> 5.2, L14; M4 (card SETTLE_NOTE) -> 8, L17, TB-3.25; M5 (L8 residual) -> L8, TB-3.6; M6 (suites) -> 11, 12; N1-N5 ->
4, 11, 2.5, 2.4, 7; design checks -> 4 point 5, TB-2.7, TB-2.8; red list -> 9.3; citations -> 0.1.

## (F) Plan review round 4 (tickets/G4-review-4.md): every finding
Readiness reviewer:
| id | state | where / reason |
|---|---|---|
| Round 3 claims verified | NOTED | the one mislabel ("kept entries of stored kinds too (L8 v3 fallback)") is now `L8 fallback b` (13.3) |
| G7 round 5 and Phase 0 | TAKEN | header (G7 r5 and r6 merged; E9 merged); 0.1 re-derived at e8ff6de2b; 0.2 step 1 says what to do with a non-empty diff |
| Major 1 stale anchors | TAKEN | 7 ("after `SPELLED_MAX_WORK`", defaults.py 112; both comment sentences with today's text, 59-60 and 83-87); `SPELLED_MAX_*` cite gone; parity-test and `moved_builders` references deleted (11, 13.2, I25); 0.2 step 1 |
| Major 2 G8 order | TAKEN | 0.3 and L23 (G8 first, flag handover, rows 60-62/66, the two G8 test files, rebase owner of the property test and the docstring, G4a vs K60/K66); 0.2 step 2: PHONE/IPV4/IBAN/UUID changes are table updates, never a STOP; G8 edits the module docstring too, G4's paragraph goes after it (6) |
| Major 3 not standalone | TAKEN | the 17 `MUST_KEEP_B64` rows (11), the digest schema and key format (11), the corpus path and the two excluded rows (I4), the docstring paragraph (11), sections A, B, D and E written out here; nothing needs v3 |
| Major 4 judges with no assertion | TAKEN | I10 written out (verdict parity on 142, output equality on 87, measured 87/87); `host_kept_labels` and `number_class` in the copy list (11) with their bodies; I12 and I18 assertions |
| Major 5 TB-3.19 | TAKEN (both halves) | kept entries renumbered against the incoming map (2.5 step 6, L20); TB-3.19's expected output is the exact measured string (`<SECRET_2>` for the chain); numbering gaps accepted in general and stated (2.5) |
| Major 6 TB-3.13 | TAKEN (first option) | held test ignores trailing `=` (3.3, L21), mutant `held test compares the padding`; TB-3.13 measured with both rules |
| Major 7 TB-2.8 | TAKEN | all 4 maps written (4 point 5 table), measured on base and prototype |
| Major 8 artifacts | TAKEN | 11 Create: evidence/G4-1.md, g4_snippets.py (written and run by the drafter), g4_share_sweep.py, `b64_mutants.py` CLI, entry format, name prefixes; 13.3 gives `old`/`new` per mutant |
| Major 9 phases green | TAKEN | FULL suite at the end of Phases 2-5; `OPEN_ROWS` strict xfails so every commit is green under CI (10.1, 12, 13.1 with `--runxfail`); Phase 2 adds test_redact_context_after_sweep, k5 rounds/fixes, fold budget; Phase 3 step 2 adds test_model_gate, test_p1d_a_*, test_p1d_link_oracle, test_k5_round12_fuzz, test_k5_fixes7/9, test_k5_classes, test_redact_own_output*, test_redact_fold_property |
| Nit strict xfails | TAKEN | 10.3: L-B1, L-B4, L-B5 measured (fail as required); L-B2 changed to a direct `not in` assertion (MEASURED: `leak_of` says "no" for base32/hex, the v4 row would XPASS); L-B4's value depends on `leak_of`'s threshold: measured value stated; L-B5 recipe given; L-B6 has no construction (3,000,000 tries) and is pinned by TB-3.3b, marked UNMEASURED as a leak |
| Nit line 762 garbled row | TAKEN | 10.4: one strict xfail (L-H4), the Java package is TB-4.7 |
| Nit 2.6 table | TAKEN | `SpelledWorkTooMuch` row and the redactor's own `InputTooLarge` inside a decoded view |
| Nit defaults "and, since G4" grammar | TAKEN | 7: two separate sentences, no list extended |
| Nit fixtures access | TAKEN | 10 (`tests.k5_support` imports, `CONSTRUCTED` imported inside the tests, `redact_mod` by importlib); TB-3.16 (c) names its unit; Phase 0 (d)/(e)/(f) copy the files into /tmp/g4-base explicitly |
| Nit 5.2 point 1 not run | TAKEN | stated risk in 5.2 point 1 and (C); Phase 4 STOP |
| Nit TB-3.2 symbolic | TAKEN | 3.1 point 3 gives the strings and the measured units |

Codebase-details reviewer:
| id | state | where / reason |
|---|---|---|
| B1 stale against S | TAKEN | header, 0, 0.1, 0.2, 7, 11, 13; patchers listed (0.1, 2.2: tests/test_k5_round5.py:278, test_k5_tools.py:317 and 339, test_redact_fold_budget.py:89 and 252, tests/fixtures/p1d_cases.py:261); test_k5_round11 described as the neutralise-hook test (line 74), not a patcher; Phase 0 (c) the only parity proof |
| B2 card path | TAKEN, one sub-claim CONTESTED | L19: the decoded view is always scanned after `neutralise_untrusted`; MEASURED (3.4 table): the URL-credential blob is shown under v4's hook and masked under v5's; TB-3.31, TB-3.32, TB-3.34, TB-3.35; TB-3.18 now checks `neutralise_untrusted`; TB-3.24 re-measured. CONTESTED: "`withhold_commands` hides `curl -u user:<pw>`": MEASURED, it does not (inline), so the curl blob was already masked under the hook; TB-3.32 is kept as a pin |
| B3 TB-3.26 | TAKEN, recipe CONTESTED in part | MEASURED: the reviewer's `SB[:14] + "<i> </i>" + SB[14:]` does NOT kill the mutant either: the first half decodes to `password=Z` (itself a hit), and the kept SECRET entry of the joined view is an assignment kind, so the joined path wins without ENCODED. The kept recipe uses a stored-kind blob, `IP[:8] + "<i> </i>" + IP[8:]`: `<ENCODED_1>`, mutant `MTAuMjAu MzAuNDA=` (killed, measured); 4 point 8 states when L10 matters |
| B4 SpelledWorkTooMuch | TAKEN | 2.6 row and note, 8, 15, TB-3.33 (MEASURED: refused with the patched limit, map unchanged); the reviewer's `password=<blob>.tail` route is held (measured) and the test uses `password=ab!<blob>` |
| B5 start look-behind not run | TAKEN | Phase 4 step 2 names the property cases; a red is a STOP |
| B6 perf | TAKEN | MEASURED (8): 1.058/1.066 on snake_case, 1.003/0.994 on prose; no pre-filter (L22, the measured pre-filter is the fallback); the `Plan <hex>` unit stated (3.1 point 8); the held set is built once per call (2.5 step 4) |
| Nit 3.4 point 9 / TB-3.17 | TAKEN | TB-3.17 re-measured: v4's input gives no fallback; new input with a closing quote |
| Nit 7 anchors | TAKEN | 7 |
| Nit 8 "defaults.py 37-40" | TAKEN | 8 cites the comment by name (52-87, 89-111) |
| Nit `_OPENINGS` `<ENC` | TAKEN, made moot by E9 | 4 point 1: `_OPENINGS` no longer exists; `password=<ENC` is masked (measured), as `<EMA` |
| Nit `_B64_TOKEN_SKIP` width | TAKEN | L-B6 widened (3.1 point 2), TB-3.3b |
| Nit textnorm `if piece.isascii():` | TAKEN | 13.3 literals list (no `piece` with `isascii()` at 8 spaces; the snippet script checks) |
| Review 1/2/3 resolutions verified | NOTED | carried (A, D, E) |
| Design attacks | NOTED | no change needed; the `_build` tie-break interplay with gate R8 found by the v5 prototype run (L24) |
| Tests red under the ticket | TAKEN | 9.3 table; plus a red neither reviewer listed: test_runmap_enforce_map.py::test_e5's FAIL-BEFORE line (measured, L24) and gate R8 equivalence; test_k5_fixes7/9 in Phase 3 step 2 (both green on the prototype) |
| Citations | TAKEN | 0.1 re-derived at e8ff6de2b |
| (drafter, not a review finding) | FIXED | v4's TB-3.14 recipe (letters and digits only) can never give a `/` in base64: the test would loop for ever; recipe changed and measured (10.3). v4's L-B2 xfail and TB-3.17 corrected (10.3) |

Coordinator heads-up (E9 merged, e8ff6de2b): TAKEN. TB-2.2 rewritten to the E9 behaviour (measured); every cite of `_KIND`,
`_OPENINGS` and "ENCODED in `_OWN_OUTPUT`" removed (header, 0.1, 2.4 step 3, 4 point 1).

Counts:
- Readiness: 9 Majors + 7 nits + the Phase 0 note: all TAKEN.
- Codebase: 1 Blocker + 5 Majors + 7 nits + the red list and citations: all TAKEN; two sub-claims CONTESTED with measurements
  (B2's `curl -u` case; B3's recipe, replaced by one that kills the mutant).
- New lead decisions: L19-L24.

## (G) Plan review round 5 (tickets/G4-review-5-codebase.md) and G8 v3 reconciliation: every finding (CHANGED in v6, new)
| id | state | where |
|---|---|---|
| M1 `MIN_MUTANTS` 105 goes red when R8 is retired | TAKEN | 9.3 R8 row, 11 Modify, 12 Phase 2 (header and step 2), L24, 15 Done, 0.1 |
| M2 the numbers describe the base, not the tree (Q9 in it) | TAKEN | header (Q9 and G7 r7 listed), 0.1 re-derived by name at bff88a7a1, 0.2, 12 Phase 0 (g) and Phase 3 step 4 (96 / 146), 13.3, L18 closed (N15 once), (C) |
| M3 G9 not reconciled | TAKEN | 0 (package line), 0.2 step 2, 0.3b (new), 2.6, 4 point 4, 7 (constant placement), 8, L25 |
| N1 tie-break moves the rule index | TAKEN | 4 point 5 (docstring clause of `enforce_map` and of test_e5; fifth map), TB-2.8, 11 Modify, 0 target files |
| N2 suites that reach `channel.clean` | TAKEN | 11 must-stay list, 12 Phase 3 step 2 and Phase 4 step 2 |
| N3 the b64 tie-break mutant's `old` is over 100 columns | NOTED | 13.3 already lets `ruff format` rewrite an `old`, recorded |
| L8 kinds neither secret nor stored | TAKEN | 3.4 point 10, L8 |
| G8 v3: PHONE entries 6-8 (not 5-7) | TAKEN | 6 |
| G8 v3: `python tests/g8_mutants.py` (30 of 30) | TAKEN | 0.3 step 3, 12 Phase 4 step 4 and Phase 5, 15 Done |
| G8 v3: oracle at line 141 (not about 121) | TAKEN | 0.3, 11 |
| G8 v3: docstring placement | TAKEN | 0.3, 6 (after the "(A re-scan inside redact() ...)" sentence, as G8 v3 4.3) |
Not settled by v6 (stated for the lead and round 6): G9 v2 does not exist yet; its read-back rule (written set or map keys) and
union kind decide whether a G9 union can make an ENCODED entry (0.3b); the fifth TB-2.8 map and the new refusal routes are
BY READING; v5's measurements are of e8ff6de2b, not bff88a7a1.
