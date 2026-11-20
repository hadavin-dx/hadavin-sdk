# Ticket E14: a memory cap on the redactor's finder build, and a run-level character cap on the map (BUILD TICKET, v1)

Owner: core-c (G7 lane). Closes: ESCALATIONS E14 (finder memory for large plain values) and G4 plan review round 8 design M2 (ENCODED
original memory has no per-run character bound; L26). Does NOT touch: the spelled-form registry and its limits (`SPELLED_MAX_CHARS`,
`SPELLED_MAX_WORK`; the E14 "20 x 20 grid = 8.68 units per character" point stays the lead's call, unchanged here), `MAX_MAP_ENTRIES`,
`REDACT_BUDGET_S`, the G4 base64 constants, G9's union/read-back limits.

Base read: cloud/core-c at a60da3394 (HEAD when measured), wip-g4 ebb134398 (G4 phases 0-3), wip-g9 26b7273cd (G9 built, not merged, E17).
Line numbers below are HEAD's (`redact.py` 2,402 lines, `agent_loop.py` 915, `config.py` 543, `defaults.py` 302).

Evidence labels used: MEASURED (a run on a scratch copy, script and raw output named), BY READING (code read, not run), NOT RUN.

## 1. The problem in one paragraph

`_Redactor._build` (redact.py 2006-2068) makes ONE trie of every rule original (`_trie(self._rules)`, 2038), then per group a second
trie (`_trie(group)`, 2050), the finder regex text (`_trie_regex`), the compiled regex and the prefix lists. Its transient memory is
about 0.46 KB per character of the map's rule originals, whatever the number of entries (MEASURED, 2.1), and nothing bounds the
characters: `MAX_MAP_ENTRIES` (2,000, defaults.py 24) bounds entries and is checked by the agent loop only AFTER the call that grew
the map (agent_loop.py 427 document, 547 tool result); `SPELLED_MAX_CHARS` bounds the written-form registry only; the redact
deadline (`REDACT_BUDGET_S`, CPU) is read in `_build`'s loops but not inside `_trie`, `_trie_regex` or `re.compile`, so a build
spends its memory before any deadline refuses. Every redactor built from a run's map pays it again: each `redact_text` call that
grows the map, each view that grows it, and the gate's `enforce_map` (`runmap._built`, 855, one build per changed map per chat call).

## 2. Measurements (tracemalloc OFF; `ru_maxrss` over a post-import baseline, one fresh process per row; thread CPU; box load ~2.5 on 4 CPUs)

Scripts and raw outputs: `/tmp/claude-0/-home-user/1ecfcb92-30a8-505b-a8c3-27491ed2aff6/scratchpad/e14t_work/` (scratch; phase 0
copies them to `handover/core-c/tickets/E14-files/`). Scratch trees there: `head/` (git archive HEAD), `g4/` (wip-g4), `g9/`
(wip-g9), `proto/` (HEAD + the prototype of section 4, diff `proto.diff`, 89 lines). Values are `password=<random [A-Za-z0-9]>`
(one SECRET each, no shared prefix beyond chance).

### 2.1 One build over N values of length L (`m_many.py build N L`: `_Redactor({...})._build()` alone) MEASURED, `build_grid.txt`

| N x L | characters | peak RSS over base | retained after | CPU |
|---|---|---|---|---|
| 1 x 262,144 / 4 x 65,536 / 16 x 16,384 / 128 x 2,048 | 262,144 | 113-114 MB | 10-20 MB | 0.64-0.73 s |
| 2 x 262,144 / 8 x 65,536 | 524,288 | 236-238 MB | 14-18 MB | 1.21-1.27 s |
| 4 x 262,144 / 16 x 65,536 | 1,048,576 | 479-480 MB | 21-28 MB | 2.79-2.97 s |
| 8 x 262,144 / 32 x 65,536 / 128 x 16,384 | 2,097,152 | 964-965 MB | 32-70 MB | 5.26-6.08 s |

Reading: peak = 0.46 KB per character, linear, INDEPENDENT of N (1 value of 262,144 costs what 128 of 2,048 cost); CPU about 2.6-2.9 us
per character per build. The memory is TRANSIENT (retained 10-70 MB: the compiled finders); a run pays the peak again at every build.
Where the peak sits (`m_parts.py`, one 262,144 value, separate processes): the first trie alone 41 MB, + regex text 43 MB, compile
after dropping the trie 44 MB; `_build` holds the first trie AND the group trie at once (2038 and 2050), hence ~114 MB (BY READING
for the attribution; the three step peaks are MEASURED).

### 2.2 E14's shape, 8 x 260,000 plain values (`m_many.py many|runmap 8 260000`) MEASURED, `many_runmap.txt`

| path | HEAD | prototype (section 4) |
|---|---|---|
| `redact_many` (one call, no deadline) | 960 MB peak, 9.17 s, accepted (E14's 956 MB traced: same) | REFUSED `InputTooLarge("FinderMemoryTooMuch")`, 145 MB peak, 3.97 s (the 8 `find`s) |
| one `RunMap`, `redact_untrusted` per string (the k1b bundle path) | 983 MB peak, 28.15 s, refused by the 6 s deadline at string 8 only AFTER the build | REFUSED `FinderMemoryTooMuch` at string 4, 369 MB peak, 5.23 s |
| `_build` of 3 x 262,144 = 786,432 (exactly the proposed cap) | (360 MB, 1.95-2.06 s on proto and g9) | accepted, 360 MB, 1.95 s |
| `_build` of 4 x 262,144 | 480 MB, 2.79 s | REFUSED, 139 MB peak, 0.46 s |

### 2.3 M2's evidence gap: one growing RunMap, 20+ calls each adding a 30-60 KB value (`m_seq.py`), plus an `enforce_map` after each call MEASURED

`seq_head_plain.txt` (HEAD, 40 calls, plain values): map 44,823 characters after call 1, 522,245 after 12, 1,033,103 after 23,
1,779,558 after 40; call CPU 0.13 s -> 1.29 s (12) -> 3.14 s (23) -> 5.21 s (40); the gate's `enforce_map` of a 25-character reply
0.07 s -> 1.31 s -> 3.29 s -> 5.19 s (it rebuilds on every changed map); peak RSS 14 MB -> 242 MB -> 488 MB -> 849 MB. Nothing refused
it: 40 calls (= `MAX_TOOL_CALLS_PER_RUN`) and 40 entries are far under `MAX_MAP_ENTRIES`; the total CPU of the sequence is ~210 s.
`seq_g4_b64.txt` (wip-g4, base64 runs of random bytes): the same curve (25 calls: 1,670,525 characters, 3.69 s a call, 542 MB).
Note: on G4 each blob is stored TWICE as HIGHENTROPY, with and without its last character (`m_g4dup.py`: 11 entries, 394k
characters, two per blob, e.g. 44,823 and 44,824); none is ENCODED for random bytes. The trie shares the common prefix, so the
characters-of-values sum over-counts the trie nodes by up to 2x for such pairs (BY READING of `_trie`; counted exactly by the
node count of section 4). `seq_g9_plain.txt` (wip-g9, 18 calls): the same as HEAD to within noise (call 13: 1.43 s, 273 MB).
`seq_proto_plain.txt` (prototype, no run-level check): calls 1-17 identical to HEAD, call 18 (800,067 characters) REFUSED
`FinderMemoryTooMuch` after 0.25 s; with the run-level check of section 4 (simulated: map characters over 524,288) the run ends
after call 13 (581,580 characters, peak 272 MB).

### 2.4 Honest sizes: the largest single build (characters of `_rules` keys) MEASURED, `honest_head.txt` (HEAD) = `honest_proto.txt` (prototype)

| shape | largest build | outcome HEAD / prototype |
|---|---|---|
| property corpus, 1,836 inputs, its own `check` (2 `redact_text` passes each; 2,933 builds) | 8,571 (round12-fuzz:202) | 1,836 ok / 1,836 ok, 0 refused |
| test_k5_round10 full-size run (1,500 IPs, then 40 x 5 arguments) | 14,392 (1,505 entries) | ok / ok |
| test_k5_perf `curl -u ` at the cap (the slowest shape test) | 262,144: ONE value, the whole text | ok / ok |
| test_k5_perf E2E units at the cap (`password= `, full-width, `p`) | 9 | ok / ok |
| test_k5_perf zero-width unit at the full cap (the test itself uses 64 KiB) | - | refused `TextTooLong` on BOTH (pre-existing, not this ticket) |
| one document of 2,000 HIGHENTROPY of 131 (G4 v8's row) | 252,505 (1,928 entries) | ok / ok |

Reading: an honest single CALL can hold one value as long as the text (262,144, `curl -u ` shape), so a PER-VALUE cap below
`MAX_REDACT_CHARS` would refuse an existing perf shape, and one at or above it bounds nothing the total cap does not (2.1: memory
depends on the total only). Headroom of the proposed run cap (524,288): 61x the corpus maximum, 36x the k5 full run, 2.0x the densest
single document (the `curl -u ` shape).

## 3. Decision (defaults, for the lead; section 10 restates it)

- D1 Two constants. `MAX_MAP_CHARS = 2 * MAX_REDACT_CHARS` (524,288): the run-level cap, `config.evidence.max_map_chars`, checked by the
  agent loop next to `max_map_entries`, ends `document_too_complex`. `MAX_FINDER_CHARS = MAX_MAP_CHARS + MAX_REDACT_CHARS` (786,432):
  the hard per-build cap, counted as trie NODES (characters not shared with an earlier rule's prefix) of the build's first trie,
  refuses EVERY redactor build past it (`redact`, `redact_many`, `redact_text`, the gate's `enforce_map`, k1b bundles). The margin of
  one `MAX_REDACT_CHARS` lets the call that crosses the run cap finish and the run end cleanly with `document_too_complex`;
  a call that adds more than that in one go (a 262,144 text whose views or folded aliases add another ~262,144) is refused by the build
  cap itself (still a refusal). Cost at the caps (MEASURED, 2.1): ~240 MB / ~1.25 s per build at the run cap, ~360 MB / ~2 s at the
  build cap, versus 965 MB / 5-6 s for E14's shape and no bound at all today.
- D2 NO per-value length cap (E14's first proposal): MEASURED (2.1, 2.4) it bounds no memory the total cap does not bound and, set
  below 262,144, it refuses the `curl -u ` perf shape and a 64-262 KB ENCODED or PEM blob. If the lead wants one anyway: it is a
  check in `_Redactor._place` (every registration) with its own message and the pins of section 7 grow by the curl shape.
- D3 Refusal: `InputTooLarge("FinderMemoryTooMuch")`, NOT a new subclass. Every caller already maps `InputTooLarge` (agent loop
  document path -> `document_too_large` 416-420; tool path -> `RedactionError` -> `redaction_error` 513-515; gate -> `CODE_MASK_BUDGET`
  model_gate.py 722; k1b bundle -> propagates, as its own bundle cap does, k1b/redaction.py 186). Same pattern as
  `SpelledMemoryTooMuch` / `SpelledWorkTooMuch`; no caller distinguishes the subclass today (BY READING).
- D4 The run-level count is `sum(map(len, set(rmap.values())))` (distinct originals: an identical original under two placeholders, as
  G4's tie-break allows, is one trie path). It over-counts shared prefixes (G4's two-per-blob pair counts 2x, 2.3): conservative;
  the exact bound is the build cap.

## 4. The change (prototype MEASURED on `proto/`, `proto.diff`; the builder writes it fresh on the rebased tree)

4.1 `defaults.py`, right after `MAX_BUNDLE_CHARS` (line 47; neither G4 nor G9 edits lines 40-55), with a comment block that cites
section 2 (the 0.46 KB per character rate, the four grid rows, E14's 960 MB -> refused, the honest maxima, why no per-value cap):
```python
MAX_MAP_CHARS = 2 * MAX_REDACT_CHARS  # 524,288: characters of distinct originals one run's map may hold (config evidence.max_map_chars)
MAX_FINDER_CHARS = MAX_MAP_CHARS + MAX_REDACT_CHARS  # 786,432: trie nodes one finder build may hold; past it InputTooLarge("FinderMemoryTooMuch")
```

4.2 `config.py` `EvidenceSettings`, next to `max_map_entries` (245), with a comment like the one above it:
```python
max_map_chars: int = Field(default=defaults.MAX_MAP_CHARS, gt=0, le=defaults.MAX_FINDER_CHARS)
```
`le`: a larger run cap is never reached (the build refuses first) and would turn the clean `document_too_complex` ending into a
`redaction_error` / `document_too_large`. Same shape as `max_document_bytes`' `le=defaults.MAX_REDACT_CHARS` (config.py 257-259).

4.3 `guard/redact.py`:
- `_trie(words, limit: int | None = None)`: with a limit, before inserting each word add `_new_nodes(root, w)` (the existing helper,
  redact.py 2150, the one `_spell` uses for `SPELLED_MAX_CHARS`) to a running count and raise `InputTooLarge("FinderMemoryTooMuch")`
  (local import from runmap, as at 1791) when the count is over the limit: the refused word is NOT inserted, the trie never holds
  more than `limit` nodes. No limit: unchanged (the group tries and `_split`'s bucket tries stay unlimited: each is a subset of the
  first trie's words, BY READING).
- `_Redactor._build`: the first trie becomes `trie = _trie(self._rules, limit=defaults.MAX_FINDER_CHARS)` (2038). It runs after
  `self._rules` is complete (alias keys included) and BEFORE the group tries, the regex and the compile, and before `_built_for`,
  `self._finders` and the cache are written: a refused build leaves the redactor unbuilt, the RunMap cache untouched, and
  `redact_text` never reaches `mapping.update(current)` (runmap.py 604), so the run's map is unchanged (BY READING; test E14-T4).
- Docstring/comment at `_build` (the MEMORY paragraph, like `_spelled`'s at 1199-1215) and in `sweep`'s comment block naming the new
  refusal. Cached reuse (`__init__` 1219-1221, `_built` 863) builds nothing and needs no check.

4.4 `runtime/agent_loop.py`, BOTH places, the SAME `if` (one refusal, one code):
- 427 (document): `if len(rmap) > self._evidence.max_map_entries or _map_chars(rmap) > self._evidence.max_map_chars:`
- 547 (tool result): the same condition, inside the existing `if`.
- a module-level helper `def _map_chars(rmap) -> int: return sum(map(len, set(rmap.values())))` (one pass over at most
  `max_map_entries` + one call's entries; negligible next to a redaction). Notes and reason codes unchanged (`document_too_complex`).

4.5 Out of scope, noted for later: `_build` holds the first trie and the group trie at once (2.1: ~40 percent of the peak); dropping
the first trie before the group loop when there is one group would lower the rate, not bound it. Not in this ticket.

## 5. Tests (new file `tests/test_redact_finder_cap.py`; every assertion message starts with its id and a space, `E14-Tn ...`)

Values below: `v(c, n)` = the character `c` followed by n-1 random `[A-Za-z0-9]` characters (fixed seed), so distinct first characters
mean no shared nodes. Small caps by `monkeypatch.setattr(defaults, "MAX_FINDER_CHARS", ...)` (the code reads `defaults.` at call time,
as `SPELLED_MAX_CHARS` is read, test_redact_settle_loop.py 1611).

| id | what | on HEAD (red-before) | after |
|---|---|---|---|
| E14-T1 | cap 1,000; `_Redactor({"<SECRET_1>": v("a",600), "<SECRET_2>": v("b",600)}).sweep("x")` raises `InputTooLarge` matching `FinderMemoryTooMuch` | RED (builds, no raise; also `MAX_FINDER_CHARS` missing) | green |
| E14-T2 | boundary at the constant: `v("a",500)`, `v("b",500)` = exactly 1,000 nodes: cap 1,000 builds and `sweep("q " + v_a + " q")` returns `q <SECRET_1> q`; cap 999 raises | RED (missing constant; 999 does not raise) | green |
| E14-T3 | nodes, not characters: P (500) + "x"*300 and P + "y"*300 = 1,100 nodes, 1,600 characters: cap 1,100 builds, 1,099 raises | RED | green |
| E14-T4 | refuse, never skip: a RunMap holding `v("a",600)` (built at the default cap); then cap 1,000 and `redact_untrusted("password=" + v("b",600) + " and " + v_a, m)` raises `FinderMemoryTooMuch`; `dict(m)` unchanged; `m.redact_cache` state unchanged; the same items through `redact_many` raise and the caller's dict is unchanged | RED | green |
| E14-T5 | the gate: `runmap.enforce_map("x " + v_a, m)` with a map over the (patched) cap raises `InputTooLarge` | RED | green |
| E14-T6 | agent run, document path, boundary: document of `10.1.1.1` .. `10.1.1.9` (9 values, 72 characters, MEASURED with `m_loop.py`): `max_map_chars` 72 -> `NO_ACTION`; 71 -> (`NEEDS_PERSON`, `document_too_complex`) and no audit event has `caught_by` (as test_k5_round10.py 141-147) | RED (config rejects the unknown key: `_Strict`) | green (MEASURED on proto: 72 NO_ACTION, 71 document_too_complex) |
| E14-T7 | agent run, tool path (agent_loop 547), as test_k5_round5.py 477-483: `k5_tools.RESULTS["app"]` = 9 addresses `10.2.2.1..9`, `ScriptLLM([{"tool": "app"}] * 2)`; the cap = the map characters after the document (computed in the test with the same redactor on the default document) + 71 -> `document_too_complex` with the tool note; the cap + 200 -> the run goes on (not `document_too_complex`) | RED | green (NOT RUN: builder) |
| E14-T8 | config: `EvidenceSettings(max_map_chars=0)` and `MAX_FINDER_CHARS + 1` rejected, `MAX_FINDER_CHARS` accepted, default equals `defaults.MAX_MAP_CHARS` | RED | green (MEASURED on proto) |
| E14-T9 | the derivation pin: `MAX_MAP_CHARS == 2 * MAX_REDACT_CHARS == 524_288`, `MAX_FINDER_CHARS == MAX_MAP_CHARS + MAX_REDACT_CHARS == 786_432` (a change of a default is a reviewed change) | RED | green |
| E14-T10 `perf` | E14's shape: `redact_many` of 8 x `"password=" + v(c, 260_000)` raises `FinderMemoryTooMuch`, thread CPU < 20 s (3.97 s MEASURED) | RED (accepted, 960 MB) | green |
| E14-T11 `perf` | at the real constant: `_Redactor` of three `v(c, 262_144)` (c = a, b, c: exactly 786,432 nodes) builds; adding one more character to one value raises | RED | green (1.95 s, 360 MB MEASURED) |
| E14-T12 | honest sizes stay far under: the k5_round10 full-size run's map (14,392 MEASURED) and the property corpus' worst build (8,571) are each under `MAX_MAP_CHARS // 30` (instrument `_build` like `m_honest.py`, or assert on `sum(map(len, set(m.values())))` for the k5 run only: cheap) | RED (constant missing) | green |

Green before AND after (no change for honest sizes; run them, do not edit them): tests/test_redact_idempotent_property.py (all 1,836
plus `test_no_input_of_the_corpora_is_refused`), tests/test_k5_perf.py (perf: `curl -u` at the cap holds ONE 262,144 value: under
both caps), tests/test_k5_round10.py (`test_the_cpu_of_a_full_size_run_stays_in_budget`, `test_a_document_with_too_many_distinct_values_is_refused_not_ground_through`),
tests/test_redact_settle_loop.py 1571-1650 (`SpelledMemoryTooMuch` keeps its pin: `redact_many` registers forms in `find`, before
the sweep's build, so the registry refuses first; BY READING, the builder confirms), tests/test_runmap_enforce_map.py (maps up to
`ENFORCE_MAX_ENTRIES` of short values: far under 786,432 nodes, BY READING), tests/test_redact_fold_budget.py (perf).

## 6. Mutants (new `tests/e14_mutants.py`, modelled on tests/g8_mutants.py; `expect` = the id and a space, at least 4 characters)

Each `old` is copied from the ruff-formatted file (G8 practice) and must occur exactly once (the runner replaces every occurrence).
Baseline file list: `tests/test_redact_finder_cap.py`, `tests/k5_support.py`, `tests/__init__.py`, `tests/conftest.py`; extra dirs
`tests/fixtures`, `tools`. Perf tests are not the killers.

| name | file | old -> new | killer | expect |
|---|---|---|---|---|
| E14-1 the first trie has no limit | redact.py | `_trie(self._rules, limit=defaults.MAX_FINDER_CHARS)` -> `_trie(self._rules)` | T1 | `E14-T1 ` |
| E14-2 the cap refuses at equality | redact.py | `if held > limit:` -> `if held >= limit:` | T2 (accept side) | `E14-T2 ` |
| E14-3 characters counted, not nodes | redact.py | `held += _new_nodes(root, w)` -> `held += len(w)` | T3 (accept side) | `E14-T3 ` |
| E14-4 the document check reads entries only | agent_loop.py | the 427 condition -> `if len(rmap) > self._evidence.max_map_entries:` | T6 | `E14-T6 ` |
| E14-5 the tool check reads entries only | agent_loop.py | the 547 condition -> the entries test alone | T7 | `E14-T7 ` |
| E14-6 the map is counted in entries | agent_loop.py | `return sum(map(len, set(rmap.values())))` -> `return len(rmap)` | T6 | `E14-T6 ` |
| E14-7 the config has no upper bound | config.py | `gt=0, le=defaults.MAX_FINDER_CHARS)` -> `gt=0)` | T8 | `E14-T8 ` |
| E14-8 the defaults drift | defaults.py | `MAX_MAP_CHARS = 2 * MAX_REDACT_CHARS` -> `MAX_MAP_CHARS = 4 * MAX_REDACT_CHARS` | T9 | `E14-T9 ` |

E14-4/E14-5: if the two conditions format identically, give each a distinct anchor (the comment on 427's line, or the indentation
of 547's) so each `old` occurs once; a mutant whose `old` occurs twice is a builder defect (E12's lesson). Good = KILLED with the
expect fragment in the first failing line. Equivalence claims need the lead.

## 7. Pins that change

- NONE of the existing tests changes (BY READING; phase 2 confirms). The new file and the new mutant file are additions.
- `CHANGELOG.md`: one line under the unreleased section (the `max_map_entries` line is the model).
- `defaults.py` comment at `SPELLED_MAX_CHARS` (118-124, "its other costs (the sweep's finder for a 260,000-character value) are not
  this limit's", "956 MB with no registry at all: a separate cost, not this limit's"): append "bounded since E14 by `MAX_FINDER_CHARS`".
  This block is also edited by G4 (123-125) and G9 (109-125): see section 8 before touching it; if it conflicts, leave it and note it.
- `ESCALATIONS.md` E14 and the G4 v8 ticket's L26 row are notes (lead/drafter), not the builder's: the builder reports the numbers.
- SECURITY wording (wording owner, NOT this build): replace "a hostile document can force about 1 GB of finder memory in one call"
  (E14's stated limit) and L26's "about 0.46 KB per character per build, no per-run character bound" by: "a run whose map holds more
  than 524,288 characters of distinct values ends `document_too_complex`; one redaction call that would build a finder over 786,432
  characters is refused (InputTooLarge, nothing shown): at most about 360 MB and 2 s of CPU per build on the test machine".

## 8. Interplay with G4 and G9 (both in flight) and where to rebase

| ticket | state | overlap with E14 | action |
|---|---|---|---|
| G4 (wip-g4, builder acdb3947 running) | phases 0-3 committed on wip-g4 | `_build`'s rules loop (tie-break, 3-12 lines ABOVE line 2038); defaults.py after `SPELLED_MAX_CHARS` (B64_* constants); adds `ENCODED` entries and the two-per-blob HIGHENTROPY pair (2.3) | E14's line 2038 edit is adjacent: a trivial textual conflict at most. E14's constants go after `MAX_BUNDLE_CHARS`, not after `SPELLED_MAX_CHARS`. G4's memory row L26 becomes bounded by E14 (M2 closes). |
| G9 (wip-g9, not merged, E17 fix builder) | built; perf regression open | `_build` end (`self._measure_rules()` after the group loop), `sweep` -> `_ensure_built`; defaults.py 109-125 | No line overlap with 2038 or `_trie` (BY READING: G9 does not call `_trie` elsewhere). MEASURED on wip-g9: the same build and sequence costs as HEAD (2.3, `g9_many.txt`), so the constants hold under G9. |
| G11 (E16 candidate 2, queued after G4/G9) | not started | `find()` post-pass | none |

Rebase rule: start from cloud/core-c AFTER G4 merges (it is first in the queue and writes ENCODED entries); do NOT wait for G9. If
G9 merges first, rebase on it too. If G9 merges AFTER E14, G9's builder resolves the 3-line neighbourhood in `_build` (E14 adds no
line there besides 2038). Re-run sections 2.3 and 2.4 (`m_seq.py plain 25`, `m_honest.py`) on the rebased tree before phase 2: the
numbers must stay within 20 percent of section 2 (stop rule 9.4).

## 9. Phases and stop rules

Phases (one commit each, `code E14: ...`, on a `wip-e14` branch from the rebase point):
0. Copy the scratch scripts and raw outputs to `handover/core-c/tickets/E14-files/` (if the scratch folder is gone, rewrite them from
   section 2: each is under 80 lines, method stated). Write `tests/test_redact_finder_cap.py` and run it on the base: record the
   red-before list (every row of section 5 marked RED must fail, and for the reason in the table).
1. defaults.py + config.py (T8, T9 green).
2. redact.py `_trie` limit and the `_build` call (T1-T5, T10-T12 green).
3. agent_loop.py both checks (T6, T7 green).
4. `tests/e14_mutants.py`, 8 mutants, all KILLED.
5. Batch: phase 1 (`-n 2`, not perf, not live) and phase 2 (whole suite incl. perf: test_k5_perf, test_redact_fold_budget,
   test_redact_settle_loop, the property corpus), ruff and bandit clean; CHANGELOG line; a notes commit with the measured rows.

Stop rules (stop, report, do not work around):
- 9.1 Any existing test fails that section 7 does not list: stop; never loosen or re-pin a security test (E17 is the precedent).
- 9.2 Any input of the property corpus or of the k5 shapes is refused, or `test_the_slowest_measured_shape_at_the_cap_stays_under_a_ceiling`
  gets slower than 1.2x its base run: stop.
- 9.3 test_redact_settle_loop's `SpelledMemoryTooMuch` pins flip to `FinderMemoryTooMuch`: stop (the lead decides the order of the two refusals).
- 9.4 Re-measured rates on the rebased tree differ from section 2 by more than 20 percent: stop and report before choosing other constants.
- 9.5 At most 3 tries per failing item; no ticket re-draft (lead order); no other constant (`MAX_MAP_ENTRIES`, `SPELLED_*`, `REDACT_BUDGET_S`, `B64_*`) changes.
- 9.6 Box loaded (2 or more pytest processes running): run direct `uv run python` calls of the scripts and single test functions,
  label the batch NOT RUN, and say so in the notes; never claim a batch that did not run.
- 9.7 Files: only defaults.py, config.py, guard/redact.py, runtime/agent_loop.py, CHANGELOG.md, the new test file, the new mutant
  file and the E14-files folder. A need to touch runmap.py, model_gate.py, k1b or tools.py: stop and ask.

## 10. Decision for the lead (defaults apply if no answer)

1. Constants: (a) DEFAULT `MAX_MAP_CHARS` 524,288 (run, ~240 MB / ~1.25 s a build), `MAX_FINDER_CHARS` 786,432 (build, ~360 MB / ~2 s);
   (b) more tolerant, 4x / 5x `MAX_REDACT_CHARS` (1,048,576 / 1,310,720: ~480 / ~600 MB, ~2.8 / ~3.6 s a build: the latter at about
   60 percent of the 6 s budget for the build alone); (c) tighter, 1x / 2x (262,144 / 524,288: ~120 / ~240 MB): a run whose
   document is the `curl -u ` perf shape could then take NO further value of any size from a tool.
2. Per-value cap: DEFAULT none (D2, measured as redundant). Alternative: a cap in `_place` at `MAX_REDACT_CHARS` (bounds nothing new).
3. Refusal: DEFAULT `InputTooLarge("FinderMemoryTooMuch")` (D3). Alternative: a subclass (no caller needs it today).
4. k1b bundles (no run-level check; `redact_bundle` lets InputTooLarge propagate to replay.py 158, as its own bundle cap does, BY
   READING): DEFAULT accept: a bundle whose distinct values pass 786,432 trie nodes is refused where it now builds ~1 GB. Alternative:
   a bundle-specific higher cap (a second constant; not designed).
5. G4 L26 / review 8 M2: DEFAULT closed by this ticket (the per-run character bound M2 asked for, at the place it named, plus the
   per-build bound); the G4 builder records no further sequence measurement (section 2.3 is it).
6. E14's grid point (20 x 20 both-ends-growing forms, 8.68 units per character, 57 percent of `SPELLED_MAX_WORK`): unchanged here; stays the lead's open call in E14.

## 11. What this does NOT bound (state it in the notes)

- The `find` passes before the build (E14's 8 x 260,000 still spends 3.97 s and 145 MB in `redact_many` before the refusal; the
  per-call deadline bounds that on the `redact_text` paths, `redact_many` with no `_deadline` has no total bound, as before).
- A refused build still costs up to the cap in nodes of the first trie (139 MB peak MEASURED at the 786,432 cap) and a call may
  build several times (each view or settle round that grows the map): each is bounded, their number is bounded by the deadline.
- The run cap counts characters of values, not the alias keys or the views' spellings that also become trie paths: the build cap is
  the exact bound; the run cap is the clean-ending one.
- Retained memory between builds (10-70 MB of compiled finders per RunMap) is not counted (MEASURED, 2.1).
