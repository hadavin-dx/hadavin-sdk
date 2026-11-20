# G12: a SECRET value that ends in prose punctuation leaves its clear copies readable (escalation E18 item G7-F4)

Status: BUILD TICKET, not built. Build AFTER G4 and G9 are merged into cloud/core-c (section 9). Drafter a5285a90, 2026-11-20.
Owner: core-c (redact.py `_Redactor._place`). One src file, one new test file, one new mutant file. No defaults.py change.

Evidence labels: MEASURED = run by the drafter with direct `uv run python` calls (no pytest session) on a `git archive` copy of
HEAD 37462c8e5 (src identical to cc239dd5c: only handover files changed since) under the scratch folder named below; MEASURED-G9 = the
same on a `git archive` copy of wip-g9 35a5cf00e with the post-G9 diff applied; MEASURED-G4 = the same on wip-g4 ebb134398 (builder
mid-way, Phase 3); EMULATED = a mutant applied by text replacement and the test file run by the drafter's direct-call runner, not by
`tools/mutation_runner`; BY READING = from the code, not run; NOT RUN = left for the builder.
Scratch (not durable): `/tmp/claude-0/-home-user/1ecfcb92-30a8-505b-a8c3-27491ed2aff6/scratchpad/g12_work/` (head/, cand/, t_wip-g9/,
t_wip-g4/, matrix.py, corpus.py, cost.py, runner.py, mut9.py, g12_src.diff, g12_src_after_g9.diff, test_redact_g12_trailing_punct_final.py).

## 1. Finding in one paragraph

The E18 probe is mis-built, and the leak class it hit is real but different. `secret = "Zq9xW4mT7pLy"`: its 6th character is `4`,
not `x`, so `s6 = "Zq9xWｘmT7pLy"` folds to `Zq9xWxmT7pLy`, a value ONE CHARACTER AWAY from the secret, not a spelling of it
(MEASURED: `textnorm.fold(s6) != secret`). The readable `Zq9xW4mT7pLy` is another string, exactly like the control
`password=Zq9xWQmT7pLy Zq9xW4mT7pLy` (MEASURED: also readable). No redactor can know it; this part of F4 is NOT a leak.
BUT the probe's separator `, ` exposes a real leak that has nothing to do with the fold: the key=value SECRET pattern takes the comma
into the value (`<SECRET_1>` = `Zq9xWｘmT7pLy,`), so the every-copy sweep looks for `...,` and never for the value without it. Where
the value is secret-shaped (upper + lower + digit) the `_PIECE` rule of `_place` registers the bare value too, which is why the fold
path looks fine for `Zq9...`. For an ordinary password it does not, and the clear copy stays:

| input (MEASURED on HEAD, `redact`) | output | map |
|---|---|---|
| `password=hunter22, hunter22` | `password=<SECRET_1> hunter22` | `{<SECRET_1>: "hunter22,"}` |
| `password=hunter22; hunter22` (control) | `password=<SECRET_1>; <SECRET_1>` | `{<SECRET_1>: "hunter22"}` |
| `password=hunter22 hunter22` (control) | `password=<SECRET_1> <SECRET_1>` | `{<SECRET_1>: "hunter22"}` |
| `password=hunter22. hunter22` / `) ` / `! ` / `? ` / `: ` | `password=<SECRET_1> hunter22` | value keeps `.`/`)`/... |
| `password=hunter22, and later hunter22` | `password=<SECRET_1> and later hunter22` | `{<SECRET_1>: "hunter22,"}` |
| `authorization: hunter22hunter; hunter22hunter` | `authorization: <SECRET_1> hunter22hunter` | value keeps `;` |
| `password=huｎter22, hunter22` (the F4 shape built as meant) | `password=<SECRET_1> hunter22` | `{<SECRET_1>: "huｎter22,"}` |
| `password=Zq9ｘW4mT7pLy, Zq9xW4mT7pLy` (fold built right, secret-shaped) | `password=<SECRET_1> <SECRET_2>` (no leak) | piece `<SECRET_2>` |
| the E18 probe as written | `password=<SECRET_1> Zq9xW4mT7pLy` | `{<SECRET_1>: "Zq9xWｘmT7pLy,", <SECRET_2>: "Zq9xWｘmT7pLy"}` |

Board correction for E18 (lead to adopt): "G7-F4: the probe's s6 is a different value (6th char is `4`); the real leak is a SECRET
value that ends in `,` `.` `)` `!` `?` `:` `]` `}` (`;` for `authorization:`): its clear copy is not swept. Not a fold or spelled-form
bug. Fix: G12."

