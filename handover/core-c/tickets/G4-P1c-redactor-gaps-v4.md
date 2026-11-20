# Ticket G4 v4: P1c redactor gaps (base64 view, whole host names, bare numbers written down)

Version 4, written by the core-c drafter (opus tier), 2026-11-20. It replaces tickets/G4-P1c-redactor-gaps-v3.md. It takes or
contests every finding of plan review round 3 (tickets/G4-review-3.md, both reviewers; section E). It keeps what v3 resolved from
round 1 (tickets/G4-review-1.md, section A) and round 2 (tickets/G4-review-2.md, section D). A builder with no other context builds
from this file alone. Nothing is built before plan review round 4 is clean.

Base of every claim in this file: `cloud/core-c` at cd8d375 (2026-11-20 08:58Z). Its `src/` and `tests/` are the same as 61ff6e7
("code B: P1d-a review round 3"). This tree already holds every fix the v3 ticket called open:
- G7 fix round 3 (da0f71f): `_Redactor.settle` is a real fixed point, and `runmap.redact_text` re-raises `RedactionError` as raised.
- gate round 4 (b83accc): `EnforceBudget`, `enforce_map`, `snapshot`, `_late_values`, `_sweep_held`, `_built`, `_held_items`, and
  runmap.py's one literal `raise RedactionError("NotSettled")` in `enforce_map`.
- G7 fix round 4 (6783535): the spelled-form caps `defaults.SPELLED_MAX_OFFSETS` / `SPELLED_MAX_FORMS`, the `bank_near` re-read in
  `settle`, and tests/p1c_builders.py with the three moved probe builders.
- P1d-a rounds 2 (a2dea63) and 3 (61ff6e7): the defang changes in approvals/gate.py.

P1d-a round 3 was merged while this ticket was being drafted. The v4 request still called it "running in /tmp/core-c-p1dr3"; that
worktree still exists, and HEAD's gate.py equals its diff. A G7 fix round 5 worktree also exists (/tmp/core-c-g7r5, branch
`wip-g7r5`); nothing of it is in HEAD. Section 0 names both dependencies and the Phase 0 rule that re-derives every cite by name.

How this file was checked. The drafter read the code at HEAD and ran these read-only, with `.venv/bin/python -B`, in-process:
- the probe, the sha256 of the inputs, the timings;
- the G4c host patterns of section 5, put into `redact.PATTERNS` in the drafter's process only;
- the card separator matrix of 3.4;
- the p1d_a mutant checks of 9.3.

Two further runs were made in a throw-away worktree /tmp/g4v4-a6, which has since been removed: the G4c patterns plus the three
fixture cells, then pytest on 8 suites. Raw scripts are in the drafter's scratch; nothing was committed. No file of the repository
was changed. Line numbers below are cd8d375's and always come with the name (section 0.1). The coordinator asked for no more test
batches because of machine load (load 10.5 on 4 cores), so some numbers are marked NOT RE-MEASURED, each with its reason.

## 0. Package line
- Package: G4 (plan item P1c, ORDER 006 item 1). Path class: redaction. Extended review: yes (no round cap).
- Lead rule (unchanged): build only a gap that a failing input proves. A gap with no failing input is cut.
- Depends on, all merged: G0, G7 with fix rounds 2-4, gate round 4, P1d-a rounds 2-3. The base sha is the first commit of
  `cloud/core-c` that the builder starts from; it is the base sha of the evidence.
- Phase 0 stop condition (v3 section 0): MET and RESOLVED. It was met because G7 r3, gate r4, G7 r4 and P1d-a r3 changed
  `_Redactor.settle`, `runmap.redact_text`, `channel.clean`/`settled` and gate.py after v3's base 193605f. It is resolved because
  v4 is written against cd8d375, which holds all of them, and every step below is re-based on it.
- Open dependencies that can still change what G4 touches: (a) a G7 fix round 5, if one is merged before G4 starts (worktree
  /tmp/core-c-g7r5); (b) any later P1d-a round (it may touch approvals/gate.py and the rows of tests/fixtures/p1d_cases.py).
  Phase 0 (section 12) handles both by the rule in 0.2.
- Source of the code: our own (rung 5), with Python stdlib `base64` as the decoder. Nothing is copied from another repository.
- Target files:
  - `src/hadavin_sdk/guard/runmap.py`: the scan refactor and the base64 step.
  - `src/hadavin_sdk/guard/redact.py`: kind ENCODED, `place_encoded`, the host patterns, the `_build` tie-break, the docstring.
  - `src/hadavin_sdk/defaults.py`: 8 constants and 2 comment clauses; SPINE's file, its own commit.
  - `src/hadavin_sdk/approvals/channel.py`: one kind added to `_ASSIGNMENT_KINDS` (L10).
  - `src/hadavin_sdk/approvals/gate.py`: one comment.

### 0.1 Cite table (name, file, line at cd8d375)
Rule for the builder: a line number is a hint, the NAME is the cite. Before each phase, `grep -n` the name; when the line moved,
go by the name.
| name | where |
|---|---|
| `redact_text` (def / `_within_cap` / `started =` / `try` / views / first `redact(` / R2 check / pairs / `for view in views:` / except tuple / `mapping.update(current)`) | runmap.py 533 / 554 / 555 / 556 / 560-561 / 563-565 / 567 / 569-577 / 578-591 / 593-596 / 603-604 |
| `_decoded_masks` (clock read per stored original) | runmap.py 488-521 (502) |
| `_views`, `_held`, `_clean`, `fits_after_nfkc`, `_expanded_len`, `undo` | runmap.py 445, 479, 427, 218, 207, 162 |
| `escape_placeholders`, `neutralise_untrusted`, `redact_untrusted` | runmap.py 354, 372, 377 |
| `_GRAMMAR`, `storable`, runmap `STORED_KINDS` | runmap.py 233, 286, 44 |
| `enforce_map` (overlap sentence of the docstring; `raise RedactionError("NotSettled")`) | runmap.py 688-775 (730-733; 775) |
| `_rules_conflict`, `snapshot`, `held_value_left` | runmap.py 791, 885, 934 |
| HOSTNAME entry of `PATTERNS` (comment above) | redact.py 406-412 (399-405) |
| `_KEPT_HOST`, `_LABELS`, `_KIND`, `_OPENINGS`, `_OWN_OUTPUT`, `strip_ansi` | redact.py 860-862, 867, 883, 884, 888, 898 |
| `redact()` (settle call) | redact.py 940-962 |
| `_Redactor` counter restore | redact.py 1105-1115 |
| `find` (fold-scan call) | redact.py 1144 (1150-1151) |
| `settle` (`raise RedactionError("NotSettled")`) | redact.py 1159-1218 (1217) |
| `_fold_scan` (`splitlines`) | redact.py 1298 (1311) |
| `_build` (sort key / rules loop) | redact.py 1794-1856 (1810-1813 / 1815-1820) |
| `_SETTLE_ROUNDS`, `SECRET_KINDS`, `_kind`, `_EVERY_COPY`, `_sweep`, `_replace_standalone`, `redact_many` | redact.py 1928, 2017-2033, 2068, 2076, 2081, 2102, 2123 |
| `MAX_MAP_ENTRIES`, budget comment (the `clean()` clause), `REDACT_BUDGET_S`, `SPELLED_MAX_*`, `STORED_KINDS` | defaults.py 24, 52-81 (77-81), 82, 90-91, 150 |
| `clean` (first `redact_text` / joined `redact_text`), `_MAX_REREADS`, `SETTLE_NOTE`, `_reread`, `settled`, `_TAGS`, `_ASSIGNMENT_KINDS`, `_neutralise` | channel.py 25-52 (37 / 44), 62, 67, 70, 76-95, 97, 98, 101 |
| `cards._card`, `requests` summary fallback | cards.py 58-63, requests.py 35-51 |
| `_CONTROL_CHARS`, `strip_controls`, `_PLACEHOLDER_DOT` (comment), `_DOMAIN_LAST`, `_whole_token`, `_outside_code`, `defang_text`, `undefang_text`, `sanitise_text`, `withhold_commands` | gate.py 135-146, 172, 241 (239-240), 256, 263, 295, 312, 324, 405, 774 |
| `redact_layered` (catches `TooDeep` only) | tools.py 976-983 |
| `redact_bundle` (`redact_untrusted` call / `Counter`) | k1b/redaction.py 172 (188 / 195) |
| agent_loop map ceiling; card None on a raise | agent_loop.py 427, 547; 622-625, 649-654 |

### 0.2 Phase 0 rule for the open dependencies (by NAME, not by line)
1. `git diff cd8d375 <base-sha> -- src/hadavin_sdk/guard/runmap.py src/hadavin_sdk/guard/redact.py src/hadavin_sdk/defaults.py src/hadavin_sdk/approvals tests/fixtures/p1d_cases.py tests/p1d_a_mutants.py tests/redact_mutants.py tests/gate_mutants.py tests/p1c_builders.py tests/test_redact_idempotent_property.py`.
   An empty diff means go.
2. Otherwise, for each name in 0.1 the diff touches, re-read that function or entry and compare it with the step of this ticket
   that names it. STOP and report only when the change contradicts a numbered step:
   - a new `except` clause in `redact_text`;
   - a second `redact(` call outside `_pass_one`;
   - a change to `_LABELS`, `SECRET_KINDS` or the HOSTNAME entry;
   - a new literal `raise RedactionError("NotSettled")` in runmap.py;
   - a p1d row whose input holds a private host name.
   A pure line shift, or a change to a name G4 does not touch, is no stop: re-derive the lines and go on.
3. p1d rows are found by id (`ROW_BY_ID["H27"]`, `["L2"]`, `["L3"]`, `["L11"]`, `["D3b"]`, `["D3c"]`), never by line. Gate rules
   are found by name (`_PLACEHOLDER_DOT`, `_outside_code`, `_per_part`, `_defang_prose`). Section 9.3's three new `after` cells and
   the A4/A5/A38/A6 killers are re-checked in Phase 4 by running them (`python tests/p1d_a_mutants.py A4 A5 A38 A6`). If a killer
   named here no longer kills, STOP and report: no killer is invented.

## 1. Problem in plain words
A secret that is only written in base64 reaches the model today, because the redactor has no decoded view:
- Short base64 blobs (under 40 characters) pass unchanged, whether alone, in a sentence, in JSON or after `data=`.
- Wrapped base64 passes when the lines are short, or leaves its last line readable.
- Long unbroken blobs are already masked whole by HIGHENTROPY.

Private host names are masked only in part:
- A private host name is masked only up to its private suffix: `db01.corp.example` becomes `<HOSTNAME_1>.example`.
- A bare host label after `host`, a label with an underscore and `[.]` dots are not masked at all.

Bare numbers without a label are not masked. That is an accepted decision (order 64 item 4); G4 writes it down and pins it.

### What the probe proves (evidence/p1c_probe.py, seed 20261120), RE-MEASURED
The probe was re-run unchanged on 1e16ab8, in-process, by wrapping the probe's `run` to record its inputs. 1e16ab8's src differs
from cd8d375's only in approvals/gate.py (P1d-a r3), which no probe call reaches. CPU 2.2 s for the whole probe. The totals and
every row list are the same as v3's (193605f):
| gap | rows | leaked at the base | G4 result |
|---|---|---|---|
| 1 base64 (1b 128 + 1c 14) | 142 | 52 (1b 48, 1c 4); 88 of the rest held by HIGHENTROPY | 52 closed; 85 unchanged; 5 change kind from HIGHENTROPY to ENCODED (no leak before or after) |
| 2 host names | 44 | 26: 12 whole, 14 part | 19 closed; 3 stay (limits: rows 10, 15, 16); 4 kept on purpose (6, 8, 9, 42); 18 already masked stay |
| 3 bare numbers | 43 | 24 not masked, 2 in part, 17 whole | not a gap: written down and pinned by class |
| 4 hostile corpus | - | - | CUT: the old 30-row corpus is not in this repository |

The gap 2 result is MEASURED. The G4c patterns of section 5 were put into `redact.PATTERNS` in-process and the probe was run
again. Exactly rows 6, 8, 9, 10, 15, 16 and 42 stay readable, and gap 1 and gap 3 are unchanged (no base64 step was in that run).

Rows 31 (`dial bücher.internal now`) and 41 (full-width dots) are already masked by the fold scan, so G4 closes 19 host rows.

## 2. Decision D1 and the central refactor
### 2.1 Where the step plugs in, and why not "decode before pass 1" (unchanged from v3)
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

    def clock(self) -> None: ...             # ONE time.thread_time() read; past the deadline: InputTooLarge
    def take(self, chars: int) -> None: ...  # units += 1, decoded_chars += chars; over B64_MAX_UNITS or
                                             # B64_MAX_DECODED_CHARS: InputTooLarge

class _B64Unit(NamedTuple):
    start: int               # offset in the ANSI-stripped text (3.1 point 5)
    end: int
    written: str             # the unit as written, line breaks included: the ENCODED original
    joined: str              # its lines, stripped, joined with nothing between: what _b64_text decodes
    lines: tuple[str, ...]   # its lines as written (stripped), for the held rule

