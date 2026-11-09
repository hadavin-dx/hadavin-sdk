# Package ticket P1d: a secret split by markup (markdown markers, an HTML entity, a terminal escape, a control character, another letter case, an inserted character) is shown unmasked by `approvals.channel.clean` and by `runmap.redact_text`. DRAFT revision 5 (plan review round 5 not yet run)

## The problem in plain words
A person (or a model) is shown a text after secrets and personal data were replaced by placeholders such as `<APIKEY_1>`. The redactor reads the text only as written, so a secret written with extra characters inside it, for example `AKIA**IOSFODNN7EXAMPLE**` (the asterisks make half of it bold), is not recognised and is shown whole. A terminal colour code, an accent mark, look-alike letters, another letter case or a line break does the same: a person or a model joins the pieces again. Two more holes of the same kind: the approval gate turns every `.` in an e-mail address or host name into `[.]` BEFORE the redactor runs, so these are never masked, and a password that contains `&` shows the part after the `&`.

**Why this ticket is over 250 lines (template rule):** the failing-input tables are the specification (lead order 146 2(a)): about 90 lines of rows, 25 of mutants, 30 of pseudocode and the caller table. History is in the revision log at the end; reviews and resolutions are in `handover/reviews/P1d/`.
**Status (2026-11-09 UTC; IST = UTC+5:30):** text only. Nothing has been run yet: no code, no pull request, no probe for revisions 2 to 5. Items marked V come from revision 1's author probes (`handover/evidence/P1d/author-probes-2026-11-07.txt`, a scratch prototype, not the build). Items marked UNVERIFIED are read or measured by the build step named beside them (BS-0 to BS-4) before their row counts. The modules `runmap`, `channel`, `gate` and `textnorm` are not on this branch; one read of `textnorm._scan_key` on `origin/core/P1b-fixwip` is the only source read. Marker: CODE-LAST v1.

## Lead rulings this revision implements (ORDER 165 to 168)
- 165: the fix is inside `runmap.redact_text` (one choke point, model path included, no P1e); the squeezed and case-folded passes are measured in P1d; a withheld card is a finished state (posted once, operator log line, visible reason); H31-H35 are fixed in P1d; P1d is a HARD DEPENDENCY of any pilot or prod merge of P1b or PR 63.
- 166: the model path withholds by default, logs, never raises; the H34 over-mask is accepted and its rate reported separately; operator route = the EXISTING one, least new surface; S11/S16 are P1d-b; the exact fallback for short values only with `coverage=exact_only` recorded and strict mode still refusing.
- 167: P1b exposes the minimum scan length and pins the `scan_holds` error classes; marker plus client-profile refusal with a negative test and a mutant; S6 to P2d-2 as a ledger row with the same hard dependency, S13 (on the `redact_text` path) folded into P1d; `display_withheld` only if the approve path can still reach the summary, proven by a test; one deterministic size cap, withhold above it, no text slices.
- 168: the size cap is config with a validated range and a stated source (here: **unmeasured placeholder**), real sizes measured in BS; rows 005/006/009/010 stay OPEN under their own topics (P2d-2, P1d-b, P1d-c) so `ledger_check --topic P1d` can pass, and keep blocking client data through the marker gate; if BS-2 cannot reach 0 false learns, **P1d is HELD** (no best effort), the exact number and failing shapes go to the lead.

