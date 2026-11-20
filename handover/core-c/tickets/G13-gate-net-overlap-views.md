# G13: the gate net reads overlap pieces and decoded forms (E19 M1, M2, N1-N3): BUILD TICKET

Owner core-c. Builder: one sonnet session, scratch copy first, then the branch. Drafted 2026-11-20 by a read-only drafter on a
`git archive` of `cloud/core-c` HEAD **72fd2cc8a** (= G8, G10, E14, G9, and the five G4 commits b4ac466..72fd2cc). Every number
below is labelled: MEASURED (direct `uv run python` on that archive and on a prototype copy of it, no pytest), REASONED, NOT RUN.
Inputs: ESCALATIONS E19, requests/xr-textfold-lead-1.md, evidence/E19-M2-producers-table.md, /tmp/xr_m1.py, G9 v3 ticket.
Lead verdict E19: M1, M2 fix now (leaks). This ticket is the GATE net; G9 already fixed the PRODUCER path.

## 0. What is true on HEAD 72fd2cc8a (re-measured before writing; do not skip 3.1)
- M1 exact input (map {<SECRET_1>: "hunter2-ABCDEFGH", <SECRET_2>: "ABCDEFGH-ZZZZZZZZ"}, text "x hunter2-ABCDEFGH-ZZZZZZZZ y"):
  MEASURED. Pre-G9 (9652b20aa~1): enforce_map -> `x hunter2-<SECRET_2> y` and held_value_left False (the leak E19 recorded).
  HEAD: enforce_map -> `x <SECRET_1><SECRET_2> y` in BOTH map orders; redact_text -> `x <SECRET_3> y`. G9's read-back closes it.
  The finder is NOT the cause (redact.py `_build` compiles `(?=(trie))`: a lookahead finder already reports overlapping starts);
  the leak was the replace order, fixed by G9's `_overlaps`/`_close`. So the lead's "`original in segment` / lookahead finder"
  half of M1 needs NO code: G13 keeps the exact input as a pin (G13-1).
- M1 net half still open, MEASURED: held_value_left reads back only the SECRET placeholders (the checker is built over the
  secret entries only), so a secret piece beside an IDENTIFIER key, or beside a key whose value does not continue it, is not
  seen: `x hunter2-<HOST_1> y` -> False; `x hunt<SECRET_2> y` -> False; `<SECRET_1>abcdef` (SECRET_2 = `>abcdef`) -> False
  and is SENT (pinned as fine by test_r2_m2). Fuzz (random 2-3 overlapping values cut from one string, kinds SECRET/APIKEY/
  BEARER/HOST/TENANT, enforce + net, 4-gram oracle): alphanumeric values HEAD 0 leaks / 12,000 (pre-G9 9 / 4,000); values with
  `<` `>` `_` (edge and held-back values) HEAD 46 leaks / 8,000.
- M2, MEASURED through `BoundGate.chat` (map {<SECRET_1>: TOKEN, ...}): UTF-16LE document, UTF-16LE with BOM, NUL-split
  message, ZWSP-split document, full-width document, percent-encoded message, `\u`-escaped message: all SENT, row ("ok", None).
- Pre-existing reds on 72fd2cc8a, NOT G13's (G4 x G9, lead item L24): test_e5b (TB-2.11) in test_runmap_enforce_map.py,
  TB-2.8 and TB-3.4 in test_b64_scan.py. Record them in the baseline; do not touch them.