## 2. Root cause (by function name; BY READING, confirmed by the MEASURED rows above)

1. `PATTERNS`, the SECRET key=value entry (redact.py ~674-692): value class
   `(?:...|[^\s\"';,]|,(?!\s*[\w.\-]+\s*[:=]))+`. A comma that begins no `key=` pair is a value character (kept on purpose: a comma
   inside a secret masks it whole), so a comma right before a space is taken in. `.`, `)`, `!`, `?`, `:`, `]`, `}` are plain value
   characters. `authorization` (`[^\s\"']{8,}`) also takes `;`. The cookie and flag patterns behave the same at their ends.
2. `_Redactor._decide` returns that value as written; `_mask_ex` -> `_place` registers it whole. The `_NOT_A_VALUE` check strips
   `.,;:)(<>` only to TEST the word list; the stored value keeps them.
3. `_Redactor._place` adds a second entry only for `_PIECE` pieces that are `_secret_shaped` (upper AND lower AND digit, or 20+
   chars). `hunter22`, `correcthorse`, `abc123def` are not, so nothing else is registered.
4. `_build` -> `_rules` -> `_sweep(placeholder, "hunter22,")` = `_EVERY_COPY`; `sweep` replaces every copy of `hunter22,`. A copy
   without the comma does not contain it. `settle` re-runs the table on changed strings, but a bare `hunter22` matches no pattern, so
   no round can find it.
5. The fold machinery is NOT involved: `_build`'s alias index (`_alias_keys`: `fold` and every `fold_view` of a non-ASCII stored
   value) already makes the clear spelling of a stored look-alike value a sweep rule (MEASURED: `password=Zq9ｘW4mT7pLy Zq9xW4mT7pLy`
   -> `<SECRET_1> <SECRET_1>`; `password=huｎter22 hunter22` -> both masked). `_spell`/`_unspell`/`_spelled_sweep` handle only
   written forms that hold a placeholder (`<SECRET_1>xy`); `_fold_scan`/`_mask_in_place` read lines that hold non-ASCII
   characters. None of them is reached by the trailing-comma gap, and none of them needs to change.

## 3. Neighbours examined (MEASURED; `matrix.py`, 900 rows = 3 secrets x 9 spellings x 6 separators x 2 orders x 3 call shapes)

Secrets `hunter22`, `huffer22pw` (ligature), `Zq9xW4mT7pLy`; spellings: plain, full-width letter, full-width digit, circled, small
capital, ligature `ﬀ`, zero-width space inside, combining acute, upper case; separators `, ` ` ` `. ` `) ` `; ` `! `; orders: spelled
copy stored first / plain stored first; shapes: one `redact` call, `redact_many` with the copy in a second string (two-pass, settle),
and `runmap.redact_text` (views). A row leaks when the clear secret, its fold, or the spelled copy is readable in the output.

| separator | HEAD leaks | G12 leaks |
|---|---|---|
| ` ` (control) | 63 | 63 |
| `; ` (control) | 63 | 63 |
| `, ` | 123 | 63 |
| `. ` | 123 | 63 |
| `) ` | 150 | 63 |
| `! ` | 150 | 63 |

After G12 every separator leaks exactly as the space control; 0 rows leak with G12 that do not leak on HEAD. The 63 left per
separator are NOT G12 and are not changed by it:
- upper case copy (18): a different value (passwords are case sensitive); not a leak by the contract.
- plain stored FIRST, spelled copy later (`password=hunter22 ... huｎter22`), bare `redact`/`redact_many` (the reverse direction):
  the sweep is literal on the written text. This is the known open hole VARIANT-1(a)/(c), strict-xfail pinned in
  tests/test_redact_fold.py (`test_variant_1_a_bare_redact_zwsp_copy_open_hole`, `test_variant_1_c_redact_text_lookalike_copy_open_hole`,
  "closed by P2d-2") and SECURITY-README L3. Through `runmap.redact_text` the views close it for full-width, zero-width, ligature;
  combining-mark copies (3 rows) still pass there (P2d-2 class, report to the P2d-2 owner).
- small capital `ɴ`: `textnorm.fold("huɴter22") == "huNter22"` (upper N), a different value from `hunter22` in both orders: a fold
  table choice, not G12 (decision 6.5).