def _scan(text, mapping, cache, neutralise, budget, depth) -> tuple[str, dict[str, str]]
def _pass_one(text, mapping, cache, neutralise, budget, depth) -> RedactionResult
def _b64_units(text: str) -> tuple[str, list[_B64Unit]]     # (the ANSI-stripped text, its units); (text, []) with no run
def _b64_held(unit: _B64Unit, known: Mapping[str, str]) -> bool
def _b64_text(joined: str) -> str | None                      # 3.2
def _b64_hits(units, known, neutralise, budget, depth) -> tuple[list[bool], dict[str, str]]   # 3.4; (hits, kept entries)
def _b64_place(stripped: str, units: list[_B64Unit], placeholders: dict[str, str]) -> str
```
- `_scan` is the whole of today's `redact_text` body except the cap, the exception wrapper and the map write. It returns the output
  and the new map and never writes `mapping`.
- `_pass_one` calls the module-level name `redact` (as `redact_text` does today), never a local alias. tests/test_k5_tools.py
  (`broken`, `flaky`, about 302-343) and tests/test_k5_round11.py patch `runmap.redact`, and must still see every call.
- The private signatures are part of the contract. I13 drives a spent deadline and the caps through `_ScanBudget` and `_pass_one`
  directly, because the public API cannot set a deadline that is already spent at the step.

### 2.3 `redact_text`'s new body (rewritten to cd8d375; the docstring gains one paragraph, section 11)
1. `_within_cap(text)`: unchanged, before the clock.
2. `started = time.thread_time()`: unchanged line; mutant R1 pins it.
3. `try:` then `cache = getattr(mapping, "redact_cache", None)`. It stays inside the try (tests/test_runmap_map_write.py, `test_m8_*`
   about line 37).
4. `budget = _ScanBudget(started)`, then `out, current = _scan(text, mapping, cache, neutralise, budget, 0)`.
5. The two handlers exactly as at cd8d375 (runmap.py 593-596), text and comment unchanged:
   ```python
       except (InputTooLarge, TooDeep, RedactionError):
           raise  # as raised: the text of `NotSettled` (the settle loop's cap) is kept for the caller's log
       except Exception as exc:  # noqa: BLE001 - whatever the redactor raised, nothing is sent
           raise RedactionError(type(exc).__name__) from None
   ```
   So a `RedactionError("NotSettled")` from either `redact()` call of `_pass_one` reaches the caller with the text "NotSettled".
   tests/test_redact_settle_loop.py `test_a_chain_that_still_changes_in_round_four_*` asserts `str(err.value) == "NotSettled"`
   through `runmap.redact_text`, and stays green.
6. The comment block and `mapping.update(current)` / `return out` at four spaces, unchanged. Gate mutants R3, R3b and R3c pin
   `    mapping.update(current)\n    return out\n` exactly once in runmap.py. A raise anywhere in steps 3-4 leaves `mapping`
   unwritten. G4 writes no `raise RedactionError("NotSettled")` in runmap.py: the one in `enforce_map` is pinned by gate mutant R5
   (tests/gate_mutants.py about line 176), and a second copy would make R5 replace both.

### 2.4 `_scan`, numbered (today's lines 557-592 moved; two `redact(` calls replaced by `_pass_one`)
1. `started = budget.started`: a local of that name, so the existing check lines keep their text.
2. `text = fits_after_nfkc(_clean(text))`; if `neutralise`: `text = fits_after_nfkc(neutralise(text))`. Call this text T.
3. `scan = not T.isascii() or any(c in T for c in "\\%&")`; `views = _views(T) if scan else []`.
   - The views are of T, computed BEFORE pass 1 as today, and NEVER of the replaced text T2.
   - Reason: a view of T2 would hold our own `<ENCODED_n>`, and `neutralise_untrusted` would escape it to the look-alike
     `‹ENCODED_n›` before redaction.
4. `result = _pass_one(T, mapping, cache, neutralise, budget, depth)`; `out, current = result.text, result.mapping`.
5. `if views and time.thread_time() - started > defaults.REDACT_BUDGET_S: raise InputTooLarge("InputTooLarge")`. This line is
   unchanged (mutant R2).
6. `pairs = _decoded_masks(current, T, started + defaults.REDACT_BUDGET_S) if views else []`.
   - An ENCODED original is plain ASCII base64 with no `%`, `\` or `&`, so `_decoded_masks` skips it before any decode.
   - `_decoded_masks` reads the clock once per stored original (runmap.py 502). At depth 1 or more, `current` holds the incoming
     map, so a decoded view whose join has views pays up to `len(map)` clock reads (at most `MAX_MAP_ENTRIES`). This is harmless and
     stated (review nit N4).
7. The neutralised pairs, unchanged.
8. `for view in views:` (one occurrence; p1d_a mutant A16 pins it). Inside the loop:
   1. the clock check (R3's condition, re-indented, 13.3);
   2. `neutralise(view)`;
   3. `view = _keep_earlier_masks(view, pairs)`;
   4. `again = _pass_one(view, current, cache, neutralise, budget, depth)`;
   5. the view rule, unchanged: `if again.mapping != current or _held(again.text) > _held(out): out, current = again.text, again.mapping`.

   In a view, a blob that was a hit on T is swept by pass 1, because ENCODED is a secret kind (every copy from 4 characters). It is
   therefore HELD there and not decoded again. A blob readable only in a view (`\/` slashes, `%3D` padding) is decoded in that view.
9. `return _clean(out), current`.

### 2.5 `_pass_one`, numbered
1. `started = budget.started`.
2. `first = redact(text, mapping=mapping, _cache=cache, _deadline=started + defaults.REDACT_BUDGET_S)`. This is pass 1 with G7's
   settle. Mutant 21's literal `_deadline=started + defaults.REDACT_BUDGET_S` stays in both redact calls of this function, which are
   the only two in runmap.py (two today as well).
3. `stripped, units = _b64_units(text)`. With no run (the gate, 3.1 point 1), return `first` here: no clock read and no other call.
4. Drop held units (`_b64_held(u, first.mapping)`, 3.3). For the decision, keep one unit per distinct `written`; every copy is still
   replaced in step 8. None left: return `first`.
5. `hits, kept = _b64_hits(units, first.mapping, neutralise, budget, depth)`. No hit: return `first`, whose output and map are
   byte-identical to the base commit's for that text.
6. `base = dict(mapping)`, then `base.update(kept)` (decision L8, 3.4 point 10).
   - `mapping` is the INCOMING map. Pass 1's additions are dropped: they hold junk such as one HIGHENTROPY entry per wrapped line of a
     blob that is now one ENCODED.
   - `kept` are the decoded view's new entries of kinds that can never be stored.
7. `placeholders = dict(zip(runs, place_encoded(base, runs)))`, with `runs` the `written` of the hit units, in order.
8. `T2 = _b64_place(stripped, copies, placeholders)`, where `copies` are all units of `stripped` (step 3, before the dedupe) whose
   `written` is a key of `placeholders`. Every copy is replaced by position; units do not overlap.
9. `return redact(T2, mapping=base, _cache=cache, _deadline=started + defaults.REDACT_BUDGET_S)`. Pass 1 leaves a placeholder
   alone, so the result holds `<ENCODED_n>` where the blob stood. Nothing is mapped back by position.

Settle and fold interplay:
- Step 9 is a full `redact()`, with its own `_SETTLE_ROUNDS` cap (4, redact.py 1928) and its own fold scan. It reruns every settle
  chain of T2; a chain in T is still in T2, because only base64 units changed.
- MEASURED with a stand-in: the property test's `CONSTRUCTED[0]` chain followed by `" "`, `","` or `"\n"` and a secret placeholder
  of another kind (`<JWT_1>`) needs the same number of settle rounds (3 `find` passes) as the chain alone, and gives the chain's own
  output plus the placeholder.
- A `RedactionError("NotSettled")` or an `InputTooLarge` raised in step 2 or step 9 propagates. `redact_text` then refuses the text
  and does not write the map (I21).
- Cost: a text with a hit pays two `redact()` calls per scanned spelling (section 8).

### 2.6 Failure behaviour by depth (decision L4)
| raised where | depth 0 (the input, its views) | depth 1 or more (inside a decoded view) |
|---|---|---|
| `TooDeep` from `_views` / `undo` | propagates: refused, as today | caught in `_b64_hits`: every unit of that decoded view is a hit unread (L4) |
| the decoded join over `MAX_REDACT_CHARS` after NFKD (`_expanded_len`) | - | checked before the recursive call: every unit of that view is a hit unread |
| `InputTooLarge` from the clock, `_ScanBudget.take`, `_decoded_masks`, `fits_after_nfkc` of a view | propagates: refused | propagates: refused |
| `RedactionError("NotSettled")` | propagates (as raised, 2.3 step 5) | propagates |

A decoded view that only grows past the cap through its escapes (a `ﷺ` run) is refused. This is stated, not handled.

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
   - Stated limit L-B6: a real blob made only of `A-Z`, `0-9` and `_`, written between `<` and `>`, is taken for a marker and is not
     decoded.
3. WRAPPED BLOCK. Two or more consecutive lines, split on `\n`; a trailing `\r`, and spaces or tabs at both ends of a line, are
   ignored. A block must meet every rule:
   - every line holds only alphabet characters;
   - the first line is at least `defaults.B64_WRAP_MIN_CHARS` (16) long, and its length is a multiple of 4;
   - every line but the last has the first line's length and no `=`;
   - the last line is 1 to first-length characters, and may end in `=` or `==`.

   It is one top-to-bottom pass, and each line is in at most one block. A block is maximal: it ends at the first line that breaks a
   rule, and that line is included if it is a valid shorter last line. It is linear (the taken lines are an index set). The
   unambiguous cases (review N2):
| # | lines (W = alphabet characters; "A16" = 16 of them) | units |
|---|---|---|
| 1 | A16 / B10 | one block (lines 1-2) |
| 2 | A16 / B16 / C16 | one block (lines 1-3; a last line of full length is valid) |
| 3 | A16 / B10 / C16 | block lines 1-2 (line 2 is a shorter last line and ends it); line 3 a RUN unit (16 >= 12) |
| 4 | A16 / B20 | no block (line 2 longer than line 1); two RUN units |
| 5 | A15 / B15 | no block (15 is not a multiple of 4); two RUN units |
| 6 | A16 / (B15 + "=") / C16 | block lines 1-2 (a last line may end in `=`); line 3 a RUN unit |
| 7 | A16 / B8 / C20 / D4 (two adjacent blocks) | block lines 1-2; block lines 3-4 |
| 8 | "  " + A16 + "\r" / B4 | one block (indentation and `\r` ignored); `written` keeps the indentation between the lines |
4. A unit is a block, or a RUN that does not start inside a block. `written` is the stretch of the stripped text from the unit's first
   character to its last.
5. ANSI: units are found on `strip_ansi(text)` (redact.py 898), and T2 is built from that stripped text.
6. Offset 0 only. A run glued to other alphabet characters is one longer run that does not decode: stated limit L-B1, pinned by a
   strict xfail.
7. Duplicates: units with the same `written` are decoded once and count once against the budget.

### 3.2 Decode (`_b64_text(joined) -> str | None`), unchanged from v3
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

### 3.3 HELD (`_b64_held`), unchanged from v3
`secret` is the set of originals of placeholders in `first.mapping` whose kind is in `SECRET_KINDS` (ENCODED included). A unit is HELD
when `written in secret`, or when every line is in `secret` or is a substring of the original of a JWT or PRIVKEY placeholder.

Only SECRET kinds hold (L12). Effect: the 80 HIGHENTROPY rows of 1b, the 3 `data:` rows and the 2 BASIC rows of 1c, JWTs and PEM
blocks are not decoded. 1c rows 2, 3, 6, 7, 10 and 11 become one ENCODED.

### 3.4 The decoded view and the hit rule (`_b64_hits`), numbered (separator replaced, review B2)
1. For each unit, in order: `budget.clock()`.
2. `len(u.joined) > defaults.B64_MAX_UNIT_CHARS`: no decode; `budget.take(0)`; a hit unread.
3. `d = _b64_text(u.joined)`. None: not a hit, not counted.
4. `depth == defaults.B64_MAX_DEPTH`: `budget.take(0)`; a hit unread (L4).
5. Otherwise `budget.take(len(d))`. The unit's piece is `_clean(d)`. A piece that holds `_B64_SEP` is a hit unread (fail closed:
   a decoded text cannot fake the boundaries).
6. No piece: return. `joined = _B64_SEP.join(pieces)` with **`_B64_SEP = "\n\n;\n\n"`** (v3's `"\n\x1e\n"` is withdrawn, see below).
   If `_expanded_len(joined) > defaults.MAX_REDACT_CHARS`, every piece's unit is a hit unread; return.
7. `seen` is the pieces as `_scan` will read them: `fits_after_nfkc(neutralise(fits_after_nfkc(_clean(joined))))` (no neutralise
   when None), split on `_B64_SEP`. If `len(seen) != len(pieces)`, every piece's unit is a hit unread; return.
8. `out, scanned_map = _scan(joined, dict(known), None, neutralise, budget, depth + 1)`. `known` is `first.mapping`, `_cache` is None,
   and the budget and neutralise are the same. On `TooDeep`, every piece's unit is a hit unread (2.6).
9. `after = out.split(_B64_SEP)`.
   - If `len(after) != len(pieces)`, every piece's unit is a hit (fail closed).
   - Else piece i is a hit when `_held(after[i]) > _held(seen[i])`.
10. Kept entries (decision L8): `{k: v for k, v in scanned_map.items() if k not in known and kind_of(k) not in runmap.STORED_KINDS and kind_of(k) != "ENCODED"}`.
    These are the decoded view's new values of kinds that are never stored (no secret kind is in `defaults.STORED_KINDS`, and
    config.py 280 rejects a stored kind outside it). Inner ENCODED entries of nested blobs are dropped, so ENCODED numbers do not
    skip. Every other entry of `scanned_map` is thrown away.

Why the separator changed (review B2, MEASURED):
- `channel._neutralise` is `withhold_commands(sanitise_text(t, defang=False))`. `sanitise_text` strips `_CONTROL_CHARS` (gate.py
  135-146: `range(0x0B, 0x20)` holds `\x1e`), so v3's separator became `\n\n`. Measured: 3 pieces gave 1 after `_neutralise`.
  `seen` and `after` therefore had one element, and every decodable unit on every card became a hit.
- `"\n\n;\n\n"` survives `channel._neutralise`, `neutralise_untrusted` and no neutralise, then `redact()`. Measured: 31 piece ends
  (keys, fences, quotes, tags, `-----BEGIN ...-----`) x 9 piece starts x the 3 neutralise choices = 837 joined texts.
  - 81 of the 837 texts lose a separator. They are exactly the 3 ends that open a quoted credential value (`secret="`, `api_key='`,
    `"password": "`), whose quoted-value patterns cross lines. Those fall back to "every unit a hit" (fail closed, over-masking only).
  - With `.:.:.` as the separator, 20 of 42 texts already failed on `password=`-style ends (the value patterns take the separator as
    the value). `;` is not taken.
