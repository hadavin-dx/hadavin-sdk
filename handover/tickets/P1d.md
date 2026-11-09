# Package ticket P1d: a secret split by formatting (Markdown markers, an HTML entity, a terminal escape, a control character, a look-alike letter, another letter case) is shown by approval cards (`approvals.channel.clean`) and sent to the model by `runmap.redact_text`. DRAFT revision 8 (plan review round 8 not yet run)

**Why this ticket is over 250 lines (template rule):** the row tables, the caller table and the mutation table are the specification the builder tests against. Keeping them here is the author's choice for the fail-before method (every row is a test id). It is not required by any order: rev 7 cited "lead order 146 2(a)" for this, and that was wrong, because 146 2(a) asks only for the rung table and the class (round-7 RS-3). About 95 lines are rows, 55 mutants, 40 pseudocode. History: `handover/reviews/P1d/revision-log.md` (revisions 1-7) and the short log at the end.
**Status (2026-11-09 UTC; IST = UTC+5:30):** text only. No code, no pull request. **Split (ORDER 177):** the defang order and `&` (rows H26, H27, H34, H36; ledger 002, 007) are now **P1d-a** (`handover/tickets/P1d-a.md`, ships first); the AWS-style learning rule with its HELD gate (rows H32, H33, H35, the AWS-rule rows, BS-2's gate; ledger 008) is **P1d-learn**; markers, floor check and canaries are **P1d-gate**. This ticket keeps the views, the learning pass of the redactor's own patterns, the residue rule, the card path, the approve path and the model path. Facts are V (revision-1 probes, not re-run), FR/CF (read), RS (round-7 resolve: read or probed on `core/cloud-handover`, no P1b), P8 (probes for this revision, `handover/evidence/P1d/rev8-probes/`). UNVERIFIED items are read or measured by the step named beside them. Marker: CODE-LAST v1.

## Lead rulings this revision implements (ORDER 165-168, 173, 176, 177, 178)
- 165: the fix is inside `runmap.redact_text` (one choke point, model path included); a withheld card is a finished state (posted once, operator log line, visible reason); P1d is a HARD DEPENDENCY of any pilot or prod merge of P1b or PR 63.
- 166: the model path withholds by default, logs, never raises; operator route = the existing `card_too_long` route (CF4); the exact fallback for short values only with `coverage=exact_only` recorded and strict mode still refusing.
- 167: P1b exposes the minimum scan length and pins the `scan_holds` error classes; one deterministic size limit, withhold above it, no NEW text slices.
- 168, 173, 176: the 30,000 cap is config with a validated range and the source **unmeasured placeholder**; a document above it is refused up front as `document_too_large` (176 N-1 (a)); rows 005, 006, 009, 010 stay OPEN under their own topics.
- 177: split as above; HELD attaches to P1d-learn, not to P1d; keep 4 markers (plus the fifth, DEFAULT 4); a withheld leaf = the fixed notice only (no size, no digest); one canary per failure class (P1d-gate); **keep `redact_bounded` for tool results until measured; the 30,000 cap applies only to documents on the model path.**
- 178 (q389 P1d-b/c): the withheld card does not say "or deny it"; it points the operator to the read-only `approvals show <run id>` (P1d-c, through the choke point).
**DEFAULT PENDING LEAD** (applied; the lead may overrule): (1) tool results up to `MAX_REDACT_CHARS` are checked under the existing time limit `REDACT_BUDGET_S`; when it fires the result is withheld (reason `size`, R233); BS-4 reports the size at which that starts; nothing is deleted. (2) Plan round 8 covers only the changed sections (G2, G3, G4, G5, G6 of round 7) with `egm-design` + `egm-implementation-readiness` in parallel; at 0 blockers the plan freezes and every remaining major becomes a build-time ledger row with a BS-0 STOP rule; result rounds stay uncapped. (3) The right-boundary limit of the AWS-style rule is accepted as a stated limit (P1d-learn N4, and the client-facing limits). (4) Names P1d-a, P1d-learn, P1d-gate, P1d; merge order P1d-a, P1d, P1d-gate, P1d-learn; the fifth marker `P1DL_APPLIED`.

## Words used (defined once; one word keeps one meaning)
- **Choke point** = `guard/runmap.py::redact_text`. Every model-bound text, log text, tool result and approval card goes through it.
- **Raw input** `r` = `fits_after_nfkc(_clean(text))`, BEFORE `neutralise`. **Pass-one text** `t` = `fits_after_nfkc(neutralise(r))` (or `r` when no `neutralise` is given): what the existing first pass redacts. **Shown** = the string `redact_text` would return.
- **View** = another spelling of a text, used ONLY to learn or to detect, never shown. **Deleting views** of a text x = `Views(v0, a, b1, c, d)` from four cumulative steps (pseudocode): at most five. **Learning views** = b1, c, d of the RAW INPUT (round-7 RS-1: on the card path `neutralise` has already turned every escape into a space). **Residue views** = all five deleting views of the dropped form of `shown`.
- **Seed entries** = placeholders already written in the text (`channel._seeded`, originals starting `"\0seed"`).
- **Known value** = every original in the map passed to `redact_text` after the call's own masking and learning, seed entries excluded, raw length at least `min_key_chars`. Card path: the map is call-local (built from the text, FR2). Model path: the run map (at most `MAX_MAP_ENTRIES` = 2,000), so a value masked in an earlier call is known in every later call.
- **Every-copy kind** / **standalone kind**: the sweep's own rule (`redact.py:11`, `_Redactor.sweep` `1011-1050`): every copy of a secret kind is masked, but only standalone copies (no letter or digit on either side) of an identifier kind (names, e-mail, host, ids). BS-0 (i) lists the two kind sets.
- **Learning pass** = the redactor's own patterns run on the learning views (output thrown away; only found originals kept). P1d-learn adds its rule here. **Learned value** = an original the learning pass adds that was not in the map before.
- **Dropped form** = shown with each genuine placeholder (in the map, not a seed) replaced by one space. **Put-back form** = shown with each genuine placeholder replaced by `" " + original + " "`.
- **Residue rule** = after masking, no known value may be readable in the residue views (per kind, below), and the put-back count test must pass. If any part fails, the text is **withheld**.
- **Residue finder** = one combined pattern of the needles of every known every-copy value with no script, built once per map version.
- **Withheld** = `redact_text` does not return the text. Default (`on_residue="withhold"`): it returns the fixed sentence `WITHHELD_NOTICE` and writes one operator log line. With `on_residue="raise"` (card callers only) it raises `runmap.LookalikeCopy`, for every reason (residue, size, error). The model path never raises.
- **ref** = the run id (format `run-` + 32 hex characters, `models.py:23-24, 91`), written in the operator log line; the same id P1d-c's `approvals show` takes.
- **KV twin** of a row = the same insertion placed inside a copy of a KNOWN value: the text first holds `password=<SV>` (SV enters the map), then a copy of SV carrying the row's insertion. **Carrier row** = a row whose insertion needs a step that changes letters or digits (decode, deleting an escape's payload such as `0m`).
- **Client profile** = stage `pilot` or `prod` (`deferred.LIVE`). **Operator** = the person who runs the deployment for the client.
- **Test legend:** fb = must FAIL on the base (post-P1d-a, post-P1b main); pb = passes on the base, output unchanged; ow = accepted over-withhold, counted separately; measure = reported, not claimed; new-surface = needs a name absent on the base; entry card = `clean` (raise mode), summary = a plan input through `Approvals.request`/`summary`, model = `redact_text` default.