- circled on `Zq9...` (1 + 1): artefact of the drafter's generator (it turned `9` into `⒨`, a different value). Ignore.
- key=value vs standalone: a standalone value (no key) matches no pattern on HEAD or G12 (nothing to sweep from); the controls
  above are the standalone copies of a key=value value, which is the shape that matters.
- two passes: `redact_many(["password=hunter22,", "later: hunter22 again"])` -> HEAD `[..., "later: hunter22 again"]`, G12
  `["password=<SECRET_1>", "later: <SECRET_2> again"]`; `redact_text(out, m) == out` for every G12 row (second pass identity).

## 4. The change (smallest; registers the bare value as a derived entry, like a `_PIECE` piece)

Why here and not elsewhere: changing the PATTERN (stop the value before a trailing comma) changes the stored value and output of
every pin that ends a value with punctuation and shows the last character of a password that really ends in `,`; a sweep through the
fold is the wrong tool (no fold is involved). `_place` already registers derived entries (pieces) with journal entries for rollback;
one more derived entry is the minimal, local fix. It adds NO written form (`_spell` is not called), so `SPELLED_MAX_WORK`,
`SPELLED_MAX_CHARS` and G9's `SPELLED_MAX_UNION_CHARS` are untouched; it adds no loop, so the deadline reading is unchanged.

### 4.1 Exact diff, AFTER G9 (apply this one; MEASURED-G9: `patch` clean on wip-g9 35a5cf00e, ruff check/format clean)

```diff
--- a/src/hadavin_sdk/guard/redact.py
+++ b/src/hadavin_sdk/guard/redact.py
@@ -922,6 +922,10 @@
 )
 
 _PIECE = re.compile(r"[^\s;,&=.:\"'\[\]{}<>]{8,}")
+# Prose punctuation a SECRET value can take in at its END (G12, escalation E18 G7-F4): the key=value value class keeps a comma that
+# begins no `key=` pair and reads `.` and `)` as value characters, so `password=hunter22, hunter22` stored `hunter22,` and the
+# every-copy sweep of that value left the clear copy `hunter22` readable. `_place` registers the value without them as well.
+_TRAIL = ".,;:!?)]}"
 
 # A placeholder token, captured so `re.split` keeps it as its own segment: `<LABEL_123>`.
 _LABELS = tuple(dict.fromkeys(label for label, _ in PATTERNS))
@@ -1759,7 +1763,8 @@
         return original, placeholder
 
     def _place(self, label: str, full: str, original: str, derived: bool = True) -> str:
-        """A new placeholder for `full`; for a secret kind, one too for each secret-shaped piece of it."""
+        """A new placeholder for `full`; for a secret kind, one too for each secret-shaped piece of it and one for `full` without the
+        prose punctuation it ends with (`_TRAIL`, G12)."""
         self.counters[label] += 1
         placeholder = f"<{label}_{self.counters[label]}>"
         self.mapping[placeholder] = full
@@ -1780,6 +1785,15 @@
                 self.reverse[piece] = f"<{label}_{self.counters[label]}>"
                 if self._journal is not None:
                     self._journal.append(("map", f"<{label}_{self.counters[label]}>", piece))
+        # G12: the value without the prose punctuation it ends with, an entry of its own (as a piece), so its copies are swept as the
+        # copies of a value written without it are (`_sweep` decides how: every copy from 4 characters, standalone at 3)
+        core = full.rstrip(_TRAIL) if derived and label in SECRET_KINDS else full
+        if core != full and len(core) >= 3 and core not in self.reverse:
+            self.counters[label] += 1
+            self.mapping[f"<{label}_{self.counters[label]}>"] = core
+            self.reverse[core] = f"<{label}_{self.counters[label]}>"
+            if self._journal is not None:
+                self._journal.append(("map", f"<{label}_{self.counters[label]}>", core))
         return placeholder
 
     def _spell(self, original: str, first: re.Match[str], placeholder: str, full: str) -> None:
```

Before G9 (HEAD; what the MEASURED rows of sections 3, 7, 8 ran): identical except `_place` has no `derived` parameter and the
core line reads `core = full.rstrip(_TRAIL) if label in SECRET_KINDS else full` (scratch `g12_src.diff`). Do NOT build that one.