- It holds no `\`, `%` or `&` and is ASCII, so it does not turn on `scan` for the joined text. It holds no alphabet character, so it
  is never part of a run.

What a fence or tag split across pieces does: `seen` and `after` are both made by the same neutralise of the same joined text. A
fence opened in piece i and closed in piece j keeps the separator lines between as code body, verbatim (measured: count kept), and
the redaction of the body still runs. A rewrite that changes the number of separators falls back to all hits. Not taken: per-piece
`_scan` calls (L15 fallback). Measured: 300 decoded pieces that each find a secret, scanned one by one against a 1,000-entry map,
cost 6.4 s (one `_build` per hit), against 0.22 s for one joined scan of 2,000 such pieces.

### 3.5 What stays out of G4a, and the bundle path
- `redact_bundle` calls `runmap.redact_untrusted` for every string (k1b/redaction.py 188), so the bundle path gets the base64 step.
  L-B3: a direct call of `redact()` or `redact_many` (tests, a future caller) gets no base64 step.
- k1b counting: `redact_bundle` returns `Counter(_kind(p) for p in mapping)` (k1b/redaction.py 195). Under L8 v4 the map holds one
  ENCODED entry per distinct hit blob, plus the kept decoded entries (secret and regulated kinds). So the report gains an
  `ENCODED n` row, and `SECRET` (or another non-stored kind) counts a value that was only written encoded. Stated: such a value is a
  distinct value the bundle hid.
- Pass 2 of the bundle sweeps the blob, which is HELD, so it is not decoded again. Pass 2 also sweeps any plain copy of a kept
  decoded secret.
- Not changed: `tools._b64_holds` / `tools._derived` and `k1b.redaction._pair`.
- `tools.redact_layered` catches only `TooDeep` (tools.py 983), so an `InputTooLarge` from the unit cap makes a tool result a tool
  error.

## 4. G4b: the kind ENCODED (guard/redact.py)
1. `_LABELS = tuple(dict.fromkeys([*(label for label, _ in PATTERNS), "ENCODED"]))` (redact.py 867). ENCODED is NOT in `PATTERNS`.
   - Everything built from `_LABELS` follows: counters, `_KIND`, `_OPENINGS`, `_OWN_OUTPUT` (`password=<ENCODED_1>` and
     `password=‹ENCODED_1›` are own output).
   - The growth-factor test (tests/test_runmap_enforce_map.py `test_e1_the_growth_factor_covers_the_longest_placeholder`, about
     line 460) still passes: ENCODED is 7 letters, AZURERESOURCE 13.
2. `SECRET_KINDS` gains "ENCODED" (redact.py 2017-2033).
3. Counter restoration needs no new code (redact.py 1105-1115).
4. `def place_encoded(mapping: dict[str, str], runs: list[str]) -> list[str]` is the only writer of ENCODED.
   - For each run in order, it returns the placeholder the run gets and adds it to `mapping` IN PLACE: exactly one entry per new run.
     No `_PIECE` pieces, no `_spelled`, no journal.
   - Numbering: the next number is `_Redactor(mapping).counters["ENCODED"] + 1`. Example: `{"<ENCODED_5>": a, "<ENCODED_2>": b}` gives
     `<ENCODED_7>`.
   - A run that is already the original of an ENCODED placeholder gets that placeholder. That is the function's contract for direct
     callers; through `_pass_one` it is unreachable, because such a run is HELD.
   - A run that is the original of an identifier-kind placeholder (TENANT) gets a NEW ENCODED entry.
   - v3's branch "a run that is the original of a SECRET-kind placeholder gets that placeholder" is DELETED (review N1: such a unit is
     HELD by 3.3 and never reaches `place_encoded`).
5. `_build` tie-break, restricted to the same original (review design check, taken).
   - The sort key at redact.py 1810-1813 (`key=lambda kv: -len(kv[1])`) is NOT changed. The rules loop at 1815-1820 becomes:
     ```python
     rule = _sweep(placeholder, original)
     if rule is not None and (
         original not in self._rules
         or (_kind(placeholder) in SECRET_KINDS and _kind(self._rules[original][1]) not in SECRET_KINDS)
     ):
         self._rules[original] = (n, placeholder, rule)
     ```
   - For one original held by an identifier and by a secret kind, the secret kind's rule wins (as `runmap._rules_conflict` already
     does in `snapshot`). Two DIFFERENT originals keep the order the stable sort gives, so `enforce_map`'s docstring ("the earlier
     in the map when equal", runmap.py 730-733) stays true.
   - No mutant pins either line (checked: no `old` text of the five mutant files holds them).
   - MEASURED at the base, with `<SECRET_1>` standing in for ENCODED: `redact("pre"+X+"post and "+X+" alone", mapping={"<TENANT_1>": X, "<SECRET_1>": X})`
     with `X = "QUJD"+"REVG"+"R0hJ"` gives `preQUJDREVGR0hJpost and <TENANT_1> alone`. That is the gap TB-2.7 closes.
   - MEASURED at the base: `enforce_map("x ab-cd-ef y", m)` gives `x ab-<TENANT_1> y` for `{"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd"}`
     and `x <SECRET_1>-ef y` for the swapped order. TB-2.8 pins both unchanged. v3's key would have changed the first to
     `x <SECRET_1>-ef y`.
6. `defaults.STORED_KINDS` does NOT change, and `runmap._GRAMMAR` gets no ENCODED entry.
7. `RedactionResult.actions` does not count ENCODED replacements (it has no reader in src; stated).
8. approvals/channel.py 98 `_ASSIGNMENT_KINDS` gains "ENCODED" (L10).

Fallback if the lead declines the name (L1): `place_encoded` issues `<SECRET_n>`, points 1, 2 and 8 are dropped, and the tests assert
SECRET.

## 5. G4c: whole host names (guard/redact.py, the HOSTNAME entries of PATTERNS)
### 5.1 One place for the suffix list (unchanged)
`_HOST_BARE = "internal|local"` and `_HOST_TAIL = "corp|lan|intranet|intra|localdomain|home" + _HOST_DOT + "arpa"`, beside the pattern.
`defaults.PRIVATE_SUFFIX_LABELS` is a different job and is not used. A `#` comment beside each names the other.

### 5.2 The main pattern (replaces redact.py 406-412; same place; no capture group). MEASURED in-process.
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
1. Start, changed from v3. A match does not start right after a name character or `-`, nor after a dot or a `[.]` that follows a name
   character. So it starts at the first label of a dotted token, as P1d-a round 3's `_DOMAIN` does (gate.py `(?<![\w-]\.)`). Two
   measured failures of the alternatives, both in the drafter's worktree:
   - v3's `(?<![\w.\-\]])` failed `tests/test_p1d_a_paths.py::test_property_no_linkable_host_on_the_card_and_the_card_reads_the_same_twice`.
     Its input `(x<HOSTNAME_1>&.]db-7.corp.internalx` was not masked at all (no start after `]`), where the base gave `db-7` masked.
   - A plain `(?<![A-Za-z0-9_-])` made `"a.-_" * 12500` quadratic: 2.2 s for 20,000 characters, and `redact_text` 11.47 s, which
     failed `test_secret_patterns_are_linear_on_a_50000_character_run[name run with dots]`.

   v4's start masks that input as `(x<HOSTNAME_1>&.]<HOSTNAME_1>` and masks `x/.db01.corp.example` as `x/.<HOSTNAME_1>`. Measured:
   0.001-0.007 s on 50,000 characters of `a[.]`, `a.-_`, `a-`, `a.`, `ab-cd.` and `a[.]`...`corp`.
2. Label class ASCII (L11). Non-ASCII labels stay the fold scan's job (it runs first on every non-ASCII line, redact.py 1150-1151).
3. Tail: after a `_HOST_TAIL` suffix, the rest of the dotted name is in the match. A trailing dot is not a label
   (`db01.corp.example.` gives `<HOSTNAME_1>.`). A port, a path and `@` end the name.
4. Bare suffix `.internal` / `.local`: a following label or `(` means code (`jdk.internal.reflect`, `threading.local()`), so there is
   no match.
5. Suffix boundary `\b` -> `(?![\w-])`, with a hyphenated rest taken in (review M3, decision L14).
   - The base's `\b` matched up to the suffix when a `-` followed it, and left the rest readable. v3's `(?![\w-])` would have left the
     whole name unmasked (a fail-open change).
   - v4 takes `-` and label characters after the suffix into the name, and, for `.internal`/`.local`, the dotted labels after them
     (code names hold no `-`).
   - MEASURED (base -> v4):
     - `db01.corp-prod`: `<HOSTNAME_1>-prod` -> `<HOSTNAME_1>`
     - `x.local-dev`: `<HOSTNAME_1>-dev` -> `<HOSTNAME_1>`
     - `x.internal-api`: `<HOSTNAME_1>-api` -> `<HOSTNAME_1>`
     - `db01.corp-prod.example`: `<HOSTNAME_1>-prod.example` -> `<HOSTNAME_1>`
     - `x.local-dev.foo`: `<HOSTNAME_1>-dev.foo` -> `<HOSTNAME_1>`
6. `_KEPT_HOST` is unchanged and applied to the whole match in `_decide`. MEASURED unchanged: `x.svc.cluster.local`,
   `x.svc.cluster.local.foo`, `eu-west-1.compute.internal`, `ec2.internal`, `jdk.internal.reflect.Method`, `threading.local()`.
   A defanged `x[.]svc[.]cluster[.]local` is masked (accepted).
7. Java packages: `com.acme.corp.billing.Service` was `<HOSTNAME_1>.billing.Service` and becomes `<HOSTNAME_1>` (limit L-H1).

### 5.3 The host-key rule (a second ("HOSTNAME", HOSTKEY) entry right after the main one; group 1 is the value). MEASURED in-process.
```
_HOST_ARCH = r"(?:x86(?:_64)?|i[3-6]86|amd64|arm64|aarch64|ppc64)"   # CPU names a build log writes after `host`
HOSTKEY = (r"(?i)(?<![\w-])(?:--)?host(?:name)?(?:[\"']?[ \t]*[:=][ \t]*[\"']?|[ \t]+)"
           r"(?!" + _HOST_ARCH + r"(?![\w-]))"
           r"([A-Za-z][A-Za-z0-9_-]{0,60}(?:-[0-9]|[0-9]{2}))(?![\w\-/@])(?!\.\w)")
```
Decision L13 (review M2 and N4). The value is one label of 3 to 63 characters that starts with a letter and ENDS in two digits or
in a hyphen and a digit, and is not a CPU architecture name.

MEASURED on the base, v3 and v4:
- Kept by v4 (each was masked by v3): `host ec2 failed`, `host k8s node`, `host x86 box`, `host http2 on`, `host x86_64`,
  `host eth0 up`, `host arm64 runner`, `host: x86_64-unknown-linux-gnu` (`rustc -vV` prints it), `hostname: Web2`, `host web1 down`.
- `host s3 bucket` was not masked even by v3, because `s3` is 2 characters. The review's claim for it is contested in section E.

The sweep side effect (review M2): a value this rule registers is a HOSTNAME entry, and `_sweep` / `_replace_standalone` (redact.py
2081, 2102) then replace every later standalone copy in the run.
- MEASURED: v3 turned `host ec2 failed; see ec2.internal, k8s.io, s3://b and x86_64 builds` into
  `host <HOSTNAME_1> failed; see <HOSTNAME_1>.internal, ...`. v4 leaves the whole line unchanged.
- For a real host the side effect is intended and stated: `host db01 down; tail db01.log` gives
  `host <HOSTNAME_1> down; tail <HOSTNAME_1>.log`.

Masked on purpose, stated in SECURITY:
- a label of letters and two or more digits after `host`, also when it is not a host: `host py311 image`, `host sha256 sum`
  (measured, masked);
- with it, every later standalone copy in the run.

Not masked (limit L-H4): a host name with a single trailing digit after a letter (`web1`, `db1`, `node7`).

Must-keep rows of v3, all MEASURED unchanged:
`host is down`, `server timed out`, `Server: nginx`, `Server: nginx/1.18.0`, `Server: AmazonS3`, `server 500 error`,
`ghost town db01`, `ghost=ab12`, `Host: api.github.com`, `host: localhost`, `--host 0.0.0.0` (IPV4 masks the address),
`host 1 of 3 failed`, `the hostname is unknown`, `host x-ray`, `host re-election`, `host 2026-11-20T10:00 started`.

Closed, measured: rows 33 `host <HOSTNAME_1> is down`, 34 `host: <HOSTNAME_1>`, 35 `hostname=<HOSTNAME_1> state=down`,
36 `psql --host <HOSTNAME_1> --port 5432`.

