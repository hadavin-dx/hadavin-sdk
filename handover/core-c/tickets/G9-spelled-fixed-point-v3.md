# G9 v3: the sweep to a fixed point over the text read back (every KEY of the map put back), at most 4 passes; unions register their value only, counted and capped; the gate masks with existing placeholders and never refuses an overlap; overlaps deeper than the reach found by an anchored check (ORDER 023, escalation E10)

Status: DRAFT v3 (complete) for plan review round 3, the LAST plan round the lead allows, core-c drafter, 2026-11-20. Rewrite of
G9-spelled-fixed-point-v2.md taking every finding of G9-review-2-readiness.md and G9-review-2-design.md (section 15). Nothing is
built in the shared tree. CHANGED in v3 (readiness M1): BASE = cloud/core-c HEAD `b9ca1a268` (G7 round 7 `bff88a7a1`, E9 round 2
`aa3b7ffdf` and Q9 `1bf4f11ba` are all IN it; v2's base 78a0c8bcf and its "G7 round 7 uncommitted" dependency are withdrawn). Every
number of this ticket was measured on clean `git archive b9ca1a268` copies in the drafter's scratch unless it is labelled COMPUTED or
NOT MEASURED: `head` (the base) and `proto` (the base + G9-files/g9_src.diff + G9-files/g9_tests.diff; the two diffs ARE this ticket's
code, section 4 and 7 show the same text). Labels: MEASURED (run, figure recorded), COMPUTED (arithmetic on measured figures), BY READING.
CHANGED in v3 (readiness M3): every script and diff phase 0 and phase 5 need is committed beside this ticket in
handover/core-c/tickets/G9-files/ (list in 8.2); nothing points to the drafter's scratch.
CHANGED in v3 (late, while this was drafted): G8 v5 (`6a852c7d3`) and G10 (`a6484cc7c`) LANDED; HEAD is now `613ee1cae`. So G9 is
the SECOND lander for G8 and its builder applies 3.1 point 2 (the `_joins` diff, 7.6's test, G9-24, `EXPECTED_COUNT = 117`,
tests/test_redact_glued_rest.py in the run list). MEASURED on `git archive 613ee1cae` (scratch `head2`): g9_src.diff, g9_tests.diff and
g9_after_g8_joins.diff apply with `--fuzz=0` (line offsets 1 to 74); `ruff format --check` and `ruff check` clean; WITHOUT pytest (the
box rule allowed one run, spent on `proto`): every G9 test incl. 7.6's, the two enforce tests, the four gate tests, `test_d8_...`, the
mutant meta tests at 117 and G8's tripwire `test_g9_read_back_follows_the_sweeps_joins` pass; G9-24 killed. The pytest figures of 8 and
9.5 are on `proto` (b9ca1a268); the builder's phase 1 run is the first pytest on the G8 + G10 + G9 tree.

## 0. The finding that shapes the design (kept; re-measured on b9ca1a268, `G9-files/g9_cases.py`)
THE PLAIN LOOP DOES NOT CLOSE E10: iterating today's sweep reaches a fixed point at the second pass with the leak intact. The swallowed
characters are hidden by a placeholder, so a pass must read the text WITH THE PLACEHOLDERS PUT BACK. MEASURED (base -> v3):
| case | input | base (every later pass the same) | v3 |
|---|---|---|---|
| (a2) `<SECRET_1>`=`abcdefgh`, `<SECRET_2>`=`efghijkl` | `abcdefghijkl` | `<SECRET_1>ijkl` | `<SECRET_3>` (=`abcdefghijkl`), 2 passes |
| (a1) V=`ab9x`, F1 `<BEARER_1>`=V+`ab`, F2 `<BEARER_2>`=`xyz`+V | `see xyzab9xab end` | `see <BEARER_2>ab end` | `see <SECRET_2> end` (=`xyzab9xab`; CHANGED in v3: kind SECRET, 4.4) |
| (b) F1 registered; `xyz<SECRET_1>ab` swept; then F2 | `xyz<BEARER_1>` | `xyz<BEARER_1>` | `<SECRET_2>` (=`xyzab9xab`) |
| natural, no map | `password=abcdefgh\ntoken=efghijkl\nsee abcdefghijkl` | `...see <SECRET_1>ijkl` (redact, redact_many, redact_text) | `...see <SECRET_3>` all three |
| natural, identifier first | `password=0.5-Xyz9\nhost 10.100.200.5-Xyz9 up` | `host <IPV4_1>-Xyz9 up` | `host <SECRET_2> up` (=`10.100.200.5-Xyz9`) |
| gate `enforce_map` | `x abcdefghijkl y` | `x <SECRET_1>ijkl y` | `x <SECRET_1><SECRET_2> y` (map untouched) |
| gate, two identifiers (CHANGED in v3) | `acme-prod-01-eu`, TENANT `acme-prod-01` / `prod-01-eu` | `<TENANT_1>-eu` | `<TENANT_1><TENANT_2>` (v2: refused `SpelledOverlap`) |
| deeper than the reach (CHANGED in v3) | `<SECRET_1>`= a 1,200-character value B, `<SECRET_2>`= B[100:]+`TAIL1234`, text B+`TAIL1234` | `<SECRET_1>TAIL1234` | `<SECRET_3>` (v2: `<SECRET_1>TAIL1234`, a stated limit) |

## 1. Goal (CHANGED in v3: no reach exception; design M1)
After every `_Redactor.sweep`, no rule original (a stored value or alias key that `_build` made a sweep rule of) occurs in the text READ
BACK (every token that is an exact KEY of the redactor's map put back to its value) covering both a readable character and part of a
token, AT ANY DEPTH into a run of tokens: within `SPELLED_READBACK_REACH` (1,024) characters of the readable text by the finder over the
read-back text, deeper by the anchored check (4.4b) for the rules longer than the reach. A redactor that may register (`redact`,
`redact_many`) registers each such run whole as ONE value (no pieces, no written form; its characters counted before it is built and
capped per call) and replaces it; any other redactor (the gate's `enforce_map` and `held_value_left`'s checker) replaces the run's
readable stretches by the EXISTING placeholders of the values that cover them (a secret's where one covers, else an identifier's) and
never refuses for an overlap. A sweep that has not reached that state after 4 passes is refused (`InputTooLarge("SpelledNotSettled")`),
and so is one whose counted work passes `SPELLED_MAX_WORK` or whose call registers more than `SPELLED_MAX_UNION_CHARS` characters of
unions: fail closed, never returned. E10 (a) and (b) are closed for every text a call reads; the two settle-loop pins and the two gate
pins are replaced. The reach deviation v2 put to the lead (L-D6) is WITHDRAWN: the reach now bounds the cost of the read-back, not what is
found (decision for the lead L-D6' in 6 only covers the fallback).

## 2. Problem (the code at b9ca1a268, by name; unchanged from v2 except the base)
- `_Redactor.sweep`: `_spelled_sweep` (written forms, run-merging union inside ONE scan), then the literal sweep per free segment, longest
  value first; both read only the free text between placeholders.
- (a) the literal sweep replaces the longer value first; a shorter value overlapping it no longer matches what is left (older than G7).
- (b) `_spelled_sweep` in a later round: the earlier form's placeholder covers the part the later form needs.
- `settle` loops "table, then sweep" to a fixed point of TEXT changes (since G7 round 7 it records the map size before the sweeps of every
  round); a text that stops changing with a leak inside is settled by that definition. The gate (`runmap.enforce_map`) loops the same
  sweep while the text changes: the same blind spot (Trap 3, a stated limit).

## 3. Files and dependencies
CHANGED in v3: the exact text of every file change is G9-files/g9_src.diff (source) and G9-files/g9_tests.diff (tests); both apply to
b9ca1a268 with `patch -p1 --fuzz=0` and reproduce `proto` byte for byte (MEASURED: `diff -r` empty after applying them to a fresh archive).
- src/hadavin_sdk/guard/redact.py: `_Redactor.__init__` (four attributes; `_measure_rules()` on the cached path), `_build`
  (`self._measure_rules()` before `self._built_for = ...`), `_place` (`derived` parameter), `_place_union` (takes a kind, counts G9
  unions), `_spelled_sweep` (`shared` work count; its `_place_union` call; its "two OPEN limits" paragraph replaced), `sweep` (the pass
  loop and its header comment), new `_sweep_once` (today's body of `sweep`), new `_ensure_built`, `_measure_rules`, `_spend`,
  `_read_back`, `_overlaps`, `_deep_hits`, `_expand`, `_masked`, `_close`; `redact` and `redact_many` (`r._may_register = True`); module
  `_SEP` and `_out_at` after `_MAX_NESTING`. CHANGED in v3 (readiness M1): NO new import (`bisect_right` is already imported at line 35;
  v2's `import bisect` dropped).
- src/hadavin_sdk/defaults.py: after `SPELLED_MAX_CHARS`: `SPELLED_MAX_PASSES = 4`, `SPELLED_READBACK_REACH = 1024`, CHANGED in v3
  `SPELLED_MAX_UNION_CHARS = 1_000_000`, each with its comment; `SPELLED_MAX_WORK`'s comment: the "Two OPEN limits (E10 ...)" sentence
  replaced by what the count is under G9.
- src/hadavin_sdk/guard/runmap.py: docstrings only: `enforce_map` (the overlap bullet replaced), `held_value_left` (one sentence added).
- src/hadavin_sdk/guard/model_gate.py: the module docstring's overlap bullet only (pinned by `test_d8_every_test_the_module_docstring_names_exists`).
- tests/test_redact_settle_loop.py: the two pins deleted, the two ratio controls edited, the G9 block appended (7.4). CHANGED in v3
  (readiness M1): NO `import tracemalloc` edit (the file imports it at line 27 since G7 round 7).
- tests/test_runmap_enforce_map.py, tests/test_model_gate.py: the two gate pins replaced (7.3).
- tests/redact_mutants.py: 22 rows appended in a new `M += [...]` block before `if __name__`, and `SL` (tests/test_redact_settle_loop.py)
  added to the runner's test list (10). tests/test_redact_mutants_meta.py: `EXPECTED_COUNT = 94` -> `116` (CHANGED in v3, readiness M2).
- handover/core-c/evidence/G9-1.md (phase 5), handover/core-c/ESCALATIONS.md (E10 RESOLVED), handover/core-c/tickets/G7-context-after-sweep.md
  (its two overlap limits replaced by 13).

### 3.1 Merge order with G4 v7, G8 v4 / v5 (CHANGED in v3, readiness M4, design M2/M3; BY READING the tickets, MEASURED where marked)
Default: EITHER ORDER; neither G9 nor G4 nor G8 needs another. The SECOND lander rebases by name and owns the checks below.
- G8 (v5 final, G8-glued-rest-gap-v5.md 8.1; v4's paragraph is superseded by v5's text). Two touch points:
  1. The literal-sweep call. At b9ca1a268 it is `segment = _replace_standalone(segment, original, placeholder)` in the body of `sweep`;
     after G8 it takes a FOURTH argument, `segment = _replace_standalone(segment, original, placeholder, _joins(placeholder))` (wrapped by
     `ruff format`). G9 moves the whole body into `_sweep_once` without touching that line: whichever lands second keeps G8's line as it
     is, inside `_sweep_once`. MEASURED: G8 v5 appendix D then g9 applied by the builder script give a tree whose redact.py has G8's call
     in `_sweep_once` (scratch `g8g9`).
  2. The read-back's standalone rule must be the sweep's. Whichever lands SECOND applies G9-files/g9_after_g8_joins.diff (3 hunks; the
     exact text of G8 v5 8.1, carried here): in `_overlaps`' `add()` the test `E[at - 1 : at] in _ALNUM or E[end : end + 1] in _ALNUM`
     becomes `joins = _joins(rule[1])` (rule[1] is the rule's placeholder, rule[2] its rule object) and `... in joins or ... in joins`;
     the same in `_deep_hits` (`joins = _joins(rules[w][1])`); `_overlaps`' docstring clause "(an identifier only where no ASCII letter or
     digit touches it IN E)" becomes "(an identifier only where no character of `_joins(placeholder)` touches it IN E: an ASCII letter or
     digit; for a PHONE value a digit)". In the same commit: G8 v5's literal G9 test `test_g9_the_read_back_judges_a_phone_copy_by_the_sweeps_joins`
     appended to the G9 block (text in 7.6), mutant G9-24 (10) and `EXPECTED_COUNT` +1 (117); tests/test_redact_glued_rest.py joins the
     phase 1 run list. MEASURED (scratch `g8g9pre` = b9ca1a268 + G8 v5 appendices D/E/A/B + G9 without the edit; `g8g9` = the same + the
     edit): G8's tripwire `test_g9_read_back_follows_the_sweeps_joins` RED on `g8g9pre` (`'x<TENANT_1>32 y'`), GREEN on `g8g9` and on G8
     alone; the 8.1 test body: `x<PHONE_1> y`, `7<TENANT_1>32 y`, map unchanged on `g8g9` (`G9-files/g9_phone.py`); the whole G9 block
     green on `g8g9` (no-pytest runner). If G8 lands second, the G8 builder applies the diff (a G9 region, named in evidence/G8-1.md).
- G4 v7 (G4-P1c-redactor-gaps-v7.md 0.3b, L25, L26):
  1. `_build`: G4 edits the RULES LOOP and the tie-break; G9 adds ONE line, `self._measure_rules()`, right before
     `self._built_for = len(self.mapping)` (after G4's loop either way). `_measure_rules` reads `self._rules` after G4's loop, so G4's rules
     are measured. No other shared line in redact.py; G4 does not touch `sweep`, `_place`, `_place_union`.
  2. ENCODED (design M3): CHANGED in v3 a G9 union that holds a token or an occurrence of ANY secret kind is registered as `SECRET`
     (4.4), never as ENCODED: `place_encoded` stays the ONLY writer of an ENCODED entry. G4 v7 0.3b point 2 ("an ENCODED entry that
     place_encoded did not write") no longer happens.
  3. `SpelledOverlap` is GONE (CHANGED in v3, design M4): G4 v7 0.3b's refusal class paragraph, TB-2.8 maps 2/4, TB-2.11/R8 and L24's
     note read `RedactionError("SpelledOverlap")`; on a tree with G9 v3 they read the masked text. MEASURED on `proto` (G9 v3 alone),
     `enforce_map("x ab-cd-ef y", m)` and the bare `_Redactor(m, None).sweep` give the same: map 1 `{"<TENANT_1>": "cd-ef", "<SECRET_1>":
     "ab-cd"}` and map 2 (the other order) `x <SECRET_1><TENANT_1> y`; maps 3 and 4 (`ab-cd` TENANT, `cd-ef` SECRET, both orders)
     `x <TENANT_1><SECRET_1> y`; the fifth map (TB-2.11's) `x <SECRET_1><TENANT_1> y` both ways. So under G9 v3 those rows are ORDER-
     INDEPENDENT; the second lander writes this column (G4 + G9) and re-runs them with the tie-break in.
  4. The `enforce_map` docstring bullet (runmap.py 730-733): G9 replaces it (3); G4 edits its clause "(the earlier in the map when
     equal)". G9's text names no order. So: if G4 lands first, G9's replacement removes G4's clause with the rest of the bullet and G9's
     builder adds G4's sentence after G9's bullet ("Since G4, an original held under a secret kind and an identifier kind follows the secret
     kind's rule; different originals keep the map's order."); if G9 lands first, G4 adds that sentence after G9's bullet (G4 v7 0.3b's own
     rule). The model_gate.py docstring bullet: G9 replaces it; G8 edits model_gate.py lines 12-14 (other sentences): textual merge only.
  5. L26 (the long ENCODED value read back at every mention): CHANGED in v3, the number REFRESHED (design M1): G4 v7's "29 mentions of
     a 65,536-character value, refused at 30" was measured on v2 BEFORE the reach. MEASURED on b9ca1a268 (`g9_hostile.py "mentions k"`,
     `enforce_map` of `step i see <SECRET_1> now.` x k, a 67,583-character wrapped base64 value under a SECRET stand-in: the kind does not
     change the cost): v2 with the reach refused at 1,000 mentions (4,135,778 units at 1,000; COMPUTED limit about 967); v3: 1,800
     ACCEPTED (3,861,855 units), 1,900 refused (COMPUTED limit about 1,870: about 2,060 units per mention, the finder passes no longer
     counted, the anchor searched once). G4's L26 text and its fallback are G4's to rewrite with this figure.
- `EXPECTED_COUNT` of tests/test_redact_mutants_meta.py: G4 v7 adds no `M` entry (its 0.3 table); G8 v5's mutants live in
  tests/g8_mutants.py (not counted here). So 94 -> 116 is G9's alone; +1 (117) when G8's joins edit lands (G9-24). A lander that finds
  another value sums the added rows.
- E9 / Q9: in the base; no shared line.

## 4. Design (exact; the code below is the text of G9-files/g9_src.diff, `ruff format`ted)
### 4.1 The loop (`sweep`, `_sweep_once`, `_ensure_built`)
`sweep` keeps its header comment; its build block becomes `_ensure_built`, its body (from "# A compound secret found late" to
`return "".join(parts)`) becomes `_sweep_once`, unchanged except `self._spelled_sweep(out, deadline, work)`. `sweep` itself, after the
header comment:
```python
        # G9 (ORDER 023, E10): the body below runs in PASSES (`_sweep_once`); after each, the text is read back with every key of the map
        # put back (`_overlaps`) and each run where a rule original covers a readable character and part of a token is replaced
        # (`_close`). At most `defaults.SPELLED_MAX_PASSES` passes; a text that has not settled is refused, never returned.
        # ONE work count for every pass of this call: spelled scans, read-backs, occurrences, the anchored check, unions
        work = [0]
        for _ in range(defaults.SPELLED_MAX_PASSES):
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
```
- In `sweep`, so every caller gets it: `redact`/`redact_many`'s first sweep, every sweep of `settle`, the gate's `first.sweep`,
  `held_value_left`'s `checker.sweep`, `_built`'s build-only `sweep("")` (no `<`: returns at once).
- CONVERGED = a pass whose read-back found nothing AND that registered nothing.
- An honest text costs ONE pass (MEASURED: corpus 9,249 of 9,262 sweep calls; every honest cost shape, 9.4).

### 4.2 The methods (exact text, between `_spelled_sweep` and `_work_refused`)
```python
    def _ensure_built(self, deadline: float | None) -> None:
        """The build block `sweep` had inline: rebuild the rules when the map grew, under `deadline`."""
        if self._built_for != len(self.mapping):
            self._build_deadline = deadline
            try:
                self._build()
            finally:
                self._build_deadline = None

    def _measure_rules(self) -> None:
        """G9: `_longest` (the longest rule original, alias keys included) and `_long` (those longer than the reach + 1, which only the
        anchored check can find deeper than the reach); set wherever `_rules` is set (`_build`, the cached path of `__init__`)."""
        self._longest = max(map(len, self._rules), default=0)
        self._long = [w for w in self._rules if len(w) > defaults.SPELLED_READBACK_REACH + 1]

    def _spend(self, work: list[int], n: int, deadline: float | None) -> None:
        """G9: add `n` units to the sweep's count; refuse past `defaults.SPELLED_MAX_WORK`; read the deadline each time the count passes a
        multiple of `_SPELL_CHECK_EVERY`."""
        before = work[0]
        work[0] = now = before + n
        if now > defaults.SPELLED_MAX_WORK:
            self._work_refused()
        if deadline is not None and now // _SPELL_CHECK_EVERY != before // _SPELL_CHECK_EVERY:
            self._over_budget(deadline)

    def _read_back(
        self, out: str, deadline: float | None, work: list[int]
    ) -> (
        tuple[
            str,
            list[tuple[int, int, int, int, str | None]],
            list[tuple[int, int, str]],
            list[tuple[int, bool, str]],
        ]
        | None
    ):
        """G9: (E, segments, tokens, deep) or None. E is the text read back; a segment is (E start, E end, out start, out end, what):
        `what` None = free text, a placeholder = a token read back (an exact key of `self.mapping`), "" = a separator (`_SEP`: a token
        that is not a key, or the middle of a long run cut out). A RUN is a maximal sequence of key tokens with no free text between
        them; on each side where it touches free text it keeps its first (left) / last (right) `keep` characters (`self._longest - 1`,
        at most `defaults.SPELLED_READBACK_REACH`); the WHOLE run when those two reach its length; a run that touches free text on
        neither side is one separator. Every piece is counted BEFORE it is appended. `tokens`: every placeholder of `out` as (start,
        end, token). `deep`: for each cut side of a run that touches free text, when some rule is longer than the reach + 1, (the out
        position of the edge, True when the free text is on the right, the anchor: the reach's characters of the run at the edge with
        the free character beside them) for `_deep_hits`. None when no token is read back next to free text."""
        keep = min(self._longest - 1, defaults.SPELLED_READBACK_REACH)
        mapping = self.mapping
        pieces: list[str] = []
        segs: list[tuple[int, int, int, int, str | None]] = []
        toks: list[tuple[int, int, str]] = []
        deep: list[tuple[int, bool, str]] = []
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
                head: list[str] = []
                taken = 0
                for tok, o0, o1 in run:
                    if taken >= lk:
                        break
                    cut = mapping[tok][: lk - taken]
                    put(cut, o0, o1, tok)
                    head.append(cut)
                    taken += len(cut)
                put(_SEP, run[0][1], run[-1][2], "")
                tail: list[tuple[str, int, int, str]] = []
                taken = 0
                for tok, o0, o1 in reversed(run):
                    if taken >= rk:
                        break
                    value = mapping[tok]
                    cut = value[len(value) - min(len(value), rk - taken) :]
                    tail.append((cut, o0, o1, tok))
                    taken += len(cut)
                for cut, o0, o1, tok in reversed(tail):
                    put(cut, o0, o1, tok)
                # a rule longer than the reach + 1 may cover more of the run than was put back
                if self._long:
                    if lk:
                        deep.append((run[0][1], False, out[run[0][1] - 1] + "".join(head)))
                    if rk:
                        deep.append(
                            (
                                run[-1][2],
                                True,
                                "".join(c for c, _, _, _ in reversed(tail)) + out[run[-1][2]],
                            )
                        )
            run.clear()

        last, left = 0, False
        for m in _PLACEHOLDER.finditer(out):  # streamed: no split list of the whole text
            a, b = m.span()
            tok = m.group(1)
            toks.append((a, b, tok))
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
        return ("".join(pieces), segs, toks, deep) if touched else None

    def _overlaps(
        self, out: str, deadline: float | None, work: list[int]
    ) -> list[tuple[int, int, str, str | None]]:
        """G9: [(start, end, kind, masked)], sorted, disjoint. out[start:end] is one run: every occurrence in E (`_read_back`; deeper
        than the reach: `_deep_hits`) of a rule original (an identifier only where no ASCII letter or digit touches it IN E) that covers
        at least one free character AND part of at least one token and no separator, merged when they overlap in `out`; tokens are taken
        whole, free text as far as the occurrences reach. `kind`: SECRET when any token of the run or any occurrence is of a secret kind,
        else the first token's kind. `masked`: only for a redactor that may not register (`_masked`), else None. Units: one per
        character of E (as it is built), one per occurrence; the finder groups and slow values read the deadline, uncounted."""
        if "<" not in out:
            return []
        # a union of written forms in this pass's `_spelled_sweep` grew the map
        self._ensure_built(deadline)
        if not (self._finders or self._slow):
            return []
        rb = self._read_back(out, deadline, work)
        if rb is None:
            return []
        E, segs, toks, deep = rb
        rules = self._rules
        occ: list[tuple[int, int, str]] = []

        def add(word: str, at: int) -> None:
            rule = rules.get(word)
            if rule is None:
                return
            end = at + len(word)
            if rule[2] is not _EVERY_COPY and (
                E[at - 1 : at] in _ALNUM or E[end : end + 1] in _ALNUM
            ):
                return
            occ.append((at, end, word))

        for finder, prefixes in self._finders:
            if deadline is not None:
                # between finder groups: a pass of a finder over E is not counted
                self._over_budget(deadline)
            for m in finder.finditer(E):
                w = m.group(1)
                add(w, m.start())
                for p in prefixes.get(w, ()):
                    add(p, m.start())
        for w in self._slow:
            if deadline is not None:
                self._over_budget(deadline)
            j = E.find(w)
            while j >= 0:
                add(w, j)
                j = E.find(w, j + 1)
        self._spend(work, len(occ), deadline)
        starts = [s[0] for s in segs]
        hits: list[tuple[int, int, str]] = []  # (out start, out end, the occurrence's placeholder)
        for a, b, w in occ:
            i0 = bisect_right(starts, a) - 1
            i1 = bisect_right(starts, b - 1) - 1
            covered = segs[i0 : i1 + 1]
            if any(s[4] == "" for s in covered):
                continue  # crosses a separator
            if all(s[4] is None for s in covered) or all(s[4] for s in covered):
                continue  # free text only (the literal sweep's) or tokens only (nothing readable)
            s0, s1 = segs[i0], segs[i1]
            oa = s0[2] if s0[4] else s0[2] + (a - s0[0])
            ob = s1[3] if s1[4] else s1[2] + (b - s1[0])
            hits.append((oa, ob, rules[w][1]))
        if deep:
            hits += self._deep_hits(out, toks, deep, deadline, work)
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
        result: list[tuple[int, int, str, str | None]] = []
        for start, end, members in groups:
            inside = [(m.start(), m.group(1)) for m in _PLACEHOLDER.finditer(out, start, end)]
            secret = any(_kind(tok) in SECRET_KINDS for _, tok in inside) or any(
                _kind(h[2]) in SECRET_KINDS for h in members
            )
            kind = "SECRET" if secret else _kind(inside[0][1])
            masked = None if self._may_register else self._masked(start, end, inside, members)
            result.append((start, end, kind, masked))
        return result

    def _deep_hits(
        self,
        out: str,
        toks: list[tuple[int, int, str]],
        deep: list[tuple[int, bool, str]],
        deadline: float | None,
        work: list[int],
    ) -> list[tuple[int, int, str]]:
        """G9: the occurrences of the rules longer than the reach + 1 (`self._long`) that reach DEEPER than the reach into a cut run.
        Such an occurrence holds the anchor of its edge (the reach's characters of the run there and the free character beside them),
        so the anchor is searched in the rule (once per distinct anchor and rule: `len(w)` units, `len(anchor)` more per place found); at each
        place the rule is compared whole with the text read back on both sides of the edge (`_expand`; `2 * len(w) + 2` units per
        comparison). One unit per (edge, long rule). Returns hits as `_overlaps` makes them: (out start, out end, placeholder)."""
        reach = defaults.SPELLED_READBACK_REACH
        rules = self._rules
        starts = [t[0] for t in toks]
        found: dict[tuple[str, str], list[int]] = {}
        hits: list[tuple[int, int, str]] = []
        for b, right, anchor in deep:
            for w in self._long:
                self._spend(work, 1, deadline)
                at = found.get((anchor, w))
                if at is None:
                    self._spend(work, len(w), deadline)  # one search of the anchor in the rule
                    at = []
                    j = w.find(anchor)
                    while j >= 0:
                        self._spend(work, len(anchor), deadline)  # a further search starts there
                        at.append(j)
                        j = w.find(anchor, j + 1)
                    found[(anchor, w)] = at
                for j in at:
                    k = j + reach if right else j + 1  # the characters of `w` before the edge
                    self._spend(work, 2 * len(w) + 2, deadline)
                    lt, lch = self._expand(out, toks, starts, b, k + 1, True)
                    rt, rch = self._expand(out, toks, starts, b, len(w) - k + 1, False)
                    if len(lt) < k or len(rt) < len(w) - k:
                        continue  # the text read back ends (or a token that is not a key stands) before the rule would
                    if lt[len(lt) - k :] != w[:k] or rt[: len(w) - k] != w[k:]:
                        continue
                    before, after = (
                        lt[len(lt) - k - 1 : len(lt) - k],
                        rt[len(w) - k : len(w) - k + 1],
                    )
                    if rules[w][2] is not _EVERY_COPY and (before in _ALNUM or after in _ALNUM):
                        continue
                    hits.append(
                        (
                            _out_at(lch, len(lt) - k, False),
                            _out_at(rch, len(w) - k - 1, True),
                            rules[w][1],
                        )
                    )
        return hits

    def _expand(
        self,
        out: str,
        toks: list[tuple[int, int, str]],
        starts: list[int],
        b: int,
        n: int,
        left: bool,
    ) -> tuple[str, list[tuple[int, int, int, bool]]]:
        """G9: up to `n` characters of `out` read back (every key token put back whole) that end at out position `b` (`left`) or start
        there; it stops at a token that is not a key and at the end of the text. Returns (text, chunks): a chunk is (offset in text,
        out start, out end, is a token), in text order. The caller counts the characters (`_deep_hits`)."""
        mapping = self.mapping
        got = 0
        # (piece, out start, out end, token), in walking order
        chunks: list[tuple[str, int, int, bool]] = []
        if left:
            # the last token that starts before b (tokens never straddle b: b is an edge)
            i = bisect_right(starts, b - 1) - 1
            pos = b
            while got < n:
                ta, tb, tok = toks[i] if i >= 0 else (0, 0, "")
                free = out[max(tb, pos - (n - got)) : pos]
                if free:
                    chunks.append((free, pos - len(free), pos, False))
                    got += len(free)
                if got >= n or i < 0 or tok not in mapping:
                    break
                value = mapping[tok]
                piece = value[len(value) - min(len(value), n - got) :]
                chunks.append((piece, ta, tb, True))
                got += len(piece)
                pos, i = ta, i - 1
            chunks.reverse()
        else:
            i = bisect_right(starts, b - 1)  # the first token that starts at or after b
            pos = b
            while got < n:
                ta, tb, tok = toks[i] if i < len(toks) else (len(out), len(out), "")
                free = out[pos : min(ta, pos + (n - got))]
                if free:
                    chunks.append((free, pos, pos + len(free), False))
                    got += len(free)
                if got >= n or i >= len(toks) or tok not in mapping:
                    break
                piece = mapping[tok][: n - got]
                chunks.append((piece, ta, tb, True))
                got += len(piece)
                pos, i = tb, i + 1
        placed: list[tuple[int, int, int, bool]] = []
        off = 0
        for piece, o0, o1, is_tok in chunks:
            placed.append((off, o0, o1, is_tok))
            off += len(piece)
        return "".join(c[0] for c in chunks), placed

    @staticmethod
    def _masked(
        start: int, end: int, toks: list[tuple[int, str]], members: list[tuple[int, int, str]]
    ) -> str:
        """G9, the gate's form of one run: its tokens as they are; each free stretch replaced by the placeholders of a left-to-right cover
        of it by the run's occurrences: at each point the SECRET-kind occurrence that covers it and reaches furthest, else the identifier
        one that does (every free character of a run lies in an occurrence: a run is their union); the same placeholder twice in a row
        written once. The occurrences are walked once, sorted (linear)."""
        members = sorted(members)
        parts: list[str] = []
        # secret? -> (end, placeholder) of the occurrence reaching furthest among those begun so far
        best: dict[bool, tuple[int, str] | None] = {True: None, False: None}
        pos, i = start, 0
        for t0, t1, tok in [(p, p + len(t), t) for p, t in toks] + [(end, end, "")]:
            s = pos
            while s < t0:  # the free stretch [pos, t0)
                while i < len(members) and members[i][0] <= s:
                    _, reach_end, placeholder = members[i]
                    i += 1
                    secret = _kind(placeholder) in SECRET_KINDS
                    if best[secret] is None or reach_end > best[secret][0]:
                        best[secret] = (reach_end, placeholder)
                cover = best[True] if best[True] is not None and best[True][0] > s else best[False]
                if not parts or parts[-1] != cover[1]:
                    parts.append(cover[1])
                s = cover[0]
            if tok:
                parts.append(tok)
            pos = t1
        return "".join(parts)

    def _close(
        self,
        out: str,
        spans: list[tuple[int, int, str, str | None]],
        deadline: float | None,
        work: list[int],
    ) -> str:
        """G9: replace each run of `_overlaps`. A redactor that may register: the run's value registered whole under its kind
        (`_place_union(..., derived=False)`: no written form, no pieces), its characters counted BEFORE the value is built; the rules
        are not rebuilt for it (every copy of its value holds the overlap that made it, which the read-back finds again and
        `_place_union` answers from `reverse`). Any other (the gate's): the run's masked form."""
        pieces: list[str] = []
        last = 0
        for start, end, kind, masked in spans:
            if self._may_register:
                size = (
                    end
                    - start
                    + sum(
                        len(self.mapping.get(m.group(1), m.group(1))) - (m.end() - m.start())
                        for m in _PLACEHOLDER.finditer(out, start, end)
                    )
                )
                self._spend(work, size, deadline)  # the union's value, before it is built
                current = self._built_for == len(self.mapping)
                placeholder = self._place_union(out[start:end], kind, derived=False)
                if current:  # a G9 union needs no rule of its own: no rebuild of the finders for it (design M6)
                    self._built_for = len(self.mapping)
            else:
                placeholder = masked
                self._spend(work, end - start + len(placeholder), deadline)
            pieces += (out[last:start], placeholder)
            last = end
            self.actions += 1
        pieces.append(out[last:])
        return "".join(pieces)
```
Module level, after `_MAX_NESTING = 200`:
```python
_SEP = "\0"  # G9: a separator in the read-back text


def _out_at(chunks: list[tuple[int, int, int, bool]], x: int, end: bool) -> int:
    """G9: the out position of character `x` of a text `_Redactor._expand` built: the start (or, for an `end`, the end) of the token it
    lies in, else its own position (+1 for an `end`)."""
    off, o0, o1, is_tok = chunks[bisect_right([c[0] for c in chunks], x) - 1]
    if is_tok:
        return o1 if end else o0
    return o0 + (x - off) + (1 if end else 0)
```

### 4.3 The read-back (`_read_back`): notes
- A token is read back when it is an EXACT KEY of `self.mapping`, whoever wrote it; any other token is a separator (`_SEP`).
- `keep = min(self._longest - 1, SPELLED_READBACK_REACH)`: an occurrence that covers a readable character on one side of a run has at
  most `_longest - 1` characters inside it; one that covers readable characters on BOTH sides covers the whole run, which is then read
  back whole (`lk + rk >= total`).
- CHANGED in v3: a cut side records `(edge, side, anchor)` in `deep` when some rule is longer than the reach + 1 (`self._long`): the
  anchor is the reach's characters of the run at the edge plus the readable character beside it. `tokens` lists every placeholder of
  `out` for `_expand`.
- Every piece is counted (`_spend`) BEFORE it is appended (memory bounded by the count; test `..._counted_per_piece_...`).
- E-to-`out` map: a free segment maps character for character, a token segment (whole value or cut piece) to the whole token.
- `_longest` and `_long` (CHANGED in v3: `_measure_rules`, both places `_rules` is set): the cached `state` 5-tuple is unchanged.

### 4.4 The overlaps (`_overlaps`) and the KIND (CHANGED in v3, design M3)
- Occurrences of rule originals in E by the finder groups (a slow value by `str.find`), with the literal sweep's standalone rule for an
  identifier (`_ALNUM`; after G8 `_joins(rule[1])`, 3.1), that cover a readable character and a token and no separator; plus the deep
  hits (4.4b); merged into runs.
- KIND: `SECRET` when any token of the run or any occurrence is of a kind in `SECRET_KINDS`; else (identifiers only) the first token's
  kind. ONE fixed secret kind, so the result does not depend on the order of `(position, kind)` and an ENCODED/BEARER/JWT token in a run
  never makes an ENCODED/BEARER/JWT union (v2's "first secret kind met" is withdrawn). G7's unions of written forms keep the first form's
  kind (`_spelled_sweep`'s call `_place_union(out[start:end], _kind(placeholder))`: unchanged behaviour).
- CHANGED in v3 (design M5): a finder pass over E is NOT counted; the deadline is read before each finder group and each slow value.
  Units of `_overlaps`: one per character of E (in `put`), one per occurrence, plus the deep check's and `_close`'s. A comb nested past
  `_MAX_NESTING` splits into up to 64 groups (`_split`); counting E per group made the cost E x (groups + 1) (9.4: 33 groups).
### 4.4b The anchored check (`_deep_hits`, `_expand`; CHANGED in v3, design M1: v2's stated limit closed)
- Only rules longer than the reach + 1 can reach deeper than the reach into a cut run. Such an occurrence holds its edge's anchor (the
  reach's characters of the run at the edge and the readable character beside them), so `w.find(anchor)` over the rule finds every place
  it can start: one search per DISTINCT (anchor, rule) (`len(w)` units, `len(anchor)` more per place found; repeated mentions of a long
  token share it), one unit per (edge, long rule). At each place the rule is compared whole with the text read back on both sides of
  the edge (`_expand`, up to `len(w) + 2` characters; `2 * len(w) + 2` units per comparison); the identifier rule applies at its two outer
  characters; a token that is not a key or the end of the text stops the comparison (no match).
- Linear in the rule per distinct anchor for a non-periodic rule (the anchor occurs at most a few times in it). A PERIODIC long rule
  next to readable text of its own period finds the anchor at many places, each counted: refused `SpelledWorkTooMuch` (test
  `..._periodic_...`; stated in 11). MEASURED: `x` x 262,143 + ` ` (the tests/test_k5_fixes4.py shape): read-back units 263,170, 0.002 s.
### 4.5 The gate's form (`_masked`) and the replacement (`_close`)
- CHANGED in v3 (design M4): `_masked` never returns None: every readable character of a run lies in an occurrence (a run is their
  union), so a cover always exists. At each point the SECRET-kind occurrence that covers it and reaches furthest, else the identifier
  one. `RedactionError("SpelledOverlap")` and the refusal are REMOVED; the result does not depend on the map order (3.1 point 3). The
  price: an identifier-only run (`acme-prod-01-eu`) restores with the shared part twice (`acme-prod-01prod-01-eu`); stated (11). The
  occurrences are walked once, sorted (readiness nit: v2's `max()` per point was O(hits^2)).
- CHANGED in v3 (design B1): `_close` counts the union's VALUE (`end - start` plus, per token, its value length minus its token length)
  through `_spend` BEFORE `_place_union` builds it; the gate's form counts the run and its masked text.
- CHANGED in v3 (design M6): a registered G9 union does not rebuild the finders: when the rules were current before it, `_close` sets
  `_built_for` to the new size. A G9 union needs no rule: every copy of its value holds the overlap that made it, which that text's own
  read-back finds and `_place_union` answers from `reverse` (MEASURED: corpus outputs identical, 9.2; fuzz 0 leaks).
### 4.6 Registration (`_place`, `_place_union`; CHANGED in v3, design B1/M3)
`_place(self, label, full, original, derived=True)`: `derived and` added to its two secret-kind conditions (no written form, no pieces
when False). `_place_union` (exact text):
```python
    def _place_union(self, union: str, kind: str, derived: bool = True) -> str:
        """The placeholder of an overlap: `union` is the text of the whole run (`xyz<SECRET_1>ab`), registered under `kind` as a value of
        its own (its restored text) unless that value has a placeholder already: then that placeholder, whatever its kind (as before G9).
        `derived=False` (G9's unions): the value only, no written form and no pieces; its characters are counted per call
        (`self._union_chars`) and the call is refused past `defaults.SPELLED_MAX_UNION_CHARS` (`InputTooLarge("SpelledUnionTooMuch")`,
        nothing stored by the refused registration)."""
        full = _PLACEHOLDER.sub(lambda p: self.mapping.get(p.group(1), p.group(1)), union)
        if full in self.reverse:
            return self.reverse[full]
        if not derived:
            if self._union_chars + len(full) > defaults.SPELLED_MAX_UNION_CHARS:
                from hadavin_sdk.guard.runmap import InputTooLarge  # runmap imports this module

                raise InputTooLarge("SpelledUnionTooMuch")
            self._union_chars += len(full)
        return self._place(kind, full, union if derived else full, derived)
```
- CHANGED in v3 (design M3): the "second placeholder of a stronger kind" of v2 is DROPPED. A union whose value the map already holds
  gets that placeholder whatever its kind (as G7's `_place_union` always did): `reverse` is never overwritten, one value never has two
  placeholders, runmap's `_rules_conflict` is not made true by G9. Such a value was restorable before G9 already (its standalone copies
  are swept under that identifier): stated in 11.
- CHANGED in v3 (design B1): `_union_chars` counts the characters of every NEW G9 union of the call; past `SPELLED_MAX_UNION_CHARS`
  (1,000,000, the size of `SPELLED_MAX_CHARS`) the call is refused (`InputTooLarge("SpelledUnionTooMuch")`, nothing stored by it). G7's
  unions (`derived=True`) pass `_spell`, which `SPELLED_MAX_CHARS` already limits.
### 4.7 Settle, refusals and rollback (unchanged from v2)
- A G9 union is registered with no journal open: `_rollback` cannot remove it. It counts as map growth for `settle` (every string is
  swept once more; no rebuild, 4.5).
- A refused sweep raises out of `settle` and out of `redact`/`redact_many`; `redact_text` writes the RunMap only after success, so a
  refused call adds NO entry to the run's map.
### 4.8 The number of passes
- With `derived=False` every measured input takes at most 2 passes per sweep (9.2, 9.3). Why 2 (an argument, not a proof; the bound 4
  is a fail-closed margin): pass 1's `_close` replaces each run by ONE token whose value is exactly the run's characters in E; every
  occurrence that made a run lies inside one token; the new values occur in E only where a run was. The gate's masked form changes E
  but keeps the run's outer characters. Where 3 could come from (not reproduced): a G7 union of written forms registered in pass 2 (with
  its pieces) or a rule built only in pass 2. Both end in `SpelledNotSettled` (fail closed) if they chain. CHANGED in v3 (design N2):
  the refusal path is shown reachable only by stubs; no real input reaching it is known.
### 4.9 Bounds (CHANGED in v3: what is counted, design B1/M5/M6)
- Per `sweep` call: at most 4 passes; ONE count (`SPELLED_MAX_WORK` = 4,000,000) for the spelled scans, the read-backs (one unit per
  character of E, one per occurrence), the anchored check, and every union's value. NOT counted: `_build`, the literal sweep, a finder
  or slow-value pass over E (each reads the deadline first).
- Per call: at most `SPELLED_MAX_UNION_CHARS` characters of G9 unions, at most `SPELLED_MAX_CHARS` of written forms.
- Per string per call: at most 1 + `_SETTLE_ROUNDS` = 5 sweeps; a G9 union adds no `_build`.
- With a deadline (every producer path, the gate): the CPU budget bounds the whole; read every 1,024 units, before each finder group and
  slow value, in `_build`, every 32nd free segment and before each value replaced. Not interrupted: one `finditer` of one finder over E,
  one `E.find` loop, one `str.replace`, one `w.find` of an anchor. With no deadline (a bare `_Redactor.sweep`): the count only (stated).
- Memory: E is at most the count; union values at most `SPELLED_MAX_UNION_CHARS` characters per call; the anchored check holds at most
  two expansions of one rule at a time and its positions (each counted).
### 4.10 Docstrings and comments (exact text in g9_src.diff)
`_spelled_sweep` (the "two OPEN limits" paragraph replaced by one saying G9's passes close them), `sweep` (header lines of 4.1),
defaults.py (three new constants' comments; `SPELLED_MAX_WORK`'s E10 sentence replaced), runmap.py `enforce_map` overlap bullet and
`held_value_left` (one sentence: the checker can raise `InputTooLarge`, reported `mask_budget_exceeded`), model_gate.py bullet (7.3).

## 5. Decisions made (drafter)
- D-1 The loop is in `sweep` (all callers). D-2 Converged = read-back found nothing and the map did not grow. D-4 Read back = exact keys.
- D-3 CHANGED in v3: union kind = SECRET when it holds any secret kind, else the first token's; a held value is reused whatever its kind.
- D-5 G9 unions register their value only (`derived=False`), CHANGED in v3: counted before they are built, capped per call, no rebuild.
- D-6 CHANGED in v3: the count holds E, occurrences, the anchored check and unions; finder passes are bounded by the deadline only.
- D-7 CHANGED in v3: the gate masks with existing placeholders, secrets first, identifiers else; no refusal for an overlap.
- D-8 CHANGED in v3: the reach bounds the read-back's cost; deeper overlaps are found by the anchored check (4.4b).

## 6. Decisions for the lead (build default first)
| id | question | default | consequence | fallback | consequence |
|---|---|---|---|---|---|
| L-D1 (CHANGED in v3) | the gate (a redactor that may not register) | MASK the run with existing placeholders: the secret's covering a character where one does, else the identifier's; NEVER refuse for an overlap | Trap 3 closed with no refusal and no map write; the result does not depend on map order (3.1); an identifier-only run restores with the shared part twice (`acme-prod-01prod-01-eu`) | (b) refuse an identifier-only run (v2's default) | a planted identifier pair refuses every call carrying it, and the same pair is masked or refused by map order (design M4) |
| L-D1 approval (CHANGED in v3, readiness M5) | the gate lane approves 7.3 (two pins, three tests, the model_gate docstring) | ASKED before phase 1; IF THE GATE LANE IS SILENT when phase 1 starts, the builder builds the default (no gate CODE changes; only tests and two docstrings) and records "L-D1: default, approval silent at <time>" in evidence/G9-1.md | the gate lane can still choose (b) after the merge: a test edit plus a `_masked` change, one commit | wait for the gate lane | phase 1 blocked |
| L-D2 | the pass bound | 4 | margin of 2 over the measured need | 2 | no margin |
| L-D3 | work count | shared per `sweep` call | honest worst 464,367 units (jar 330x64; headroom 8.6x) | per pass | up to 4 x 4M per sweep |
| L-D3b (CHANGED in v3) | what a read-back unit is | E as built + occurrences (+ the anchored check, unions); finder passes NOT counted, deadline between groups | a 33-group comb: 349,712 units for the cookie probe (v2 counting: 11.9M COMPUTED, refused) | v2's (E per finder pass) | honest texts on a deeply nested map refused (design M5) |
| L-D6' (CHANGED in v3, replaces L-D6: THE REACH DEVIATION) | overlaps deeper than `SPELLED_READBACK_REACH` (1,024) into a run | FOUND: anchored check for rules longer than the reach (4.4b); Goal "closed at any depth" | MEASURED: k5 shape 0.002 s; the deep cases masked (0, 7.4); a periodic long value beside its own period is refused, not walked | the v2 limit: not looked for deeper than 1,024; Goal "closed for overlaps up to the reach" | two long values sharing more than 1,024 characters (PEM bodies) leave the tail readable, as at the base |
| L-D7 (new in v3) | per-call limit on union characters | `SPELLED_MAX_UNION_CHARS` = 1,000,000 | honest H2 (6,900 overlapping pairs) registers 72,780 (13.7x headroom); the planted 130,000-character secret refused after 7 unions (9.4) | 262,144 (one text's cap) | 3.6x headroom on H2; one long secret overlapping two short values refuses |
| L-D5 | an overlap visible only in a decoded view | out of G9 | `&#49;<IPV4_3>`, `ａbcd<SECRET_2>` as today | read the views back too | not designed |

## 7. Acceptance tests (exact text: G9-files/g9_tests.diff)
### 7.1 What is added, deleted and edited
- tests/test_redact_settle_loop.py: the two pins DELETED (7.2); the two ratio controls edited (7.2); the G9 block (7.4, 29 tests, one
  `perf`-marked) appended. It uses the file's `R`, `SHORT`, `defaults`, `runmap`, `pytest`, `re`, `random`, `tracemalloc`,
  `_stepping_clock`, `_best_cpu`, `_cookie_log`, `_copies_of`; no import edit (CHANGED in v3).
- tests/test_runmap_enforce_map.py: 1 pin -> 2 tests; tests/test_model_gate.py: 1 pin -> 4 tests (7.3).
### 7.2 The pins and the controls (as v2)
- DELETED `test_an_overlap_completed_only_in_a_later_round_leaves_the_swallowed_part_readable_a_stated_limit` (replaced by
  `test_g9_an_overlap_completed_only_in_a_later_round_is_masked_whole`) and `test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit`
  (replaced by `test_g9_two_overlapping_values_in_raw_text_are_masked_whole`); the comment `# --- M-B (a): two compound values that overlap
  as RAW text` gains ", closed by G9 (tests in the G9 block)". ESCALATIONS.md E10 names the first pin: replace the name there too.
- `test_5000_compound_secrets_at_the_size_cap_the_trie_walk_is_not_dict_misses` takes `monkeypatch` and stubs `r._overlaps` after its
  count assert; `_swept_cpu` sets `r._overlaps = lambda *a: []` after `r.sweep("")` (both: the scan alone in both runs of the ratio).
### 7.3 The gate tests and the model_gate docstring (exact)
tests/test_runmap_enforce_map.py: `test_stated_limit_partial_overlap_leaves_a_tail` (179-196) is REPLACED by:
```python
def test_trap3_a_partial_overlap_of_two_secret_values_is_masked_with_their_placeholders():
    """Trap 3, closed by G9 (E10). `abcd` and `cdef` are both known and the text holds `abcdef`: neither contains the other, so the sweep
    replaces one and the other's rest stood readable (`<SECRET_1>ef`, `ab<SECRET_2>`: the stated limit pinned here before G9). The text read
    back with the map's placeholders put back still holds the other value across the placeholder; the gate may not add an entry, so the
    readable rest is replaced by the EXISTING placeholder of the value that covers it: `<SECRET_1><SECRET_2>` whatever the map order. The map
    is not written (`_enforce` asserts it) and nothing readable is left. The same for an earlier call's output read with a value learned
    since. A held-back value is not in the main sweep's map, so its rest stays HERE; the gate's net finds it (`held_value_left`)."""
    assert (
        _enforce("abcdef", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"}) == "<SECRET_1><SECRET_2>"
    )
    assert (
        _enforce("abcdef", {"<SECRET_2>": "cdef", "<SECRET_1>": "abcd"}) == "<SECRET_1><SECRET_2>"
    )
    assert (
        _enforce("abcdefg", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdefg"}) == "<SECRET_1><SECRET_2>"
    )
    assert (
        _enforce("x <SECRET_1>ef y", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"})
        == "x <SECRET_1><SECRET_2> y"
    )
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


def test_trap3_an_overlap_of_two_identifiers_is_masked_with_their_placeholders():
    """G9, L-D1 (CHANGED in G9 v3, design M4): a readable character covered only by an identifier is replaced by that identifier's EXISTING
    placeholder: no refusal (v2 refused the text, and which pair refused depended on the map order), the map is not written. Restored,
    the shared part of the two identifiers appears twice (a stated limit of the gate, model_gate's docstring). A secret and an identifier
    give the same text in either map order."""
    identifiers = {"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"}
    assert _enforce("acme-prod-01-eu", identifiers) == "<TENANT_1><TENANT_2>"
    assert _enforce("acme-prod-01 and prod-01-eu", identifiers) == "<TENANT_1> and <TENANT_2>"
    for m in (
        {"<SECRET_1>": "ab-cd", "<TENANT_1>": "cd-ef"},
        {"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd"},
    ):
        assert _enforce("x ab-cd-ef y", m) == "x <SECRET_1><TENANT_1> y", m

```
tests/test_model_gate.py: `test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent` (566-573) is REPLACED by:
```python
def test_b1_a_partial_overlap_is_masked_with_both_placeholders_in_what_is_sent():
    """`abcd` and `cdef` known, `abcdef` in the text: `<SECRET_1><SECRET_2>` is sent (G9; before it `<SECRET_1>ef` was sent, a stated limit)."""
    bound, client, _, sink = build(
        mapping=runmap.RunMap({"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"})
    )
    bound.chat([{"role": "user", "content": "abcdef"}], system="s", route="main")
    assert client.sent[0]["messages"][0]["content"] == "<SECRET_1><SECRET_2>"
    assert sink.codes() == [("ok", None)]


def test_b1_an_overlap_of_two_identifiers_is_sent_masked_with_their_placeholders():
    """G9, L-D1 (CHANGED in G9 v3): two identifiers that overlap in the text (`acme-prod-01`, `prod-01-eu` in `acme-prod-01-eu`): the
    readable rest is replaced by the existing placeholder of the identifier that covers it; the call is sent, no refusal."""
    bound, client, _, sink = build(
        mapping=runmap.RunMap({"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"})
    )
    bound.chat([{"role": "user", "content": "acme-prod-01-eu"}], system="s", route="main")
    assert client.sent[0]["messages"][0]["content"] == "<TENANT_1><TENANT_2>"
    assert sink.codes() == [("ok", None)]


def test_b1_a_net_sweep_that_is_refused_is_reported_as_mask_budget_exceeded(monkeypatch):
    """G9 (readiness nit, v3): the net's checker sweep can raise `InputTooLarge` (its count, the deadline, `SpelledNotSettled`); `_chunk`
    does not catch it, `_enforced` reports it as `mask_budget_exceeded`: nothing is sent."""

    def refused(text, snap):
        raise runmap.InputTooLarge("SpelledNotSettled")

    monkeypatch.setattr(runmap, "held_value_left", refused)
    bound, client, _, sink = build(
        mapping=runmap.RunMap({"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"})
    )
    with pytest.raises(model_gate.MaskBudgetExceeded):
        bound.chat([{"role": "user", "content": "abcdef"}], system="s", route="main")
    assert client.sent == [] and sink.codes() == [("refused", "mask_budget_exceeded")]


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
model_gate.py module docstring, the bullet "- Two known values that overlap in the text ..." (4 lines ending
`E::test_stated_limit_partial_overlap_leaves_a_tail`) is REPLACED by the text in g9_src.diff (it names the two new E tests).
`held_value_left`'s callers: model_gate `_chunk` only; an `InputTooLarge` from its checker reaches `_enforced`'s `except
runmap.InputTooLarge` -> `mask_budget_exceeded` (CHANGED in v3, readiness nit: now PINNED by `test_b1_a_net_sweep_that_is_refused_...`).
### 7.4 The G9 block (exact text in g9_tests.diff; appended to tests/test_redact_settle_loop.py)
| test (prefix `test_g9_`) | pins | mutant |
|---|---|---|
| an_overlap_completed_only_in_a_later_round_is_masked_whole | E10 (b), REPLACES the round 3 pin: round 2 sweeps `xyz<SECRET_1>ab` to `xyz<F1>`; round 3 registers F2 `xyz<SECRET_1>` | - |
| two_overlapping_values_in_raw_text_are_masked_whole | E10 (a), REPLACES the raw pin: `abcdefgh` and `efghijkl` in `abcdefghijkl` (the literal sweep cut the second), and F1 = V+`ab`, F2 = `xyz`+V in a raw  | G9-2 |
| the_raw_overlap_through_redact_redact_many_and_redact_text | The natural input (no seeded map): two secrets found by their keys, then a raw `abcdefghijkl` | - |
| every_key_of_the_map_is_read_back_whoever_wrote_it_and_nothing_else | The read-back puts back a token that is an exact KEY of the map, whoever wrote it (this redactor, an earlier call, the fold scan reusing a placeholder | G9-7 |
| a_short_run_of_tokens_is_read_back_whole | A run whose kept head and tail together reach its length is read back WHOLE (no separator in the middle): the value `abcdefgh` spans `ab`, the whole ` | G9-12 |
| a_union_that_holds_a_secret_is_a_secret_even_when_an_identifier_comes_first | An input that occurs: `0.5-Xyz9` is a password, `10.100.200.5` an address found by its pattern | G9-8 |
| a_union_whose_value_the_map_holds_reuses_that_placeholder_whatever_its_kind | Design M3 (v3): the run's value `abcdefghijkl` is already held, under TENANT | G9-9 |
| a_union_of_identifiers_only_is_an_identifier | (see the code) | - |
| a_union_registers_its_value_only_no_pieces_and_no_written_form | A G9 union adds ONE entry (its value): no secret-shaped piece of its readable part, no written form | G9-10 |
| the_hostile_chain_settles_in_two_passes | The chain that needs 3 passes (depth 1), 4 (depth 2) and is refused (depth 3, 4) when unions register pieces settles in at most 2 passes per sweep her | - |
| a_redactor_that_may_not_register_masks_an_overlap_with_the_existing_placeholders | The gate's redactor (L-D1 default): it may not add to the map, so the run is masked with the placeholders of the values that cover its readable part ( | G9-4 |
| a_redactor_that_may_not_register_masks_an_identifier_overlap_with_the_identifiers_placeholders | Design M4 (v3): a readable character covered only by an identifier is replaced by that identifier's EXISTING placeholder, never a refusal (two identif | G9-13 |
| a_sweep_that_settles_in_the_fourth_pass_is_accepted | (see the code) | - |
| a_sweep_that_has_not_settled_after_four_passes_is_refused | (see the code) | G9-1, G9-3 |
| a_pass_that_grew_the_map_is_not_the_last | Converged means: nothing found AND nothing registered in the pass (a union of written forms in `_spelled_sweep` grows the map after the build the read | G9-11 |
| through_redact_a_refusal_is_raised_not_returned | Class-level stubs (every redactor the call makes): a read-back that always finds a run in a text with a `<`. | - |
| an_honest_text_settles_in_one_pass | (see the code) | - |
| the_read_back_is_counted_per_piece_and_refused_before_it_is_built | Forged copies of a key whose value is long (`x<SECRET_1> ` 20,000 times, a 2,000-character value): read back whole E would be 40 million characters | G9-5 |
| the_count_reads_the_clock_each_time_it_passes_a_multiple_of_1024 | `_spend`, the one count of a sweep call: past `SPELLED_MAX_WORK` it refuses (`SpelledWorkTooMuch`); with a deadline it reads the clock when the count  | G9-14 |
| the_read_back_reads_the_deadline | The read-back reads the clock through the count (the body is stubbed so that it reads none; the gate's redactor registers nothing, so no `_build` read | - |
| the_finder_groups_read_the_deadline_between_them | Design M5 (v3): a finder pass over E is not counted (a map nested past `_MAX_NESTING` splits into up to 64 groups, and counting E once per group refus | G9-16 |
| the_read_back_counts_its_pieces_and_its_occurrences | The units of one read-back, exactly: one per character of E (`x abcdefghijkl y`, 16), one per occurrence found (`abcdefgh`, `efghijkl`: 2); the finder | G9-15 |
| a_union_is_counted_with_its_whole_value_before_it_is_built | Design B1 (v3): `_close` counts the union's VALUE (every token of the run put back), not the run's length in the text: a run of one token of a 1,000-c | G9-17 |
| the_unions_of_one_call_are_limited_in_characters_and_the_call_is_refused | Design B1 (v3): the characters of the unions one call registers are counted (`_union_chars`) and the CALL is refused past `defaults.SPELLED_MAX_UNION_ | G9-18 |
| a_union_does_not_rebuild_the_finders | Design M6 (v3): a G9 union needs no sweep rule (a copy of its value elsewhere holds the overlap that made it; the read-back finds it again and `_place | G9-19 |
| the_read_back_costs_about_two_sweeps_of_the_text_it_reads (perf) | The cookie log of 300 prefix lengths, its copies x 4 (the shape the scan's ratio test uses) | - |
| a_long_value_beside_readable_text_is_read_back_only_the_reach_deep | Found by the whole suite on the v2 prototype (tests/test_k5_fixes4.py, 1.2 s -> 40 s): `x` x 262,143 + ` ` is one HIGHENTROPY token and a space (20,00 | G9-20, G9-23 |
| an_overlap_deeper_than_the_reach_is_found_by_the_anchored_check | Design M1 (v3): a value that overlaps a token by more than `SPELLED_READBACK_REACH` characters is found by the anchored check (`_deep_hits`) and maske | G9-21 |
| a_long_periodic_value_beside_its_own_period_is_refused_by_the_count | The anchored check compares the rule at every place its anchor is found, at every edge; a PERIODIC long value (`x` x 1,100) beside readable text of th | G9-22 |
### 7.5 Fail-before (CHANGED in v3, readiness M1 and nit "27 ids"; MEASURED per test on `head` + g9_tests.diff with the drafter's no-pytest runner, the box rule allowing one pytest)
On `head` + the test diff, these 35 tests fail (every other test of the three files passes; the perf-marked G9 test is not run):
the 28 non-perf G9 tests of 7.4 (13 assertion failures where the base returns the old text, e.g. `xyz<BEARER_1>`, `DID NOT RAISE` for the
periodic one, the rest `AttributeError` for `_overlaps` / `_sweep_once` / `_spend` / `_close` / `SPELLED_*`); the edited control
`test_5000_compound_secrets_at_the_size_cap_the_trie_walk_is_not_dict_misses` (`AttributeError ... '_overlaps'`; green on the build);
`test_trap3_a_partial_overlap_of_two_secret_values_is_masked_with_their_placeholders`, `test_trap3_an_overlap_of_two_identifiers_is_masked_with_their_placeholders`,
`test_b1_a_partial_overlap_is_masked_with_both_placeholders_in_what_is_sent`, `test_b1_an_overlap_of_two_identifiers_is_sent_masked_with_their_placeholders`,
`test_b1_a_held_back_value_cut_by_an_overlap_refuses_the_call_as_held_value_left` (`DID NOT RAISE HeldValueLeft`) and
`test_d8_every_test_the_module_docstring_names_exists` (the base docstring names the deleted pin). GREEN on the base (pins existing
behaviour): `test_b1_a_net_sweep_that_is_refused_is_reported_as_mask_budget_exceeded`. The pytest count on the base is COMPUTED: 35 failed.
### 7.6 When G8 is merged (3.1): the test G8 v5 8.1 gives, appended to the G9 block
```python
def test_g9_the_read_back_judges_a_phone_copy_by_the_sweeps_joins():
    """G8 + G9 (ticket G8 v5, 8.1): the read-back judges a copy by the literal sweep's rule, `redact._joins`: the read-back
    `x` + `4155550132` is a copy of the known PHONE value (G8's sweep replaces it when it is written raw), `7` + it is not."""
    phone = "415" + "555" + "0132"
    r = _registering({"<TENANT_1>": phone[:8], "<PHONE_1>": phone})
    assert r.sweep("x<TENANT_1>32 y") == "x<PHONE_1> y"
    assert r.sweep("7<TENANT_1>32 y") == "7<TENANT_1>32 y"
    assert r.mapping == {"<TENANT_1>": phone[:8], "<PHONE_1>": phone}
```
MEASURED (its body, `g9_phone.py`): green on `g8g9`; on `g8g9pre` the first assert gets `x<TENANT_1>32 y` (red). At the gate the same text
gives `x<TENANT_1><PHONE_1> y` (identifier cover, L-D1).

## 8. Phases and commands (box rule: `uptime` first, wait while the load is over 6; pytest `-n 2` at most)
Order: L-D1 asked before phase 1; silent = default (6). Evidence paths: `F=handover/core-c/tickets/G9-files`.
- Phase 0 (no code). `git rev-parse HEAD`. Base gate: `git archive HEAD | tar -x -C /tmp/g9-base && cd /tmp/g9-base && patch -p1 --fuzz=0 --dry-run < $OLDPWD/$F/g9_src.diff && patch -p1 --fuzz=0 --dry-run < $OLDPWD/$F/g9_tests.diff`
  -> both apply (a line offset is fine; a FAILED hunk: re-derive it by name from section 4, the anchors are
  `grep -n "    def sweep(\|    def _spelled_sweep(\|    def _place_union(\|    def _place(\|    def _build(\|    def __init__(\|^def redact(\|^def redact_many(\|^_MAX_NESTING = \|^SPELLED_MAX_CHARS = " src/hadavin_sdk/guard/redact.py src/hadavin_sdk/defaults.py`).
  If `grep -n "def _joins(" src/hadavin_sdk/guard/redact.py` finds G8: also `patch --dry-run` of `$F/g9_after_g8_joins.diff` after the other two (3.1).
  `uv run --all-extras --group test python $F/g9_cases.py .` -> the "base" column of section 0.
  Fail-before: apply `g9_tests.diff` only in /tmp/g9-base; `uv run --all-extras --group test pytest -q -n 2 -p no:cacheprovider -m "not perf" tests/test_redact_settle_loop.py tests/test_runmap_enforce_map.py tests/test_model_gate.py`
  -> `35 failed`, exactly the ids of 7.5 (COMPUTED count; each id MEASURED red).
- Phase 1 (code + tests, ONE commit): in the worktree `patch -p1 --fuzz=0 < $F/g9_src.diff && patch -p1 --fuzz=0 < $F/g9_tests.diff`
  then (G8 IS in at 613ee1cae) `patch -p1 --fuzz=0 < $F/g9_after_g8_joins.diff`, 7.6's test appended to the G9 block, mutant
  G9-24 appended to the G9 rows and `EXPECTED_COUNT = 117`. Command:
  `uv run --all-extras --group test pytest -q -n 2 -p no:cacheprovider -m "not perf and not live" tests/test_redact*.py tests/test_runmap*.py tests/test_model_gate*.py tests/test_k1b*.py tests/test_s6_approvals.py tests/warden_port tests/test_k5_fixes1.py tests/test_k5_fixes4.py`
  `tests/test_redact_glued_rest.py` (G8 is merged: it is IN the list) -> MEASURED on `proto` (b9ca1a268, without the G8 file):
  `3476 passed, 3 skipped, 4 xfailed in 127.16s`; on 613ee1cae expect that plus G8's file (G8 v5: `419 passed, 26 xfailed` for its
  own run) plus 7.6's test, 0 failed (NOT MEASURED through pytest; header).
  Then `uv run --all-extras --group test ruff format --check src tests && uv run --all-extras --group test ruff check src tests` -> clean (MEASURED).
- Phase 2 (the whole suite, once, at a load under 3): `uv run --all-extras --group test pytest -q -n 2 -m "not perf and not live" tests`
  -> 0 failed (NOT run by the drafter in v3; v2's one run found the reach regression, now covered by phase 1's k5 files). Perf:
  `uv run --all-extras --group test pytest -q -p no:xdist -m perf tests/test_redact_settle_loop.py tests/test_k5_perf.py tests/test_redact_fold_budget.py`.
- Phase 3 (mutants): `uv run --all-extras --group test python tests/redact_mutants.py G9-` -> the 22 rows of 10 (23 with G9-24), all
  good; then the whole runner once: no new BAD.
- Phase 4 (evidence and docs): run each script of 8.2 once, raw output into evidence/G9-1.md; section 13's wording; ESCALATIONS E10
  RESOLVED; the G7 ticket's two overlap limits replaced.
### 8.2 G9-files (committed with this ticket; each takes the tree as argv[1]; run with `uv run --all-extras --group test python`)
| file | what | expected (MEASURED on proto unless said) |
|---|---|---|
| g9_src.diff, g9_tests.diff | the code and the tests (phase 1) | apply with `--fuzz=0` on b9ca1a268 |
| g9_after_g8_joins.diff | 3.1's edit on a tree with G8 + G9 | 3 hunks; applies on `g8g9pre` |
| g9_probe.py | wraps `sweep` / `_overlaps`: passes and units per sweep | (helper) |
| g9_cases.py | section 0 and 9.1 | the v3 column of 0 |
| g9_fuzz.py | `PYTHONHASHSEED=0 ... g9_fuzz.py . 10000 7 {abc,mixed} {redact,natural,gate}` | 0 leaks, 0 refused, 1 or 2 passes (9.2) |
| g9_chain.py | the hostile chain | 2 passes per sweep at depths 0-4 |
| g9_corpus_diff.py + g9_cmp.py | `... g9_corpus_diff.py <tree> <dump.json>` on the base and the build, then `g9_cmp.py base.json build.json` | 1,836 inputs, 0 rows differ; restore failures 63 = 63; 13 two-pass sweeps |
| g9_shapes.py, g9_cost.py | honest shapes and H1/H2 through `redact_text` | 9.4 table within noise |
| g9_hostile.py | review round 2 shapes: `"planted 10" "planted 300" "planted 1500" "comb 1700 + jar via redact_text" "bundle 1000" "bundle 3000" "curl union" "mentions 1800" "mentions 1900"` | 9.4 |
| g9_comb_groups.py | `... g9_comb_groups.py . 6500` | 33 finders, 349,712 units |
| g9_deep.py | the anchored check's cases | section 0's deep row; k5 shape 263,170 units |
| g9_phone.py | 7.6's body on a G8 + G9 tree | `'x<PHONE_1> y' '7<TENANT_1>32 y' True` |

## 9. Measurements (proto vs head, b9ca1a268; 4 cores, load 0.5 to 6 from other sessions; thread CPU seconds)
### 9.1 Cases: section 0 plus (MEASURED, `g9_cases.py`): `ab<SECRET_1>gh` (`cdef`, `abcdefgh`) -> `<SECRET_2>`; `zabcdefghijkl y` with
`<TENANT_1>`=`abcdefghijkl` -> `z<TENANT_1> y` (CHANGED in v3: the held placeholder, 4.6); `acme-prod-01-eu` with two TENANTs ->
`<TENANT_3>` (registering) and `<TENANT_1><TENANT_2>` (gate); gate `10.100.200.5-Xyz9 y` -> `<IPV4_1><SECRET_1> y`;
`held_value_left("SECR<SECRET_2>")` True; fold view `see ａbcdefghijkl` -> `see ａbcd<SECRET_2>` on both (L-D5).
### 9.2 Random search and corpus (MEASURED; `g9_fuzz.py` 10,000 inputs each, seed 7, `PYTHONHASHSEED=0`)
| alphabet | entry | head | v3 (passes per sweep call) |
|---|---|---|---|
| abc | redact | - (v2 on 78a0c8bcf: leaks in every row) | 0 leak, 0 refused; {1: 20000, 2: 97} |
| abc | natural | - (v2 on 78a0c8bcf: leaks in every row) | 0 leak, 0 refused; {1: 45342, 2: 97} |
| abc | gate | - (v2 on 78a0c8bcf: leaks in every row) | 0 leak, 0 refused; {1: 31934, 2: 97} |
| mixed | redact | 5,938 leak (10,000) | 0 leak, 0 refused; {1: 20000, 2: 5938} |
| mixed | natural | - (v2 on 78a0c8bcf: leaks in every row) | 0 leak, 0 refused; {1: 66794, 2: 5938} |
| mixed | gate | - (v2 on 78a0c8bcf: leaks in every row) | 0 leak, 0 refused; {1: 32883, 2: 5940} |
Property corpus (`g9_corpus_diff.py`, 1,836 inputs, `redact`, a second `redact`, `redact_text`, a second `redact_text`): outputs
byte-identical to the base in all four; restore failures 63 on both (the corpus' own); sweep calls {1: 9,249, 2: 13}, max 19,318 units.
### 9.3 The hostile chain (`g9_chain.py`): depths 0-4 through `redact` and `redact_text`: 2 passes per sweep, at most 610 units, under
3 ms; the line `at hIjK1mNoPq2<SECRET_3> ;` keeps its partial copy (D-5, 11). (v2 measured 3, 4 and refused with pieces registered.)
### 9.4 Cost (CHANGED in v3: base b9ca1a268; units = the largest shared count of one sweep call, g9_probe)
| shape (entry) | head s | v3 s | v3 passes | v3 max units |
|---|---|---|---|---|
| curl -u at cap | 2.26 | 2.23 | {1: 1} | 1 |
| password= at cap | 0.86 | 0.94 | {1: 1} | 288,357 |
| jar 330x64 + copies to cap | 0.43 | 0.59 | {1: 1} | 464,367 |
| jar 275x128 + copies to cap | 0.39 | 0.52 | {1: 1} | 405,677 |
| cookie 300 prefix lengths + copies to cap | 0.25 | 0.38 | {1: 1} | 350,609 |
| signed ids 300 + copies to cap | 0.52 | 0.42 | {1: 1} | 274,878 |
| 5000 password=uuid.k_i (250k) | 1.18 | 1.05 | {1: 1} | 264,998 |
| H1 forged copies of a 2,000-char secret's key | 0.90 | 0.43 InputTooLarge(SpelledWorkTooMuch) | {1: 1} | 4,000,003 |
| H2 overlapping pairs to the cap | 1.55 | 2.35 | {1: 1, 2: 1} | 625,852 |
Review round 2 shapes (MEASURED, `g9_hostile.py`, one run each):
| shape | head | v2 on b9ca1a268 (with the reach) | v3 |
|---|---|---|---|
| design B1 planted: a 130,000-char secret + N lines `<SECRET_1>XY<i>` + N keys `token=<last 5>XY<i>` (`redact`), N = 10 | 2.27 s (N=40), 130,480 chars of map | 5.63 s, 1,430,190 chars of map | REFUSED `SpelledUnionTooMuch` after 2.38 s (the base's own cost 2.27), traced peak 60 MB (= base) |
| the same, N = 300 | - | 39.96 s, 39,135,700 chars of map (601 entries of ~130,000), traced peak 128 MB | REFUSED `SpelledUnionTooMuch`, 2.42 s, 60 MB |
| the same, N = 1,500 | - | REFUSED `SpelledWorkTooMuch` (E alone, 6.2M units) | REFUSED `SpelledWorkTooMuch`, 2.89 s |
| design M5 comb: P[:i]+`Z`, i = 4..1700 (9 finder groups) + the jar at cap (`redact_text`, then `enforce_map`) | 0.94 / 1.52 s | 1.14 / 1.91 s, 2,666,576 units | 1.10 / 1.92 s, 1,386,769 units |
| comb depth 6,500 (33 finder groups), the cookie probe read back (`g9_comb_groups.py`) | - | 11.9M units COMPUTED (349,712 x 34): refused | 349,712 units, 0.31 s |
| design M6 `redact_many`, 1,000 strings with one overlap each | 0.37 s | - | 0.51 s (v3 BEFORE the no-rebuild rule of 4.5: 85.6 s, one `_build` per string) |
| the same, 3,000 strings | 1.08 s | - | 1.86 s; without overlaps 1.12 s |
| design M6 curl -u at cap with one overlap (`redact_text`) | 2.19 s | - | 2.32 s, passes {1: 1, 2: 1}, 526,360 units |
| G4 L26 shape (3.1 point 5), 1,800 / 1,900 mentions | ok | refused at 1,000 | 1,800 ok (3,861,855 units); 1,900 refused |
| a periodic value `x` x 262,143 + 100,000 `x` beside its token (bare sweep, no deadline) | 5.31 s (the literal sweep's quadratic shape, older than G9) | - | REFUSED `SpelledWorkTooMuch` after 9.4 s (the read-back's finder pays the same shape once more; with a deadline both are refused at the budget) |
### 9.5 Suite (CHANGED in v3, ONE pytest run, `-n 2`): phase 1's list on `proto`: `3476 passed, 3 skipped, 4 xfailed in 127.16s`
(the four G9 files, the k5 files of v2's regression, the mutant meta test with the 22 rows, warden_port).
### 9.6 Mutants (CHANGED in v3: measured WITHOUT pytest, box rule): each row applied to a copy of `proto`, its killer run alone by the
drafter's runner: 22 of 22 killed, the failing line holding the row's `expect` (pytest prints `AssertionError: <message>`; every `expect`
is a message the test writes, or `DID NOT RAISE`, so it is machine-independent: readiness nit). `tools.mutation_runner` was NOT run.

## 10. Mutants (CHANGED in v3, readiness M2: 22 rows, every one listed; `Mutant(...)` with explicit `pinned=` as the E9 rows; exact text in g9_tests.diff)
Appended as a new block before `if __name__` of tests/redact_mutants.py; `SL = "tests/test_redact_settle_loop.py"` is defined there
and added to `run_mutants`' test list (`test_file` must be one of the copied tests). `EXPECTED_COUNT` 94 -> 116.
```python
# ---- G9 (ORDER 023, E10): the sweep to a fixed point over the text read back (ticket G9-spelled-fixed-point-v3.md, section 10) ----
# Mutant built directly with an explicit `pinned=` (as the E9 rows; the PREFIX table is not touched). Every `old` occurs once in redact.py.
SL = "tests/test_redact_settle_loop.py"


def g9(name, old, new, killer, expect):
    return Mutant(
        name,
        RD,
        old,
        new,
        expect,
        test_file=SL,
        only_test=killer,
        pinned=f"tests/test_redact_settle_loop::{killer}",
    )


M += [
    g9("G9-1 one pass more than the bound", "for _ in range(defaults.SPELLED_MAX_PASSES):",
       "for _ in range(defaults.SPELLED_MAX_PASSES + 1):",
       "test_g9_a_sweep_that_has_not_settled_after_four_passes_is_refused", "passes 5"),
    g9("G9-2 the read-back removed", "            spans = self._overlaps(out, deadline, work)\n", "            spans = []\n",
       "test_g9_two_overlapping_values_in_raw_text_are_masked_whole", "E10a: the raw overlap is not one entry"),
    g9("G9-3 the refusal returns the text", '        raise InputTooLarge("SpelledNotSettled")', "        return out",
       "test_g9_a_sweep_that_has_not_settled_after_four_passes_is_refused", "DID NOT RAISE"),
    g9("G9-4 the gate registers", "            if self._may_register:\n", "            if True:\n",
       "test_g9_a_redactor_that_may_not_register_masks_an_overlap_with_the_existing_placeholders",
       "gate: not masked with existing placeholders"),
    g9("G9-5 the pieces of the read-back not counted", "self._spend(work, len(piece), deadline)  # counted before it is held",
       "self._spend(work, 0, deadline)  # counted before it is held",
       "test_g9_the_read_back_is_counted_per_piece_and_refused_before_it_is_built", "DID NOT RAISE"),
    g9("G9-7 the seeded keys not read back", "            if tok in mapping:\n",
       '            if tok in mapping and int(tok[:-1].rsplit("_", 1)[1]) > 2:\n',
       "test_g9_every_key_of_the_map_is_read_back_whoever_wrote_it_and_nothing_else",
       "a key given with the text was not read back"),
    g9("G9-8 the union takes the first token's kind", 'kind = "SECRET" if secret else _kind(inside[0][1])',
       "kind = _kind(inside[0][1])",
       "test_g9_a_union_that_holds_a_secret_is_a_secret_even_when_an_identifier_comes_first",
       "the union of an address and a secret is not a SECRET"),
    g9("G9-9 a held value registered again", "        if full in self.reverse:\n            return self.reverse[full]\n        if not derived:",
       "        if not derived:",
       "test_g9_a_union_whose_value_the_map_holds_reuses_that_placeholder_whatever_its_kind",
       "a held value got a second placeholder"),
    g9("G9-10 the union registers pieces and its written form", "self._place_union(out[start:end], kind, derived=False)",
       "self._place_union(out[start:end], kind, derived=True)",
       "test_g9_a_union_registers_its_value_only_no_pieces_and_no_written_form", "the union registered more than its value"),
    g9("G9-11 converged ignores map growth", "if not spans and len(self.mapping) == size:", "if not spans:",
       "test_g9_a_pass_that_grew_the_map_is_not_the_last", "bodies 1"),
    g9("G9-12 a short run cut in the middle", "elif lk + rk >= total:", "elif False:",
       "test_g9_a_short_run_of_tokens_is_read_back_whole", "the short run was cut"),
    g9("G9-13 the gate covers with identifiers first",
       "cover = best[True] if best[True] is not None and best[True][0] > s else best[False]",
       "cover = best[False] if best[False] is not None and best[False][0] > s else best[True]",
       "test_g9_a_redactor_that_may_not_register_masks_an_identifier_overlap_with_the_identifiers_placeholders",
       "an identifier was written where a secret covers"),
    g9("G9-14 the count reads no clock",
       "if deadline is not None and now // _SPELL_CHECK_EVERY != before // _SPELL_CHECK_EVERY:", "if False:",
       "test_g9_the_count_reads_the_clock_each_time_it_passes_a_multiple_of_1024", "DID NOT RAISE"),
    g9("G9-15 the occurrences not counted", "self._spend(work, len(occ), deadline)", "self._spend(work, 0, deadline)",
       "test_g9_the_read_back_counts_its_pieces_and_its_occurrences", "[16]"),
    g9("G9-16 the finder groups read no clock",
       "# between finder groups: a pass of a finder over E is not counted\n                self._over_budget(deadline)",
       "# between finder groups: a pass of a finder over E is not counted\n                pass",
       "test_g9_the_finder_groups_read_the_deadline_between_them", "DID NOT RAISE"),
    g9("G9-17 the union counted by its length in the text", "self._spend(work, size, deadline)  # the union's value, before it is built",
       "self._spend(work, end - start, deadline)  # the union's value, before it is built",
       "test_g9_a_union_is_counted_with_its_whole_value_before_it_is_built", "[17]"),
    g9("G9-18 the unions of a call not limited", "if self._union_chars + len(full) > defaults.SPELLED_MAX_UNION_CHARS:", "if False:",
       "test_g9_the_unions_of_one_call_are_limited_in_characters_and_the_call_is_refused", "DID NOT RAISE"),
    g9("G9-19 a union rebuilds the finders", "                    self._built_for = len(self.mapping)\n            else:",
       "                    pass\n            else:", "test_g9_a_union_does_not_rebuild_the_finders", "builds [1"),
    g9("G9-20 the anchor searched again at every edge", "found[(anchor, w)] = at", "pass",
       "test_g9_a_long_value_beside_readable_text_is_read_back_only_the_reach_deep", "[63079]"),
    g9("G9-21 the anchored check removed", "hits += self._deep_hits(out, toks, deep, deadline, work)", "hits += []",
       "test_g9_an_overlap_deeper_than_the_reach_is_found_by_the_anchored_check", "1100"),
    g9("G9-22 the anchored comparisons not counted", "self._spend(work, 2 * len(w) + 2, deadline)", "self._spend(work, 0, deadline)",
       "test_g9_a_long_periodic_value_beside_its_own_period_is_refused_by_the_count", "DID NOT RAISE"),
    g9("G9-23 the read-back reach removed", "keep = min(self._longest - 1, defaults.SPELLED_READBACK_REACH)",
       "keep = self._longest - 1",
       "test_g9_a_long_value_beside_readable_text_is_read_back_only_the_reach_deep", "[40002]"),
]  # fmt: skip
```
- When G8 is merged (3.1): G9-24 `g9("G9-24 the read-back ignores the sweep's joins", "            joins = _joins(rule[1])  # G8: the literal sweep's rule; a digit only, for a PHONE value\n", "            joins = _ALNUM\n", "test_g9_the_read_back_judges_a_phone_copy_by_the_sweeps_joins", "<PHONE_1>")`
  and `EXPECTED_COUNT = 117`. MEASURED on 613ee1cae (`head2`, no-pytest runner): killed (the first assert gets `x<TENANT_1>32 y`); its
  `expect` `<PHONE_1>` is read from pytest's plain-assert line (`== 'x<PHONE_1> y'`), NOT checked through the runner.
- NOT rows: G9-6 (the separator check, equivalent: a NUL value's NUL-free alias key is swept first; pinned in `test_g9_every_key_...`),
  v2's G9-15 (a free-only occurrence counted; equivalent by measurement). Gaps in the numbering: 6 only (v2's 15-18 renumbered).

## 11. Stated limits after G9 (CHANGED in v3 where marked)
- `redact_many` across strings: a value split across two strings is two texts (as before).
- CHANGED in v3: no reach limit. A PERIODIC long value beside readable text of its own period is refused (`SpelledWorkTooMuch`),
  not walked (fail closed).
- Decoded views (L-D5): an overlap visible only after decoding is not read back.
- Fold and alias spellings: a token whose key stands for a spelling other than the one written can make a false overlap (over-masks).
- A partial copy of a secret glued to another token stays readable when no stored value completes across it (D-5).
- Unions are never rolled back; a refused call drops them and never writes the RunMap.
- Cross-call completion: a text returned before the second value was known is closed where it is read again (the gate, a later `redact`).
- CHANGED in v3: the gate never refuses for an overlap. Where only an identifier covers a readable character it writes that identifier's
  placeholder: restored, an identifier-only run gives the shared part twice (`acme-prod-01prod-01-eu`), and an identifier that covers
  part of a secret's token restores the identifier's whole value (`<TENANT_1><SECRET_1>` for TENANT `ab-cd`, SECRET `cd-ef`: the
  restored `ab-cd` holds `cd`, as every standalone copy of that identifier did before G9).
- CHANGED in v3: a union whose value the map already holds under an identifier is written as that identifier (`z<TENANT_1> y`): the value
  was restorable before G9 already.
- CHANGED in v3: one call registers at most 1,000,000 characters of unions; past it the call is refused (`SpelledUnionTooMuch`): a
  document holding a secret of 130,000 characters that overlaps 8 short values beside its copies is refused (fail closed).
- Held-back values are not keys of the gate's `first.mapping` (design N3): an overlap with a held-back IDENTIFIER is not seen by the
  main sweep; a held-back SECRET is found by the net's checker (`held_value_left`, refused).
- Forged keys at the gate (design N5): the model can write a key it has seen next to text (`acme-<TENANT_2>`); the gate reads it back
  and masks, and a forged key of a long value costs read-back work: a message that repeats it may be refused (`mask_budget_exceeded`)
  in its call and in later calls that carry it.
- A separator character at a cut edge reads as not alphanumeric (design N1): a false standalone occurrence of an identifier, rare,
  over-masks only.
- With no deadline (a bare `_Redactor.sweep`): the count only, no total time bound; finder passes over E uncounted (as before G9 for
  the literal sweep).
- The pass bound 4: reached only by stubs (4.8).

## 12. Risks
- Cost: +0.06 to +0.8 s at the cap (9.4; H2 +0.8 s); honest worst 464,367 units of 4M (8.6x).
- The gate's behaviour changes in a lane that is not core-c's alone (L-D1): what the model sees for an overlap.
- The anchored check is new code (about 110 lines): MEASURED by 4 tests, 4 mutants, the k5 files, the corpus and the fuzz.
- No rebuild for G9 unions (4.5): a later copy of a union value is closed by its own read-back (one pass more for that string).

## 13. For SECURITY wording (CHANGED in v3)
"Two stored values that overlap in the text (one ends where the other begins), found in the same pass or in later ones, are masked as ONE
value: nothing of either stays readable, however deep the overlap reaches into a placeholder. The check reads the text with every
placeholder of the run's map put back, whoever wrote it, at most 4 times per sweep; a text that does not settle, that needs too much work,
or whose overlaps would register too many characters is refused and nothing of it is shown. At the model gate, which may not add values to
the run's map, the readable rest is covered by the existing placeholders of the values that cover it (a secret's first); two overlapping
identifiers are both written as placeholders, so restoring them repeats their shared part. Someone who can plant a document can force a
refusal of the whole document (fail closed). Not covered: an overlap visible only in a decoded form of the text (an HTML entity, an escape,
a full-width letter), a value split across two strings of one batch or by a framing word, and a text returned by an earlier call before the
second value was known (it is masked when the gate reads it again)."

## 14. Not verified
- The whole suite on v3 (phase 2); the perf-marked files; `tools.mutation_runner` on the 22 rows (9.6: killed by the drafter's runner).
- The fail-before COUNT through pytest (each id measured red without pytest; 7.5).
- G4 v7 merged with G9 v3 (BY READING, 3.1; the TB-2.8 column measured on G9 v3 alone, without G4's tie-break).
- G8 + G9 through pytest (the tripwire and the G9 block measured green without pytest on `g8g9`; G8's own 419 tests not run on `g8g9`).
- Python 3.12; Windows; a machine near `REDACT_BUDGET_S`.

## 15. The findings of G9-review-2-readiness.md and G9-review-2-design.md
| id | verdict | where / why |
|---|---|---|
| R-M1 base stale, counts, tracemalloc | TAKEN | base b9ca1a268 (header); G7 r7 dependency dropped; every count re-measured (7.5, 8, 9); no tracemalloc edit (3, 7.1) |
| R-M2 mutants 15 vs 16, EXPECTED_COUNT, `m()` KeyError | TAKEN | 22 rows listed in full (10), `Mutant(...)` with `pinned=`, `SL` in the runner list, 94 -> 116 |
| R-M3 scripts in no repo | TAKEN | G9-files/ (8.2), diffs included; phase 0 runs from them |
| R-M4 merge order with G4 v7 / G8 | TAKEN | 3.1 (G8 v5 final: sweep line with its 4th argument, `_joins` diff, test, mutant, run list; G4: `_build`, ENCODED, SpelledOverlap rows, docstring bullet, L26, EXPECTED_COUNT) |
| R-M5 L-D1 unresolved | TAKEN | 6: asked before phase 1, default if silent, recorded |
| R-nit G9-5 expect not portable / truncation | TAKEN | every expect is a written message or `DID NOT RAISE` (9.6) |
| R-nit G9-17 / gaps / "27 ids" | TAKEN | 10 (gap 6 only), 7.5 (35 ids, listed) |
| R-nit test_runmap_enforce_map.py:616 | TAKEN | no line cite; consumers of the cached tuple unchanged (4.3) |
| R-nit `_sweep_passes` undercounts | TAKEN | `_passes_per_sweep` wraps `sweep` and `_overlaps` (7.4) |
| R-nit `_masked` O(hits^2) | TAKEN | linear walk (4.5) |
| R-nit timing ratio not perf-marked | TAKEN | `test_g9_the_read_back_costs_...` is `@pytest.mark.perf` |
| R-nit held_value_left InputTooLarge not pinned | TAKEN | `test_b1_a_net_sweep_that_is_refused_...` (7.3) |
| R-nit 4.3 long inline docstring | TAKEN | 4.3 is notes; the docstrings are in the code |
| D-B1 unions unbounded | TAKEN | `len(full)` charged before building (G9-17), `SPELLED_MAX_UNION_CHARS` refuses the call (G9-18), planted shape MEASURED (9.4) |
| D-M1 reach 1,024 deviation | TAKEN (option 1) | anchored check (4.4b), measured; Goal closed at any depth; L-D6' gives the lead the fallback; L26 refreshed (3.1) |
| D-M2 `_joins` | TAKEN | 3.1 point 2, diff, test, G9-24, run list; MEASURED on G8 + G9 |
| D-M3 kind / ENCODED / second placeholder | TAKEN | fixed SECRET kind (4.4), second placeholder dropped (4.6) |
| D-M4 identifier refusal order-dependent | TAKEN | masks with the identifier's placeholder, never refuses (4.5), order-independent (3.1 point 3) |
| D-M5 finder-pass counting, deadline between groups | TAKEN | not counted, deadline per group (4.4, G9-16), comb MEASURED (9.4) |
| D-M6 unmeasured shapes | TAKEN | bundle, curl+union, comb measured; the bundle was quadratic (85.6 s) and is fixed by 4.5's no-rebuild rule (G9-19) |
| D-N1 separator at a cut edge | TAKEN | stated (11) |
| D-N2 "two passes everywhere" | TAKEN | 4.8: refusal path shown reachable only by stubs |
| D-N3 held-back values | TAKEN | stated (11) |
| D-N4 G9-5 expect, work pin, ratio flake | TAKEN | portable expects; the unit pins stay (they are the spec of the count, each a mutant's killer); ratio perf-marked |
| D-N5 forged keys at the gate | TAKEN | stated (11, 13) |
