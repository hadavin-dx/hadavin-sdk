# Ticket G4 v3: P1c redactor gaps (base64 view, whole host names, bare numbers written down)

Version 3, written by the core-c drafter (opus tier), 2026-11-20. It replaces tickets/G4-P1c-redactor-gaps-v2.md and takes or
contests every finding of plan review round 2 (tickets/G4-review-2.md); what v2 resolved from round 1 (tickets/G4-review-1.md)
is kept (section A). A builder with no other context builds from this file alone. Nothing is built before plan review round 3
is clean.

Base of every claim in this file: HEAD of `cloud/core-c` at 193605f (2026-11-20), read and run read-only by the drafter (the
probe and a few in-process checks with `.venv/bin/python -B`; no file of the repository was changed, no test file was run
through pytest). HEAD already holds G7 fix round 2 / MJ-B (`_Redactor.settle` redact.py:1141-1176, `_SETTLE_ROUNDS` = 4
redact.py:1751; commit a2b6311 "work in progress of the running G7 fix round 2 builder, NOT verified"). The G7 round 3 fix and
the gate round 4 fix are being built in other worktrees (/tmp/core-c-g7r3, /tmp/core-c-gate4) and are NOT in HEAD. Every line
number below is HEAD's. Phase 0 (section 12) re-checks every number on the real base before any code.

## 0. Package line
- Package: G4 (plan item P1c, ORDER 006 item 1). Path class: redaction. Extended review: yes (no round cap).
- Lead rule (unchanged): build only a gap that a failing input proves. A gap with no failing input is cut.
- Depends on, merged first: G0, the integration with G7 (d95a727), G7 fix round 2 (MJ-B, already in HEAD), then the G7 round 3
  fix and the gate round 4 fix (both open). G4 starts from the first commit of `cloud/core-c` that holds all of them; its sha is
  the base sha of the evidence. If either open fix changes `runmap.redact_text`, `_decoded_masks`, `_views`, `_Redactor.settle`,
  the HOSTNAME entry or `approvals/channel.py` `clean`/`settled`, Phase 0 stops and reports (section 12).