### 5.4 Restorable grammar (unchanged)
`runmap._GRAMMAR["HOSTNAME"]` is unchanged, so an original with `_` or `[.]` is never stored. Fallback (L5): add `_` to the grammar.

## 6. G4d: bare numbers (written down, pinned; unchanged)
One paragraph in the module docstring of guard/redact.py, after the "What this is not" paragraph:

"A bare number with no label or context (for example `ref 55556666 paid`) is not masked, by decision (order 64 item 4). Masked by
shape: 10 to 16 contiguous digits (PHONE; exactly 12 as ACCOUNTID) and 16 digits in four groups of four joined by spaces or hyphens
(CREDITCARD). Other groupings are masked in part or not at all: 16 digits joined by dots lose their first 12 to MAC and keep the last
group; 15 digits in 4-6-5 groups lose the first 10 to PHONE and keep the last 5."

The pin, by class, RE-MEASURED on 1e16ab8 (the same rows):
- 24 not masked: 1-7, 9-12, 14-20, 30, 35, 38-40, 43;
- 2 in part: 29, 32;
- 17 whole: 8, 13, 21-28, 31, 33, 34, 36, 37, 41, 42.

## 7. Constants (defaults.py, one SPINE commit holding only these lines and their comments)
They are placed after `SPELLED_MAX_FORMS` (defaults.py 91). Exact comment above each, one line each; no host and no 32-character run
in them:
| constant | value | comment text and the source of the number |
|---|---|---|
| `B64_MIN_CHARS` | 12 | "# shortest base64 run (padding not counted) the redactor decodes; 12 characters are 9 bytes". Source: under 15, the shortest leaked probe blob (1b row 83), and a multiple of 4. |
| `B64_WRAP_MIN_CHARS` | 16 | "# shortest first line of a wrapped base64 block; every line but the last has its length". Source: chosen; the probe wraps at 32, 64 and 76. |
| `B64_PRINTABLE_SHARE` | 0.90 | "# share of printable characters a decoded run needs to count as text". Source: chosen; Phase 4 sweeps 0.85 to 0.95. |
| `B64_UTF16_ZERO_SHARE` | 0.90 | "# share of zero bytes at the odd (LE) or even (BE) positions that reads a decoded run as UTF-16". Source: chosen; ASCII in UTF-16 has 1.0. |
| `B64_MAX_UNITS` | `MAX_MAP_ENTRIES` (2000) | "# decodable, not held base64 units per redact_text call (all views, all depths); one more is refused (InputTooLarge)". Source: the run map's default ceiling (L9). |
| `B64_MAX_DECODED_CHARS` | `MAX_REDACT_CHARS` (262,144) | "# decoded characters per redact_text call; past it the call is refused (InputTooLarge)". Source: the redactor's own cap. |
| `B64_MAX_UNIT_CHARS` | 65536 | "# longest base64 unit that is decoded; a longer one that pass one did not hold is masked unread". Source: a quarter of the cap. |
| `B64_MAX_DEPTH` | 3 | "# levels of base64 decoded and read; a unit found at this depth is masked unread". Source: the probe's double rows need 2, plus one of slack. |

Two comment clauses (review nit N5, taken):
- In the budget comment above `REDACT_BUDGET_S` (defaults.py 52-81), after "...every 1,024th unit of work of the compound-form scan
  (...)", add: "and, since G4, once before each base64 unit that is decoded or masked unread (`runmap._ScanBudget.clock`)".
- In the `clean()` clause (defaults.py 77-81), after "(at most 3 calls, none when pass 1 changed nothing)", add: "; a call whose text
  holds a decodable base64 unit that pass one did not hold also runs `redact()` a second time per scanned spelling and one scan of
  the decoded texts (G4)".

Fallback (L7): the eight constants as module constants in runmap.py; then write 65536 as `1 << 16`. tests/test_no_hardcoded_values.py
(about 164) forbids the literal `= 65536` in the `K5_FILES`.

## 8. Cost and map growth (re-measured; cards corrected)
Baseline RE-MEASURED on 1e16ab8 (whose redactor is cd8d375's): this container, `time.thread_time()`, best of 3, a fresh `RunMap`,
scratch script. The machine was loaded (the coordinator reported load 10.5 on 4 cores soon after), so read the ratios, not the
seconds.

| text | `redact_text` | `redact_untrusted` | v3 (193605f) |
|---|---|---|---|
| 100,000 characters of snake_case words and paths | 0.164 s | 0.173 s | 0.128 s |
| 100,000 characters of prose | 0.164 s | 0.151 s | 0.155 s |
| the snake_case text with one planted `password=` | 0.263 s | 0.262 s | 0.294 s |
| 2,000 base64 secrets (57,999 characters, each base64 of `password=` + 12 characters) | 0.086 s | 0.076 s | 0.085 s |

defaults.py 37-40 records that G7 r3 and r4 raised the worst-case cost (`password=` x N 2.5 to 3.2 s).

NOT RE-MEASURED, and why:
- the step's own cost on cd8d375: G4 is not built (I16 measures it in Phase 3);
- the prototype numbers on main 51c9fc4 (step 5.1 / 5.5 / 0.7 percent; 4,096 secrets 0.72-0.82 s): no main export was made, and the
  machine is loaded.

A text with a hit pays `redact()` twice per scanned spelling, plus one recursive `_scan` per spelling with units. Held units are
swept, never decoded twice.

MAX_MAP_ENTRIES: `defaults.MAX_MAP_ENTRIES` = 2000 (defaults.py 24) is `config.evidence.max_map_entries` (config.py 245).
agent_loop.py 427 and 547 end the run `NEEDS_PERSON` / `document_too_complex` when the map is over it.
- Per `redact_text` call, G4 adds one ENCODED entry per hit unit (at most `B64_MAX_UNITS`) plus the kept decoded entries (L8 v4:
  secret and regulated kinds only).
- A run that crosses its ceiling is refused by that existing check (I23).

Cost of the caps for legitimate big input, corrected (review M4). A text with more than 2,000 distinct decodable, not held runs, or
more than 262,144 decoded characters, raises `InputTooLarge`:
- a document ends `NEEDS_PERSON` `document_too_large`;
- a tool result becomes a tool error (`redact_layered` catches only `TooDeep`);
- a k1b bundle raises `InputTooLarge`;
- a CARD is NOT shown `SETTLE_NOTE`. The first `redact_text` calls of `channel.clean` (channel.py 37 and 44) and `cards._card`
  (cards.py 58-63) are not wrapped; only `settled`'s re-reads (channel.py 76-95) turn a refusal into `SETTLE_NOTE`. So
  `render_shadow` / `render_abstain` raise, and agent_loop.py 622-625 / 649-654 catch it as an unrenderable card: `card = None`,
  no card is posted, and the event is recorded `abstain_undelivered` or `shadow` with `result="undelivered"`;
- `requests` summary (requests.py 35-51) falls back to its short text with "Inputs: (too large to show here)";
- `FakeChannel.send` / `notify` and `SlackChannel` notify (channel.py 159, 166; slack_channel.py 187) raise to their callers.

This is the same path every card text over the redactor's cap takes today. It is stated, not changed (L17); TB-3.24 pins it.
Masking every further unit unread past the cap was not taken (contested in round 2, M7).

## 9. Expected results per probe row
### 9.1 Base64, 142 rows ("unchanged" = output and map digest equal to the base commit's, through both functions)
| rows | value | expected |
|---|---|---|
| 1b 1-5, 7, 8 | kv secret short | one `<ENCODED_n>` where the blob stood; the map holds the ENCODED entry and the decoded SECRET entry (L8 v4) |
| 1b 6, 9-16 | kv secret | unchanged (HIGHENTROPY holds it) |
| 1b 17-32 | bearer token | unchanged |
| 1b 33-37, 39, 40 | AWS key id short | ENCODED |
| 1b 38, 41-48 | AWS key id | unchanged |
| 1b 49-53, 56 | e-mail short | ENCODED (no EMAIL entry kept: EMAIL is a stored kind) |
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
| 1c 3, 6, 7, 10, 11 | wrapped at 64 / 76, no leak today | KIND CHANGE: exactly `<ENCODED_1>`; no HIGHENTROPY entry |
| 1c 4, 8, 12 | `data:` URL | unchanged (HIGHENTROPY) |
| 1c 13, 14 | `Basic <b64>` | unchanged (BASIC) |

RE-MEASURED on 1e16ab8:
- The leaked rows are exactly 1b 1-5, 7, 8, 33-37, 39, 40, 49-53, 56, 65-72, 81-88, 97-101, 104, 113-117, 120 and 1c 1, 2, 5, 9.
- `redact_untrusted` gives the same verdict on every 1b row.
- 1c has 14 rows: both `no_digit_line` searches find nothing, and they still consume the generator.

The constructed shapes are in section 10's TB list, each with its recipe and expected output.

### 9.2 Host names, 44 rows (G4 column MEASURED in-process with the patterns of 5.2/5.3)
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

Totals: 19 closed (13 part rows, 6 whole rows); 3 limits, 4 kept, 18 unchanged.

### 9.3 Other literal expectations in the tests tree that the host change turns (MEASURED where marked)
| where (by name) | today expected | after G4 (exact) | action |
|---|---|---|---|
| tests/fixtures/p1d_cases.py `ROW_BY_ID["H27"]` card (about 331-339) | `host <HOSTNAME_1>[.]example[.]com down` | `host <HOSTNAME_1> down` (MEASURED through `channel.clean`) | Modify the `after` cell |
| `ROW_BY_ID["L2"]` card (about 577-585) | `SAME` (= base cell ``run `curl <HOSTNAME_1>.example.com` now``) | ``run `curl <HOSTNAME_1>` now`` (MEASURED) | Modify `after` from SAME to this literal; base cell stays |
| `ROW_BY_ID["L3"]` card (about 593-601) | `SAME` | ```` ```\nping <HOSTNAME_1>\n```\nthen evil[.]com ```` (MEASURED) | Modify `after` from SAME to this literal |
| tests/warden_port/privacy_corpus.py 36, 37 | (kind only) | `db at <HOSTNAME_1>:5432`, `smb://<HOSTNAME_1>/share` (MEASURED, both functions) | stay green (kind assertions); carved out of I4 into I12b |
| tests/fixtures/p1d_a_base_rows.json `L2/card`, `L3/card` | base record | not changed | contested in round 2 (the JSON records base 2742c1b and is read only for `BS0` cells) |
| tests/test_p1d_a_paths.py property `_PIECES` (`HOST = "db-7.corp.internal"`, about 26) | no host shown | stays green: MEASURED in /tmp/g4v4-a6 with v3's start look-behind it went RED; v4's start (5.2 point 1) masks it | the reason for the start change |
| tests/test_text_parts_together.py about 242 (`db-7.corp`), tests/test_k1b_redaction.py 18 (`db01.corp.local`), tests/test_model_gate.py about 1744 (`db1.corp.example.org` map entry) | masked whole / unchanged | unchanged | stay green: with the pre-final start look-behind these suites, warden_port, p1d rows and paths, fold budget, no-hardcoded and lockin ran 710 passed, 1 failed (the perf test of 5.2 point 1); NOT RE-RUN on the final look-behind (machine load) |

`H27`'s `check_extra` (p1d_cases.py about 641-647) stays true. `assert len(ROWS) == 70` is unchanged.

Gate mutants whose killers move (tests/p1d_a_mutants.py, by name). MEASURED in-process: the G4c patterns installed, the mutant's
replacement applied to the function's source by `exec` (the same text replacement `tools/mutation_runner` makes), and the row
compared with its G4 expected cell:
| mutant | old killer | killed after G4 by | measured |
|---|---|---|---|
| A4 (`_PLACEHOLDER_DOT.sub` removed in `_defang_prose`) | `test_row_H27_card` (no longer kills) | `test_row_D3b_defang` (`mail <EMAIL_1>.org` -> `mail <EMAIL_1>[.]org`) | only D3b fails |
| A5 (`parts = [line]` in `_per_part`) | `test_row_L2_card` (no longer kills) | `test_row_D3c_defang` | only D3c fails |
| A38 (`fix(part) if i % 2 else part`) | `test_row_L2_card` (no longer kills) | `test_row_D3c_defang` (L3, I1, L4, L8, D3b also fail) | D3c fails |
| A6 (`for s, e, ch in []` in `_outside_code`) | `test_row_L3_card` (no longer kills) | **`test_row_L11_slack`** (``` ```\nping a[.]b\n``` ```: the slack re-read undefangs the fence body) | only L11 fails; I1, L4, L3, L8, L2, H27, D3b, D3c pass |

A6's killer is named, so v3's "if neither kills it, STOP" is resolved; Phase 4 runs the four with the runner to confirm. A42 already
uses D3b and is unchanged.

The comment above `_PLACEHOLDER_DOT` (gate.py 239-240) becomes: "# A placeholder (`<EMAIL_1>`, or a host name masked before G4 and
stored) followed by a dot and a name character: what follows the dot would stay linkable. Written `[.]` (P1d-a, D3)." The pattern
itself stays.

## 10. Invariants and the exact test list
Two kinds of test:
- TG tests (tests/test_p1c_gaps.py) use public names only and run on the base (FAIL-BEFORE).
- TB tests use private names reached INSIDE each test (`runmap.<name>`, `redact_mod.<name>`; no module-level import of a G4 name).
  They live in tests/test_b64_scan.py (G4a/G4b) and tests/test_host_names.py (G4c).

Shared values, built from parts:
- `S12 = "Zq9" + "xW4" + "mT7" + "pL2"`;
- `SB = b64("password=" + S12)` = `cGFzc3dvcmQ9WnE5eFc0bVQ3cEwy` (28);
- `B1 = b64("this is just a status message")` (40);
- `B2 = b64("ok status 200")` = `b2sgc3RhdHVzIDIwMA==`;
- `X = "QUJD" + "REVG" + "R0hJ"`.