### 4.2 Rules the code keeps (state them in review)
- Uses `full` (the restored value), not `original`: a value holding placeholders is stored restored, the core must be too.
- SECRET kinds only (`SECRET_KINDS`; after G4 it includes `ENCODED`, but `place_encoded` writes the map directly and never calls
  `_place`: MEASURED-G4 by reading wip-g4 `place_encoded`, and G9's ENCODED unions are `derived=False`). Identifier kinds take no
  trailing punctuation today (MEASURED: TENANT `acme01,` -> `acme01`, HOSTNAME `db01.corp.internal.` -> without the dot, IPV4, EMAIL).
- `derived` only: G9's unions register their value only (G9 v3 4.6); the core obeys the same switch.
- `len(core) >= 3`: the same floor as `_sweep` (under 3 never swept). 3 characters get standalone copies only, 4+ every copy: the
  comma form now behaves exactly like the form without the comma (decision 6.3).
- `core not in self.reverse`: a value the map already holds keeps its one placeholder (no second placeholder per value).
- The journal entry: a discarded in-place round (`_folded_line` -> `_rollback`) removes the core with its value.
- Restore: secret kinds are never restored (`runmap.restore_text` -> `storable`), so the extra entry changes no restored text.

## 5. Tests (new file tests/test_redact_g12_trailing_punct.py; exact text, ruff format/check clean; sha256 prefix 5e64f06d53c4)

```python
"""G12 (escalation E18 item G7-F4): prose punctuation that a SECRET value takes in at its end.

The key=value value class keeps a comma that begins no `key=` pair and reads `.`, `)`, `!`, `?`, `:`, `]`, `}` as value characters
(`authorization:` reads `;` too), so `password=hunter22, hunter22` stored `hunter22,` and the every-copy sweep of that value left the
clear copy `hunter22` readable. `_place` registers the value without its trailing punctuation as an entry of its own (as a piece).
The E18 probe as written replaced the 6th character (`4`, not `x`) by U+FF58: its "plain copy" is another value (pinned below).
Every assertion message starts with its id (`G12-n `): the mutants of tests/g12_mutants.py expect it."""

from __future__ import annotations

import importlib
import sys

import pytest

from hadavin_sdk.guard import runmap, textnorm

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]

PW = "hunter22"  # made up; not secret-shaped (no upper case), so no `_PIECE` entry hides the gap


@pytest.mark.parametrize("mark", [",", ".", ")", "!", "?", ":", "]", "}", ",,", "...,", "),"])
def test_g12_a_trailing_mark_does_not_leave_the_clear_copy(mark):
    r = R.redact(f"password={PW}{mark} {PW}")
    assert PW not in r.text, f"G12-1 {r.text}"
    assert r.mapping == {"<SECRET_1>": PW + mark, "<SECRET_2>": PW}, f"G12-2 {r.mapping}"


def test_g12_the_authorization_value_drops_a_semicolon_too():
    v = "hunter22hunter"
    r = R.redact(f"authorization: {v}; {v}")
    assert r.text == "authorization: <SECRET_1> <SECRET_2>", f"G12-3 {r.text}"


def test_g12_the_copy_in_another_string_of_the_call_is_swept():
    out, mapping = R.redact_many([f"password={PW},", f"later: {PW} again"])
    assert out == ["password=<SECRET_1>", "later: <SECRET_2> again"], f"G12-4 {out}"
    assert mapping == {"<SECRET_1>": PW + ",", "<SECRET_2>": PW}, f"G12-4 {mapping}"


@pytest.mark.parametrize(
    "spelled",
    [
        PW[:2] + "ｎ" + PW[3:],  # full-width n
        PW[:6] + "２" + PW[7:],  # full-width 2
        PW[:2] + "ⓝ" + PW[3:],  # circled n
        PW[:2] + "​" + PW[2:],  # zero-width space inside
        PW[:3] + "́" + PW[3:],  # combining acute
    ],
    ids=["fullwidth-letter", "fullwidth-digit", "circled", "zero-width", "combining"],
)
def test_g12_a_spelled_stored_original_sweeps_its_plain_copy(spelled):
    """The E18 shape built as intended: the stored value is a compatibility spelling of the clear copy."""
    text = f"password={spelled}, {PW}"
    assert PW not in R.redact(text).text, "G12-5 bare redact"
    m = runmap.RunMap()
    out = runmap.redact_text(text, m)
    assert PW not in textnorm.fold(out) and spelled not in out, f"G12-5 {out}"
    assert runmap.redact_text(out, m) == out, f"G12-6 {out}"


def test_g12_the_e18_probe_as_written_holds_a_different_value():
    value = "Zq9xW4mT7pLy"  # made up
    s6 = value[:5] + "ｘ" + value[6:]  # the 6th character is `4`: the fold is Zq9xWxmT7pLy
    assert textnorm.fold(s6) != value, "G12-7 the probe's fold"
    r = R.redact(f"password={s6}, {value}")
    # a value one character away is not a copy: unchanged by G12
    assert r.text == f"password=<SECRET_1> {value}", f"G12-7 {r.text}"


def test_g12_a_three_character_core_is_swept_as_its_control_without_the_comma():
    control = R.redact("password=abc abc").text
    assert control == "password=<SECRET_1> <SECRET_1>", f"G12-8 control {control}"
    assert R.redact("password=abc, abc").text == "password=<SECRET_1> <SECRET_2>", "G12-8 abc"
    # under 3 characters: no core, as `_sweep` never sweeps such a value
    assert R.redact("password=ab, ab").mapping == {"<SECRET_1>": "ab,"}, "G12-8 ab"
    # 3 characters: standalone copies only, as for the control
    assert R.redact("password=abc, xabcx").text == "password=<SECRET_1> xabcx", "G12-8 glued"


def test_g12_a_core_the_map_holds_gets_no_second_placeholder():
    r = R.redact(f"password={PW} x\npassword={PW}, y")
    assert r.mapping == {"<SECRET_1>": PW, "<SECRET_2>": PW + ","}, f"G12-9 {r.mapping}"
    assert r.text == "password=<SECRET_1> x\npassword=<SECRET_2> y", f"G12-9 {r.text}"


def test_g12_a_rolled_back_value_takes_its_core_with_it():
    """A discarded in-place round (``_folded_line``) rolls back what it registered: the core goes with its value, so the number
    handed out again names one value only."""
    r = R._Redactor(None)
    counters = r._open_journal()
    r._place("SECRET", PW + ",", PW + ",")
    assert r.mapping == {"<SECRET_1>": PW + ",", "<SECRET_2>": PW}, f"G12-10 {r.mapping}"
    r._rollback(counters)
    assert r.mapping == {} and r.reverse == {}, f"G12-10 {r.mapping} {r.reverse}"
    assert r._place("SECRET", "zz9other", "zz9other") == "<SECRET_1>", "G12-10 number"
    assert r.sweep(f"x {PW} y") == f"x {PW} y", "G12-10 a ghost entry sweeps the core"


def test_g12_identifier_kinds_are_unchanged():
    tenant = R.redact("user_id=acme01, then acme01").mapping
    assert tenant == {"<TENANT_1>": "acme01"}, f"G12-11 {tenant}"
    host = R.redact("host db01.corp.internal. next db01.corp.internal").mapping
    assert host == {"<HOSTNAME_1>": "db01.corp.internal"}, f"G12-11 {host}"
    # no identifier pattern takes trailing punctuation today; the rule is for the secret kinds only
    r = R._Redactor(None)
    r._place("TENANT", "acme01,", "acme01,")
    assert r.mapping == {"<TENANT_1>": "acme01,"}, f"G12-11 {r.mapping}"


def test_g12_a_g9_union_registers_its_value_only_and_no_core():
    """G9's unions (`derived=False`) register the value only: no written form, no pieces, and no G12 core."""
    r = R._Redactor(None)
    r._place("SECRET", PW + ",", PW + ",", derived=False)
    assert r.mapping == {"<SECRET_1>": PW + ","}, f"G12-12 {r.mapping}"
```

