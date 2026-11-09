# Package ticket P1d: a secret split by markup (markdown markers, an HTML entity, a terminal escape, a control character, another letter case, an inserted character) is shown unmasked by `approvals.channel.clean` and by `runmap.redact_text`. DRAFT revision 2 (egm-draft step run; plan review round 2 not yet run)

**Why this ticket is over 250 lines (template rule):** the failing-input table is the specification (lead order 146 2(a)); most lines are table rows. The rule text itself is lines 60-110.
**Revision 2, written 2026-11-09 (UTC; IST = UTC+5:30) by the cloud session (Opus, `egm:egm-draft`), from revision 1 (2026-11-07), the two round-1 plan reviews (`reviews/P1d/round1-design.md`: 2 Blockers, 10 Majors; `round1-readiness.md`: 8 Blockers, 10 Majors, 5 Nits) and the lead's rulings in ORDER 165.** Text only: no code, no pull request. **Not done, first:** nothing in this ticket was run again for revision 2. Every number marked V is from revision 1's author probes (`handover/evidence/P1d/author-probes-2026-11-07.txt`, a scratch prototype that is NOT the build); every number marked UNVERIFIED must be measured by the build step named beside it before that row counts. `egm:egm-brainstorm` was not run (no `concepts_brief.md`; the lead did not waive the draft step, ORDER 165 item 9, and revision 1 is the brief). The sibling report is `handover/studio-notes/p1d-siblings.md`. Marker: CODE-LAST v1.

## Lead rulings this revision implements (ORDER 165, 2026-11-09)
1. The fix goes inside `runmap.redact_text` (one choke point), the model path included. No P1e ticket.
2. The squeeze pass and the case-folded pass are measured in P1d (steps BS-2, BS-3). No client data before P1d is merged.
3. A refused card is a finished state (posted once, never resent) with an operator log line and a visible reason, in this package.
4. The draft step is not waived. Known leaks H31 to H35 are fixed in P1d, not deferred (fix, do not defer).
5. P1b ships the `textnorm` library; P1d wires `runmap.redact_text` to it. P1d is a HARD DEPENDENCY of any P1b or PR 63 merge into a pilot or prod path.

## Words used in this ticket (defined once; one word keeps one meaning)
- **The choke point** = `guard/runmap.py::redact_text`. Every model-bound text, log text, tool result and approval card goes through it.
- **A view** = another spelling of the same text that a reader, a renderer or a terminal may show. **Healing views** = the views that delete or undo something to join a split value: markers deleted, tags deleted, escape sequences deleted, control characters deleted, entities and percent-codes decoded, look-alike letters folded, `[.]` read as `.`, plus two matching-only views: **squeezed** (every character that is not a letter or digit removed) and **case-folded** (lower case).
- **Known value** = an original the redactor masked in this text (the run map), or one a pattern finds in any healing view (found by the **learning pass**: the patterns run on every view, the output is thrown away, only the found originals are kept).
- **Put-back** = the shown text with each genuine placeholder (`<APIKEY_1>`) replaced by its original, one space either side. **Dropped form** = the shown text with each genuine placeholder replaced by one space. Both are tests of "could a person re-join the pieces".
- **Residue rule** = the final check: no known value may be readable in any healing view of the dropped form, and the count of any value's scan keys in the put-back form may not exceed the count the put-back originals explain. If a known value is readable, the text is **withheld**.
- **Withhold** = `redact_text` does not return the text. By default (`on_residue="withhold"`) it returns the fixed sentence `WITHHELD_NOTICE` and writes one operator log line (reason, number of characters, number of views, number of known values; never any content). With `on_residue="raise"` (approval cards) it raises `runmap.LookalikeCopy` (a `RedactionError`; name and meaning from `designs/lookalike-leak.md` section 5; the message is the class name only).
- **fb / pb** = a test row that fails on the base commit (fail-before, the new behaviour) / passes on it by design (a guard row that must stay unchanged).
- **The operator** = the person who runs the studio's deployment for the client; the ticket does not assume a web console exists (see Risk R6).

## The problem in plain words
A person (or a model) is shown a text after secrets and personal data were replaced by placeholders such as `<APIKEY_1>`. The redactor reads only the text as written. If a secret is written with extra characters inside it, for example `AKIA**IOSFODNN7EXAMPLE**` (the asterisks make half of it bold in Markdown), the pattern does not match and the key is shown. The same happens with a terminal colour code, a backspace, an accent mark, look-alike letters, a different letter case, a line break or one inserted character. In a card, the person can re-join the pieces by eye (Slack shows the characters as typed; a Markdown viewer shows them joined); a model re-joins them too. A second hole of the same kind: the approval gate changes every `.` in a domain to `[.]` BEFORE the redactor runs, so a plain e-mail address or internal host name is never masked (`anna.m@example[.]org` is shown). A third: a password that itself contains `&` shows the part after the `&`; a key glued to a word shows in full.