## 1. Scope
IN: runmap.py (`held_value_left` + new `_touching_piece`, `held_in_views`, `_windows`, `_piece_index`, `_starts_one`, snapshot
field `pieces`; `_canonical_view`/`replace_canonical` `drop` parameter; `escape_markers`; docstrings of `escape_placeholders`,
`enforce_map`), model_gate.py (`_chunk` one line; module docstring), tests/test_model_gate.py, tests/test_runmap_enforce_map.py,
tests/gate_mutants.py. OUT: redact.py (G9 owns the producer overlap; G12 owns `_place`), textnorm.py (M3 builder), producers,
k1b, extract.py, contract tests (tests/contracts/*: core-a's side; if one pins "UTF-16 sent as written" core-a updates it).

Rules the diff implements:
- M1 (net): a KEY of the snapshot with, touching it on the left, a piece of >= 4 characters that is the START of a secret
  value (prefix), or on the right a piece that is the END of one (suffix), makes `held_value_left` True -> CODE_HELD_LEFT.
  Read window: from the key back to the previous key (or forward to the next), at most longest-value - 1 characters. Lookup:
  only where the piece's first (left) / last (right) 4 characters are a value's head/tail (frozensets), then one bisection
  in the sorted values (or sorted reversed values). Each lookup spends its characters from the call's EnforceBudget.
- M2: `_chunk` runs `held_value_left(fixed)` and then `held_in_views(fixed)`: the views are `_clean(fixed)` (NUL and lone
  surrogates out) when it differs, plus `_views(cleaned)` when cleaned is non-ASCII or holds `\` `%` `&` (the producer's own
  trigger, runmap `_scan`). Any view where `held_value_left` is True refuses with CODE_HELD_LEFT ("a view holds a secret the
  raw text did not": the raw text was checked first, so any True here is that). A text over `VIEW_WINDOW` = MAX_REDACT_CHARS
  // 4 (65,536) is cut into windows overlapping 10 x longest + 16 (`_views` refuses a form over MAX_REDACT_CHARS; the gate
  holds texts up to 8 x that). `_views` may raise InputTooLarge (-> mask_budget_exceeded) or TooDeep (-> mask_refused).
- N3: the marker search drops Mn/Me as well as Cf (nothing else uses the parameter). N2: docstring. N1: section 6.

## 2. The source diff (exact; prototype on the 72fd2cc8a archive, ruff format/check clean)
Apply with search text, not line numbers (HEAD may move). sha256 prefixes of the prototype diffs: runmap 62c180dd4c8048e6,
model_gate 416f2b56b2b9508b (`git diff -U1` / `-U0` from 72fd2cc8a).

```diff
--- a/src/hadavin_sdk/guard/runmap.py
+++ b/src/hadavin_sdk/guard/runmap.py
@@ -319,5 +319,11 @@ _ASCII_OR_ONE = re.compile(r"[\x00-\x7f]+|[^\x00-\x7f]")  # a run of ASCII, or o
 
-def _canonical_view(text: str) -> tuple[str, list[int]]:
-    """The canonical form of `text` (NFKC, invisible format characters removed) and, for each canonical
-    character, the index of the original character it came from."""
+_INVISIBLE = frozenset({"Cf"})
+# G13 (E19 N3): what the result-marker search also drops. `canonical` composes nothing, so a combining mark after `<` (U+0338)
+# stays between the two `<` of a marker look-alike and `_MARKER` did not match it.
+_INVISIBLE_OR_MARK = frozenset({"Cf", "Mn", "Me"})
+
+
+def _canonical_view(text: str, drop: frozenset[str] = _INVISIBLE) -> tuple[str, list[int]]:
+    """The canonical form of `text` (NFKC, characters of a category in `drop` removed: by default the invisible format
+    characters) and, for each canonical character, the index of the original character it came from."""
     chars: list[str] = []
@@ -331,3 +337,3 @@ def _canonical_view(text: str) -> tuple[str, list[int]]:
         for d in unicodedata.normalize("NFKC", piece):
-            if unicodedata.category(d) != "Cf":
+            if unicodedata.category(d) not in drop:
                 chars.append(d)
@@ -338,3 +344,6 @@ def _canonical_view(text: str) -> tuple[str, list[int]]:
 def replace_canonical(
-    text: str, pattern: re.Pattern[str], repl: Callable[[re.Match[str]], str]
+    text: str,
+    pattern: re.Pattern[str],
+    repl: Callable[[re.Match[str]], str],
+    drop: frozenset[str] = _INVISIBLE,
 ) -> str:
@@ -346,3 +355,3 @@ def replace_canonical(
         return pattern.sub(repl, text)
-    canon, index = _canonical_view(text)
+    canon, index = _canonical_view(text, drop)
     out: list[str] = []
@@ -364,4 +373,6 @@ def escape_placeholders(text: str) -> str:
     would look like the placeholder the redactor later issues to a different value, and restore or the grounding
-    check would treat it as that value. Every placeholder-shaped literal becomes a non-placeholder. Call it on
-    `canonical(text)`, so Unicode look-alikes are already ASCII."""
+    check would treat it as that value. Every placeholder-shaped literal becomes a non-placeholder. It is found in the canonical
+    view (NFKC one character at a time, invisible format characters removed), so a COMPATIBILITY spelling (full-width
+    `＜ＩＰＶ４＿２＞`, a zero-width space inside) is caught; a confusable from another script that NFKC keeps (Cyrillic `А` for
+    `A`, UTS #39 look-alikes) is not folded and is not escaped (G13, E19 N2)."""
     return replace_canonical(text, _LOOKALIKE, lambda m: f"\u2039{m.group(1)}_{m.group(2)}\u203a")
@@ -375,4 +386,5 @@ def escape_markers(text: str) -> str:
     zero-width spellings (found in the canonical form, rewritten in the original; the rest of the text is left
-    as it was written)."""
-    return replace_canonical(text, _MARKER, lambda m: "[[")
+    as it was written). Combining marks are dropped for this search too (G13, E19 N3): `<<` + U+0338 + `TOOL RESULT` is a
+    marker look-alike."""
+    return replace_canonical(text, _MARKER, lambda m: "[[", _INVISIBLE_OR_MARK)
 
@@ -1084,3 +1096,3 @@ def enforce_map(text: str, mapping: Mapping[str, str]) -> str:
       not cleaned either: a copy split by NUL characters (a UTF-16 document read as UTF-8 has one after
-      every character) is not found.
+      every character) is not found. The gate's net reads those forms of a SECRET value (`held_in_views`, G13).
     - A value that itself holds a placeholder-shaped token (`ab<X_1>cd`) is never replaced: the sweep
@@ -1097,3 +1109,4 @@ def enforce_map(text: str, mapping: Mapping[str, str]) -> str:
       on the raw text, with every placeholder set aside; where it touches a placeholder that is ALREADY in the
-      text it is not replaced (the `>` belongs to that placeholder) and its tail stays readable.
+      text it is not replaced (the `>` belongs to that placeholder) and its tail stays readable (4 or more characters
+      of a SECRET value there: the net refuses the call, `_touching_piece`, G13).
     - A map key that is not a genuine placeholder (`<host_1>`: lower case) is not set aside by any sweep,
@@ -1150,2 +1163,4 @@ class MapSnapshot(dict):
     checker: Any  # a redactor over exactly those secret values, for `held_value_left`
+    # `_piece_index` of the secret values (G13)
+    pieces: tuple[list[str], list[str], frozenset[str], frozenset[str], int]
 
@@ -1289,2 +1304,3 @@ def snapshot(mapping: Mapping[str, str], cache: dict[str, Any] | None = None) ->
         known.checker = _built(secrets, cache, "check", deadline) if secrets else None
+        known.pieces = _piece_index(known.secret_values)
     except RedactionError:
@@ -1296,2 +1312,96 @@ def snapshot(mapping: Mapping[str, str], cache: dict[str, Any] | None = None) ->
 
+# G13 (E19 M1): the shortest piece of a secret value that the net reads as a leak where it touches a placeholder.
+NET_MIN_PIECE = 4
+
+
+def _piece_index(
+    values: frozenset[str],
+) -> tuple[list[str], list[str], frozenset[str], frozenset[str], int]:
+    """G13: the secret values longer than `NET_MIN_PIECE`, sorted; their reversals, sorted; the first and the last
+    `NET_MIN_PIECE` characters of each; the longest length. `_touching_piece` looks a piece up by bisection."""
+    fwd = sorted(v for v in values if len(v) > NET_MIN_PIECE)
+    rev = sorted(v[::-1] for v in fwd)
+    heads = frozenset(v[:NET_MIN_PIECE] for v in fwd)
+    tails = frozenset(v[-NET_MIN_PIECE:] for v in fwd)
+    return fwd, rev, heads, tails, max(map(len, fwd), default=0)
+
+
+def _starts_one(ordered: list[str], piece: str) -> bool:
+    """True when some string of the sorted list `ordered` starts with `piece`."""
+    i = bisect.bisect_left(ordered, piece)
+    return i < len(ordered) and ordered[i].startswith(piece)
+
+
+def _touching_piece(text: str, snap: MapSnapshot) -> bool:
+    """G13 (E19 M1): True when a KEY of the map has, right before it, a piece of `NET_MIN_PIECE` or more characters
+    that is the START of a secret value (shorter than the value), or right after it a piece that is the END of one:
+    `hunter2-<SECRET_2>`, `<SECRET_1>-ZZZZ`. Such a piece is what is left when two known values overlap and one was
+    masked across the other, whatever the placeholder holds. Only the text between the key and the next (or previous)
+    key is read, at most the longest value's length minus one. A piece is looked up only where its
+    first (left) or last (right) `NET_MIN_PIECE` characters are those of a value; each lookup's characters are spent
+    from the call's budget (`InputTooLarge` past it)."""
+    fwd, rev, heads, tails, longest = snap.pieces
+    if not fwd:
+        return False
+    budget, k = snap.budget, NET_MIN_PIECE
+    tokens = [m.span() for m in _PLACEHOLDER.finditer(text) if m.group() in snap]
+    for n, (start, end) in enumerate(tokens):
+        if not n % 256:
+            budget.check()
+        before = tokens[n - 1][1] if n else 0
+        after = tokens[n + 1][0] if n + 1 < len(tokens) else len(text)
+        left = text[max(before, start - longest + 1) : start]
+        for i in range(len(left) - k, -1, -1):  # the piece left[i:] ends at the key
+            if left[i : i + k] in heads:
+                budget.spend_chars(len(left) - i)
+                if _starts_one(fwd, left[i:]):
+                    return True
+        right = text[end : min(after, end + longest - 1)]
+        for j in range(k, len(right) + 1):  # the piece right[:j] starts at the key
+            if right[j - k : j] in tails:
+                budget.spend_chars(j)
+                if _starts_one(rev, right[:j][::-1]):
+                    return True
+    return False
+
+
+def held_in_views(text: str, snap: MapSnapshot) -> bool:
+    """G13 (E19 M2): the net over the forms of `text` a reader (or the model) may decode: the text without NUL and lone
+    surrogates (a UTF-16 document read as UTF-8) and, when it holds a non-ASCII character or `\\`, `%` or `&`, every
+    `_views` form of that. True when `held_value_left` finds a secret value in any of them. Each view's characters are
+    spent from the call's budget; a text whose views would pass `defaults.MAX_REDACT_CHARS` is read in overlapping
+    windows. `_views` can raise `InputTooLarge` or `TooDeep`: the caller refuses the call."""
+    if not snap.secret_values:
+        return False
+    cleaned = _clean(text)
+    views = [cleaned] if cleaned != text else []
+    if not cleaned.isascii() or any(c in cleaned for c in "\\%&"):
+        for window in _windows(cleaned, max(map(len, snap.secret_values))):
+            views += _views(window)
+    for view in views:
+        snap.budget.spend_chars(len(view))
+        snap.budget.check()
+        if held_value_left(view, snap):
+            return True
+    return False
+
+
+# G13: a text longer than this is read by `held_in_views` in windows of this size (`_views` refuses a form past
+# `defaults.MAX_REDACT_CHARS`, and NFKC can triple a text; the gate holds texts up to 8 times that cap).
+VIEW_WINDOW = defaults.MAX_REDACT_CHARS // 4
+
+
+def _windows(text: str, longest: int) -> list[str]:
+    """`text` whole when it fits one window, else windows of `VIEW_WINDOW` characters that overlap by ten times the
+    longest secret value plus 16 (an escaped spelling is at most ten characters a character: `&#1114111;`). An overlap of
+    half a window or more is `InputTooLarge`."""
+    if len(text) <= VIEW_WINDOW:
+        return [text]
+    overlap = 10 * longest + 16
+    if overlap * 2 >= VIEW_WINDOW:
+        raise InputTooLarge("InputTooLarge")
+    step = VIEW_WINDOW - overlap
+    return [text[i : i + VIEW_WINDOW] for i in range(0, len(text) - overlap, step)]
+
+
 def held_value_left(text: str, snap: MapSnapshot) -> bool:
@@ -1311,3 +1421,5 @@ def held_value_left(text: str, snap: MapSnapshot) -> bool:
     )
-    return snap.checker.sweep(opened, snap.budget.cpu_deadline) != opened
+    if snap.checker.sweep(opened, snap.budget.cpu_deadline) != opened:
+        return True
+    return _touching_piece(text, snap)  # G13 (E19 M1)
 
```

```diff
--- a/src/hadavin_sdk/guard/model_gate.py
+++ b/src/hadavin_sdk/guard/model_gate.py
@@ -20,2 +20,3 @@ sweep and follows its rule (`redact._sweep`); the full list with the reasons is
-  the placeholder written for another.
-  T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate
+  the placeholder written for another. Since G13 (E19 M2) the net reads those forms: for a value of a SECRET kind the
+  call is then refused (`held_value_left`); an identifier in such a form passes as written.
+  T::test_t7_a_hidden_spelling_of_a_known_secret_refuses_the_call_an_identifier_passes
@@ -25,3 +26,4 @@ sweep and follows its rule (`redact._sweep`); the full list with the reasons is
-- A copy split by NUL characters (a UTF-16 document: the gate reads documents as UTF-8) or by an ANSI colour
-  sequence passes: the gate does not clean the text, the producers' redactor does.
-  T::test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced
+- The gate does not clean the text it sends. A copy of a SECRET value split by NUL characters (a UTF-16 document: the
+  gate reads documents as UTF-8) refuses the call (G13: the net reads the text without NUL); a copy of an identifier split
+  so, and any copy split by an ANSI colour sequence, passes as written.
+  T::test_d7_a_copy_split_by_nul_or_utf16_refuses_the_call_an_ansi_split_copy_passes
@@ -48 +50,2 @@ sweep and follows its rule (`redact._sweep`); the full list with the reasons is
-  tail stays readable (`<SECRET_1>abc`), but the placeholder is never cut open.
+  tail stays readable (`<SECRET_1>abc`), but the placeholder is never cut open. For a SECRET value the net refuses
+  the call when 4 or more of its characters stand there (G13).
@@ -60 +63,9 @@ sweep and follows its rule (`redact._sweep`); the full list with the reasons is
-  refuse every value that merely lies inside a fixed word (`ESULT`).
+  refuse every value that merely lies inside a fixed word (`ESULT`). G13 (E19): the net also refuses (1) a piece of 4 or
+  more characters of a SECRET value that touches a key of the map and is the value's start (before the key) or end (after
+  it): `hunter2-<SECRET_2>`, and (2) a SECRET value found in a decoded form of the chunk (`runmap.held_in_views`: without
+  NUL, NFKC, invisible characters removed, JSON/percent/entity/backslash escapes undone, composed). NOT read: a piece from
+  the middle of a value between two keys, a piece one character away from a key, a piece shorter than 4, another letter
+  case, an ANSI-split copy, a base64-encoded copy (the producers' G4 step).
+  T::test_g13_10_a_secret_in_a_decoded_form_refuses_the_call
+  T::test_g13_13_m1_a_secret_prefix_beside_a_key_refuses_the_call
+  E::test_g13_4_boundaries_of_the_piece_rule
@@ -745 +756 @@ class BoundGate:
-        if runmap.held_value_left(fixed, mapping):
+        if runmap.held_value_left(fixed, mapping) or runmap.held_in_views(fixed, mapping):
```

## 3. Tests (red before, green after)
### 3.1 Phase 0: `uv run python` the M1 repro (both map orders) and section 0's M2 cases on the head first (stop rule 1).

### 3.2 Append to tests/test_runmap_enforce_map.py (then `ruff format` the file; the ids in the messages are the mutant expects)
```python
# --- G13 (E19 M1, N3): the gate net reads a piece of a secret value beside a key; the marker look-alike with a mark -------
M1_A, M1_B = "hunter2-" + "ABCDEFGH", "ABCDEFGH" + "-ZZZZZZZZ"  # the review's two overlapping secret values
M1_TEXT = "x hunter2-ABCDEFGH-ZZZZZZZZ y"


def _g13_snap(extra=None):
    entries = {"<SECRET_1>": M1_A, "<SECRET_2>": M1_B, "<HOST_1>": "db1.corp.example.org"}
    return runmap.snapshot(runmap.RunMap({**entries, **(extra or {})}))


def test_g13_1_the_review_input_leaves_no_piece_in_either_map_order():
    """G13-1 (E19 M1, review input; green since G9, kept as the pin): enforce plus the net never send `hunter2-` or `-ZZZZZZZZ`."""
    for entries in ({"<SECRET_1>": M1_A, "<SECRET_2>": M1_B}, {"<SECRET_1>": M1_B, "<SECRET_2>": M1_A}):
        snap = runmap.snapshot(runmap.RunMap(entries))
        out = runmap.enforce_map(M1_TEXT, snap)
        sent = not runmap.held_value_left(out, snap)
        assert not (sent and ("hunter2-" in out or "-ZZZZZZZZ" in out)), "G13-1 a piece of an overlapping secret was sent"


def test_g13_2_a_secret_prefix_beside_a_key_is_held():
    """G13-2 (E19 M1): `hunter2-` (the first 8 characters of a secret value) right before a placeholder of the map."""
    assert runmap.held_value_left("x hunter2-<HOST_1> y", _g13_snap()), "G13-2 the prefix beside a key was not seen"


def test_g13_3_a_secret_suffix_beside_a_key_is_held():
    """G13-3 (E19 M1): `-ZZZZZZZZ` (the last 9 characters of a secret value) right after a placeholder of the map."""
    assert runmap.held_value_left("x <HOST_1>-ZZZZZZZZ y", _g13_snap()), "G13-3 the suffix beside a key was not seen"


def test_g13_4_boundaries_of_the_piece_rule():
    """G13-4: 4 characters touching a key are a piece; 3 are not; a space between, a token that is not a key of the map
    and a piece from the middle of a value are not read (stated limits)."""
    snap = _g13_snap()
    assert runmap.held_value_left("x hunt<HOST_1> y", snap), "G13-4 four characters before a key were not seen"
    assert runmap.held_value_left("x <HOST_1>ZZZZ y", snap), "G13-4 four characters after a key were not seen"
    assert not runmap.held_value_left("x hun<HOST_1> zzz y", snap), "G13-4 three characters were read as a piece"
    assert not runmap.held_value_left("x hunt <HOST_1> y", snap), "G13-4 a piece one space away was read"
    assert not runmap.held_value_left("x hunt<FAKE_1> y", snap), "G13-4 a token that is not a key was read"
    assert not runmap.held_value_left("x <HOST_1>ter2-AB<HOST_1> y", snap), "G13-4 a middle piece was read"


def test_g13_5_a_held_back_value_beside_a_placeholder_written_before_is_refused_not_sent():
    """G13-5 (E19 M1; was the r2-M2 pin `<SECRET_1>abcdef` sent): the tail of `>abcdef` beside a placeholder is 6 of its 7
    characters; the net refuses it now."""
    snap = runmap.snapshot(runmap.RunMap({"<SECRET_1>": "S3cr" + "3t", "<SECRET_2>": ">abc" + "def"}))
    assert runmap.held_value_left("<SECRET_1>abcdef", snap), "G13-5 the tail of a held-back value was not seen"
    assert not runmap.held_value_left("<SECRET_1> abc", snap), "G13-5 three characters after a space were read"


def test_g13_6_the_piece_check_spends_the_call_budget():
    """G13-6: each piece looked up spends its characters from the call's budget; past it, InputTooLarge (fail closed)."""
    snap = _g13_snap()
    snap.budget.chars = 1_000  # 150 lookups of 8 characters
    try:
        runmap.held_value_left("q huntXXXX<HOST_1> " * 150, snap)
    except runmap.InputTooLarge:
        return
    raise AssertionError("G13-6 the piece lookups spent nothing")


def test_g13_8_the_views_spend_the_call_budget():
    """G13-8 (E19 M2): each decoded form the net reads spends its characters from the call's budget."""
    snap = _g13_snap()
    snap.budget.chars = 1_000
    try:
        runmap.held_in_views("\uff57ord " * 400, snap)  # 2,000 characters; the canonical form differs (full-width w)
    except runmap.InputTooLarge:
        return
    raise AssertionError("G13-8 the views spent nothing")


def test_g13_7_a_marker_look_alike_with_a_combining_mark_is_escaped():
    """G13-7 (E19 N3): `<<` + U+0338 + `TOOL RESULT` is escaped like the plain marker; text with no marker keeps its marks."""
    assert runmap.escape_markers("<<\u0338TOOL RESULT call_id=x>>").startswith("[["), "G13-7 the look-alike stayed"
    assert runmap.escape_markers("<\u0338<tool result").startswith("[["), "G13-7 a mark between the two < kept it"
    assert runmap.escape_markers("cafe\u0301 x") == "cafe\u0301 x", "G13-7 a text with no marker changed"
```

### 3.3 Append to tests/test_model_gate.py (`GateRefused` is already imported there), then `ruff format`
```python
# --- G13 (E19 M2): the net also reads the decoded forms of every enforced chunk ------------------------------------------
FULL_WIDTH = "".join(chr(ord(c) + 0xFEE0) for c in TOKEN)
def _g13_outcome(bound, messages=CLEAN, documents=None) -> str:
    """The refusal code of one call, or "sent" (the id of each G13 assertion stays on its failure line)."""
    try:
        bound.chat(messages, system="s", route="main", documents=documents)
    except GateRefused as exc:
        return exc.code
    return "sent"


G13_SPELLINGS = {
    "utf-16-le document": ("doc", f"key {TOKEN} at x".encode("utf-16-le")),
    "utf-16-le document with a BOM": ("doc", b"\xff\xfe" + f"key {TOKEN}".encode("utf-16-le")),
    "nul-split message": ("msg", "a " + chr(0).join(TOKEN) + " b"),
    "zero-width-space-split document": ("doc", f"k {TOKEN[:5]}\u200b{TOKEN[5:]} y".encode()),
    "full-width document": ("doc", f"k {FULL_WIDTH} y".encode()),
    "percent-encoded message": ("msg", "k " + "".join(f"%{ord(c):02X}" for c in TOKEN)),
}


@pytest.mark.parametrize("where,payload", G13_SPELLINGS.values(), ids=G13_SPELLINGS.keys())
def test_g13_10_a_secret_in_a_decoded_form_refuses_the_call(where, payload):
    """G13-10 (E19 M2): a known secret that reached the gate in a form a reader decodes (a document that bypassed every
    producer) refuses the call with `held_value_left`; nothing is sent."""
    bound, client, _, sink = build(mapping=runmap.RunMap({"<SECRET_1>": TOKEN, "<IPV4_1>": IP}))
    messages = [{"role": "user", "content": payload}] if where == "msg" else CLEAN
    code = _g13_outcome(bound, messages, [payload] if where == "doc" else None)
    assert code == "held_value_left" and client.sent == [], "G13-10 a decoded secret was sent"
    assert sink.codes() == [("refused", "held_value_left")], "G13-10 the row does not say held_value_left"


def test_g13_11_a_document_with_decodable_forms_and_no_secret_is_sent_as_written():
    """G13-11: non-ASCII letters, `%41`, `&amp;` and `\\u0041` with no known secret in any form: the caller's bytes are sent."""
    doc = "ｈｅｌｌｏ wörld %41 &amp; \\u0041 <IPV4_1>".encode()
    bound, client, _, _ = build(mapping=runmap.RunMap({"<SECRET_1>": TOKEN, "<IPV4_1>": IP}))
    bound.chat(CLEAN, system="s", route="main", documents=[doc])
    assert client.sent[0]["docs"][0] is doc, "G13-11 a clean document was changed or refused"


def test_g13_12_a_long_document_is_read_in_windows_and_a_secret_on_a_window_edge_is_found():
    """G13-12: a document over `runmap.VIEW_WINDOW` (the gate holds texts up to 8 x the redaction cap) is read in overlapping
    windows; a full-width secret at every position around the first window edge is found, and the same document without it is sent."""
    filler = "wörd " * (runmap.VIEW_WINDOW // 5 + 50)
    edge = runmap.VIEW_WINDOW - (10 * len(TOKEN) + 16)
    for at in (edge - len(TOKEN), edge - 3, edge, runmap.VIEW_WINDOW - 3):
        doc = (filler[:at] + FULL_WIDTH + filler[at:]).encode()
        bound, client, _, _ = build(mapping=runmap.RunMap({"<SECRET_1>": TOKEN}))
        assert _g13_outcome(bound, documents=[doc]) == "held_value_left", f"G13-12 missed at {at}"
    bound, client, _, _ = build(mapping=runmap.RunMap({"<SECRET_1>": TOKEN}))
    bound.chat(CLEAN, system="s", route="main", documents=[filler.encode()])
    assert client.sent, "G13-12 a long clean document was refused"


def test_g13_13_m1_a_secret_prefix_beside_a_key_refuses_the_call():
    """G13-13 (E19 M1 at the gate): `hunt` + a key of the map, `hunt` being the first 4 characters of a secret value."""
    mapping = runmap.RunMap({"<SECRET_1>": "hunter2-" + "ABCDEFGH", "<IPV4_1>": IP})
    bound, client, _, _ = build(mapping=mapping)
    code = _g13_outcome(bound, [{"role": "user", "content": "x hunt<IPV4_1> y"}])
    assert code == "held_value_left" and client.sent == [], "G13-13 the prefix beside a key was sent"
```

### 3.4 Pins that change in tests/test_model_gate.py (exact; the module docstring lines in section 2 name the new tests)
- `test_t7_stated_limit_a_hidden_spelling_...` (5 params: full-width, ZWSP, `%73`, `\u0073`, `&#115;`) asserted the document is
  sent `is doc`. BECOMES: refused `held_value_left`, nothing sent; an identifier (HOST) in full-width still sent as written.
- `test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced` (the "UTF-16 sent as written" pin,
  E19 cites :1753, now :1793 after G4) BECOMES: the NUL-split message and the UTF-16LE document each refuse `held_value_left`;
  the ANSI-split copy is still sent as written (stated limit) with the whole copy beside it replaced.
- `test_r2_m2_safety_net_...` last line sent `<SECRET_1>abcdef` (SECRET_2 = `>abcdef`). BECOMES: refused; `<SECRET_1> abc`
  is sent. The G24 mutant (gate_mutants.py:323) keeps this killer and its expect `did not raise`.
- `test_d8_every_test_the_module_docstring_names_exists` goes red until the docstring hunks of section 2 are in (expected).
```diff
--- a/tests/test_model_gate.py
+++ b/tests/test_model_gate.py
@@ -402,9 +402,19 @@
 @pytest.mark.parametrize("spelling", HIDDEN.values(), ids=HIDDEN.keys())
-def test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate(spelling):
-    """Only the spelling the map holds is replaced. Finding hidden spellings is the pattern redactor's work
-    (the producers call redact_text / redact_untrusted, which scan the decoded views)."""
+def test_t7_a_hidden_spelling_of_a_known_secret_refuses_the_call_an_identifier_passes(spelling):
+    """Only the spelling the map holds is replaced (finding hidden spellings is the pattern redactor's work). Since G13
+    (E19 M2) the net reads the decoded forms: a hidden spelling of a SECRET value refuses the call; a hidden spelling of an
+    identifier still passes as written (stated limit)."""
     doc = f"line {spelling} end".encode()
     bound, client, _, _ = build(mapping=known())
-    bound.chat(CLEAN, system="s", route="main", documents=[doc])
-    assert client.sent[0]["docs"][0] is doc
+    exc = gate_refusal(bound, documents=[doc])
+    assert exc.code == "held_value_left" and client.sent == [], (
+        "T7 a hidden secret spelling was sent"
+    )
+    host = "db1.corp.example.org"
+    wide = f"line {''.join(chr(ord(c) + 0xFEE0) for c in host)} end".encode()
+    bound, client, _, _ = build(mapping=runmap.RunMap({"<HOST_1>": host}))
+    bound.chat(CLEAN, system="s", route="main", documents=[wide])
+    assert client.sent[0]["docs"][0] is wide, (
+        "T7 a hidden identifier spelling was not sent as written"
+    )
 
@@ -1792,5 +1802,6 @@
 
-def test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced():
-    """The gate does not clean the text: a NUL between characters, a UTF-16 document read as UTF-8, and an ANSI
-    colour sequence inside a copy pass as written. Whole copies beside them are replaced."""
+def test_d7_a_copy_split_by_nul_or_utf16_refuses_the_call_an_ansi_split_copy_passes():
+    """The gate does not clean the text it sends. Since G13 (E19 M2) its net reads the text without NUL: a secret split by
+    NUL, or in a UTF-16 document read as UTF-8, refuses the call. A copy split by an ANSI colour sequence still passes
+    as written (stated limit); a whole copy beside it is replaced."""
     mapping = runmap.RunMap({"<SECRET_1>": TOKEN, "<IPV4_1>": IP})
@@ -1800,12 +1811,12 @@
     assert TOKEN.encode() not in utf16
+    for messages, documents in (
+        ([{"role": "user", "content": f"a {nul} b"}], None),
+        (CLEAN, [utf16]),
+    ):
+        bound, client, _, _ = build(mapping=mapping)
+        exc = gate_refusal(bound, messages=messages, documents=documents)
+        assert exc.code == "held_value_left" and client.sent == [], "D7 a NUL-split secret was sent"
     bound, client, _, _ = build(mapping=mapping)
-    bound.chat(
-        [{"role": "user", "content": f"a {nul} b {ansi} c {TOKEN}"}],
-        system="s",
-        route="main",
-        documents=[utf16, f"{nul} {IP}".encode()],
-    )
-    assert client.sent[0]["messages"][0]["content"] == f"a {nul} b {ansi} c <SECRET_1>"
-    assert client.sent[0]["docs"][0] is utf16
-    assert client.sent[0]["docs"][1] == f"{nul} <IPV4_1>".encode()
+    bound.chat([{"role": "user", "content": f"b {ansi} c {TOKEN}"}], system="s", route="main")
+    assert client.sent[0]["messages"][0]["content"] == f"b {ansi} c <SECRET_1>"
 
@@ -2434,4 +2445,6 @@
     assert exc.code == "held_value_left" and gate._llm.sent == []
-    # a copy that sits at the edge of a placeholder already in the text is not "raw"
-    bound.chat([{"role": "user", "content": "<SECRET_1>abcdef"}], system="s", route="main")
+    # since G13 (E19 M1) six of its seven characters beside a placeholder are a piece of it: refused; apart from it, sent
+    exc = gate_refusal(bound, messages=[{"role": "user", "content": "<SECRET_1>abcdef"}])
+    assert exc.code == "held_value_left", "R2-M2 the tail beside a placeholder was sent"
+    bound.chat([{"role": "user", "content": "<SECRET_1> abc"}], system="s", route="main")
 
```

### 3.5 Red before / green after (MEASURED: these exact tests, called directly, on 72fd2cc8a and on the prototype)
| test | 72fd2cc8a | prototype |
|---|---|---|
| G13-1 exact M1 input, both orders (pin since G9) | green | green |
| G13-2 prefix beside identifier key, G13-3 suffix, G13-4 boundaries, G13-5 `<SECRET_1>abcdef`, G13-6 piece budget | red (assertion, id on the line) | green |
| G13-7 U+0338 marker (N3) | red | green |
| G13-8 views budget, G13-12 windows | red (AttributeError: no `held_in_views` / `VIEW_WINDOW`) | green |
| G13-10 x 6 (UTF-16LE, UTF-16LE+BOM, NUL-split msg, ZWSP doc, full-width doc in a document that bypassed a producer, `%XX` msg) | red "G13-10 a decoded secret was sent" | green |
| G13-11 clean non-ASCII + `%41` `&amp;` `\u0041` doc sent `is doc` | green | green |
| G13-13 M1 at the gate (`hunt<IPV4_1>`) | red | green |
| t7 x5, d7, r2_m2 (changed pins) | red | green |
| whole test_model_gate.py (direct runner: plain + parametrize + monkeypatch) | 250 ok / 0 fail | 259 ok / 0 fail |
| whole test_runmap_enforce_map.py | 48 ok / 1 fail (e5b, pre-existing) | 56 ok / 1 fail (same e5b) |
| test_runmap_map_write 10, test_runmap_e15 15, test_redact_own_output 27, _hardening 44, test_textnorm_siblings 22, test_gate_install_callers 10 (+5 needing fixtures), test_k5_classes 3,755 | - | all ok |
NOT RUN by the drafter (the builder runs them with pytest, one file per command): test_k5_round5/7 (need `cryptography`), test_redact_glued_rest, test_k5_fixes7 (my direct runner mis-expands their `pytest.param`/tuple params: runner artefact, they do not call the gate), test_b64_scan beyond the 2 pre-existing reds (54 ok).

Boundaries pinned: 3 vs 4 chars both sides, a space, a non-key token, a middle piece (G13-4); window edges (G13-12).

## 4. Budgets and cost (MEASURED; one EnforceBudget per chat call: 6 s CPU and wall, ENFORCE_MAX_TOTAL_CHARS, _STEPS)
2,000 planted SECRET values (`Zq9x{i:04d}Lm4wKp`), 256 KB text; snapshot+enforce+net(+views):
| text | HEAD | G13 |
|---|---|---|
| ASCII words | 0.08 s | 0.08 s |
| ASCII with `%20` | 0.11 s | 0.14 s |
| non-ASCII words (views run) | 0.11 s | 0.51 s |
| 13,000 keys between words (piece rule worst honest case) | 0.25 s | 0.35 s |
| `Zq9x0<SECRET_n>` repeated (hostile: a head beside every key) | 0.29 s | 0.37 s, refused held_value_left |
| non-ASCII 600,000 chars (over the cap: 10 windows) | 0.08 s | 0.81 s |
| 2,000 HELD-BACK values (`ECRET_i>x0000`), ASCII / non-ASCII+`%` | 0.31 / 0.31 s | 0.52 / 0.98 s |
No call reached mask_budget_exceeded. Views cost 0 for an ASCII text without `\ % &` (the common case). Memory: `pieces` holds
two sorted lists of the secret values (references + one reversed copy: <= MAX_MAP_CHARS 524,288 characters) and two sets of 4-char
strings. False refusals: property corpus (tests/test_redact_idempotent_property.py CORPUS, 1,978 inputs, 1,470 with a secret
in the map; redact_text -> snapshot -> enforce -> net -> views): 0 refused on HEAD, 0 on G13, MEASURED. The M1 fuzz with
alphanumeric values: 0 sent leaks, 0 refused on both. Edge/held-back fuzz: 46 -> 3 leaks / 8,000 (the 3: middle pieces of
values holding `<` or `>` between two keys: stated limit, decision D5).

## 5. Mutants (tests/gate_mutants.py, add to `M`; RUNMAP = runmap.py, MAP_TEST = test_runmap_enforce_map.py, default TEST/GATE)
Each search text occurs exactly once in the prototype. Emulated by the drafter (mutate the copy, call the killer directly):
12 of 12 killed with the expect on the first failure line. Format: name | file | old -> new | killer [param] | expect.
- G13a the piece rule is not run | RUNMAP | `    return _touching_piece(text, snap)  # G13 (E19 M1)\n` -> `    return False\n` | test_g13_2_a_secret_prefix_beside_a_key_is_held | `G13-2 `
- G13b the right side is not read | RUNMAP | `                if _starts_one(rev, right[:j][::-1]):\n` -> `                if False:\n` | test_g13_3_a_secret_suffix_beside_a_key_is_held | `G13-3 `
- G13c a piece needs 5 | RUNMAP | `NET_MIN_PIECE = 4\n` -> `NET_MIN_PIECE = 5\n` | test_g13_4_boundaries_of_the_piece_rule | `G13-4 four`
- G13d a piece of 3 counts | RUNMAP | `NET_MIN_PIECE = 4\n` -> `NET_MIN_PIECE = 3\n` | test_g13_4_boundaries_of_the_piece_rule | `G13-4 three`
- G13e any placeholder-shaped token counts | RUNMAP | `    tokens = [m.span() for m in _PLACEHOLDER.finditer(text) if m.group() in snap]\n` -> `    tokens = [m.span() for m in _PLACEHOLDER.finditer(text)]\n` | test_g13_4_boundaries_of_the_piece_rule | `G13-4 a token`
- G13f piece lookups spend nothing | RUNMAP | `                budget.spend_chars(len(left) - i)\n` -> `                pass\n` | test_g13_6_the_piece_check_spends_the_call_budget | `G13-6 `
- G13g the gate does not read views | GATE | `        if runmap.held_value_left(fixed, mapping) or runmap.held_in_views(fixed, mapping):\n` -> `        if runmap.held_value_left(fixed, mapping):\n` | test_g13_10_a_secret_in_a_decoded_form_refuses_the_call `[full-width document]` | `G13-10 `
- G13h the NUL-free text is not a view | RUNMAP | `    views = [cleaned] if cleaned != text else []\n` -> `    views = []\n` | test_g13_10_... `[utf-16-le document]` | `G13-10 `
- G13i `_views` never runs | RUNMAP | `    if not cleaned.isascii() or any(c in cleaned for c in "\\%&"):\n` -> `    if False:\n` | test_g13_10_... `[full-width document]` | `G13-10 `
- G13j windows do not overlap | RUNMAP | `    overlap = 10 * longest + 16\n` -> `    overlap = 0\n` | test_g13_12_a_long_document_is_read_in_windows_and_a_secret_on_a_window_edge_is_found | `G13-12 `
- G13k views spend nothing | RUNMAP | `        snap.budget.spend_chars(len(view))\n` -> `        pass\n` | test_g13_8_the_views_spend_the_call_budget | `G13-8 `
- G13l the marker search keeps marks | RUNMAP | `    return replace_canonical(text, _MARKER, lambda m: "[[", _INVISIBLE_OR_MARK)\n` -> `    return replace_canonical(text, _MARKER, lambda m: "[[")\n` | test_g13_7_a_marker_look_alike_with_a_combining_mark_is_escaped | `G13-7 `
(`param` as junit writes it: `[full-width document]`, `[utf-16-le document]`.) Existing G24 stays (killer r2_m2, `did not raise`).
Run `python tests/gate_mutants.py G13` (its baseline runs the 3 files once); if the box cannot take it, 3 at a time.

## 6. Nits
- N1: the agent loop checks max_map_entries (2,000) AFTER a producer call, BEFORE the model call (agent_loop.py:433, :556);
  one producer call can add > 4,096 entries and `config.max_map_entries` has no upper bound, so ENFORCE_MAX_* are a reachable
  second line (REASONED). "2,000 planted values force mask_budget_exceeded each call": NOT REPRODUCED (section 4). DEFAULT: one
  comment line under ENFORCE_MAX_STEPS, no constant change, no new test (test_r2_m3 pins the 4,101-value refusal):
  `# Above defaults.MAX_MAP_ENTRIES on purpose: the run cap is checked after a producer call; these bound the call before it.`
- N2: the `escape_placeholders` docstring hunk in section 2 (compatibility forms only; UTS #39 confusables not folded).
- N3: section 2 (`_INVISIBLE_OR_MARK`) + G13-7. Model-visible spoof only; the gate's own framing check is unchanged.

## 7. Interplay
- G4 (base64 view, was building in /tmp/core-c-g4): ALREADY MERGED in 72fd2cc8a. G13 does not touch `_b64_*`/`_scan`. The gate
  net does NOT decode base64 (the producers' G4 step does): a base64-encoded known secret in a document that bypassed every
  producer is still sent: stated in the model_gate docstring hunk, decision D4. G4's two TB reds above are not G13's.
- G9: the read-back closes the producer and enforce overlap; G13's piece rule is the independent net (it does not call
  `_overlaps`). `held_value_left` still calls `snap.checker.sweep` first (its G9 InputTooLarge/SpelledNotSettled unchanged).
- G12 (redact.py `_place`, trailing-punctuation twin): no textual overlap; whichever lands second re-runs G13-1..13 and the
  corpus check. `<SECRET_1>,` (twin `hunter22`/`hunter22,`) has a 1-char right piece: no refusal (REASONED).
- M3 (textnorm.py), G7-F3/F4 (redact.py): no file overlap. core-a contract tests (stale `_bind` dict): core-a's side.

## 8. Run list (one command each, in order; no pytest batch over the tree)
1. 3.1; baseline `uv run pytest -q` on test_model_gate.py, test_runmap_enforce_map.py (e5b red), test_b64_scan.py (2 red).
2. Add the tests (3.2, 3.3) and the pin changes (3.4) only; run the two files: the red set must be exactly 3.5's red column.
3. Apply section 2; `ruff format` + `ruff check` on the four files; run the two files: green except e5b.
4. One at a time: test_runmap_map_write, test_runmap_e15_placeholder_spellings, test_redact_own_output(_hardening),
   test_redact_glued_rest, test_k5_fixes7, test_textnorm_siblings, test_gate_install_callers, test_b64_scan,
   test_redact_idempotent_property (corpus: 0 new refusals), test_k5_round5, test_k5_round7.
5. Mutants (5). 6. Section 4 table by script: every row < 2 s, no mask_budget_exceeded. 7. Commit per phase ("code G: G13 ...").

## 9. Stop rules
- The exact M1 input leaks on the head (enforce output holds `hunter2-` or `-ZZZZZZZZ` and the net says False): STOP, report.
- Any test outside 3.4's list changes from green to red, or the property corpus gets one new refusal: STOP (a false refusal
  is a denial of service on honest runs).
- A row of section 4 over 2 s, or any mask_budget_exceeded in it: STOP, report the row.
- A mutant survives, or its expect is not on the first failure line: fix the test message, not the mutant; twice: STOP.
- HEAD moved and a search text of section 2 or 5 is not found exactly once: re-anchor by reading; never by line number.

## 10. Evidence: MEASURED = sections 0, 3.5, 4 (archive + prototype, direct calls); NOT RUN = pytest, mutation runner, CI;
REASONED = N1, G12 interplay, the window overlap (an escape is <= 10 chars a char).
## 11. Lead decisions (defaults in force unless the lead says otherwise)
- D1 k1b replay with `--i-know-data-is-already-masked` binds the gate with NO_MAP: neither enforce nor this net runs.
  DEFAULT unchanged (operator-acknowledged). Option: bind the replay with the bundle's map (net runs, may refuse).
- D2 k1b assistant echo `tool NAME {call.input}` (loop.py:211-213) and rendered tool results (loop.py:214) are not
  re-redacted. DEFAULT unchanged (model-origin over masked data). Option: redact_value on the echo (core-c, small).
- D3 extract.py:47 sends a caller's raw document, no producer; no caller in src. DEFAULT unchanged (F-install deletes it).
- D4 base64 at the gate: DEFAULT not read (cost; producers' G4). Option: run `_b64_units` decode as one more view.
- D5 middle pieces between two keys (3 / 8,000 fuzz, values with `<`/`>` only): DEFAULT stated limit. Option: refuse a free
  segment between two keys that is a substring of a secret value (one `in` over the joined values per segment: costly).
- D6 N1: comment only (default) vs a reachability test.
- D7 the r2_m2 pin flips from "sent" to "refused" (`<SECRET_1>abcdef`): DEFAULT refuse (the lead's prefix/suffix rule).
  Also any honest text where 4+ characters of a secret's start touch a key is refused (0 in the corpus).
- D8 identifiers in decoded forms (full-width HOST) still pass as written: DEFAULT unchanged (the net is for secret kinds).