### 5.1 Red before, green after (24 test ids)
| test (id prefix `tests/test_redact_g12_trailing_punct.py::`) | base = wip-g9 (MEASURED-G9) | HEAD (MEASURED) | G12 |
|---|---|---|---|
| `test_g12_a_trailing_mark_does_not_leave_the_clear_copy[,]` ... `[),]` (11 ids) | RED (G12-1) | RED | green |
| `test_g12_the_authorization_value_drops_a_semicolon_too` | RED (G12-3) | RED | green |
| `test_g12_the_copy_in_another_string_of_the_call_is_swept` | RED (G12-4) | RED | green |
| `test_g12_a_spelled_stored_original_sweeps_its_plain_copy[fullwidth-letter|fullwidth-digit|circled|zero-width|combining]` | RED (G12-5) | RED | green |
| `test_g12_a_three_character_core_is_swept_as_its_control_without_the_comma` | RED (G12-8 abc) | RED | green |
| `test_g12_a_rolled_back_value_takes_its_core_with_it` | RED (G12-10) | RED | green |
| `test_g12_the_e18_probe_as_written_holds_a_different_value` | green (pin: unchanged) | green | green |
| `test_g12_a_core_the_map_holds_gets_no_second_placeholder` | green (guard for M3) | green | green |
| `test_g12_identifier_kinds_are_unchanged` | green (guard for M6) | green | green |
| `test_g12_a_g9_union_registers_its_value_only_and_no_core` | green (guard for M7) | TypeError (no `derived` on HEAD: why this ticket builds after G9) | green |