## Verified facts (V = read or run in revision 1 on main `0dabf1f` / P1b `0d843b4`; raw output `handover/evidence/P1d/author-probes-2026-11-07.txt`; not re-run for revision 2)
- V1: `clean` gives the same output on main, on P1b and on `core/ci-lint-set` for every row below: the hole is on main.
- V2: `gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `_RENDERED_MARKUP` exist (`gate.py:197-226`) and nothing calls them (only `vulture_whitelist.py` on `core/ci-lint-set`). They are the unfinished fix of review R9-O1. `gate.py:151` already builds `MarkdownIt("commonmark")` as `_MD`.
- V3: `gate._rendered`'s docstring says `AKIA&amp;...` "shows a key joined"; a renderer shows `AKIA&IOSF...` (an inserted `&`). The docstring is wrong (BN-P1d-2). The `&` is an INSERTED character: row H33 is the case.
- V4: `redact.strip_ansi` puts a SPACE where an escape sequence stood between two letters, on purpose; a terminal shows the two parts JOINED. P1d adds deleting views.
- V5: the redactor's own views (`runmap._views`, `runmap.py:~380-420`; P1b adds `composed`) do not delete markers, escapes or control characters, and do not fold case or look-alikes for PATTERN matching; the known-value sweep (`redact.py:~1204 _sweep`) is literal and case-sensitive. The same split key reaches the model through documents, tool results, tool errors and logs (sibling report S1-S5, measured).
- V6: `textnorm.scan_holds(text, value)` holds `AKIAIOSFODNN7EXAMPLE` in `key AKIA**IOSFODNN7EXAMPLE** x` and in the lower-case copy; it raises `ViewTooShort` for a very short scannable value (a dotted address `10.0.0.1`); `textnorm.fold` turns Cyrillic look-alikes and a combining accent back into `AKIA...` but keeps `**`.
- V7: `register_value` (strict by default) raises `CoverageRefused` for Latin and digit values. P1d never calls `register_value`; it calls `scan_holds` on values found at run time. (P1b round-1 resolve M3 changes this: ordinary ASCII secrets will be accepted with an exact view. P1d does not depend on it.)
- V8: a first prototype ran the whole redactor BEFORE the gate: it broke two existing fuzz tests (a long tag masked as `<HIGHENTROPY_1>` hid `password%3D` from the joined pass). Revision 2 moves ONLY the defang step (below), not the whole redactor.
- V9 (cost of the prototype, one 4-CPU container, thread CPU time, other agents' suites on the same machine): 3,000 chars 0.21 s (today 0.03 s); 30,000 chars 2.69 s (0.24 s); 120,000 chars 12.9 s (0.98 s). A loop with values outside the views took 190 s at 30,000 chars: loop order matters (views outer, values inner; textnorm's `scan_cache` keeps two texts).
- UNVERIFIED and to be measured at build start (BS-1 to BS-4): the 5 failing baseline tests (cause), the squeezed and case-folded patterns' false-match rate, the cost at the window size, whether the high-entropy pattern makes F14 refuse.

## Merge-order preconditions (every one is a gate for the build start, BS-0)
1. P1a (PR 63, `core/P1a`, textnorm foundations) merged; P1b merged (branch `core/P1b-fixwip`, head `0d843b4` at the time of writing; P1b round-1 fix batch is running, so P1d is built on the merged P1b, not on the branch). `textnorm` is NOT on `0dabf1f`: a P1d test file must not import `textnorm` at module top (a fail-before collection error would hide as a failure); imports happen inside the test functions or through `pytest.importorskip` is NOT used (a skip would hide a fail).
2. `defaults.py` constants of P1b (`REDACT_BUDGET_S`, `TEXTNORM_*`) exist on the base.
3. `vulture_whitelist.py` and `tools/mutation_runner.py` exist on the base. At the time of writing they exist only on `core/ci-lint-set` (and are absent from main); if that branch is not merged first, P1d builds `tests/p1d_mutants.py` with a plain subprocess loop and drops the whitelist step, and says so in its report.
4. The 5 baseline test failures are named with their cause (BS-0) and are green or recorded as environment before "done" is claimed.

## RUNG TABLE (R447, R448, R450; scale of 2026-11-06: 1 no-code tools, 2 our own core modules, 3 existing free tools (MCP, RAG, model features), 4 free libraries and open code (tested, licence-checked), 5 our own new code last. Tier C: a core change on a redaction path.)
Gate: core SDK change, no client (rung 0 not applicable), no fee, no new dependency. Rung 1 closed (R447: no redaction step inside a no-code flow). Rung 3 closed (a model feature cannot be exact and runs after the text left). **Guarantee class** (new column): **exact** = holds for every value in the set named in the row, with a test; **best effort** = holds for the cases tested, no claim beyond; **detection-only** = detects and reports, does not prevent. The class applies to a value that is in the run map OR that a pattern finds in some healing view. An unknown secret with no pattern (a plain password, no key word) is OUT of the guarantee: not detected, not prevented (said once here, repeated in the CHANGELOG).
| component | need | rung tried | evidence (source, date) | what only our code gives | guarantee class | verdict |
|---|---|---|---|---|---|---|
| healing views (deleting and decoding views) | read the text as a renderer, terminal or person shows it | 2 (`gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `redact._ANSI`, `strip_controls`, `runmap.undo`) | V2, V4 read 2026-11-07 | one public function that builds them to a fixed point under a cap | exact for deletion, decoding and fold views of known values | CUT-TO-CONFIG+GLUE (reuse, one function) |
| Markdown rendering by a library | rendered view | 4: `markdown-it-py` (already imported by `gate.py:72`, `_MD` at `:151`) | NOT run (UNVERIFIED). CommonMark only; it does not read Slack `*bold*` / `~strike~`. Deleting the markers over-reads on purpose (the safe side). Licence file not read. BS-5 runs it once on rows H01-H06 and C01-C08 to confirm it adds no row. | nothing | n/a | CUT (not used), measured by BS-5 |
| decoding (`runmap.undo`) | entities, percent, backslash, JSON to a fixed point | 2 | `runmap.py` read; rows H08-H10 pass today because of it | nothing | exact | CUT-TO-CONFIG+GLUE |
| folding and scanning (`textnorm.fold`, `scan_views`, `scan_holds`, `scan_cache`) | look-alikes, accents, case, separators, one inserted character | 2 (P1b, merged first) | V6 (run 2026-11-07 on `0d843b4`) | no second normaliser is written (order 146 2(c)) | exact for the P1b-documented coverage; best effort beyond (script minimums) | CUT-TO-CONFIG+GLUE |
| squeezed and case-folded pattern pass | find an UNKNOWN pattern-shaped key written in lower case, split over lines or with one inserted character (H31-H33) | 2 (the same patterns, a new view) | UNVERIFIED: over-matching not measured. BS-2 measures it first. | the pattern set run on two more views, learning only | exact for key shapes the pattern set has; false-learn rate bounded by BS-2 | KEEP-CODE (small) |
| the residue rule (`finish`) | decide whether a known value is still readable with placeholders put back | 4: detect-secrets, gitleaks, Presidio find secret SHAPES; none compares a text with OUR run map (P1c BS-1 ran gitleaks 8.30.1 on base64 rows, `tickets/P1c.md:16`) | not run here (UNVERIFIED for this need); test idea: H23 (a known value in lower case has no secret shape for a shape tool) | redaction before a person (R447 guarantee) | exact for known values | KEEP-CODE, about 80 lines (estimate; revision-1 prototype 72) |
| defang after redaction | `[.]` must not split an e-mail or host before the redactor | 2 (`gate.sanitise_text`) | V8 | one parameter and one call after `redact_text` | exact | KEEP-CODE, about 15 lines |
| `LookalikeCopy` | one refusal class shared with P2d-2 | 2 (design text) | read | 3 lines | n/a | KEEP-CODE |
**80 percent (R448):** 8 needs (read as rendered; decode; fold; unknown shapes in other views; decide what is still readable with placeholders put back; fail closed at the choke point; mask before our own markup; bound the cost). Rungs 2 and 4 give 4 = 50 percent; no library works inside the choke point. Under 80 percent; a guarantee path in any case. **Cost (R450 b, estimates):** build 10-14 agent-hours (the scope grew from revision 1: the model path, H31-H35, measurements) plus uncapped review rounds; 0 fees, 0 model tokens, 0 new dependency; upkeep about 200 lines.