- Source of the code: our own (rung 5), with Python stdlib `base64` as the decoder. Nothing is copied from another repository.
- Target: `src/hadavin_sdk/guard/runmap.py` (the scan refactor and the base64 step), `src/hadavin_sdk/guard/redact.py` (kind
  ENCODED, `place_encoded`, the host patterns, the `_build` tie-break, docstring), `src/hadavin_sdk/defaults.py` (8 constants,
  SPINE's file, its own commit), `src/hadavin_sdk/approvals/channel.py` (one kind added to `_ASSIGNMENT_KINDS`, L10),
  `src/hadavin_sdk/approvals/gate.py` (one comment).

## 1. Problem in plain words
A secret that is only written in base64 reaches the model today: the redactor has no decoded view. Short base64 blobs
(under 40 characters) pass unchanged, alone, in a sentence, in JSON, after `data=`. Wrapped base64 passes when the lines are
short, or leaves its last line readable. Long unbroken blobs are already masked whole by HIGHENTROPY.
A private host name is masked only up to its private suffix: `db01.corp.example` becomes `<HOSTNAME_1>.example`.
A bare host label after `host`, an underscore label and `[.]` dots are not masked at all.
Bare numbers without a label are not masked. That is an accepted decision (order 64 item 4); it is written down and pinned.

### What the probe proves (evidence/p1c_probe.py, seed 20261120)
The drafter re-ran the probe unchanged on HEAD 193605f (in-process, output in the drafter's scratch only). Main 51c9fc4 numbers
(evidence/P1c-probe.md) in brackets where they differ.
| gap | rows | leaked on HEAD | G4 result |
|---|---|---|---|
| 1 base64 (1b 128 + 1c 14) | 142 | 52 (1b 48, 1c 4; the same row numbers as on main) | 52 closed; 85 unchanged; 5 change kind HIGHENTROPY to ENCODED (no leak before or after) |
| 2 host names | 44 | 26: 12 whole, 14 part [28] | 19 closed; 3 stay (limits: rows 10, 15, 16); 4 kept on purpose (6, 8, 9, 42); 18 already masked stay |
| 3 bare numbers | 43 | 24 not masked, 2 in part (the same rows as on main) | not a gap: written down and pinned by class |
| 4 hostile corpus | - | - | CUT: the old 30-row corpus is not in this repository |
Rows 31 (`dial bücher.internal now`) and 41 (full-width dots) leak on main and do NOT leak on HEAD: the fold scan (G1/G3) masks
row 31 as `dial <HOSTNAME_1> now` and withholds row 41's line (`[line withheld: look-alike text hid a protected value]
<HOSTNAME_1>`). So G4 closes 19 host rows, not v2's 21.
"Prototype" below means the drafter's scratch code of v2 on a clean export of main 51c9fc4 (no fold scan, no MJ-B). Every
prototype number is marked; the builder re-measures on the base.

## 2. Decision D1 and the central refactor
### 2.1 Where the step plugs in, and why not "decode before pass 1"
G4 edits `redact_text` and `_Redactor`'s label registry; MJ-B is already in HEAD and the open G7 round 3 fix may edit the same
functions, so G4 starts after it (section 0). The base64 step runs on the cleaned, neutralised input AFTER pass 1, because pass 1
tells it which runs are already masked (HELD, 3.3). Option not taken (round 1's proposal): decode before pass 1 and replace every
unit that decodes. It changes the kind of every blob HIGHENTROPY, BASIC or JWT holds today and cuts a JWT with an e-mail in its
payload into ENCODED segments; it gives up invariant I3. The chosen design pays one more pass 1 only on a text with a hit.

### 2.2 The new private names (all in guard/runmap.py: tests/test_k1b_redaction_layers.py:134-157 pins that every call of
`redact(` / `redact_many(` in src is in guard/runmap.py, so no helper moves out)
```python
@dataclass
class _ScanBudget:
    """The base64 step's budget for ONE redact_text call; the text, every view and every depth share it."""
    started: float           # redact_text's `started` (time.thread_time() at entry); the deadline is
                             # started + defaults.REDACT_BUDGET_S, read when checked, as every other check does
    units: int = 0           # units decoded or masked unread so far (decodable, not held), all views and depths
    decoded_chars: int = 0   # characters of decoded text read so far (len of each _b64_text result)

    def clock(self) -> None: ...          # ONE time.thread_time() read; past the deadline: InputTooLarge
    def take(self, chars: int) -> None: ...  # units += 1, decoded_chars += chars; over B64_MAX_UNITS or
                                             # B64_MAX_DECODED_CHARS: InputTooLarge

class _B64Unit(NamedTuple):
    start: int               # offset in the ANSI-stripped text (see 3.1 point 5)
    end: int
    written: str             # the unit as written, line breaks included: the ENCODED original
    joined: str              # its lines, stripped, joined with nothing between: what _b64_text decodes
    lines: tuple[str, ...]   # its lines as written (stripped), for the held rule

def _scan(text: str, mapping: dict[str, str], cache: dict | None,
          neutralise: Callable[[str], str] | None, budget: _ScanBudget, depth: int) -> tuple[str, dict[str, str]]:
    """The whole of today's redact_text body except the cap, the exception wrapper and the map write: returns the
    output and the new map (the incoming map plus entries). Never writes `mapping`. Recursive through _b64_hits."""

def _pass_one(text: str, mapping: dict[str, str], cache: dict | None,
              neutralise: Callable[[str], str] | None, budget: _ScanBudget, depth: int) -> RedactionResult:
    """redact() of `text`, then the base64 step; on a hit, redact() of the replaced text. Used for the input and
    for every view, at every depth."""

def _b64_units(text: str) -> tuple[str, list[_B64Unit]]:   # (the ANSI-stripped text, its units); (text, []) when no run
def _b64_held(unit: _B64Unit, known: Mapping[str, str]) -> bool
def _b64_text(joined: str) -> str | None                    # section 3.2
def _b64_hits(units: list[_B64Unit], known: dict[str, str], neutralise: Callable[[str], str] | None,
              budget: _ScanBudget, depth: int) -> list[bool]  # section 3.4
def _b64_place(stripped: str, units: list[_B64Unit], placeholders: dict[str, str]) -> str
```
The private signatures are part of the contract: I13 drives a spent deadline and the caps through `_ScanBudget` and
`_pass_one` directly (the public API cannot set a deadline that is already spent at the step).

### 2.3 `redact_text`'s new body (the docstring gains one paragraph, section 11)
1. `_within_cap(text)` (unchanged, before the clock).
2. `started = time.thread_time()` (unchanged line: mutant R1 pins it).
3. `try:` `cache = getattr(mapping, "redact_cache", None)` (stays inside the try: tests/test_runmap_map_write.py m8).
4. `budget = _ScanBudget(started)`; `out, current = _scan(text, mapping, cache, neutralise, budget, 0)`.
5. `except (InputTooLarge, TooDeep): raise` / `except Exception as exc: raise RedactionError(type(exc).__name__) from None`
   (unchanged).
6. The comment block and `mapping.update(current)` / `return out` at four spaces, unchanged (gate mutants R3, R3b, R3c pin
   `    mapping.update(current)\n    return out\n` exactly once in runmap.py). A raise anywhere in steps 3-4 leaves `mapping`
   unwritten.

### 2.4 `_scan`, numbered (today's lines 553-588 moved, with two calls replaced)
1. `started = budget.started` (a local of that name, so the existing check lines keep their text).
2. `text = fits_after_nfkc(_clean(text))`; if `neutralise`: `text = fits_after_nfkc(neutralise(text))`. Call this text T.
3. `scan = not T.isascii() or any(c in T for c in "\\%&")`; `views = _views(T) if scan else []`. The views are of T, computed
   BEFORE pass 1 as today (runmap.py:556-557), and NEVER of the replaced text T2 (2.6). Reason (review M6): a view of T2 would
   hold our own `<ENCODED_n>`, and `neutralise_untrusted` would escape it to the look-alike `‹ENCODED_n›` before redaction.
4. `result = _pass_one(T, mapping, cache, neutralise, budget, depth)`; `out, current = result.text, result.mapping`.
5. `if views and time.thread_time() - started > defaults.REDACT_BUDGET_S: raise InputTooLarge("InputTooLarge")` (unchanged
   line, mutant R2).
6. `pairs = _decoded_masks(current, T, started + defaults.REDACT_BUDGET_S) if views else []`. `_decoded_masks` sees T (the
   cleaned, neutralised input: a hit blob is still written in it) and `current` (after the pass on T2: it holds the ENCODED
   entries). An ENCODED original is plain base64 (no `%`, `\`, `&`, ASCII), so `_decoded_masks` skips it before any decode.
7. The neutralised pairs, unchanged.
8. `for view in views:` (one occurrence: p1d_a mutant A16 pins it): the clock check (R3's condition, re-indented, section
   13.3), `neutralise(view)`, `view = _keep_earlier_masks(view, pairs)` (it sees the views of T), then
   `again = _pass_one(view, current, cache, neutralise, budget, depth)`, then the view rule unchanged:
   `if again.mapping != current or _held(again.text) > _held(out): out, current = again.text, again.mapping`.
   In a view the blob that was a hit on T is swept by pass 1 (ENCODED is a secret kind: every copy from 4 characters), so it is
   HELD there and not decoded again; a blob readable only in a view (`\/` slashes, `%3D` padding) is decoded in that view.
9. `return _clean(out), current`.

### 2.5 `_pass_one`, numbered
1. `started = budget.started`.
2. `first = redact(text, mapping=mapping, _cache=cache, _deadline=started + defaults.REDACT_BUDGET_S)` (pass 1 as today, with
   MJ-B's settle; mutant 21's literal `_deadline=started + defaults.REDACT_BUDGET_S` is kept in both redact calls of this
   function, which are the only two in runmap.py, as today).
3. `stripped, units = _b64_units(text)`. With no run (the gate, 3.1 point 1) return `first` here: no clock read, no other call.
4. Drop held units (`_b64_held(u, first.mapping)`, 3.3); for the decision keep one unit per distinct `written` (every copy
   is still replaced in step 8). None left: return `first`.
5. `hits = _b64_hits(units, first.mapping, neutralise, budget, depth)`. No hit: return `first` (output and map byte-identical to
   the base commit's for that text).
6. `base = dict(mapping)` (the INCOMING map: pass 1's additions are dropped, they hold junk such as one HIGHENTROPY entry per
   wrapped line of a blob that is now one ENCODED). L8 fallback only: plus the decoded scan's new entries (3.4 point 9).
7. `placeholders = dict(zip(runs, place_encoded(base, runs)))` with `runs` = the `written` of the hit units in order.
8. `T2 = _b64_place(stripped, copies, placeholders)`, where `copies` are all units of `stripped` (step 3, before the dedupe)
   whose `written` is a key of `placeholders`: every copy replaced by position (units do not overlap).
9. `return redact(T2, mapping=base, _cache=cache, _deadline=started + defaults.REDACT_BUDGET_S)`. Pass 1 leaves a placeholder
   alone, so the result holds `<ENCODED_n>` where the blob stood; nothing is mapped back by position.
Settle and fold interplay: step 9 is a full `redact()` with its own `_SETTLE_ROUNDS` cap and its own fold scan; it reruns every
settle chain of T2 (a chain in T is still in T2: only base64 units changed). A `RedactionError("NotSettled")` or an
`InputTooLarge` raised in step 9 propagates: `redact_text` refuses the text and does not write the map (I21). Cost: a text with
a hit pays two `redact()` calls per scanned spelling (section 8).

### 2.6 Failure behaviour by depth (decision L4 and review M7)
| raised where | depth 0 (the input, its views) | depth 1 or more (inside a decoded view) |
|---|---|---|
| `TooDeep` from `_views` / `undo` | propagates: refused, as today | caught in `_b64_hits`: every unit of that decoded view is a hit unread (L4) |
| the decoded join over `MAX_REDACT_CHARS` after NFKD (`_expanded_len`) | - | checked before the recursive call: every unit of that view is a hit unread |
| `InputTooLarge` from the clock, `_ScanBudget.take`, `_decoded_masks`, `fits_after_nfkc` of a view | propagates: refused | propagates: refused |
| `RedactionError("NotSettled")` | propagates: refused | propagates: refused |
A decoded view that only grows past the cap through its escapes (a `ﷺ` run) is refused; stated, not handled.

## 3. G4a: the base64 rules (zero decision)
### 3.1 Units (`_b64_units`)
Alphabet `[A-Za-z0-9+/_\-]`. One `=`, two `=` or none may end a run.
1. GATE: `_B64_RUN = re.compile(rf"(?<![A-Za-z0-9+/_\-])[A-Za-z0-9+/_\-]{{{defaults.B64_MIN_CHARS},}}={{0,2}}(?![A-Za-z0-9+/_\-=])")`,
   compiled once at import (a test that needs another minimum patches `runmap._B64_RUN`). The gate is ONE `search` on the
   run text of point 2; no match means no unit and nothing else runs. A `=` before a run is allowed (`data=<b64>`): the
   look-behind excludes the alphabet only (prototype: excluding `=` too left all 7 `data=` rows open).
2. PLACEHOLDERS AND MARKERS ARE NEVER RUNS (review M4; v2's section A claim "`<`, `>` end a run" was false: they are not in
   the alphabet, so the look-behind let `HIGHENTROPY_1` inside `<HIGHENTROPY_1>` start a run). Before the search, every match of
   `_B64_TOKEN_SKIP = re.compile(r"[<‹](?:[A-Za-z][A-Za-z0-9]*_\d+|[A-Z][A-Z0-9_]*)[>›]")` is blanked to the same
   number of spaces (offsets stay): a genuine placeholder (`<CREDITCARD_12>`), its escaped look-alike as
   `runmap.escape_placeholders` writes it (`‹HIGHENTROPY_7›`, U+2039 and U+203A), a lower-case look-alike in model-written
   text (`<ipv4_2>`), and the markers `<SECRET_REDACTED>` (tools.py:766, k1b/redaction.py:86). Only when the text holds `<` or
   U+2039 (otherwise no work). Stated limit L-B6: a real blob made only of `A-Z`, `0-9`, `_` and written between `<` and `>`
   is taken for a marker and not decoded.
3. WRAPPED BLOCK: two or more consecutive lines (split on `\n`; a trailing `\r` and spaces or tabs at both ends of a line are
   ignored) where every line holds only alphabet characters, the first line is at least `defaults.B64_WRAP_MIN_CHARS` (16)
   long and its length is a multiple of 4, every line but the last has the first line's length and no `=`, and the last line
   is 1 to first-length characters (it may end in `=` or `==`). One top-to-bottom pass; each line in at most one block; the
   block is maximal (it ends at the first line that breaks a rule, that line included if it is a valid shorter last line).
   Linear: no window of lines is tried twice, and the taken lines are an index set, not a list scanned per run (prototype: a
   per-run scan of the block list made a 262,000-character text 35 percent slower).
4. A unit is a block, or a RUN that does not start inside a block. `written` is the stretch of the stripped text from the
   unit's first to its last character (for a block: its lines and the line breaks and indentation between them).
5. ANSI (review nit, taken): units are found on `strip_ansi(text)` (redact.py:890, the same function `find` runs first), and
   T2 is built from that stripped text; pass 1 strips ANSI anyway, so `redact(T2)` reads the same text pass 1 read. A run glued
   to an escape (`ESC[1m` + blob) is then aligned; without this it read as `m` + blob, a longer run that does not decode.
6. Offset 0 only. A run glued to other alphabet characters (`/v1/blob/<b64>`, `keyx<b64>`) is one longer run that does not
   decode: it stays as today. Stated limit L-B1, pinned by a strict xfail (prototype: both leak).
7. Duplicates: units with the same `written` are decoded once and count once against the budget (tests/test_k5_fixes5.py:38-44
   feeds 20,000 copies of one 12-character run; after the tools scrub they are 20,000 `<SECRET_REDACTED>`, which point 2
   blanks).

### 3.2 Decode (`_b64_text(joined) -> str | None`)
1. Strip the trailing `=`. Call the rest the body.
2. Alphabet: a body with `+` or `/` AND `-` or `_` is mixed: None. A body with `-` or `_` is URL-safe: map `-` to `+` and `_`
   to `/`. Otherwise standard.
3. Length: `len(body) % 4 == 1`: None. Otherwise pad with `=` to a multiple of 4 (written padding is ignored).
   `base64.b64decode(padded, validate=True)`; non-canonical trailing bits accepted; any `binascii.Error` / `ValueError`: None.
4. Bytes to text, first rule that applies, each decode strict: a. BOM `FF FE`: UTF-16-LE of the rest; `FE FF`: UTF-16-BE of
   the rest; `EF BB BF`: UTF-8 of the rest; b. else UTF-8; if that fails or fails rule 5: c. if the length is even and at least
   4: at least `defaults.B64_UTF16_ZERO_SHARE` (0.90) of the odd-index bytes are 0: UTF-16-LE; else that share of the
   even-index bytes: UTF-16-BE.
5. Printable share on the decoded `str`, before `_clean`: characters with `c.isprintable() or c in "\t\n\r"`; text when the
   share is at least `defaults.B64_PRINTABLE_SHARE` (0.90) and the string is not empty. NUL is not printable, so NUL-interleaved
   UTF-16 read as UTF-8 fails and is tried as UTF-16.
6. Hex, base32, base85, gzip and quoted-printable are not decoded (stated limit L-B2).

### 3.3 HELD (`_b64_held`; what pass 1 masks as a secret is left as pass 1 wrote it)
With `secret = {originals of placeholders in first.mapping whose kind is in SECRET_KINDS}` (ENCODED included, section 4):
a unit is HELD when `written in secret`, or when every line is in `secret` or is a substring of the original of a JWT or
PRIVKEY placeholder. Changes from v2: (a) a whole-unit test, so a wrapped ENCODED original (multi-line) from an earlier call
or from pass 1 of k1b's second bundle pass is held and not decoded again; (b) only SECRET kinds hold (decision L12): a run
that pass 1 took as an identifier (TENANT `org_id=<b64>`) is decoded; on a hit it becomes ENCODED instead of a stored,
restorable TENANT. Effect unchanged: the 80 HIGHENTROPY rows of 1b, the 3 `data:` rows and the 2 BASIC rows of 1c, JWTs and
PEM blocks are not decoded; a wrapped block whose full lines are HIGHENTROPY and whose last line is readable is not held and
becomes one ENCODED (1c rows 2, 3, 6, 7, 10, 11). Exact originals, not "still readable in `first.text`": base64 of `pwd=...`
often holds `PWd...=`, which SECRET takes as key `PWd...` with value `=`; with exact originals that run is not held (prototype).
Cost: one pass over `first.mapping` per `_pass_one` that has a unit (none for a text with no run).

### 3.4 The decoded view and the hit rule (`_b64_hits`), numbered
1. For each unit in order: `budget.clock()` (one clock read per unit that is not held, before its decode; none for a held
   unit and none for a text with no run).
2. `len(u.joined) > defaults.B64_MAX_UNIT_CHARS` (65,536): no decode; `budget.take(0)`; hit unread (fail closed; one
   attachment cannot use the decoded budget).
3. `d = _b64_text(u.joined)`; None: not a hit, not counted.
4. `depth == defaults.B64_MAX_DEPTH` (3): `budget.take(0)`; hit unread (decoded only to know it is base64 text, not scanned). So
   three levels are decoded and read; a fourth is masked unread (L4). The input and its views are depth 0.
5. Otherwise `budget.take(len(d))`; its piece is `_clean(d).replace("\x1e", " ")`.
6. No piece: return. `joined = _B64_SEP.join(pieces)` with `_B64_SEP = "\n\x1e\n"`. If `_expanded_len(joined) >
   defaults.MAX_REDACT_CHARS`: every piece's unit is a hit unread; return.
7. `seen` = the pieces as `_scan` will read them: `fits_after_nfkc(neutralise(fits_after_nfkc(_clean(joined))))` (no
   neutralise when None), split on `_B64_SEP`.
8. `out, scanned_map = _scan(joined, dict(known), None, neutralise, budget, depth + 1)` (`known` = `first.mapping`: a value
   pass 1 found in plain text elsewhere is known in the decoded view and its encoded copy is a hit; `_cache=None`, the same
   budget, the same neutralise). `TooDeep`: every piece's unit is a hit unread (2.6).
9. `after = out.split(_B64_SEP)`. If `len(after) != len(pieces)`: every piece's unit is a hit (a pattern that runs "to the end
   of the text", or a fold-scan block withheld across lines, ate a separator; `\x1e` is a line boundary of `str.splitlines`,
   which `_fold_scan` uses at redact.py:1267, so a withheld multi-line block can swallow it). Else piece i is a hit when
   `_held(after[i]) > _held(seen[i])`: a new value AND a value the map already held (the view rule of `redact_text`, per piece).
   L8 fallback only: return also `{k: v for k, v in scanned_map.items() if k not in known}`.
Under the default (L8), the decoded scan's map is thrown away after the decision, whatever the result; inner ENCODED entries of
nested blobs are thrown away with it, so a nested blob adds exactly ONE entry (its outer unit) and numbers do not skip.

### 3.5 What stays out of G4a (L-B3 corrected, review B2)
- v2's L-B3 was false. k1b `redact_bundle` calls `runmap.redact_untrusted` for every string (k1b/redaction.py:188), so the
  bundle path DOES get the base64 step. `redact_many` has no caller in src, and tests/test_k1b_redaction_layers.py:134-157
  pins that every bare `redact(` / `redact_many(` call in src (and demos) is in guard/runmap.py. L-B3 now reads: a direct call
  of `redact()` or `redact_many` (tests, a future caller) gets no base64 step; every src path goes through `redact_text`.
- k1b counting: `redact_bundle` returns `Counter(_kind(p) for p in mapping)` (k1b/redaction.py:195), read as
  `distinct_values_masked` (k1b/replay.py:158-161; tests/test_k1b_redaction.py:126-134). Under the default (L8), the map holds
  one ENCODED entry per distinct blob that was a hit, and no decoded entry: the report gains an `ENCODED n` row and every other
  count is unchanged. The bundle's two passes share the map: pass 1 places `<ENCODED_n>`; in pass 2, pass 1 sweeps the blob
  (its original is in the map) so the unit is HELD (3.3 a) and is not decoded again. Under the L8 fallback the decoded
  EMAIL/HOSTNAME/IPV4/SECRET entries are in the map and counted although no placeholder of theirs is in the output; that
  fallback needs `redact_bundle` to count only placeholders present in its output (a k1b/redaction.py change, not in G4).
- Not changed and not merged: `tools._b64_holds` / `tools._derived` (SPINE's file: the scrub of handed-out secrets) and
  `k1b.redaction._pair` (one Kubernetes Secret value under a credential key): different jobs. No offsets other than 0, no
  base32, no hex.
- `tools.redact_layered` catches only `TooDeep` (tools.py:983): an `InputTooLarge` from the unit cap makes a tool result a tool
  error (section 8 cost).

## 4. G4b: the kind ENCODED (guard/redact.py)
1. `_LABELS = tuple(dict.fromkeys([*(label for label, _ in PATTERNS), "ENCODED"]))` (redact.py:865). ENCODED is NOT in
   `PATTERNS`. Everything built from `_LABELS` follows: counters, `_KIND`, `_OPENINGS`, `_OWN_OUTPUT` (`password=<ENCODED_1>`
   and `password=‹ENCODED_1›` are own output, not a new secret), the growth-factor test (tests/test_runmap_enforce_map.py:462:
   ENCODED has 7 letters, AZURERESOURCE 13).
2. `SECRET_KINDS` gains "ENCODED" (redact.py:1838): every copy swept from 4 characters; `_rules_conflict` in snapshot puts it
   first; `held_value_left` checks it.
3. Counter restoration needs no new code (redact.py:1097-1106 restores every kind in `_LABELS`).
4. `def place_encoded(mapping: dict[str, str], runs: list[str]) -> list[str]`, the only writer of ENCODED. For each run in
   order, the placeholder it gets, added to `mapping` IN PLACE, exactly one entry per new run (no `_PIECE` pieces, no
   `_spelled`, no journal). Numbering (review nit): the next number is taken from `_Redactor(mapping).counters["ENCODED"] + 1`,
   so it is the redactor's own rule by construction: over the map in insertion order, `c = max(c + 1, n)` for each ENCODED key
   with a countable number n (else 0). Example: `{"<ENCODED_5>": a, "<ENCODED_2>": b}` gives c = max(1, 5) = 5, then
   max(6, 2) = 6, next `<ENCODED_7>` (the same as a later `_Redactor` hands out). Shared originals: a run that is the original
   of a placeholder of a SECRET kind gets that placeholder (the one `_Redactor.reverse` holds: the last in insertion order); a
   run that is the original of an identifier-kind placeholder only gets a NEW ENCODED entry (never a restorable placeholder).
   The original is the unit as written in the stripped, cleaned and neutralised text, line breaks included, never the decoded
   text. O(map + runs).
5. `_build` tie-break (review nit `reverse` last-wins vs `_build` first-wins, taken): `_build` keeps the FIRST rule per
   original over `_ordered` (redact.py:1642-1650), so a new ENCODED entry for an original a TENANT entry already holds would get
   TENANT's standalone rule and a glued copy would stay. The sort key at redact.py:1644 becomes
   `key=lambda kv: (-len(kv[1]), _kind(kv[0]) not in SECRET_KINDS)`: for one original (equal length), a secret kind's rule
   comes first, the rule `runmap._rules_conflict` already applies in `snapshot`. The AL-1 mutant's line above it is not
   touched. Test I7b.
6. `defaults.STORED_KINDS` does NOT change and `runmap._GRAMMAR` gets no ENCODED entry: never stored, never restored, even with
   `kinds={"ENCODED"}`.
7. `RedactionResult.actions` does not count ENCODED replacements (no reader in src; stated).
8. approvals/channel.py:98 `_ASSIGNMENT_KINDS` gains "ENCODED" (decision L10; review M8): `clean` takes the tag-joined
   alternative only when it finds a new original of one of these kinds; without ENCODED a blob split by a tag
   (`<b>`-half-`</b>`-half) is decoded in the joined text, but the card keeps the text where both halves stay readable.
   HIGHENTROPY has the same gap today: stated, not changed here.
Fallback if the lead declines the name (L1): `place_encoded` issues `<SECRET_n>` (SECRET is in `_LABELS` and `SECRET_KINDS`),
points 1, 2 and 8 are dropped, the tests assert SECRET.

## 5. G4c: whole host names (guard/redact.py, the HOSTNAME entries of PATTERNS)
### 5.1 One place for the suffix list
`_HOST_BARE = "internal|local"` (a host only when nothing follows) and `_HOST_TAIL =
"corp|lan|intranet|intra|localdomain|home" + _HOST_DOT + "arpa"` (a host whatever follows), beside the pattern.
`defaults.PRIVATE_SUFFIX_LABELS` (config's in-cluster http check) is a different job and is NOT used: it lists `test`,
`invalid`, `svc`, `cluster`, `home`. A `#` comment beside each names the other.

### 5.2 The main pattern (replaces redact.py:404-410; same place; no capture group)
```
_HOST_LABEL = r"[A-Za-z0-9_-]+"   # ASCII letters and digits, underscore, hyphen; unbounded (point 4)
_HOST_DOT = r"(?:\.|\[\.\])"      # a dot, or a defanged [.]
HOSTNAME = (r"(?i)(?<![\w.\-\]])(?:" + _HOST_LABEL + _HOST_DOT + r")+(?:"
            r"(?:" + _HOST_BARE + r")(?![\w-])(?!" + _HOST_DOT + r"\w|\()"
            r"|(?:" + _HOST_TAIL + r")(?![\w-])(?:" + _HOST_DOT + _HOST_LABEL + r")*)")
```
1. Start: not after a word character (Unicode `\w`), `.`, `-` or `]`: a match starts at the first label and masks the name
   whole. Underscore is a label character (`db_01`).
2. Label class ASCII (decision L11; v2 had Unicode `\w`). Measured on HEAD: row 31 is already masked by the fold scan, which runs
   first on every non-ASCII line (redact.py:1130-1133). A Unicode label class would make the direct pattern match a look-alike
   host on the raw line with the same fold as the folded match, so the fold scan would no longer see the line as suspect and
   would mask the look-alike under a second placeholder instead of withholding the line (tests/test_text_parts_together.py
   CARDS, rows `cyrillic`, by reading; not run). Non-ASCII labels stay the fold scan's job.
3. Tail: after a `_HOST_TAIL` suffix the rest of the dotted name is in the match (`db01.corp.example`,
   `billing-db.prod.corp.example`, `xn--bcher-kva.corp.example`, `db01.corp.example.com_x`). A trailing dot is not a label:
   `db01.corp.example.` gives `<HOSTNAME_1>.`. A port, a path and `@` end the name.
4. Bare suffix `.internal` / `.local`: as today; a following label or `(` means code (`jdk.internal.reflect`,
   `threading.local()`): no match. Labels and label count unbounded on purpose: one start per dotted token, so the greedy `+`
   backtracks at most once per label (linear); a bound would be fail-open (prototype on main, CPU s: `a.` x 130,000 old 0.154
   new 0.025; `ab-cd.` x 40,000 old 0.152 new 0.012; 262,000 characters of `abc.def.ghi` old 0.023 new 0.011).
5. `_KEPT_HOST` unchanged, applied to the whole match in `_decide`: `x.svc.cluster.local`, `eu-west-1.compute.internal`,
   `ec2.internal` stay. A defanged `x[.]svc[.]cluster[.]local` is masked (accepted).
6. Java packages: `com.acme.corp.billing.Service` was `<HOSTNAME_1>.billing.Service`, becomes `<HOSTNAME_1>` (limit L-H1).

### 5.3 The host-key rule (a second ("HOSTNAME", HOSTKEY) entry right after the main one; group 1 is the value)
```
HOSTKEY = (r"(?i)(?<![\w-])(?:--)?host(?:name)?(?:[\"']?[ \t]*[:=][ \t]*[\"']?|[ \t]+)"
           r"(?=[A-Za-z0-9_-]{0,62}[0-9])"
           r"([A-Za-z][A-Za-z0-9_-]{1,61}[A-Za-z0-9])(?![\w\-/@])(?!\.\w)")
```
Changed from v2 (review M8 and the HOSTKEY nits, decision L2): the key `server` is dropped, and the value must START WITH A
LETTER and hold AT LEAST ONE DIGIT (a hyphen no longer counts). Keys: `host`, `hostname`, `--host`, `--hostname`, with `=`,
`:` or spaces. One label, 3 to 63 characters, not followed by a word character, `-`, `/`, `@` or a dot and a word character.
A dotted value is never this rule's (`Host: api.github.com` stays; a private dotted one is the main pattern's).
Must-keep (all unchanged; prototype for v2's rows, by reading for the new ones): `host is down`, `server timed out`,
`Server: nginx`, `Server: nginx/1.18.0`, `Server: AmazonS3`, `server 500 error`, `ghost town db01`, `ghost=ab12`,
`Host: api.github.com`, `host: localhost`, `--host 0.0.0.0` (IPV4 masks the address as today), `host 1 of 3 failed`,
`the hostname is unknown`, `host x-ray`, `host re-election`, `host 2026-11-20T10:00 started`.
Masked on purpose (stated): `hostname: Web2` gives `hostname: <HOSTNAME_1>` (a single-label host name with a digit is what the
rule is for; it is then swept standalone and is storable and restorable as any HOSTNAME).
Closed: rows 33 `host db01 is down`, 34 `host: db01`, 35 `hostname=db01 state=down`, 36 `psql --host db01 --port 5432`.

### 5.4 Restorable grammar
`runmap._GRAMMAR["HOSTNAME"]` (`[A-Za-z0-9.\-]{3,253}`) unchanged: an original with `_` or `[.]` is masked for the model and
never stored or restored (fail safe). Fallback (L5): add `_` to the grammar.

## 6. G4d: bare numbers (written down, pinned)
One paragraph in the module docstring of guard/redact.py, after the "What this is not" paragraph (no digits run of 12, no host:
test_no_hardcoded_values scans docstrings):
"A bare number with no label or context (for example `ref 55556666 paid`) is not masked, by decision (order 64 item 4).
Masked by shape: 10 to 16 contiguous digits (PHONE; exactly 12 as ACCOUNTID) and 16 digits in four groups of four joined by
spaces or hyphens (CREDITCARD). Other groupings are masked in part or not at all: 16 digits joined by dots lose their first 12
to MAC and keep the last group; 15 digits in 4-6-5 groups lose the first 10 to PHONE and keep the last 5."
Pin (class level): tests/test_p1c_gaps.py classifies the 43 gap-3 rows with the probe's rule and asserts per row: 24 NOT masked
(1-7, 9-12, 14-20, 30, 35, 38-40, 43), 2 part (29, 32), 17 whole (8, 13, 21-28, 31, 33, 34, 36, 37, 41, 42); re-measured on
HEAD by the drafter: the same rows. A row that differs at build time: report, change no pattern.

## 7. Constants (defaults.py, one SPINE commit holding only these lines and their comments)
Placed after `REDACT_BUDGET_S`. Exact comment above each (`#` comments: no host and no 32-character run in them):
| constant | value | comment text (one line each) and the source of the number |
|---|---|---|
| `B64_MIN_CHARS` | 12 | "# shortest base64 run (padding not counted) the redactor decodes; 12 characters are 9 bytes". Source: chosen under 15, the shortest leaked probe blob (1b row 83, an IPv4 address, unpadded) and a multiple of 4; v1's 16 left row 83 open (prototype). |
| `B64_WRAP_MIN_CHARS` | 16 | "# shortest first line of a wrapped base64 block; every line but the last has its length". Source: chosen; it was an unnamed literal in v2. The probe wraps at 32, 64 and 76; 16 keeps two unrelated short lines from being one block. |
| `B64_PRINTABLE_SHARE` | 0.90 | "# share of printable characters a decoded run needs to count as text". Source: chosen, not measured. Phase 4 measures that no probe or must-keep row changes verdict anywhere between 0.85 and 0.95 (evidence). |
| `B64_UTF16_ZERO_SHARE` | 0.90 | "# share of zero bytes at the odd (LE) or even (BE) positions that reads a decoded run as UTF-16". Source: chosen; it was v2's unnamed "90 percent"; ASCII text in UTF-16 has a share of 1.0. |
| `B64_MAX_UNITS` | `MAX_MAP_ENTRIES` (2000) | "# decodable, not held base64 units per redact_text call (all views, all depths); one more is refused (InputTooLarge)". Source: the run map's default ceiling (defaults.py:24): one call cannot by itself add more ENCODED entries than a default run may hold (section 8; decision L9). |
| `B64_MAX_DECODED_CHARS` | `MAX_REDACT_CHARS` (262,144) | "# decoded characters per redact_text call; past it the call is refused (InputTooLarge)". Source: the decoded view is one text for the redactor and must fit its own cap. |
| `B64_MAX_UNIT_CHARS` | 65536 | "# longest base64 unit that is decoded; a longer one that pass one did not hold is masked unread". Source: chosen, a quarter of the cap (no probe blob is over 1,000 characters). v2 called it `B64_MAX_BLOCK_CHARS`; it covers a run too. |
| `B64_MAX_DEPTH` | 3 | "# levels of base64 decoded and read; a unit found at this depth is masked unread". Source: chosen: the probe's double rows need 2, one more of slack; past it fail closed (L4). |
The comment above `REDACT_BUDGET_S` (defaults.py:51-64) already describes MJ-B's settle rounds (review nit, taken: v2's "stale"
was wrong); it gains one clause only, after "...inside the sweeps of those rounds (...)": "and, since G4, once before each
base64 unit that is decoded or masked unread (`runmap._ScanBudget.clock`)".
Fallback (L7): the eight as module constants in runmap.py beside `MAX_DECODED_MASKS`; then write 65536 as `1 << 16`
(tests/test_no_hardcoded_values.py:161-165 forbids the literal `= 65536` in runmap.py, which is in `K5_FILES`).

## 8. Cost and map growth
Baseline on HEAD 193605f, measured by the drafter (this container, `time.thread_time()`, best of 3, `redact_text` with a fresh
map; scratch script, not committed): 100,000 characters of snake_case words and paths 0.128 s; 100,000 characters of prose
0.155 s; the snake_case text with one planted `password=` 0.294 s (MJ-B's extra rounds); 2,000 base64 secrets (57,999
characters, each `password=` + 12 characters) 0.085 s.
Prototype on main 51c9fc4 (no MJ-B, no fold scan): the step alone cost 5.1 percent (100,000 snake_case), 5.5 percent (262,000),
0.7 percent (prose); 4,096 base64 secrets 0.72-0.82 s (mostly `_build` over 8,192 entries); 4,097 raised `InputTooLarge` after
0.20 s. With the L8 default the map holds one entry per hit, not two, so `_build` costs about half of that. The "2.4x per
redact()" and "about 2 s" of v2 were estimates and are dropped; I16 measures.
A text with a hit pays `redact()` twice per scanned spelling (T, then each view that holds a decodable unit not held) plus one
recursive `_scan` per spelling with units; held units are swept, never decoded twice. Past the deadline: `InputTooLarge`, never a
skipped step.
MAX_MAP_ENTRIES (v2's claim "enforced nowhere" was FALSE; review M4 / B3): `defaults.MAX_MAP_ENTRIES` = 2000 (defaults.py:24)
is `config.evidence.max_map_entries` (config.py:245); runtime/agent_loop.py:427 (document) and :547 (each tool result) end the
run `NEEDS_PERSON` / `document_too_complex` when `len(rmap) > max_map_entries`, after `_save_map` (tests/test_k5_round10.py:142
pins it with a ceiling of 20). Bound with G4: per `redact_text` call G4 adds at most one ENCODED entry per hit unit (the default
keeps no decoded entry and no inner entry), and hits are at most `B64_MAX_UNITS` = 2000. A run that crosses its ceiling through
ENCODED entries is refused by that existing check (fail closed, nothing more is sent); I23 drives it with a small ceiling.
Under the L8 fallback a hit adds its ENCODED entry plus every value the decoded view held (at least two per hit).
Cost of the caps for legitimate big input (review M7, stated, not measured on real dumps): a text with more than 2,000 distinct
decodable, not held runs (a dump of many Kubernetes Secret values, a log of many short base64 payloads) or more than 262,144
decoded characters is refused whole where it passed before (with those blobs readable): a document ends `NEEDS_PERSON`
`document_too_large`; a tool result becomes a tool error (`redact_layered` catches only `TooDeep`); a card shows `SETTLE_NOTE`; a
k1b bundle raises `InputTooLarge`. Past the cap the alternative of masking every further unit unread was not taken: it would
over-mask benign runs and add entries past the map ceiling anyway (contested in section D, M7).

## 9. Expected results per probe row (HEAD numbering is the probe's)
### 9.1 Base64, 142 rows ("unchanged" = output and map digest equal to the base commit's, both functions)
| rows | value | expected |
|---|---|---|
| 1b 1-5, 7, 8 | kv secret short | one `<ENCODED_n>` where the blob stood; the map holds no SECRET entry for it (L8 default) |
| 1b 6, 9-16 | kv secret | unchanged (HIGHENTROPY holds it) |
| 1b 17-32 | bearer token | unchanged |
| 1b 33-37, 39, 40 | AWS key id short | ENCODED |
| 1b 38, 41-48 | AWS key id | unchanged |
| 1b 49-53, 56 | e-mail short | ENCODED |
| 1b 54, 55, 57-64 | e-mail | unchanged |
| 1b 65-72 | host name short (70 UTF-16-LE, 71 double) | ENCODED |
| 1b 73-80 | host name long | unchanged |
| 1b 81-88 | private IPv4 short (83 = 15 characters; 86 UTF-16-LE) | ENCODED |
| 1b 89-96 | private IPv4 long | unchanged |
| 1b 97-101, 104 | connection string short | ENCODED |
| 1b 102, 103, 105-112 | connection string | unchanged |
| 1b 113-117, 120 | JSON with password short | ENCODED |
| 1b 118, 119, 121-128 | JSON with password | unchanged |
| 1c 1, 5, 9 | wrapped at 32 | the whole block is one `<ENCODED_1>` |
| 1c 2 | wrapped at 64, last line held 11 of 14 password characters | one `<ENCODED_1>` |
| 1c 3, 6, 7, 10, 11 | wrapped at 64 / 76, no leak today | KIND CHANGE: exactly `<ENCODED_1>` |
| 1c 4, 8, 12 | `data:` URL | unchanged (HIGHENTROPY) |
| 1c 13, 14 | `Basic <b64>` | unchanged (BASIC) |
1c has 14 rows, not 18: both `no_digit_line` searches of the probe run 200,000 iterations and find nothing (NOT CONSTRUCTED,
measured on HEAD); they still consume the seeded generator, so `build()` (11) keeps them. Totals: 52 closed (48 in 1b, 4 in 1c),
85 unchanged, 5 change kind. On HEAD the leaked rows are exactly the ones listed (drafter's re-run: 1b 1-5, 7, 8, 33-37, 39,
40, 49-53, 56, 65-72, 81-88, 97-101, 104, 113-117, 120; 1c 1, 2, 5, 9).
Constructed shapes (the builder adds them to tests/test_b64_scan.py; values built from parts):
| shape | expected | status |
|---|---|---|
| JSON with `\/`-escaped slashes | ENCODED through the JSON view | prototype pass |
| `%3D` padding | ENCODED (the run before `%` decodes unpadded; the undo view too) | prototype pass |
| value already in the map, seen in base64 | the known placeholder counts: ENCODED | prototype pass |
| UTF-16-BE without BOM, short (under 40 characters) | ENCODED | builder builds it |
| triple base64, short (levels 1, 2, 3 read at depths 1, 2, 3) | ENCODED | builder builds it |
| fourth level | masked unread at depth 3 | builder builds it |
| `TooDeep` inside the decoded text (a percent nesting deeper than `defaults.SCRUB_MAX_LAYERS`, blob under 40 characters) | `<ENCODED_1>`, no `TooDeep` raised (L4) | builder builds it |
| a TENANT-held blob (`org_id=` + base64 of `pwd=` + 8 characters, URL-safe alphabet) | `org_id=<ENCODED_1>`; no TENANT entry (L12) | builder builds it |
| a blob after an ANSI colour escape | ENCODED (3.1 point 5) | builder builds it |
| glued to a prefix (`/v1/blob/<b64>`, `keyx<b64>`) | leaks (offset 0 only) | limit L-B1, strict xfail |
| a blob split across two JSON fields | the second half readable | limit L-B4, strict xfail |
| wrapped lines with a log prefix per line | readable | limit L-B5, strict xfail |
| base32, hex | not decoded | limit L-B2, strict xfail |
| an all-capital blob written as `<...>` | not decoded | limit L-B6, strict xfail |
| row 83 with `B64_MIN_CHARS` 16 (fallback L6) | stays a leak | limit only if L6 is declined |

### 9.2 Host names, 44 rows (on HEAD)
| row | input shape | expected after G4 | class on HEAD |
|---|---|---|---|
| 1, 2, 17, 19, 24, 26, 29, 37, 38, 44 | `...corp.example` with port, URL, upper case, trailing dot, punycode, `host=`, JSON, two names | whole name one placeholder (`dial <HOSTNAME_1> now`, `:5432`, `/v1`, the trailing `.` outside; row 44 `<HOSTNAME_1>` and `<HOSTNAME_2>`) | part: closed |
| 21 | URL with credentials | `use postgres://app:<URLCRED_1>@<HOSTNAME_1>:5432/orders now` | part: closed |
| 39, 40 | `.`, `%2E` dots | whole name, through the views | part: closed |
| 32 | `db_01.corp.example` | `dial <HOSTNAME_1> now` | whole: closed |
| 43 | `db01[.]corp[.]example` | `dial <HOSTNAME_1> now` | whole: closed |
| 33, 34, 35, 36 | `host db01`, `host: db01`, `hostname=db01`, `--host db01` | `<HOSTNAME_1>` in place of `db01` | whole: closed (host-key rule) |
| 3, 4, 5, 7, 11, 12, 13, 14, 18, 20, 22, 23, 25, 27, 28, 30, 31, 41 | already masked (31 and 41 by the fold scan on HEAD) | unchanged | masked |
| 6, 8 | `.internal` / `.local` then more labels | unchanged (code-name guard) | kept on purpose |
| 9 | `.svc.cluster.local` | unchanged (`_KEPT_HOST`) | kept on purpose |
| 42 | `ip-<IPV4_1>.eu-west-1.compute.internal` | unchanged (`_KEPT_HOST`; IPV4 masks the address) | kept on purpose |
| 10 | `billing.payments.svc` | unchanged | limit L-H2 |
| 15, 16 | `db01.acme.example`, `db01.acme.test` | unchanged | limit L-H3 |
Totals: 19 closed (13 part rows: 1, 2, 17, 19, 21, 24, 26, 29, 37, 38, 39, 40, 44; 6 whole rows: 32, 33, 34, 35, 36, 43),
3 limits, 4 kept, 18 unchanged.

### 9.3 Every other literal expectation in the tests tree that the host change turns (review B1, both reviewers)
Found by `grep -rnE "<HOSTNAME_[0-9]+>(\.|\[\.\]|%2E)[A-Za-z]" tests` and a grep for private suffixes in tests (HEAD):
| where | row | today expected | after G4 (exact) | action |
|---|---|---|---|---|
| tests/fixtures/p1d_cases.py:333-340 | H27 card | `host <HOSTNAME_1>[.]example[.]com down` | `host <HOSTNAME_1> down` | Modify the `after` cell |
| tests/fixtures/p1d_cases.py:578-585 | L2 card | `SAME` (= base cell `run \`curl <HOSTNAME_1>.example.com\` now`) | `run \`curl <HOSTNAME_1>\` now` | Modify `after` from SAME to this literal; the base cell stays |
| tests/fixtures/p1d_cases.py:594-601 | L3 card | `SAME` (= ```` ```\nping <HOSTNAME_1>.example.com\n```\nthen evil[.]com ````) | ```` ```\nping <HOSTNAME_1>\n```\nthen evil[.]com ```` | Modify `after` from SAME to this literal |
| tests/warden_port/privacy_corpus.py:36 | MASKED HOSTNAME | (kind only) | `db at <HOSTNAME_1>:5432` | stays green unchanged (tests/warden_port/test_redaction_classes.py asserts the kind); carved out of I4 into I12b |
| tests/warden_port/privacy_corpus.py:37 | MASKED HOSTNAME | (kind only) | `smb://<HOSTNAME_1>/share` | as above |
| tests/fixtures/p1d_a_base_rows.json:48-49 | `L2/card`, `L3/card` | base record | not changed | contested (section D, readiness B1): the JSON records the P1d-a base commit 2742c1b and is read only for `BS0` cells; H27, L2, L3 cells are literals |
| tests/fixtures/p1d_cases.py:505-510 (D3a-D3f), tests/test_p1d_a_paths.py:188-189, 325 | defang inputs that already hold `<HOSTNAME_1>.` | unchanged | unchanged | they call `gate.defang_text` / `undefang_text` directly, no redaction |
| tests/test_text_parts_together.py:224 (`db-7.corp.internal`), :242 (`db-7.corp`) | glued rest | masked whole today | masked whole (tail takes the glued `9`, `_x`, `a`) | stays green unchanged (by reading) |
| tests/test_k1b_redaction.py:18 (`db01.corp.local`) | k1b fixture | masked whole | masked whole | unchanged |
| tests/test_model_gate.py:1709-1714 | a map entry `db1.corp.example.org` | gate replaces the known spelling | unchanged (no redaction of that line) | unchanged |
`H27`'s `check_extra` (p1d_cases.py:642-647: a redactor call saw `db01.corp.example.com`, none saw `[.]`) stays true: every call
goes through `runmap.redact` (2.5). `assert len(ROWS) == 70` (p1d_cases.py:631) is unchanged: no row is added.
Gate mutants that used these rows as killers (tests/p1d_a_mutants.py): A4 (`_PLACEHOLDER_DOT` sub, killer H27), A5 and A38
(inline-code split, killer L2), A6 (closed fences, killer L3). After G4 these rows hold no dotted name next to a placeholder or
inside code, so by reading the four survive. Modify tests/p1d_a_mutants.py: A4 killer `test_row_D3b_defang` (`mail <EMAIL_1>.org`
to `mail <EMAIL_1>[.]org`; A42 uses it too), A5 and A38 killer `test_row_D3c_defang` (code span kept), A6 killer: run
`python tests/p1d_a_mutants.py A6` with `test_row_I1_card` and `test_row_L4_card`; if neither kills it, STOP and report (no
row is invented here). The comment above `_PLACEHOLDER_DOT` (approvals/gate.py:230-231) says the redactor masks only the
internal part of a host; it becomes: "# A placeholder (`<EMAIL_1>`, or a host name masked before G4 and stored) followed by a dot
and a name character: what follows the dot would stay linkable. Written `[.]` (P1d-a, D3)." The pattern itself stays (D3a-D3f,
stored older texts).

## 10. Invariants (each one test or one parametrised test; tests/test_p1c_gaps.py = TG, tests/test_b64_scan.py = TB)
- I1 (TG). The 52 leaked base64 rows: `leak_of(protected, out)` is "no" and `<ENCODED_` is in `out`, through `redact_text` and
  `redact_untrusted`.
- I2 (TG). The 85 unchanged rows: digest of (output, sorted map) equal to the base fixture, both functions.
- I3 (TG). The 5 kind-change rows: output exactly `<ENCODED_1>`; the map has no HIGHENTROPY entry.
- I4 (TG). Must-keep base64, digest equal to the base fixture, both functions: 17 constructed rows (11: `MUST_KEEP_B64`) and the
  60 privacy-corpus rows that the host change does not touch (48 MASKED + 14 KEPT = 62, counted from
  tests/warden_port/privacy_corpus.py at HEAD, minus the two HOSTNAME rows of 9.3): 77 rows. v2's "79 of 79" is withdrawn
  (it counted 62 + 17 on main; the two host rows change).
- I5 (TB). A text with no run of `B64_MIN_CHARS`, and a text whose runs are all held, makes exactly as many `runmap.redact` calls
  and exactly as many `time.thread_time()` reads as the same build with `runmap._B64_RUN` patched to `re.compile(r"(?!)")`, and
  returns the same text and map (zero extra clock reads, review CountedClock nit). Inputs: `pw=ab%41 here`,
  `pw=ab%41 x A` (tests/test_redact_fold_budget.py budget_1b and budget_2 texts), 100,000 characters of prose, a HIGHENTROPY
  blob, and the placeholder rows of I19.
- I6 (TB). ENCODED is never restored: `restore_text(out, m)` and `restore_text(out, m, kinds=frozenset({"ENCODED"}))` leave
  `<ENCODED_n>`; `storable(m)` holds no ENCODED key.
- I7 (TB). Numbering: `place_encoded({"<ENCODED_5>": a}, [b])` gives `<ENCODED_6>`; `{"<ENCODED_5>": a, "<ENCODED_2>": b}`
  then a new run gives `<ENCODED_7>`; two blobs give 1 and 2; the same blob in two calls with one map gets the same placeholder;
  a run equal to a TENANT original gets a new ENCODED entry. I7b: with that map, a glued copy of the run elsewhere is swept
  (`_build` tie-break, 4 point 5).
- I8 (TB). One entry per hit unit: the ENCODED original equals the unit as written (line breaks included), never the decoded
  text; four levels of base64 of `status ok` give `x <ENCODED_1>` and exactly one new entry (L8 default; v2's "three inner
  entries" is withdrawn).
- I9 (TG and the property test). Idempotent: `redact_text(redact_text(t, m), m)` changes neither text nor map, for all 229 probe
  rows (measured on HEAD: 229 of 229 today). `redact_untrusted` is not idempotent by design (a second pass escapes genuine
  placeholders: 142 of 229 rows change on HEAD) and is not tested for it.
- I10 (TG). Parity: the same leak verdict for `redact_untrusted` and `redact_text` on the 142 base64 rows; the same output on the
  44 host and 43 number rows.
- I11 (TG). Host must-keep rows of 5.3 and `x.svc.cluster.local`, `x.svc.cluster.local.foo`, `eu-west-1.compute.internal`,
  `jdk.internal.reflect.Method`, `threading.local()`: output equal to the base fixture.
- I12 (TG). The 19 closed host rows: no label of the name readable outside a placeholder (the probe's label test); the 25 other
  rows digest-equal. I12b (TB, not in FAIL-BEFORE): the two privacy rows of 9.3 give exactly their new strings.
- I13 (TB). Caps fail closed, nothing returned, map not written: unit `B64_MAX_UNITS + 1` (patched to 3, with 4 distinct units),
  decoded characters over `B64_MAX_DECODED_CHARS` (patched to 10), and `_b64_hits` with `_ScanBudget(started=-1e9)` (a spent
  deadline) each raise `InputTooLarge`; the last before any `_b64_text` call (a spy).
- I14 (TB). Depth: a unit decodable at depth `B64_MAX_DEPTH` is ENCODED even when it holds only benign text.
- I15 (TB). Separator fallback: `_b64_hits` with pieces whose scan output has fewer separators (a decoded
  `-----BEGIN PRIVATE KEY-----` without END; a fold-scan block withheld across `\x1e`) marks every unit of that view a hit.
- I16 (TB, `@pytest.mark.perf`). Cost, mechanism in 13.4.
- I17 (property test). tests/test_redact_idempotent_property.py stays green with 1,977 inputs (1,835 + the 142 base64 rows as a
  new group `p1c-b64`), 0 refused, 0 fail; its p1c rows come from `p1c_cases.build()`.
- I18 (TG). Bare numbers: the 43 gap-3 rows keep their class (24 / 2 / 17).
- I19 (TB). Placeholders and markers are never runs: `_b64_units(t)[1] == []` and output/map equal to the step-off build for
  `x <HIGHENTROPY_7> y`, `card <CREDITCARD_12> ok`, `<SECRET_REDACTED>`, `‹HIGHENTROPY_7›`, `<GCPRESOURCE_1>`,
  `<AZURERESOURCE_12>`, and `"<SECRET_REDACTED> " * 20_000` (under the cap), through both functions.
- I20 (TB). G7 settle and fold interplay: (a) the property test's `CONSTRUCTED[0]` chain + " " + a short blob: output equals
  `redact_text(chain, {})` + " <ENCODED_1>" (the chain's three rounds run again on T2); (b) the chain wrapped at 64 as base64
  with a readable last line: exactly `<ENCODED_1>` (the chain settles inside the decoded view); (c) `café ` + a short blob:
  `café <ENCODED_1>` (the fold scan runs in both passes); (d) a look-alike e-mail line holding a short blob: no leak by
  `leak_of`, the line withheld.
- I21 (TB). A `RedactionError("NotSettled")` and an `InputTooLarge` raised by the SECOND `redact()` of `_pass_one` (a wrapper on
  `runmap.redact` that raises on call 2) propagate out of `redact_text`, and the caller's map is unchanged.
- I22 (TB). `redact_untrusted` of a short blob + ` password%3D` + 12 characters: the output holds a genuine `<ENCODED_1>` and a
  `<SECRET_n>`, and no `‹ENCODED` (views are of T, 2.4 step 3).
- I23 (TB). Map ceiling: with `{"evidence": {"max_map_entries": 40}}` (tests.k5_support `k5_cfg`, `build_runtime`, `handle`), a
  document of 30 distinct base64 blobs of `password=` + 12 characters is not stopped as `document_too_complex` (30 entries);
  with 45 blobs it ends `NEEDS_PERSON` / `document_too_complex`.
- I24 (TB). approvals: `channel.clean` of a blob split by `<b>`...`</b>` shows no half of it (L10).
- I25 (TG). `sha256("\x00".join(inputs of build(), in order: 142 base64, 44 host, 43 number))` equals the literal
  `630d55c4c5fb1cbb8d37cff627a73e64063b071decbe3c4bccf0438c87ebe213` (computed by the drafter from evidence/p1c_probe.py's
  builders at HEAD in probe call order, Python 3.13.18; Phase 0 recomputes it from the probe file and must get the same value).

## 11. Files
Create:
- `tests/p1c_cases.py`: a copy of the probe's builders and judges (`rand`, `gap1_values`, `ENCODINGS`, `b64`, `wrap`,
  `no_digit_line`, the 1c case list, `gap2_cases`, `luhn_number`, `gap3_cases`, `lcs`, `_decodings`, `readable`, `leak_of`,
  `B64_RUN` of the probe, `PLACEHOLDER`), NO module-level generator: one pure function
  `build() -> Cases` (`functools.cache`) that makes a fresh `random.Random(20261120)` and consumes it in the probe's call order
  (gap1 values, the 1b rows, the 1c rows including both `no_digit_line` searches, gap2, gap3), passing it to every builder as
  an argument. `Cases` holds `values` (8 dicts), `b64` (142 (id, protected, text)), `hosts` (44 (id, name, text)), `numbers`
  (43 (id, number, text)), `plain` (the 16 short/long texts). Also the literal lists `MUST_KEEP_B64` (17 rows: base64 of `this
  is just a status message` and of `ok status 200`, base64 of `bytes(range(256))`, a 9-byte PNG header in base64, a
  Kubernetes `data:` value of `log_level: info` config text, a JWT with payload `{"sub":"demo","iat":0}` and one with an e-mail
  in its payload (built from parts), a UUID with and one without dashes, a SHA-256 and a SHA-1 hex digest, a 7-character git
  sha, `internationalization`, `redact_text_body_for_views`, `warden-dev-lab-tick-silent`, `/usr/local/lib/python3/site-packages`,
  `getImplementationsForKind`) and `HOST_MUST_KEEP` (5.3 and I11). Independent of import order and of xdist (review M2/M5).
  Cost: `build()` takes about 1.6 s of CPU (measured on HEAD; the two 200,000-iteration searches), paid once per process.
  Not imported from handover/: tests must not read the evidence folder.
- `tests/test_p1c_gaps.py`: TG invariants (I1-I4, I9-I12, I18, I25). Public names only (`redact_text`, `redact_untrusted`,
  `restore_text`, `storable`), so it runs unchanged on the base commit (FAIL-BEFORE). Test ids: `test_base64_row[b64-1b-001]` ...
  `[b64-1c-14]`, `test_host_row[host-01]` ... `[host-44]`, `test_number_row[num-01]` ... `[num-43]`, `test_must_keep_b64[...]`,
  `test_must_keep_corpus[masked-NN|kept-NN]`, `test_host_must_keep[...]`, `test_idempotent[...]`, `test_parity`,
  `test_inputs_are_the_probe_inputs`.
- `tests/test_b64_scan.py`: TB invariants (I5-I8, I12b, I13-I16, I19-I24), unit tests of `_b64_text`, `_b64_units`,
  `_b64_held`, `place_encoded`, `_ScanBudget`, the host-key grammar, the constructed shapes of 9.1 and the strict xfails L-B1,
  L-B2, L-B4, L-B5, L-B6, L-H1. Private names are reached as `runmap.<name>` / `redact_mod.<name>` INSIDE each test (no
  module-level import of a G4 name), so a phase's selection collects before a later phase's names exist. Every test of G4c
  (TG and TB) has `host` in its id, so `-k host` selects or deselects G4c.
- `tests/fixtures/p1c_base_digests.json`: `{"base": <base sha>, "rows": {"<id>/text": sha256, "<id>/untrusted": sha256}}` for
  every input of `build()`, `MUST_KEEP_B64`, `HOST_MUST_KEEP` and the 62 privacy rows, where sha256 is of
  `json.dumps([out, sorted(mapping.items())], ensure_ascii=True)` with a fresh `{}` map. Digests, not outputs: no fake secret
  value is written to the fixture.
- `tests/fixtures/make_p1c_base_digests.py`: the script that writes that file when run in a worktree of the base commit
  (`python tests/fixtures/make_p1c_base_digests.py > tests/fixtures/p1c_base_digests.json`); not collected by pytest.
- `tests/b64_mutants.py`: the G4 mutants of 13.3 for `tools/mutation_runner.py`, shaped like tests/redact_mutants.py.
Modify:
- `src/hadavin_sdk/guard/runmap.py`: `_ScanBudget`, `_B64Unit`, `_B64_RUN`, `_B64_TOKEN_SKIP`, `_B64_SEP`, `_b64_units`,
  `_b64_text`, `_b64_held`, `_b64_hits`, `_b64_place`, `_pass_one`, `_scan`, `redact_text` (2.3); imports `place_encoded` and
  `strip_ansi` from redact. Docstring paragraph of `redact_text` (no host, no long run): "Base64 step (G4): every run of the
  base64 alphabet that pass one did not mask as a secret and that decodes to text is decoded; the decoded texts are scanned as
  ONE text by this same procedure (views, decoded masks, nested base64 to `defaults.B64_MAX_DEPTH`), and a run whose decoded
  text held anything that scan masks is replaced whole by one `<ENCODED_n>` before pass one runs again. ENCODED is a secret
  kind, never stored or restored. At most `defaults.B64_MAX_UNITS` units and `defaults.B64_MAX_DECODED_CHARS` decoded
  characters per call, the deadline checked before each unit; past either, `InputTooLarge`."
- `src/hadavin_sdk/guard/redact.py`: `_LABELS`, `SECRET_KINDS`, `place_encoded`, the `_build` sort key, `_HOST_LABEL`,
  `_HOST_DOT`, `_HOST_BARE`, `_HOST_TAIL`, the HOSTNAME pattern and its comment, the HOSTKEY entry, the module docstring (6 and
  one sentence: "A value only written in base64 is found by the decoded view of `runmap.redact_text` and masked whole as
  ENCODED; `redact()` itself does not decode"). Examples (`db01.corp.example`, `jdk.internal.reflect`, `eu-west-1...`) in `#`
  comments only: tests/test_no_hardcoded_values.py scans every string constant including docstrings (its `host` pattern takes
  `x.internal`, `x.corp`, `x.lan`; `long-secret-shape` any 32-character mixed run) and has no ALLOWED entry for redact.py or
  runmap.py; tests/test_lockin_guard.py:519-536 flags AWS region names and vendor hosts in string constants the same way.
- `src/hadavin_sdk/defaults.py` (SPINE's file, its own commit): section 7.
- `src/hadavin_sdk/approvals/channel.py`: `_ASSIGNMENT_KINDS` gains "ENCODED" (L10).
- `src/hadavin_sdk/approvals/gate.py`: the comment of 9.3 only.
- `tests/fixtures/p1d_cases.py`: the `after` cells of H27, L2, L3 (9.3).
- `tests/p1d_a_mutants.py`: the killers of A4, A5, A38 (and A6 as measured) (9.3).
- `tests/redact_mutants.py`: R3's `old` text re-indented (13.3) and mutant 21's docstring sentence: "removes both
  `_deadline=started + defaults.REDACT_BUDGET_S` arguments of `runmap._pass_one` (pass one and the pass on the replaced text, used
  for the input and every view)".
- `tests/test_redact_idempotent_property.py`: `_p1c_module()` and `_P1C` replaced by `from tests import p1c_cases`; groups
  `p1c-gap1` (16, `build().plain`), `p1c-b64` (142, new), `p1c-gap2` (44), `p1c-gap3` (43) from `build()`; `EXPECTED_INPUTS =
  1977`, `P1C_B64 = 142` pinned beside `P1C_GAP2`/`P1C_GAP3`; the docstring's corpus table and "Measured" sentence updated with
  the Phase 4 numbers. Note: gap2/gap3 texts now follow the probe's call order (today's property test seeds and calls
  gap1/gap2/gap3 without the 1b/1c draws, so its gap2/gap3 random parts differ from the probe's; measured on HEAD).
- `CHANGELOG.md` (Unreleased, a "Redaction: base64 and host names (G4)" item in Upgrade steps) and `SECURITY.md` (the stated
  limits list): the text of the section "For SECURITY wording", through the security wording review.
Must stay green UNCHANGED (run, do not edit; a red one is a finding: report it, do not edit it in this step):
tests/warden_port (test_redaction.py OWN_SHAPES JWT and BASIC rows and `test_a_high_entropy_value_after_any_key_is_masked`,
test_redaction_classes.py, test_redaction_bank.py, test_redaction_review*.py), tests/test_redact_context_after_sweep.py,
tests/test_redact_own_output.py, tests/test_redact_own_output_hardening.py, tests/test_redact_settle_loop.py,
tests/test_redact_fold.py, tests/test_redact_fold_budget.py (:78 counts `len(PATTERNS)`, which HOSTKEY grows by one; the
CountedClock tests :186-256), tests/test_redact_fold_seams.py, tests/test_redact_fold_property.py, tests/test_redact_marks.py,
tests/test_redact_g3_port.py, tests/test_k5_round12_fuzz.py, tests/test_k5_round8.py, tests/test_k5_round9.py,
tests/test_k5_round9b.py, tests/test_k5_round10.py, tests/test_k5_fixes5.py, tests/test_k5_fixes7.py, tests/test_k5_fixes9.py,
tests/test_k5_layers.py, tests/test_k5_round5.py, tests/test_k5_classes.py, tests/test_k5_producers.py, tests/test_k5_perf.py
(`-m perf`; :67-74 sweeps every PATTERNS entry, HOSTKEY included), tests/test_runmap_enforce_map.py,
tests/test_runmap_map_write.py, tests/test_k1b_redaction.py, tests/test_k1b_redaction_layers.py, tests/test_text_parts_together.py,
tests/test_model_gate.py, tests/test_p1d_a_paths.py, tests/test_p1d_a_rows.py (after its fixture edit),
tests/test_no_hardcoded_values.py, tests/test_lockin_guard.py, tests/test_gate_mutants_picked_up.py, and the mutant runs of 13.3.
Delete: nothing. Migration: none (maps are per run and in memory; ENCODED is never stored).

## 12. Build order (phases; each ends green, with its own test selection; one commit per phase on the builder's branch)
Common prefix: `uv run --all-extras --group test`. "Green" = the named selection passes with only the ids listed as expected
failures failing.
Phase 0, no code. (a) Base sha (section 0); `git worktree add /tmp/g4-base <base-sha>`. (b) Run evidence/p1c_probe.py from that
worktree; its totals and row lists must equal 1, 6, 9.1 and 9.2 of this ticket (HEAD 193605f); any difference: STOP and report.
(c) Write tests/p1c_cases.py and recompute I25's sha256 against the probe file's own builders; differ: STOP. (d) Write
tests/fixtures/make_p1c_base_digests.py, run it in /tmp/g4-base, keep the JSON. (e) FAIL-BEFORE (13.1). (f) The modified
tests/test_redact_idempotent_property.py in /tmp/g4-base: 1,977 inputs, 0 refused, 0 fail; red: STOP (a property of the base, not
G4's). Green checkpoint: the full suite of the base (`pytest -q -n 2`, perf deselected as CI does) recorded.
Phase 1, defaults.py (SPINE commit): the 8 constants and the comment clause. Run tests/test_no_hardcoded_values.py,
tests/test_k5_review.py, tests/test_lockin_guard.py. Green: all.
Phase 2, G4b (redact.py: `_LABELS`, `SECRET_KINDS`, `place_encoded`, `_build` sort key; channel.py `_ASSIGNMENT_KINDS`). Run
`pytest tests/test_b64_scan.py -k "place_encoded or numbering or restore or tie_break" tests/test_runmap_enforce_map.py
tests/test_redact_own_output.py tests/test_redact_own_output_hardening.py tests/test_k5_classes.py tests/test_redact_settle_loop.py
tests/test_redact_idempotent_property.py tests/warden_port -q -n 2`, then `python tests/redact_mutants.py`, `python
tests/gate_mutants.py` (HADAVIN_RUN_MUTANTS not needed: run by hand), `python tests/stage_mutants.py`. Green: all; every mutant
good.
Phase 3, G4a (runmap.py refactor and step). Run `pytest tests/test_b64_scan.py tests/test_p1c_gaps.py
tests/test_redact_fold_budget.py tests/test_redact_fold.py tests/test_redact_marks.py tests/test_redact_idempotent_property.py
tests/test_runmap_map_write.py tests/test_k5_fixes5.py tests/test_k5_layers.py tests/test_k5_round8.py tests/test_k5_round9.py
tests/test_k5_round9b.py tests/test_k1b_redaction.py tests/test_k1b_redaction_layers.py tests/test_k5_round10.py
tests/test_k5_producers.py tests/test_gate_mutants_picked_up.py -q -n 2`. Expected failures: exactly the G4c tests (ids with
`host`) that need the new host patterns: the 19 `test_host_row[host-NN]` of the closed rows of 9.2, I12b and the TB host-key
and tail tests; nothing else. Then `python
tests/redact_mutants.py` (63 mutants at HEAD, counted; review said 70), `python tests/b64_mutants.py`, `python
tests/textnorm_mutants.py runmap`, and the snippet check of 13.3. Green: as stated.
Phase 4, G4c (the host patterns, p1d_cases.py, p1d_a_mutants.py, gate.py comment). Run `pytest tests/test_p1c_gaps.py
tests/test_b64_scan.py tests/warden_port tests/test_p1d_a_rows.py tests/test_p1d_a_paths.py tests/test_text_parts_together.py
tests/test_model_gate.py tests/test_k1b_redaction.py tests/test_no_hardcoded_values.py -q -n 2`, `pytest tests/test_k5_perf.py
-m perf -p no:xdist -q`, `python tests/p1d_a_mutants.py`. Green: all, no expected failure left; every p1d_a mutant good.
Phase 5, G4d and documents: the redact.py docstring paragraph, CHANGELOG.md, SECURITY.md. Run the full suite (`pytest -q -n 2`),
`pytest -m perf -p no:xdist -q` (I16 and the redactor perf tests), ruff and bandit (13.5), the probe re-run on the G4 head.
Green: all; the probe shows 0 base64 leaks, 7 host rows readable (rows 6, 8, 9, 10, 15, 16, 42), numbers 24 / 2 / 17.

## 13. Tests and evidence
### 13.1 FAIL-BEFORE
`cp tests/p1c_cases.py tests/test_p1c_gaps.py /tmp/g4-base/tests/ && cp tests/fixtures/p1c_base_digests.json
/tmp/g4-base/tests/fixtures/ && cd /tmp/g4-base && uv run --all-extras --group test pytest tests/test_p1c_gaps.py -q`
Expected on HEAD's numbers: exactly 76 failures (57 base64: 52 leaks + 5 kind changes; 19 host rows); every other id passes
(I4, I9, I10, I11, I18, I25 included). The failing ids go into the evidence verbatim. `git worktree remove /tmp/g4-base`
afterwards. (v2's 78 counted 21 host rows on main; `-p no:randomly` dropped: pytest-randomly is not a dependency.)
### 13.2 Parity
I25 is a literal in the test (not read from evidence/). Phase 0 (c) is the proof that the probe and the copy build the same inputs.
### 13.3 Mutants
Pins that already exist (review M3): every `old` text of tests/redact_mutants.py, tests/p1d_a_mutants.py, tests/gate_mutants.py,
tests/stage_mutants.py and tests/textnorm_mutants.py whose file is guard/runmap.py or guard/redact.py occurs after G4 as many times
as at the base, with one exception: redact_mutants R3's `old` becomes
`"            time.thread_time() - started > defaults.REDACT_BUDGET_S\n        ):  # a hostile text"` (the loop moves from the
`try` of `redact_text` to the top level of `_scan`; the builder copies the exact text `ruff format` writes). In particular: mutant
21's `_deadline=started + defaults.REDACT_BUDGET_S` (twice, both in `_pass_one`), R1 `started = time.thread_time()` (once, in
`redact_text`), R2 (once, in `_scan`), DM-1/DM-1b (`_decoded_masks`, untouched), W13 (`_views`, untouched), p1d_a A16
`for view in views:` (once), gate R3/R3b/R3c `    mapping.update(current)\n    return out\n` (once:
tests/test_gate_mutants_picked_up.py checks "exactly once" on every run), and redact.py's N4/N8/W and A7-A45 texts (G4's new code
holds none of them, e.g. no `        return found\n`, no `(?<![\w.\-?&])`). Check (evidence): a one-off script that imports each M
list and prints `old`, file, count at base and at head. Killers of R2 (budget_1b), R3 (budget_2) and 21 stay killers: the
no-run texts they use make no extra clock read (I5).
New mutants, tests/b64_mutants.py (each must be KILLED, raw result in the evidence):
| mutant | killed by |
|---|---|
| skip the printable rule | TB `_b64_text` of base64 of `bytes(range(256))` is None; I4 binary row |
| accept a mixed alphabet run | TB `_b64_text` of a run with `+` and `_`; I4 path row |
| drop the `len % 4 == 1` rule | TB a 13-character body is None |
| drop the UTF-16 rules | 1b rows 70, 86 (I1) |
| drop the depth limit | I14 |
| drop the unit cap / the decoded-character cap / the clock check per unit | I13 (each its own case) |
| clock read before the gate (in `_b64_units` or `_pass_one` before the run search) | I5 (one extra read) |
| no placeholder blanking | I19 (`_b64_units` of `x <HIGHENTROPY_7> y` is not empty); I5 (one extra clock read per placeholder body) |
| no ANSI strip before the unit search | TB ANSI row (9.1) |
| no dedupe of identical units | TB 4 copies of one blob with the unit cap patched to 1 |
| held by any kind (v2 rule) | TB TENANT-held row (L12) |
| no whole-unit held test | TB: a wrapped ENCODED original redacted again with the same map is not decoded (a spy on `_b64_text` sees no call) |
| `TooDeep` in a decoded view propagates | TB TooDeep row |
| no size pre-check of the decoded join | TB with `MAX_REDACT_CHARS` patched small |
| views of T2 instead of T | I22 |
| ENCODED outside `SECRET_KINDS` | TB `_sweep("<ENCODED_1>", run) is _EVERY_COPY`; a glued copy masked |
| ENCODED in `STORED_KINDS` or given a grammar | I6 |
| counter not restored for ENCODED / `place_encoded` own counter rule | I7 |
| `place_encoded` splits pieces; original = decoded text | I8 |
| `_build` sort key without the kind | I7b |
| skip neutralise on the decoded text | TB `redact_untrusted` of base64 of `password=<FOO_1>` is ENCODED |
| skip `_views` on the decoded text | TB base64 of `password%3Dx...` is ENCODED |
| no held rule | I2 (80 HIGHENTROPY rows), I4 JWT rows |
| held = "run still readable" | TB the `PWd...=` row |
| mask only the found span inside the decoded text | I1 |
| drop the wrapped-line join / join any window of lines | 1c rows 1, 2, 5, 9; TB two unrelated short lines are not one unit |
| no separator fallback | I15 |
| first pass's map kept / decoded scan's map kept (L8 off) | I3 (no HIGHENTROPY entry); I8 (one entry); I23 (30 blobs over 40 entries) |
| ENCODED not in `_ASSIGNMENT_KINDS` | I24 |
| host: drop the tail / `_` not a label character / drop `[.]` | rows 1, 2, 17 / row 32 / row 43 |
| host: drop the `.internal`/`.local` guard; unkeep `.cluster.local` | KEPT `jdk.internal.reflect`, `threading.local()`; row 9 |
| host: Unicode label class | tests/test_text_parts_together.py `test_card_*cyrillic*` (by reading; else a TB look-alike row) |
| host-key: value without a digit, value starting with a digit, `server` key back, dotted values | `host x-ray`; `host 2026-11-20T10:00 started`; `Server: AmazonS3`; `Host: api.github.com` |
### 13.4 Perf mechanism (I16, review M9)
In tests/test_b64_scan.py, `@pytest.mark.perf`, run serially. Clock and repetition: `tests/fixtures/timing.block_seconds`, best
of `timing.REPEATS` (5). Baseline: the SAME build in the same test, with `runmap._B64_RUN` patched to `re.compile(r"(?!)")` (the
step is then one failed search per scanned spelling), measured interleaved with the step on. Constants at the top of the test,
each with its source: `PLAIN_RATIO = 1.15` (100,000 characters of snake_case and paths; prototype overhead 5.1 percent),
`PROSE_RATIO = 1.10` (100,000 characters of prose; prototype 0.7 percent), `PLANTED_RATIO = 1.15` (the snake_case text with one
`password=`), `FLOOR_S = 0.005` (a difference under 5 ms passes whatever the ratio: noise on a 0.13 s call), and
`CAP_CEILING_S = defaults.REDACT_BUDGET_S` for `B64_MAX_UNITS` distinct base64 secrets (one `redact_text`, thread CPU). The
baseline therefore measures the step's own cost, not the base commit; the HEAD numbers of section 8 are the reference recorded in
the evidence.
### 13.5 Evidence commands (raw output to evidence/G4-1.md)
- ruff check on the changed src files and the new and modified tests; `ruff format --check` on the same.
- each phase's selection of section 12, then the full suite `-n 2`, then `-m perf -p no:xdist`.
- the mutant runs of 13.3 and the snippet-count script.
- `uv run --group scan bandit -q -r src/hadavin_sdk/guard -ll`.
- the probe re-run on the G4 head with its totals; the B64_PRINTABLE_SHARE sweep of 7 (0.85 to 0.95).

## 14. Lead decisions (build default first, fallback if declined)
| id | question | build default | fallback |
|---|---|---|---|
| L1 | new kind name | ENCODED | SECRET (section 4 last paragraph) |
| L2 | host keys | `host`, `hostname`, `--host`, `--hostname` with `=`, `:` or space; one label that starts with a letter and holds a digit; no `server` key (changed from v2: `Server: AmazonS3` was a false positive) | `=` and `:` only: rows 33 and 36 become limits (17 closed) |
| L3 | rows 15, 16 (no private suffix) and row 10 (`.svc` short form) | stay unmasked, stated limits | add `svc` to `_HOST_BARE` (row 10 closes; every in-cluster short name is masked) |
| L4 | a fourth base64 level, and `TooDeep` inside a decoded view | the unit is masked unread | `TooDeep` refuses the whole text (repository convention of `undo`) |
| L5 | restore of underscore host names | grammar unchanged: not restorable | add `_` to `_GRAMMAR["HOSTNAME"]` |
| L6 | shortest run | 12 characters (row 83 closes) | 16 (row 83 a stated limit) |
| L7 | where the constants live | defaults.py, a SPINE commit | module constants in runmap.py (`1 << 16` for 65536) |
| L8 | decoded finds (CHANGED default) | only the ENCODED entries of the hit units are kept; the decoded view's finds and inner entries are thrown away | kept in the run map: plain copies of a decoded secret elsewhere are swept, BUT decoded EMAIL/HOSTNAME/IPV4 are in `defaults.STORED_KINDS` (defaults.py:124-138), so `agent_loop._save_map` stores them at rest and `restore_text` restores them (a value the document only ever wrote encoded); the map grows by at least two entries per hit; k1b's counts include values not shown |
| L9 | unit cap and what happens past it | `B64_MAX_UNITS` = `MAX_MAP_ENTRIES` (2000), refusal past it | 4,096 (v2), refusal past it |
| L10 | approvals/channel.py `_ASSIGNMENT_KINDS` | gains ENCODED | unchanged: a tag-split blob stays readable on a card (stated, as HIGHENTROPY today) |
| L11 | host label class | ASCII letters, digits, `_`, `-` (non-ASCII labels are the fold scan's) | Unicode `\w` (tests/test_text_parts_together.py CARDS re-derived first) |
| L12 | which pass-1 kinds hold a run | SECRET kinds (ENCODED included) and JWT/PRIVKEY substrings | any kind (v2): a TENANT- or HOSTNAME-held blob is never decoded |

## 15. Security notes, what stays out, rollback, reviewers, done
- No secret value is logged or put in an exception; `InputTooLarge` / `RedactionError` carry only their type name.
- The decoded text never leaves the redactor: only `<ENCODED_n>` is written; its original (the encoded run) lives in the run map
  in memory, is never stored (I6) and is swept in every copy. Under the L8 default no decoded value enters the map.
- Stays out: `redact()` / `redact_many` called directly; offsets other than 0; base32, hex, gzip; blobs glued to a prefix, split
  across fields or log prefixes; `tools.py` and `k1b/redaction.py`; any other pattern; HIGHENTROPY in `_ASSIGNMENT_KINDS`.
- Rollback: tag `pre-G4` on the base commit. No migration. Text already written with `<ENCODED_n>` stays as text.
- Reviewers: one correctness and one adversarial reviewer, fresh, given the diff, this ticket and evidence/G4-1.md only.
- Done: every phase green, FAIL-BEFORE recorded (76 ids), every mutant of 13.3 good, the snippet counts equal, the
  must-stay-green list green, ruff, bandit, CodeQL, SonarCloud, CodeRabbit green, the result review clean.

## For SECURITY wording and CHANGELOG (after the build, through the security wording review)
SECURITY.md, "Stated limits of redaction":
- A value written only in base64 (standard or URL-safe, padded or not, UTF-8 or UTF-16, wrapped at a fixed width, up to three
  levels deep) is masked whole as ENCODED by the redactor's decoded view; an ENCODED value is never stored or restored. Not
  found: a blob glued to other base64 characters, split across fields or across lines with a prefix, an all-capital blob
  written between `<` and `>`, base32, hex. A text with more than 2,000 distinct decodable base64 values is refused.
- A private host name (under `.corp`, `.lan`, `.intranet`, `.intra`, `.localdomain`, `home.arpa`, or ending in `.internal` /
  `.local`) is masked whole, and a single host label after `host`/`hostname` that holds a digit is masked; a dotted name with
  no private suffix is not; `.svc` short names, `.cluster.local` and AWS's own names are kept on purpose.
CHANGELOG.md, Unreleased, Upgrade steps: "**Redaction: base64 and host names (G4).** A value hidden in base64 is now masked as
`<ENCODED_n>` (a new kind, never stored or restored); a private host name is masked whole (`<HOSTNAME_1>` where
`<HOSTNAME_1>.example` was shown), also with `_` in a label or `[.]` dots, and `host db01` / `hostname=db01` mask `db01`. Texts
with more than 2,000 distinct base64 values are refused (`InputTooLarge`). Cost: <the I16 numbers measured in Phase 5>."

## (A) Round 1 (tickets/G4-review-1.md): what v2 resolved, kept
| finding | where now | state |
|---|---|---|
| g4r-B1 plug-in point; mapping into `out`; I1 false for held rows | 2.1-2.5, 3.3, 9.1, I1-I3 | resolved; now with signatures and the numbered body (round 2 B2) |
| g4r-B2 ENCODED creation, counters, `_PIECE`, reuse, label tests, I6 | 4, I6-I8 | resolved |
| g4r-B3 host-key grammar, position, group | 5.3, L2 | resolved; grammar tightened in v3 |
| g4r-B4 rows 10/15/16; keep mechanisms; tail; suffix list; grammar | 5.1-5.4, 9.2, I12, L3, L5 | resolved; recounted on HEAD (19 closed) |
| g4r-M5 decode rules; neutralise; recursion; depth | 3.2, 3.4, L4 | resolved |
| g4r-M6 join rule; candidate cap; budget; placeholders; `redact_many` | 3.1, 3.4, 7, 8, 3.5 | resolved; v2's "placeholders are never candidates" was false and is fixed in 3.1 point 2 (round 2 M4) |
| g4r-M7 G7 order, sweep, property test, call counts | 0, 2.5, I5, I17, I20, I21 | resolved; interplay now tested (round 2 M5) |
| g4r-M8 build default and fallback; defaults commit | 14, 7 | resolved |
| g4r-M9 builders, per-row table, FAIL-BEFORE, files, must-keep, mutants, `is_masked`, parity | 9-13 | resolved; builder RNG made pure (round 2 M2/M5) |
| readiness nits | whole ticket | resolved |
| g4c-B1 label, `SECRET_KINDS`, public function, counter test; `STORED_KINDS` unchanged | 4, I6, I7 | resolved |
| g4c-B2 the 90 non-leaked rows; JWT split | 3.3, 9.1, I2-I4 | resolved (held rule) |
| g4c-M1 21 of 24; second suffix list | 5.1, 9.2 | resolved; 19 of 22 open rows on HEAD |
| g4c-M2 host-key false positives, sweep and restore of words | 5.3 | resolved; `server` dropped in v3 |
| g4c-M3 cost bound; clock per candidate; one view; caps; gate apart from `scan` | 3.4, 7, 8, 3.1 | resolved; v2's contest of "`MAX_MAP_ENTRIES` enforced nowhere" is WITHDRAWN (it is enforced at agent_loop.py:427/547; round 2 M4/B3) |
| g4c-M4 `_clean`, `undo`, `fits_after_nfkc`, printable after decode, LE/BE | 3.2, 3.4 | resolved |
| g4c-M5 glued prefix, padding, row 83, `\/`, `%3D`, views, `Basic` | 3.1, 3.2, 9.1, L6 | resolved; glued prefix a stated limit |
| g4c-M6 tail, Java guard, underscore, non-ASCII, `[.]`, `_KEPT_HOST` | 5.2, 5.4, I11 | resolved; non-ASCII labels left to the fold scan (L11) |
| g4c-M7 prerequisites; G7 pins | 0, 11, I17 | resolved |
| code nits | 6, 4, 9.1 | resolved |

## (B) RUNG TABLE and NEEDED-CHECK (CODE-LAST v1, scale of 2026-11-06)
NEEDED-CHECK. Read at HEAD: runmap.py `redact_text`, `_views`, `undo`, `_clean`, `fits_after_nfkc`, `_decoded_masks`,
`_keep_earlier_masks`, `_GRAMMAR`, `storable`, `restore_text`, `enforce_map`, `snapshot`, `redact_bounded`, `redact_value`;
redact.py PATTERNS (HOSTNAME, BASIC, BEARER), `_KEPT_HOST`, `_LABELS`, `_OWN_OUTPUT`, `strip_ansi`, `_Redactor.__init__`,
`find`, `settle`, `_check_deadline`, `_over_budget`, `_fold_scan` (start), `_decide`, `_mask_ex`, `_place`, `_build`, `sweep`,
`SECRET_KINDS`, `_COMMON`, `_sweep`, `redact_many`; defaults.py `MAX_MAP_ENTRIES`, `REDACT_BUDGET_S` and its comment,
`STORED_KINDS`; tools.py `redact_layered`, `MARKER`; k1b/redaction.py `redact_bundle`; approvals/channel.py `clean`,
`_TAGS`, `_ASSIGNMENT_KINDS`, `settled`; approvals/gate.py `_PLACEHOLDER_DOT`, `_defang_prose`; agent_loop.py 420-432, 540-552.
Verdict: NEEDED for G4a and G4c; G4d is a docstring and a pin.
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| base64 decoded view | a secret only written in base64 is masked | 2 core: `_views` (no base64), `tools._b64_holds` (known handed-out values only, not on the `redact_text` path), `k1b._pair` (one Kubernetes value); 3 tools: none in-process; 4 library: stdlib `base64` (no new dependency); detect-secrets / gitleaks style scanners UNVERIFIED, not fetched, not usable in-process on the redaction path | probe on main and on HEAD; prototype | decode tied to the redactor's patterns, map, views, caps and deadline | KEEP-CODE, small |
| kind ENCODED | a mask that says "decoded blob", never restorable | 2 core: SECRET exists | section 4 | the label only | KEEP-CODE (fallback SECRET, L1) |
| whole host name, host key | the full dotted name is masked | 2 core: HOSTNAME too narrow; 4 library: a public-suffix list, UNVERIFIED, needs an update path | probe; prototype | - | KEEP-CODE: a pattern change |
| bare numbers | written down | 2 core: decision order 64 item 4 | probe | - | CUT to a docstring and a pin |

## (C) NOT CHECKED
- Nothing was built and no pytest run was made by the drafter. Run read-only on HEAD 193605f: the probe (all tables), the
  sha256 of the 229 inputs, `redact_text` idempotence on the 229 rows, `redact_untrusted` second-pass change count, a few
  `redact_text` / `channel.clean` outputs (rows 1, 24, 31, 32, 39-41, 43; `host 10.20.30.40.example.com`), the timing of 8, and
  `_b64_text` (v2 rules, scratch copy) on placeholder bodies (`CREDITCARD_1`, `SECRET_REDACTED`, `AZURERESOURCE_12` decode to
  bytes that fail UTF-8; `HIGHENTROPY_1` is 13 characters, `len % 4 == 1`).
- The behaviour of the four p1d_a mutants after G4 (A4, A5, A38, A6) and of `test_text_parts_together` CARDS under a Unicode
  label class: by reading only.
- Every "prototype" number (main 51c9fc4, no fold scan, no MJ-B); the cost of the step on HEAD; timing on Windows or under load.
- The G7 round 3 and gate round 4 fixes (not in HEAD).
- Whether the modified property test is green on the base with the probe-order gap2/gap3 values and the 142 base64 rows
  (Phase 0 f).
- Whether k1b fixtures hold base64 that decodes (they would gain an `ENCODED` count only).
- Real dumps for the cost of the caps (8).
- How the approval card and the model gate show ENCODED to an operator beyond `_ASSIGNMENT_KINDS`.

## (D) Plan review round 2 (tickets/G4-review-2.md): every finding
Readiness reviewer:
| id | finding (short) | state | where / reason |
|---|---|---|---|
| B1 | p1d L2/L3 (and the JSON base records) go red; grep the tests tree | TAKEN, JSON part CONTESTED | 9.3 (H27, L2, L3 with exact new strings; whole-tree grep listed; p1d_a mutant killers re-pointed). The JSON is not edited: it records the base commit 2742c1b's output and is read only for `BS0` cells (test_p1d_a_rows.py:29-42); H27/L2/L3 cells are literals, so the edit would falsify a record and change no test |
| B2 | the central refactor unspecified | TAKEN | 2.2 (signatures, `_ScanBudget`, `_B64Unit`), 2.3-2.5 (numbered bodies), 2.4 step 3 and 6 (which text the views, `_decoded_masks` and `_keep_earlier_masks` see: T, never T2) |
| M1 | no build order | TAKEN | 12 (phases 0-5, selection and green state each; reviewer's order defaults, G4b, G4a, G4c, G4d) |
| M2 | RNG-dependent test data; 1,835 | TAKEN | 11 `build()` with a private `Random`; property test imports it; count 1,977 (I17) |
| M3 | I4 "79 of 79" vs the two privacy rows | TAKEN | I4 = 77 rows (17 + 60, counted), I12b; "79" withdrawn |
| M4 | "MAX_MAP_ENTRIES enforced nowhere" is false | TAKEN | 8 (agent_loop.py:427, :547), L9, I23; the v2 contest withdrawn |
| M5 | no G7/MJ-B and fold interplay test; NotSettled; rows 31/41 | TAKEN | 2.5, 2.6, I20, I21; rows 31/41 measured on HEAD (already masked) and Phase 0 (b) stops on any row difference |
| M6 | neutralise on views of T2 escapes `<ENCODED_1>` | TAKEN | 2.4 step 3 (views of T only), I22 |
| M7 | base-output fixture, FAIL-BEFORE copy, sha256 literal, I4 literal | TAKEN | 11 (digests fixture and its script in Create), 13.1 (three files copied), I25 literal, `MUST_KEEP_B64` literal |
| M8 | `Server: AmazonS3`, `hostname: Web2` | TAKEN | 5.3 (`server` key dropped, letter-first value with a digit; AmazonS3 a must-keep row; `hostname: Web2` masked on purpose, stated), L2 |
| M9 | I16 perf mechanism | TAKEN | 13.4 |
| nit | `tools/mutants` does not exist | TAKEN | 13.3: `tools/mutation_runner.py` through tests/b64_mutants.py |
| nit | must-stay-green omits settle-loop and fold suites | TAKEN | 11 |
| nit | unsourced numbers | TAKEN | 7 (source per constant), 8 (HEAD timing measured, estimates dropped) |
| nit | `place_encoded` numbering and shared originals | TAKEN | 4 points 4-5, I7, I7b |
| nit | section 7 comment text | TAKEN | 7 |
| nit | `no_digit_line` at import | TAKEN | 11: lazy cached `build()`, 1.6 s measured, both searches find nothing and stay for the RNG stream |
| nit | `-p no:randomly` | TAKEN | dropped (13.1) |
| nit | "2.4x" and "about 2 s" are estimates | TAKEN | dropped (8) |
| claim check | round-1 B1/B4/M6 | TAKEN | as B2, B1, M4 above |
Codebase-details reviewer:
| id | finding (short) | state | where / reason |
|---|---|---|---|
| B1 | H27, L2, L3 red; gate.py:230-232 note | TAKEN | 9.3 |
| B2 | L-B3 false; k1b counting | TAKEN | 3.5 |
| B3 | MAX_MAP_ENTRIES enforced; bound growth; only-ENCODED default; small-ceiling test | TAKEN | 8, L8 default flipped, L9, I23 |
| M1 | I4 vs 9.2; 62 listed, 17 unlisted | TAKEN | I4 and 11 (all 17 listed, 48 + 14 = 62 counted from the file) |
| M2 | integration does not give the recursion; which text | TAKEN | 2.2-2.5 |
| M3 | tests/redact_mutants.py pins | TAKEN, count CONTESTED | 13.3; the file has 63 mutant entries at HEAD (counted `m(` calls), not 70 |
| M4 | placeholders are run candidates | TAKEN | 3.1 point 2, I19 |
| M5 | shared RNG; pure `build()` | TAKEN | 11; `build()` returns all 229 rows plus the 16 plain values |
| M6 | test_no_hardcoded_values / lockin rules | TAKEN | 11 (examples in `#` comments only), must-stay-green |
| M7 | caps refuse legitimate input; TooDeep in decoded views | TooDeep part TAKEN; cap part PARTLY CONTESTED | 2.6, L4 (TooDeep and an over-size decoded join masked unread); past the unit or decoded-character cap the call is still refused: masking every further unit unread would over-mask benign runs and add entries past the map ceiling (which refuses the run anyway); the cost is stated in 8 |
| M8 | `_ASSIGNMENT_KINDS` | TAKEN | 4 point 8, L10, I24 |
| nit | MJ-B "being built" but in HEAD | TAKEN | header, 0 |
| nit | REDACT_BUDGET_S comment only lacks the decoded scan | TAKEN | 7 (one clause) |
| nit | CHANGELOG.md, SECURITY.md | TAKEN | 11, "For SECURITY wording and CHANGELOG" |
| nit | CountedClock: zero clock reads for no-run text | TAKEN | 3.4 point 1, I5 |
| nit | `reverse` last-wins vs `_build` first-wins | TAKEN | 4 points 4-5, I7b |
| nit | runs inside ANSI escapes | TAKEN | 3.1 point 5 (stripped before the search, not a limit) |
| nit | `\x1e` and `splitlines` in `_fold_scan` | TAKEN | 3.4 point 9, I15 |
| nit | HOSTKEY `host x-ray`, `host re-election`, `host 2026-11-20T10:00` | TAKEN | 5.3 must-keep rows |
| nit | L8 decoded EMAIL/HOSTNAME/IPV4 stored at rest | TAKEN | L8 (default flipped; the storage question is the fallback's cost) |
| nit | I9 corpus needs the 142 base64 rows | TAKEN | I9 over all 229 in TG, and group `p1c-b64` in the property test (I17) |
| forgotten suites | settle loop, map write, perf, fold budget, round10, k1b x2, producers, no-hardcoded, lockin, fixes5, layers, round8/9/9b, p1d rows, redact_mutants | TAKEN | 11 must-stay-green, 12 per phase; added beyond the list: p1d_a_mutants (killers), gate_mutants (exactly-once check), stage_mutants, textnorm_mutants, test_text_parts_together, test_model_gate, fixes7, fixes9, round5 |
Counts: readiness 2 Blockers + 9 Majors + 8 nits + the claim check: all TAKEN, one part contested (B1's JSON). Codebase 3
Blockers + 8 Majors + 10 nits + the suites list: all TAKEN; contested in part: M3's mutant count (63, not 70) and M7's cap
behaviour (refusal kept, cost stated).