Totals: wip-g9 base 20 red + 4 green; wip-g9 + G12 24 green (MEASURED-G9). HEAD (first 23 ids) 20 red + 3 green; HEAD + G12 23 green
(MEASURED). wip-g4 + G12 (first 23 ids) 23 green (MEASURED-G4).

## 6. Decisions for the lead (build default first)
6.1 Reclassify E18 G7-F4 as section 1 says (probe built wrong; real leak = trailing punctuation). DEFAULT: adopt, build G12.
6.2 `_TRAIL = ".,;:!?)]}"`. Quotes, `>`, `-`, `/`, `=` are excluded (`=` ends base64; `>` ends a placeholder; quotes are taken by the
    quoted-value patterns). DEFAULT: as written.
6.3 Floor 3 (same as `_sweep`, so `password=abc, abc` behaves as `password=abc abc`) vs 4 (only every-copy values). DEFAULT: 3.
6.4 A LEADING bracket is not stripped: `password=(hunter22), hunter22` registers `(hunter22` and the clear `hunter22` stays readable,
    exactly as the HEAD control `password=(hunter22) hunter22` does (MEASURED). DEFAULT: out of scope, new limit row (L-G12a) in the
    SECURITY pass; a one-line `.lstrip("([{")` would close it (not measured).
6.5 Small capital letters fold to UPPER case (`ɴ` -> `N`), so `password=huɴter22 hunter22` leaves `hunter22` (any separator, HEAD and
    G12). DEFAULT: report to the textnorm owner (G10 lane), not G12.
6.6 The B-N4 known limit widens slightly: a planted `password=word,` now also masks `word` (not only `word,`) in every line, as
    `password=word` already does. DEFAULT: accept (same rule as the comma-less form).
6.7 Reverse direction (plain stored first, look-alike copy later) stays the P2d-2 open hole (section 3). DEFAULT: unchanged here.

## 7. Cost and bounds (MEASURED on HEAD vs HEAD + G12, CPU seconds `time.thread_time`, best of 2, load avg 3.2-3.3 on 4 cores)

| shape (`runmap.redact_untrusted(text, {})`, tests/test_k5_perf.py E2E_UNITS) | 16 Ki HEAD / G12 | 64 Ki HEAD / G12 |
|---|---|---|
| `curl -u ` | 0.124 / 0.135 | 0.486 / 0.538 |
| `password= ` | 0.060 / 0.063 | 0.238 / 0.257 |
| full-width `password=` | 0.318 / 0.312 | 1.416 / 1.303 |
| JSON escape | 0.069 / 0.073 | 0.272 / 0.293 |
| zero-width | 0.346 / 0.349 | 1.369 / 1.593 |