Every "base" output below was MEASURED on cd8d375's redactor unless marked.

### 10.1 TG (tests/test_p1c_gaps.py, created in Phase 0)
- I1 `test_base64_row[b64-1b-NNN|b64-1c-NN]` (the 52 leak rows): `leak_of(protected, out)` is "no" and `<ENCODED_` is in `out`,
  through `redact_text` and `redact_untrusted`.
- I2 the same id for the 85 unchanged rows: the digest of (output, sorted map) equals the base fixture, through both functions.
- I3 the same id for the 5 kind-change rows: the output is exactly `<ENCODED_1>` and the map has no HIGHENTROPY key.
- I4 `test_must_keep_b64[NN]` (17 `MUST_KEEP_B64`) and `test_must_keep_corpus[masked-NN|kept-NN]` (60 = 48 + 14 - 2, RE-COUNTED on
  the file): digest equal, both functions. 77 ids.
- I9 `test_idempotent[<id>]` over the 229: `redact_text(redact_text(t, m), m)` changes neither text nor map.
- I10 `test_parity`.
- I11 `test_host_must_keep[...]`: 5.3's must-keep list, the 10 v4 rows of 5.3 (`host ec2 failed` ... `host web1 down`), the sweep row
  `host ec2 failed; see ec2.internal, k8s.io, s3://b and x86_64 builds`, and `x.svc.cluster.local`, `x.svc.cluster.local.foo`,
  `eu-west-1.compute.internal`, `jdk.internal.reflect.Method`, `threading.local()`. Each output is equal to the base fixture.
- I12 `test_host_row[host-NN]`: the 19 closed rows show no readable label; the other 25 are digest-equal.
- I18 `test_number_row[num-NN]`.
- I25 `test_inputs_are_the_probe_inputs`: `sha256("\x00".join(inputs))` equals
  `630d55c4c5fb1cbb8d37cff627a73e64063b071decbe3c4bccf0438c87ebe213`. RE-COMPUTED by the drafter on 1e16ab8, from the probe's own
  run order, by recording the 245 inputs of the probe's `run` with `redact_text` and dropping the 16 of 1a. It is the same value as
  v3's.

### 10.2 TB, Phase 2 part (tests/test_b64_scan.py, created in Phase 2; G4b only)
| id | name | input recipe | exact expected |
|---|---|---|---|
| TB-2.1 | `test_encoded_kind_is_a_secret_label_never_stored` | - | `"ENCODED" in redact_mod._LABELS`; `in redact_mod.SECRET_KINDS`; `not in defaults.STORED_KINDS`; `not in runmap._GRAMMAR`; `redact_mod._sweep("<ENCODED_1>", "abcd") is redact_mod._EVERY_COPY` |
| TB-2.2 | `test_encoded_kind_own_output` | `redact_mod.redact("password=<ENCODED_1>")`; `redact_mod.redact("password=‹ENCODED_1›")` | text unchanged, mapping `{}` (both) |
| TB-2.3 | `test_place_encoded_numbering` (I7) | `m={"<ENCODED_5>": "a"*12}`, runs `["b"*12]`; `m={"<ENCODED_5>": "a"*12, "<ENCODED_2>": "c"*12}`, runs `["b"*12]`; `{}`, runs `["a"*12, "b"*12]` | `["<ENCODED_6>"]`; `["<ENCODED_7>"]`; `["<ENCODED_1>", "<ENCODED_2>"]`; each map grows by exactly the new runs |
| TB-2.4 | `test_place_encoded_numbering_is_the_redactor_counter` | the three maps above | the number used == `redact_mod._Redactor(m_before).counters["ENCODED"] + 1` |
| TB-2.5 | `test_place_encoded_identifier_original_gets_a_new_entry` | `m={"<TENANT_1>": X}`, runs `[X]` | `["<ENCODED_1>"]`; `m == {"<TENANT_1>": X, "<ENCODED_1>": X}` |
| TB-2.6 | `test_place_encoded_reuses_an_encoded_original` | `m={"<ENCODED_3>": X}`, runs `[X]` | `["<ENCODED_3>"]`; `len(m) == 1` |
| TB-2.7 | `test_tie_break_same_original_secret_rule_first` (I7b) | `redact_mod.redact("pre"+X+"post and "+X+" alone", mapping={"<TENANT_1>": X, "<ENCODED_1>": X})` | text `pre<ENCODED_1>post and <ENCODED_1> alone` (base with SECRET standing in: `preQUJDREVGR0hJpost and <TENANT_1> alone`) |
| TB-2.8 | `test_tie_break_keeps_the_order_of_different_originals` | `runmap.enforce_map("x ab-cd-ef y", m)` for the 4 maps of 4 point 5 | exactly the 4 measured base outputs (`x ab-<TENANT_1> y`, `x <SECRET_1>-ef y`, `x <TENANT_1>-ef y`, `x ab-<SECRET_1> y`) |
| TB-2.9 | `test_encoded_is_never_restored_or_stored` (I6) | `m={"<ENCODED_1>": SB}` | `runmap.restore_text("x <ENCODED_1>", m) == "x <ENCODED_1>"`; the same with `kinds=frozenset({"ENCODED"})`; `runmap.storable(m) == {}`; `runmap.storable(m, frozenset({"ENCODED"})) == {}` |
| TB-2.10 | `test_assignment_kinds_hold_encoded` | - | `"ENCODED" in channel._ASSIGNMENT_KINDS` |

