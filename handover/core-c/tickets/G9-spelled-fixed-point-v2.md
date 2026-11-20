# G9 v2: the sweep to a fixed point over the text read back (every KEY of the map put back), at most 4 passes; unions register their value only; the gate masks with existing placeholders (ORDER 023, escalation E10)

Status: DRAFT v2 (complete; every number measured unless section 14 says otherwise) for plan review round 2, core-c drafter, 2026-11-20. Rewrite of G9-spelled-fixed-point.md (v1)
taking or contesting every finding of G9-review-1.md (section 15). Nothing is built. Base of every measurement: cloud/core-c 78a0c8bcf
(src identical to d8777d5a7: G7 rounds 3-6, E9 `_OWN_OUTPUT` SECRET-only, Q9 merged). Measured on clean `git archive` copies of 78a0c8bcf in
the drafter's scratchpad (`g9v2/head`, the base; `g9v2/proto`, this design applied by `g9v2/scripts/make_proto2.py`, plus section 7's test
edits by `g9v2/scripts/edit_tests.py`). The shared tree was not edited and no test was run in it. Scripts (scratch; the builder commits
the ones of section 8): `g9v2/scripts/{make_proto2,edit_tests,cases2,fuzz2,chain,corpus_diff2,cmp,cost,cost2,bound,rbcost,mut2,diffm}.py`.

## 0. The finding that shapes the design (kept from v1, re-measured on 78a0c8bcf)
THE PLAIN LOOP DOES NOT CLOSE E10: iterating today's sweep reaches a fixed point at the second pass with the leak intact. The swallowed
characters are hidden by a placeholder, so a pass must read the text WITH THE PLACEHOLDERS PUT BACK. Cases (`cases2.py`, base -> v2):
| case | input | base (every later pass the same) | v2 |
|---|---|---|---|
| (a2) `<SECRET_1>`=`abcdefgh`, `<SECRET_2>`=`efghijkl` | `abcdefghijkl` | `<SECRET_1>ijkl` | `<SECRET_3>` (=`abcdefghijkl`), 2 passes |
| (a1) V=`ab9x`, F1 `<BEARER_1>`=V+`ab`, F2 `<BEARER_2>`=`xyz`+V | `see xyzab9xab end` | `see <BEARER_2>ab end` | `see <BEARER_3> end` (=`xyzab9xab`), 2 passes |
| (b) F1 registered; `xyz<SECRET_1>ab` swept; then F2 | `xyz<BEARER_1>` | `xyz<BEARER_1>` | `<BEARER_3>` (=`xyzab9xab`), 2 passes |
| natural, no map | `password=abcdefgh\ntoken=efghijkl\nsee abcdefghijkl` | `...see <SECRET_1>ijkl` (redact, redact_many, redact_text) | `...see <SECRET_3>` all three |
| natural, identifier first | `password=0.5-Xyz9\nhost 10.100.200.5-Xyz9 up` | `host <IPV4_1>-Xyz9 up` (5 of 8 characters of the password) | `host <SECRET_2> up` (SECRET, =`10.100.200.5-Xyz9`) |
| gate `enforce_map` | `x abcdefghijkl y` | `x <SECRET_1>ijkl y` | `x <SECRET_1><SECRET_2> y` (map untouched) |
| gate, an earlier call's output | `x <SECRET_1>ijkl y` | unchanged | `x <SECRET_1><SECRET_2> y` |

