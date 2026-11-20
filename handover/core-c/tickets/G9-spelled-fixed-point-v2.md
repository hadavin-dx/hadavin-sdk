# G9 v2: the sweep to a fixed point over the text read back (every KEY of the map put back), at most 4 passes; unions register their value only; the gate masks with existing placeholders (ORDER 023, escalation E10)

Status: DRAFT v2 (first complete draft; measurements being filled), core-c drafter, 2026-11-20. Rewrite of G9-spelled-fixed-point.md (v1)
taking or contesting every finding of G9-review-1.md (section 15). Nothing is built. Base of every measurement: cloud/core-c 78a0c8bcf
(src identical to d8777d5a7: G7 rounds 3-6, E9 `_OWN_OUTPUT` SECRET-only, Q9 merged). Measured on clean `git archive` copies of 78a0c8bcf in
the drafter's scratchpad (`g9v2/head`, the base; `g9v2/proto`, this design applied by `g9v2/scripts/make_proto2.py`). The shared tree was
not edited and no test was run in it.

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
- src/hadavin_sdk/defaults.py: `SPELLED_MAX_PASSES = 4` after `SPELLED_MAX_WORK`; `SPELLED_MAX_WORK`'s comment (the count is per sweep CALL,
  shared by its passes, and counts the read-back; the "Two OPEN limits (E10)" sentence replaced).
- src/hadavin_sdk/guard/runmap.py: docstrings only: `enforce_map` (the Trap 3 limit bullet replaced), `held_value_left` (it can now find an
  overlap and can raise `InputTooLarge` through the checker's sweep). No code change: `first` and `checker` are bare `_Redactor`s, so they
  take the gate behaviour (`_may_register` False) by default.
- src/hadavin_sdk/guard/model_gate.py: no change (L-D1: an optional distinct code is the gate lane's call).
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
    text it keeps its first (left) / last (right) `self._longest - 1` characters; the WHOLE run when those two reach its length (the short
    run: `ab<cdef>gh` against `abcdefgh`); a run that touches free text on neither side is one separator. Every piece is counted BEFORE it is
    appended. None when no token is read back next to free text (nothing to check: no clock read, no work beyond the pieces)."""
    keep = self._longest - 1
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
  80,000 inputs over `abc` and over mixed-case-plus-digit values of 8 to 14 characters, three entry points each).
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
  pass grows the map; measured worst (section 9.4): [M].
- With a deadline (every producer path: `redact_text`, `redact_many`, `redact`): the call's `REDACT_BUDGET_S` CPU budget bounds the whole;
  read in `_build`, every 1,024 units of the spelled scan AND of the read-back (`_spend`), every 32nd free segment and before each value
  replaced. Not interrupted: one `finditer` of a finder over E, one `E.find` loop of one slow value, one `str.replace`. With no deadline (a
  bare `_Redactor.sweep(text)`): 4M units per sweep, no total bound (stated, as today).
- Memory: E is at most `SPELLED_MAX_WORK` characters (every piece counted before it is appended; test 9 bounds the traced peak); honest
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

## 6. Decisions for the lead (build default first)
| id | question | default | consequence | fallback | consequence |
|---|---|---|---|---|---|
| L-D1 | the gate (a redactor that may not register) | MASK the run with the existing placeholders of the secret values covering its readable part (`<SECRET_1><SECRET_2>`); refuse THAT TEXT (`RedactionError("SpelledOverlap")`, gate code `mask_refused`) only when an identifier alone covers a readable character | Trap 3 closed for secret values with no refusal and no map write; the model sees two tokens where the text had one value; identifier-identifier overlaps refuse the call; the two gate pins become "masked" tests (section 7.3; gate-lane edit) | (b) refuse every overlap (v1's) / (c) skip the check | (b) a planted pair refuses every call carrying it; (c) Trap 3 stays: the tail of a secret readable (see the table below) |
| L-D1b | a distinct gate code for `SpelledOverlap` | none: it is a RedactionError, so `mask_refused` (already distinct from `mask_budget_exceeded`) | no model_gate change | a new `CODE_OVERLAP_REFUSED` in model_gate | a gate-lane edit; the audit row names the cause |
| L-D2 | the pass bound | 4 (`SPELLED_MAX_PASSES`) | margin of 2 over the measured need | 2 | no margin; a chain through a G7 union would refuse |
| L-D3 | work count | shared per `sweep` call | honest worst [M] units | per pass | up to 4 x 4M per sweep |
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
### 7.1 tests/test_redact_settle_loop.py: the G9 block (appended; the file's `R`, `SHORT`, `defaults`, `runmap`, `pytest`, `_stepping_clock`; new imports `tracemalloc` at the top)
[the full code: section 7.4]
### 7.2 The two settle-loop pins
- `test_an_overlap_completed_only_in_a_later_round_leaves_the_swallowed_part_readable_a_stated_limit` (calls `_spelled_sweep`, stays green
  in phase 1) is DELETED and replaced by `test_g9_an_overlap_completed_only_in_a_later_round_is_masked_whole`.
- `test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit` (red in phase 1) is DELETED and replaced by
  `test_g9_two_overlapping_values_in_raw_text_are_masked_whole`; the section comment `# --- M-B (a): ...` becomes `# --- M-B (a), closed by G9 ...`.
### 7.3 The gate pins (phase 2; tests/test_runmap_enforce_map.py, tests/test_model_gate.py)
[filled below]
### 7.4 Code of 7.1
[filled below]

## 8. Phases and commands
[filled below]

## 9. Measurements
[filled below]

## 10. Mutants
[filled below]

## 11. Stated limits after G9
[filled below]

## 12. Risks
[filled below]

## 13. For SECURITY wording
[filled below]

## 14. Not verified
[filled below]

## 15. The findings of G9-review-1.md
[filled below]