## Goals and Non-Goals
**Goals.** (G1) No known value (run map or pattern-found in a healing view) is readable in any text `redact_text` returns or any card `clean` returns, for the families in the rows below. (G2) One implementation at the one choke point; `clean`, `SlackChannel._blocks`, documents, tool results, tool errors, logs and `redact_value` get it without a new call site. (G3) A text the rule cannot clear is withheld in a stated way: a card is not posted and is not retried; model-bound text becomes a fixed notice; an operator log line says why. (G4) The false-withhold rate is measured and has a ceiling (BS-3). (G5) E-mail addresses and internal host names are masked in cards (H26, H27).
**Non-Goals.** (N1) An unknown secret with no pattern (guarantee-class table above). (N2) Fixing what a person types into a free-text field after the card is posted. (N3) `tools._secret_forms` (handed-out secrets, 11 fixed spellings): owned by P2d-2; P1d only exports `healing_views` for it (test T-API below). (N4) Putting a web console in place: the card text names the request id and says to ask the operator (R6).

## Alternatives considered (each rejected with a concrete reason)
- **A1 Heal and show** (what `redact_text` does for its `undo` views, `runmap.py:~422-429`: show the redacted healed view instead of the original). Rejected for the general rule: it works for views that only delete or decode, but a fold or case-fold view changes the characters (a key in lower case would be shown in lower case, a changed text the person did not write), the card text would differ from the request the approver is asked to approve (an approval-binding risk), and the card for `AKIA**IOS...**` would lose the bold markers a person wrote. Kept as a trigger: if BS-3 shows a false-withhold rate above the ceiling for deletion-only views, A1 is used for those views only.
- **A2 Offset-mapped masking** (delete-only views keep an index back to the source, so the exact span including the markers is replaced by a placeholder). Rejected for now: offsets exist only for deletion views; entity, percent and fold views change length, so full coverage needs span tracking inside `textnorm` (not built, P1b is frozen for it). Trigger: a measured false-withhold rate above the ceiling in the pilot.
- **A3 Escape the markers in the shown text** (`**` becomes `\*\*`). Rejected: it does not help a person on Slack `plain_text` (the characters are the same) and breaks code in cards.
- **A4 Check only in `clean`** (revision 1). Rejected by both reviewers and by the lead: the model path has the same hole (S1-S5), `_blocks` is a second call site, and a second copy of the rule would drift from the P2d-2 copy.
- **A5 Pre-mask only e-mail and host before the gate** (revision 1). Rejected: it covered two kinds by the evidence of one broken test; the gate's defang changes any dotted run ending in a TLD (`gate._DOMAIN`, `gate.py:112`). Replaced by moving the defang after redaction (BS-4 checks every kind).
- **A6 A library (Presidio, detect-secrets, gitleaks, markdown-it-py)**: see the rung table; none knows the run map.
- **Chosen:** healing views + learning pass + residue rule inside `redact_text`; withhold by default, raise for cards.

## Risks and Mitigations
- R1 False withholds (a normal text refused). Mitigation: the rule withholds only when a KNOWN value is readable in a healing view of the dropped form (a normal text has no known value); ceilings measured in BS-3; F rows.
- R2 Cost on large texts (documents are large). Mitigation: windows (below), views capped, one clock, a deterministic character cap; measured at the cap and at cap+1 in BS-4.
- R3 The squeezed pass over-learns (a hash or an identifier read as a key). Mitigation: BS-2 measures the learn rate on made-up prose, JSON, base64, hex digests, UUIDs, code; any pattern whose squeezed-view false-learn rate is above 0 on the corpus is restricted to its own exact shape and length (the AKIA / ASIA shape is exactly 20 characters).
- R4 A model-path run ends or a document silently disappears. Mitigation: the notice sentence is visible to the model and to the operator log; `redact_untrusted` documents get the notice, not an exception; a run is never ended by a withhold.
- R5 Guard-test change. Mitigation: the learning calls are internal functions of `runmap`, not calls of the public `redact_text`, so the hook lint of `test_k5_round11.py` needs no exemption (BN-P1d-3); if the builder finds otherwise, the exemption is by (file, function) and the lint gets an assertion that each exempt function discards its result.
- R6 The card says "open the full request in the console": the console route is UNVERIFIED. Mitigation: the card says "ask the operator to review request `<approval_id>`"; the id is public in the card header.
- R7 P1b changes under P1d. Mitigation: BS-0 pins the P1b head; P1d does not call anything private of `textnorm`.
- R8 Over-masking from the `&` fix (H34). Mitigation: measured on query-string rows (F16); the safe side is masking one extra parameter.

## Sinks (who reads the text, and which views apply)
| sink | how the text is rendered | what a reader can re-join | views applied |
|---|---|---|---|
| Slack card (`SlackChannel._blocks`, `plain_text`) | markers shown literally (no Markdown) | a person copies `AKIA**IOSF...**` by hand; an entity shows `&amp;`; a colour code shows as junk or nothing | all healing views (the person re-joins) |
| Markdown viewer / console, `notify` top-level text | CommonMark or mrkdwn may join the pieces | the viewer shows the key whole | all |
| `FakeChannel` / log | verbatim | same as a person | all |
| model (documents, tool results, tool errors, `safe_head`, `redact_value`) | tokenised verbatim | a model re-joins split pieces and may echo them | all |
So the rule is the same for every sink (the reader on the weakest sink decides). The revision-1 claim that Slack shows the key joined is withdrawn (IR-1-3); the person re-joining it is the reason Slack still refuses.