Ratios 64Ki/16Ki stay ~4 (linear) on both. Worst case for G12 (every value ends in a comma, all distinct): 262,144 chars of
`password=hvNNNNNN, x` lines through `runmap.redact_text` -> HEAD 12,483 entries 1.24 s; G12 24,966 entries 1.52-1.64 s (two runs);
the same text without commas 13,107 entries 1.31-1.45 s. All far under `REDACT_BUDGET_S` = 6.0. The map at most doubles (one core
per value, never more): the finder build (E14's memory, ~0.46 KB per char) grows by at most the core's characters, which are fewer
than the value's. `SPELLED_MAX_WORK`, `SPELLED_MAX_CHARS`, `SPELLED_MAX_UNION_CHARS`: not touched (no written form). Deadline:
no new loop; the extra rules go through `_build`'s existing per-512 deadline check.

## 8. Over-masking and pins (MEASURED)
- Property corpus (tests/test_redact_idempotent_property.py `CORPUS`, 1,836 inputs, its own `check` called directly): HEAD 0 fail,
  G12 0 fail, 0 refused. Output of `runmap.redact_text` byte-identical on all 1,836; 11 rows (round12-fuzz 6, 110, 249, 259, 342,
  379, 457, 604, 798, 866, 1008) gain ONE map entry (the core, kinds SECRET and URLCRED), output unchanged. No new over-masking.
- Direct-call runner (every `test_` function, parametrize expanded, no fixtures) over the 23 files tests/test_redact*.py,
  tests/warden_port/test_redaction*.py, tests/test_runmap*.py: HEAD 3,069 pass / 47 fail, G12 3,069 pass / 47 fail, 0 ids differ.
  The 47 fail identically on both: strict-xfail open holes run without their mark (4 in test_redact_fold.py) and 43 runner artefacts in
  test_redact_glued_rest.py (fixture-built rows). 74 fixture tests and 11 marked tests not run (run them in section 10).
- tests/test_redact_g3_port.py (in the runner): identical. G3/G8 corpus rows: no row's output changes.
- wip-g9 + G12: tests/test_redact_settle_loop.py + tests/test_redact_idempotent_property.py 1,914 pass, 0 fail (MEASURED-G9).
- PINS THAT CHANGE: none found. Expected none in tests that assert a whole map of a comma-ended secret value; the builder's Phase 4
  batch is the check (STOP rule 11.3).

## 9. Rebase order and where (G4 and G9 build now; G12 lands after BOTH merge)
Order: G4 -> G9 -> G12 (or G9 -> G4 -> G12). E14 (finder memory cap) may land before or after G12: no shared line unless E14 picks
the "check in `_Redactor._place`" option of its section 4, then put E14's check FIRST in `_place` (before `self.counters[label] += 1`)
and count the core as a registration too (`len(core)`), else a capped call could still register the core.
Anchors (re-find by text, never by line number):
1. `_TRAIL` + its 3-line comment: immediately AFTER the module line `_PIECE = re.compile(r"[^\s;,&=.:\"'\[\]{}<>]{8,}")`
   (HEAD 924, wip-g9 924, wip-g4 865; MEASURED: `patch` applies, fuzz 1 on wip-g4 because G4 changed the line after).
2. `_Redactor._place`: the docstring line; and the core block at the END of `_place`, after the `for piece in (...)` loop (whose
   condition G9 makes `derived and label in SECRET_KINDS`) and before `return placeholder`. The core line MUST read
   `if derived and label in SECRET_KINDS` (G9's `derived` parameter). MEASURED-G9: hunk applies at offset +8.
3. Untouched by G12 (no conflict): G9's `sweep`, `_sweep_once`, `_ensure_built`, `_read_back`, `_overlaps`, `_masked`, `_close`,
   `_place_union`, `_spelled_sweep`, `settle`; G4's `_build` tie-break, `place_encoded`, `_LABELS`, `SECRET_KINDS`, runmap b64 views.
4. If a G9/G4 commit lands after G12 started: rebase, re-run Phase 1 (red) only if `_place` changed.

## 10. Phases and run list (box rule: `uptime` first; wait while load > 6; pytest `-n 2` at most; one heavy batch at a time)
Phase 0 (base): `git log -1` on cloud/core-c shows the G4 and G9 merges; `grep -n "    def _place(\|^_PIECE = " src/hadavin_sdk/guard/redact.py`
  shows `derived: bool = True` in the signature. If not: STOP (11.1).
Phase 1 (red): add tests/test_redact_g12_trailing_punct.py (section 5) ALONE, run
  `uv run --all-extras --group test pytest -q -n 0 tests/test_redact_g12_trailing_punct.py` -> expect exactly 20 failed, 4 passed
  (ids of 5.1). Commit the test file ("test G: G12 red").
Phase 2 (fix): apply 4.1; `uv run ruff format --check` and `uv run ruff check` on the two files; same pytest -> 24 passed. Commit.
Phase 3 (mutants): add tests/g12_mutants.py (section 12); `uv run --all-extras --group test python tests/g12_mutants.py` -> 7 of 7
  good. Commit.
Phase 4 (touched suites, one batch, `-n 2`): tests/test_redact_g12_trailing_punct.py tests/test_redact_settle_loop.py
  tests/test_redact_idempotent_property.py tests/test_redact_fold.py tests/test_redact_g3_port.py tests/test_redact_glued_rest.py
  tests/test_redact_context_after_sweep.py tests/test_redact_own_output_hardening.py tests/test_runmap_enforce_map.py
  tests/warden_port tests/test_k5_round8.py tests/test_k5_round12_fuzz.py tests/test_p1c*.py tests/test_b64*.py
  -> 0 failed beyond the base's xfails (compare with the same batch on the base: record both numbers).
Phase 5 (perf, alone): `pytest -q -n 0 -m perf tests/test_k5_perf.py tests/test_redact_settle_loop.py` -> as on the base.
Phase 6 (mutant suites that read redact.py): `python tests/redact_mutants.py`, `python tests/g8_mutants.py`, G9's mutant file
  (as G9 names it) -> the same counts as on the base (no mutant changes verdict).
Phase 7: one full batch `pytest -q -n 2` when the board says the slot is free; record passed/failed/xfailed vs base.

## 11. Stop rules
11.1 Base lacks G4 or G9 (Phase 0): stop, report; do not build the pre-G9 variant.
11.2 Phase 1 not exactly 20 red / 4 green, or a red one fails for a reason other than its `G12-n ` id: stop, report the ids.
11.3 Any test outside the new file turns red in Phase 4/6/7 that is green on the base: stop; do not edit that test; report its id and
     first line (a pin that changes needs a lead decision; none is expected).
11.4 Phase 5: any perf test red that is green on the base, or any k5 shape > 1.5x its base time in two runs: stop, report numbers.
11.5 A mutant not good (survives or fails on another id): stop; do not weaken the test; report.
11.6 No change to PATTERNS, `_sweep`, `sweep`, `_build`, defaults.py, textnorm.py, runmap.py. If the fix seems to need one: stop.

## 12. Mutants (new file tests/g12_mutants.py, modelled on tests/g8_mutants.py; EMULATED on wip-g9 + G12, 7 of 7 killed)
Expect = the first failing line holds the id and a space (>= 4 chars). Test file run: `[TEST, "tests/__init__.py", "tests/conftest.py"]`.
`C = "        core = full.rstrip(_TRAIL) if derived and label in SECRET_KINDS else full\n"`,
`I = "        if core != full and len(core) >= 3 and core not in self.reverse:\n"`,
`J = '                self._journal.append(("map", f"<{label}_{self.counters[label]}>", core))\n'`.

| name | old -> new | killer (`tests/test_redact_g12_trailing_punct::`) | expect | EMULATED |
|---|---|---|---|---|
| `G12-M1 the core is never registered` | I -> `        if False:\n` | `test_g12_a_trailing_mark_does_not_leave_the_clear_copy[,]` | `G12-1 ` | killed (20 ids) |
| `G12-M2 only a comma is trailing` | `_TRAIL = ".,;:!?)]}"` -> `_TRAIL = ","` | `test_g12_a_trailing_mark_does_not_leave_the_clear_copy[.]` | `G12-1 ` | killed (10 ids) |
| `G12-M3 a held core gets a second placeholder` | I -> `        if core != full and len(core) >= 3:\n` | `test_g12_a_core_the_map_holds_gets_no_second_placeholder` | `G12-9 ` | killed |
| `G12-M4 the core is not journaled` | J -> `                pass\n` | `test_g12_a_rolled_back_value_takes_its_core_with_it` | `G12-10 ` | killed |
| `G12-M5 the floor is 4` | I -> I with `>= 4` | `test_g12_a_three_character_core_is_swept_as_its_control_without_the_comma` | `G12-8 ` | killed |
| `G12-M6 identifier kinds get a core` | C -> `        core = full.rstrip(_TRAIL) if derived else full\n` | `test_g12_identifier_kinds_are_unchanged` | `G12-11 ` | killed |
| `G12-M7 a G9 union gets a core` | C -> C without `derived and ` | `test_g12_a_g9_union_registers_its_value_only_and_no_core` | `G12-12 ` | killed |

EQUIVALENT (not in the file; state in the header): dropping `core != full and ` from I. Proof: when `core == full`, `full` was put in
`self.reverse` four statements earlier (`self.reverse[full] = placeholder`) and nothing between removes it, so `core not in
self.reverse` is already False (EMULATED: survives, as expected).
Use `m(name, old, new, killer, expect)` as g8_mutants.py does (`Mutant(name, RD, old, new, expect, test_file=TEST,
only_test=killer, pinned=PIN + killer)`, `PIN = "tests/test_redact_g12_trailing_punct::"`); the `[,]`/`[.]` ids are pytest's own ids
for those parameters: check them with `pytest --collect-only -q` in Phase 3 and pin what it prints.

## 13. Docs (the SECURITY/README pass after G4/G9, not this build)
- E18 G7-F4 row: "probe built with a different value; real leak (trailing punctuation) fixed by G12 (commit ...)".
- New limit rows: L-G12a (leading bracket, 6.4) unless the lead builds it; the small-capital fold note (6.5) to the textnorm owner.
- CHANGELOG: "A secret written as `password=value,` (or ending in `.`, `)`, `!`, `?`, `:`, `]`, `}`) now also masks the copies of
  `value` elsewhere in the text."