## Words used (defined once; one word keeps one meaning)
- **Choke point** = `guard/runmap.py::redact_text`. Every model-bound text, log text, tool result and approval card goes through it.
- **View** = another spelling of the same text. **Deleting views** = the five-step pipeline below (used by the residue test and by learning). **Squeezed** = a text with every character that is not a letter or digit removed (digits kept).
- **Known value** = an original the redactor masked in this call (seed entries excluded) or one found by the **learning pass** (the redactor's patterns run on the views; the output is thrown away; only the found originals are kept). A known value shorter than `P1D_MIN_KEY_CHARS` is skipped (outside the guarantee).
- **Dropped form** = the shown text with each genuine placeholder replaced by one space. **Put-back form** = the shown text with each genuine placeholder replaced by `" " + original + " "`. Both test "could a reader join the pieces".
- **Residue rule** = after masking, no known value may be readable in any deleting view of the dropped form, and the put-back count test must pass. If either fails the text is **withheld**.
- **Withheld** = `redact_text` does not return the text. Default (`on_residue="withhold"`): it returns the fixed sentence `WITHHELD_NOTICE` and writes one operator log line. With `on_residue="raise"` (approval-card callers only) it raises `runmap.LookalikeCopy`, for every reason (residue, size, error). The model path never raises.
- **Not approvable** = a request whose card was withheld: no buttons, and the approve path refuses it.
- **Carrier row** = a row whose input needs a step that changes letters or digits (decode, deleting an escape's payload such as `0m`); it decides that step by itself because the scan key already ignores punctuation (R1).
- **Tier C** = a core change on a redaction path (extended review, no round cap).
- **Row groups:** **fb** = must FAIL on the base (fail-before); **pb** = passes on the base and stays unchanged; **ow** = accepted over-withhold, counted and reported separately; **new-surface** = needs a name that does not exist on the base (see fail-before).
- **Operator** = the person who runs the studio's deployment for the client.

## Verified facts (V = revision 1 probes on main `0dabf1f` / P1b `0d843b4`, not re-run; R = read on 2026-11-09)
- V1: `clean` gives the same output on main, P1b and `core/ci-lint-set` for every row: the hole is on main.
- V2: `gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `_RENDERED_MARKUP` exist (`gate.py:197-226`) and nothing calls them. V3: `gate._rendered`'s docstring says `AKIA&amp;...` "shows a key joined"; a renderer shows `AKIA&IOSF...` (BN-P1d-2). V4: `redact.strip_ansi` puts a SPACE where an escape stood between letters on purpose; a terminal shows the parts joined.
- V5: the redactor's own views (`runmap._views`; P1b adds `composed`) do not delete markers, escapes or control characters and do not fold case or look-alikes for pattern matching; `redact.py:~1204 _sweep` is literal and case-sensitive. The split key reaches the model through documents, tool results, tool errors and logs (sibling report S1-S5).
- V6: `textnorm.scan_holds(text, value)` holds `AKIAIOSFODNN7EXAMPLE` in `key AKIA**IOSFODNN7EXAMPLE** x` and its lower-case copy; raises `ViewTooShort` for `10.0.0.1`; `textnorm.fold` turns Cyrillic look-alikes and a combining accent into Latin but keeps `**`.
- **R1 (decisive):** `textnorm._scan_key` (`origin/core/P1b-fixwip`, `textnorm.py:1088-1093`) keeps only letters and digits (`str.isalnum()`, category not `Lm`). So `scan_holds` ignores `* _ ~` backtick `. &`, spaces, controls and line breaks by itself. For the residue test only steps that carry or change letters and digits matter (decode, deleting tags and escape sequences, fold if `scan_holds` does not fold). Deleting markers and line breaks matters for the learning pass. UNVERIFIED: the P1b fix batch (commit `2034512`) may change this; BS-0 re-reads (stop rule). A P1d test pins R1 (`test_scan_holds_ignores_non_alphanumerics`) so a P1b change fails with a clear message.
- V7: `register_value` (strict) raises `CoverageRefused` for Latin and digit values; P1d never calls it. V8: a prototype that ran the whole redactor BEFORE the gate broke two fuzz tests; only the defang moves.
- V9 (prototype cost, 4-CPU shared container; the prototype had the five-view pipeline and no fast path): 3,000 chars 0.21 s (today 0.03 s); 30,000 chars 2.69 s (0.24 s); 120,000 chars 12.9 s (0.98 s); known-value count not recorded. Loop order matters: views outer, values inner (190 s the other way at 30,000).

## Merge-order preconditions (BS-0 gates)
1. P1a (PR 63) and P1b merged. The fail-before base is post-P1b main. A P1d test file imports `textnorm` only inside test functions.
2. P1b exposes the minimum scan length as `TN_MIN` and pins the `scan_holds` error classes (`ViewTooShort`, `EmptyView`, `TextnormError`) by a test (ORDER 167 item 1). BS-0 reads both; a difference from V6/R1 = STOP, back to review.
3. `defaults.py` can take the constants; `vulture_whitelist.py` and `tools/mutation_runner.py` exist on the base (else `tests/p1d_mutants.py` uses a plain subprocess loop and says so).
4. The 5 baseline failures are listed by test id and cause and fixed here or recorded as environment with an owner before "done".
5. **Hard dependency (ORDER 167 item 2, ORDER 168):** `runmap.P1D_APPLIED = True` is added by P1d. The client profile's start function (BS-0 names file and function) refuses to start unless ALL THREE markers exist: `P1D_APPLIED` (this package), `P2D2_APPLIED` (P2d-2 adds it) and `P1DB_APPLIED` (P1d-b adds it); the two others are absent until their packages land, so P1d alone does not open the client profile. The message names the missing package. Start-up canary (extra, ORDER 167 item 2): the start function runs one split-key canary built from parts (`AKIA**` + `IOSFODNN7EXAMPLE` + `**`) through `redact_text` and refuses unless the result is withheld. Tests: `test_client_profile_refuses_without_marker` (once per marker), `test_client_profile_refuses_when_canary_leaks`, `test_client_profile_starts_with_all_markers`; mutants M22, M28.

## RUNG TABLE (R447, R448, R450; scale of 2026-11-06: 1 no-code, 2 own core modules, 3 existing free tools, 4 free libraries, 5 own new code last)
Gate: core SDK change, no client, no fee, no new dependency. Rung 1 closed (R447). Rung 3 closed (a model feature cannot be exact and runs after the text left). **Guarantee class:** **exact** = holds for every value in the set named in the row, up to the cap, with a test; **best effort** = holds for the cases tested; **detection-only**. An unknown secret with no pattern (a plain password, no key word) is OUT of the guarantee. Reuse covers building the views; our new code is the residue check, the learning pass and the wiring.
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| views, decode, fold | read the text as a renderer, terminal or person shows it | 2 (`gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `redact._ANSI`, `runmap.undo`, `textnorm.fold`) | V2, V4, R1 | one private function with a fixed order | exact on the listed rows up to the cap | CUT-TO-CONFIG+GLUE |
| Markdown library | rendered view | 4: `markdown-it-py` (imported by `gate.py:72`) | CommonMark only; does not read Slack `*bold*` / `~strike~`; not built | nothing | n/a | CUT |
| fold and scan | look-alikes, accents, case, separators | 2 (P1b `fold`, `scan_holds`, `scan_cache`) | V6, R1 | a narrow second step set: `delete_noise`, `squeezed`, and the exact fallback for short values (P1b has none of the three) | exact for P1b's documented coverage | CUT-TO-CONFIG+GLUE |
| learning pass | find an UNKNOWN key with an inserted character or in lower case | 2 (the redactor's patterns on more views) | UNVERIFIED; BS-2 | the shape on the squeezed view plus the digit rule | exact on rows; ships only at 0 false learns (else HELD) | KEEP-CODE (small) |
| residue rule | decide whether a known value is readable with placeholders put back | 4: detect-secrets, gitleaks, Presidio find SHAPES; none compares a text with OUR run map | not run (UNVERIFIED); test idea: row KV | redaction before a person (R447 guarantee) | exact for known values up to the cap | KEEP-CODE, about 80 lines (estimate) |
| fail closed, bounded cost | never return an unchecked text | 2 (`InputTooLarge`) | V9 | one deterministic cap, one catch-all | exact (the refusal) | KEEP-CODE, about 25 lines |
| defang after redaction | `[.]` must not split an e-mail or host before the redactor | 2 (`gate.sanitise_text`) | V8 | one parameter and one call order | exact | KEEP-CODE, about 15 lines |
**80 percent (R448):** needs: read as rendered; decode; fold; unknown shapes in other views; decide what is readable with placeholders put back; fail closed; mask before our own markup. Rungs 2 and 4 meet three of seven; no library works inside the choke point; a guarantee path in any case. **Cost (estimate):** build 10-14 agent-hours plus uncapped review rounds; 0 fees, 0 model tokens, 0 new dependency.

## Goals and Non-Goals
**Goals.** (G1) No known value is readable in any text `redact_text` returns or any card `clean` returns, for the families in the rows, up to the cap. (G2) One implementation at the one choke point; `clean`, `SlackChannel._blocks`, documents, tool results, tool errors, logs and `redact_value` get it without a new call site. (G3) A text the rule cannot clear is withheld in a stated way (caller table). (G4) The false-withhold rate and the H34 over-mask rate are measured separately (BS-3). (G5) E-mail addresses and internal host names are masked in cards.
**Non-Goals.** (N1) An unknown secret with no pattern. (N2) What a person types after the card is posted. (N3) S6 `tools._secret_forms` / `_scrub_layers`: P2d-2. (N4) A new endpoint or console. (N5) Exactness above the cap: above it the text is withheld, not checked. (N6) Unknown (not in the map) secrets of a token kind other than AKIA/ASIA written in another letter case or with `.`, `&` or a line break inserted: those kinds are case-sensitive by definition, so a changed-case copy is not the secret; H37 variants measure it (not claimed).

## Alternatives considered
- **A1 Heal and show** (show the healed view). Rejected: fold and case views change the characters, the card would differ from the request the approver approves. Trigger: BS-3 above ceiling for deletion-only views; then A1 for those views only. BS-1 and BS-3 name A1 as their fallback.
- **A2 Offset-mapped masking.** Rejected for now: span tracking inside `textnorm` (P1b frozen). **A3 Escape the markers in the shown text.** Rejected: no help on Slack `plain_text`; breaks code in cards. **A4 Check only in `clean`.** Rejected: the model path has the same hole. **A5 Pre-mask only e-mail and host before the gate.** Rejected: covers two kinds; the defang moves after redaction. **A6 A library** (Presidio, detect-secrets, gitleaks, markdown-it-py): none knows the run map. **A7 Text slices for large texts.** Rejected: filler longer than the overlap splits a key; one cap and withhold above it (ORDER 167 item 5).
- **A8 Fixed-point loop for views.** Rejected: step order cannot matter in a fixed point. A fixed ordered pipeline; ONE bounded second round of steps a and b1 only if a combination row C01-C10 fails on one pass (decided by the row at BS-0/build, and then `PIPELINE_VIEWS`-style test bound becomes 7).
- **A9 Stored one-bit field (`display_withheld`).** Not the default: new state in approvals. The approve path calls the same `clean` on the stored raw text. The bit is the ONE allowed addition if BS-0 (d) finds that the raw text is not reachable at approve time.
- **A10 A fast path for plain text.** Not built. Added only if BS-4 shows p95 over `REDACT_BUDGET_S / 4` at the cap (exclusion set in BS-4).
- **A11 Extra view `b2` (noise deletion before fold).** Dropped: `scan_holds` ignores noise itself and `d` deletes it after fold; restored only if a row passes only with it (BS-0 stop rule).
- **Chosen:** fixed-order views, a narrow learning pass, the residue rule, all inside `redact_text`; withhold by default; raise only for cards.

## Risks and mitigations
- R1 False withholds. Only a KNOWN value readable in a deleting view of the dropped form withholds; ceilings in BS-1 and BS-3; guard rows F01-F19.
- R2 Cost. One cap and a bounded pipeline; cost is views (at most 5) x known values per call, and calls per run (`redact_value` leaves). Latency target BS-4, measured with 10, 200 and 2,000 known values and a many-leaf JSON.
- R3 The learning pass over-learns. Prose such as `Southeast Asia and Oceania` squeezes to `southeastasiaandoceania`. Rule: on `squeezed(d)` the shape is `(?i)(AKIA|ASIA)([A-Z2-7]{16})` (real base32 alphabet, so `0 1 8 9` break the run), unanchored, and a match counts only if its 16 trailing characters contain at least one of `2-7`. About 3.6 percent of real keys have no such digit and are found only when written as is (the redactor's own pattern). BS-2 measures. **If BS-2 cannot reach 0 false learns, P1d is HELD (ORDER 168 item 3): the exact count and the failing shapes go to the lead; no best-effort fallback is written.**
- R4 A model-path text disappears. The notice is visible to the model and the log; no exception; a run is never ended by a withhold.
- R5 Guard-test change. The learning pass is a private function, so the hook lint of `test_k5_round11.py` needs no exemption (BN-P1d-3).
- R6 P1b changes under P1d. BS-0 pins the P1b head, `TN_MIN` and the error classes; P1d calls nothing private of `textnorm`.
- R7 The `&` fix over-masks (H34). Measured, accepted (ORDER 166 item 2).
- R8 Hostile text forces a withhold or blanks a stored tool input. Fail-safe, accepted. In `redact_value` the stored leaf is the fixed notice only: reason, `source` and character count are in the operator log line; the stored record deliberately keeps nothing else (no digest: a digest of a text that holds a secret lets a short secret be tested offline).
- R9 `redact_value` stores the notice in place of a leaf. If an approval-binding hash reads a stored redacted text, the bound content changes. BS-0 (e) lists every reader; if one hashes, `redact_value` uses `on_residue="raise"` for it.
- R10 A judge or vendor screen that returned "clean" for a notice would fail open. Rule in the caller table; tests.

## Sinks
| sink | what a reader can re-join |
|---|---|
| Slack card (`plain_text`) | a person copies `AKIA**IOSF...**`; an entity shows `&amp;`; a colour code shows as junk |
| Markdown viewer / `notify` text | the viewer shows the key whole |
| `FakeChannel`, log | verbatim |
| model (documents, tool results, tool errors, `safe_head`, `redact_value`) | a model re-joins and may echo |
The weakest reader decides: the same rule for every sink.

## Constants (both in `defaults.py` as config with a validated range; out of range refused at start; no literal in code)
- `P1D_MAX_TEXT_CHARS`: start **30000**, range 1,000 to 1,000,000. **Source: unmeasured placeholder** (no real model-path text sizes exist yet). BS-1 and BS-4 measure the real sizes of documents, tool results, tool errors and `redact_value` totals (p50, p95, max) and the share above 10,000 and 30,000. Commit rule: the largest size at which the 95th percentile of `redact_text` over the BS-1 corpus and the largest real-shaped document stays under `REDACT_BUDGET_S / 4` on the build machine, never below 30000. If the bound cannot hold at 30000: STOP, back to the lead. The same constant applies to each call AND to the sum of leaf characters of one `redact_value` call (above it the whole value becomes the notice): ONE cap, no second constant. `REDACT_BUDGET_S`: BS-0 (h) reads its file and value; if it does not exist, STOP (no invented value).
- `P1D_MIN_KEY_CHARS`: start **8**, range 4 to 64. A known value shorter than this is skipped. Commit rule: may be raised if BS-1 shows false withholds from short common values, never lowered. Three zones: below the floor, outside the guarantee (best effort, CHANGELOG); from the floor up to `TN_MIN - 1`, the exact fallback; `TN_MIN` and above, `scan_holds`. BS-0 reads `TN_MIN`; if `TN_MIN <= P1D_MIN_KEY_CHARS` the fallback zone is empty: the fallback code, M13-M15 and its boundary rows are deleted and F07 runs through `scan_holds`.
- New names besides the two constants: `WITHHELD_NOTICE`, `LookalikeCopy`, `is_withheld`, `P1D_APPLIED` (and the two markers of other packages that this ticket only checks).
- Reasons: `residue | size | error`. No clock, no deadline, no alert constant. The view count is NOT a constant: five steps, at most 5 views by construction; one test pins it.

## The algorithm (pseudocode; no code; the builder writes the regexes from the names)
```
redact_text(text, mapping, neutralise=None, *, on_residue="withhold", source="", approval_id=""):
  ctx = (source, approval_id, len(text), on_residue)
  try:
    text = text.replace("\x00", "")
    if len(text) > P1D_MAX_TEXT_CHARS:  return _withhold("size", ctx)
    shown, mapping2 = <the existing redaction, unchanged, incl. neutralise>   # BS-0 (f): mapping is updated in place or returned; the ticket follows the base
    views   = _healing_views(text)                            # Views(v0, a, b1, c, d)
    learned = _learn_unknown(views)                           # set[str]
    known   = {k for k in originals(mapping2, seeds excluded) | learned if len(k) >= P1D_MIN_KEY_CHARS}
    return _finish(ctx, shown, mapping2, known, nviews=len(views.all()))
  except LookalikeCopy: raise
  except Exception as exc:         # InputTooLarge, TooDeep, TextnormError, RecursionError, MemoryError, bugs
    return _withhold("error", ctx, exc=type(exc).__name__)    # class name only

_withhold(reason, ctx, *, views=-1, known=-1, exc=None):   # the ONLY place that logs; -1 is logged as "-"
  log one WARNING line; if ctx.on_residue == "raise": raise LookalikeCopy (from None) else return WITHHELD_NOTICE

_healing_views(t) -> Views:   # CUMULATIVE: each step takes the previous output; Views.all() is the de-duplicated tuple
  v0 = t
  a  = undo(v0)                       # entities, percent-codes, backslash/JSON escapes, to P1b depth (BS-0 reads it; H08 and C10 need two rounds)
  b1 = delete_carriers(a)             # tags and comments (gate._RENDERED_MARKUP, else a documented fallback), ANSI/CSI/OSC/C1 and a lone ESC (redact._ANSI): their payload is gone
  c  = textnorm.fold(b1)              # look-alikes, accents, full-width
  d  = delete_noise(c)                # [*~`] always; "_" when not between two alphanumerics (judged AFTER the others are removed); controls; Cf/Cc; CR, LF, U+2028/2029
  # test (not an assert in code): a crafted text where all five steps differ yields five views, never more

squeezed(s) = the characters of s with str.isalnum() true, in order      # digits 0-9 kept

_learn_unknown(views) -> set[str]:
  found = set()
  for v in (views.a, views.b1, views.c, views.d):                  # v0 is covered by the existing redaction
      found |= redact._find_matches(v)                             # NEW private helper: the match loop of redact_text extracted, no behaviour change
  for m in re.finditer(r"(?i)(AKIA|ASIA)([A-Z2-7]{16})", squeezed(views.d)):      # unanchored (H35)
      if re.search("[2-7]", m.group(2)): found.add(m.group(0))
  return found      # BS-4 may drop views from the first loop only if no named row fails without them (commit rule below)

_finish(ctx, shown, mapping, known, nviews):
  dropped = shown with each genuine placeholder (in mapping, not a seed) replaced by " "
  for v in _healing_views(dropped).all():                          # views OUTER, values INNER, inside textnorm.scan_cache() (entered once per call)
      for k in known: if _holds(v, k): return _withhold("residue", ctx, views=nviews, known=len(known))
  p = put_back(shown)                                              # ONE pass; see the formula
  for k in known: if count(scan_key(k), scan_key(p)) > e(k): return _withhold("residue", ctx, views=nviews, known=len(known))
  return shown
```
- **`_holds(v, k)`** = `textnorm.scan_holds(text=v, value=k)`; for a value below `TN_MIN` the exact fallback (next section).
- **Put-back formula** (the algorithm is owned by `designs/lookalike-leak.md` section 5 item 3, frozen draft 11, in the studio notes; the wording below is the lead session's restatement and is UNVERIFIED against that note, BS-0 compares): each genuine placeholder is replaced by `" " + original + " "` in ONE pass (a placeholder-shaped text inside a put-back original is not replaced again). `count` = non-overlapping occurrences (`str.count`) of `scan_key(k)` in `scan_key(p)`. `e(k)` = the number the tally explains: copies of `scan_key(k)` that lie inside one put-back original, plus copies spanning adjacent put-back originals (the scan key drops the spaces, so adjacent originals form one run). `count > e` means a copy outside any put-back original = residue. The builder copies rows LK-JAMO-PB (Korean: 11 syllables `chr(0xAC00 + i*21*28)` for i in 0..10, then U+B85C; Tamil: `"Tamilv"` + U+0B92) and LK-UNFOLD from the note into the fixtures file character for character. Only `shown` is put back (no `undo(shown)` form); row PB-ENC below is the test of that cut.
- **The text checked is the text returned:** `_finish` runs on the string `redact_text` returns, after `neutralise`. In `clean` the joined pass is itself a second `redact_text` call, and `defang_text` only inserts `[` `]` around `.`, which the scan key ignores (R1). Test `test_returned_card_bytes_pass_the_check` re-runs `_finish` on the returned card for H01-H25.
- **Commit rule for learning views (BS-4):** try `{a, d}` and `{d}`; a view stays in the first learning loop only if a named H, C or S13 row fails without it.

## Short values (ORDER 166 item 5, ORDER 167)
`scan_holds` raises `ViewTooShort` for a value below `TN_MIN`. For a known value of length from `P1D_MIN_KEY_CHARS` up to `TN_MIN - 1`: (1) **exact fallback**: case-INSENSITIVE exact substring search in EVERY deleting view of the dropped form, with a boundary rule `(?<![0-9A-Za-z])` before and `(?![0-9A-Za-z])` after the escaped value, each side only when the value's own first or last character is a letter or digit; (2) values below `P1D_MIN_KEY_CHARS` are skipped (CHANGELOG); (3) one INFO line per call that used the fallback: `redaction coverage=exact_only values=%d` (no content); (4) **strict mode unchanged:** P1d never calls `register_value`; `TEXTNORM_STRICT_COVERAGE` still makes it raise `CoverageRefused`; `test_strict_mode_still_refuses` pins that nothing in P1d lifts it.

## Refusal behaviour: every caller of `clean` and `redact_text` (BS-0 completes the table from a grep on the base; a test fails if a caller is missing; an unmatched caller blocks the build)
One literal per constant:
- `WITHHELD_NOTICE` = `(withheld: this text may hold a secret written with hidden formatting)`; `runmap.is_withheld(text) -> bool` (equality with the constant).
- Card text (posted once) = `Request <approval_id> cannot be shown safely. It may hold a password, key or e-mail address written with formatting inside it. It cannot be approved from this card. Ask the sender to send it again without formatting, or deny it.` For plan inputs the same sentence is used with the prefix `Inputs: ` (one wording, reviewed once).
- Operator log line (WARNING, logger `hadavin_sdk.guard.runmap`) = `redaction withheld a text: reason=%s source=%s approval_id=%s chars=%d views=%d known=%d`; empty `source`/`approval_id` logged as `-`; `views`/`known` are `-` for `size` and `error`; the `error` case also logs `exc=<class name>`; never any content.
| caller | entry point | on withhold | buttons | pinning test (input, assertion) |
|---|---|---|---|---|
| `SlackChannel._blocks` / `update` / `send` (`slack_channel.py:81,197`) | `clean` raises | posts the card text once; `sent_at` set so `resend_unsent` finds nothing | no | `test_h30`: H01 as summary; one post, no key, no retry |
| `requests.summary` (`requests.py:39,47`) | `clean` raises | the stored request keeps the RAW plan inputs; the displayed text is the card text; not approvable | no | `test_h40`, `test_no_approve_buttons_when_inputs_withheld` |
| `cards.py:59`, `channel.py:111` `post_card` | `clean` raises | same as `_blocks` | no | `test_caller_cards`, `test_caller_post_card`: H01 as card text |
| `channel.py:104` `notify` | `clean` raises | the card text (with the id if known, else the sentence without the id) replaces the message; one log line | n/a | `test_caller_notify`: H01 text; unknown id |
| `FakeChannel` | `clean` raises | records one send of the card text | no | `test_h40` |
| `agent_loop._deliver` (`~560-567`) | n/a | nothing raises there | n/a | `test_deliver_never_sees_lookalikecopy`: a withheld text through the loop, no exception |
| model path: `redact_untrusted`, `prepare_output`, `redact_layered`, `error_reason`, `safe_head` | `redact_text` default | returns `WITHHELD_NOTICE`, logs, never raises; a JSON tool result becomes the notice string and the consumer treats a non-JSON result as an error (fails closed) | n/a | rows S1-S5 |
| `redact_value` (`runmap.py:569-598`; stored records, audit, `evidence.py:191`) | default | the leaf becomes `WITHHELD_NOTICE`; total leaf characters above the cap withhold the whole value | n/a | S5, `test_redact_value_notice` (the stored record shows the notice at the right path), X03 |
| guards: `guard/judge.py:71` (its one `redact_text` line), `guard/bedrock_guardrail.py:98` (one line), `evals.py:63` in `src/hadavin_sdk/` (one line) | default | `is_withheld` means refuse or escalate (the existing verdict of that guard, named at BS-0), never "clean"; for `evals.py` the case is marked failed | n/a | `test_judge_refuses_on_notice`, `test_guardrail_refuses_on_notice`, `test_eval_case_fails_on_notice` |
| `evidence.grounded` (N2) | n/a | no code change: a notice never grounds an action (a mismatch fails closed) | n/a | pin test `test_grounded_fails_on_notice` only |
BS-0 adds every other caller it finds and greps every `except InputTooLarge|TooDeep` (`redact_text` no longer raises them: it withholds); each such caller's new behaviour is named.

## Operator route and approve path (ORDER 166 item 3, ORDER 167 item 4): ONE mechanism
BS-0 (d) names the file and function of (i) the EXISTING deny call, (ii) expiry, (iii) the approve function, who may call each, AND states which text `requests.py` stores (raw or fallback).
**Design:** (1) a request whose card was withheld stays in the store like any pending request, with no buttons. (2) It leaves the pending state through the existing deny call or expiry, which need no view of the content; the operator reads the request id and reason from the log line. (3) The approve function calls **the same `clean`, with the same arguments**, on the RAW stored summary and raw plan inputs, and refuses on `LookalikeCopy` with the existing refusal error class. If the run map or the stored raw text is absent or unreadable at approve time, it refuses (fails closed). No new field, no schema change, `receiver.py` untouched. A different run map at approve time can only add values, so it can only refuse more; `test_normal_request_still_approvable` pins that an ordinary request stays approvable.
**Tests:** `test_approve_refuses_every_withheld_row` parametrised over EVERY row `clean` withholds (H01-H25, H28, H30, H40, C01-C10) plus `test_withheld_request_cannot_be_approved_by_callback` (hand-made approve call) and the run-map-absent row; mutant M21.
**Stop rule (BS-0):** if the approve function cannot reach the raw stored text and the run map, or if deny is reachable only from the card button, the ticket goes back to review with ONE allowed addition: a one-bit `display_withheld` set at card time and read by the approve function (proven by a test that the approve path reads it), or one operator deny call as a ticket line. Content review by a person is P1d-c (ledger 010).

## Scope of S11, S16, S6, S13
- S11 (`k1b/redaction.py sensitive()`) and S16 (`receiver.log_message`): **P1d-b**, own package and ledger topic (rows 006, 009), ticket written after this plan review is clean. Closes with marker `P1DB_APPLIED`.
- S13 (`redact.py:1204 _sweep`): **in P1d**; rows H22-H24, S13-1/2; ledger 001 and 004.
- S6 (`tools._secret_forms` / `_scrub_layers`): does not call `redact_text`; **P2d-2**, row 005, topic P2d-2, same hard dependency; closes with marker `P2D2_APPLIED`.
- P1d-c (row 010, content review by an operator): own topic, blocks client data until decided by the lead.

## Template fields
- **Package id and name:** P1d, "split secrets at the choke point". One pull request on branch `core/P1d`, from main after P1a and P1b merge. **Path class:** redaction AND security; **extended review (no round cap): yes**, plan and result. **Depends on:** preconditions above; not P1c (H27 has one expected output per case).
- **Class (R337, R7):** "a value is matched only in the spelling as written, while a reader or renderer reads another spelling". Standards (from memory; read date UNVERIFIED, R450): CommonMark 0.31 sections 6.2, 6.1, 2.5; ECMA-48 sections 5.4, 8.3; Unicode UAX #15 and UTS #39.
- **Source of the code:** our own code only; nothing copied. **Neutral default / alternative:** the redactor has no vendor; alternative A1 has its trigger; `on_residue` selects withhold (default) or raise.
- **Race / process tests:** not applicable (no shared state; the scan cache is per call).
- **Files:**
  - change `src/hadavin_sdk/guard/runmap.py`: `redact_text`, `LookalikeCopy`, `WITHHELD_NOTICE`, `is_withheld`, private `_healing_views`, `_learn_unknown`, `_finish`, `_withhold`, `P1D_APPLIED`; helpers stay in `runmap.py` (no new module; BS-0 may move them to `guard/_views.py` only if importing `gate` privates would create a cycle, and records why).
  - change `src/hadavin_sdk/guard/redact.py`: private `_find_matches(text) -> list[str]` (extracted loop, output of `redact_text` identical, pinned by a test); SECRET value stop-set gains `&` (H34).
  - change `src/hadavin_sdk/approvals/channel.py` (`clean`: raise mode, defang after redaction, pre-mask deleted, joined pass shares the mapping), `slack_channel.py` (`_blocks`), `requests.py` (displayed fallback, not approvable, approve calls `clean`), `gate.py` (`sanitise_text(defang=)`, public `defang_text`, docstring of `_rendered`); `cards.py` only if the BS-0 grep finds a caller there.
  - change `guard/judge.py`, `guard/bedrock_guardrail.py`, `src/hadavin_sdk/evals.py`, `runtime/evidence.py` (the notice lines in the table; `evidence.py` for `redact_value` only).
  - change the client-profile start function (named by BS-0): three markers and canary. change `defaults.py` (two constants), `vulture_whitelist.py` (remove the `gate._rendered` entry), `CHANGELOG.md`.
  - create `tests/test_p1d_rows.py`, `tests/test_p1d_callers.py`, `tests/fixtures/p1d_cases.py`, `tests/p1d_mutants.py`, `tools/p1d_corpus.py` (flags `--seed N --kind all|bs1|bs2|bs3`), `tools/p1d_cost.py` (flags `--sizes --known-counts --leaves`), evidence under `handover/evidence/P1d/`.
  - NOT in P1d: `k1b/redaction.py`, `approvals/receiver.py` (P1d-b), `tools.py` S6 (P2d-2).
- **Interface:** public: `runmap.LookalikeCopy(RedactionError)` (message = the class name only); `WITHHELD_NOTICE: str`; `is_withheld(text: str) -> bool`; `redact_text(text, mapping, neutralise=None, *, on_residue: Literal["withhold","raise"] = "withhold", source: str = "", approval_id: str = "") -> str` (no existing function loses an argument); `gate.sanitise_text(text, *, defang: bool = True)`; `gate.defang_text(text)` (public because `clean` lives in another module and must defang AFTER redaction; `_defang` stays private); `P1D_APPLIED: bool`. Private: `_healing_views(text) -> Views`; `_learn_unknown(views) -> set[str]`; `_finish(...) -> str`; `_withhold(...) -> str`; `redact._find_matches(text) -> list[str]`.
- **Behaviour, exactly:** the algorithm above, plus: (1) the SECRET assignment value extends over `&`; its stop-set stays white space, a quote and `;`; the pattern runs on the undo view, so `&amp;` has become `&` and does not stop it; (2) `clean` = NUL removal, ONE `redact_text(text, seeded, neutralise=_neutralise, on_residue="raise", source="card", approval_id=...)` where `_neutralise` = `gate.sanitise_text(..., defang=False)` plus `withhold_commands`; then the joined pass (`_TAGS.sub`) as a SECOND `redact_text` call that receives the SAME mapping object as the first (BS-0 (f) reads whether the mapping is updated in place; if the base returns a new one, the returned mapping is passed on); then `defang_text`; (3) callers: the table. Fallback if BS-4 finds a kind the moved defang still breaks: a documented per-kind pre-mask for exactly that kind (BN-P1d-8).
- **Existing core code reused:** `gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `_RENDERED_MARKUP`, `redact.strip_ansi`/`_ANSI`, `strip_controls`, `runmap.undo`, `textnorm.fold/scan_holds/scan_cache`, `InputTooLarge`, `TooDeep`. Checked and not reused: `textnorm.register_value`, `tools._secret_forms`.
- **Security and least-privilege notes:** no identity, right, secret or config beyond two constants. No new read of raw stored text beyond what the approve path already holds. The operator line carries counts, never content (a test greps the log for the key). Test values are built from parts; the only whole-key literal is `AKIAIOSFODNN7EXAMPLE`.
- **Rollback:** tag `pre-P1d` before the pull request. **Non-revertible semantic changes, marked in the CHANGELOG:** stored records and model text may contain `WITHHELD_NOTICE`; `clean` raises `LookalikeCopy`; the SECRET value is masked over `&`; e-mail and host are masked in cards; the client profile needs three markers. Loud-failure test `test_withheld_notice_is_loud`.
- **Reviewers:** correctness (`egm-codebase-details`) + adversarial (`egm-design`, `egm-implementation-readiness`), fresh agents with the diff, this ticket and the evidence only; no round cap.
- **Done =** a fresh round finds no blocker or major and all gates green: tests (3.12 and 3.13), ruff check, ruff format --check, bandit -ll, guard tests, CodeQL, SonarCloud, CodeRabbit; ledger rows 001-004, 007, 008 FIXED-VERIFIED; hand-over rows 005 (P2d-2), 006 and 009 (P1d-b), 010 (P1d-c) stay OPEN under their own topics with the hard-dependency note (ORDER 168 item 2) so `ledger_check --topic P1d` passes; the lead merges.

## Failing inputs (literals in `tests/fixtures/p1d_cases.py`; parametrised, the row id is the test id)
**Literals (built from parts):** K = `"AKIA" + "IOSFODNN7EXAMPLE"`; K4 = `AKIA`; K16 = `IOSFODNN7EXAMPLE`. S = `"Tq7mZ" + "4xKp2Vb9Lr3NcW8dYh6uJs"` (S5 = `Tq7mZ`, S22 = `4xKp2Vb9Lr3NcW8dYh6uJs`). E = `"anna" + "." + "m" + "@" + "example" + "." + "org"`. PW(n) = the first n characters of `Qm8vRt2xLp5nZc7bKd3wHj`. ESC = `chr(27)`. **KV** = the text first holds `password=<S>` (S enters the map), then the second copy named in the row. H29: v1 = `Zx4cV7bN1mQa`, v2 = `Wl9sD3fG6hJk`. H36: E as `anna%2Em%40example%2Eorg` and `anna&#46;m&#64;example&#46;org`. X01 filler = `"a "` repeated.
**Entry point per row:** card rows (H10-H30 KV twins, H40, C rows) go through `clean` (raises) and `redact_text(on_residue="raise")`; all other rows go through `redact_text` default (returns the notice). "Withheld" below means the entry point's own form. **Fail-before method:** the new test files run on post-P1b main in a temporary worktree (`git worktree add <tmp> <base>`; copy only the new test files and `tests/fixtures`). Every fb row must FAIL by an assertion, every pb row must PASS. Rows marked **new-surface** use a name that does not exist on the base (`LookalikeCopy`, `WITHHELD_NOTICE`, `is_withheld`, `on_residue=`, `P1D_APPLIED`); they reach it only through one helper `p1d_api()` that returns sentinels (`getattr(module, name, None)`), so on the base the assertion fails with "value shown" or "notice missing" and never with `AttributeError`; `test_fail_before_outcomes` runs the suite on the base and counts failures against errors (errors must be 0). Raw output to `handover/evidence/P1d/fail-before.txt`, head SHA on line 1.
| row | group | input | on base | expected after P1d |
|---|---|---|---|---|
| H01 | fb | `key AKIA**IOSFODNN7EXAMPLE** here` | key shown | withheld (learned: squeezed view) |
| H02a-e | fb | `AKIA**IOSFODNN**7EXAMPLE`; `AKIAIO*SFODNN7EXAMPLE*`; `AKIA~~IOSFODNN7EXAMPLE~~`; ``AKIA`IOSFODNN7EXAMPLE` ``; `AKIA_*IOSFODNN7EXAMPLE*_` (the `_` is judged after `*` is removed) | shown | withheld |
| H07a-b | pb | `AKIA<b></b>IOSFODNN7EXAMPLE`; `AKIA<!-- -->IOSFODNN7EXAMPLE` | masked | masked, same |
| H08a-g | pb | `AKIA&ZeroWidthSpace;IOSFODNN7EXAMPLE`; `&shy;`; `&NoBreak;`; `&InvisibleTimes;`; `&#8203;`; `&#x200B` (no `;`); `&amp;#8203;` | masked | masked, same |
| H09a-c | pb | `AKIA&#73;OSFODNN7EXAMPLE`; `&#x49;`; `&#73` (no `;`) | masked | masked, same |
| H10 | fb (carrier) | KV, second copy `<S5>&amp;<S22>` | shown | withheld |
| H11 | fb (carrier) | `"AKIA" + ESC + "[0m" + "IOSFODNN7EXAMPLE"` | shown as `AKIA IOSF...` | withheld |
| H12a-d | fb (carrier) | ESC `[38;5;196m` inside the key; C1 `\x9b0m`; OSC `ESC]0;t\x07`; OSC 8 `ESC]8;;http://x\x07` | shown | withheld (each its own case) |
| H13 | fb | the four characters backslash, `x`, `1`, `b` written as TEXT inside the key: `AKIA` + `\x1b[0m` (a literal backslash) + `IOSFODNN7EXAMPLE` | shown | withheld (over-refusal accepted: a reader joins the literal) |
| H14 | fb | `AKIA` + ESC + `IOSFODNN7EXAMPLE` (lone ESC) | 19 of 20 chars shown | withheld |
| H15a-b | fb | `x\x08AKIAIOSFODNN7EXAMPLE`; `AKIA\x08IOSFODNN7EXAMPLE` | shown | withheld |
| H16 | fb | `AKIA\rIOSFODNN7EXAMPLE` | shown on two lines | withheld |
| H17a-k | pb | BEL, DEL, NEL U+0085, VT, FF, NUL, ZWSP U+200B, ZWJ U+200D, WJ U+2060, U+202E, soft hyphen U+00AD, each once between `AKIA` and `IOSFODNN7EXAMPLE` | masked | masked, same |
| H18a-b | fb | `AKIA` + U+0301 + `IOSFODNN7EXAMPLE`; U+0323 variant | shown | withheld |
| H19 | pb | the key in full-width letters (U+FF21 ...) | masked | masked |
| H20 | fb | KV, second copy `<S5>` + U+FF0A + `<S22>` | shown | withheld |
| H21 | fb | Cyrillic `А` (U+0410) for both `A` of `AKIA` (key not in the map) | shown | withheld (learned after fold) |
| H22 | fb | KV, second copy `<S5>**<S22>**` | shown | withheld (S13) |
| H23 | fb | KV, second copy S in lower case | shown | withheld (S13) |
| H24 | fb | KV, second copy `<S5>\n<S22>` | shown | withheld (S13) |
| H25 | fb (carrier) | `password=<S5>` + ESC + `[1m<S22>` | `<SECRET_1> ` + tail | withheld |
| H26 | fb | `contact <E> please` | `anna.m@example[.]org` | `contact <EMAIL_1> please` |
| H27a | fb | `host db01.corp.example.com down`, spy `neutralise`, base HAS a HOSTNAME kind (P1c merged; BS-0 reads) | redactor receives `db01[.]corp...` | redactor receives `db01.corp.example.com`; output holds that kind's placeholder and no `db01` |
| H27b | fb | same, base has NO HOSTNAME kind | redactor receives `db01[.]corp...` | redactor receives the undefanged text (`test_redactor_sees_undefanged_text`); output is the defanged text |
| H28a-b | fb | `anna.m**@example.org**`; `anna.m@exam` + ESC + `[0mple.org` | shown | withheld |
| H29a | pb | `passwor<span></span>d%3D<v1>%0D<v2>` | decided at BS-0 by running it on the base | masked tail / withheld; either way recorded |
| H29b | fb (carrier) | KV, second copy `<S5><b></b><S22>` (killer of M4; the second copy is a literal search of S in the sweep and is shown on the base; this row's group is fixed now) | shown | withheld |
| H30a | fb | H01's input as `req.summary` through `SlackChannel._blocks` | shown | card text, no buttons, no key, no retry |
| H30b | fb | key split across a withheld command: `<K4>` + ` ` + `rm -rf x` + ` ` + `<K16>` as summary (the joined pass re-forms it) | shown | withheld |
| H31 | fb | `AKIAIOSFODN\nN7EXAMPLE` (not in the map) | shown | withheld (BS-2 gated) |
| H32 | fb | `akiaiosfodnn7example` (not in the map; has a `7`) | shown | withheld (BS-2 gated) |
| H33a-c | fb | `AKIA&amp;IOSFODNN7EXAMPLE`; `AKIA.IOSFODNN7EXAMPLE`; `AKIA\*IOSFODNN7EXAMPLE` | shown | withheld (squeezed view; BS-2 gated) |
| H34a | fb | `password=ab12&cd34ef56gh78ij` (raw `&`) | `<SECRET_1>&cd34...` | whole run masked |
| H34b | ow | `password=<S5>&amp;<S22>` (undo view makes `&amp;` a `&`, BS-0 confirms); also `password=hunter22&user=bob` | `<SECRET_1>&amp;...` | whole run masked; over-mask of `&user=bob` counted (BS-3) |
| H35 | fb | `keyzAKIAIOSFODNN7EXAMPLE` | shown | withheld (unanchored shape; BS-2 gated) |
| H36a-b | fb | the two encoded e-mails of the literals | shown | withheld |
| H37a-c | fb | **chosen at BS-0:** one fixed-prefix token kind OTHER than AKIA/ASIA from the redactor's pattern table (default: the GitHub-token shape if the table has it), built from parts, split by `**` (a), by a newline (b), by a full-width `*` (c), not in the map | shown | withheld (learned from the deleting views). If the table has no such kind: step `d`, M5 and these rows are deleted and the pipeline is 4 views |
| H37d-e | measure | the same kind in lower case (d) and with `.` inserted (e) | shown | measured, reported, not claimed (N6) |
| H40 | fb | H01 as a plan input through `requests.summary` then `FakeChannel.send` | key shown | card text with `Inputs: `, no key, no buttons; one send, no retry |
| S13-1, S13-2 | fb | `password=<S>` in a document, then S in another case, then S split by `**`, through `redact_untrusted` | shown | the notice |
| PB-ENC | pb? | a placeholder written as `&lt;SECRET_1&gt;` next to a value (built from parts) | recorded at BS-0 | stop rule: if a row fails without the `undo(shown)` form of the put-back test, that form returns with PB-ENC as its killer; otherwise it stays deleted |
**Combination rows (one pass proof):** C01 `AKIA**` + Cyrillic `О` + `SFODNN7EXAMPLE**`; C02 `AKIA**IO` + U+0301 + `SFODNN7EXAMPLE`; C03 `AKIA&ast;&ast;IOSFODNN7EXAMPLE`; C04 `AKIA&amp;ast;IOSFODNN7EXAMPLE`; C05 `AKIA` + ESC + `[0m**IOSFODNN7EXAMPLE`; C05b `AKIA&#27;[0mIOSFODNN7EXAMPLE`; C06 `AKIA` + ESC + `[0m\nIOSFODNN7EXAMPLE`; C07 `akia**iosfodnn7example`; C08 `AKIA%2A%2AIOSFODNN7EXAMPLE`; **C09** `AKIA&a**mp;#73;OSFODNN7EXAMPLE` and `AKIA%2<b></b>AIOSFODNN7EXAMPLE`; **C10** `AKIA%252AIOSFODNN7EXAMPLE`. Each KV twin is a case too. Expected: withheld. If C09 or C10 fails on one pass, A8's second round is added by the row.
**Digit-rule rows:** `asia-prose` = `Southeast Asia and Oceania`, `Asia 2024 Q3 revenue growth`, `Eurasia 2025 results`, `Asia-Pacific 2025 results`, and `asia-long` = `Asia and Oceania markets overview` (16 or more letters after "Asia"): all expected NOT withheld. `asia-nodigit` = `AKIA` + `ABCDEFGHIJKLMNOP` in lower case (16 letters, none from `2-7`): expected NOT withheld, outside the guarantee.
**Boundary rows:** n in {`P1D_MIN_KEY_CHARS - 1`, `P1D_MIN_KEY_CHARS`} for every variant {plain, lower case, `**` inside, ESC inside}, KV with PW(n): n below the floor is not withheld (no crash); n at the floor is withheld. If the fallback zone exists also n in {`TN_MIN - 1`, `TN_MIN`}: the first via the exact fallback with one `coverage=exact_only` line, the second via `scan_holds`.
**Size and error rows:** X01 text of exactly `P1D_MAX_TEXT_CHARS` with a split key 100 characters before the end: checked and withheld; X02 cap + 1: `WITHHELD_NOTICE` (`reason=size`) by default, `LookalikeCopy` in raise mode; X03 a `redact_value` whose leaves sum to cap + 1: the whole value is the notice; E01 a failure injected into `_healing_views`: the notice, `reason=error`, class name logged, no content; E02 raise mode: `LookalikeCopy`; E03 `InputTooLarge` from `undo` (LK-UNFOLD) treated like E01.
**Guard (pb) rows, output unchanged against base (base outputs measured by the evidence runner and pinned in the fixtures file before the ticket is frozen):** F01 ``Approve **restart** of `web-01` in ~~old~~ demo?``; F02 placeholders already in the text are not put back; F02b a seed value written plainly in the text is not a known value (not withheld); F03 `"a" * 40` hex commit id and a 64-hex digest in code spans, written as `"0123456789abcdef" * 2 + "01234567"` and `"0123456789abcdef" * 4`; F04 a Markdown table with bold and code; F05 `Tom &amp; Jerry &lt;ok&gt; &#169; 2026`; F06 `ESC[32mok ESC[0m done`; F07 `10.0.0.1` twice (exact fallback if `TN_MIN > 8`, else `scan_holds`; no withhold; one coverage line in the first case); F08 ``run `make`test``; F09 `password=<S>` masked as today (also pins `count > e`); F10 `José Müller`; F11 a 3,000-character card of ordinary prose; F12 an ARN with its 12-digit account id inside a longer stored value; F13 Greek and Cyrillic prose words; F15 `https://x.example/?a=1&b=2`; F17 2,000 characters of prose with `**`, `*`, `~~`; F18 `10.0.0.1` inside `210.0.0.12` (NOT found); F19 `test_strict_mode_still_refuses`. **ow rows:** F14 (``` `<25 letters and digits>`/`<26 letters and digits>` ```: deleting the backticks joins two identifiers into a 52-character run) and F16 (`password=hunter22&user=bob`).
**Model-path rows:** S1-S5: H01's input through `redact_untrusted`, `prepare_output`, `error_reason`, `safe_head`, `redact_value`: each returns the notice or masked text, never the key, never raises (no `on_residue` passed).
**Pin tests:** `test_scan_holds_ignores_non_alphanumerics` (R1); `test_views_at_most_five`; `test_mutant_ids_exist` (every `M<n>` cited in this ticket exists in the table with the cited meaning); `test_redact_matches_unchanged` (`_find_matches` extraction changes no `redact_text` output); `test_scan_cache_entered_once_per_redact_value`.

## Build steps before any code (BS); each has an output and a stop rule
- **BS-0** (a) list the 5 baseline failures; pin the P1b head, `TN_MIN`, the error classes; **read `_scan_key` and the step function of `scan_holds` on merged P1b; if `_scan_key` no longer keeps only letters and digits, STOP, back to review**; record whether `scan_holds` folds look-alikes; (b) read `undo`'s decode depth; (c) build the caller table by grep, completing it, and grep every `except InputTooLarge|TooDeep`; (d) the operator route (see section), including which text `requests.py` stores; (e) list every reader of a `redact_value` result for a hash (R9); (f) name the client-profile start function; read whether `redact_text` updates `mapping` in place (G8); (g) pick H37's kind; (h) check `defaults.py` takes the constants and read `REDACT_BUDGET_S` (stop if missing); (i) confirm that the match loop of `redact_text` exists as described for `_find_matches` (else back to review); (j) compare the put-back formula with the frozen note; (k) pin exact line numbers for every `~` in this ticket; (l) run every row of the table on the base and pin the outputs of the pb rows and F rows in the fixtures file; (m) check that dropping `b2` changes no H or C outcome (A11).
- **BS-1** model-path false withhold: a made-up corpus of 500 documents, tool results and logs (prose, JSON, stack traces, UUID-heavy logs, snake_case, base64, code), fixed seed, `tools/p1d_corpus.py`, through `redact_text`. Ceiling 0 withholds ("0 of 500 supports a rate below about 0.6 percent at 95 percent", rule of three). Any withhold is listed and fixed or justified by a real hidden value; fallback A1. Also report text-size percentiles (the evidence for the cap).
- **BS-2** learning-pass false learn per pattern on the same corpus plus hex digests, UUIDs, base64 blobs, 2,000 lines of code and prose with "Asia"/"akia"; the squeezed learning ships only at false-learn 0. **If not 0: P1d is HELD; report the exact count and the failing shapes to the lead; the client-data gate stays closed.**
- **BS-3** card path: guard rows plus 500 made-up cards; ceiling 0 withholds on non-secret cards (fallback A1). Reported SEPARATELY: false-withhold rate (ow rows excluded and listed), false-abstain rate, H34 over-mask rate (200 made-up URLs and assignments).
- **BS-4** cost, `tools/p1d_cost.py`: `_healing_views` and `_finish` at 3,000, 30,000 and 120,000 characters, with 10, 200 and 2,000 known values, and a `redact_value` of 5,000 short leaves; latency target: p95 at 3,000 and 30,000 characters under `REDACT_BUDGET_S / 4` and a stated bound for the worst structure. Set the constants by their commit rules; try the learning-view subsets. **Fast path (built only if the target fails):** its test is "no character that any step touches": `& % \ < >`, `* ~` backtick `_`, ESC, controls, C1, line breaks, and any non-ASCII character; rows `AKIA**...` and a multi-line text must NOT take it (mutant M20); BS-4 reports its hit rate on the multi-line corpus. Also the defang move on the 31 pattern kinds (raw versus gated text; list every kind whose output differs). STOP, back to the lead, if the target cannot be met at 30000 or normal traffic holds documents above the cap.

## Mutation plan (`tests/p1d_mutants.py`; one mutant per mechanism; a surviving mutant is declared equivalent with a written reason and the code it protects is deleted, or a row is added). Plain boundary checks (cap off by one, `count >= e`, `except` re-wrap, buttons kept) are ordinary assertions, not mutants. Mutants are cited by number; `test_mutant_ids_exist` pins this.
| mutant | planted change | killer; only-this-step row |
|---|---|---|
| M1 | `_finish` not called | H22 |
| M2 | catch-all in `redact_text` removed | E01 |
| M3 | decode (a) removed | H10, C03; only this step: H10 |
| M4 | tag/comment/ANSI/C1/ESC deletion (b1) removed | H25, H29b; only this step: H25 |
| M5 | noise deletion (d) removed (exists only if H37 has a kind) | H37a-c |
| M6 | fold (c) removed | H21 (if BS-0 shows `scan_holds` already folds, H18/KV rows do not kill it; H21 only) |
| M7 | squeezed learning pass removed | H32, H33, H35 |
| M8 | digit rule removed | `asia-long`, `asia-nodigit` |
| M9 | class `[A-Z2-7]` widened to `[A-Z0-9]` | `Asia 2024 Q3 revenue growth` |
| M10 | put-back without the two spaces | LK-JAMO-PB (Korean and Tamil) |
| M11 | dropped-form loop removed (put-back kept) | H11 (the escape payload is seen only by the dropped form's views) |
| M12 | `TextnormError` swallowed as "no hit" | E03 and `test_textnorm_error_withholds` (map value `"&#65018;" * 14600`, a text without it) |
| M13 | `ViewTooShort` fallback removed (value skipped); exists only if the zone exists | boundary row `TN_MIN - 1`, KV with `**` inside |
| M14 | fallback case-sensitive; same condition | boundary row, lower-case variant |
| M15 | fallback uses the squeezed view or drops the boundary rule; same condition | F13, F18 |
| M16 | seed entries put back in the put-back form | F02 |
| M17 | defang before redaction again | H26, `test_redactor_sees_undefanged_text` |
| M18 | `on_residue` default flipped to `"raise"` | S1-S5 |
| M19 | `LookalikeCopy` caught in `clean` and the text returned | H01 asserts `type(exc) is LookalikeCopy` |
| M20 | fast path takes texts with `*`, `%` or a line break; exists only if the fast path is built | `AKIA**...` row, C08 |
| M21 | approve check removed | `test_approve_refuses_every_withheld_row` |
| M22 | marker refusal removed from the client profile | `test_client_profile_refuses_without_marker` (once per marker) |
| M23 | judge/guardrail treats the notice as clean | `test_judge_refuses_on_notice` |
| M24 | first learning loop (patterns on the views) removed | H21, H37a |
| M25 | seed entries counted as known values | F02b |
| M26 | joined pass gets a fresh mapping instead of the shared one | H30b |
| M27 | `redact_value` total-size rule removed | X03 |
| M28 | start-up canary removed | `test_client_profile_refuses_when_canary_leaks` |
Runner: `tools/mutation_runner.py` if on the base, else a subprocess loop; every mutant restored in a `finally`; tree checked clean at the end. Required: M1-M12, M16, M17, M21, M22, M23, M24, M26. The builder may not merge two mutants without a written reason in the evidence.

## Evidence commands (EVIDENCE RUNNER, a separate agent; raw output to `handover/evidence/P1d/evidence-<n>.md`; line 1 is `git rev-parse HEAD`; no cloud configuration in the environment; heavy jobs through `tools/heavy_slot.py --slots 3 --timeout 2400 --`; gate on pytest's own exit code)
```
uv run --all-extras --group test ruff check
uv run --all-extras --group test ruff format --check
uv run --all-extras --group test bandit -ll -r src
uv run --all-extras --group test pytest -q -rs -m "not live and not perf" tests/test_p1d_rows.py tests/test_p1d_callers.py
uv run --python 3.12 --all-extras --group test pytest -q -rs -m "not live and not perf"
uv run --python 3.13 --all-extras --group test pytest -q -rs -m "not live and not perf"
uv run --all-extras --group test python tests/p1d_mutants.py                      # alone
uv run --all-extras --group test python tools/p1d_corpus.py --seed 1 --kind all   # BS-1, BS-2, BS-3
uv run --all-extras --group test python tools/p1d_cost.py --sizes 3000,30000,120000 --known-counts 10,200,2000 --leaves 5000   # BS-4, alone
git worktree add <tmp> <base-sha>; cp <new test files and fixtures> <tmp>; (cd <tmp> && uv run --all-extras --group test pytest -q tests/test_p1d_rows.py tests/test_p1d_callers.py > fail-before.raw 2>&1)   # fail-before
```
Each command is redirected to its file (`> out 2>&1; rc=$?; tail -n 3 out; echo rc=$rc`).

## Build notes
BN-P1d-1 cite the base SHA; rebase on whatever main holds after P1b merges and rerun fail-before there. BN-P1d-2 correct `gate._rendered`'s docstring (an entity that decodes to a visible character inserts it; H33). BN-P1d-3 the learning pass is a private function; if the hook lint of `test_k5_round11.py` objects, exempt by (file, function) with an assertion that the result is discarded. BN-P1d-4 views outer, values inner. BN-P1d-5 P2d-2 promotes `_healing_views`/`_finish` (with an `extra=` argument) in its own ticket; the count rule has one copy. BN-P1d-6 test texts never say "staging", "dev" or "test" as a stage name (R449); F01 says "demo". BN-P1d-7 remove the `gate._rendered` entry from `vulture_whitelist.py`. BN-P1d-8 per-kind pre-mask only for a kind BS-4 lists. BN-P1d-9 operator review of withheld content is P1d-c (ledger 010). BN-P1d-10 the markdown-it-py comparison is not built. BN-P1d-11 the P1b fix batch (`2034512`, BN-22 in P1.md) is the P1b state BS-0 pins once merged.

## Owner-facing wording (plain words, rule 14)
- CHANGELOG, Upgrade steps: "Text shown to a person or sent to a model: a password, key or e-mail address written with formatting characters inside it (bold or italic markers, a terminal colour code, a backspace, an accent mark, look-alike letters, a line break) is no longer shown. For keys that start with AKIA or ASIA the same holds in another letter case or with one extra character such as `&` or `.`. An approval card for such a request is posted once without buttons and cannot be approved; an operator log line says why. Text sent to a model is replaced by a short notice, and so is any text longer than a stated limit (the limit is a first estimate, not yet measured). E-mail addresses and internal host names in approval cards are now replaced by placeholders (before, they were shown with `[.]` in place of each dot). A password that contains `&` is now hidden up to the next space. The client profile does not start until three fixes have landed. Not covered: a secret that no pattern recognises and that is not already known (a plain password with no key word before it), values shorter than a stated length, and secrets of other key kinds written in another letter case or with an extra character."
- For the owner's status message: "We found a gap where a key, password or e-mail address written with formatting characters inside it could be shown on an approval card or sent to the model. The fix is being planned. Until it is merged, such values can be shown, so no real client data goes through this software."

## Ledger rows (`handover/ledger.md`; severity by the author, the lead confirms; each row names the marker that closes its gate)
| id | package / topic | severity | summary | status |
|---|---|---|---|---|
| BL-core-p1d-001 | P1d | BLOCKER | `clean` and `redact_text` show a key split by markers, escapes, controls, accents, look-alikes, and a known value in another case or split (H01-H25, S13) | OPEN |
| BL-core-p1d-002 | P1d | BLOCKER | `clean` never masks e-mail and internal hosts (defang before redaction, H26-H28) | OPEN |
| BL-core-p1d-003 | P1d | MAJOR | `SlackChannel._blocks` second `redact_text` outside the check; a withheld request must not be approvable, approve repeats `clean` (H30, H40) | OPEN |
| BL-core-p1d-004 | P1d | BLOCKER | the same split key passes every model producer (S1-S5, S13) | OPEN |
| BL-core-p1d-005 | P2d-2 | MAJOR | handed-out secret echoed in another case or with markers (S6 only); same hard dependency as P1d; closes with `P2D2_APPLIED` | OPEN (hand-over) |
| BL-core-p1d-006 | P1d-b | MAJOR | `k1b.redaction.sensitive` misses disguised key names (S11); same hard dependency; closes with `P1DB_APPLIED` | OPEN (hand-over) |
| BL-core-p1d-007 | P1d | MAJOR | SECRET value ends at `&` (H34) | OPEN |
| BL-core-p1d-008 | P1d | MAJOR | glued, dotted or `&`-inserted key passes (H33, H35) | OPEN |
| BL-core-p1d-009 | P1d-b | MINOR | `receiver.log_message` logs a callback URL unredacted (S16); closes with `P1DB_APPLIED` | OPEN (hand-over) |
| BL-core-p1d-010 | P1d-c | MAJOR | no way for an operator to review the content of a withheld request (BN-P1d-9) | OPEN (hand-over) |
The lead's cilint row `BL-hadavin-sdk-cilint-001` (ORDER 146) is the parent of 001 to 004; the lead confirms the link.

## EGM steps, in order (R374, rule 13)
(1) brainstorm: not run, revision 1 is the brief; (2) draft: revision 5 (`egm:egm-draft`, 2026-11-09); (3) plan review round 5: fresh `egm-design`, `egm-implementation-readiness`, `egm-zoom-out`, given this ticket, the sibling report and the round-4 resolve only; (4) `egm:egm-resolve`; repeat (3)-(4) until a round finds no blocker or major (redaction path, no cap); (5) build after P1b merges; (6) EVIDENCE RUNNER; (7) result review by `egm:*` reviewers; (8) resolve, repeat until clean; (9) `egm:egm-drift-report`.

## Slot needs (rule 17)
Build iterations: only the new test files and the clean-related files (1-2 minutes). Final head, once: full suite on 3.12 and 3.13 (2 slots), the mutant run (1 slot, alone with at most the other-Python suite), BS timing (1 slot, ALONE). Real clock: build 10-14 hours, evidence 1-2 hours, each review round 1-2 hours. P2d-2 and P5c also read `channel.py` (a rebase conflict, no slot conflict). P1d is first in the build queue after the P1b fix batch and blocks the pilot merge of P1b/PR 63.

## OPEN QUESTIONS for the lead (only what ORDER 165 to 168 did not answer; each has a default applied in this revision)
1. **Gate shape (default applied):** the client profile refuses to start until three markers exist (`P1D_APPLIED`, `P2D2_APPLIED`, `P1DB_APPLIED`) plus a start-up canary, so P1d alone does not open it. Confirm, or say the other two stay process rules held by the lead.
2. **Audit record (default applied):** a withheld leaf in a stored tool input keeps only the fixed notice; reason, source and character count are in the operator log; no digest. Say if a size and a digest of the withheld text should also be stored (a digest can help an offline guess of a short secret).

## UNVERIFIED (not read or run in revision 5)
Every V number; the 5 baseline failures' cause; `TN_MIN`; whether `scan_holds` folds look-alikes by itself; `undo`'s decode depth; the existing deny, expiry and approve functions and what `requests.py` stores; whether `redact_text` updates `mapping` in place; the match loop for `_find_matches`; the caller table beyond the sibling report; `REDACT_BUDGET_S`; H29a's base result; H37's kind; the put-back wording against the frozen note; the effect of the digit rule; the BS results; the standard section numbers; Python 3.13; whether `vulture_whitelist.py` and `tools/mutation_runner.py` have reached the base; `textnorm._scan_key` was read once on the P1b fix-branch head and the fix batch `2034512` was not re-read for it.

## Rules cited
R233 (redaction fails closed), R337 (class-level fixes), R363 (no single dependency), R374 (EGM order), R447, R448 (CODE LAST, rung table), R449 (stage names), R450 (research and licence gate); studio preamble rules 3, 5, 6, 7, 12, 13, 14, 17, 19, 20, 21.

## Revision log
Rev 1 (2026-11-07): author draft without the skill. Rev 2 (2026-11-09): round-1 reviews and ORDER 165. Rev 3 (2026-11-09): round-2 reviews and ORDER 166 (no slices, fixed-order pipeline, private helpers, model path never raises, caller table, existing-route operator decision, short values, digit rule, S11/S16 to P1d-b, fixtures file). Rev 4 (2026-11-09): round-3 reviews, `round3-resolve.md` G1-G22 and ORDER 167 (`scan_holds` scan key read, R1; one operator design; pseudocode; constants; catch-all; S13 into P1d, S6 to P2d-2; marker plus client-profile refusal; 26 mutants). Rev 5 (2026-11-09): round-4 reviews (design 1B/8M, readiness 3B/19M, zoom-out 5M), `round4-resolve.md` G1-G17 and ORDER 168: approve path calls the same `clean` (one mechanism, parametrised test, stop-rule bit); pipeline cut to five views (`b2` dropped, in-code assert replaced by a test), fast path not built unless BS-4 needs it; floor and cap are config with ranges, cap source "unmeasured placeholder", floor independent of `TN_MIN` with three zones; `undo(shown)` forms dropped (PB-ENC stop rule); one case-insensitive squeezed pass, M7/M8 equivalent pair merged, digit rule and class split; `_find_matches` named; `_withhold` the only logger with a context; joined pass shares the mapping (H30b, M26); three markers plus start-up canary; `redact_value` total-size rule (X03) and stored leaf = notice only; every row has a group, entry point and literal, new-surface sentinel helper, mutants renumbered (28, two conditional pairs) with `test_mutant_ids_exist`; exact evidence commands; defaults for the two remaining questions; BS-2 failure = HELD. One deviation from the resolve: H29b is fixed as **fb**, not pb (the sweep is literal, so the base shows the second copy). `defang_text` stays public (CONTEST of zoom-out N-4: `clean` is in another module).