## Template fields
- **Package id and name:** P1d, "split secrets at the choke point". One pull request on branch `core/P1d`, from main after P1a and P1b merge.
- **Path class:** redaction AND security. **Extended review (no round cap): yes**, plan and result.
- **Depends on (merged first):** the preconditions above. `designs/lookalike-leak.md` (FROZEN draft 11) gives the refusal class and the count rule; P1d builds `LookalikeCopy` and the count rule first and P2d-2 calls them (BN-P1d-5). Not dependent on P1c; P1c edits `redact.py` HOSTNAME (row H27 changes from partial to whole when P1c lands).
- **Class (R337, R7):** "a value is matched only in the spelling as written, while a reader or renderer reads another spelling": markup, case, line breaks or one inserted character between the characters of a value. Standards: CommonMark 0.31 sections 6.2, 6.1, 2.5; ECMA-48 sections 5.4, 8.3; Unicode UAX #15 and UTS #39. All cited from memory, not re-read today (UNVERIFIED read date).
- **Source of the code:** our own code only; no library code is copied.
- **Target modules:** `src/hadavin_sdk/guard/runmap.py` (the rule; `redact_text` change), `approvals/channel.py` (call with `on_residue="raise"`, defang after redaction), `approvals/slack_channel.py` (`_blocks`), `approvals/requests.py` (the fallback sentence), `approvals/gate.py` (`defang` parameter), `guard/redact.py` (SECRET value grammar for `&`; unanchored learning shape for H35), `k1b/redaction.py` (`sensitive` uses `healing_views`; sibling S11), `approvals/receiver.py` (`log_message` goes through `safe_head`; sibling S16).
- **Interface (every new name; no signature of an existing public function loses an argument):**
  - `runmap.LookalikeCopy(RedactionError)`; `runmap.WITHHELD_NOTICE: str` (constant, plain sentence).
  - `runmap.healing_views(text: str, *, clock: Callable[[], float] = time.monotonic, deadline: float | None = None) -> tuple[str, ...]` (public, one place; the views listed in "Healing views", built to a fixed point: every step is applied again to every new view until no new view appears; the number of views is capped by `defaults.P1D_MAX_VIEWS`; more raises `InputTooLarge`).
  - `runmap.finish(source: str, shown: str, mapping: Mapping[str, str], *, clock=time.monotonic, deadline: float | None = None) -> None` (public, raises `LookalikeCopy`): the learning pass, the dropped-form test and the put-back count test. `source` = the text exactly as given to `redact_text` (after NUL removal, before the neutralise hook); `shown` = the text `redact_text` would return; `mapping` = the run map after the call (including the seeded entries; seeds are skipped).
  - `runmap.redact_text(text, mapping, neutralise=None, *, on_residue: Literal["withhold", "raise"] = "withhold") -> str`: after the existing passes it calls `finish`; on `LookalikeCopy` it returns `WITHHELD_NOTICE` (logging one operator line `hadavin_sdk.guard.runmap` WARNING: `redaction withheld a text: reason=residue chars=%d views=%d known=%d`) or re-raises when `on_residue="raise"`. The existing `except (InputTooLarge, TooDeep)` at `redact_text` also names `LookalikeCopy` so it is not re-wrapped (IR-1-7).
  - `defaults.py`: `P1D_MAX_VIEWS` (decided by BS-4), `P1D_WINDOW_CHARS`, `P1D_WINDOW_OVERLAP`, `P1D_MAX_TEXT_CHARS`, `P1D_MIN_KEY_CHARS`. No literal threshold in code. The 12 and 8 of revision 1 are NOT constants any more: the minimum scan length is whatever `textnorm.scan_holds` accepts (design-1-5); on `textnorm.ViewTooShort` the value is searched by exact substring in the plain AND the case-folded dropped form (so a lower-case copy of an 8-11 character password is still found, rows B01-B06).
  - `gate.sanitise_text(text, *, defang: bool = True)` and `gate.defang_text(text)`; `clean` runs the hook with `defang=False` and defangs the returned text.