### 10.3 TB, Phase 3 part (appended to tests/test_b64_scan.py in Phase 3)
| id | name | input recipe | exact expected |
|---|---|---|---|
| TB-3.1 | `test_b64_text_rules` | `_b64_text` of: `b64("status ok here")`; `b64(bytes(range(256)))`; `"QUJD+REVG_R0hJ"`; `"QUJDREVGR0hJS"` (13); `b64("10.20.30.40".encode("utf-16-le"))`; `b64("10.20.30.40".encode("utf-16-be"))` = `ADEAMAAuADIAMAAuADMAMAAuADQAMA==`; `b64(b"\xff\xfe" + "ok".encode("utf-16-le"))`; `b64("unpadded!!")`.rstrip("=") | `"status ok here"`; None; None; None; `"10.20.30.40"`; `"10.20.30.40"`; `"ok"`; `"unpadded!!"` |
| TB-3.2 | `test_b64_units_wrapped_block_table` (N2) | the 8 rows of 3.1 point 3 | exactly the units of that table (`(start, end)` and `written`) |
| TB-3.3 | `test_b64_units_placeholders_are_never_runs` (I19) | `x <HIGHENTROPY_7> y`, `card <CREDITCARD_12> ok`, `<SECRET_REDACTED>`, `‹HIGHENTROPY_7›`, `<GCPRESOURCE_1>`, `<AZURERESOURCE_12>`, `"<SECRET_REDACTED> " * 20_000` | `_b64_units(t)[1] == []`; `redact_text` / `redact_untrusted` output and map equal to the build with `runmap._B64_RUN = re.compile(r"(?!)")` |
| TB-3.4 | `test_no_run_no_extra_work` (I5) | `pw=ab%41 here`, `pw=ab%41 x A`, 100,000 characters of prose, a 48-character HIGHENTROPY blob, the rows of TB-3.3 | `runmap.redact` calls, `time.thread_time` reads (a counting wrapper), text and map equal to the step-off build |
| TB-3.5 | `test_short_blob_alone_is_encoded` | `SB` | `<ENCODED_1>`; map `{"<SECRET_1>": S12, "<ENCODED_1>": SB}` (base: `SB` unchanged) |
| TB-3.6 | `test_decoded_secret_entry_kept_and_a_plain_copy_swept` (L8 v4; review M5) | `SB + " and later " + S12 + " alone"` | `<ENCODED_1> and later <SECRET_1> alone` |
| TB-3.7 | `test_four_levels_one_entry` (I8, I14) | `"x " + b64^4("status ok")` = `x V1hwT1UyRkhVa2xXYm5CS1VucHNlUT09` | `x <ENCODED_1>`; exactly one new map entry (base: unchanged) |
| TB-3.8 | `test_three_levels_read` | `b64^3("pwd=Zq9xW4m")` = `WTBoa2ExQldjSGhQV0doWVRrY3dQUT09` | `<ENCODED_1>`; `leak_of("Zq9xW4m", out) == ("no", ...)` (base: unchanged) |
| TB-3.9 | `test_utf16_be_short` | `ADEAMAAuADIAMAAuADMAMAAuADQAMA==` | `<ENCODED_1>`; no IPV4 key (IPV4 is a stored kind) |
| TB-3.10 | `test_too_deep_inside_a_decoded_view_is_masked_unread` (L4) | `b64("%" + "25"*9 + "41")` = `JTI1MjUyNTI1MjUyNTI1MjUyNTQx` | `<ENCODED_1>`; no `TooDeep` raised (base: unchanged) |
| TB-3.11 | `test_tenant_held_blob_becomes_encoded` (L12) | `org_id=cHdkPUtwN3JUcTJX` (base64 of `pwd=Kp7rTq2W`) | `org_id=<ENCODED_1>`; no TENANT key (base: `org_id=<TENANT_1>`) |
| TB-3.12 | `test_blob_after_an_ansi_escape` | `"\x1b[1m" + SB + "\x1b[0m"` | `<ENCODED_1>` |
| TB-3.13 | `test_percent_padding` | `"data=" + b64("password=Zq9xW4mT7pL")[:-1] + "%3D"` = `data=cGFzc3dvcmQ9WnE5eFc0bVQ3cEw%3D` | `data=<ENCODED_1>%3D` (base: unchanged) |
| TB-3.14 | `test_json_escaped_slashes` | `json.dumps({"data": b})` with `/` written `\/`, where `b` = the first base64 of `"pwd=" + 8 made-up characters` that holds a `/` (built in the test) | `{"data": "<ENCODED_1>"}` |
| TB-3.15 | `test_known_value_seen_in_base64` | map `{"<SECRET_1>": S12}`, text `"x " + b64("note " + S12)` | `x <ENCODED_1>` |
| TB-3.16 | `test_caps_fail_closed` (I13) | (a) `B64_MAX_UNITS` patched to 3, 4 distinct short blobs; (b) `B64_MAX_DECODED_CHARS` patched to 10, `SB`; (c) `_b64_hits` with `_ScanBudget(started=-1e9)` | each raises `InputTooLarge`; the caller's map is unchanged; (c) before any `_b64_text` call (spy count 0) |
| TB-3.17 | `test_separator_fallback` (I15) | `_b64_hits` with three units decoding to `secret="`, `plain words here`, `x` | all three hits (measured: the quoted-value patterns cross the separator) |
| TB-3.18 | `test_separator_survives_every_neutralise` | pieces `["status ok", "hello world", "x"]` joined by `_B64_SEP`, through `channel._neutralise`, `runmap.neutralise_untrusted`, None | 3 pieces each time |
| TB-3.19 | `test_settle_chain_beside_a_blob` (I20 a, a', N3) | `CONSTRUCTED[0] + sep + SB` for sep in `" "`, `","`, `"\n"` | `redact_text(CONSTRUCTED[0], RunMap()) + sep + "<ENCODED_1>"`; no `NotSettled` (measured with a JWT stand-in: the same 3 rounds) |
| TB-3.20 | `test_wrapped_chain_settles_inside_the_view` (I20 b) | `wrap(b64(CONSTRUCTED[0]), 64)` | `<ENCODED_1>` |
| TB-3.21 | `test_fold_scan_runs_in_both_passes` (I20 c, d) | `"café " + SB`; `"Ꭺlice@example.com " + SB` | `café <ENCODED_1>`; `[line withheld: look-alike text hid a protected value] <EMAIL_1>` (base for the second: the same, measured) |
| TB-3.22 | `test_errors_of_the_second_pass_propagate` (I21) | a wrapper on `runmap.redact` raising `RedactionError("NotSettled")`, then `InputTooLarge("InputTooLarge")`, on call 2; text `SB` | `pytest.raises(RedactionError)` with `str(err.value) == "NotSettled"` (and an `InputTooLarge`); the caller's `RunMap` is equal to before |
| TB-3.23 | `test_views_are_of_the_input` (I22) | `redact_untrusted(SB + " password%3D" + S12)` | holds `<ENCODED_1>` and a `<SECRET_` and no `‹ENCODED` |
| TB-3.24 | `test_card_two_benign_runs_and_one_secret` (review B2) | `channel.clean(f"note {B1} then {B2} and {SB} end")` | exactly `f"note {B1} then {B2} and <ENCODED_1> end"` (base: the input unchanged, measured) |
| TB-3.25 | `test_card_cap_refusal_is_a_raise` (review M4) | `B64_MAX_UNITS` patched to 1; `channel.clean(f"a {B1} b {B2}")`; `cards.render_abstain("r", "x", [f"{B1} {B2}"])` | both raise `InputTooLarge` (no `SETTLE_NOTE`) |
| TB-3.26 | `test_card_tag_split_blob` (I24) | `channel.clean("<b>" + SB[:14] + "</b>" + SB[14:])` | neither half of `SB` is in the output |
| TB-3.27 | `test_encoded_through_enforce_map_and_snapshot` (review B8) | `W = wrap(b64("2026-11-20 deploy db_password=" + S12 + " applied"), 32)`, `m = RunMap({"<ENCODED_1>": W})`; `t = "x " + W + " y"` | `enforce_map(t, m) == "x <ENCODED_1> y"`; `held_value_left("x <ENCODED_1> y", snapshot(m)) is False`; `held_value_left(t, snapshot(m)) is True` |
| TB-3.28 | `test_map_ceiling` (I23) | `k5_cfg(tmp_path, config={"evidence": {"max_map_entries": 40}})`, a document of 15 (then 25) distinct `b64("password=" + rand12)` | 15: not stopped, the map holds 30 entries (ENCODED + SECRET each); 25: `NEEDS_PERSON` / `document_too_complex` |
| TB-3.29 | `test_held_wrapped_original_is_not_decoded_again` | `t = W` (TB-3.27), `m = RunMap()`, `redact_text(t, m)` twice | the second call makes zero `_b64_text` calls (spy); same output |
| TB-3.30 | `test_perf_step_overhead` (I16, `@pytest.mark.perf`) | 13.4 | 13.4 |
| xfail strict | `test_limit_glued_prefix` (L-B1), `test_limit_split_fields` (L-B4), `test_limit_log_prefixed_lines` (L-B5), `test_limit_base32_hex` (L-B2), `test_limit_capital_blob_in_angle_brackets` (L-B6) | `"/v1/blob/" + SB`; `{"a": SB[:14], "b": SB[14:]}`; each wrapped line prefixed `"2026-11-20 INFO "`; `base64.b32encode(b"password=" + S12.encode())`; `"<" + b64-of-capitals + ">"` | each asserts `leak_of(S12, out)[0] == "no"`, which FAILS today and after G4, so a strict xfail; an XPASS means the limit closed (report it) |

### 10.4 TB, Phase 4 part (tests/test_host_names.py, created in Phase 4)
| id | name | input recipe | exact expected |
|---|---|---|---|
| TB-4.1 | `test_host_key_masks_db01` | the rows 33-36 of 5.3, plus `host web-1 down` | the 5.3 outputs; `host <HOSTNAME_1> down` |
| TB-4.2 | `test_host_key_keeps_tech_words` (review M2, N4) | the 10 v4-kept rows of 5.3 and `host s3 bucket` | each unchanged |
| TB-4.3 | `test_host_key_sweep_side_effect` | `host ec2 failed; see ec2.internal, k8s.io, s3://b and x86_64 builds`; `host db01 down; tail db01.log` | unchanged; `host <HOSTNAME_1> down; tail <HOSTNAME_1>.log` |
| TB-4.4 | `test_host_key_two_digit_words_are_masked` (stated) | `host py311 image`, `host sha256 sum` | `host <HOSTNAME_1> image`, `host <HOSTNAME_1> sum` |
| TB-4.5 | `test_host_suffix_hyphen_rest` (review M3) | the 5 rows of 5.2 point 5 | each `<HOSTNAME_1>` |
| TB-4.6 | `test_host_start_after_a_bracket_or_a_lone_dot` | `(x<HOSTNAME_1>&.]db-7.corp.internalx`, `x/.db01.corp.example`, `..db01.corp` (with `RunMap({"<HOSTNAME_1>": "\0seed"})` for the first) | `db-7` not in the output; `x/.<HOSTNAME_1>`; `..<HOSTNAME_1>` |
| TB-4.7 | `test_host_whole_names` | `db01.corp.example`, `db01.corp.example.`, `com.acme.corp.billing.Service`, `db_01.corp.example`, `db01[.]corp[.]example`, `x[.]svc[.]cluster[.]local`, `db01.corp.example.com_x` | `<HOSTNAME_1>`, `<HOSTNAME_1>.`, and `<HOSTNAME_1>` for each of the other five |
| TB-4.8 | `test_host_kept_names` | the 6 rows of 5.2 point 6 | each unchanged |
| TB-4.9 | `test_host_privacy_rows_new_strings` (I12b) | privacy_corpus.py rows 36, 37 | `db at <HOSTNAME_1>:5432`, `smb://<HOSTNAME_1>/share` (both functions) |
| TB-4.10 | `test_host_patterns_are_linear` (`@pytest.mark.perf`) | each of `"a[.]"*12500`, `"a.-_"*12500`, `"a-"*25000+".corp"`, `"a."*25000`, `"ab-cd."*8000` | each HOSTNAME pattern's `findall` under 0.05 s |
| xfail strict | `test_limit_host_single_trailing_digit` (L-H4), `test_limit_java_package` (L-H1, asserts `.billing.Service` readable: FAILS after G4 because it is masked, so this row is a stated over-mask, not an xfail; written as a plain assert of `<HOSTNAME_1>`) | `host web1 down` | asserts `"web1" not in out`; xfail strict |

## 11. Files
Create:
- `tests/p1c_cases.py` (Phase 0). It reconciles with G7 r4's tests/p1c_builders.py (review B8).
  - It IMPORTS `RNG`, `SEED`, `reseed`, `rand`, `gap1_values`, `gap2_cases`, `gap3_cases` and `luhn_number` from tests/p1c_builders.py,
    which are not copied again.
  - It copies from evidence/p1c_probe.py only what tests/p1c_builders.py does not hold: `b64`, `ENCODINGS`, `wrap`, `no_digit_line`,
    the 1c case list, `lcs`, `_decodings`, `readable`, `leak_of`, the probe's `B64_RUN` and `PLACEHOLDER`. These draw from
    `p1c_builders.RNG`, the probe's stream.
  - `build() -> Cases` (`functools.cache`) calls `reseed()` and consumes the stream in the probe's order: gap1 values, the 1b rows, the
    1c rows (both `no_digit_line` searches), gap2, gap3.
  - `Cases` holds `values` (8 dicts), `b64` (142 (id, protected, text)), `hosts` (44), `numbers` (43) and `plain` (16).
  - It also holds `MUST_KEEP_B64` (the 17 rows of v3, unchanged) and `HOST_MUST_KEEP` (5.3 and I11).
  - Docstring rule: `build()` moves `p1c_builders.RNG`, so a caller of the gap builders calls `reseed()` first (the property test
    does, about line 101). It is not imported from handover/.
  - NOT RE-MEASURED: v3's "1.6 s of CPU for `build()`"; the whole probe, redaction included, took 2.2 s CPU on 1e16ab8.
- `tests/test_p1c_gaps.py` (Phase 0): 10.1, public names only.
- `tests/fixtures/p1c_base_digests.json` and `tests/fixtures/make_p1c_base_digests.py` (Phase 0; as v3: digests of
  `json.dumps([out, sorted(mapping.items())], ensure_ascii=True)`, no value written).
- `tests/test_b64_scan.py` (Phase 2, extended in Phase 3): 10.2, 10.3.
- `tests/test_host_names.py` (Phase 4): 10.4.
- `tests/b64_mutants.py` (Phase 3; host mutants added in Phase 4): 13.3.

Modify:
- `src/hadavin_sdk/guard/runmap.py`:
  - add `_ScanBudget`, `_B64Unit`, `_B64_RUN`, `_B64_TOKEN_SKIP`, `_B64_SEP`, `_b64_units`, `_b64_text`, `_b64_held`, `_b64_hits`,
    `_b64_place`, `_pass_one`, `_scan`;
  - change `redact_text` (2.3), with the docstring paragraph of v3, its last sentence reading "...past either, `InputTooLarge`; the
    decoded texts are scanned joined by a line holding `;`, and a decoded value of a kind that is never stored stays in the run's map
    (its plain copies are masked)";
  - import `place_encoded` and `strip_ansi` from redact.
- `src/hadavin_sdk/guard/redact.py`:
  - `_LABELS`, `SECRET_KINDS`, `place_encoded`, the `_build` rules loop (4 point 5; the sort key is unchanged);
  - `_HOST_LABEL`, `_HOST_DOT`, `_HOST_BARE`, `_HOST_TAIL`, `_HOST_ARCH`, the HOSTNAME pattern and its comment, the HOSTKEY entry;
  - the module docstring (6 and one sentence). Examples go in `#` comments only (test_no_hardcoded_values, test_lockin_guard).
- `src/hadavin_sdk/defaults.py`: section 7.
- `src/hadavin_sdk/approvals/channel.py`: `_ASSIGNMENT_KINDS`.
- `src/hadavin_sdk/approvals/gate.py`: the comment of 9.3 only.
- `tests/fixtures/p1d_cases.py`: the `after` cells of H27, L2 and L3.
- `tests/p1d_a_mutants.py`: the killers of A4, A5, A38 and A6 (9.3 table).
- `tests/redact_mutants.py`:
  - R3's `old` AND `new` re-indented (review N2): `old = "            time.thread_time() - started > defaults.REDACT_BUDGET_S\n        ):  # a hostile text"`,
    `new = "            False\n        ):  # a hostile text"`. MEASURED: `ruff format` on this repository's settings (line-length 100)
    writes a loop at the top level of a function as `if (` / 12 spaces + condition / 8 spaces + `):  # a hostile text: ...`.
  - Mutant 21's docstring sentence (line 5) becomes "removes both `_deadline=started + defaults.REDACT_BUDGET_S` arguments of
    `runmap._pass_one` (pass one and the pass on the replaced text, used for the input and every view)".
- `tests/test_redact_idempotent_property.py`:
  - keep G7 r4's groups `p1c-gap1/2/3` exactly as they are (they are pinned by `test_the_moved_builders_give_the_rows_of_the_evidence_probe`);
  - add the group `p1c-b64` (142 texts of `p1c_cases.build().b64`) after `p1c-gap3`;
  - `EXPECTED_INPUTS = 1977` (1835 + 142) and `P1C_B64 = 142` beside `P1C_GAP2`/`P1C_GAP3`, plus `assert counts["p1c-b64"] == P1C_B64`.
  - v3's "replace `_p1c_module()`/`_P1C`" and the "FileNotFoundError guard" are withdrawn: G7 r4 already removed the loader. `_P1C`
    is now read only by the skip-if parity test.
- `CHANGELOG.md` and `SECURITY.md`: the text of the "For SECURITY wording" section.

Must stay green UNCHANGED (run, do not edit; a red one is a finding: report it):
- tests/warden_port (test_redaction.py OWN_SHAPES and `test_a_high_entropy_value_after_any_key_is_masked`, test_redaction_classes.py,
  test_redaction_bank.py, test_redaction_review*.py, **test_providers.py**)
- tests/test_redact_context_after_sweep.py, test_redact_own_output.py, test_redact_own_output_hardening.py, test_redact_settle_loop.py
- tests/test_redact_fold.py, test_redact_fold_budget.py (:78 counts `len(PATTERNS)`, which HOSTKEY grows by one; the CountedClock
  tests), test_redact_fold_seams.py, test_redact_fold_property.py, test_redact_marks.py, test_redact_g3_port.py
- tests/test_k5_round12_fuzz.py, test_k5_round8.py, test_k5_round9.py, test_k5_round9b.py, test_k5_round10.py, **test_k5_round6.py,
  test_k5_round7.py, test_k5_round11.py** (neutralise-hook count about 74)
- tests/test_k5_fixes5.py, test_k5_fixes7.py, test_k5_fixes9.py, **test_k5_fixes1.py, test_k5_fixes2.py, test_k5_fixes3.py**
- tests/test_k5_layers.py, test_k5_round5.py, test_k5_classes.py, test_k5_producers.py, test_k5_perf.py (`-m perf`),
  **test_k5_tools.py** (`broken`/`flaky` patch `runmap.redact`), **test_k5_review.py**
- **tests/test_textnorm_order137.py, test_textnorm_meta.py, test_textnorm_fixbatch.py, test_textnorm_siblings.py**
- tests/test_runmap_enforce_map.py, test_runmap_map_write.py, test_k1b_redaction.py, test_k1b_redaction_layers.py
- tests/test_text_parts_together.py, test_model_gate.py, test_p1d_a_paths.py, **test_p1d_link_oracle.py**, test_p1d_a_rows.py
  (after its fixture edit)
- **tests/test_p7_store.py, test_p7_tick.py**
- tests/test_no_hardcoded_values.py, test_lockin_guard.py, test_gate_mutants_picked_up.py, and the mutant runs of 13.3.

Bold = added in v4. Delete: nothing. Migration: none.

## 12. Build order (each phase ends green with its own selection; one commit per phase on the builder's branch)
Prefix: `uv run --all-extras --group test`. "Green" = the listed command passes, with exactly the listed ids failing. CI runs
`pytest -q -n 3 -m "not live and not perf"` (.github/workflows/ci.yml 98); here `-m "not perf"` is written wherever `-n` is used,
and perf runs separately with `-p no:xdist`. `-k` is never used across several files (review B3).

Phase 0 (no src code):
- (a) Base sha; 0.2 rule; `git worktree add --detach /tmp/g4-base <base-sha>`.
- (b) Run evidence/p1c_probe.py in /tmp/g4-base. Its totals and row lists must equal 1, 6, 9.1 and 9.2.
  - On a difference, UPDATE this ticket's tables and the 76-id list from the new run, record both in the evidence, and go on. This is
    a moved base, not a defect.
  - STOP only if a host or base64 row that G4 closes now leaks in a NEW way (a new kind of leak, not a count).
- (c) Write tests/p1c_cases.py; `build()`'s sha256 must equal I25's literal. If it differs: STOP (the copy is wrong, not the base).
- (d) Write and run make_p1c_base_digests.py in /tmp/g4-base; keep the JSON.
- (e) Write tests/test_p1c_gaps.py; FAIL-BEFORE (13.1).
- (f) Change tests/test_redact_idempotent_property.py (the `p1c-b64` group) and run it in /tmp/g4-base: 1,977 inputs, 0 refused,
  0 fail. Red: STOP (a property of the base, not G4's). NOT RE-MEASURED by the drafter (machine load).
- (g) Record at the base: `python tests/redact_mutants.py`, `python tests/gate_mutants.py`, `python tests/stage_mutants.py`,
  `python tests/p1d_a_mutants.py`, `python tests/textnorm_mutants.py runmap`, each verdict per mutant. At cd8d375, redact_mutants
  `N15 the alias build asks for no budget` is `ERROR SNIPPET NOT FOUND`: its `old` text is in no file (`_build` now reads a local
  `deadline`; found by the drafter's snippet count, section C). Later phases compare with this record. N15 is reported to the G7
  owner, not fixed in G4 (L18).
- (h) The full suite at the base: `pytest -q -n 2 -m "not live and not perf"`, recorded.

Commit: the four new test files plus the property-test change. On the builder branch, tests/test_p1c_gaps.py now has the 76 red ids
of 13.1. No phase before 3 runs it.

Phase 1, defaults.py (SPINE commit): the 8 constants and the 2 comment clauses.
- `pytest tests/test_no_hardcoded_values.py tests/test_k5_review.py tests/test_lockin_guard.py -q`
- Expected red: none.

Phase 2, G4b (redact.py `_LABELS`, `SECRET_KINDS`, `place_encoded`, the `_build` rules loop; channel.py `_ASSIGNMENT_KINDS`). Create
tests/test_b64_scan.py with TB-2.1 .. TB-2.10.
1. `pytest tests/test_b64_scan.py -q`. Expected red: none.
2. `pytest tests/test_runmap_enforce_map.py tests/test_redact_own_output.py tests/test_redact_own_output_hardening.py tests/test_k5_classes.py tests/test_redact_settle_loop.py tests/test_redact_idempotent_property.py tests/test_runmap_map_write.py tests/warden_port tests/test_k5_tools.py tests/test_k5_round11.py tests/test_textnorm_order137.py tests/test_textnorm_meta.py tests/test_textnorm_fixbatch.py tests/test_textnorm_siblings.py tests/test_p7_store.py tests/test_p7_tick.py tests/test_model_gate.py -q -n 2 -m "not perf"`.
   Expected red: none.
3. `python tests/redact_mutants.py`, `python tests/gate_mutants.py`, `python tests/stage_mutants.py`. Expected: the Phase 0 (g)
   verdict for every mutant.

Phase 3, G4a (runmap.py refactor and step; R3 and mutant 21 text in redact_mutants.py; tests/b64_mutants.py). Append TB-3.1 ..
TB-3.30 and the five strict xfails to tests/test_b64_scan.py.
1. `pytest tests/test_b64_scan.py tests/test_p1c_gaps.py -q -n 2 -m "not perf"`. Expected red: EXACTLY the 19 ids
   `test_host_row[host-01]`, `[host-02]`, `[host-17]`, `[host-19]`, `[host-21]`, `[host-24]`, `[host-26]`, `[host-29]`, `[host-32]`,
   `[host-33]`, `[host-34]`, `[host-35]`, `[host-36]`, `[host-37]`, `[host-38]`, `[host-39]`, `[host-40]`, `[host-43]`, `[host-44]`.
   The 57 base64 ids of 13.1 are green now.
2. `pytest tests/test_redact_fold_budget.py tests/test_redact_fold.py tests/test_redact_fold_seams.py tests/test_redact_marks.py tests/test_redact_idempotent_property.py tests/test_redact_settle_loop.py tests/test_redact_context_after_sweep.py tests/test_runmap_map_write.py tests/test_runmap_enforce_map.py tests/test_k5_fixes1.py tests/test_k5_fixes2.py tests/test_k5_fixes3.py tests/test_k5_fixes5.py tests/test_k5_layers.py tests/test_k5_round6.py tests/test_k5_round7.py tests/test_k5_round8.py tests/test_k5_round9.py tests/test_k5_round9b.py tests/test_k5_round10.py tests/test_k5_round11.py tests/test_k5_tools.py tests/test_k1b_redaction.py tests/test_k1b_redaction_layers.py tests/test_k5_producers.py tests/test_text_parts_together.py tests/test_gate_mutants_picked_up.py tests/test_textnorm_order137.py tests/test_textnorm_meta.py tests/test_textnorm_fixbatch.py tests/test_textnorm_siblings.py tests/test_p7_store.py tests/test_p7_tick.py tests/warden_port -q -n 2 -m "not perf"`.
   Expected red: none.
3. `pytest tests/test_b64_scan.py -m perf -p no:xdist -q` (I16).
4. `python tests/redact_mutants.py` (63 mutants: `len(M)` by import; the 64th `m(` line the review counted is `def m(` at line 50),
   `python tests/b64_mutants.py`, `python tests/textnorm_mutants.py runmap`, `python tests/gate_mutants.py`, and the snippet script
   of 13.3. Expected: the Phase 0 (g) verdicts, every b64 mutant KILLED, snippet counts equal.

Phase 4, G4c (the host patterns, p1d_cases.py, p1d_a_mutants.py, gate.py comment; tests/test_host_names.py; host mutants in
b64_mutants.py).
1. `pytest tests/test_host_names.py tests/test_p1c_gaps.py tests/test_b64_scan.py -q -n 2 -m "not perf"`. Expected red: none.
2. `pytest tests/warden_port tests/test_p1d_a_rows.py tests/test_p1d_a_paths.py tests/test_p1d_link_oracle.py tests/test_text_parts_together.py tests/test_model_gate.py tests/test_k1b_redaction.py tests/test_no_hardcoded_values.py tests/test_lockin_guard.py tests/test_redact_fold_budget.py tests/test_k5_tools.py tests/test_p7_store.py tests/test_p7_tick.py -q -n 2 -m "not perf"`.
   Expected red: none.
3. `pytest tests/test_k5_perf.py tests/test_p1d_a_paths.py tests/test_host_names.py -m perf -p no:xdist -q`. Expected red: none.
   `test_secret_patterns_are_linear_on_a_50000_character_run` is the guard of 5.2 point 1.
4. `python tests/p1d_a_mutants.py` (every mutant good; A4, A5, A38 and A6 killed by the 9.3 killers), `python tests/b64_mutants.py host`,
   and the `B64_PRINTABLE_SHARE` sweep 0.85-0.95 (no probe or must-keep row changes verdict).

Phase 5, G4d and documents (the redact.py docstring paragraph, CHANGELOG.md, SECURITY.md).
- `pytest -q -n 2 -m "not live and not perf"` (full), `pytest -m perf -p no:xdist -q`, `pytest tests/test_k5_review.py -q`, ruff
  and bandit (13.5), the probe on the G4 head.
- Green: all. The probe shows 0 base64 leaks, 7 host rows readable (6, 8, 9, 10, 15, 16, 42), and numbers 24 / 2 / 17.

## 13. Tests and evidence
### 13.1 FAIL-BEFORE
`cp tests/p1c_cases.py tests/test_p1c_gaps.py /tmp/g4-base/tests/ && cp tests/fixtures/p1c_base_digests.json /tmp/g4-base/tests/fixtures/ && cd /tmp/g4-base && uv run --all-extras --group test pytest tests/test_p1c_gaps.py -q`

tests/p1c_cases.py imports tests/p1c_builders.py, which is in the base.

Expected: exactly these 76 failures. Every other id passes (I4, I9, I10, I11, I18, I25 included).
- 48 1b leaks: `test_base64_row[b64-1b-001]` .. `[b64-1b-005]`, `[b64-1b-007]`, `[b64-1b-008]`, `[b64-1b-033]` .. `[b64-1b-037]`,
  `[b64-1b-039]`, `[b64-1b-040]`, `[b64-1b-049]` .. `[b64-1b-053]`, `[b64-1b-056]`, `[b64-1b-065]` .. `[b64-1b-072]`,
  `[b64-1b-081]` .. `[b64-1b-088]`, `[b64-1b-097]` .. `[b64-1b-101]`, `[b64-1b-104]`, `[b64-1b-113]` .. `[b64-1b-117]`, `[b64-1b-120]`;
- 9 1c rows (4 leaks + 5 kind changes): `test_base64_row[b64-1c-01]`, `[02]`, `[03]`, `[05]`, `[06]`, `[07]`, `[09]`, `[10]`, `[11]`;
- 19 host rows: the ids of Phase 3 step 1.

Derived from the re-measured row lists; the test itself is not written yet. `git worktree remove /tmp/g4-base` afterwards.

### 13.2 Parity
I25 is a literal in the test. Phase 0 (c) proves that the probe and the copy build the same inputs.

### 13.3 Mutants
Pins that already exist: every `old` text of tests/redact_mutants.py, p1d_a_mutants.py, gate_mutants.py, stage_mutants.py and
textnorm_mutants.py whose file is guard/runmap.py or guard/redact.py occurs after G4 as many times as at the base.

The one exception is R3, whose `old` and `new` are re-indented as in section 11.

MEASURED at cd8d375 by the drafter's snippet script: 113 such mutants (redact_mutants 55 redact.py + 7 runmap.py, p1d_a_mutants
18 + 1, gate_mutants 24, stage_mutants 3, textnorm_mutants 5). Every `old` occurs exactly once, except:
- mutant 21 (twice, as intended);
- N15 (zero: stale at the base, L18).

The script imports each list and prints name, file, and the count at the base and at the head; its output goes in the evidence.

Literals G4 must keep at their counts:
- `_deadline=started + defaults.REDACT_BUDGET_S` (twice, both in `_pass_one`);
- `started = time.thread_time()` (once);
- R2's line (once, in `_scan`);
- `for view in views:` (once);
- `    mapping.update(current)\n    return out\n` (once);
- `raise RedactionError("NotSettled")` in runmap.py (once, in `enforce_map`).

New mutants in tests/b64_mutants.py, each to be KILLED, the raw result in the evidence. These are the v3 list, with three changed
rows and two new ones:
| mutant | killed by |
|---|---|
| skip the printable rule | TB-3.1 (`bytes(range(256))`); I4 binary row |
| accept a mixed alphabet run | TB-3.1 |
| drop the `len % 4 == 1` rule | TB-3.1 (13 characters) |
| drop the UTF-16 rules | TB-3.1; 1b rows 70, 86 (I1) |
| drop the depth limit | TB-3.7 (I14) |
| drop the unit cap / the decoded-character cap / the clock check per unit | TB-3.16 a / b / c |
| clock read before the gate | TB-3.4 |
| no placeholder blanking | TB-3.3 |
| no ANSI strip | TB-3.12 |
| no dedupe of identical units | TB-3.16 variant: 4 copies of one blob, unit cap patched to 1, no raise |
| held by any kind | TB-3.11 |
| no whole-unit held test | TB-3.29 |
| `TooDeep` in a decoded view propagates | TB-3.10 |
| no size pre-check of the decoded join | TB-3.16 variant with `MAX_REDACT_CHARS` patched small |
| views of T2 instead of T | TB-3.23 |
| ENCODED outside `SECRET_KINDS` | TB-2.1 |
| ENCODED in `STORED_KINDS` or given a grammar | TB-2.9 |
| `place_encoded` own counter rule | TB-2.3, TB-2.4 |
| `place_encoded` splits pieces; original = decoded text | TB-3.7 (one entry), TB-3.27 |
| tie-break removed / tie-break as v3's sort key | TB-2.7 / TB-2.8 (CHANGED) |
| skip neutralise on the decoded text | TB `redact_untrusted` of b64 of `password=<FOO_1>` is ENCODED (TB-3.23 file) |
| skip `_views` on the decoded text | TB-3.13 variant: b64 of `password%3D` + S12 is ENCODED |
| no held rule | I2 (80 HIGHENTROPY rows), I4 JWT rows |
| mask only the found span inside the decoded text | I1 |
| drop the wrapped-line join / join any window of lines | 1c rows 1, 2, 5, 9; TB-3.2 |
| no separator fallback | TB-3.17 |
| **separator `\n\x1e\n` (v3's)** | TB-3.24 (NEW: two benign runs would become `<ENCODED_n>`) |
| **kept entries of stored kinds too (L8 v3 fallback)** | TB-3.9 (no IPV4 key) (NEW) |
| no kept entries (L8 v3 default) | TB-3.6 (CHANGED) |
| first pass's map kept | I3; TB-3.28 |
| ENCODED not in `_ASSIGNMENT_KINDS` | TB-3.26 |
| host: drop the tail / `_` not a label character / drop `[.]` | rows 1, 2, 17 / row 32 / row 43 |
| host: drop the `.internal`/`.local` guard; unkeep `.cluster.local` | TB-4.8 |
| host: v3 start look-behind / plain ASCII look-behind | TB-4.6 / TB-4.10 (NEW) |
| host: suffix `(?![\w-])` without the hyphen rest (v3) | TB-4.5 (NEW) |
| host: Unicode label class | tests/test_text_parts_together.py cyrillic cards (by reading; else a TB look-alike row) |
| host-key: v3 value rule (any digit) / no `_HOST_ARCH` / `server` key back / dotted values | TB-4.2 (`host ec2 failed`) / TB-4.2 (`host x86_64`) / `Server: AmazonS3` / `Host: api.github.com` |

### 13.4 Perf mechanism (I16; unchanged mechanism, re-based numbers)
- In tests/test_b64_scan.py, marked `@pytest.mark.perf` and run serially. Clock and repetition: `tests/fixtures/timing.block_seconds`,
  best of `timing.REPEATS`.
- Baseline: the SAME build with `runmap._B64_RUN = re.compile(r"(?!)")`, measured interleaved.
- `PLAIN_RATIO = 1.15`, `PROSE_RATIO = 1.10`, `PLANTED_RATIO = 1.15`, `FLOOR_S = 0.005`, and `CAP_CEILING_S = defaults.REDACT_BUDGET_S`
  for `B64_MAX_UNITS` distinct base64 secrets.
- The section 8 table is the reference recorded in the evidence.

### 13.5 Evidence commands (raw output to evidence/G4-1.md)
- ruff check and `ruff format --check` on the changed files;
- each phase's selection;
- the mutant runs and the snippet script;
- `uv run --group scan bandit -q -r src/hadavin_sdk/guard -ll`;
- the probe on the G4 head;
- the printable-share sweep.

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
| L8 | decoded finds (CHANGED again, review M5) | the ENCODED entries of the hit units, plus the decoded view's new entries of kinds NOT in `defaults.STORED_KINDS` (secret and regulated kinds; never stored, so nothing new is stored at rest); a bare plain copy of a decoded secret is masked (TB-3.6); inner ENCODED and identifier finds are thrown away | (a) v3's default: only ENCODED entries kept; then the residual "a bare plain copy elsewhere stays unmasked" is stated in SECURITY and pinned by a strict xfail (TB-3.6 as xfail); (b) every decoded entry kept (EMAIL/HOSTNAME/IPV4 then stored at rest) |
| L9 | unit cap | `B64_MAX_UNITS` = `MAX_MAP_ENTRIES`, refusal past it | 4,096, refusal past it |
| L10 | `_ASSIGNMENT_KINDS` | gains ENCODED | unchanged: a tag-split blob stays readable on a card |
| L11 | host label class | ASCII | Unicode `\w` |
| L12 | which pass-1 kinds hold a run | SECRET kinds and JWT/PRIVKEY substrings | any kind |
| L13 (new) | host-key value | starts with a letter, ends in two digits or `-digit`, not a CPU architecture name (`_HOST_ARCH`); `web1` is a limit (L-H4), `py311`/`sha256` are masked and their later copies swept (stated) | v3's rule (any digit): `ec2`, `k8s`, `x86`, `http2`, `eth0`, `x86_64`, `Web2` masked and their later standalone copies swept (`<HOSTNAME_1>.internal` etc.), stated in SECURITY |
| L14 (new) | a private suffix followed by `-rest` (`db01.corp-prod`, `x.local-dev`, `x.internal-api`) | masked whole, the hyphen rest and (for `.internal`/`.local`) the following labels inside the match | v3's `(?![\w-])`: not masked at all, stated |
| L15 (new) | how the decoded texts are scanned | one joined scan with the separator `"\n\n;\n\n"`, every unit a hit when a separator is lost | one `_scan` per decoded text (no separator; measured 6.4 s per 300 hitting pieces against a 1,000-entry map: big texts would be refused at the deadline) |
| L16 (new) | `_build` tie-break | for the same original only (rules loop) | v3's sort key `(-len, kind not in SECRET_KINDS)`: also reorders different equal-length originals; the `enforce_map` docstring sentence is then changed |
| L17 (new) | a card whose text passes a base64 cap | refused as today for any over-cap text: no card posted, the event recorded undelivered (8) | `cards._card` catches `RedactionError` and shows a fixed text (a change to approvals/cards.py) |
| L18 (new) | redact_mutants N15's stale `old` text (found by the drafter) | reported to the G7 owner; G4 compares with the base verdict | G4 re-points N15 to `            if deadline is not None:\n                self._over_budget(deadline)\n` (`_build`) and runs it |

## 15. Security notes, what stays out, rollback, reviewers, done
- No secret value is logged or put in an exception.
- The decoded text never leaves the redactor. Only `<ENCODED_n>` is written. Its original lives in the run map in memory, is never
  stored (TB-2.9), and is swept in every copy.
- Under L8 v4, decoded values of kinds that are never stored stay in the map (memory only); decoded identifiers do not.
- Stays out: `redact()` / `redact_many` called directly; offsets other than 0; base32, hex, gzip; blobs glued to a prefix, split
  across fields or log prefixes; `tools.py` and `k1b/redaction.py`; HIGHENTROPY in `_ASSIGNMENT_KINDS`; a refused card (L17).
- Rollback: tag `pre-G4` on the base commit. No migration.
- Reviewers: one correctness and one adversarial reviewer, fresh, given the diff, this ticket and evidence/G4-1.md only.
- Done:
  - every phase green;
  - FAIL-BEFORE recorded (76 ids);
  - every mutant of 13.3 good (against the Phase 0 (g) record);
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
  - Not found: a blob glued to other base64 characters, split across fields or across lines with a prefix; an all-capital blob
    written between `<` and `>`; base32; hex.
  - A text with more than 2,000 distinct decodable base64 values is refused; a card with such a text is not posted.
- Host names.
  - A private host name (under `.corp`, `.lan`, `.intranet`, `.intra`, `.localdomain`, `home.arpa`, or ending in `.internal` /
    `.local`, also with a hyphenated rest such as `.corp-prod`) is masked whole.
  - A single host label after `host`/`hostname` that ends in two digits or in a hyphen and a digit is masked, and so is every later
    standalone copy of it in the run. That includes a non-host word of that shape (`py311`); CPU architecture names are not masked.
  - A label with one trailing digit (`web1`) is not masked.
  - A dotted name with no private suffix is not masked.
  - `.svc` short names, `.cluster.local` and AWS's own names are kept on purpose.

CHANGELOG.md, Unreleased, Upgrade steps: "**Redaction: base64 and host names (G4).** A value hidden in base64 is now masked as
`<ENCODED_n>` (a new kind, never stored or restored), and a secret found inside it is masked in its plain copies too. A private host
name is masked whole (`<HOSTNAME_1>` where `<HOSTNAME_1>.example` was shown), also with `_` in a label, `[.]` dots or a hyphenated
suffix. `host db01` / `hostname=db01` mask `db01`. Texts with more than 2,000 distinct base64 values are refused (`InputTooLarge`).
Cost: <the I16 numbers measured in Phase 3>."

## (A) Round 1 (tickets/G4-review-1.md): what v2 resolved, kept
Unchanged from v3's section A: every round-1 finding is resolved. In v4:
- g4c-M2 (host-key false positives) is tightened again (L13);
- g4r-M6 / g4c-M3 (the joined decoded view) has its separator replaced (L15);
- g4c-M6 `_KEPT_HOST` is re-measured.

## (B) RUNG TABLE and NEEDED-CHECK
Unchanged from v3's section B, re-read at cd8d375. Added to the read list: gate.py `_CONTROL_CHARS`, `sanitise_text`, `_outside_code`,
`_per_part`; cards.py `_card`; agent_loop.py 610-675; tests/p1c_builders.py.

## (C) NOT CHECKED / NOT RE-MEASURED
- Nothing of G4 was built. Every TB expected value of a G4 path is derived by reading, or measured with a stand-in (marked).
- The final HOSTNAME start look-behind (5.2 point 1) was not run through the 8 suites, because of the coordinator's load stop. The
  pre-final variant ran 710 passed, 1 failed (the perf row it was changed for). The final one was checked by:
  - the probe (19 closed);
  - the corpus diff (2 rows);
  - 53 host rows;
  - the p1d card cells and A-mutant checks;
  - the 6 perf micro-cases.
- The A4/A5/A38/A6 killers: measured in-process by replacing the function source, not by `tools/mutation_runner` (load). Phase 4
  runs the runner.
- The section 8 timings on a loaded machine; the prototype numbers; `build()`'s 1.6 s; Phase 0 (f), the property test with 1,977
  inputs at the base.
- Whether k1b fixtures hold base64 that decodes (they would gain an `ENCODED` count, and possibly a SECRET count under L8 v4).
- FOUND (outside G4): redact_mutants `N15 the alias build asks for no budget` has an `old` text that occurs 0 times at cd8d375, so
  `python tests/redact_mutants.py` reports `ERROR SNIPPET NOT FOUND` at the base. This is a G7 round 3/4 leftover (L18).

## (D) Plan review round 2 (tickets/G4-review-2.md)
Every finding stays as v3's section D recorded it (all TAKEN; contested in part: readiness B1's JSON, codebase M3's count of 63 and
M7's cap behaviour). Two have changed state since:
- M5 (property test), reconciled with G7 r4's p1c_builders in v4;
- codebase nit "L8 decoded EMAIL/HOSTNAME/IPV4 stored at rest", which still holds: v4's L8 keeps only kinds never stored.

## (E) Plan review round 3 (tickets/G4-review-3.md): every finding
Readiness reviewer:
| id | state | where / reason |
|---|---|---|
| A (stale against S) | TAKEN | header, 0, 0.1 (every cite re-derived by name), 2.3-2.5, 8, I20 re-measured |
| B1 step 5 and the stop rule | TAKEN | 2.3 step 5 is the cd8d375 clause verbatim; stop condition recorded met and resolved (0); every "open fix / not in HEAD" sentence deleted |
| B2 `\x1e` on the card path | TAKEN | 3.4: separator `"\n\n;\n\n"` (measured 837 texts), `seen` length check, pieces holding the separator, fences across pieces; TB-3.24 is the card test (2 benign runs + 1 secret -> exactly one `<ENCODED_1>`); TB-3.18 |
| B3 Phase 2 `-k` | TAKEN | 12: no `-k` at all; Phase 2 runs the whole new file first, then the suites |
| B4 TB names and outputs | TAKEN | 10.2-10.4: every TB test named, with recipe and exact output; strict xfails assert `leak_of(...) == "no"` (fail before and after); L-H1 is a plain assert, not an xfail |
| B5 tests per phase | TAKEN | 11 and 12: which file each phase creates; exact red ids (Phase 0: 76; Phase 3: 19; others none); host tests in their own file in Phase 4 |
| B6 A6 STOP | TAKEN | 9.3: run against the mutant by hand: `test_row_L11_slack` kills A6 (L3, I1, L4, L8 do not); A4 -> D3b, A5 -> D3c, A38 -> D3c re-verified |
| B7 baselines | TAKEN | 8 re-measured (table); Phase 0 (b) now updates the ticket on a moved base and stops only on a new kind of leak |
| B8 must-stay-green; `enforce_map`; property guard | TAKEN | 11 (bold suites); TB-3.27; the guard is already gone in G7 r4, and v4's property change only adds `p1c-b64` |
| N1 sha256, 1.6 s | TAKEN in part | sha256 recomputed (equal); 1.6 s NOT RE-MEASURED (load; the whole probe is 2.2 s) |
| N2 wrapped block table | TAKEN | 3.1 point 3 table (8 rows), TB-3.2 |
| N3 mutant count | TAKEN | 63 by `len(M)`; the 64th `m(` is `def m(` |
| N4 `x86_64`, `eth0` | TAKEN | 5.3, L13, TB-4.2 |

Codebase reviewer:
| id | state | where / reason |
|---|---|---|
| B1 | TAKEN | as readiness B1; tests/test_redact_settle_loop.py "NotSettled" text stays green |
| M1 cites | TAKEN | 0.1 table (name + current line), 0.2 rule "by name"; e.g. `_LABELS` 867, `SECRET_KINDS` 2017, HOSTNAME 406-412, settle 1159-1218, `_SETTLE_ROUNDS` 1928, `redact_text` 533, `_build` 1794, `REDACT_BUDGET_S` 82 (comment 52-81), `STORED_KINDS` defaults.py 150, gate comment 239-240 (all moved again since the review) |
| M2 HOSTKEY false positives, sweep | TAKEN; `host s3 bucket` CONTESTED | 5.3, L13, TB-4.2, TB-4.3. `s3` is 2 characters and the value needs at least 3: v3 already left it (measured) |
| M3 suffix boundary | TAKEN | 5.2 point 5, L14, TB-4.5 (all three named rows decided and measured) |
| M4 card SETTLE_NOTE | TAKEN | 8 corrected (no card posted, event recorded undelivered); L17; TB-3.25 |
| M5 L8 residual | TAKEN (second option) | L8 v4 keeps decoded entries of kinds not in STORED_KINDS; TB-3.6; the residual for identifiers is narrow (their plain copies are found by their own patterns) and the v3 default stays as fallback (a) with its xfail |
| M6 forgotten suites | TAKEN | 11 and 12 Phases 2-5 |
| N1 unreachable branch | TAKEN | 4 point 4: the SECRET-kind branch deleted; ENCODED reuse kept as the function contract (TB-2.6) |
| N2 R3 `new` re-indent | TAKEN | 11 (`old` and `new`, measured with ruff format) |
| N3 more settle rounds on T2 | TAKEN | 2.5 (measured with a stand-in: same 3 rounds), TB-3.19 with three separators |
| N4 clock reads per original | TAKEN | 2.4 step 6 |
| N5 defaults.py comment | TAKEN | 7 (second clause) |
| design check: `_build` sort key | TAKEN | 4 point 5 (tie-break for the same original only), TB-2.7, TB-2.8 (measured base outputs) |
| design check: other points | TAKEN as read | `storable()` / config.py 280, k1b `_kind` (3.5 updated for L8 v4), ENCODED in `_OWN_OUTPUT`, CountedClock (TB-3.4) |
| tests red under the ticket | TAKEN | B1 fixed; additionally v4 found and fixed a red that neither reviewer listed: test_p1d_a_paths' card property under v3's start look-behind (5.2 point 1) |
| citation table | TAKEN | 76 derived from re-measured lists; 77 = 17 + 60 re-counted; 229 and sha256 recomputed; 63 confirmed |

Counts:
- Readiness: 1 Blocker + 7 Majors + 4 nits + the A list: all TAKEN; N1 in part (1.6 s not re-measured).
- Codebase: 1 Blocker + 6 Majors + 5 nits + the design check, the red list and the cite table: all TAKEN, one sub-claim CONTESTED (M2's
  `host s3 bucket`).
- New lead decisions: L13-L18.