## Facts
- V1: `clean` gives the same output on main, P1b and `core/ci-lint-set` for every row. V2: `gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `_RENDERED_MARKUP` exist (`gate.py:197-226`), nothing calls them. V3: `gate._rendered`'s docstring is wrong about `AKIA&amp;...` (BN-P1d-2). V4: `redact.strip_ansi` puts a space where an escape stood. V5: the redactor's views do not delete markers, escapes or controls and do not fold case for pattern matching; `_sweep` is literal and case-sensitive. V6: `textnorm.scan_holds` holds the key in `key AKIA**IOSFODNN7EXAMPLE** x` and its lower-case copy; raises `ViewTooShort` for `10.0.0.1`. V7: P1d never calls `register_value`. V8: running the whole redactor BEFORE the gate broke two fuzz tests; only the defang moves (P1d-a). V9 (prototype cost, 4 shared CPUs, five views, per-value scan, no skips): 3,000 chars 0.21 s; 30,000 2.69 s; 120,000 12.9 s.
- **FR1 (decisive):** `textnorm._scan_key` (`origin/core/P1b-fixwip`, `textnorm.py:1088-1093`) keeps only letters and digits. UNVERIFIED after P1b's fix batch (`2034512`); BS-0 re-reads (STOP rule); `test_scan_holds_ignores_non_alphanumerics` pins it.
- FR2: `MAX_REDACT_CHARS = MAX_DOCUMENT_BYTES = 262_144`, `REDACT_BUDGET_S = 6.0`, `MAX_MAP_ENTRIES = 2000`; `redact_text` raises `InputTooLarge` on the input cap (`_within_cap`) and on the budget, writes the caller's map only at the end (`runmap.py:417-479`). `redact_value` raises `InputTooLarge` when `_chars(value)` (NFKD-expanded, dict keys included) is over `MAX_REDACT_CHARS` (`runmap.py:521-551`). `clean` builds call-local maps (`channel.py:18-39`).
- FR3: `requests.summary` (`requests.py:33-51`) returns `clean(...)` and on `RedactionError` falls back to a "too large" text WITH buttons. `Approvals.request` (`requests.py:95-110`) computes `summary(plan, self.detector)`, saves, then `_send`s. `_send` (`112-130`) leaves `sent_at` empty on failure; `resend_unsent` (`132-144`) resends those. `decide` (`146-180`) checks `not_pending`, `old_step`, `step_expired`, then `plan_hash_mismatch`. `store.get_plan(run_id)` exists (`protocol.py:69`); `Plan.hash()` (`models.py:134`). `app.request_approval` (`app.py:194-200`) refuses a too-long summary BEFORE anything is saved (`card_too_long`), and `agent_loop.py:717-720` turns that into `NEEDS_PERSON`. `SlackChannel._blocks` (`slack_channel.py:67-121`) re-redacts `withhold_commands(req.summary)` and adds Approve/Reject unless `approver_ids is None`.
- FR4: `withhold_commands` replaces to the end of the line. `cards.py:14` imports from `requests.py`. `cards.Card(text, blocks, display_hash = sha256_hex(text))` (`cards.py:27-31, 58-63`). The AWS pattern is `\b(?:AKIA|ASIA|...)[A-Za-z0-9_\-]{8,}\b` (`redact.py:195`). `EvidenceSettings.max_document_bytes` has `le=MAX_REDACT_CHARS`; `agent_loop.py:354-386` refuses a larger document as `document_too_large` and more than `MAX_MAP_ENTRIES` values as `document_too_complex` (both `NEEDS_PERSON`). The start function is `app.build`.
- FR5 (P1b at `2034512`): `TN_MIN` = 4 (`TEXTNORM_MIN_DIGIT_CHARS` 6 for digits only); public `scan_needles`, `scan_keyset`, `scan_views_no_value`, `value_scripts`.
- **RS-1 (probe, this branch):** after the card neutraliser, `AKIA` + ESC + `[0m` + `IOSF...` is `AKIA IOSF...`; ESC + `I` eats the `I` (H14: 19 of 20 characters). So learning must read the raw input.
- **RS-4 (probe through `clean`, this branch, not the BS-0 (l) run):** H07c, H10, H15a, C03, C04 leak (fb); H15b and H17a-j are masked (pb). Not probed: H29a, joined-forms-placeholder, PB-ENC.
- **RS-5 (read):** `redact_text` already redacts `canonical`, the JSON-unescaped view and `undo(text)` and returns the redacted VIEW when the map grows (`runmap.py:362, 466-471`).
- **P8-1:** with P1d-a's prototype, H34b (`password=<SV_A>&amp;<SV_B>`) is masked whole by that existing second pass (`rows-proto-query.txt`), so on the post-P1d-a base it is pb and no longer the killer of `_edge_run` (M29).

## Merge-order preconditions (BS-0 gates)
1. P1a (PR 63), P1b and **P1d-a** merged. The fail-before base is that main. A P1d test file imports `textnorm` only inside test functions.
2. P1b exposes `TN_MIN` and pins `ViewTooShort`, `EmptyView`, `TextnormError` by a test (ORDER 167 item 1). BS-0 reads them, `_value_needles` and `_all_views`; a difference from V6/FR1/FR4/FR5 = STOP.
3. `tools/heavy_slot.py`, `tools/mutation_runner.py`, `vulture_whitelist.py`: rebase onto the branch that has them before the build starts; do not recreate them (ORDER 176).
4. The baseline failures are listed by test id and cause and fixed here or recorded as environment with an owner before "done".
5. `P1D_APPLIED = True` is added to `guard/runmap.py`; it means "P1d-a and P1d merged". The start gate itself is P1d-gate.

## RUNG TABLE (R447, R448, R450; scale of 2026-11-06: 1 no-code, 2 own core modules, 3 existing free tools, 4 free libraries, 5 own new code last)
Gate: core SDK change, no client, no fee, no new dependency. Rung 1 closed (R447, inside the choke point). Rung 3 closed (a model feature cannot be exact and runs after the text left). **Guarantee:** **exact** = holds for every value in the named set, up to the size limit, with a test; **best effort** = holds for the tested cases; **detection-only**. An unknown secret with no pattern is OUT of the guarantee.
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| views, decode, fold | read the text as a renderer, terminal or person shows it | 2 (`gate` view primitives and `channel._TAGS` moved to `guard/_views.py`, `redact._ANSI`, `runmap.undo`, `textnorm.fold`) | V2, V4, FR1 | one function, fixed order, built from the same primitives; backspace applied as a terminal does | exact on the listed rows up to the limit | CUT-TO-CONFIG+GLUE |
| Markdown library | rendered view | 4: `markdown-it-py` (`gate.py:72`) | CommonMark only, no Slack `*bold*`; not built | nothing | n/a | CUT |
| existing second pass | decode view a | 2 (RS-5) | RS-5 | nothing new: a is not learned on (round-7 G5) | as today | CUT (reuse) |
| fold and scan | look-alikes, accents, case, separators | 2 (P1b) | V6, FR1, FR5 | `delete_noise`, the exact fallback for short scan keys | exact for P1b's coverage | CUT-TO-CONFIG+GLUE |
| residue finder | check thousands of known values in one pass | 2 (`redact._trie`, `_trie_regex`, `_compile_uncached`, `RunMap.redact_cache`; P1b needles) | FR4 | one finder per map version | exact; `test_finder_equals_scan_holds` | CUT-TO-CONFIG+GLUE |
| learning pass | find an UNKNOWN value the patterns see only in a view | 2 (the redactor's patterns on more views) | UNVERIFIED; BS-0 (p), BS-2 | three learning views | **best effort**: rows plus the made-up BS-2 corpus | KEEP-CODE (small) |
| residue rule | decide whether a known value is readable | 4: detect-secrets, gitleaks, Presidio find SHAPES; none compares a text with OUR run map | not run (UNVERIFIED); test idea: KV twins | redaction before a person (R447) | exact for known values up to the limit | KEEP-CODE, about 90 lines (estimate) |
| fail closed, bounded cost | never return an unchecked text | 2 (`InputTooLarge`, `REDACT_BUDGET_S`, the scan guard, `document_too_large`) | V9, FR2 | one catch-all, one work bound | exact (the refusal) | KEEP-CODE, about 30 lines |
| settings | validated cap, floor, work bound, learn limit | 2 (`scrub_settings.ScrubSettings` pattern) | FR4 | four fields | exact (range refusal) | CUT-TO-CONFIG+GLUE |
| approve re-check and no-save route | a withheld card is never approvable | 2 (`card_too_long` route, `get_plan`, `decide`) | FR3 | one re-check from the stored plan | exact (same text, same map) | CUT-TO-CONFIG+GLUE |
**80 percent (R448):** needs: read as rendered; decode; fold; unknown shapes in other views; decide what is readable; fail closed. Rungs 2 and 4 meet three of six. **Cost (estimate):** build 10-14 agent-hours plus uncapped result rounds; 0 fees, 0 tokens, 0 new dependency.

## Goals and Non-Goals
**Goals.** (G1) No known value is readable in any text `redact_text` returns or any card `clean` returns, for the families in the rows, up to the size limit. (G2) One implementation at the choke point; `clean`, `card_text`, documents, tool results, tool errors, logs and `redact_value` get it without a new call site (enforced by `test_redactor_entry_only_in_runmap`). (G3) A text that cannot be cleared is withheld in a stated way (caller table); a request whose card is withheld is never saved and never approvable. (G4) False-withhold rates measured separately (BS-1, BS-3).
**Non-Goals.** (N1) An unknown secret with no pattern. (N2) What a person types after the card is posted. (N3) S6 `tools._secret_forms`: P2d-2. (N4) A new endpoint or console (P1d-c's `approvals show` is its own package). (N5) Documents above `max_text_chars` are refused as `document_too_large`; a text above `MAX_REDACT_CHARS` or past the time limit is withheld. (N6) Unknown secrets of a token kind other than AKIA/ASIA in another letter case or with `.`, `&` or a line break inserted (H37d-e measure it). (N7) Unknown AKIA/ASIA keys in lower case or with one gap character: P1d-learn (until it merges, P1d-gate keeps the client profile closed). (N8) The defang order and `&`: P1d-a.

## Alternatives considered
- **A1 Heal and show.** Rejected for both paths: fold and case views change characters, so a card would differ from the request approved; ORDER 165/166 rule withhold. Trigger: BS-3 above its ceiling; then A1 for deletion-only views.
- **A2 Offset-mapped masking.** Rejected (span tracking inside frozen `textnorm`). Therefore a value found only in a view withholds.
- **A3** escape the markers in the shown text; **A4** check only in `clean`; **A5** pre-mask only e-mail and host; **A6** a library; **A7** text slices: rejected as in rev 7 (revision log).
- **A8 Fixed-point loop for views.** Rejected; one bounded second round of a then b1 on view d only if a KV-twin row of C01-C10 fails on one pass (view bound then 7).
- **A9 Save the withheld request with a stored bit.** Rejected (migration 0006, no deny route). Chosen: never save it, plus a re-check from the stored plan for rows stored earlier.
- **A10 Let views b1, c, d join the existing second pass (RS-5).** Rejected, with reasons (round-7 G5): that loop SHOWS the whole view it redacted; d deletes every line break, backtick and `*` of the whole card or log line; c changes letters (A1); b1 deletes tags and escapes from the whole text; A2 forbids a per-region splice. View a already IS that loop's `undo` view, so it is not learned on again.
- **A11** extra view b2: dropped unless a row needs it (BS-0 (m)). **A12** lower `MAX_REDACT_CHARS` as the cap: rejected. **A13** per-value `scan_holds` against the run map: rejected (cost). **A15** one global fast path: rejected.
- **A16 Approve-path backstop by learning only** (round-7 G3 option 2). Rejected: it cannot see a known value that leaked before P1d. Chosen: re-check from the stored raw plan (same text, same map) and no learning in the channels' re-checks.
- **A17 Keep learned values of a withheld text out of the map** (round-7 D-M6). Rejected: committing them is what keeps a later copy in an unlearnable shape known (S13-2, MAP-1). A per-call limit is added instead.
- **Chosen:** fixed-order views; learning on the raw input; a value found only in a view withholds; the residue rule per kind with a combined finder; withhold by default; raise only for cards; a withheld card never becomes a saved request; the approve path re-checks from the stored plan.

## Risks and mitigations
- RK1 False withholds. Learned values withhold (unknown, found only in a view); known values withhold only when readable in a residue view, per kind; BS-1 (model, real-looking maps of 10, 200, 2,000 values) and BS-3 (cards) measure; guard rows F01-F21.
- RK2 Cost. `max_work`, `REDACT_BUDGET_S`, the finder, per-step skips; BS-0 (p) and BS-4. RK2b (DEFAULT 1): a tool result near `MAX_REDACT_CHARS` may pass the time limit and be withheld (V9: 12.9 s at 120,000 characters before the finder); BS-4 reports the size where that starts.
- RK3 The learning pass false-learns. BS-2 measures the pattern-on-views pass with ceiling 0; any false learn is fixed by dropping that view or kind (commit rule) or goes to the lead (OPEN QUESTION 2). The AWS-style rule's HELD gate is in P1d-learn.
- RK4 A model-path text disappears: the notice is visible; a run is never ended by a withhold.
- RK6 P1b changes under P1d: BS-0 pins P1b; P1d calls nothing private of `textnorm`.
- RK8 Hostile text forces a withhold: fail-safe, accepted; a stored withheld leaf is the fixed notice only (ORDER 177).
- RK9 `redact_value` stores the notice in place of a leaf; it never raises in default mode; BS-0 (e) reads hash readers.
- RK10 A judge, vendor screen, eval or grounding check that read "clean" for a notice would fail open: caller table.
- RK11 Log abuse: `source` from a fixed set; `ref` logged only if it matches `run-[0-9a-f]{32}`, else `?`; a thread-local guard stops re-entry from a log filter.
- RK12 Documents between 30,001 and 262,144 characters, accepted today, are refused as `document_too_large` (ORDER 176 N-1 (a)); in CHANGELOG.
- RK13 Approve-path cost: one card redaction per decision click (BS-4; Slack wants a reply within 3 s).

## Settings (validated config; no literal in code)
New `src/hadavin_sdk/redaction_settings.py` (pattern of `scrub_settings.py`, importable from `guard` without `config.py`): frozen `RedactionSettings`, defaults in `defaults.py`, key path `evidence.redaction.*`; out of range = pydantic error, turned into `ConfigError` by `load_config`. `runmap._SETTINGS` set once by `runmap.apply_settings(s)` from `app.build`. Tests `test_constants_out_of_range_refused` (each field, both ends), `test_apply_settings_used_by_redact_text`; an autouse fixture restores `_SETTINGS`.
- `max_text_chars` (`P1D_MAX_TEXT_CHARS`): start **30000**, range 1,000 to `MAX_REDACT_CHARS` (`le=`, round-7 R-M2). **Source: unmeasured placeholder.** **Documents only (ORDER 177):** `EvidenceSettings` gets a validator `max_document_bytes <= redaction.max_text_chars`, and the default of `max_document_bytes` becomes this value, so a longer document is refused as `document_too_large` before it is read. `redact_text` does NOT check it; its own limit stays `MAX_REDACT_CHARS` (existing `_within_cap`). `redact_bounded`, `drop_margin`, `CUT_MARGIN`, `defaults.cut_margin`, the producers row "tool error reason" and `CHOKE_FAMILY` stay unchanged (ORDER 177; nothing deleted). Tests `test_document_limit_above_cap_refused`, `test_document_over_cap_is_document_too_large`.
- `min_key_chars` (`P1D_MIN_KEY_CHARS`): start **8**, range 4 to 16 (P1d-gate refuses above 8 in the client profile).
- `max_work` (`P1D_MAX_WORK`) = (number of known values checked one by one, those with a script) x (total length of the residue views); start **50,000,000**, range 1,000,000 to 1,000,000,000, **source: unmeasured placeholder**; above it: withheld, reason `size`.
- `max_learned_per_call` (`P1D_MAX_LEARNED`): start **16**, range 1 to 256, **source: unmeasured placeholder** (round-7 G9); above it: withheld, reason `size`, nothing learned committed. More than `MAX_MAP_ENTRIES` values in a run already ends it `NEEDS_PERSON document_too_complex` (FR4).
- **Length zones on SCAN-KEY length:** raw length below `min_key_chars`: skipped (outside the guarantee, CHANGELOG); scan key shorter than `TN_MIN` (6 for digits only) or empty: the exact fallback; otherwise the finder or `scan_holds`.
- New names: `WITHHELD_NOTICE`, `LookalikeCopy`, `is_withheld`, `contains_notice`, `apply_settings`, `P1D_APPLIED`, `channel.card_text`, `channel.CARD_WITHHELD_TEXT`, `channel.card_withheld_text`, `cards.withheld_card`, `Approvals._card_check`, `redact.find_matches`, `redact.add_known`. Reasons: `residue | size | error`.

## The algorithm (pseudocode; no code)
```
redact_text(text, mapping, neutralise=None, *, on_residue="withhold", source="", ref="", _learn=True):
  try:
    ctx = (_checked_source(source), _safe_id(ref), len(text), on_residue)
    r = fits_after_nfkc(_clean(text))                          # raw input (existing first step); _within_cap(text) first
    t, shown, work = <the existing redaction, unchanged, incl. neutralise and the second pass, into a WORK copy>
    if _learn:                                                 # private flag; False only in channel re-checks (G3)
      before = set(originals(work))
      _learn_unknown(_healing_views(r), work)                  # RAW input, before neutralise (RS-1)
      learned = set(originals(work)) - before
      if len(learned) > _SETTINGS.max_learned_per_call: return _withhold("size", ctx, mapping)
      if learned: return _withhold("residue", ctx, mapping, work=work)   # found only in a view (A2; RS-1 rule 2)
    return _finish(ctx, shown, mapping, work)
  except LookalikeCopy: raise
  except InputTooLarge: return _withhold("size", ...)          # input cap, budget, view cap (existing raises)
  except Exception as exc:                                     # TooDeep, TextnormError, RecursionError, MemoryError, bugs
    return _withhold("error", ..., exc=type(exc).__name__)      # class name only

_withhold(reason, ctx, mapping, *, work=None, ...):            # the ONLY place that logs
  one WARNING line (re-entrancy guard RK11)
  model path and reason residue: mapping updated from `work` (masked AND learned values; MAP-1)
  reasons size/error, or raise mode: mapping unchanged (MAP-2)
  raise mode: raise LookalikeCopy (from None); else return WITHHELD_NOTICE

_healing_views(x) -> Views:   # CUMULATIVE; a skipped step is the identity; skips are exact (test_skips_are_exact)
  v0 = x
  a  = undo(v0)             only if the existing scan guard is true      # the second pass's own decode (RS-5)
  b1 = delete_carriers(a)   only if a holds "<", ESC, a C1 character or BS
       # _views.TAG.sub("", a); then each BS deletes itself and the character before it (overstrike, ECMA-48 8.3.5);
       # then ANSI/CSI/OSC/C1/lone ESC deleted
  c  = textnorm.fold(b1)    only if b1 is not ASCII
  d  = delete_noise(c)      only if c holds * ~ backtick, a control, CR, LF, U+2028, U+2029    # underscore kept

_learn_unknown(views, work):
  for v in (views.b1, views.c, views.d):                       # not v0 (pass one) and not a (the second pass)
    for kind, value in find_matches(v, kinds=SECRET_KINDS - {HIGHENTROPY, CREDITCARD, IBAN}):
      redact.add_known(work, kind, value)
  # P1d-learn adds _learn_aws(views.d) here

_finish(ctx, shown, mapping, work):
  known = {o in originals(work): not seed(o) and len(o) >= _SETTINGS.min_key_chars}
  if not known: commit work; return shown
  dropped = shown with each genuine placeholder replaced by " "
  rv = _healing_views(dropped)
  every, single = split known by kind (every-copy / standalone)
  scripted = {k in every with textnorm.value_scripts(k) non-empty}
  if len(scripted) * sum(len(v) for v in rv.all()) > _SETTINGS.max_work: return _withhold("size", ...)
  finder = residue finder of (every - scripted), cached in work's redact_cache under the map version
  for v in rv.all():                                            # views OUTER (BN-P1d-4)
    for w in textnorm.scan_views_no_value(v):
      if finder.search(w): return _withhold("residue", ctx, mapping, work=work)
    with textnorm.scan_cache():
      for k in scripted: if _holds(v, k): return _withhold("residue", ...)
    for k in every with a short scan key: if exact_fallback(v, k): return _withhold("residue", ...)
    for k in single: if standalone_copy(v, k): return _withhold("residue", ...)   # no squeeze views for these
  p = put_back(shown)                                           # conditional, BS-0 (q)
  for k in known: if count(k, p) > e(k): return _withhold("residue", ...)
  commit work to mapping (in place, FR2); return shown
```
- **Residue finder:** for each every-copy known value with no script, its needles = `textnorm.scan_needles(v)` plus the keys of `scan_keyset(v)` that reach `TN_MIN`; one trie-regex from `redact._trie`, `_trie_regex`, `_compile_uncached` (not `re`'s cache, R371). `test_finder_equals_scan_holds` (property): a finder hit for (text, v) iff `scan_holds(text=text, value=v)`.
- **`standalone_copy(v, k)`** (round-7 G4) = k occurs in v case- and accent-insensitively (the fold below) with no letter or digit on either side. So `ChristopherSmith`, `user_id=Christopher123`, `Christophersen` and F21 are not withheld for a known `Christopher` / `anna.m@example.org`.
- **`_holds(v, k)`** = `textnorm.scan_holds(text=v, value=k)`; on `ViewTooShort`/`EmptyView` the exact fallback.
- **`_edge_run`** (an every-copy known value glued in a decoded view): rev 7's only killer H34b is pb after P1d-a (P8-1), and the finder already finds glued copies (substring of the scan key). It stays only if BS-0 (q) names a row that fails without it; else it is not built and M29 is dropped with that reason.
- **Sweep, case and accent (round-7 G4):** `_Redactor.sweep` gets one pass that compares per character after NFD, base letter if the rest is combining marks, then casefold if that keeps one character; only for originals whose folded form keeps its length. `shown` is NFKC (precomposed), so spans map back one to one, and the copy is masked in place under the original's placeholder with the existing every-copy/standalone rule (`JOSE MULLER` is masked under `José Müller`'s placeholder). A value whose fold changes length keeps the plain case pass; a split copy of it still withholds.
- **Put-back count** (copied from `handover/designs/lookalike-leak.md` section 5 item 3, frozen draft 11): each genuine placeholder replaced by `" " + original + " "` in ONE pass; `count(k, p)` = non-overlapping count of each key of k in each key of p; `e(k)` = the sum over put-back originals O of (O's placeholders put back) x (the SMALLEST count of k's key over `scan_keyset(O)`; empty = 0); `count > e` = residue. It stays only if H34b's replacement row (chosen at BS-0 (q)) or LK-JAMO-PB fails without it; else the test, M10, M38 and LK-JAMO-PB are dropped.
- **The text checked is the text returned:** `_finish` runs on `shown`. P1d-a's `defang_text` only inserts `[` `]` (`test_defang_text_only_inserts_brackets`, P1d-a). `test_returned_card_bytes_pass_the_check`.
- **`find_matches(text, *, kinds=None) -> list[(kind, original)]`:** a throwaway `_Redactor(None)`'s `find` placements in order, without touching any map. `test_find_matches_equals_redact_mapping`.
- **Commit rule for learning views (BS-4):** a view stays in the learning loop only if a named row fails without it.

## Short scan keys (ORDER 166 item 5, ORDER 167)
For a known value whose scan key is shorter than `TN_MIN` (6 for digits only) or empty: (1) **exact fallback**: case-insensitive exact substring search in every residue view, with `(?<![0-9A-Za-z])` before and `(?![0-9A-Za-z])` after the escaped value, each side only when the value's own first or last character is a letter or digit; (2) one INFO line per call that used it: `redaction coverage=exact_only values=%d`; (3) **strict mode unchanged**: P1d never calls `register_value`; `test_strict_mode_still_refuses`. F18: `10.0.0.1` inside `210.0.0.12` is NOT found.

## Refusal behaviour (callers)
**Completeness:** `guard/producers.py` gets `NOTICE_HANDLING` keyed by producer name; a test asserts its keys equal the `PRODUCERS` names. `test_redactor_entry_only_in_runmap` (AST, round-7 G11): calls of `redact`, `_Redactor`, `find_matches`, `add_known` only in `guard/runmap.py` and `redact.py`; an explicit allowlist for the three outside sites (`k1b/redaction.py:177-186`, `tools.py:873`, `agent_loop.py:372`, not re-read; BS-0 (c) confirms), each with its ledger row and marker (P1d-b / P2d-2), removed when the marker lands.
- `WITHHELD_NOTICE` = `(withheld: this text could not be checked safely for secrets)`. `is_withheld(text)` = equality; `contains_notice(text)` = it occurs inside text.
- **Card text (ORDER 178; `approvals/channel.py`, re-exported by `cards.py`):** `CARD_WITHHELD_TEXT` = `cannot be shown safely. It may hold a password, key or e-mail address written with formatting inside it, and it cannot be approved from this card. Ask the sender to send it again without formatting.` Builder `card_withheld_text(run_id=None, inputs=False)` = `This request ` + the constant, then: if `run_id` matches `run-[0-9a-f]{32}` and `getattr(runmap, "P1DC_APPLIED", False)`: ` An operator can see which part caused this with the read-only command: hadavin-sdk approvals show <run_id> --by <your name>`; else if `run_id` matches: ` An operator can find the reason in the operator log under ref <run_id>.`; else ` An operator can find the reason in the operator log.` `inputs=True` puts `Inputs: ` first. The builder text is fixed text plus a checked id: it is NEVER passed through `clean` or `card_text` (`withhold_commands` would remove the command; `test_withheld_card_text_not_recleaned`). `test_card_withheld_text_exact` (all forms, marker on and off). The command syntax is P1d-c's (`P1d-c.md:29`); if P1d-c changes it, this one constant changes with it.
- `cards.withheld_card(run_id) -> Card` (round-7 G13): `text = card_withheld_text(run_id)`, one section block, no actions block, `display_hash = sha256_hex(text)` (the `_card` function), built without `clean`.
- Operator log line (WARNING, logger `hadavin_sdk.guard.runmap`) = `redaction withheld a text: reason=%s source=%s ref=%s chars=%d views=%s known=%s` (+ ` exc=<class name>` for `error`); never content. `source` (fixed set): `card`, `card_joined`, `card_check`, `notify`, `document`, `tool_result`, `tool_error`, `safe_head`, `redact_value`, `judge`, `guardrail`, `eval`, `canary`; anything else `other`.
- **`clean(text, *, ref="", source="card") -> str`:** (1) `text = text.replace("\0", "")`; `mapping = _seeded(text)`; `out = redact_text(text, mapping, neutralise=_neutralise, on_residue="raise", source=source, ref=ref)`. (2) `joined = _TAGS.sub("", text)`; if `joined != text`: `before = _assignment_originals(mapping)` (snapshot BEFORE the second call); add each `_seeded(joined)` entry not in `mapping`; `alt = redact_text(joined, mapping, neutralise=_neutralise, on_residue="raise", source="card_joined", ref=ref)`; if `_assignment_originals(mapping) - before`: `result = alt`; else `result = out`, and if the second call added any non-seed entry, `result = redact_text(out, mapping, on_residue="raise", source="card_joined", ref=ref)`. (3) `return gate.defang_text(result)` (P1d-a).
- **`card_text(summary, *, ref="") -> str`:** the current `_blocks` body moved (`withhold_commands`, seeded map, `redact_text(..., neutralise=_neutralise, on_residue="raise", source="card", ref=ref, _learn=False)`), then `gate.defang_text`. With no known value and no learning it can withhold only for size or error (round-7 G3), so it never false-withholds a saved request. `test_card_text_accepts_every_clean_output` (property: `card_text(clean(x))` never raises when `clean(x)` returned).
- **`Approvals._card_check(req) -> bool`** (round-7 G3): `plan = self.store.get_plan(req.run_id)`; `False` if `plan.hash() != req.plan_hash`; else `summary(plan, None)` in raise mode (`source="card_check"`, `ref=req.run_id`): the same text and the same map as at creation (settings changed since can only make it stricter); `LookalikeCopy` = `False`. No detector, so no model call.
| caller | entry point | on withhold | buttons | pinning test |
|---|---|---|---|---|
| `app.request_approval` (`app.py:194-200`) | `summary` raises | `post_card(cards.withheld_card(plan.run_id))` once; returns `Delivery(ok=False, reason="card_withheld")`; no request saved. Other `card_too_long` sites (`slack_channel.py:164`, `app.py:188, 196`) unchanged | no | `test_withheld_summary_saves_no_request`, `test_withheld_card_posted_once_without_buttons` |
| `agent_loop` (`~719`) | n/a | passes `card_withheld` through: `NEEDS_PERSON` reason `card_withheld` | n/a | `test_run_ends_needs_person_card_withheld` |
| `requests.summary` (`ref = plan.run_id`) | `clean` raises | `except LookalikeCopy: raise` before `except RedactionError` | n/a | `test_summary_lets_lookalikecopy_through` |
| `Approvals.request` | `summary` raises | computed BEFORE `save_approval_request`; nothing saved (`summary` runs twice, here and in `request_approval`: deterministic, cost in BS-4) | n/a | `test_withheld_summary_saves_no_request` |
| `Approvals.decide` (rows stored before P1d) | `_card_check(req)` after `not_pending`/`old_step`/`step_expired`, before the approver checks | audits `error_code="card_withheld"`, returns `(False, "card_withheld")` | n/a | `test_decide_refuses_stored_withheld_summary`, `test_decide_refuses_plan_hash_mismatch_on_check`, `test_decide_check_equals_creation_check` (property over BS-3 cards) |
| `Approvals._send` (and so `resend_unsent`) | `_card_check(req)` first | `self.channel.send(req, approver_ids, withheld=True)`; `sent_at` set after that post succeeds, so no resend loop; the row ends by `sweep` expiry (EXPIRED, not `NEEDS_PERSON`) | no | `test_withheld_send_sets_sent_at_once`, H30b |
| `SlackChannel.send/_blocks/update` | `withheld=True`, or `card_text` raises | section text `card_withheld_text(req.run_id)`; no `actions` block whatever `approver_ids` is | no | `test_h30a`, `test_h30b`, `test_sent_at_only_after_post` |
| `FakeChannel.send` | as Slack | records one send of the builder text | no | `test_h40` |
| channel Protocol `send(req, approver_ids, *, withheld: bool = False)` | n/a | new keyword; BS-0 (n) lists every implementer in `src` and `demos` | n/a | `test_every_channel_accepts_withheld` |
| `cards._card` (`render_shadow` ref `plan.run_id`, `render_abstain` ref `run_id`) | `clean` raises | text `card_withheld_text(run_id)`; label buttons dropped | no | `test_caller_cards` |
| `channel.py:110-111` `notify` | `clean` raises | builder text (no run id) | n/a | `test_caller_notify` |
| model path: `redact_untrusted`, `prepare_output`, `redact_layered`, `error_reason`, `safe_head` | default | returns the notice, logs, never raises | n/a | S1-S5 |
| document producer (`agent_loop.py:354-386`) | `contains_notice(safe_text)` | `document_too_large` (`NEEDS_PERSON`); the notice never goes to the model as a document; the old `except InputTooLarge/TooDeep` stay (round-7 G7, RS-7) | n/a | `test_document_notice_is_document_too_large` |
| tool-result producer | default | the notice is the visible tool result | n/a | S3 |
| JSON tool-result consumer (BS-0 (f)) | n/a | a notice in place of JSON is an error | n/a | `test_tool_result_notice_fails_closed` |
| `redact_value` (stored records, audit, `evidence.py:191`) | default | leaf becomes the notice; `_chars(value) > MAX_REDACT_CHARS` (existing rule): the whole value is the notice | n/a | S5, `test_redact_value_notice`, X03 |
| `guard/judge.py:71`, `guard/bedrock_guardrail.py:98` | `contains_notice(text)` BEFORE the call | `Verdict(flagged=True, score=1.0, backend=..., reason_code="guard_unavailable")` (`judge.py:80-87` precedent); no model or vendor call | n/a | `test_judge_refuses_on_notice`, `test_guardrail_refuses_on_notice` |
| `src/hadavin_sdk/evals.py:63` | `contains_notice(doc_text)` | `raise ConfigError(<the existing message>)` (the `except RedactionError` is no longer reached) | n/a | `test_eval_case_fails_on_notice` |
| `runtime/evidence.py` `validate`, `grounded` | notice in any leaf / the evidence | `Checked(..., "invalid_proposal")`; `grounded` refuses | n/a | `test_validate_invalid_on_notice`, `test_grounded_fails_on_notice` |
**Who can deny a withheld request:** none is saved for new requests; rows stored before P1d expire through `sweep`. The operator reads the cause through P1d-c's `approvals show` (ledger 010, ORDER 173, 178).

## Scope of S11, S16, S6, S13
- S11, S16: **P1d-b** (rows 006, 009, 011, 012; 012 stays BLOCKER, ORDER 178), marker `P1DB_APPLIED`. S6: **P2d-2** (row 005), marker `P2D2_APPLIED`; P1d owns `LookalikeCopy` and `WITHHELD_NOTICE`; P2d-2 feeds `_withhold`. P1d-c (row 010): marker `P1DC_APPLIED`. All markers are checked by **P1d-gate**.
- S13 (`_sweep`): **in P1d** (case- and accent-insensitive sweep pass plus the cumulative known value); rows H22-H24, S13-1..3.

## Template fields
- **Package id and name:** P1d, "split secrets at the choke point". Branch `core/P1d` from main after P1a, P1b and P1d-a merge. **Path class:** redaction AND security; extended review (no round cap) for result rounds; plan rounds per DEFAULT 2.
- **Class (R337):** "a value is matched only in the spelling as written, while a reader or renderer reads another spelling". Standards (from memory; read date UNVERIFIED, R450): CommonMark 0.31 sections 6.2, 6.1, 2.5; ECMA-48 sections 5.4, 8.3 (8.3.5 backspace); Unicode UAX #15, UTS #39.
- **Source of the code:** our own code only. **Neutral default / alternative:** no vendor; A1 has its trigger; `on_residue` selects withhold or raise.
- **Race / process tests:** none (scan cache per call; finder per map version; thread-local re-entrancy guard, `test_log_filter_reentry`).
- **Files:**
  - create `guard/_views.py`: `TAG = re.compile(r"<!--.*?-->|<(?![A-Z][A-Z0-9]*_\d+>)[^<>]{0,200}>", re.DOTALL)`, `RENDERED_MARKUP`, `ANSI_AS_TEXT`, `views`, `rendered` moved from `gate`, `redact._ANSI`'s pattern; `channel._TAGS` built from `TAG`; `guard` never imports from `approvals`. Create `redaction_settings.py`.
  - change `guard/runmap.py` (`redact_text`, `LookalikeCopy`, `WITHHELD_NOTICE`, `is_withheld`, `contains_notice`, `apply_settings`, `_SETTINGS`, `_healing_views`, `_learn_unknown`, `_finish`, `_withhold`, `P1D_APPLIED`, `redact_value` per the caller table); `guard/redact.py` (`find_matches`, `add_known`, the sweep pass); `config.py`, `defaults.py`, `app.py` (`apply_settings`, `request_approval` catch), `runtime/agent_loop.py` (`card_withheld`, the document check); `approvals/channel.py`, `slack_channel.py`, `requests.py` (`summary`, `request`, `decide`, `_send`, `_card_check`), `cards.py` (`withheld_card`, re-export, `_card`), `gate.py` (imports from `_views.py`, `_rendered` docstring); `guard/judge.py`, `guard/bedrock_guardrail.py`, `evals.py`, `runtime/evidence.py`, `tools.py` (`error_reason` notice handling only), `guard/producers.py` (`NOTICE_HANDLING`); `vulture_whitelist.py` (remove `gate._rendered`); `CHANGELOG.md`.
  - create `tests/test_p1d_rows.py`, `tests/test_p1d_callers.py`, `tests/p1d_mutants.py`; extend `tests/fixtures/p1d_cases.py` and `tools/p1d_corpus.py` (both created by P1d-a; `--kind bs1|bs3|f11|f17 --map-size 10|200|2000`); create `tools/p1d_cost.py`.
  - NOT in P1d: `k1b/redaction.py`, `approvals/receiver.py` (P1d-b), `tools.py` S6 (P2d-2), `app.build`'s start gate (P1d-gate), the AWS-style rule (P1d-learn), any `store/*` file or migration.
- **Interface:** public `runmap.LookalikeCopy(RedactionError)` (message = class name); `WITHHELD_NOTICE`; `is_withheld(text) -> bool`; `contains_notice(text) -> bool`; `apply_settings(s) -> None`; `redact_text(text, mapping, neutralise=None, *, on_residue: Literal["withhold","raise"] = "withhold", source: str = "", ref: str = "") -> str` (no existing argument lost; `_learn` is private); `channel.clean(text, *, ref="", source="card")`; `channel.card_text(summary, *, ref="")`; `channel.CARD_WITHHELD_TEXT`; `channel.card_withheld_text(run_id=None, inputs=False)`; `cards.withheld_card(run_id) -> Card`; channel `send(..., *, withheld=False)`; `redact.find_matches(text, *, kinds=None)`; `redact.add_known(mapping, kind, value) -> str`; `P1D_APPLIED: bool`.
- **Existing core code reused:** as rev 7 (gate primitives, `_TAGS`, `strip_ansi`, `_trie*`, `_Redactor.find/_place`, `redact_cache`, `undo`, `textnorm` public functions, `InputTooLarge`, `TooDeep`, `REDACT_BUDGET_S`, the scan guard, the second pass, `producers.py`, the `scrub_settings` pattern, `card_too_long`, `document_too_large`, `store.get_plan`, `Plan.hash`). Checked and not reused: `runmap._views` (A10), `register_value`, `_secret_forms`, `MAX_REDACT_CHARS` as the document cap (A12).
- **Security and least-privilege notes:** no identity, right or secret; four settings. No raw text is stored for a withheld request (none is saved). The operator line carries counts and the run id, never content (a test greps the log for the key). Test values are built from parts; the only whole-key literal is `AKIAIOSFODNN7EXAMPLE`.
- **Rollback:** tag `pre-P1d`. **Non-revertible semantic changes (CHANGELOG, one sentence each):** stored records and model text may contain `WITHHELD_NOTICE`; `clean` raises `LookalikeCopy`; a withheld request is never saved and the run ends `NEEDS_PERSON card_withheld`; a stored request whose card is withheld cannot be approved and expires; case and accent copies of known values are masked; documents over `max_text_chars` are refused; `redact_value` returns the notice instead of raising. `test_withheld_notice_is_loud`.
- **Reviewers:** result rounds: fresh `egm-codebase-details`, `egm-design`, `egm-implementation-readiness`, given the diff, this ticket and the evidence only; no round cap.
- **Done =** a fresh result round finds no blocker or major; all gates green (tests 3.12 and 3.13, ruff check, ruff format --check, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit); ledger rows 001, 003, 004 FIXED-VERIFIED (001 and 004 only with the two-call rows S13-1..3); BS-1, BS-3 at ceiling; BS-2 (pattern-on-views pass) at 0; rows 002, 007 (P1d-a), 008 (P1d-learn), 005, 006, 009, 010, 011, 012 are not this package's; the lead merges.

## Failing inputs (literals in `tests/fixtures/p1d_cases.py`; the row id is the test id)
**Literals (built from parts):** K = `"AKIA" + "IOSFODNN7EXAMPLE"`; K4 = `AKIA`; K16 = `IOSFODNN7EXAMPLE`; SV = `SV_A + SV_B`, SV_A = `"Tq7mZ"`, SV_B = `"4xKp2Vb9Lr3NcW8dYh6uJs"`; EM = `"anna" + "." + "m" + "@" + "example" + "." + "org"`; PW(n) = first n characters of `"Qm8vRt2x" + "Lp5nZc7bKd3wHj"`; ESC = `chr(27)`; H29: v1 = `"Zx4cV7" + "bN1mQa"`, v2 = `"Wl9sD3" + "fG6hJk"`; X01 filler = `"a "` repeated.
**Fail-before method:** the new test files run on the base in a temporary worktree. Every fb row FIRST asserts a base-runnable leak oracle `leaks(output, secret)` = `textnorm.scan_holds(text=output, value=secret)` (or the exact fallback), prefix `LEAK:`; only then does it touch new names through `p1d_api()` (sentinels for absent names; an unknown keyword becomes a failure with prefix `NEW_SURFACE:`). Rows whose base output holds no key by construction assert their exact expected text. Every test carries `@pytest.mark.p1d(cls="fb"|"pb"|"ow"|"measure")` (round-7 G12); non-row tests are fb new-surface unless they pin unchanged behaviour (pb). `test_fail_before_outcomes` is run by the evidence runner: base SHA, both test files in a worktree of the base on 3.12 and 3.13, failures counted per prefix from junit; errors 0, every fb row failed with its prefix, every pb row passed. Raw output `handover/evidence/P1d/fail-before.txt`, base SHA on line 1.
**KV twin column:** "yes" = the row also runs as its KV twin. **Card rows' "withheld"** = `LookalikeCopy` from `clean`; through `request_approval`: no request saved.
| row | group | entry | KV twin | input | on base | expected after P1d |
|---|---|---|---|---|---|---|
| H01 | fb, new-surface | card | no | `key AKIA**IOSFODNN7EXAMPLE** here` | key shown | `LookalikeCopy` (learned: pattern on view d) |
| H02a-e | fb, new-surface | card | no | `AKIA**IOSFODNN**7EXAMPLE`; `AKIAIO*SFODNN7EXAMPLE*`; `AKIA~~IOSFODNN7EXAMPLE~~`; ``AKIA`IOSFODNN7EXAMPLE` ``; `AKIA_*IOSFODNN7EXAMPLE*_` | shown | withheld |
| H07a-b | pb | card | no | `AKIA<b></b>IOSFODNN7EXAMPLE`; `AKIA<!-- -->IOSFODNN7EXAMPLE` | masked | same |
| H07c | fb (RS-4) | card | no | `AKIA<!-- a > b -->IOSFODNN7EXAMPLE` | `AKIA b -->IOSF...` | masked (joined pass with the comment-first `TAG`) |
| H08a-g, H09a-c | pb | card | no | entity forms as rev 7 (`&ZeroWidthSpace;`, `&shy;`, `&NoBreak;`, `&InvisibleTimes;`, `&#8203;`, `&#x200B`, `&amp;#8203;`; `&#73;`, `&#x49;`, `&#73`) | masked | same |
| H10 | fb (RS-4), carrier | card | is one | KV, second copy `<SV_A>&amp;<SV_B>` | leaks | withheld |
| H11 | fb, carrier | card | yes | `"AKIA" + ESC + "[0m" + "IOSFODNN7EXAMPLE"` | `AKIA IOSF...` | withheld (raw-input learning, RS-1) |
| H12a-d | fb, carrier | card | yes | ESC `[38;5;196m`; C1 `\x9b0m`; OSC `ESC]0;t\x07`; OSC 8 `ESC]8;;http://x\x07` inside the key | shown | withheld |
| H13 | fb, carrier | card | yes | the text `\x1b[0m` (literal backslash) inside the key | shown | withheld (over-refusal accepted) |
| H14 | fb | card | yes | `AKIA` + ESC + `IOSFODNN7EXAMPLE` | 19 of 20 shown | withheld (found only in a view) |
| H15a | fb (RS-4) | card | yes | `x\x08AKIAIOSFODNN7EXAMPLE` | `xAKIA...` | withheld (overstrike in b1 deletes `x` and BS; the plain pattern learns it) |
| H15b | pb (RS-4) | card | yes | `AKIA\x08IOSFODNN7EXAMPLE` | masked | same |
| H16, H16b, H16c | fb | card | yes | CR; U+2028; U+2029 inside the key | two lines | withheld |
| H17a-k | pb (a-j RS-4; k BS-0) | card | no | BEL, DEL, NEL, VT, FF, NUL, U+200B, U+200D, U+2060, U+202E, U+00AD inside the key | masked | same |
| H18a-b | fb | card | no | U+0301; U+0323 inside the key | shown | withheld |
| H19 | pb | card | no | the key in full-width letters | masked | same |
| H20 | fb | card | is one | KV, second copy `<SV_A>` + U+FF0A + `<SV_B>` | shown | withheld |
| H21 | fb | card | yes | Cyrillic `А` for both `A` of `AKIA` | shown | withheld (learned after fold) |
| H22 | fb | card | is one | KV, second copy `<SV_A>**<SV_B>**` | shown | withheld |
| H23 | fb | card | is one | KV, second copy SV in lower case | shown | masked under SV's placeholder |
| H24 | fb | card | is one | KV, second copy `<SV_A>\n<SV_B>` | shown | withheld |
| H25 | fb, carrier | card | yes | `password=<SV_A>` + ESC + `[1m<SV_B>` | `<SECRET_1> ` + tail | withheld |
| H28a-b | fb | card | no | `anna.m**@example.org**`; `anna.m@exam` + ESC + `[0mple.org` (not fixed by P1d-a, P8 `rows-proto-query.txt`) | shown | withheld |
| H29a | pb? | card | no | `passwor<span></span>d%3D<v1>%0D<v2>` | BS-0 (l) | recorded |
| H29b | fb, carrier | card | is one | KV, second copy `<SV_A><b></b><SV_B>` | shown | withheld |
| H30a | fb | Slack | no | H01's input as `req.summary` through `SlackChannel._blocks` | shown | builder text, no actions block |
| H30b | fb | Slack | no | a request stored before P1d whose plan inputs hold H01's input, its summary inserted directly, sent by `resend_unsent` | shown with buttons | builder text, no actions block, `sent_at` set once; `decide` returns `(False, "card_withheld")` |
| H31 | fb | model | no | `AKIAIOSFODN\nN7EXAMPLE` | shown | notice (pattern on view d) |
| H34b | pb (P8-1) | card, model | no | `password=<SV_A>&amp;<SV_B>` | masked (P1d-a) | same |
| H37a-c | fb | model | no | the GitHub-token shape (prefix from `_KEY_PREFIXES`, BS-0 (g)), built from parts, split by `**`, a newline, a full-width `*` | shown | notice |
| H37d-e | measure | model | no | the same in lower case; with `.` inserted | shown | measured (N6) |
| H40 | fb | summary | no | H01 as a plan input through `request_approval` with `FakeChannel` | key shown | no request saved; one post of the builder text with the run id; `NEEDS_PERSON card_withheld` |
| SUM-1..5 | fb | summary | no | H11, H12a, H14, H16 and C06 as plan inputs (they reach the card as `\u001b`, `\r` text inside `canonical_json`, round-7 G8) | shown | no request saved (raw-input views after decode) |
| S13-1 | fb | model | no | two calls, same run map: call 1 `password=<SV>`; call 2 SV in lower case | shown | call 2 masked |
| S13-2 | fb | model | no | as S13-1, call 2 SV split by `**` | shown | call 2 notice |
| S13-3 | fb | model | no | a 2,000-value map plus one `**`-split copy of value 1,999 | shown | notice; latency recorded |
| MP-1..4 | pb, new rows (round-7 G4) | model | no | known `Christopher`: `ChristopherSmith`, `user_id=Christopher123`, `Christophersen`; known `José Müller`: `JOSE MULLER` | shown as written | MP-1..3 unchanged (not withheld); MP-4 masked under the placeholder |
| FLOOD | fb | model | no | 40 different keys, each split by `**` | shown | notice, `reason=size`, map unchanged (`max_learned_per_call`) |
| POISON | measure | model | no | a false-learn shape if BS-0 (p) finds one | n/a | listed; RK3 |
| joined-forms-placeholder, PB-ENC | pb? | card / model | no | as rev 7 | BS-0 (l) | never the key |
| LK-JAMO-PB, LK-UNFOLD | as rev 7 | model | no | as rev 7 (revision log rev 7: Korean and Tamil joining rows; values that fail while building needles) | | as rev 7 |
**Combination rows (entry card; each runs as its KV twin, which DECIDES A8):** C01 `AKIA**` + Cyrillic `О` + `SFODNN7EXAMPLE**`; C02 `AKIA**IO` + U+0301 + `SFODNN7EXAMPLE`; C03 (fb, RS-4) `AKIA&ast;&ast;IOSFODNN7EXAMPLE`; C04 (fb, RS-4) `AKIA&amp;ast;IOSFODNN7EXAMPLE`; C05 `AKIA` + ESC + `[0m**IOSFODNN7EXAMPLE`; C05b `AKIA&#27;[0mIOSFODNN7EXAMPLE`; C06 `AKIA` + ESC + `[0m\nIOSFODNN7EXAMPLE`; C07 `akia**iosfodnn7example` (unknown form: not learned without P1d-learn, measure; KV twin decides); C08 `AKIA%2A%2AIOSFODNN7EXAMPLE`; C09 `AKIA&a**mp;#73;OSFODNN7EXAMPLE` and `AKIA%2<b></b>AIOSFODNN7EXAMPLE`; C10 `AKIA%252AIOSFODNN7EXAMPLE`. Expected: withheld.
**Short-key and boundary rows:** n in {`min_key_chars - 1`, `min_key_chars`} for {plain, lower case, `**` inside, ESC inside}, KV with PW(n): below not withheld; at the floor withheld (lower case: masked). Scan-key length `TN_MIN - 1` (fallback, one `coverage=exact_only` line) and `TN_MIN` (finder). `kv-empty-key` = `password=!!!!!!!!`: masked as today.
**Size and error rows:** X01 a document of exactly `max_text_chars` with a split key 100 characters before the end: read and withheld; X02 a document of cap + 1: `document_too_large`; X02b `redact_text` on `MAX_REDACT_CHARS + 1`: notice `reason=size` (raise mode: `LookalikeCopy`); X03 a `redact_value` with `_chars` over `MAX_REDACT_CHARS`: whole value is the notice; X04 scripted values x view length over `max_work` (lowered in the test): `reason=size`; X05 the budget firing (monkeypatched clock): `reason=size`; X06 (measure, DEFAULT 1) a 120,000-character tool result with a split key at the end: checked or `reason=size`, time recorded; E01 a failure injected into `_healing_views`: notice, `reason=error`, class name logged, no content; E02 raise mode: `LookalikeCopy`; E03 `TooDeep` from `undo`: as E01; MAP-1 after a `residue` withhold on the model path the map holds this call's masked and learned values; MAP-2 after `size`/`error` the map is unchanged.
**Guard rows (pb, base outputs pinned at BS-0 (l)):** F01-F20 as rev 7 (F01 ``Approve **restart** of `web-01` in ~~old~~ demo?``; F02 placeholders not put back; F02b a seed value is not known; F03 hex in code spans; F04 a Markdown table; F05 `Tom &amp; Jerry &lt;ok&gt; &#169; 2026`; F06 coloured `ok`; F07 `10.0.0.1` twice; F08 ``run `make`test``; F09 `password=<SV>`; F10 `José Müller`; F11/F17 corpus; F12 an ARN account id; F13 Greek and Cyrillic prose; F15 a URL query; F18 `10.0.0.1` in `210.0.0.12`; F19 strict mode; F20 `/users/christopher/profile` with `Christopher` known: masked). **F21** (`anna.m@example.org` known, `Anna M. Example Org` in the text) moves from ow to **pb** (standalone kinds read no squeeze views). **ow:** F14 (25/26-character code spans), F16 is P1d-a's.
**Model-path rows:** S1-S5: H01's input through `redact_untrusted`, `prepare_output`, `error_reason`, `safe_head`, `redact_value`: notice or masked, never the key, never raises.
**Pin and property tests:** `test_scan_holds_ignores_non_alphanumerics`; `test_finder_equals_scan_holds`; `test_skips_are_exact` (Hypothesis: views with skips equal views without); `test_views_at_most_five`; `test_mutant_ids_exist`; `test_find_matches_equals_redact_mapping`; `test_scan_cache_entered_once_per_redact_text_call` (round-7 G14); `test_card_withheld_text_exact`; `test_withheld_card_text_not_recleaned`; `test_log_line_has_no_newline_from_input`; `test_joined_pass_alt_returned_on_new_assignment`; `test_out_rechecked_after_joined_pass_learns`; `test_normal_request_still_approvable`; `test_card_text_accepts_every_clean_output`; `test_decide_check_equals_creation_check`; `test_redactor_entry_only_in_runmap`; `test_no_request_saved_for_every_withheld_row` (H01, H02a-e, H07c, H10-H16c, H18, H20-H22, H24, H25, H28a-b, H29b, H40, SUM-1..5, C01-C10 and KV twins, minus rows found pb at BS-0).

## Build steps (BS-0 before code; BS-1 to BS-4 on the final head)
**BS-0 (reads and early probes; no product code).** (a) baseline failures; pin P1b, `TN_MIN`, the error classes, `_value_needles`, `_all_views`, `_scan_key` (STOP if not letters and digits only); (b) `undo`'s depth; (c) callers of `clean`, `redact_text`, `redact_bounded`, `drop_margin`, every `except InputTooLarge|TooDeep`, the `tools.py` byte cuts (resolve: ~667, 741, 789-845; zoom-out: 776, 955, 1000) with a row for a key straddling a cut BEFORE redaction, and the three outside redactor sites; (d) confirm FR3 on the base; (e) hash readers of `redact_value` results; (f) the JSON tool-result consumer; (g) the GitHub-token prefix for H37; (h) settings in `defaults.py`/`config.py`; (i) `_Redactor.find`, `_place`, the every-copy and standalone kind sets; (j) the put-back formula against the note; (k) exact line numbers for every `~`; (l) every row on the base, pin pb and F outputs, settle every pb?; (m) dropping `b2` changes no H or C outcome; (n) import cycles; every implementer of the channel `send`; (o) `safe_head` order and limits (every `limit` at least the notice's length), log filters; (p) the pattern-on-views learning on the first 200 corpus documents (false learns per shape; any = report before the build) and a finder-plus-skips prototype at 30,000 characters with 2,000 values against 1.5 s; (q) the put-back test and `_edge_run` off: name a killer row for each, else drop them (M10, M29, M38, LK-JAMO-PB) with the reason; the M54 killer (a row that learns only after `[.]` or placeholder insertion; if none, M54 is declared equivalent with the reason). Any STOP goes back to review.
- **BS-1** model-path false withhold: 500 made-up documents as multi-call runs with accumulated maps of 10, 200 and 2,000 values; maps are real-looking made-up names (with accents, Greek, Cyrillic), e-mails, host names and 8-40 character tokens (round-7 G4), not generator strings. Ceiling 0 withholds (0 of 500 supports a rate below about 0.6 percent at 95 percent, rule of three); any withhold is listed and fixed or justified by a real hidden value.
- **BS-2** false learns of the pattern-on-views pass on the BS-1 corpus plus hex digests, UUIDs, base64 blobs and 2,000 lines of code; per pattern and per view. Ceiling 0 (RK3; not the HELD gate, which is P1d-learn's).
- **BS-3** card path: guard rows plus 500 made-up cards (200 ordinary, 100 Markdown, 100 e-mails and host names, 100 commands); ceiling 0 withholds on non-secret cards. Reported SEPARATELY: false-withhold rate (ow rows listed), false-abstain rate.
- **BS-4** cost (`tools/p1d_cost.py`, ALONE on its slot): `redact_text` at 3,000, 30,000 and 120,000 characters with 10, 200, 2,000 known values (finder build time apart), a `redact_value` of 5,000 short leaves, `_card_check` per decision; target p95 at 3,000 and 30,000 under `REDACT_BUDGET_S / 4`; the size at which tool results start to be withheld (DEFAULT 1); set `max_work` from the numbers (source stays placeholder). **STOP:** if the target fails at 30,000, back to the lead.

## Mutation plan (`tests/p1d_mutants.py`; one mutant per mechanism; a survivor is declared equivalent with a written reason and its code deleted, or a row is added). Numbers kept from rev 7; moved: M7-M9, M33-M35 to P1d-learn, M17 to P1d-a (A1), M22, M28, M31 to P1d-gate; M43-M49 are used there.
| mutant | planted change | killer |
|---|---|---|
| M1 | `_finish` not called | H22 |
| M2 | catch-all removed | E01 |
| M3 | decode (a) removed from `_healing_views` | C08, C03 |
| M4 | carrier deletion (b1) removed | H25, H29b |
| M5 | noise deletion (d) removed | H37a-c |
| M6 | fold (c) removed | H21 |
| M10 | put-back without the two spaces (conditional) | LK-JAMO-PB |
| M11 | residue-view loop removed (put-back kept) | H22 |
| M12 | `TextnormError` swallowed as "no hit" | LK-UNFOLD (1), E03 |
| M13 | short-scan-key fallback removed | boundary row `TN_MIN - 1` with `**` |
| M14 | fallback case-sensitive | boundary row, ESC variant in lower case |
| M15 | fallback reads a squeeze view or drops the boundary rule | F13, F18 |
| M16 | seed entries put back | F02 |
| M18 | `on_residue` default `"raise"` | S1-S5 |
| M19 | `LookalikeCopy` caught in `clean` | H01 (asserts `type(exc) is LookalikeCopy`), H30a |
| M20a-d | one trigger character removed from step a / b1 / c / d's skip test | `test_skips_are_exact`, C08 (a), H15a (b1), H21 (c), H16b (d) |
| M21 | `_card_check` skipped in `decide` | `test_decide_refuses_stored_withheld_summary` |
| M23 | judge or guardrail treats the notice as clean | `test_judge_refuses_on_notice`, `test_guardrail_refuses_on_notice` |
| M24 | learning on b1-d removed | H21, H37a |
| M25 | seed entries counted as known | F02b |
| M26 | joined pass gets a fresh map, or the snapshot after the second call | `test_joined_pass_alt_returned_on_new_assignment`, H30a |
| M27 | `redact_value` size rule removed | X03 |
| M29 | `_edge_run` removed (conditional, BS-0 (q)) | chosen at BS-0 |
| M30 | the `error` catch-all returns the raw text | E01 (result equals the notice) |
| M32 | `grounded` accepts the notice | `test_grounded_fails_on_notice` |
| M36 | known reduced to this call's values | S13-2 |
| M37 | re-entrancy guard removed | `test_log_filter_reentry` |
| M38 | `e(k)` uses the largest count (conditional) | chosen at BS-0 (q) |
| M39 | `except LookalikeCopy: raise` removed in `summary` | `test_summary_lets_lookalikecopy_through` |
| M40 | `except LookalikeCopy: raise` removed from the catch-all | H01 (card) |
| M41 | case/accent sweep pass removed | H23, S13-1 |
| M42 | document-limit validator removed | `test_document_limit_above_cap_refused` |
| M50 | learning reads the post-`neutralise` text | H11 |
| M51 | backspace overstrike removed | H15a |
| M52 | "learned value withholds" removed | H14 |
| M53 | `_card_check` skipped in `_send` | H30b |
| M54 | learning left on in `card_text` | `test_card_text_accepts_every_clean_output` + the BS-0 (q) row (or equivalent) |
| M55 | kind rule removed (standalone kinds read as every-copy) | MP-1 |
| M56 | accent fold removed from the sweep pass | MP-4 |
| M57 | document producer's notice check removed | `test_document_notice_is_document_too_large` |
| M58 | `max_learned_per_call` removed | FLOOD |
| M59 | `min_key_chars` compared with `>` | boundary row at the floor |
| M60 | `max_work` compared with `>=` | X04 at the boundary |
| M61 | actions block kept on withhold | `test_h30a` |
| M62 | MAP-1 commit removed | MAP-1 |
| M63 | put-back `count >= e` (conditional) | LK-JAMO-PB control |
| M64 | `withheld_card` built through `clean` | `test_withheld_card_text_not_recleaned` |
| M65 | run-id pointer shown without `P1DC_APPLIED` | `test_card_withheld_text_exact` (marker off) |
| M66 | `sent_at` not set after a withheld post | `test_withheld_send_sets_sent_at_once` |
Runner: `tools/mutation_runner.py` (rebased in, precondition 3); every mutant restored in a `finally`; `git status --porcelain` clean at the end. **Required: every mutant except the conditional ones** (M10, M29, M38, M63 exist only while their mechanism exists). The builder may not merge two mutants without a written reason.

## Evidence commands (EVIDENCE RUNNER, a separate agent; raw output to `handover/evidence/P1d/evidence-<n>.md`; line 1 `git rev-parse HEAD`; no cloud configuration in the environment; heavy jobs through `tools/heavy_slot.py --slots 3 --timeout 2400 --`, max 3 at once (ORDER 178); gate on each command's own exit code; copied from `.github/workflows/ci.yml` lines 79-119, round-7 G15)
```
uv run --all-extras --group test ruff check src tests demos
uv run --all-extras --group test ruff format --check src tests demos
uv run --all-extras --group test bandit -q -r src demos -ll
uv run --all-extras --group test pytest -q -rs -m "not live and not perf" tests/test_p1d_rows.py tests/test_p1d_callers.py
uv run --python 3.12 --all-extras --group test pytest -q -m "not live and not perf" -rs
uv run --python 3.13 --all-extras --group test pytest -q -m "not live and not perf" -rs
HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test pytest -q -m perf -rs
uv run --all-extras --group test python tests/p1d_mutants.py                       # alone
uv run --all-extras --group test python tools/p1d_corpus.py --seed 1 --kind all    # BS-1, BS-2, BS-3; exit 0 pass, 1 error, 3 over ceiling
uv run --all-extras --group test python tools/p1d_cost.py --sizes 3000,30000,120000 --known-counts 10,200,2000 --leaves 5000   # BS-4, alone
git worktree add <tmp> <base-sha>; cp <new test files and fixtures> <tmp>; for py in 3.12 3.13; do (cd <tmp> && uv run --python $py --all-extras --group test pytest -q --junitxml=fb-$py.xml tests/test_p1d_rows.py tests/test_p1d_callers.py > fail-before-$py.raw 2>&1); done
```
`<tmp>` = `mktemp -d` under the scratchpad; `<base-sha>` = `git rev-parse origin/main` after P1d-a merges; `<dsn>` = the session's local test database. Each command `> out 2>&1; rc=$?; tail -n 3 out; echo rc=$rc`.

## Build notes
BN-P1d-1 cite the base SHA; rebase after P1d-a merges and rerun fail-before. BN-P1d-2 correct `gate._rendered`'s docstring. BN-P1d-3 the learning pass is private; if the hook lint of `test_k5_round11.py` objects, exempt by (file, function) with an assertion that the result is discarded. BN-P1d-4 views outer, values inner. BN-P1d-5 P2d-2 promotes `_healing_views`/`_finish` (with an `extra=` argument) in its own ticket. BN-P1d-6 test texts never use "staging", "dev" or "test" as a stage name (R449); F01 says "demo". BN-P1d-7 remove `gate._rendered` from `vulture_whitelist.py`. BN-P1d-9 operator review is P1d-c. BN-P1d-10 the markdown-it-py comparison is not built. BN-P1d-11 the P1b fix batch (`2034512`) is the P1b state BS-0 pins once merged. BN-P1d-12 P1d-learn calls into `_learn_unknown`; keep that function's signature stable.

## Owner-facing wording (plain words, rule 14)
- CHANGELOG: "Text shown to a person or sent to a model: a password, key or e-mail address written with formatting characters inside it (bold or italic markers, a terminal colour code, a backspace, an accent mark, look-alike letters, a line break) is no longer shown. A secret already hidden once is also hidden when it appears again in another letter case or without its accents. An approval request whose card cannot be shown safely is not created: one message without buttons says so, the run stops and waits for a person, and an operator log line says why (an operator can read the cause with a read-only command once that package lands). Text sent to a model that cannot be checked is replaced by a short notice. Documents longer than a stated limit (30,000 characters, a first estimate, not yet measured) are refused before they are read. Not covered: a secret that no pattern recognises and that is not already known, values shorter than a stated length, and secrets of other key kinds written in another letter case or with an extra character. AWS-style keys in small letters or with one extra character are a separate fix."
- For the owner's status message: "We found a gap where a key, password or e-mail address written with formatting characters inside it could be shown on an approval card or sent to the model. The fix is planned in four parts; the first part (e-mail addresses and passwords with `&`) is small and goes first. Until all parts are merged, the software refuses to start for a client, so no real client data goes through it."

## Ledger rows (`handover/ledger.md`; each row names its topic and the marker that closes its gate)
| id | package / topic | severity | summary | status |
|---|---|---|---|---|
| BL-core-p1d-001 | P1d | BLOCKER | `redact_text` (and so `clean`) shows a key split by markers, escapes, controls, accents or look-alikes, and a known value copied in another case or split (H01-H25, H28, S13) | OPEN |
| BL-core-p1d-002 | P1d-a | BLOCKER | `clean` never masks e-mail and internal hosts (defang before redaction, H26-H27) | OPEN (moved) |
| BL-core-p1d-003 | P1d | MAJOR | `SlackChannel._blocks` second `redact_text` with buttons; a withheld card must never become an approvable request (H30, H40; no-save route and the `_card_check` re-check) | OPEN |
| BL-core-p1d-004 | P1d | BLOCKER | the same split key passes every model producer (S1-S5, S13) | OPEN |
| BL-core-p1d-005 | P2d-2 | MAJOR | handed-out secret echoed in another case or with markers (S6); `P2D2_APPLIED` | OPEN (hand-over) |
| BL-core-p1d-006 | P1d-b | MAJOR | `k1b.redaction.sensitive` misses disguised key names (S11); `P1DB_APPLIED` | OPEN (hand-over) |
| BL-core-p1d-007 | P1d-a | MAJOR | SECRET value ends at `&` (H34) | OPEN (moved) |
| BL-core-p1d-008 | P1d-learn | MAJOR | lower-case, dotted or `&`-inserted unknown AWS-style key passes (H32, H33, H35); `P1DL_APPLIED`; HELD gate | OPEN (moved) |
| BL-core-p1d-009 | P1d-b | MINOR | `receiver.log_message` logs a callback URL unredacted (S16) | OPEN (hand-over) |
| BL-core-p1d-010 | P1d-c | MAJOR | no operator view of a withheld request's cause; option B, `P1DC_APPLIED` | OPEN (hand-over) |
Rows 011 (MAJOR) and 012 (BLOCKER, ORDER 178) belong to P1d-b. The lead's row `BL-hadavin-sdk-cilint-001` (ORDER 146) is the parent of 001-004.

## EGM steps, in order (R374, rule 13)
(1) brainstorm: not run, revision 1 is the brief; (2) draft: revision 8 (headless drafting agent applying `round7-resolve.md` and ORDERS 177-178; the `egm:egm-draft` skill was not invoked by this agent, see the report); (3) plan review round 8: fresh `egm-design` + `egm-implementation-readiness`, changed sections only (DEFAULT 2); (4) `egm:egm-resolve`; freeze at 0 blockers; (5) build after P1d-a and P1b merge; (6) EVIDENCE RUNNER; (7) result review by `egm:*` reviewers; (8) resolve, repeat until clean (no cap); (9) `egm:egm-drift-report`.

## Slot needs (rule 17)
Build iterations: only the new test files and the touched files (1-2 minutes). Final head, once: full suite on 3.12 and 3.13 (2 slots), the mutant run (1 slot), BS-4 (1 slot, ALONE). Real clock (estimate): BS-0 2-3 hours, build 10-14 hours, evidence 1-2 hours, each review round 1-2 hours. P1d-a (2-3 hours) runs first and in parallel with BS-0's reads. P2d-2, P5c also edit `channel.py` and `requests.py` (rebase conflict, no slot conflict).

## OPEN QUESTIONS for the lead (defaults applied)
1. **H28 placement:** ORDER 177 put H26-H28 into P1d-a, but the P1d-a prototype shows H28a-b (split e-mail addresses) are not fixed by the defang move; they stay here. Say if they should instead be removed from both.
2. **Pattern-on-views false learns (RK3):** this ticket gives the learning pass of the redactor's own patterns a ceiling of 0 in BS-2 but no HELD gate (ORDER 177 attaches HELD to P1d-learn). Default: a false learn is fixed by dropping that view or kind; if it cannot be, back to you. Say if this pass should carry HELD too.
3. **Every learned value withholds:** applying round-7 RS-1 rule 2 literally makes every value the learning pass adds withhold the text (it was, by definition, found only in a view). This is simpler than rev 7 and stricter; BS-1/BS-3 measure the cost.
4. **Channel `send(..., withheld=True)`:** a small Protocol change, needed so `_send` can post the fixed card without buttons. BS-0 (n) lists the implementers.

## UNVERIFIED (not read or run in revision 8)
Every V number; FR1 after `2034512`; `TN_MIN` and the needle functions on merged P1b; `undo`'s depth; the `tools.py` byte cuts; the three outside redactor sites; every pb? row; H37's prefix; the put-back formula; the finder's latency; `max_work`; all BS results; standard section numbers; Python 3.12 (probes ran on 3.13 only); `requests.py` line numbers after P1a/P1b merge; P1d-c's final command syntax.

## Rules cited
R233, R337, R363, R371, R374, R447, R448, R449, R450; studio preamble rules 3, 5, 6, 7, 12, 13, 14, 17, 19, 20, 21.

## Revision log
Revisions 1-7: `handover/reviews/P1d/revision-log.md`. **Rev 8 (2026-11-09):** split by ORDER 177 into P1d-a, P1d-learn, P1d-gate and this ticket (rows, mutants, preconditions moved; P1d-a prototype probes P8); `round7-resolve.md` applied: G2 (learning on the raw input, learned values withhold, backspace overstrike, H15a fb, M50-M52), G3 (`_card_check` from the stored plan, no learning in channel re-checks, `_send` posts the fixed card and sets `sent_at`, A16, M53-M54), G4 (residue per kind, case- and accent-insensitive sweep, real-looking BS-1 maps, MP rows, F21 pb, M55-M56), G5 (view a not learned on, A10 rewritten), G6 (cap on documents only, `redact_bounded` kept, `le=MAX_REDACT_CHARS`, `_chars`), G7 (notice consumers, document producer, M57), G8 (SUM rows), G9 (`max_learned_per_call`, FLOOD, A17, M58), G10 and G1/G16 moved, G11 (AST test), G12 (exact skips property, M20a-d, H16b-c, pb? settled from RS-4, `p1d` marks), G13 (`cards.withheld_card`), G14 (test renamed), G15 (CI commands), G17 (log moved, RS-3 citation corrected), nits (M59-M63, autouse fixture, decide order); ORDER 178 (card text without "or deny it", run-id pointer to `approvals show` gated on `P1DC_APPLIED`, ref = run id, M64-M66); DEFAULT PENDING LEAD 1-4 recorded.