- **Behaviour, exactly (pseudocode names are the build's names):**
  1. `redact_text` strips NUL, then if `len(text) > P1D_MAX_TEXT_CHARS` it processes the text in windows of `P1D_WINDOW_CHARS` characters overlapping by `P1D_WINDOW_OVERLAP` (the overlap is at least the longest width any pattern can match, a constant derived from the pattern set and tested; rows W01-W03), collecting known values over all windows and running the residue test per window against the whole set. Below the cap it is one window. (Cost is linear in the number of windows; V9's super-linear growth is per window.)
  2. Per window: build `healing_views` (one clock, one `deadline = clock() + REDACT_BUDGET_S` started at the top of `redact_text`; every loop checks it; past it raises `InputTooLarge`). Views outer, values inner, inside `textnorm.scan_cache()` (V9).
  3. Learning: run the existing patterns on every view (output discarded) AND on the squeezed and case-folded views; keep non-seed originals found: these are the known values (with the map's own). The unanchored shape of the AKIA / ASIA key (20 characters, no leading `\b`) is learned too, for H35.
  4. Residue rule on `shown`: `dropped` form tested against each known value: a value that `scan_holds` cannot scan (`ViewTooShort`, `EmptyView`) is searched exactly in the plain and case-folded dropped forms; any other `textnorm.TextnormError` withholds. Then the put-back count test of `designs/lookalike-leak.md` section 5 item 3 (`c > e` withholds), with the key minimum `P1D_MIN_KEY_CHARS`.
  5. Pattern fixes in `redact.py`: (a) the SECRET assignment value extends over `&` up to white space, a quote or `;` (H34); (b) none other: H35 is covered by the unanchored learning shape of item 3 (the redactor's own `\b` patterns stay unchanged, so existing behaviour does not change).
  6. `clean`: NUL removal, then ONE `redact_text(text, seeded, neutralise=_neutralise, on_residue="raise")` (the hook is `gate.sanitise_text(..., defang=False)` plus `withhold_commands`), then the joined pass (`_TAGS.sub`) with the same call, then `defang_text` on the result. The pre-mask of revision 1 is deleted. Fallback if BS-4 finds a kind the moved defang still breaks: a documented per-kind pre-mask for exactly that kind (BN-P1d-8).
  7. `SlackChannel._blocks`: the same call with `on_residue="raise"`; on `LookalikeCopy` it posts ONE fixed card `Request <approval_id> cannot be shown safely. Ask the operator to review it.` WITHOUT buttons (the existing `approver_ids is None` branch) and logs the operator line. `SlackChannel.update` and `send` use the same path, so a refused request is posted once, has no buttons, and `resend_unsent` finds `sent_at` set (no retry loop). The request can be decided only by an operator route, or it expires (R6).
  8. `requests.summary`: for `LookalikeCopy` the fallback line becomes `Inputs: not shown. They may hold a password or key written with formatting inside it. Ask the operator to review request <approval_id>.` (`TooDeep` and `InputTooLarge` keep today's text).
  9. `agent_loop._deliver` (`agent_loop.py:~560-567`) swallows channel exceptions into an undelivered card today; with items 6 to 8 nothing raises there for this class, and a test pins that.
- **Existing core code reused (checked):** as in the rung table. Checked and not reused: `textnorm.register_value`, `tools._secret_forms`.
- **Security and least-privilege notes:** no identity, right, secret or config beyond five constants. Test values are built from parts; the only whole-key literal is the AWS documentation example key. The learning pass holds found originals in memory for the call only; nothing is stored or logged (the operator line carries counts, never content; a test greps the log text for the key).

## Failing inputs, one named negative test per row (`tests/test_p1d_*.py`; K = `AKIAIOSFODNN7EXAMPLE` (the allowed literal), K4 = `AKIA`, K16 = `IOSFODNN7EXAMPLE`; S = a 27-character made-up secret built from parts, S5/S22 its first 5 and last 22 characters; E = a made-up e-mail built from parts)
Expected "withheld" means: `redact_text` default returns `WITHHELD_NOTICE`; `clean` raises `LookalikeCopy`. Every fb row fails on the base commit by an assertion (the base returns the key).
| row | input | on base | expected after P1d | test name |
|---|---|---|---|---|
| H01 | `key AKIA**IOSFODNN7EXAMPLE** here` | key shown | withheld | `test_h01_bold_markers_inside_key_withheld` |
| H02 | `AKIA**IOSFODNN**7EXAMPLE` | shown | withheld | `test_h02_bold_markers_mid_key` |
| H03 | `AKIAIO*SFODNN7EXAMPLE*` | shown | withheld | `test_h03_italic_star` |
| H04 | `AKIA~~IOSFODNN7EXAMPLE~~` | shown | withheld | `test_h04_strike` |
| H05 | ``AKIA`IOSFODNN7EXAMPLE` `` | shown | withheld | `test_h05_code_span` |
| H06 | `AKIA_*IOSFODNN7EXAMPLE*_` | shown | withheld | `test_h06_slack_bold_italic` |
| H07 (pb) | `AKIA<b></b>IOSFODNN7EXAMPLE`, `AKIA<!-- -->IOSFODNN7EXAMPLE` | masked | masked, same output | `test_h07_html_tags_still_masked` |
| H08 (pb) | `AKIA&ZeroWidthSpace;IOSFODNN7EXAMPLE`, `&shy;`, `&NoBreak;`, `&InvisibleTimes;`, `&#8203;`, `&#x200B` (no `;`), `&amp;#8203;` | masked | masked, same | `test_h08_invisible_entities_still_masked` |
| H09 (pb) | `AKIA&#73;OSFODNN7EXAMPLE` (and hex `&#x49;`, and `&#73` no `;`) | masked | masked, same | `test_h09_letter_entities_still_masked` |
| H10 | `password=<S>` then `<S5>&amp;<S22>` | 2nd copy shown with `&` | withheld | `test_h10_known_value_split_by_entity` |
| H11 | `AKIA\x1b[0mIOSFODNN7EXAMPLE` | shown as `AKIA IOSF...` | withheld | `test_h11_ansi_csi` |
| H12 | four variants: `\x1b[38;5;196m` inside the key; C1 `\x9b0m`; OSC `\x1b]0;t\x07`; OSC 8 link `\x1b]8;;http://x\x07` | shown | withheld, each its own parametrised case (builder measures all four, replacing the revision-1 count that had three) | `test_h12_ansi_variants` |
| H13 | `AKIA\\x1b[0mIOSFODNN7EXAMPLE` (escape written as text) | shown | withheld (over-refusal risk noted in R1; a person reading `\x1b[0m` literal sees the key joined) | `test_h13_ansi_written_as_text` |
| H14 | `AKIA\x1bIOSFODNN7EXAMPLE` (lone ESC eats one letter) | 19 of 20 characters shown | withheld | `test_h14_lone_escape` |
| H15 | `x\x08AKIAIOSFODNN7EXAMPLE` and `AKIA\x08IOSFODNN7EXAMPLE` | shown | withheld | `test_h15_backspace` |
| H16 | `AKIA\rIOSFODNN7EXAMPLE` | shown on two lines | withheld | `test_h16_carriage_return` |
| H17 (pb) | BEL, DEL, NEL `\x85`, VT, FF, NUL, ZWSP, ZWJ, WJ, U+202E, soft hyphen, each once between `AKIA` and `IOSFODNN7EXAMPLE` | masked | masked, same | `test_h17_controls_and_invisibles_still_masked` |
| H18 | `AKIA` + U+0301 + `IOSFODNN7EXAMPLE`; U+0323 variant | shown | withheld (both variants measured by the builder) | `test_h18_combining_mark` |
| H19 (pb) | the key in full-width forms | masked | masked | `test_h19_fullwidth_still_masked` |
| H20 | `AKIA` + U+FF0A (full-width `*`) + `IOSFODNN7EXAMPLE` | shown | withheld. Revision 1 labelled this "refused (measured)" while its own rule order could not refuse it (fold ran last); the fixed-point `healing_views` (fold, then delete markers again) does | `test_h20_fullwidth_marker` |
| H21 | Cyrillic `А` for both `A` of `AKIA` | shown | withheld | `test_h21_cyrillic_lookalike` |
| H22 | `password=<S>` then `<S5>**<S22>**` | 2nd copy shown | withheld | `test_h22_known_bold_split` |
| H23 | `password=<S>` then S in lower case | shown | withheld | `test_h23_known_other_case` |
| H24 | `password=<S>` then `<S5>\n<S22>` | shown | withheld | `test_h24_known_split_line` |
| H25 | `password=<S5>\x1b[1m<S22>` | `<SECRET_1> ` + tail shown | withheld | `test_h25_value_cut_by_escape` |
| H26 | `contact <E> please` (E = `anna.m@example.org` built from parts) | `anna.m@example[.]org` shown | `contact <EMAIL_1> please` | `test_h26_email_masked_before_defang` |
| H27 | `host db01.corp.example.com down` (the exact string, `.corp` is in the HOSTNAME pattern) | defanged text shown | `host <HOSTNAME_1> down` after P1c; `<HOSTNAME_1>.example.com` today (partial), asserted as the exact string the builder measures on the base | `test_h27_host_masked_before_defang` |
| H28 | `anna.m**@example.org**`, `anna.m@exam\x1b[0mple.org` | shown | withheld | `test_h28_email_split` |
| H29 | `passwor<span></span>d%3D<v1>%0D<v2>` (v1, v2 made up, 12 chars each) | tail shown | masked tail; NEW named test (the existing fuzz test stays green; it was already green on base, so it is not a fail-before) | `test_h29_tag_and_encoded_tail` |
| H30 | H01's input as `req.summary` through `SlackChannel._blocks`, plus the output of `requests.summary` of a plan whose input holds the key split by `**` | shown | one fixed card, no buttons, no key; no retry | `test_h30_slack_block_path` |
| H31 | `AKIAIOSFODN\nN7EXAMPLE` (key split over two lines, no key word, NOT in the map) | shown | withheld (squeezed pass learns it) | `test_h31_unknown_key_split_line` |
| H32 | `akiaiosfodnn7example` (lower case, NOT in the map) | shown | withheld (case-folded pass learns it) | `test_h32_unknown_key_lower_case` |
| H33 | `AKIA&amp;IOSFODNN7EXAMPLE`, `AKIA.IOSFODNN7EXAMPLE`, `AKIA\*IOSFODNN7EXAMPLE` (one character INSERTED) | shown | withheld | `test_h33_unknown_key_inserted_character` |
| H34 | `password=ab12&cd34ef56gh78ij` | `<SECRET_1>&cd34ef56gh78ij` shown | `<SECRET_1>` covers the whole run (the tail is masked); `password=<S5>&amp;<S22>` also masked | `test_h34_value_with_ampersand` |
| H35 | `keyzAKIAIOSFODNN7EXAMPLE` (glued to a word) | shown | withheld (unanchored learning shape) | `test_h35_glued_key` |
| H40 | H01 as a plan input through `requests.summary` then `FakeChannel.send` | key shown | the fallback line of item 8 and no key; `FakeChannel` records one send, no retry (pins what a person sees) | `test_h40_fallback_card` |
**Combination rows (design-1-3: views reached by fixed point):**
| row | input | expected | test name |
|---|---|---|---|
| C01 | `AKIA**` + Cyrillic `О` + `SFODNN7EXAMPLE**` (marker + look-alike) | withheld | `test_c01_marker_and_lookalike` |
| C02 | `AKIA**IO` + U+0301 + `SFODNN7EXAMPLE` (marker + combining mark) | withheld | `test_c02_marker_and_combining` |
| C03 | `AKIA&ast;&ast;IOSFODNN7EXAMPLE` (entity-encoded marker) | withheld | `test_c03_entity_marker` |
| C04 | `AKIA&amp;ast;IOSFODNN7EXAMPLE` (double-encoded marker) | withheld | `test_c04_double_entity_marker` |
| C05 | `AKIA\x1b[0m**IOSFODNN7EXAMPLE` (entity + ANSI order, ANSI + marker) | withheld | `test_c05_ansi_and_marker` |
| C06 | `AKIA\x1b[0m\nIOSFODNN7EXAMPLE` (ANSI + line break) | withheld | `test_c06_ansi_and_newline` |
| C07 | `akia**iosfodnn7example` (lower case + marker, not in the map) | withheld | `test_c07_case_and_marker` |
| C08 | `AKIA%2A%2AIOSFODNN7EXAMPLE` (percent-encoded marker) | withheld | `test_c08_percent_marker` |
**Length boundary rows (scan minimum; design-1-5), value = a made-up password of the stated length, known (in the map) and written lower case and upper case in a later copy:** B01 10 chars lower, B02 10 chars upper, B03 11 lower, B04 11 upper, B05 12 lower, B06 12 upper, B07 13 lower, B08 13 upper: every one withheld (`test_b01..b08`). Window rows: W01 secret straddling the window boundary by 1 character before, W02 exactly at, W03 1 after the overlap start: withheld. Cap rows: X01 text of `P1D_MAX_TEXT_CHARS`, X02 of cap+1 characters: both complete under the budget (windows); X03 a text whose view count would pass `P1D_MAX_VIEWS` withholds with reason `views` (`InputTooLarge`).
**False-withhold rows (must pass, output unchanged against base except where noted):** F01 `Approve **restart** of `web-01` in ~~old~~ demo?`; F02 placeholders already in the text (seeds not put back); F03 a commit id and a 64-hex digest in code spans; F04 a Markdown table with bold and code; F05 `Tom &amp; Jerry &lt;ok&gt; &#169; 2026`; F06 `\x1b[32mok\x1b[0m done`; F07 the same dotted address twice (`10.0.0.1`, ViewTooShort path: exact search, not a withhold); F08 ``run `make`test``; F09 `password=<S>` (masked as today); F10 an accented name `José Müller`; F11 a 3,000-character card (timing saved, deadline asserted); F12 a stored value holding a shorter known value (an ARN with its 12-digit account id); F13 Greek and Cyrillic prose words; F14 (decision, was NEEDS-LEAD 4) ``` `<25 letters and digits>`/`<26 letters and digits>` `` withheld by the prototype (deleting the backticks joins two identifiers into a 52-character run that the high-entropy pattern masks; plain spelling is masked today): decision: keep withholding, count it in the BS-3 rate; F15 a URL with a query list `https://x.example/?a=1&b=2` (no secret key word: unchanged); F16 `password=hunter22&user=bob` (H34's over-mask: the output masks `hunter22&user=bob`; a row pins the new text); F17 a long paragraph of ordinary prose with `**` and `*` and `~~` (2,000 characters). Named `test_f01..f17`.
**Sibling rows:** T-API `test_healing_views_is_public_and_stable` (P2d-2's use: `healing_views("AKIA**IOSFODNN7EXAMPLE**")` contains `AKIAIOSFODNN7EXAMPLE`); S1 to S5 (model path): the same input as H01 through `redact_untrusted`, `prepare_output`, `error_reason`, `safe_head`, `redact_value`: each returns text without the key (the notice); S11 `k1b.redaction.sensitive` with key names `db_pass` + U+200B + `word`, `db_p` + Cyrillic `а` + `ssword`, `db-pass**word**`: all sensitive; S16 `receiver.log_message` with a `?t=<K>` query logs the masked text; a `LookalikeCopy` log line never holds the key (grep).

## Build steps before any code (BS) — each has a stated output
- **BS-0** list the 5 failing baseline tests with the cause; pin the P1b head; check the preconditions.
- **BS-1** the model-path false-withhold measurement: a made-up corpus of 500 documents/tool results (prose, JSON, logs, markdown) run through the new `redact_text`; report the withhold rate. Ceiling: 0 withholds on the 500 (any withhold is listed and either fixed or justified by a real hidden value).
- **BS-2** the squeezed and case-folded learning pass: false-learn rate per pattern on the same corpus plus hex digests, UUIDs, base64 blobs, 2,000 lines of code. Restrict any pattern that learns something on ordinary text (R3).
- **BS-3** the card path: the F rows and a corpus of 500 made-up cards; ceiling 0 withholds on non-secret cards.
- **BS-4** cost: `healing_views` and `finish` at 3,000, 30,000 and 120,000 characters, at the window size and at the cap and cap+1; the cost of the defang move on every pattern kind (31 kinds: a made-up sample of each through the redactor on raw text and on gated text, listing every kind where the output differs). Choose `P1D_*` values from these numbers; the single clock is `time.monotonic`, the tests stub the `clock` argument.
- **BS-5** the one-off `markdown-it-py` comparison on H01-H06, C01-C08.

## Mutation plan (`tests/p1d_mutants.py`; each mutant with its killer and the literal input)
| mutant | planted change | killer |
|---|---|---|
| M1 | `finish` not called in `redact_text` | `test_h01_...` input `AKIA**IOSFODNN7EXAMPLE**` |
| M2 | `_blocks` posts the text unchecked | `test_h30_...` |
| M3 | ANSI-deleting view removed | `test_h11_ansi_csi` |
| M4 | the escape-written-as-text view removed | `test_h13_...` |
| M5 | `strip_controls` view removed | killer `test_h16_carriage_return` (`AKIA\rIOSFODNN7EXAMPLE`); revision 1 named H15 too. Equivalence decision: `gate._views` already adds `strip_controls` (`gate.py:212-220`) and `_CONTROL_CHARS` covers the range, so if the build keeps `gate._views` as a source of views, M5 is EQUIVALENT and is declared so with that reason; if `healing_views` builds its own control step, M5 is a real mutant killed by H16 |
| M6 | `_rendered` / marker deletion removed | `test_h01_...` through `test_h06_...` |
| M7 | `undo` removed from the views | `test_h10_...` (`<S5>&amp;<S22>`) and `test_h29_tag_and_encoded_tail` |
| M8 | tag-deleting view removed | `test_h29_...` |
| M9 | fold view removed | `test_h21_...`, `test_h18_...` |
| M10 | marker deletion NOT applied again after fold | `test_h20_fullwidth_marker`, `test_c01_...` |
| M11 | view-step order changed (fold before delete) | `test_c02_...` |
| M12 | learning pass removed (map values only) | `test_h31_...` (unknown key) |
| M13 | squeezed view removed from the learning pass | `test_h33_...` |
| M14 | case-folded view removed from the learning pass | `test_h32_...` |
| M15 | put-back without the two spaces | the lookalike input of `designs/lookalike-leak.md` LK-JAMO-PB copied into `test_lk_jamo_pb` |
| M16 | placeholders left in place instead of put back | `test_h25_...` |
| M17 | dropped-form test removed | `test_h25_...`, `test_h22_...` |
| M18 | `c > e` becomes `c >= e` | `test_f09_...` |
| M19 | `TextnormError` swallowed as "no hit" | `test_textnorm_error_withholds`: a value `scan_holds` refuses (built from the lookalike LK-UNFOLD input) |
| M20 | `ViewTooShort` fallback removed (value skipped) | `test_b01_...` (10 chars) |
| M21 | threshold edge: scan minimum off by one (`<` vs `<=`) | `test_b03`, `test_b05`, `test_b07` |
| M22 | longest-first removed from any replacement | `test_longest_first_placeholder`: `a@b.example.com` inside `x@a@b.example.com` |
| M23 | seed entries put back | `test_f02_...` |
| M24 | defang before redaction again (move undone) | `test_h26_...` |
| M25 | deadline never checked / second clock | `test_deadline_stub`: `clock` stub jumping past `deadline` after the first view, expects `InputTooLarge` |
| M26 | `LookalikeCopy` caught inside `clean` and the text returned | `test_h01_...` asserts `type(exc) is LookalikeCopy` |
| M27 | `mapping` vs `joined_map` mix-up when the joined pass is returned | `test_joined_pass_uses_its_own_map` (an input where only the joined text holds a known value) |
| M28 | window overlap 0 | `test_w01..w03` |
| M29 | `&` fix removed from SECRET | `test_h34_...` |
| M30 | unanchored shape removed | `test_h35_...` |
| M31 | `LookalikeCopy` and `InputTooLarge` swapped in `requests.summary` (the split) | `test_h40_fallback_card` |
| M32 | log line holds the content | `test_operator_log_has_no_content` (grep for the key) |
Mutation runner: `tools/mutation_runner.py` if on the base (precondition 3), else a subprocess loop in the same file; every mutant restored in a `finally`, the tree checked clean at the end.

## Fail-before proof
The new test files run on the base commit first (`git worktree add <tmp> <base>`, copy only the new test files and `tests/fixtures`, `uv run --all-extras --group test pytest <files>`): every fb row (H01-H06, H10-H16, H18, H20-H35, H40, C01-C08, B01-B08, W01-W03, S1-S5, S11, S16, T-API) must FAIL by assertion (never by an import error: imports of `textnorm` are inside functions on the base, where a missing module is an assertion failure through a helper that raises `AssertionError`); every pb and F row must PASS. No strict-xfail rows remain. Raw output to `handover/evidence/P1d/fail-before.txt`.

## Evidence commands (EVIDENCE RUNNER, a separate agent)
`ruff check`, `ruff format --check`, `pytest` full on Python 3.12 and 3.13, `bandit -ll`, `python tests/p1d_mutants.py` (32 mutants, alone), the F11 timing and BS-4's sizes (alone, no other heavy job), the BS-1 to BS-3 corpus runs. Raw output to `handover/evidence/P1d/evidence-<n>.md`; every log carries the head SHA on line 1.

## Build notes (BN-P1d-n)
- BN-P1d-1: cite the base SHA; rebase on whatever main holds after P1b merges and re-run the fail-before proof there too.
- BN-P1d-2: correct `gate._rendered`'s docstring (an entity that decodes to a visible character joins nothing; it inserts it; row H33 is that case).
- BN-P1d-3: the learning calls are internal functions of `runmap`, not calls of the public `redact_text`; the hook lint of `test_k5_round11.py` keeps working unchanged. If it does not, exempt by (file, function) with an assertion that the result is discarded.
- BN-P1d-4: views outer, values inner (V9).
- BN-P1d-5: P2d-2 calls `runmap.finish` / `healing_views`; the count rule has one copy.
- BN-P1d-6: test texts never say "staging", "dev" or "test" as a stage name (R449); F01 says "demo".
- BN-P1d-7: remove the `gate._rendered` entry from `vulture_whitelist.py` in the same pull request (when the file exists on the base).
- BN-P1d-8: the per-kind pre-mask fallback of item 6, only for a kind BS-4 lists.

## Owner-facing wording (CHANGELOG and the card; plain words, checked against rule 14)
- Card line (new): "Request <id> cannot be shown safely. It may hold a password, key or e-mail address written with formatting inside it, which we cannot hide with certainty. Ask the operator to review it." Posted once, without approve buttons.
- Model-bound text: "(withheld: this text may hold a secret written with hidden formatting)".
- CHANGELOG, Upgrade steps: "Text shown to a person or sent to a model: a password, key or e-mail address written with formatting characters inside it (bold or italic markers, a terminal colour code, a backspace, an accent mark, look-alike letters, another letter case, a line break or one extra character such as `&` or `.`) is no longer shown. An approval card for such a request is posted once without buttons, and an operator log line says why. Text sent to a model is replaced by a short notice. E-mail addresses and internal host names in approval cards are now replaced by placeholders (before, they were shown with `[.]` in place of each dot). A password that contains `&` is now hidden up to the next space. Not covered: a secret that no pattern recognises and that is not already known (a plain password with no key word before it)."
- Sentence for the owner's status message: "We found a gap where a key, password or e-mail address written with formatting characters inside it could be shown on an approval card or sent to the model. The fix is being built. Until it is merged, such values can be shown, so no real client data goes through this software."

## Ledger rows (`handover/ledger.md`; severity by the author, the lead confirms)
| id | package | severity | summary | status |
|---|---|---|---|---|
| BL-core-p1d-001 | P1d | BLOCKER | `clean` and `redact_text` show a key split by markers, escapes, controls, accents, look-alikes (H01-H25) | OPEN |
| BL-core-p1d-002 | P1d | BLOCKER | `clean` never masks e-mail and internal hosts (gate defang before redaction, H26-H28) | OPEN |
| BL-core-p1d-003 | P1d | MAJOR | `SlackChannel._blocks` second `redact_text` outside the check (H30) | OPEN |
| BL-core-p1d-004 | P1d | BLOCKER | the same split key passes every model producer (S1-S5); now in scope | OPEN |
| BL-core-p1d-005 | P2d-2 | MAJOR | handed-out secret echoed in another case or with markers (S6); P2d-2 uses `healing_views` | OPEN |
| BL-core-p1d-006 | P1d | MAJOR | `k1b.redaction.sensitive` misses disguised key names (S11); now in scope | OPEN |
| BL-core-p1d-007 | P1d | MAJOR | SECRET value ends at `&` (H34); now in scope | OPEN |
| BL-core-p1d-008 | P1d | MAJOR | glued, dotted or `&`-inserted key passes (H33, H35); now in scope | OPEN |
| BL-core-p1d-009 | P1d | MINOR | `receiver.log_message` logs a callback URL unredacted (S16); now in scope | OPEN |
The lead's cilint ledger row `BL-hadavin-sdk-cilint-001` (ORDER 146) is the parent of 001 to 004; the lead confirms the link.

## EGM steps needed, in order (R374, rule 13)
(1) brainstorm: not run, revision 1 serves as the brief (ORDER 165 item 9 keeps the draft step; the brainstorm was not asked for); (2) this draft (revision 2, `egm:egm-draft`, 2026-11-09); (3) plan review round 2: `egm-design` + `egm-implementation-readiness` (+ `egm-zoom-out` for scope: the scope grew), fresh agents, given this ticket, the sibling report and the evidence file only; (4) `egm:egm-resolve`; repeat (3)-(4) until a round finds no blocker or major (redaction path, no cap); (5) build after P1b merges; (6) EVIDENCE RUNNER; (7) result review by `egm:*` reviewers; (8) resolve, repeat until clean; (9) `egm:egm-drift-report`.

## Slot needs (rule 17)
Build iterations: only the new test files and the 10 clean-related files (about 1-2 minutes). Final head, once: full suite on 3.12 and 3.13 (2 slots), the 32-mutant run (1 slot, alone with at most the other-Python suite), BS timing rows (1 slot, ALONE). Real clock estimate: build 10-14 hours, evidence 1-2 hours, each review round 1-2 hours. P2d-2 and P5c also read `channel.py`: a rebase conflict, no slot conflict. P1d is first in the build queue after the P1b fix batch (ORDER 165); it blocks the P1b/PR 63 pilot merge.

## OPEN QUESTIONS for the lead (what this draft could not decide)
1. Does the lead accept the default `on_residue="withhold"` for ALL model-path callers (document replaced by a notice)? The alternative is `"raise"` and ending the run; I recommend withhold (a run keeps going, the operator log shows why). BS-1 gives the rate.
2. The H34 fix masks `&user=bob` after `password=hunter22` (over-mask, safe side). Accept, or restrict to tails that do not look like `&name=`? I recommend accept (the safe side; F16 pins it).
3. Is there an operator route (a console) that can decide a request whose card was withheld? UNVERIFIED. Without one, the request waits until it expires. Decide before the pilot.
4. Scope: S11 (`k1b` key names) and S16 (`receiver` log) are included here as small items; if the lead prefers separate packages, they are cut (each is about 20 lines).
5. P1b must supply the `ViewTooShort` fallback behaviour as documented (P1b fix batch is open): P1d reads `scan_holds`'s error classes only.

## UNVERIFIED (not read or not run by me in revision 2)
Every V number (revision 1's prototype, not re-run); the 5 baseline failures' cause; row H40 and the `agent_loop._deliver` claim on the built code; markdown-it-py behaviour and licence file; the window overlap constant; BS-1 to BS-5 results; the standard section numbers; Python 3.13 (only 3.12.13 ran in revision 1); the demo repositories; whether `vulture_whitelist.py` and `tools/mutation_runner.py` have reached the base.

## Rules cited
R233 (redaction fails closed), R337 (class-level fixes), R363 (no single dependency), R374 (EGM order), R447, R448 (CODE LAST, rung table), R449 (stage names), R450 (research and licence gate); studio preamble rules 3, 5, 6, 7, 12, 13, 14, 17, 19, 20, 21.

## Revision log
Rev 1 (2026-11-07): author draft without the skill. Rev 2 (2026-11-09): `egm:egm-draft` from the round-1 reviews and ORDER 165: choke point and model path in scope, H31-H35 fixed, defang moved after redaction (pre-mask removed), one public `healing_views` / `finish`, withhold semantics, sink table, rung scale and guarantee class, alternatives, risks, combination, boundary, window and cap rows, 32 mutants with killers, deterministic cap, one clock.