## 1. Goal
After every `_Redactor.sweep`, no rule original (a stored value or alias key that `_build` made a sweep rule of) occurs in the text READ BACK
(every token that is an exact KEY of the redactor's map put back to its value) covering both a readable character and part of a token. A
redactor that may register (`redact`, `redact_many`) registers each such run whole as ONE value (no pieces, no written form) and replaces
it; any other redactor (the gate's `enforce_map` and `held_value_left`) replaces the run's readable stretches by the EXISTING placeholders of
the secret values that cover them, and refuses that one text (`RedactionError("SpelledOverlap")`) only when a readable character is covered
by an identifier alone. A sweep that has not reached that state after 4 passes is refused (`InputTooLarge("SpelledNotSettled")`), never
returned. E10 (a) and (b) are closed for every text a call reads; the two settle-loop pins and the two gate pins are replaced.

## 2. Problem (the code at 78a0c8bcf, by name)
- `_Redactor.sweep`: `_spelled_sweep` (written forms, run-merging union inside ONE scan), then the literal sweep per free segment, longest
  value first; both read only the free text between placeholders.
- (a) the literal sweep replaces the longer value first; a shorter value overlapping it no longer matches what is left (older than G7).
- (b) `_spelled_sweep` in a later round: the earlier form's placeholder covers the part the later form needs.
- `settle` loops "table, then sweep" to a fixed point of TEXT changes; a text that stops changing with a leak inside is settled by that
  definition. The gate (`runmap.enforce_map`) loops the same sweep while the text changes: the same blind spot (Trap 3, a stated limit).

## 3. Files and dependencies
- src/hadavin_sdk/guard/redact.py (anchors BY NAME, section 8 phase 0): `_Redactor.__init__` (two attributes, `_longest` on the cached
  path), `_build` (`_longest`), `sweep` (the pass loop), new `_sweep_once` (today's body of `sweep`), new `_ensure_built` (today's inline
  build block), new `_spend`, `_read_back`, `_overlaps`, `_masked`, `_close`, `_place` (`derived` parameter), `_place_union` (takes a kind),
  `_spelled_sweep` (`shared` work count; its `_place_union` call), `redact` and `redact_many` (`r._may_register = True`), module constant
  `_SEP` and `import bisect`; docstrings: `_spelled_sweep` ("two OPEN limits" paragraph), `settle` (the passes and the bounds), `sweep`
  (header comment), module docstring line on overlaps.
- src/hadavin_sdk/defaults.py: `SPELLED_MAX_PASSES = 4` and `SPELLED_READBACK_REACH = 1024` (with a comment: how deep into a run of
  placeholders an occurrence is looked for; 4.3, 11) after `SPELLED_MAX_WORK`; `SPELLED_MAX_WORK`'s comment (the count is per sweep CALL,
  shared by its passes, and counts the read-back; the "Two OPEN limits (E10)" sentence replaced).
- src/hadavin_sdk/guard/runmap.py: docstrings only: `enforce_map` (the Trap 3 limit bullet replaced), `held_value_left` (it can now find an
  overlap and can raise `InputTooLarge` through the checker's sweep). No code change: `first` and `checker` are bare `_Redactor`s, so they
  take the gate behaviour (`_may_register` False) by default.
- src/hadavin_sdk/guard/model_gate.py: the module docstring's overlap bullet only (7.3; `test_d8_every_test_the_module_docstring_names_exists`
  pins the test names it lists). No code (L-D1b: an optional distinct code is the gate lane's call).
- tests/test_redact_mutants_meta.py: the pinned mutant count + 16 (section 10).
- tests/test_redact_settle_loop.py: the two pins replaced, the G9 block (section 7), the two ratio controls (phase 1).
- tests/test_runmap_enforce_map.py, tests/test_model_gate.py: the two gate pins replaced, three gate tests added (section 7.3; owner of the
  gate lane approves, L-D1).
- tests/redact_mutants.py: section 10's rows appended at the END of `M`.
- handover/core-c/evidence/: `g9_cases.py`, `g9_corpus_diff.py`, `g9_fuzz.py`, `g9_cost.py`, `g9_chain.py` (section 8) and `G9-1.md`.
- handover/core-c/ESCALATIONS.md (E10 RESOLVED), handover/core-c/tickets/G7-context-after-sweep.md (the two overlap limits replaced by 13).
DEPENDENCIES (builder worktrees not merged at 78a0c8bcf; whichever lands second re-derives by NAME):
- G7 round 7 (`/tmp/core-c-g7r7`, uncommitted): `settle` records the map size before the sweeps of EVERY round (a G9 union in any round's
  sweep then puts every string in `todo`: correct, costs one more round of sweeps), `_spell` gains the `SpelledMemoryTooMuch` cap
  (`_place_union(..., derived=False)` never calls `_spell`: G9 unions cost it nothing), `redact` drops the bank-flip re-read and passes
  `known=None`. No line of `sweep`, `_overlaps` or `_place_union` is touched by it; the `_place` edit (`derived`) and its `_spell` call
  site are adjacent: merge by name.
- E9/Q9 review fixes (`/tmp/core-c-e9b`): the `_OWN_OUTPUT` comment block only. Independent.
- G8 (G8b): edits the literal sweep's call `segment = _replace_standalone(segment, original, placeholder)` in the body of `sweep`; after G9
  that line is in `_sweep_once` (same text, moved). Whichever lands second applies its edit to `_sweep_once`.

## 4. Design (exact; the prototype `make_proto2.py` is this text applied, instrumentation aside)
### 4.1 The loop
```python
def sweep(self, out: str, deadline: float | None = None) -> str:
    # (today's header comment, plus: G9 passes; see the docstring of `_overlaps`)
    work = [0]  # ONE work count for every pass of this call: spelled scans, read-backs, finder passes, unions
    for _ in range(defaults.SPELLED_MAX_PASSES):  # 4
        size = len(self.mapping)
        out = self._sweep_once(out, deadline, work)
        spans = self._overlaps(out, deadline, work)
        if not spans and len(self.mapping) == size:
            return out  # converged: this pass found no overlap and registered nothing
        if spans:
            out = self._close(out, spans, deadline, work)
    from hadavin_sdk.guard.runmap import InputTooLarge  # runmap imports this module
    raise InputTooLarge("SpelledNotSettled")

def _sweep_once(self, out: str, deadline: float | None, work: list[int]) -> str:
    """One body of the sweep, as `sweep` was before G9: build if the map grew, the written forms, the literal sweep per free segment."""
    self._ensure_built(deadline)
    out = self._spelled_sweep(out, deadline, work)
    ...  # today's literal sweep, unchanged (from `parts = _PLACEHOLDER.split(out)` to `return "".join(parts)`)

def _ensure_built(self, deadline: float | None) -> None:
    """The build block `sweep` had inline: rebuild the rules when the map grew, under `deadline`."""
    if self._built_for != len(self.mapping):
        self._build_deadline = deadline
        try:
            self._build()
        finally:
            self._build_deadline = None
```
- In `sweep`, so every caller gets it: the first sweep of `redact`/`redact_many`, every sweep of `settle`, the gate's `first.sweep` and
  `held_value_left`'s `checker.sweep`, `_built`'s build-only `sweep("")` (no `<`: returns at once).
- CONVERGED = a pass whose read-back found nothing AND that registered nothing (the map size is unchanged). The second condition covers a
  union of written forms made by this pass's `_spelled_sweep` after the build the literal sweep used (pinned: `test_g9_a_pass_that_grew_the_map_is_not_the_last`).
- An honest text costs ONE pass: the body as today plus one read-back.
### 4.2 The work count and the clock (`_spend`)
```python
def _spend(self, work: list[int], n: int, deadline: float | None) -> None:
    """G9: add `n` units to the sweep's count; refuse past `defaults.SPELLED_MAX_WORK`; read the deadline each time the count passes a
    multiple of `_SPELL_CHECK_EVERY`."""
    before = work[0]
    work[0] = now = before + n
    if now > defaults.SPELLED_MAX_WORK:
        self._work_refused()
    if deadline is not None and now // _SPELL_CHECK_EVERY != before // _SPELL_CHECK_EVERY:
        self._over_budget(deadline)
```
`_spelled_sweep(self, out, deadline, shared: list[int] | None = None)`: `done = -_SPELL_CHECK_EVERY + (shared[0] if shared else 0)` and,
before each of its two `return`s after the scan, `if shared is not None: shared[0] = done + work` (its own counting is unchanged). Its call
in `_sweep_once` passes `work`. So the 4,000,000 units are ONE budget for the spelled scans, read-backs, finder passes and unions of every
pass of one `sweep` call (L-D3).
### 4.3 The read-back (`_read_back`)
A token is read back when it is an EXACT KEY of `self.mapping`, whoever wrote it (this redactor, the fold scan's `_mask_in_place` reverse
hit, `_withhold`, `_sub_glued`, an earlier call whose output is in the text, the model): no hand-kept written set (design M1, readiness B2).
A token that is not a key is a separator. Cost of forged keys: the per-piece count (below; test `..._counted_per_piece_...`).
```python
_SEP = "\0"  # module level: a separator in the read-back text

def _read_back(self, out: str, deadline: float | None, work: list[int]
               ) -> tuple[str, list[tuple[int, int, int, int, str | None]]] | None:
    """(E, segments) or None. A segment is (E start, E end, out start, out end, what): `what` None = free text, a placeholder = a token read
    back, "" = a separator. A RUN is a maximal sequence of key tokens with no free text between them. On each side where it touches free
    text it keeps its first (left) / last (right) `keep` characters (`self._longest - 1`, at most `defaults.SPELLED_READBACK_REACH`); the
    WHOLE run when those two reach its length (the short run: `ab<cdef>gh` against `abcdefgh`); a run that touches free text on neither side is one separator. Every piece is counted BEFORE it is
    appended. None when no token is read back next to free text (nothing to check: no clock read, no work beyond the pieces)."""
    keep = min(self._longest - 1, defaults.SPELLED_READBACK_REACH)  # how far an occurrence is looked for into a run
    mapping = self.mapping
    pieces: list[str] = []
    segs: list[tuple[int, int, int, int, str | None]] = []
    e = 0
    touched = False

    def put(piece: str, o0: int, o1: int, what: str | None) -> None:
        nonlocal e
        self._spend(work, len(piece), deadline)  # counted before it is held
        pieces.append(piece)
        segs.append((e, e + len(piece), o0, o1, what))
        e += len(piece)

    run: list[tuple[str, int, int]] = []  # (token, out start, out end)
    run_left = False

    def flush(right: bool) -> None:
        nonlocal touched
        if not run:
            return
        lk, rk = (keep if run_left else 0), (keep if right else 0)
        total = sum(len(mapping[tok]) for tok, _, _ in run)
        if not lk and not rk:
            put(_SEP, run[0][1], run[-1][2], "")
        elif lk + rk >= total:  # the short run: read back whole
            touched = True
            for tok, o0, o1 in run:
                put(mapping[tok], o0, o1, tok)
        else:  # head, a separator, tail
            touched = True
            taken = 0
            for tok, o0, o1 in run:
                if taken >= lk:
                    break
                cut = mapping[tok][: lk - taken]
                put(cut, o0, o1, tok)
                taken += len(cut)
            put(_SEP, run[0][1], run[-1][2], "")
            tail: list[tuple[str, int, int, str]] = []
            taken = 0
            for tok, o0, o1 in reversed(run):
                if taken >= rk:
                    break
                value = mapping[tok]
                cut = value[len(value) - min(len(value), rk - taken):]
                tail.append((cut, o0, o1, tok))
                taken += len(cut)
            for cut, o0, o1, tok in reversed(tail):
                put(cut, o0, o1, tok)
        run.clear()

    last, left = 0, False
    for m in _PLACEHOLDER.finditer(out):  # streamed: no split list of the whole text
        a, b = m.span()
        tok = m.group(1)
        if a > last:
            flush(True)
            put(out[last:a], last, a, None)
            left = True
        if tok in mapping:
            if not run:
                run_left = left
            run.append((tok, a, b))
        else:
            flush(False)
            put(_SEP, a, b, "")
        left = False
        last = b
    if last < len(out):
        flush(True)
        put(out[last:], last, len(out), None)
    else:
        flush(False)
    return ("".join(pieces), segs) if touched else None
```
- Why `_longest - 1` suffices: an occurrence that covers a readable character on one side of a run has at most `_longest - 1` characters
  inside the run; one that covers readable characters on BOTH sides covers the whole run, so the run is at most `_longest - 2` long and is
  read back whole (`lk + rk >= total`).
- Why the REACH (1,024): found by the whole suite on the prototype. `x` x 262,143 + ` ` (tests/test_k5_fixes4.py, tools.prepare_output)
  is ONE HIGHENTROPY token and a space; read back whole, the finder's lookahead tried the 262,143-character value at every position of a
  periodic E: 40 s instead of 1.2 s (quadratic, and invisible to the unit count, which counts E's characters, not the regex's steps).
  With the reach: 1.06 s (`reach.py`; 512: 0.80 s). Each side of a run then costs at most about REACH^2/2 character comparisons in the
  finder (0.5 M), and forged keys are refused by the count first (a 2,000-character periodic secret, 1,000 forged copies: refused
  `SpelledWorkTooMuch` in 0.03 s). The price is a stated limit: an overlap deeper than 1,024 characters into a run is not looked for
  (11; pinned by `test_g9_an_overlap_deeper_than_the_reach_is_not_looked_for_a_stated_limit`). The body's literal sweep has the same
  quadratic shape over FREE text (a raw periodic segment against a long periodic value), older than G9 and not changed by it.
- E-to-`out` map: a free segment maps character for character (`out start + (E offset - E start)`); a token segment (whole value or a cut
  piece of it) maps to the WHOLE token `[out start, out end)`; a separator matches nothing (an occurrence that covers one is dropped).
- `_longest`: `max(map(len, self._rules), default=0)`, set in `_build` (before `self._built_for = ...`) and on the cached path of
  `__init__` (after the 5-tuple is unpacked). `_rules` is keyed by every rule original INCLUDING alias keys (`_ordered` holds the alias
  items), so an NFKC-lengthened alias key is counted (design Nit 2). The cached `state` tuple keeps its shape (5 items: readiness M4,
  design M4): its consumers are `_Redactor.__init__` (unpack), `_build` (write), `runmap._built` (copies `(cache["map"], cache["state"])`
  as an opaque pair into the gate's holder), `runmap.snapshot`'s private copy of `redact_cache`, and the test
  tests/test_runmap_enforce_map.py:616 (order of the two writes); none changes.
### 4.4 The overlaps (`_overlaps`)
```python
def _overlaps(self, out: str, deadline: float | None, work: list[int]) -> list[tuple[int, int, str, str | None]]:
    """[(start, end, kind, masked)], sorted, disjoint. out[start:end] is one run: every occurrence in E of a rule original (an identifier
    only where no ASCII letter or digit touches it IN E) that covers at least one free character AND part of at least one token and no
    separator, merged when they overlap in `out`; tokens are taken whole, free text as far as the occurrences reach. `kind`: the first
    SECRET kind met in `out` order among the run's tokens and the occurrences' placeholders, else the first token's kind. `masked`: only
    for a redactor that may not register (`_masked`), else None."""
    if "<" not in out:
        return []
    self._ensure_built(deadline)  # a union of written forms in this pass's `_spelled_sweep` grew the map
    if not (self._finders or self._slow):
        return []
    rb = self._read_back(out, deadline, work)
    if rb is None:
        return []
    E, segs = rb
    rules = self._rules
    occ: list[tuple[int, int, str]] = []

    def add(word: str, at: int) -> None:
        rule = rules.get(word)
        if rule is None:
            return
        end = at + len(word)
        if rule[2] is not _EVERY_COPY and (E[at - 1:at] in _ALNUM or E[end:end + 1] in _ALNUM):
            return
        occ.append((at, end, word))

    for finder, prefixes in self._finders:
        self._spend(work, len(E), deadline)  # one finder pass over E
        for m in finder.finditer(E):
            w = m.group(1)
            add(w, m.start())
            for p in prefixes.get(w, ()):
                add(p, m.start())
    for w in self._slow:
        self._spend(work, len(E), deadline)  # one str.find pass over E per slow value
        j = E.find(w)
        while j >= 0:
            add(w, j)
            j = E.find(w, j + 1)
    self._spend(work, len(occ), deadline)
    starts = [s[0] for s in segs]
    hits: list[tuple[int, int, str]] = []  # (out start, out end, the occurrence's placeholder)
    for a, b, w in occ:
        i0 = bisect.bisect_right(starts, a) - 1
        i1 = bisect.bisect_right(starts, b - 1) - 1
        covered = segs[i0:i1 + 1]
        if any(s[4] == "" for s in covered):
            continue  # crosses a separator
        if all(s[4] is None for s in covered) or all(s[4] for s in covered):
            continue  # free text only (the literal sweep's) or tokens only (nothing readable)
        s0, s1 = segs[i0], segs[i1]
        oa = s0[2] if s0[4] else s0[2] + (a - s0[0])
        ob = s1[3] if s1[4] else s1[2] + (b - s1[0])
        hits.append((oa, ob, rules[w][1]))
    if not hits:
        return []
    hits.sort()
    groups: list[list] = []  # [start, end, [hits]]
    for h in hits:
        if groups and h[0] < groups[-1][1]:
            groups[-1][1] = max(groups[-1][1], h[1])
            groups[-1][2].append(h)
        else:
            groups.append([h[0], h[1], [h]])
    result = []
    for start, end, members in groups:
        toks = [(m.start(), m.group(1)) for m in _PLACEHOLDER.finditer(out, start, end)]
        met = sorted([(p, _kind(tok)) for p, tok in toks] + [(h[0], _kind(h[2])) for h in members])
        kind = next((k for _, k in met if k in SECRET_KINDS), _kind(toks[0][1]))
        masked = None if self._may_register else self._masked(start, end, toks, members)
        result.append((start, end, kind, masked))
    return result
```
- The KIND (design M3, readiness B3): an occurrence's kind is the kind of `self._rules[word][1]`, the placeholder whose rule `_build` kept
  for that original (for an alias key, the alias map's placeholder; for a value held twice, the first in `_ordered`, as the literal sweep
  writes). The union holds a secret when any token in the run or any occurrence is of a SECRET kind; then its kind is the FIRST secret kind
  met in `out` order (a token at its start, an occurrence at its start; ties: the order of `sorted` on (position, kind)). A union of
  identifiers only takes the first token's kind (as G7's union took the first form's).
- `self._rules[w][1]` is never missing: `occ` holds only words of `_rules`.
### 4.5 The gate's form (`_masked`) and the replacement (`_close`)
```python
@staticmethod
def _masked(start: int, end: int, toks: list[tuple[int, str]], members: list[tuple[int, int, str]]) -> str | None:
    """The run as the gate writes it: its tokens as they are; each free stretch replaced by the placeholders of a minimal left-to-right
    cover of it by occurrences of SECRET-kind values (at each point the occurrence reaching furthest; the same placeholder twice in a row
    written once). None when a free character is covered by no secret-kind occurrence (only by an identifier, which must restore exactly)."""
    secret = [h for h in members if _kind(h[2]) in SECRET_KINDS]
    parts: list[str] = []
    pos = start
    for t0, t1, tok in [(p, p + len(t), t) for p, t in toks] + [(end, end, "")]:
        s = pos
        while s < t0:  # the free stretch [pos, t0)
            best = max((h for h in secret if h[0] <= s < h[1]), key=lambda h: h[1], default=None)
            if best is None:
                return None
            if not parts or parts[-1] != best[2]:
                parts.append(best[2])
            s = best[1]
        if tok:
            parts.append(tok)
        pos = t1
    return "".join(parts)

def _close(self, out: str, spans: list[tuple[int, int, str, str | None]], deadline: float | None, work: list[int]) -> str:
    """Replace each run of `_overlaps`. A redactor that may register: the run's value registered whole under its kind, no written form, no
    pieces (`_place_union(..., derived=False)`). Any other: the run's masked form; a run with none refuses the text."""
    pieces: list[str] = []
    last = 0
    for start, end, kind, masked in spans:
        self._spend(work, end - start, deadline)
        if self._may_register:
            placeholder = self._place_union(out[start:end], kind, derived=False)
        elif masked is not None:
            placeholder = masked
        else:
            from hadavin_sdk.guard.runmap import RedactionError  # runmap imports this module
            raise RedactionError("SpelledOverlap")
        pieces += (out[last:start], placeholder)
        last = end
        self.actions += 1
    pieces.append(out[last:])
    return "".join(pieces)
```
`_may_register`: `self._may_register = False` in `__init__` (after `self._next_prefix_id = 0`); `redact` and `redact_many` set
`r._may_register = True` right after constructing `r`. Every other `_Redactor` (runmap `snapshot`'s `first`, `_built`'s, `checker`) keeps
False.
### 4.6 Registration (`_place`, `_place_union`)
```python
def _place(self, label: str, full: str, original: str, derived: bool = True) -> str:
    # body as today, with `derived and` added to the two secret-kind conditions:
    first = _PLACEHOLDER.search(original) if derived and label in SECRET_KINDS else None
    ...
    for piece in (_PIECE.findall(_PLACEHOLDER.sub(" ", original)) if derived and label in SECRET_KINDS else ()):

def _place_union(self, union: str, kind: str, derived: bool = True) -> str:
    """The placeholder of an overlap: `union` is the text of the whole run (`xyz<SECRET_1>ab`), registered under `kind` as a value of its
    own (its restored text) unless that value has a placeholder already. A placeholder it already has is reused unless `kind` is a secret
    kind and that placeholder's is not: then a second placeholder of `kind` is registered (a union holding a secret is never under an
    identifier kind, so never restorable). `derived=False` (G9's unions): the value only, no written form, no pieces."""
    full = _PLACEHOLDER.sub(lambda p: self.mapping.get(p.group(1), p.group(1)), union)
    have = self.reverse.get(full)
    if have is not None and (_kind(have) in SECRET_KINDS or kind not in SECRET_KINDS):
        return have
    return self._place(kind, full, union if derived else full, derived)
```
`_spelled_sweep`'s call becomes `placeholder = self._place_union(out[start:end], _kind(placeholder))` (G7's unions keep their written form
and pieces: unchanged behaviour; their kind is the first form's, a secret kind by construction). The "second placeholder" case leaves the
value under two placeholders; `_build` keeps the FIRST one's rule for its literal sweep (the identifier's, standalone); the union token that
was written is the secret one and is read back inside a token from then on (measured: `z<SECRET_3> y`, section 9.1). runmap `_rules_conflict`
already handles a value under two rules at the gate (E5).
### 4.7 Settle, refusals and rollback (readiness M5, design Nit 2)
- A G9 union is registered with no journal open (sweeps never run inside `_open_journal`): `_rollback` cannot remove it, and `settle`
  never rolls back. It counts as map growth for `settle` (`known`, and with G7 round 7 every round): every string is swept once more.
- A refused sweep (`SpelledNotSettled`, `SpelledWorkTooMuch`, a deadline) raises out of `settle` and out of `redact`/`redact_many`: nothing
  is returned, the `_Redactor` (a copy of the caller's map) is dropped with its unions. `redact_text` updates the RunMap only after success
  (`mapping.update(current)` is its last statement), so a refused call adds NO entry to the run's map. The run's `redact_cache` may hold
  the state built for the dropped map: it is keyed by `cache["map"] == self.mapping`, so the next call rebuilds (as for any refused call).
### 4.8 The number of passes (design M2: the v1 claim "passes 3 and 4 are unreachable" is DELETED and replaced by this)
- With pieces registered (v1's `_place` path), passes 3 and more ARE reachable by a real input (measured, `chain.py`, section 9.3): the
  critic's chain needs 3 passes at depth 1, 4 at depth 2, and is REFUSED (`SpelledNotSettled`) at depth 3 and 4, through `redact` and
  `redact_text`.
- With `derived=False` (this design) the same inputs take 2 passes at every depth, and every random search took at most 2 (section 9.2:
  120,000 inputs: 20,000 over `abc` and 20,000 over mixed-case-plus-digit values of 8 to 14 characters, through three entry points each).
- Why 2 (an argument, not a proof; the bound 4 is a fail-closed margin, as `_SETTLE_ROUNDS` is): pass 1's `_close` replaces each run by ONE
  token whose value is exactly the run's characters in E, so E is unchanged as text; every occurrence that made a run now lies inside one
  token (not an overlap); an occurrence outside the runs that reaches into one covered, in pass 1, either a token character (then it was
  part of the run) or only free characters of the run (a free-only occurrence, which the literal sweep of pass 1 cannot leave for an
  every-copy value, and which for an identifier fails the same E standalone test in both passes). The new rules (the union values) occur in
  E only where a run was (each value holds at least one token's value of the run whole). The gate's masked form changes E (it writes the
  covering values' full texts); its outer edges keep the characters next to the free text outside the run (the cover starts at the run's
  first free character and ends at its last), so the same argument applies; measured: 2 passes in the gate's 20,000 + 20,000 searches.
- Where 3 passes could still come from (not reproduced): a G7 union of written forms registered in pass 2 (with its pieces), or a
  rule built only in pass 2 that a free-only occurrence of pass 1 matches. Both end in `SpelledNotSettled` (fail closed) if they chain.
### 4.9 Bounds (design M5: `_build`, finder cost and `_sweep_once` added)
- Per `sweep` call: at most 4 passes; each pass = `_ensure_built` (only when the map grew: pass 1 after a find, pass k+1 after pass k's unions)
  + `_spelled_sweep` (counted) + the literal sweep (NOT counted, as today: one finder pass per free segment and one `str.replace` per value
  present) + the read-back (counted: one unit per character of E, plus len(E) per finder and per slow value, plus one per occurrence) +
  `_close` (counted: one per character of each run). One shared count: at most `SPELLED_MAX_WORK` = 4,000,000 units for all passes.
  NOT in the count: `_build` (O(map) dict/sort work plus compiling the trie regex; the deadline is read every 512 rules), the literal sweep.
- Per string per call: at most 1 + `_SETTLE_ROUNDS` (4) = 5 sweeps, so at most 20 bodies, 20 read-backs and at most 20 `_build`s when every
  pass grows the map; a pass that grows the map is one that found a run, and every measured input needs at most 2 passes (one `_build`
  more per sweep that found a run). Measured (9.4): forcing every sweep to 4 passes costs 1.9x on the jar shape (0.58 -> 1.12 s), so 5 such
  sweeps of one string would be about 5.6 s, at the edge of the 6 s budget; past it the call is refused (deadline).
- With a deadline (every producer path: `redact_text`, `redact_many`, `redact`): the call's `REDACT_BUDGET_S` CPU budget bounds the whole;
  read in `_build`, every 1,024 units of the spelled scan AND of the read-back (`_spend`), every 32nd free segment and before each value
  replaced. Not interrupted: one `finditer` of a finder over E, one `E.find` loop of one slow value, one `str.replace`. With no deadline (a
  bare `_Redactor.sweep(text)`): 4M units per sweep, no total bound (stated, as today).
- Memory: E is at most `SPELLED_MAX_WORK` characters, and per run at most 2 x `SPELLED_READBACK_REACH` + 1 (every piece counted before it is appended; test 9 bounds the traced peak); honest
  texts: at most len(out) + 2 x (`_longest` - 1) per run; a union adds ONE map entry (no trie node: no `_spell`).

## 5. Decisions made (drafter)
- D-1 The loop is in `sweep` (all callers), not in `settle` (case (a) has no settle round; the gate has no settle).
- D-2 The convergence test is the read-back plus "the map did not grow", not a second body run (honest = 1 pass).
- D-3 Union kind: first secret kind met (4.4); a reverse hit of a weaker kind registers a second placeholder of the secret kind (4.6).
  BUILT in the prototype and tested (`test_g9_a_union_that_holds_a_secret_...`, `..._an_identifier_holds_gets_a_secret_placeholder_...`).
- D-4 Read back = exact keys of the map (no written set).
- D-5 G9 unions register their value only (`derived=False`): no pieces, no written form. A readable copy elsewhere of a PART of a secret
  (the chain's `hIjK1mNoPq2<SECRET_3>`) stays readable, exactly as any partial copy of a secret does today: the base rule masks stored
  values, not their substrings; v1's pieces made the chain's later lines masked but bought 3, 4 and refused passes.
- D-6 The read-back, finder passes and unions are counted in the existing `SPELLED_MAX_WORK` (shared per sweep call), not a new limit.
- D-7 The gate's default (L-D1) is to mask with existing placeholders; refuse one text when an identifier must restore exactly.
- D-8 The read-back looks at most `SPELLED_READBACK_REACH` = 1,024 characters into a run of placeholders (4.3; L-D6).

## 6. Decisions for the lead (build default first)
| id | question | default | consequence | fallback | consequence |
|---|---|---|---|---|---|
| L-D1 | the gate (a redactor that may not register) | MASK the run with the existing placeholders of the secret values covering its readable part (`<SECRET_1><SECRET_2>`); refuse THAT TEXT (`RedactionError("SpelledOverlap")`, gate code `mask_refused`) only when an identifier alone covers a readable character | Trap 3 closed for secret values with no refusal and no map write; the model sees two tokens where the text had one value; identifier-identifier overlaps refuse the call; the two gate pins become "masked" tests (section 7.3; gate-lane edit) | (b) refuse every overlap (v1's) / (c) skip the check | (b) a planted pair refuses every call carrying it; (c) Trap 3 stays: the tail of a secret readable (see the table below) |
| L-D1b | a distinct gate code for `SpelledOverlap` | none: it is a RedactionError, so `mask_refused` (already distinct from `mask_budget_exceeded`) | no model_gate change | a new `CODE_OVERLAP_REFUSED` in model_gate | a gate-lane edit; the audit row names the cause |
| L-D2 | the pass bound | 4 (`SPELLED_MAX_PASSES`) | margin of 2 over the measured need | 2 | no margin; a chain through a G7 union would refuse |
| L-D3 | work count | shared per `sweep` call | honest worst 1,029,656 units (cookie shape; 3.9x headroom) | per pass | up to 4 x 4M per sweep |
| L-D3b | what a read-back unit is | one per character of E as built PLUS one per character per finder pass | honest worst 1.03 M | E as built only (the first finder pass free) | about 0.5 M on the cookie shape; the finder passes over E (3 groups for nested prefixes) uncounted, bounded by the deadline only |
| L-D6 | the read-back reach | 1,024 characters | `x`x262k+space 1.06 s (base 1.2 s); overlaps deeper than 1,024 into a token not looked for | 4,096 | about 16x the worst finder cost per run side (8 M comparisons); deeper overlaps covered |
| L-D5 | an overlap visible only in a decoded view (entities, escapes, folds) | out of G9 (views are G1/G10's) | `&#49;<IPV4_3>`, `ａbcd<SECRET_2>` stay as today | read the views back too | cost per view; not designed |
The three gate options compared (design M4; values A, B overlap, B swept second so A's token stands and B's tail is readable):
| option | leak | refusals | map |
|---|---|---|---|
| (a) mask (default) | none | only when an identifier alone covers a readable character (`acme-prod-01` + `prod-01-eu` in `acme-prod-01-eu`): that call | untouched |
| (b) refuse every overlap | none | every call whose text holds the overlap: an attacker who plants two short values (`password=inter`, `token=terna`: 4+ characters, a secret kind, swept in every copy) refuses every model call carrying `interna` that did not pass through `redact` first (a system prompt, a message the agent wrote); a refused message in the history refuses every later call of the run | untouched |
| (c) skip | up to len(B) - 1 characters of B per copy (a 40-character key overlapping a 4-character value: 36 characters), attacker-independent | none | untouched |
The DoS left with (a): an attacker who plants two IDENTIFIER values that overlap (TENANT, HOSTNAME, an address) refuses every gate call
whose text holds the overlap as written (`mask_refused`), and the run keeps the message in its history. Identifiers are found by patterns
(a host name, an address), not by `key=` planting, so the planted pair costs more than two `password=` lines; stated in 11 and 13.

## 7. Acceptance tests
### 7.1 What is added, deleted and edited (all measured on `proto`, section 9)
- tests/test_redact_settle_loop.py: `import tracemalloc` added after `import time`; the two pins DELETED (7.2); the two ratio controls
  edited (7.2); the G9 block (7.4, 23 tests, appended at the end of the file: it uses the file's `R`, `SHORT`, `defaults`, `runmap`,
  `pytest`, `re`, `_stepping_clock`, `_best_cpu`, `_cookie_log`, `_copies_of`).
- tests/test_runmap_enforce_map.py and tests/test_model_gate.py: 7.3. src/hadavin_sdk/guard/model_gate.py: its module docstring names the
  enforce test of the overlap limit (`E::test_stated_limit_partial_overlap_leaves_a_tail`; pinned by
  `test_d8_every_test_the_module_docstring_names_exists`, which went red on the prototype until the docstring was edited): that bullet
  is replaced by the text of 7.3 (a docstring edit in the gate lane's file, no code).
### 7.2 The pins and the controls
- DELETED `test_an_overlap_completed_only_in_a_later_round_leaves_the_swallowed_part_readable_a_stated_limit` (calls `_spelled_sweep`
  directly, so it does not go red; it is replaced by `test_g9_an_overlap_completed_only_in_a_later_round_is_masked_whole`), and
  `test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit` (red on the build; replaced by
  `test_g9_two_overlapping_values_in_raw_text_are_masked_whole`). The comment `# --- M-B (a): two compound values that overlap as RAW text`
  becomes `# --- M-B (a), closed by G9 (tests in the G9 block): two compound values that overlap as RAW text`. ESCALATIONS.md E10 names the
  first pin: replace the name there too.
- `test_5000_compound_secrets_at_the_size_cap_the_trie_walk_is_not_dict_misses` takes `monkeypatch`; after its
  `assert swept.count("copy <SECRET_") == 5000, ...` line insert
  `monkeypatch.setattr(r, "_overlaps", lambda *a: [])  # G9: both runs time the scan alone (the read-back has its own test)`.
  (On the build without this line it stays GREEN: the gate-mode redactor masks instead of refusing, and the mask only slows the
  `without` run; the line keeps the ratio the scan's.)
- `_swept_cpu` (used by `test_the_scan_does_not_depend_on_how_many_distinct_prefix_lengths_are_registered`): after `r.sweep("")` insert
  `r._overlaps = lambda *a: []  # G9: the scan alone, in both runs of the ratio (the read-back: test_g9_the_read_back_costs_...)`.
  Without it the test is RED on the build: `(0.240, 0.045)` (the read-back's finder passes over the 300 nested cookie values; measured
  on its own by `test_g9_the_read_back_costs_about_two_sweeps_of_the_text_it_reads`).
### 7.3 The gate tests (exact)
tests/test_runmap_enforce_map.py: `test_stated_limit_partial_overlap_leaves_a_tail` (lines 179-196 at 78a0c8bcf) is REPLACED by:
```python
def test_trap3_a_partial_overlap_of_two_secret_values_is_masked_with_their_placeholders():
    """Trap 3, closed by G9 (E10). `abcd` and `cdef` are both known and the text holds `abcdef`: neither contains the other, so the sweep
    replaces one and the other's rest stood readable (`<SECRET_1>ef`, `ab<SECRET_2>`: the stated limit pinned here before G9). The text read
    back with the map's placeholders put back still holds the other value across the placeholder; the gate may not add an entry, so the
    readable rest is replaced by the EXISTING placeholder of the value that covers it: `<SECRET_1><SECRET_2>` whatever the map order. The map
    is not written (`_enforce` asserts it) and nothing readable is left. The same for an earlier call's output read with a value learned
    since. A held-back value is not in the main sweep's map, so its rest stays HERE; the gate's net finds it (`held_value_left`)."""
    assert _enforce("abcdef", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"}) == "<SECRET_1><SECRET_2>"
    assert _enforce("abcdef", {"<SECRET_2>": "cdef", "<SECRET_1>": "abcd"}) == "<SECRET_1><SECRET_2>"
    assert _enforce("abcdefg", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdefg"}) == "<SECRET_1><SECRET_2>"
    assert _enforce("x <SECRET_1>ef y", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"}) == "x <SECRET_1><SECRET_2> y"
    # two identifiers: each is touched by a letter of the other, so NEITHER is replaced in the overlap, and read back neither stands alone
    identifiers = {"<TENANT_1>": "abcd", "<TENANT_2>": "cdef"}
    assert _enforce("abcdef", identifiers) == "abcdef"
    # ... while each standalone copy still is
    assert _enforce("abcdef abcd cdef", identifiers) == "abcdef <TENANT_1> <TENANT_2>"
    # the held-back value `SECRET_1` (8 characters) loses to the shorter `ET_1zz9` (7) in the sweep; the net sees the rest
    held_back = {"<SECRET_1>": "SECRET_1", "<SECRET_2>": "ET_1zz9"}
    assert _enforce("SECRET_1zz9", held_back) == "SECR<SECRET_2>"
    assert runmap.held_value_left("SECR<SECRET_2>", runmap.snapshot(held_back))
    assert _enforce("SECRET_1 zz9", held_back) == "<SECRET_1> zz9"


def test_trap3_an_overlap_an_identifier_must_restore_refuses_the_text():
    """G9, L-D1: a readable character covered only by an identifier (restored exactly on the way back) has no existing placeholder that can
    stand for it, so THIS text is refused: RedactionError("SpelledOverlap"), not InputTooLarge (the gate's code is `mask_refused`, not the
    budget's). The map is not written; a text without the overlap is enforced against the same map."""
    identifiers = {"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"}
    with pytest.raises(runmap.RedactionError, match="SpelledOverlap") as caught:
        runmap.enforce_map("acme-prod-01-eu", identifiers)
    assert not isinstance(caught.value, runmap.InputTooLarge)
    assert _enforce("acme-prod-01 and prod-01-eu", identifiers) == "<TENANT_1> and <TENANT_2>"
```
tests/test_model_gate.py: `test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent` (lines 566-573) is REPLACED by:
```python
def test_b1_a_partial_overlap_is_masked_with_both_placeholders_in_what_is_sent():
    """`abcd` and `cdef` known, `abcdef` in the text: `<SECRET_1><SECRET_2>` is sent (G9; before it `<SECRET_1>ef` was sent, a stated limit)."""
    bound, client, _, sink = build(
        mapping=runmap.RunMap({"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"})
    )
    bound.chat([{"role": "user", "content": "abcdef"}], system="s", route="main")
    assert client.sent[0]["messages"][0]["content"] == "<SECRET_1><SECRET_2>"
    assert sink.codes() == [("ok", None)]


def test_b1_an_overlap_an_identifier_must_restore_refuses_the_call_as_mask_refused():
    """G9, L-D1: two identifiers that overlap in the text (`acme-prod-01`, `prod-01-eu` in `acme-prod-01-eu`): no existing placeholder can
    stand for the readable rest, so the call is refused (`mask_refused`); nothing is sent, nothing reserved."""
    bound, client, meter, sink = build(
        mapping=runmap.RunMap({"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"})
    )
    with pytest.raises(UnmaskedInput):
        bound.chat([{"role": "user", "content": "acme-prod-01-eu"}], system="s", route="main")
    assert client.sent == [] and sink.codes() == [("refused", "mask_refused")]


def test_b1_a_held_back_value_cut_by_an_overlap_refuses_the_call_as_held_value_left():
    """G9: the held-back `SECRET_1` loses to `ET_1zz9` in the sweep (`SECR<SECRET_2>`); the net's checker reads the text back with every
    secret value and finds `SECRET_1` across the placeholder: the call is refused (`held_value_left`), where `SECR<SECRET_2>` was sent."""
    from hadavin_sdk.guard.model_gate import HeldValueLeft

    bound, client, _, sink = build(
        mapping=runmap.RunMap({"<SECRET_1>": "SECRET_1", "<SECRET_2>": "ET_1zz9"})
    )
    with pytest.raises(HeldValueLeft):
        bound.chat([{"role": "user", "content": "SECRET_1zz9"}], system="s", route="main")
    assert client.sent == [] and sink.codes() == [("refused", "held_value_left")]
```
src/hadavin_sdk/guard/model_gate.py, module docstring, the bullet "- Two known values that overlap in the text ..." (4 lines ending
`E::test_stated_limit_partial_overlap_leaves_a_tail`) is REPLACED by:
```
- Two known values that overlap in the text without one containing the other (`abcd` and `cdef` in `abcdef`):
  since G9 the text read back with the map's placeholders put back is checked, and the readable rest is replaced by
  the EXISTING placeholder of the secret value that covers it (`<SECRET_1><SECRET_2>`; the map is not written);
  where only an identifier covers it the call is refused (`mask_refused`). Two identifiers that touch each other
  there are both left. A value that is a piece of one of the map's placeholders is not in the main sweep: its rest
  stays and the net (`held_value_left`) refuses the call.
  E::test_trap3_a_partial_overlap_of_two_secret_values_is_masked_with_their_placeholders
  E::test_trap3_an_overlap_an_identifier_must_restore_refuses_the_text
```
runmap.py `enforce_map` docstring: the bullet "- Two known values that overlap in the text without one containing the other ..." is
replaced by the same text (minus the test names); `held_value_left`'s docstring gains: "Its checker's sweep reads the text back (G9): a
secret value spelled across a placeholder is found; the sweep can raise `InputTooLarge` (its work count, the deadline,
`SpelledNotSettled`), which `_chunk` does not catch: `_enforced` reports it as `mask_budget_exceeded`. The checker holds only secret
values, so it never raises `SpelledOverlap`."
`held_value_left`'s callers: model_gate `_chunk` only (grep at 78a0c8bcf). An `InputTooLarge` from the checker passes `_chunk`
(model_gate.py:739, no `try`) up to `_enforced`'s `except runmap.InputTooLarge` (model_gate.py:721): code `mask_budget_exceeded`, the call
refused, never sent: the behaviour of any other budget refusal of the gate (L-D1, stated in 11).
### 7.4 The G9 block (exact code, appended to tests/test_redact_settle_loop.py)
```python
# --- G9 (ORDER 023, E10): the sweep to a fixed point over the text read back --------------------------------------------------------

_TOKEN = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
_A, _B = "abcd" + "efgh", "efgh" + "ijkl"  # two SECRET values that overlap by `efgh`


def _registering(mapping: dict[str, str] | None) -> R._Redactor:
    """A redactor that may register a union, as `redact` and `redact_many` make it."""
    r = R._Redactor(mapping)
    r._may_register = True
    return r


def test_g9_an_overlap_completed_only_in_a_later_round_is_masked_whole():
    """E10 (b), REPLACES the round 3 pin: round 2 sweeps `xyz<SECRET_1>ab` to `xyz<F1>`; round 3 registers F2 `xyz<SECRET_1>`. The read-back of
    `xyz<F1>` is `xyz` + V + `ab`: F2's value covers `xyz` and part of F1, so the run is registered whole and replaced; nothing of it stays
    readable. Its number is not pinned (it depends on the order of registration); its value and kind are."""
    r = _registering({"<SECRET_1>": SHORT})
    f1 = r._place("BEARER", SHORT + "ab", "<SECRET_1>ab")
    round2 = r.sweep("xyz<SECRET_1>ab")
    assert round2 == f"xyz{f1}"
    f2 = r._place("BEARER", "xyz" + SHORT, "xyz<SECRET_1>")
    round3 = r.sweep(round2)
    assert _TOKEN.fullmatch(round3) and round3 not in (f1, f2), round3
    assert r.mapping[round3] == "xyz" + SHORT + "ab" and R._kind(round3) == "BEARER"
    assert r.sweep(round3) == round3


def test_g9_two_overlapping_values_in_raw_text_are_masked_whole():
    """E10 (a), REPLACES the raw pin: `abcdefgh` and `efghijkl` in `abcdefghijkl` (the literal sweep cut the second), and F1 = V+`ab`,
    F2 = `xyz`+V in a raw `xyz`+V+`ab`. Each run is one new SECRET/BEARER value; the map gains exactly that entry."""
    plain = _registering({"<SECRET_1>": _A, "<SECRET_2>": _B})
    assert plain.sweep(_A + "ijkl") == "<SECRET_3>"
    assert plain.mapping == {"<SECRET_1>": _A, "<SECRET_2>": _B, "<SECRET_3>": _A + "ijkl"}
    r = _registering({"<SECRET_1>": SHORT})
    f1 = r._place("BEARER", SHORT + "ab", "<SECRET_1>ab")
    f2 = r._place("BEARER", "xyz" + SHORT, "xyz<SECRET_1>")
    out = r.sweep("see xyz" + SHORT + "ab end")
    union = out.removeprefix("see ").removesuffix(" end")
    assert _TOKEN.fullmatch(union) and union not in (f1, f2), out
    assert r.mapping[union] == "xyz" + SHORT + "ab"


def test_g9_the_raw_overlap_through_redact_redact_many_and_redact_text():
    """The natural input (no seeded map): two secrets found by their keys, then a raw `abcdefghijkl`. Before G9: `see <SECRET_1>ijkl`."""
    lines = ["password=" + _A, "token=" + _B, "see " + _A + "ijkl"]
    text = "\n".join(lines)
    expected = ["password=<SECRET_1>", "token=<SECRET_2>", "see <SECRET_3>"]
    result = R.redact(text)
    assert result.text == "\n".join(expected)
    assert result.mapping == {"<SECRET_1>": _A, "<SECRET_2>": _B, "<SECRET_3>": _A + "ijkl"}
    assert result.restore(result.text) == text
    many, mapping = R.redact_many(lines)
    assert many == expected and mapping["<SECRET_3>"] == _A + "ijkl"
    assert runmap.redact_text(text, runmap.RunMap()) == "\n".join(expected)


def test_g9_every_key_of_the_map_is_read_back_whoever_wrote_it_and_nothing_else():
    """The read-back puts back a token that is an exact KEY of the map, whoever wrote it (this redactor, an earlier call, the fold scan
    reusing a placeholder): `<SECRET_1>` came in with the text. A token that is not a key (`<SECRET_9>`) is a separator: nothing is read
    across it (mutant G9-7)."""
    r = _registering({"<SECRET_1>": _A, "<SECRET_2>": _B})
    assert r.sweep("x <SECRET_1>ijkl y") == "x <SECRET_3> y"
    assert r.mapping["<SECRET_3>"] == _A + "ijkl"
    other = _registering({"<SECRET_1>": _A, "<SECRET_2>": _B})
    assert other.sweep("x <SECRET_9>ijkl y") == "x <SECRET_9>ijkl y"
    assert other.sweep("x efgh<SECRET_9>ijkl y") == "x efgh<SECRET_9>ijkl y"
    assert len(other.mapping) == 2
    # a value that holds a NUL (the separator's character): its NUL-free alias key is swept by the body, as at the base; no union
    nul = _registering({"<SECRET_1>": "\0" + "wxyz"})
    assert nul.sweep("a<SECRET_9>wxyz") == "a<SECRET_9><SECRET_1>" and len(nul.mapping) == 1


def test_g9_a_short_run_of_tokens_is_read_back_whole():
    """Readiness B1: a run whose kept head and tail together reach its length is read back WHOLE (no separator in the middle): the value
    `abcdefgh` spans `ab`, the whole `<SECRET_1>` (`cdef`) and `gh`."""
    r = _registering({"<SECRET_1>": "cdef", "<SECRET_2>": _A})
    assert r.sweep("ab<SECRET_1>gh") == "<SECRET_2>"  # a reverse hit: the run's value is `<SECRET_2>`'s
    assert len(r.mapping) == 2


def test_g9_a_union_that_holds_a_secret_is_a_secret_even_when_an_identifier_comes_first():
    """Design M3 / readiness B3, an input that occurs: `0.5-Xyz9` is a password, `10.100.200.5` an address found by its pattern. The
    address is replaced first (longer, standalone there) and the secret's tail `-Xyz9` stood readable after `<IPV4_1>`. The run starts with
    an IPV4 token but holds a secret: its union is a SECRET (swept in every copy, never restored by the gate's side), not an IPV4."""
    secret = "0.5" + "-Xyz9"
    text = f"password={secret}\nhost 10.100.200.5-Xyz9 up"
    result = R.redact(text)
    assert result.text == "password=<SECRET_1>\nhost <SECRET_2> up"
    assert result.mapping == {"<SECRET_1>": secret, "<IPV4_1>": "10.100.200.5", "<SECRET_2>": "10.100.200.5-Xyz9"}
    r = _registering({"<IPV4_1>": "10.100.200.5", "<SECRET_1>": secret})
    assert r.sweep("10.100.200.5-Xyz9 y") == "<SECRET_2> y"


def test_g9_a_union_whose_value_an_identifier_holds_gets_a_secret_placeholder_of_its_own():
    """Design M3: the run's value `abcdefghijkl` is already held, under TENANT (an identifier: restorable). Reusing it would put two secrets
    under an identifier; a second placeholder of the SECRET kind is registered instead and written."""
    r = _registering({"<TENANT_1>": _A + "ijkl", "<SECRET_1>": _A, "<SECRET_2>": _B})
    assert r.sweep("z" + _A + "ijkl y") == "z<SECRET_3> y"
    assert r.mapping["<SECRET_3>"] == _A + "ijkl" == r.mapping["<TENANT_1>"]


def test_g9_a_union_of_identifiers_only_is_an_identifier():
    r = _registering({"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"})
    assert r.sweep("acme-prod-01-eu") == "<TENANT_3>"
    assert r.mapping["<TENANT_3>"] == "acme-prod-01-eu"


def test_g9_a_union_registers_its_value_only_no_pieces_and_no_written_form():
    """Design M2: a G9 union adds ONE entry (its value): no secret-shaped piece of its readable part, no written form. With pieces, the
    readable tail `hIjK1mNoPq2R` was registered and a hostile chain needed a pass more per link (measured: 3, 4, refused)."""
    s1, s2 = "xY7wV6uT5s" + "R4aB3dE5fG9", "G9" + "hIjK1mNoPq2R"
    r = _registering({"<SECRET_1>": s1, "<SECRET_2>": s2})
    assert r.sweep(s1 + "hIjK1mNoPq2R end") == "<SECRET_3> end"
    assert r.mapping == {"<SECRET_1>": s1, "<SECRET_2>": s2, "<SECRET_3>": s1 + "hIjK1mNoPq2R"}
    assert r._spelled == {}


def _chain(depth: int) -> str:
    """The design critic's chain (M2): S1 ends with `G9`, S2 = `G9hIjK1mNoPq2R`; then `depth` lines `at <the first 12-k characters of
    hIjK1mNoPq2R><a secret starting with the next one>`: with pieces registered, the piece of pass k straddles line k+1's token."""
    tail = "hIjK1mNoPq2R"
    secrets = ["xY7wV6uT5s" + "R4aB3dE5fG9", "G9" + tail]
    rows = []
    for k in range(1, depth + 1):
        x = tail[12 - k] + ["sT7uVw9z", "wQ4eZ5tY", "kL8mN2bV", "pO3iU7yT"][k - 1]
        secrets.append(x)
        rows.append(f"at {tail[: 12 - k]}{x} ;")
    return "\n".join([f"password={s}" for s in secrets] + [f"see {secrets[0]}{tail} end", *rows])


def test_g9_the_hostile_chain_settles_in_two_passes(monkeypatch):
    """Design M2: the chain that needs 3 passes (depth 1), 4 (depth 2) and is refused (depth 3, 4) when unions register pieces settles in
    2 passes here, every depth: a union adds only its own value, which no other place in the text spells."""
    calls: list[int] = []
    real = R._Redactor._overlaps

    def counted(self, out, deadline, work):
        found = real(self, out, deadline, work)
        calls.append(len(found))
        return found

    monkeypatch.setattr(R._Redactor, "_overlaps", counted)
    for depth in range(5):
        calls.clear()
        out = R.redact(_chain(depth)).text
        assert "hIjK1mNoPq2R" not in out and out.count("see <SECRET_") == 1, out
        assert max(_sweep_passes(calls)) <= 2, (depth, calls)


def _sweep_passes(calls: list[int]) -> list[int]:
    """Passes per sweep call from the sequence of `_overlaps` results: a sweep ends at the first pass that found nothing."""
    passes, n = [], 0
    for found in calls:
        n += 1
        if not found:
            passes.append(n)
            n = 0
    return passes


def test_g9_a_redactor_that_may_not_register_masks_an_overlap_with_the_existing_placeholders():
    """The gate's redactor (L-D1 default): it may not add to the map, so the run is masked with the placeholders of the values that cover
    its readable part (`<SECRET_1><SECRET_2>`): nothing readable, nothing invented, the map untouched."""
    r = R._Redactor({"<SECRET_1>": _A, "<SECRET_2>": _B})
    assert r.sweep("x " + _A + "ijkl y") == "x <SECRET_1><SECRET_2> y"
    assert r.sweep("x <SECRET_1>ijkl y") == "x <SECRET_1><SECRET_2> y"  # a placeholder already in the text (an earlier call's)
    assert r.sweep("x <SECRET_1><SECRET_2> y") == "x <SECRET_1><SECRET_2> y"
    assert r.mapping == {"<SECRET_1>": _A, "<SECRET_2>": _B}


def test_g9_a_redactor_that_may_not_register_refuses_an_overlap_an_identifier_must_restore():
    """When a readable character of the run is covered only by an identifier (restored exactly by the gate's side), no existing
    placeholder can stand for it: the text is refused, RedactionError("SpelledOverlap"), NOT an InputTooLarge (a distinct gate code)."""
    r = R._Redactor({"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"})
    with pytest.raises(runmap.RedactionError, match="SpelledOverlap") as caught:
        r.sweep("acme-prod-01-eu")
    assert not isinstance(caught.value, runmap.InputTooLarge)
    assert len(r.mapping) == 2


def test_g9_a_sweep_that_settles_in_the_fourth_pass_is_accepted(monkeypatch):
    r = _registering({"<SECRET_1>": SHORT})
    calls: list[str] = []

    def overlaps(out, deadline, work):
        calls.append(out)
        return [(0, len(out), "SECRET", None)] if len(calls) < defaults.SPELLED_MAX_PASSES else []

    monkeypatch.setattr(r, "_overlaps", overlaps)
    monkeypatch.setattr(r, "_close", lambda out, spans, deadline, work: out)
    assert r.sweep("x <SECRET_1> y") == "x <SECRET_1> y"
    assert len(calls) == defaults.SPELLED_MAX_PASSES == 4


def test_g9_a_sweep_that_has_not_settled_after_four_passes_is_refused(monkeypatch):
    r = _registering({"<SECRET_1>": SHORT})
    calls: list[str] = []

    def overlaps(out, deadline, work):
        calls.append(out)
        return [(0, len(out), "SECRET", None)]

    monkeypatch.setattr(r, "_overlaps", overlaps)
    monkeypatch.setattr(r, "_close", lambda out, spans, deadline, work: out)
    with pytest.raises(runmap.InputTooLarge, match="SpelledNotSettled"):
        r.sweep("x <SECRET_1> y")
    assert len(calls) == 4


def test_g9_a_pass_that_grew_the_map_is_not_the_last(monkeypatch):
    """Converged means: nothing found AND nothing registered in the pass (a union of written forms in `_spelled_sweep` grows the map
    after the build the read-back used). Stubbed: the first body registers a value, the read-back finds nothing: a second pass runs."""
    r = _registering({"<SECRET_1>": SHORT})
    bodies: list[str] = []
    real = r._sweep_once

    def body(out, deadline, work):
        bodies.append(out)
        if len(bodies) == 1:
            r._place("SECRET", "qrstuvwx", "qrstuvwx")
        return real(out, deadline, work)

    monkeypatch.setattr(r, "_sweep_once", body)
    assert r.sweep("x qrstuvwx y") == "x <SECRET_2> y"
    assert len(bodies) == 2


def test_g9_through_redact_a_refusal_is_raised_not_returned(monkeypatch):
    """Class-level stubs (every redactor the call makes): a read-back that always finds a run in a text with a `<`."""

    def never(self, out, deadline, work):
        return [(0, len(out), "SECRET", None)] if "<" in out else []

    monkeypatch.setattr(R._Redactor, "_overlaps", never)
    monkeypatch.setattr(R._Redactor, "_close", lambda self, out, spans, deadline, work: out)
    text = "password=" + SHORT + "qrstu"
    with pytest.raises(runmap.RedactionError, match="SpelledNotSettled"):
        R.redact(text)
    with pytest.raises(runmap.RedactionError, match="SpelledNotSettled"):
        R.redact_many([text, "clean"])
    with pytest.raises(runmap.RedactionError, match="SpelledNotSettled"):
        runmap.redact_text(text, runmap.RunMap())


def test_g9_an_honest_text_settles_in_one_pass(monkeypatch):
    r = _registering(None)
    out = r.find("password=" + SHORT + "qrstu and token=" + SHORT + " and again " + SHORT)
    calls: list[int] = []
    real = r._overlaps
    monkeypatch.setattr(r, "_overlaps", lambda *a: calls.append(1) or real(*a))
    swept = r.sweep(out)
    assert SHORT not in swept and len(calls) == 1, (swept, calls)


def test_g9_the_read_back_is_counted_per_piece_and_refused_before_it_is_built(monkeypatch):
    """Readiness M3: forged copies of a key whose value is long (`x<SECRET_1> ` 20,000 times, a 2,000-character value): read back whole E
    would be 40 million characters. Every piece is counted BEFORE it is appended: with the limit at 100,000 the read-back is refused after
    about 50 pieces and never holds more (peak traced memory under 1 MB; the prototype that counted after building peaked at 56 MB)."""
    long = ("Qz9" * 700)[:2000]
    r = R._Redactor({"<SECRET_1>": long})
    r.sweep("")
    text = "x<SECRET_1> " * 20_000
    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", 100_000)
    tracemalloc.start()
    try:
        with pytest.raises(runmap.InputTooLarge, match="SpelledWorkTooMuch"):
            r._overlaps(text, None, [0])
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 1_000_000, peak
    with pytest.raises(runmap.InputTooLarge, match="SpelledWorkTooMuch"):
        r.sweep(text)


def test_g9_the_read_back_reads_the_deadline(monkeypatch):
    """Readiness M5: the read-back reads the clock each time the work count passes a multiple of 1,024 (the body is stubbed so that it
    reads none; the gate's redactor registers nothing, so no `_build` reads it either). A spent deadline refuses at the first reading; a
    future one returns the text masked (mutant G9-14)."""
    r = R._Redactor({"<SECRET_1>": _A, "<SECRET_2>": _B})
    r.sweep("")
    text = " ".join(["w<SECRET_1>ijkl"] * 200)  # read back: about 3,400 characters
    monkeypatch.setattr(r, "_sweep_once", lambda out, deadline, work: out)
    readings = _stepping_clock(monkeypatch)
    with pytest.raises(runmap.InputTooLarge, match="InputTooLarge"):
        r.sweep(text, 0.5)
    assert readings["n"] == 1
    assert r.sweep(text, 1e9) == " ".join(["w<SECRET_1><SECRET_2>"] * 200)


def test_g9_the_read_back_counts_its_pieces_its_finder_passes_and_its_occurrences():
    """Design M5: the units of one read-back, exactly: one per character of E (`x abcdefghijkl y`, 16), one per character per finder pass
    (one finder: 16), one per occurrence found (`abcdefgh`, `efghijkl`: 2). The union's characters are counted by `_close` (mutant G9-16)."""
    r = R._Redactor({"<SECRET_1>": _A, "<SECRET_2>": _B})
    r.sweep("")
    assert len(r._finders) == 1 and not r._slow
    work = [0]
    assert [s[:2] for s in r._overlaps("x <SECRET_1>ijkl y", None, work)] == [(2, 16)]
    assert work == [16 + 16 + 2]


def test_g9_the_read_back_costs_about_two_sweeps_of_the_text_it_reads():
    """Design M5 / readiness M1: the cookie log of 300 prefix lengths, its copies x 4 (the shape the scan's ratio test uses). The read-back
    of the swept text costs one finder pass per finder group over E, about what a sweep of the raw text it stands for costs (measured 2.1
    times, 0.21 s against 0.10 s on the test machine); a read-back that walked every token's value again per occurrence is far over it."""
    log = _cookie_log(300)
    probe = "\n".join([_copies_of(log)] * 4)
    r = R._Redactor(None)
    r.find(log)
    r.sweep("")
    swept = r._sweep_once(probe, None, [0])
    raw = R._PLACEHOLDER.sub(lambda m: r.mapping.get(m.group(1), m.group(1)), swept)
    read_back = _best_cpu(lambda: r._overlaps(swept, None, [0]))
    r._overlaps = lambda *a: []
    plain = _best_cpu(lambda: r.sweep(raw))
    assert plain > 0.015, plain
    assert read_back < 4 * plain + 0.01, (read_back, plain)


def test_g9_a_long_value_beside_readable_text_is_read_back_only_the_reach_deep():
    """Found by the whole suite on the prototype (tests/test_k5_fixes4.py, 1.2 s -> 40 s): `x` x 262,143 + ` ` is one HIGHENTROPY token and a
    space; read back whole, the finder tried the 262,143-character value at every position of a periodic E (quadratic). A run is read back
    at most `defaults.SPELLED_READBACK_REACH` (1,024) characters deep on each side that touches readable text."""
    r = R._Redactor({"<HIGHENTROPY_1>": "x" * 200_000})
    r.sweep("")
    work = [0]
    assert r._overlaps("<HIGHENTROPY_1> ", None, work) == []
    reach = defaults.SPELLED_READBACK_REACH
    assert work == [2 * (1 + reach + 1)], work  # E = a separator, the last 1,024 `x`, the space: built, then one finder pass


def test_g9_an_overlap_deeper_than_the_reach_is_not_looked_for_a_stated_limit():
    """STATED LIMIT (section 11): a value that overlaps a token by more than `SPELLED_READBACK_REACH` characters is not looked for: its
    readable tail stays. Pinned so that a change of the reach is looked at."""
    base = "".join(f"{n:04x}Qz" for n in range(200))  # 1,200 characters, not periodic
    tail = "TAIL" + "1234"
    r = _registering({"<SECRET_1>": base, "<SECRET_2>": base[100:] + tail})
    assert r.sweep(base + tail) == "<SECRET_1>" + tail  # the overlap is 1,100 characters deep in <SECRET_1>
    near = _registering({"<SECRET_1>": base, "<SECRET_2>": base[200:] + tail})
    assert near.sweep(base + tail) == "<SECRET_3>"  # 1,000 deep: found
```
### 7.5 Fail-before (measured: the edits of 7.1-7.4 applied to the `head` archive, tests only)
`uv run --all-extras --group test pytest -q -n 3 -m "not perf" tests/test_redact_settle_loop.py tests/test_runmap_enforce_map.py
tests/test_model_gate.py tests/test_redact_context_after_sweep.py` on `head`+tests: `30 failed, 443 passed`. The 30, with the reason:
| test | reason on the base |
|---|---|
| test_g9_an_overlap_completed_only_in_a_later_round_is_masked_whole | `AssertionError: xyz<BEARER_1>` (round 3 unchanged) |
| test_g9_two_overlapping_values_in_raw_text_are_masked_whole | `assert '<SECRET_1>ijkl' == '<SECRET_3>'` |
| test_g9_the_raw_overlap_through_redact_redact_many_and_redact_text | `assert 'password=<SE...SECRET_1>ijkl' == 'password=<SE...ee <SECRET_3>'` |
| test_g9_every_key_of_the_map_is_read_back_whoever_wrote_it_and_nothing_else | `assert 'x <SECRET_1>ijkl y' == 'x <SECRET_3> y'` |
| test_g9_a_short_run_of_tokens_is_read_back_whole | `assert 'ab<SECRET_1>gh' == '<SECRET_2>'` |
| test_g9_a_union_that_holds_a_secret_is_a_secret_even_when_an_identifier_comes_first | `assert 'password=<SE...V4_1>-Xyz9 up' == 'password=<SE...<SECRET_2> up'` |
| test_g9_a_union_whose_value_an_identifier_holds_gets_a_secret_placeholder_of_its_own | `assert 'z<SECRET_1>ijkl y' == 'z<SECRET_3> y'` |
| test_g9_a_union_of_identifiers_only_is_an_identifier | `assert '<TENANT_1>-eu' == '<TENANT_3>'` |
| test_g9_a_union_registers_its_value_only_no_pieces_and_no_written_form | `assert '<SECRET_1>hIjK1mNoPq2R end' == '<SECRET_3> end'` |
| test_g9_the_hostile_chain_settles_in_two_passes | `AttributeError: type object '_Redactor' has no attribute '_overlaps'` |
| test_g9_a_redactor_that_may_not_register_masks_an_overlap_with_the_existing_placeholders | `assert 'x <SECRET_1>ijkl y' == 'x <SECRET_1><SECRET_2> y'` |
| test_g9_a_redactor_that_may_not_register_refuses_an_overlap_an_identifier_must_restore | `DID NOT RAISE RedactionError` |
| test_g9_a_sweep_that_settles_in_the_fourth_pass_is_accepted, ..._has_not_settled_after_four_passes_is_refused, test_g9_an_honest_text_settles_in_one_pass, test_g9_the_read_back_is_counted_per_piece_and_refused_before_it_is_built, test_g9_the_read_back_counts_its_pieces_its_finder_passes_and_its_occurrences | `AttributeError: ... has no attribute '_overlaps'` |
| test_g9_a_long_value_beside_readable_text_is_read_back_only_the_reach_deep | `AttributeError: ... has no attribute '_overlaps'` |
| test_g9_an_overlap_deeper_than_the_reach_is_not_looked_for_a_stated_limit | its second assertion: `assert '<SECRET_1>TAIL1234' == '<SECRET_3>'` (the first, the limit itself, holds at the base) |
| test_g9_through_redact_a_refusal_is_raised_not_returned | `AttributeError: type object '_Redactor' has no attribute '_overlaps'` |
| test_g9_a_pass_that_grew_the_map_is_not_the_last, test_g9_the_read_back_reads_the_deadline, test_g9_the_read_back_costs_about_two_sweeps_of_the_text_it_reads | `AttributeError: ... has no attribute '_sweep_once'` |
| test_trap3_a_partial_overlap_of_two_secret_values_is_masked_with_their_placeholders | `assert '<SECRET_1>ef' == '<SECRET_1><SECRET_2>'` |
| test_trap3_an_overlap_an_identifier_must_restore_refuses_the_text | `DID NOT RAISE RedactionError` |
| test_b1_a_partial_overlap_is_masked_with_both_placeholders_in_what_is_sent | `assert '<SECRET_1>ef' == '<SECRET_1><SECRET_2>'` |
| test_b1_an_overlap_an_identifier_must_restore_refuses_the_call_as_mask_refused | `DID NOT RAISE UnmaskedInput` |
| test_b1_a_held_back_value_cut_by_an_overlap_refuses_the_call_as_held_value_left | `DID NOT RAISE HeldValueLeft` |
| test_5000_compound_secrets_at_the_size_cap_the_trie_walk_is_not_dict_misses | `AttributeError: ... has no attribute '_overlaps'` (the edited control; green on the build) |
| test_d8_every_test_the_module_docstring_names_exists | the model_gate docstring of the base names the deleted enforce pin (green once 7.3's docstring edit is in) |
On `proto` (the design + the same test edits): the four files `473 passed` (base: 449 collected; -2 settle pins, -2 gate pins, +23, +2, +3).

## 8. Phases and commands (one complete command per phase; `uptime` first, wait while the load is over 6; `-n 3` at most)
Order: L-D1 decided BEFORE phase 1 (the gate tests change in phase 1: the gate lane's owner approves 7.3 and the model_gate docstring).
- Phase 0 (no code). `git rev-parse HEAD`; derive the anchors by NAME, never by line:
  `grep -n "    def sweep(\|    def _spelled_sweep(\|    def _place_union(\|    def _place(\|    def _build(\|    def __init__(\|^def redact(\|^def redact_many(\|^_MAX_NESTING = \|^SPELLED_MAX_WORK = " src/hadavin_sdk/guard/redact.py src/hadavin_sdk/defaults.py`.
  If G7 round 7 has landed: its `settle` and `_spell` edits are kept as they are; `_place`'s `derived` goes on the signature it has then.
  If G8 has landed: its edit of the line `segment = _replace_standalone(segment, original, placeholder)` is inside `sweep`'s body; it moves
  with that body into `_sweep_once` unchanged.
  `uv run --all-extras --group test python handover/core-c/evidence/g9_cases.py .` -> the "base" column of section 0.
  Copy the tests of 7.1-7.4 in; `uv run --all-extras --group test pytest -q -n 3 -m "not perf" tests/test_redact_settle_loop.py tests/test_runmap_enforce_map.py tests/test_model_gate.py tests/test_redact_context_after_sweep.py`
  -> expected red EXACTLY the 30 of 7.5 (`30 failed, 443 passed`).
- Phase 1 (code: section 4 in redact.py, `SPELLED_MAX_PASSES` in defaults.py, the model_gate and runmap docstrings of 7.3; the tests are
  already in). Command: the phase 0 pytest command -> GREEN: `473 passed`, 0 failed. Phase 1 is one commit; nothing is red at its end.
  (Measured on `proto` without the test edits: `4 failed` exactly: `test_the_scan_does_not_depend_on_how_many_distinct_prefix_lengths_are_registered`,
  `test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit`, `test_stated_limit_partial_overlap_leaves_a_tail`,
  `test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent`; that is why the edits come with the code.)
- Phase 2 (the wide redactor and gate list): `uv run --all-extras --group test pytest -q -n 3 -m "not perf and not live" tests/test_redact*.py tests/test_runmap*.py tests/test_model_gate*.py tests/test_k1b*.py tests/test_s6_approvals.py tests/warden_port`
  -> GREEN: measured on proto `3417 passed, 3 skipped, 4 xfailed` (before the reach was added; the reach's own runs: 9.5). Then `uv run --all-extras --group test ruff format src tests && uv run --all-extras --group test ruff check src tests`.
- Phase 3 (the whole suite, once, at a load under 3): `uv run --all-extras --group test pytest -q -n 3 -m "not perf and not live" tests`
  -> expected 0 failed (see 9.5 and 14 for what the drafter could and could not run). Perf: `uv run --all-extras --group test pytest -q -p no:xdist -m perf tests/test_redact_settle_loop.py tests/test_k5_perf.py tests/test_redact_fold_budget.py`.
- Phase 4 (mutants): `uv run --all-extras --group test python tests/redact_mutants.py G9-` -> the 16 rows of section 10, all good;
  tests/test_redact_mutants_meta.py's pinned count +16; then the whole runner once: no new BAD.
- Phase 5 (evidence and docs): the scripts below committed under handover/core-c/evidence/ and run once each, raw output in `G9-1.md`;
  section 13's wording; ESCALATIONS E10 RESOLVED; the G7 ticket's two overlap limits replaced.
Evidence scripts (from the drafter's scratch, each takes the tree as argv[1]; the builder fixes the import of `cost.py`'s shapes into
`g9_cost.py` and drops the prototype counters, reading passes by wrapping `_Redactor._overlaps` as the chain test does):
| script | command | expected (measured on proto, section 9) |
|---|---|---|
| g9_cases.py | `uv run --all-extras --group test python handover/core-c/evidence/g9_cases.py .` | the "v2" column of section 0 |
| g9_corpus_diff.py | `... g9_corpus_diff.py . /tmp/g9_corpus.json` (against the base's dump with `g9_cmp.py`) | 1,836 inputs, 0 rows differ in 4 entry points; restore failures 63 = 63 (the corpus' own); 2-pass sweeps 13 |
| g9_fuzz.py | `PYTHONHASHSEED=0 ... g9_fuzz.py . 20000 7 {abc,mixed} {redact,natural,gate}` | 0 leaks, 0 refused, every sweep 1 or 2 passes (9.2) |
| g9_chain.py | `... g9_chain.py .` (and `G9_DERIVED`-style: `_place_union(..., derived=True)` for the comparison) | 2 passes at depths 0-4 |
| g9_cost.py | `... g9_cost.py .` | 9.4's table within the machine's noise; H1 refused `SpelledWorkTooMuch` at 3 MB traced |

## 9. Measurements (`proto` vs `head`, 78a0c8bcf; 4 cores, load 1 to 5 from other sessions; CPU seconds are best of 2 thread-CPU runs)
### 9.1 Cases
Section 0's table (cases2.py), plus: `ab<SECRET_1>gh` (`<SECRET_1>`=`cdef`, `<SECRET_2>`=`abcdefgh`) -> `<SECRET_2>` (the short run read back
whole; base `ab<SECRET_1>gh`); `zabcdefghijkl y` with `<TENANT_1>`=`abcdefghijkl` -> `z<SECRET_3> y` (second placeholder, secret kind; base
`z<SECRET_1>ijkl y`); `acme-prod-01-eu` with two TENANTs -> `<TENANT_3>` (base `<TENANT_1>-eu`); gate: the same -> `SpelledOverlap`; gate
`10.100.200.5-Xyz9 y` -> `<IPV4_1><SECRET_1> y` (base `<IPV4_1>-Xyz9 y`); `held_value_left("SECR<SECRET_2>")` True (base False). v1's D-3
input `10.0.0.5xqzw` -> `10.0.<SECRET_1>` on both (readiness B3 was right: the identifier is touched by `x`, no overlap exists there; the
replacement test is the IPV4-first one). Fold view (L-D5): `password=abcdefgh token=efghijkl see ａbcdefghijkl` ->
`see ａbcd<SECRET_2>` on both: the full-width `ａ` is read as written, so `abcdefgh` does not occur in E.
### 9.2 Pass distribution and random search (`fuzz2.py`, 20,000 inputs each, seed 7; leak = the oracle of the v1 fuzz)
| alphabet | entry | head | v2 (passes per sweep call) |
|---|---|---|---|
| abc, 4-7 | redact (seeded) | 190 leak | 0 leak, 0 refused; {1: 40,000, 2: 191} |
| abc | natural (`password=` lines, redact_many) | 191 leak | 0 leak; {1: 90,737, 2: 191} |
| abc | gate (enforce_map) | 191 leak | 0 leak, 0 refused; {1: 63,819, 2: 190} |
| mixed case + digits, values 8-14 from a 30-char base | redact | 11,827 leak | 0 leak, 0 refused; {1: 40,000, 2: 11,833} |
| mixed | natural | 11,830 leak | 0 leak; {1: 133,283, 2: 11,830} |
| mixed | gate | 11,830 leak | 0 leak, 0 refused; {1: 65,758, 2: 11,830} |
No sweep took 3 passes in the 120,000 inputs; no restore difference and no change by a second `redact` (redact rows). The script's value set
was a `list(set)` (order by hash seed), so these counts move by one or two between runs; the committed script sorts it (`PYTHONHASHSEED=0`
as well). Property corpus (1,836 inputs; `redact`, a second `redact` of the output with its map, `redact_text`, a second `redact_text` of its
output on the same RunMap): outputs byte-identical to the base in all four, restore failures 63 on both (the corpus' own), 9,262 sweep calls:
{1: 9,249, 2: 13} (the 13 runs are in second calls whose input holds keys of the map; each resolved to a reverse hit or to a view the
caller did not choose: no output changed). v1's 9.6 concern (13 hits when every token is read back) is therefore answered without a
written set: the read-back of keys finds them, and they change nothing.
### 9.3 The hostile chain (design M2; `chain.py`; the values are mixed case plus digits, 8+ characters)
S1 = `xY7wV6uT5sR4aB3dE5fG9` (ends with `G9`), S2 = `G9hIjK1mNoPq2R`; line `see S1+hIjK1mNoPq2R end`; then `depth` lines
`at hIjK1mNoPq2R[:12-k] + X_k` with `X_k` a secret starting with the next character (`RsT7uVw9z`, `2wQ4eZ5tY`, `qkL8mN2bV`, `PpO3iU7yT`).
| depth | v1-style (G9 unions register pieces and written form) | v2 |
|---|---|---|
| 0 | 2 passes | 2 passes |
| 1 | 3 passes (`at <SECRET_6> ;`) | 2 passes (`at hIjK1mNoPq2<SECRET_3> ;`) |
| 2 | 4 passes | 2 passes |
| 3 | REFUSED `SpelledNotSettled` (needs a 5th) | 2 passes |
| 4 | REFUSED | 2 passes |
Same through `redact` and `redact_text`; under 3 ms each. So the refusal path IS reachable by a real input when unions register pieces
(v1's design), and is not reached by any input built or searched under v2.
### 9.4 Cost (`cost2.py`, `bound.py`; redact_text with a fresh RunMap at the cap; units = the shared count of one sweep call)
Measured before the reach (4.3) was added; no honest shape below has a value of 1,024 characters or more beside readable text, so the
reach does not change them (it changes H1: E per forged copy 2 x 1,024 + 2 characters instead of 2,002; still refused).
| shape | head s | v2 s | v2 passes | v2 max units per sweep (of 4,000,000) |
|---|---|---|---|---|
| curl -u at cap | 2.16-2.28 | 2.24-2.27 | 1 | 1 |
| password= at cap | 0.86 | 0.93-0.97 | 1 | 550,501 |
| jar 330x64 + copies | 0.40 | 0.59-0.63 | 1 | 569,785 |
| jar 275x128 + copies | 0.40-0.41 | 0.52-0.54 | 1 | 511,498 |
| cookie 300 prefix lengths + copies | 0.26-0.34 | 0.39-0.42 | 1 | 1,029,656 (headroom 3.9x) |
| signed ids 300 + copies | 0.38-0.40 | 0.41-0.42 | 1 | 527,517 |
| 5,000 password=uuid.k_i | 0.94-1.12 | 1.13-1.15 | 1 | 514,997 |
| H1 forged `x<SECRET_1> ` x 30,000, a 2,000-char value | returns, 1.07 s, 3 MB | REFUSED `SpelledWorkTooMuch` after 0.54 s, 3 MB traced (v1: 1.68 s, 56 MB) | - | refused at 4M |
| H2 overlapping pairs to the cap (6,900 `password=`/`token=` pairs, each overlapping in a `see` line) | 1.74 | 2.71-2.83 | {1: 1, 2: 1} | 1,149,314 |
Upper bound in time (`bound.py`: every sweep forced to 4 passes, real bodies and read-backs): jar 330x64 0.58 -> 1.12 s; 5,000 uuid 1.13 ->
1.35 s; H2 forced: refused `SpelledNotSettled` after 2.56 s. Each extra pass costs one body and one read-back of the string (no `_build` when
the map did not grow). Per string per call at most 5 sweeps x 4 passes: on the jar shape about 5 x 1.12 s = 5.6 s if every settle round swept
it with 4 passes, under `REDACT_BUDGET_S` = 6 s only just; past the budget the call is refused (`InputTooLarge`, deadline). Units: the
honest worst is now 1.03 M (cookie: E counted once as built and once per finder pass; 3 finder groups for 300 nested prefixes): L-D3b.
The read-back alone on the cookie probe: 0.21 s against 0.10 s for a sweep of the raw text it stands for (2.1x; `rbcost.py`), 0.03 s for the
body over the swept copies: the read-back costs about what the literal sweep cost on the raw text, which is the price of reading it again.
### 9.5 Suites on `proto` (the design + every test edit of section 7)
- The four files of phases 0-1: `473 passed`; on `head` with the tests: `30 failed, 443 passed` (7.5).
- Phase 2 list, BEFORE the test edits: `4 failed, 3391 passed, 3 skipped, 4 xfailed` (the four of phase 1's note); AFTER them:
  `3417 passed, 3 skipped, 4 xfailed`.
- The whole suite, ONCE (`-m "not perf and not live" -n 3 tests`, 8 min 26 s; load 1 to 6.5: two subset runs of the drafter overlapped it
  by mistake): `9 failed, 14254 passed, 561 skipped, 10 xfailed`. Three are the scratch archive's (not a git checkout):
  `test_ci_gitleaks_scope.py::test_the_gitleaks_config_has_only_narrow_path_allowlists` and `test_repo_rules.py::test_licences_are_proprietary`
  (`git ls-files` exit 128), `test_no_reference_material.py::test_no_vendor_brand_string_is_tracked` (a file of the archive's handover/
  that git would not list). SIX WERE REAL: `test_k5_fixes1.py::test_a_tool_result_is_cut_before_redaction_whatever_the_manifest_cap`,
  `test_k5_fixes4.py::test_a_large_output_cut_at_the_window_is_not_refused_for_its_marker` and
  `test_k5_fixes4.py::test_lengths_around_the_window_are_all_accepted[262131|262132|262133|262144]`: `InputTooLarge` (deadline), 37 to 44 s
  each against 1.1 to 1.3 s on `head` (re-run alone at load 2.6). Cause and fix: 4.3 "Why the REACH". After the fix: those six and the four
  files: `505 passed`; the G9 tests 23 passed. The whole suite was NOT run again after the fix (box rule: once); the builder's phase 3 is.
### 9.6 Mutants (`mut2.py`/`mut3.py` against the G9 tests on proto; each killer run alone, its first `E` line recorded)
16 killed (the rows of section 10, with the first `E` line as the `expect` fragment); G9-6 and G9-15 survived and are equivalent (10).

## 10. Mutants (append at the END of `M` in tests/redact_mutants.py, file `RD`, `test_file="tests/test_redact_settle_loop.py"` unless said; `old` is the text of section 4)
| name | old | new | killer (`only_test`) | expect (first `E` line, measured) |
|---|---|---|---|---|
| G9-1 one pass more than the bound | `for _ in range(defaults.SPELLED_MAX_PASSES):` | `for _ in range(defaults.SPELLED_MAX_PASSES + 1):` | test_g9_a_sweep_that_has_not_settled_after_four_passes_is_refused | `assert 5 == 4` |
| G9-2 the read-back removed | `        spans = self._overlaps(out, deadline, work)\n` | `        spans = []\n` | test_g9_two_overlapping_values_in_raw_text_are_masked_whole | `'<SECRET_1>ijkl' == '<SECRET_3>'` |
| G9-3 the refusal returns the text | `    raise InputTooLarge("SpelledNotSettled")` | `    return out` | test_g9_a_sweep_that_has_not_settled_after_four_passes_is_refused | `DID NOT RAISE InputTooLarge` |
| G9-4 the gate registers | `        if self._may_register:\n            placeholder = self._place_union` | `        if True:\n            placeholder = self._place_union` | test_g9_a_redactor_that_may_not_register_masks_an_overlap_with_the_existing_placeholders | `'x <SECRET_3> y' == 'x <SECRET_1><SECRET_2> y'` |
| G9-5 the pieces of the read-back not counted | `        self._spend(work, len(piece), deadline)  # counted before it is held` | `        self._spend(work, 0, deadline)  # counted before it is held` | test_g9_the_read_back_is_counted_per_piece_and_refused_before_it_is_built | `AssertionError: 49501189` (the traced peak, 49.5 MB) |
| G9-7 the seeded keys not read back | `        if tok in mapping:\n` | `        if tok in mapping and int(tok[:-1].rsplit("_", 1)[1]) > 2:\n` | test_g9_every_key_of_the_map_is_read_back_whoever_wrote_it_and_nothing_else | `'x <SECRET_1>ijkl y' == 'x <SECRET_3> y'` |
| G9-8 the union takes the first token's kind | `kind = next((k for _, k in met if k in SECRET_KINDS), _kind(toks[0][1]))` | `kind = _kind(toks[0][1])` | test_g9_a_union_that_holds_a_secret_is_a_secret_even_when_an_identifier_comes_first | `<IPV4_2> up' == ` |
| G9-9 a weaker reverse hit reused | `if have is not None and (_kind(have) in SECRET_KINDS or kind not in SECRET_KINDS):` | `if have is not None:` | test_g9_a_union_whose_value_an_identifier_holds_gets_a_secret_placeholder_of_its_own | `'z<TENANT_1> y' == 'z<SECRET_3> y'` |
| G9-10 the union registers pieces and its written form | `self._place_union(out[start:end], kind, derived=False)` | `self._place_union(out[start:end], kind, derived=True)` | test_g9_a_union_registers_its_value_only_no_pieces_and_no_written_form | `assert {'<SECRET_1>'` (the map holds the piece) |
| G9-11 converged ignores map growth | `if not spans and len(self.mapping) == size:` | `if not spans:` | test_g9_a_pass_that_grew_the_map_is_not_the_last | `assert 1 == 2` |
| G9-12 a short run cut in the middle | `elif lk + rk >= total:` | `elif False:` | test_g9_a_short_run_of_tokens_is_read_back_whole | `'ab<SECRET_1>gh' == '<SECRET_2>'` |
| G9-13 the gate masks with identifiers too | `secret = [h for h in members if _kind(h[2]) in SECRET_KINDS]` | `secret = members` | test_g9_a_redactor_that_may_not_register_refuses_an_overlap_an_identifier_must_restore | `DID NOT RAISE RedactionError` |
| G9-14 the read-back reads no clock | `if deadline is not None and now // _SPELL_CHECK_EVERY != before // _SPELL_CHECK_EVERY:` | `if False:` | test_g9_the_read_back_reads_the_deadline | `DID NOT RAISE InputTooLarge` |
| G9-16 a finder pass not counted | `        self._spend(work, len(E), deadline)  # one finder pass over E\n` | `` | test_g9_the_read_back_counts_its_pieces_its_finder_passes_and_its_occurrences | `assert [18] == [34]` |
| G9-18 the read-back reach removed | `keep = min(self._longest - 1, defaults.SPELLED_READBACK_REACH)` | `keep = self._longest - 1` | test_g9_an_overlap_deeper_than_the_reach_is_not_looked_for_a_stated_limit | `'<SECRET_3>' == '<SECRET_1>TAIL1234'` |
NOT added: G9-6 `if any(s[4] == "" for s in covered):` -> `if False:` (a separator crossed): SURVIVED, equivalent: the separator is
`\0`, and a rule original holding a NUL has a NUL-free alias key that the body sweeps first (`a<SECRET_9>wxyz` -> `a<SECRET_9><SECRET_1>`
at the base and after G9; pinned in `test_g9_every_key_...`); the check stays as defence. G9-15 (a free-only occurrence counted:
`if all(s[4] is None ...) or all(s[4] ...)` -> `if all(s[4] ...)`): SURVIVED the tests and gave 0 output differences on 40,000 fuzz
inputs (abc and mixed, `PYTHONHASHSEED=0`): equivalent by 4.8's argument; not added (readiness minor: proven by measurement, not by reading).
The `expect` fragments are the first `E` line of each killer run alone on the prototype (`mut3.py`); `tools.mutation_runner` itself was
not run on them (14). Rows keep v1's numbers where they kept their meaning; G9-6, G9-15 and G9-17 are not rows.

## 11. Stated limits after G9
- `redact_many` across strings: a value whose head ends one string and whose tail starts the next is two texts; neither the old nor the new
  code reads across the boundary (and the gate's framing-word limit stands: a value split by a fixed framing word is not seen).
- The reach (L-D6): an overlap deeper than `SPELLED_READBACK_REACH` (1,024) characters into a run of placeholders is not looked for
  (two values overlapping by more than 1,024 characters, e.g. two PEM blocks sharing a long body): the tail of the second stays readable,
  as at the base. Pinned.
- Decoded views (L-D5): an overlap visible only after decoding (an HTML entity `&#49;<IPV4_3>`, a full-width letter `ａbcd<SECRET_2>`, an
  escape) is not read back: G9 reads the text as written and the keys' values as stored.
- Fold and alias spellings (design Nit 1): E holds each key's STORED value; where a token stands for a spelling other than the one written
  (`_withhold` registers the folded spelling; an alias key maps to the placeholder of its written variant), E holds characters the text did
  not have. A value matched across them is a false overlap: it over-masks (a union of real text and that token, one entry). Harmless to
  confidentiality; 0 occurrences in the corpus (outputs identical).
- A partial copy of a secret glued to another token stays readable when no stored value completes across the token (the chain's
  `hIjK1mNoPq2<SECRET_3>`): G9 unions register no pieces, as the base masks values, not their substrings.
- Unions are never rolled back (no journal is open in a sweep); a refused call drops them with its redactor and never writes the RunMap.
- Cross-call completion: a text RETURNED by an earlier call before the value was known (`<SECRET_1>ijkl`, `efghijkl` learned later) is not
  changed after the fact. It is closed where it is read again: the gate reads every key of its snapshot back and masks it before the model
  sees it (`x <SECRET_1><SECRET_2> y`); a later `redact()` over it with the run's map unions it. Where the caller's `neutralise` escapes
  placeholders (untrusted text through `redact_text`), the input's tokens are look-alikes, not keys, and are not read back.
- The gate refuses ONE TEXT, hence the call, when a readable character of a run is covered by an identifier alone
  (`RedactionError("SpelledOverlap")`, code `mask_refused`); a message kept in the run's history refuses every later call that carries it.
- The gate's net (`held_value_left`) now finds a held-back secret cut by an overlap and refuses the call (`held_value_left`, where
  `SECR<SECRET_2>` was sent); its checker can raise `InputTooLarge`, reported as `mask_budget_exceeded`.
- The pass bound: a sweep that needs more than 4 passes is refused (`SpelledNotSettled`); reached only by stubs under this design; a chain
  through a G7 union of written forms (which still registers pieces) or a rule first built in pass 2 could reach it (not reproduced).
- With no deadline (a bare `_Redactor.sweep`): 4M units per sweep call, no total bound (as before).
- A union whose value an identifier already holds gets a second, secret-kind placeholder; the identifier's rule still governs the literal
  sweep of that value's other copies (the base's order), as runmap's E5 rule does at the gate.

## 12. Risks
- Cost: +0.05 to +0.23 s at the cap on the jar/cookie shapes (+20 to 58 %); the honest worst unit count is 1.03 M of 4 M (headroom 3.9x,
  down from 11x in v1's accounting, because finder passes over E are now counted).
- The gate's behaviour changes in a lane that is not core-c's alone (L-D1): what the model sees for an overlap (`<SECRET_1><SECRET_2>` for one
  value) and a new refusal for identifier overlaps.
- Order dependence of placeholder numbers: a union takes the next number of its kind when it is found; deterministic per input.
- Idempotence: a second `redact` of the output changes nothing (measured on 1,836 + 40,000 inputs); `enforce_map` stays idempotent (`_enforce`).

## 13. For SECURITY wording (replaces the two overlap limits of the G7 text)
"Two stored values that overlap in the text (one ends where the other begins), found in the same pass or in later ones, are masked as ONE
value: nothing of either stays readable. The check reads the text with every placeholder of the run's map put back, whoever wrote it, at most
4 times per sweep; a text that does not settle is refused (`SpelledNotSettled`) and nothing of it is shown. At the model gate, which may not
add values to the run's map, the readable rest is covered by the existing placeholders of the secret values (`<SECRET_1><SECRET_2>`); where
only an identifier covers it, the call is refused (`mask_refused`), and so is every later call that carries that text. Someone who can plant
two overlapping identifier values (two host names, two tenant ids) can therefore make the gate refuse every call that holds the overlap as
written; someone who can plant a document can force a refusal of the whole document (fail closed). Not covered: an overlap visible only in a
decoded form of the text (an HTML entity, an escape, a full-width letter), a value split across two strings of one batch or by a framing word,
and a text returned by an earlier call before the second value was known (it is masked when the gate reads it again)."

## 14. Not verified
- The whole suite AFTER the reach fix (its one run was before the fix: 9.5); the phase 2 list after the fix (green before it).
- The mutant `expect` fragments through `tools.mutation_runner` (killers measured with the drafter's runner).
- The perf-marked files on proto (`-m perf`); the settle-loop generator's pass distribution (v1 measured 86,264 sweeps, all 1 pass, on its
  design; v2's suite run passes the generator test, the distribution was not printed).
- G7 round 7 and the E9/Q9 review fixes merged with this design (by reading: no shared lines; `_place`'s signature adjacent).
- Python 3.12; Windows timings; a slower machine near `REDACT_BUDGET_S` with 4-pass sweeps (9.4: 5.6 s computed, not run).

## 15. The findings of G9-review-1.md
| id | verdict | where / why |
|---|---|---|
| R-B1 design prose only, no signatures, tuple shapes, short run, E-to-out map | TAKEN | 4.1-4.6: every function body with signature and return shape; `_overlaps` returns `(start, end, kind, masked)`; the short run read back whole (`lk + rk >= total`, test `..._short_run_...` with the reviewer's `ab<S1>gh`); the segment table is the E-to-`out` map (4.3); refused work raises from `_spend`, nothing returned |
| R-B2 `_written` sites incomplete | TAKEN (superseded) | no written set: a token is read back when it is an exact key of the map (4.3); one test reads back a key the redactor did not write (`<SECRET_1>` given in the text); the 13 v1 hits are measured to change no output (9.2) |
| R-B3 the D-3 test is wrong | TAKEN | measured: `10.0.0.5xqzw` -> `10.0.<SECRET_1>` (no overlap exists); replaced by an input that occurs (`host 10.100.200.5-Xyz9`, 9.1) and the reverse-weaker case; kind rule and `_place_union(union, kind, derived)` specified (4.4, 4.6) and built in the prototype |
| R-M1 phase 1 not green | TAKEN | the test edits come with the code: phase 1 ends `473 passed`; the 4 that would be red without them are named (8) |
| R-M2 gate edits not specified | TAKEN | 7.3: both replacements, three new tests, the held-back rows kept and extended, names and docstrings, the model_gate docstring (d8 pins it), `held_value_left` through `_chunk` -> `mask_budget_exceeded` |
| R-M3 hostile memory not tested | TAKEN | the count is per piece in `put` (4.3); test `..._counted_per_piece_and_refused_before_it_is_built` (limit 100,000, peak traced under 1 MB); H1 at the cap: refused at 3 MB (v1 56 MB); mutant G9-5 has a real old text |
| R-M4 where `_longest` lives | TAKEN | recomputed from `_rules` (alias keys included) in `_build` and on the cached path; the 5-tuple unchanged; consumers listed (4.3) |
| R-M5 rollback, settle, deadline test | TAKEN | 4.7 (no journal, a refused call drops its unions, the RunMap is written only on success); test `..._reads_the_deadline` |
| R-M6 no command for "honest = 1 pass" | TAKEN | evidence scripts with commands and expected counts (8); corpus and fuzz re-run on 78a0c8bcf (9.2) |
| R-M7 test bodies missing | TAKEN | 7.3-7.4 exact code; test 1 pins value and kind, not the number; `redact_many(lines)` with `lines` given; constructors explicit; the class-level stub written out; test 8's `find` given |
| R-M8 phase commands, full suite | TAKEN | one complete command per phase (8); the full suite run once on the prototype: it found a real regression (the quadratic read-back of a long value, six k5 tests), fixed by the reach (4.3) and re-checked on those tests; three archive-only failures named (9.5) |
| R-minor L-D1 owner and blocking | TAKEN | the gate lane approves 7.3 before phase 1 (8) |
| R-minor D-3 build order | TAKEN | D-3 is in the build and the prototype (5) |
| R-minor G9-7 no old/new, no killer | TAKEN | new G9-7 with text and killer (10) |
| R-minor G9-6 `...` and equivalence by reading | TAKEN | exact text; equivalence shown by reason (the NUL alias) and G9-15's by 40,000 inputs; neither row added |
| R-minor fail-before ids | TAKEN | 7.5: 27 ids with reasons |
| R-minor G8b line | TAKEN | `segment = _replace_standalone(segment, original, placeholder)` (3, 8) |
| R-minor InputTooLarge message | TAKEN | `InputTooLarge(RedactionError(RuntimeError))` keeps its argument as the message; `pytest.raises(match=...)` passed on proto for all three codes |
| D-M1 the written set is an allow-list | TAKEN | exact keys (4.3); the cross-call case at the gate measured (`x <SECRET_1>ijkl y` -> masked) and stated (11) |
| D-M2 passes 3+ reachable | TAKEN | the claim deleted; the chain built: 3, 4, refused with pieces; 2 at every depth without (9.3); `derived=False` (4.6); `_build`, finder passes, `_sweep_once` in the bounds (4.9, 9.4) |
| D-M3 union kind | TAKEN | 4.4, 4.6; second placeholder of the secret kind on a weaker reverse hit; tested with inputs that occur |
| D-M4 gate default | TAKEN | mask with existing placeholders; refuse one text for identifiers; the three options compared (6); `held_value_left` raising, cache tuple unchanged |
| D-M5 claims the design does not keep | TAKEN | Goal rewritten to what is built; headroom recomputed with finder passes (3.9x); bodies per string stated; cross-call and `redact_many` limits stated (11) |
| D-Nit1 false overlaps from fold/alias | TAKEN | stated (11) |
| D-Nit2 alias keys, one deadline read, E as one string, re-measure, rollback | TAKEN | `_longest` over `_rules`; the deadline read every 1,024 units of the read-back (one `finditer` is still not interrupted: stated in 4.9); E counted per piece and re-measured (9.4 H1); rollback stated (4.7) |
