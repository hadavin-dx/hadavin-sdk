# Package ticket P1d: a secret split by markup (markdown markers, an HTML entity, a terminal escape, a control character, another letter case, an inserted character) is shown unmasked by `approvals.channel.clean` and by `runmap.redact_text`. DRAFT revision 3 (egm-draft step run; plan review round 3 not yet run)

**Why this ticket is over 250 lines (template rule):** the failing-input tables are the specification (lead order 146 2(a)); about 120 lines are table rows, and the mutant table is another 25.
**Revision 3, written 2026-11-09 (UTC; IST = UTC+5:30) by the cloud session (Opus, `egm:egm-draft`), from revision 2, the three round-2 plan reviews (`reviews/P1d/round2-design.md`: 2 Blockers, 12 Majors; `round2-readiness.md`: 2 Blockers, 14 Majors; `round2-zoomout.md`: 10 Majors), my resolution of them (`reviews/P1d/round2-resolve.md`, groups G1-G12) and the lead's ORDER 165 and ORDER 166.** Text only: no code, no pull request. **Not done, first:** nothing in this ticket was run again for revision 3, and the reviewers and I read no source for it (runmap, channel, gate and textnorm are not on branch `core/cloud-handover`). Every number marked V is from revision 1's author probes (`handover/evidence/P1d/author-probes-2026-11-07.txt`, a scratch prototype that is NOT the build); every item marked UNVERIFIED is measured or read by the build step named beside it (BS-0 to BS-5) before its row counts. `egm:egm-brainstorm` was not run (no `concepts_brief.md`; revision 1 is the brief; ORDER 165 item 9 keeps the draft step). Marker: CODE-LAST v1.

## The problem in plain words
A person (or a model) is shown a text after secrets and personal data were replaced by placeholders such as `<APIKEY_1>`. The redactor reads only the text as written. If a secret is written with extra characters inside it, for example `AKIA**IOSFODNN7EXAMPLE**` (the asterisks make half of it bold in Markdown), the pattern does not match and the key is shown. The same happens with a terminal colour code, a backspace, an accent mark, look-alike letters, another letter case, a line break or one inserted character; a person re-joins the pieces by eye, a model re-joins them too. Two more holes of the same kind: the approval gate changes every `.` in a domain to `[.]` BEFORE the redactor runs, so a plain e-mail address or internal host name is never masked; and a password that contains `&` shows the part after the `&`.

## Lead rulings this revision implements
ORDER 165 (2026-11-09): (1) the fix goes inside `runmap.redact_text`, one choke point, the model path included; no P1e. (2) The squeezed and case-folded passes are measured in P1d (BS-2, BS-3); no client data before P1d is merged. (3) A refused card is a finished state (posted once, never resent) with an operator log line and a visible reason, in this package. (4) The draft step is not waived; H31 to H35 are fixed in P1d, not deferred. (5) P1b ships `textnorm`; P1d wires `redact_text` to it; P1d is a HARD DEPENDENCY of any P1b or PR 63 merge into a pilot or prod path.
ORDER 166 (2026-11-09): (1) model path: withhold the text by default, log it, fail closed, **no raise** on the model path. (2) H34 over-mask accepted; its measured rate is reported next to the false-withhold rate, separately (BS-3). (3) Operator route: use the existing route with the least new surface, name it and why here; no new endpoint without a ticket line (section "Operator route"). (4) S11 and S16: in P1d only if they sit on the `redact_text` path; otherwise ledger rows now and their own package (section "Scope of S11 and S16"). (5) The `ViewTooShort` exact fallback is accepted only with `coverage=exact_only` recorded and the client-profile strict mode still refusing (ORDER 137 D2; section "Short values").

## Words used in this ticket (defined once; one word keeps one meaning)
- **The choke point** = `guard/runmap.py::redact_text`. Every model-bound text, log text, tool result and approval card goes through it.
- **A view** = another spelling of the same text that a reader, renderer or terminal may show. **Deleting views** delete or undo something to join a split value (markers, tags, escape sequences, control characters and line breaks deleted; entities, percent-codes and escapes decoded; look-alikes folded; `[.]` read as `.`). **Matching-only views** (used by the learning pass, never by the residue test): **squeezed** (every character that is not a letter or digit removed) and **case-folded** (lower case).
- **Known value** = an original the redactor masked in this text (the run map), or one a pattern finds in a view (found by the **learning pass**: the patterns run on the views, the output is thrown away, only the found originals are kept).
- **Put-back form** = the shown text with each genuine placeholder (`<APIKEY_1>`) replaced by `" " + original + " "` (one space each side), in the text and in its decoded form; **dropped form** = each genuine placeholder replaced by one space. Both are tests of "could a person re-join the pieces".
- **Residue rule** = the final check: no known value may be readable in any deleting view of the dropped form, and no value's count `c` of scan keys in the put-back form may exceed the count `e` the put-back originals explain (formula quoted below). A known value that is still readable means the text is **withheld**.
- **Withhold** = `redact_text` does not return the text. Default (`on_residue="withhold"`): it returns the fixed sentence `WITHHELD_NOTICE` and writes one operator log line. With `on_residue="raise"` (used ONLY by the approval-card callers) it raises `runmap.LookalikeCopy`. The model path never raises (ORDER 166 item 1).
- **fb / pb / ow** = a test row that must FAIL on the base commit (fail-before: the new behaviour) / PASS on it by design and stay unchanged (guard row) / is an accepted over-withhold row, tracked separately (ow).
- **Operator** = the person who runs the studio's deployment for the client.

## Verified facts (V = read or run in revision 1 on main `0dabf1f` / P1b `0d843b4`; raw output `handover/evidence/P1d/author-probes-2026-11-07.txt`; not re-run for revisions 2 or 3)
- V1: `clean` gives the same output on main, on P1b and on `core/ci-lint-set` for every row below: the hole is on main.
- V2: `gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `_RENDERED_MARKUP` exist (`gate.py:197-226`) and nothing calls them (only `vulture_whitelist.py` on `core/ci-lint-set`); unfinished fix of review R9-O1. `gate.py:151` builds `MarkdownIt("commonmark")` as `_MD`.
- V3: `gate._rendered`'s docstring says `AKIA&amp;...` "shows a key joined"; a renderer shows `AKIA&IOSF...` (an inserted `&`). The docstring is wrong (BN-P1d-2); the inserted character is row H33.
- V4: `redact.strip_ansi` puts a SPACE where an escape sequence stood between two letters, on purpose; a terminal shows the two parts JOINED.
- V5: the redactor's own views (`runmap._views`, `runmap.py:~380-420`; P1b adds `composed`) do not delete markers, escapes or control characters and do not fold case or look-alikes for PATTERN matching; the known-value sweep (`redact.py:~1204 _sweep`) is literal and case-sensitive. The same split key reaches the model through documents, tool results, tool errors and logs (sibling report S1-S5, measured).
- V6: `textnorm.scan_holds(text, value)` holds `AKIAIOSFODNN7EXAMPLE` in `key AKIA**IOSFODNN7EXAMPLE** x` and in the lower-case copy; raises `ViewTooShort` for a very short scannable value (`10.0.0.1`); `textnorm.fold` turns Cyrillic look-alikes and a combining accent back into `AKIA...` but keeps `**`.
- V7: `register_value` (strict by default) raises `CoverageRefused` for Latin and digit values. P1d never calls `register_value`.
- V8: a first prototype ran the whole redactor BEFORE the gate and broke two fuzz tests; only the defang step moves (below).
- V9 (prototype cost, one 4-CPU container, thread CPU time, other agents' suites on the same machine): 3,000 chars 0.21 s (today 0.03 s); 30,000 chars 2.69 s (0.24 s); 120,000 chars 12.9 s (0.98 s). A loop with values outside the views took 190 s at 30,000 chars: loop order matters (views outer, values inner).
- UNVERIFIED: the 5 failing baseline tests, the `scan_holds` minimum, the false-learn rates, the cost at the cap, the existing operator route, every caller table entry below.

## Merge-order preconditions (gates for the build start, BS-0)
1. P1a (PR 63, `core/P1a`) merged; P1b merged (branch `core/P1b-fixwip`, head `0d843b4` when written; its fix batch is running, so P1d builds on the MERGED P1b). **The fail-before base is post-P1b main** (textnorm present), so a fail-before failure is never "module missing". A P1d test file imports `textnorm` only inside test functions.
2. `defaults.py` constants of P1b (`REDACT_BUDGET_S`, `TEXTNORM_*`) exist on the base. BS-0 reads the named minimum scan length from `textnorm` and pins the error classes of `scan_holds` (`ViewTooShort`, `EmptyView`, `TextnormError`) against V6; if they differ, STOP and send the ticket back to review.
3. `vulture_whitelist.py` and `tools/mutation_runner.py` exist on the base (today only on `core/ci-lint-set`). If not, P1d builds `tests/p1d_mutants.py` with a plain subprocess loop and drops the whitelist step, and says so.
4. The 5 baseline failures are listed by test id, with cause, and are fixed in this package or recorded as environment with an owner before "done" (no "known" label).
5. Hard dependency enforcement (ORDER 165 item 5): see NEEDS-LEAD 2 below; until the lead names the gate, the ticket adds one marker constant `runmap.P1D_APPLIED = True` and a test that the client profile refuses to start when it is absent (proposal, least surface).

## RUNG TABLE (R447, R448, R450; scale of 2026-11-06: 1 no-code tools, 2 our own core modules, 3 existing free tools (MCP, RAG, model features), 4 free libraries and open code (tested, licence-checked), 5 our own new code last. Tier C: a core change on a redaction path.)
Gate: core SDK change, no client, no fee, no new dependency. Rung 1 closed (R447: no redaction step inside a no-code flow). Rung 3 closed (a model feature cannot be exact and runs after the text left). **Guarantee class:** **exact** = holds for every value in the set named in the row, up to the stated cap, with a test; **best effort** = holds for the cases tested; **detection-only** = detects and reports. An unknown secret with no pattern (a plain password, no key word) is OUT of the guarantee: not detected, not prevented (said once here and in the CHANGELOG).
**Summary in one line (zoom-out nit 11): reuse (rungs 2 and 4) covers the building of views; our new code is the residue check, the learning pass for fixed-width key shapes, and the wiring.**
| component | need | rung tried | evidence (source, date) | what only our code gives | guarantee class | verdict |
|---|---|---|---|---|---|---|
| deleting and decoding views | read the text as a renderer, terminal or person shows it | 2 (`gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `redact._ANSI`, `strip_controls`, `runmap.undo`) | V2, V4 read 2026-11-07 | one private function with a FIXED ORDER of steps | exact up to the cap, for known values and for patterns, in the deleting views | CUT-TO-CONFIG+GLUE |
| Markdown rendering by a library | rendered view | 4: `markdown-it-py` (already imported by `gate.py:72`) | NOT run (UNVERIFIED). CommonMark only; does not read Slack `*bold*` / `~strike~`. BS-5 runs it once; it is adopted only if it adds a row that fails today | nothing | n/a | CUT (decision rule in BS-5) |
| fold and scan (`textnorm.fold`, `scan_holds`, `scan_cache`) | look-alikes, accents, case, separators | 2 (P1b) | V6 (2026-11-07) | no second normaliser (order 146 2(c)) | exact for the P1b-documented coverage; short values see "Short values" | CUT-TO-CONFIG+GLUE |
| learning pass on squeezed / case-folded views | find an UNKNOWN fixed-width key (AKIA/ASIA) with an inserted character or in lower case (H32, H33) | 2 (same pattern, new view) | UNVERIFIED; BS-2 measures false learn first | the AKIA/ASIA shape on two more views | exact for AKIA/ASIA keys; best effort for the rest (off by default, switched on per pattern only when BS-2 shows false-learn 0) | KEEP-CODE (small) |
| the residue rule | decide whether a known value is readable with placeholders put back | 4: detect-secrets, gitleaks, Presidio find secret SHAPES; none compares a text with OUR run map (P1c BS-1 ran gitleaks 8.30.1 on base64 rows, `tickets/P1c.md:16`) | not run for this need (UNVERIFIED); test idea: row KV-case (a known value in another case has no shape for a shape tool) | redaction before a person (R447 guarantee) | exact for known values up to the cap | KEEP-CODE, about 80 lines (estimate) |
| fail closed, bounded cost | never return an unchecked text | 2 (`REDACT_BUDGET_S`, `InputTooLarge`) | V9 | one deterministic cap | exact (the refusal) | KEEP-CODE, about 15 lines |
| defang after redaction | `[.]` must not split an e-mail or host before the redactor | 2 (`gate.sanitise_text`) | V8 | one parameter and one call order | exact | KEEP-CODE, about 15 lines |
| `LookalikeCopy` | one refusal class shared with P2d-2 | 2 (design text) | owner of the name: `handover/designs/lookalike-leak.md` section 5 (frozen draft 11) | 3 lines | n/a | KEEP-CODE |
**80 percent (R448):** the eight needs are: read as rendered; decode; fold; unknown shapes in other views; decide what is readable with placeholders put back; fail closed; mask before our own markup; bound the cost. Rungs 2 and 4 meet needs 1 to 3 and 7 (four of eight = 50 percent); no library works inside the choke point. Under 80 percent; a guarantee path in any case. **Cost (R450 b, estimates):** build 10-14 agent-hours, plus uncapped review rounds; 0 fees, 0 model tokens, 0 new dependency; upkeep about 200 lines.

## Goals and Non-Goals
**Goals.** (G1) No known value is readable in any text `redact_text` returns or any card `clean` returns, for the families in the rows below, up to the cap. (G2) One implementation at the one choke point; `clean`, `SlackChannel._blocks`, documents, tool results, tool errors, logs and `redact_value` get it without a new call site. (G3) A text the rule cannot clear is withheld in a stated way (table "Refusal behaviour"). (G4) The false-withhold rate and the H34 over-mask rate are measured separately and have ceilings (BS-3). (G5) E-mail addresses and internal host names are masked in cards (H26, H27).
**Non-Goals.** (N1) An unknown secret with no pattern. (N2) What a person types into a free-text field after the card is posted. (N3) `tools._secret_forms` (handed-out secrets): owned by P2d-2; P1d keeps its helpers PRIVATE and P2d-2 promotes what it needs (G7). (N4) A new web console or endpoint. (N5) Exactness above the cap: above the cap the text is withheld, not checked.

## Alternatives considered (each rejected with a concrete reason)
- **A1 Heal and show** (what `redact_text` does for its `undo` views): show the redacted healed view instead of the original. Rejected as the general rule: a fold or case view changes the characters (a key in lower case would be shown in lower case), the card text would differ from the request the approver approves (approval-binding risk), and the bold markers a person wrote would vanish. Trigger: if BS-3 shows a false-withhold rate above ceiling for deletion-only views, A1 is used for those views only.
- **A2 Offset-mapped masking** (index back to the source for deletion views). Rejected for now: offsets exist only for deletion views; entity, percent and fold views change length, so it needs span tracking inside `textnorm` (not built; P1b frozen). Trigger: a measured false-withhold rate above ceiling in the pilot.
- **A3 Escape the markers in the shown text.** Rejected: no help on Slack `plain_text`; breaks code in cards.
- **A4 Check only in `clean`** (rev 1). Rejected: the model path has the same hole (S1-S5), `_blocks` is a second call site, and a second copy of the rule would drift from P2d-2's.
- **A5 Pre-mask only e-mail and host before the gate** (rev 1). Rejected: covers two kinds from one broken test; the gate's defang changes any dotted run ending in a TLD (`gate._DOMAIN`, `gate.py:112`). Replaced by moving the defang after redaction.
- **A6 A library** (Presidio, detect-secrets, gitleaks, markdown-it-py): see the rung table; none knows the run map.
- **A7 Text slices (windows) for large texts** (rev 2). Rejected after round 2: filler longer than the overlap puts a split key into two slices (design B-1), the prototype cost (V9) is not shown to occur in real traffic, and slices create a new bug class. Replaced by one deterministic cap and withhold above it. Trigger: BS-4 shows real documents above the cap in normal traffic (then back to review).
- **A8 Fixed-point loop for views** (rev 2). Rejected after round 2: step order cannot matter in a fixed point, so mutants M10/M11 were meaningless. Replaced by a fixed ordered pipeline; a loop is added only when a combination row shows a miss.
- **Chosen:** fixed-order deleting views, a narrow learning pass, the residue rule, all inside `redact_text`; withhold by default; raise only for cards.

## Risks and Mitigations
- R1 False withholds. Mitigation: the rule withholds only when a KNOWN value is readable in a deleting view of the dropped form (a normal text has none); ceilings in BS-1 and BS-3; guard rows F01-F17 (F14 and F16 are ow rows, counted separately).
- R2 Cost on large texts. Mitigation: ONE deterministic cap (`P1D_MAX_TEXT_CHARS`) and a view cap (`P1D_MAX_VIEWS`); above either the text is withheld (fail closed); the wall clock is only a safety net with the SAME outcome; tests count views and characters, never seconds.
- R3 The learning pass over-learns. The AKIA/ASIA shape in the squeezed or case-folded view matches ordinary prose (the word "Asia" followed by 16 letters or digits once spaces are squeezed away, e.g. `Southeast Asia and Oceania` becomes `southeastasiaandoceania`). Mitigation (written now, from this analysis): on the squeezed and case-folded views a match counts ONLY when its 16 trailing characters contain at least one digit; an all-letter key is still found on the views that keep case (deleting views). BS-2 measures the rest. Any other pattern is excluded from squeezed and case-folded learning unless BS-2 shows false-learn 0 on the corpus. A false learn is a false withhold (the learned value is by construction unmasked in the shown text), so the BS-2 rate and the BS-1/BS-3 rates are one quantity.
- R4 A model-path run ends or a document silently disappears. Mitigation: the notice is visible to the model and the operator log; no exception on the model path; a run is never ended by a withhold.
- R5 Guard-test change. Mitigation: the learning pass is a private function (`_learn_unknown`), not a call of the public `redact_text`, so the hook lint of `test_k5_round11.py` needs no exemption (BN-P1d-3).
- R6 P1b changes under P1d. Mitigation: BS-0 pins the P1b head and the `scan_holds` error classes; P1d calls nothing private of `textnorm`.
- R7 Over-masking from the `&` fix (H34). Mitigation: measured (BS-3, "over-mask rate"), accepted by the lead (ORDER 166 item 2).
- R8 Hostile text forces a withhold (a free denial-of-service lever: `AKIA**...` in a document blanks it or makes a request unapprovable). Fail-safe for approvals, but real. Mitigation: the operator log line carries the `source` and a counter per source per minute from config (`P1D_WITHHOLD_ALERT_PER_MIN`); the operator sees a flood; accepted otherwise.
- R9 `redact_value` (stored records and audit; callers `agent_loop.py:~489`, `evidence.py:~191`) stores the notice in place of a text leaf. If an approval-binding hash reads that stored text, the bound content changes. Mitigation: BS-0 lists every reader of a redacted stored value; if any hash reads one, `redact_value` uses `on_residue="raise"` and that caller handles it (decision recorded in the BS-0 report).

## Sinks (who reads the text, and which views apply)
| sink | how rendered | what a reader can re-join | views applied |
|---|---|---|---|
| Slack card (`SlackChannel._blocks`, `plain_text`) | markers literal | a person copies `AKIA**IOSF...**` by hand; an entity shows `&amp;`; a colour code shows as junk | all deleting views (the person re-joins) |
| Markdown viewer / `notify` top-level text | CommonMark or mrkdwn may join the pieces | the viewer shows the key whole | all |
| `FakeChannel` / log | verbatim | same as a person | all |
| model (documents, tool results, tool errors, `safe_head`, `redact_value`) | tokenised verbatim | a model re-joins and may echo | all |
The rule is the same for every sink (the weakest reader decides). Slack `plain_text` still refuses because a person re-joins the characters.

## Refusal behaviour: every caller of `clean` and `redact_text` (BS-0 completes this table from a grep; a test fails if a `clean` caller is not in it)
A request whose inputs cannot be shown is **not approvable from its card**. It carries no buttons, and the approve path refuses it (see "Operator route"). One literal text per constant:
- `WITHHELD_NOTICE` (model-bound and stored text) = `(withheld: this text may hold a secret written with hidden formatting)`
- Card text (posted once) = `Request <approval_id> cannot be shown safely. It may hold a password, key or e-mail address written with formatting inside it. It cannot be approved from this card.`
- Operator log line (WARNING, logger `hadavin_sdk.guard.runmap`) = `redaction withheld a text: reason=%s source=%s approval_id=%s chars=%d views=%d known=%d`, `reason` in `residue|size|views|clock`; never any content.
| caller | on `LookalikeCopy` / withhold | buttons | pinning test |
|---|---|---|---|
| `SlackChannel._blocks` / `update` / `send` (`slack_channel.py:81,197`) | posts the card text once, no buttons (`approver_ids is None` branch); `sent_at` set so `resend_unsent` finds nothing | no | `test_h30` |
| `requests.summary` (`requests.py:39,47`) | the plan inputs are replaced by `Inputs: not shown. They may hold a password or key written with formatting inside it.`; the request is marked `display_withheld` IN MEMORY by the same call (BS-0 decides how without a schema change: the summary returns a result object or the approve path re-runs the check) and is **not approvable**; the card shows no buttons | no | `test_h40`, `test_no_approve_buttons_when_inputs_withheld` (negative test) |
| `cards.py:59` | same as `_blocks` | no | `test_caller_cards` |
| `channel.py:104` `notify` (top-level text) | the notice text replaces the message; one log line | n/a | `test_caller_notify` |
| `channel.py:111` `post_card` | same as `_blocks` | no | `test_caller_post_card` |
| `FakeChannel` | records one send of the card text | no | `test_h40` |
| `agent_loop._deliver` (`agent_loop.py:~560-567`) | swallows channel exceptions today; with the rows above nothing raises there; a test pins it | n/a | `test_deliver_never_sees_lookalikecopy` |
| model path: `redact_untrusted`, `prepare_output`, `error_reason`, `safe_head`, `redact_value` | returns `WITHHELD_NOTICE`, logs; **never raises** (ORDER 166 item 1) | n/a | rows S1-S5 |
BS-0 adds any further caller it finds; a caller that cannot be matched to a row blocks the build.

## Operator route (ORDER 166 item 3: existing route, least new surface)
Today, per the sibling report and revision 1, the repository is not known to hold an operator console (UNVERIFIED; BS-0 greps the approvals package for the existing decision path, e.g. the receiver's decision handler and `requests`' decide function, and names it in the BS-0 report). **Decision for this package:** no new endpoint, no new read of raw stored text. A request whose card was withheld stays in the store like any other pending request. It can leave the pending state through the EXISTING deny path (and by expiry), both of which need no view of the content. The existing approve path **refuses** such a request: it re-runs the same `redact_text(..., on_residue="raise")` check on the stored summary and refuses on `LookalikeCopy` (no new stored field, no schema change; BS-0 confirms the approve path has access to the summary). The operator reads only the request id and reason from the log line and may deny it; if the content must be reviewed by a person, that is a separate ticket with its own read policy and negative test (BN-P1d-9). This is the smallest surface because the approver never gets a new way to read unmasked text.

## Template fields
- **Package id and name:** P1d, "split secrets at the choke point". One pull request on branch `core/P1d`, from main after P1a and P1b merge.
- **Path class:** redaction AND security. **Extended review (no round cap): yes**, plan and result.
- **Depends on (merged first):** the preconditions above. Not dependent on P1c; P1c edits `redact.py` HOSTNAME (row H27 is asserted so that it holds with or without P1c).
- **Class (R337, R7):** "a value is matched only in the spelling as written, while a reader or renderer reads another spelling". Standards: CommonMark 0.31 sections 6.2, 6.1, 2.5; ECMA-48 sections 5.4, 8.3; Unicode UAX #15 and UTS #39 (cited from memory; read date UNVERIFIED).
- **Source of the code:** our own code only; no library code is copied.
- **Neutral default / working alternative:** the redactor has no vendor; the neutral default is the built-in rule. The alternative path (A1 heal-and-show) is written with its trigger above. `on_residue` selects withhold (default) or raise.
- **Target modules and files (create / change / delete, each with the reason):**
  - change `src/hadavin_sdk/guard/runmap.py`: the rule (`redact_text`, `LookalikeCopy`, `WITHHELD_NOTICE`, private `_healing_views`, `_learn_unknown`, `_finish`); `P1D_APPLIED` marker.
  - create `src/hadavin_sdk/guard/_views.py` ONLY if BS-0's import graph shows that `runmap` importing `gate` privates would invert the layering or create a cycle; then it owns the moved view functions and regexes (`_ANSI_AS_TEXT`, `_rendered`, `_views`) and both `runmap` and `gate` import it. Otherwise the code stays where it is. (Decision at BS-0, recorded; M5/M6 equivalence follows from it.)
  - change `approvals/channel.py`: `clean` calls `redact_text(..., on_residue="raise")` and defangs after redaction; delete the pre-mask.
  - change `approvals/slack_channel.py`: `_blocks` handles the withheld card.
  - change `approvals/requests.py`: the fallback line and the not-approvable state; the approve path check.
  - change `approvals/gate.py`: `sanitise_text(defang=)`, `defang_text`; correct the `_rendered` docstring (BN-P1d-2).
  - change `guard/redact.py`: SECRET value stop-set gains `&` (H34); unanchored AKIA/ASIA learning shape lives in `runmap` (the redactor's own patterns stay unchanged).
  - change `defaults.py`: `P1D_MAX_VIEWS`, `P1D_MAX_TEXT_CHARS`, `P1D_MIN_KEY_CHARS`, `P1D_WITHHOLD_ALERT_PER_MIN` (values from BS-4; no literal threshold in code).
  - create `tests/test_p1d_rows.py` (parametrised per family), `tests/test_p1d_callers.py`, `tests/fixtures/p1d_cases.py` (all literal inputs), `tests/p1d_mutants.py`.
  - change `vulture_whitelist.py` (remove the `gate._rendered` entry when the file exists on the base), `CHANGELOG`.
  - create evidence files under `handover/evidence/P1d/`.
  - NOT in P1d: `k1b/redaction.py`, `approvals/receiver.py` (P1d-b, below).
- **Interface (every new name; no existing public function loses an argument):**
  - public: `runmap.LookalikeCopy(RedactionError)` (message = the class name only); `runmap.WITHHELD_NOTICE: str`; `runmap.redact_text(text, mapping, neutralise=None, *, on_residue: Literal["withhold","raise"] = "withhold", source: str = "", approval_id: str = "") -> str` (`source` and `approval_id` are used only in the log line); `gate.sanitise_text(text, *, defang: bool = True)`; `gate.defang_text(text)`; the `P1D_*` constants in `defaults`.
  - PRIVATE (underscore, no `__all__`, no test of a public API; P2d-2 promotes what it needs in its own ticket, BN-P1d-5): `runmap._healing_views(text) -> tuple[str, ...]` (the fixed pipeline below); `runmap._learn_unknown(views: tuple[str, ...], known: Mapping[str, str]) -> dict[str, str]` (placeholder key to original; entries from the seed set are tracked in a separate set `seeds`, never mixed into this dict); `runmap._finish(source, shown, mapping, known, *, deadline) -> None` (raises `LookalikeCopy`).
  - the existing `except (InputTooLarge, TooDeep)` in `redact_text` also names `LookalikeCopy`, so it is not re-wrapped.
- **Behaviour, exactly:**
  1. `redact_text` removes NUL. **Size gate:** if `len(text) > P1D_MAX_TEXT_CHARS`: default mode returns `WITHHELD_NOTICE` with `reason=size`; `raise` mode raises `InputTooLarge`. The cap is deterministic; below the cap everything is checked over the WHOLE text (no slices).
  2. **Views (fixed order, applied once each; no loop):** (a) DECODE: `runmap.undo` (entities, percent-codes, backslash and JSON escapes); (b) DELETE: markers (`* _ ~ \`` runs), tags and comments, ANSI/CSI/OSC/C1 sequences and a lone ESC, control characters including CR, BS, NUL and invisibles, line breaks; (c) FOLD: `textnorm.fold`; (d) DELETE again (a full-width marker reaches a plain marker only after fold). Each step's output joins the view set (the plain text is view 0). More than `P1D_MAX_VIEWS` views, or a clock past `deadline = clock() + REDACT_BUDGET_S` (taken once at the top, the safety net), withholds with `reason=views|clock`. Views outer, values inner, inside `textnorm.scan_cache()` (V9). A fixed-point loop is added only if a combination row (C01-C08) shows a miss.
  3. **Learning pass:** the patterns run on the deleting views (output discarded; found originals are known values). On the SQUEEZED and CASE-FOLDED views only the AKIA/ASIA shape runs (case-insensitive; unanchored, for H35; a match counts only when its 16 trailing characters contain at least one digit, R3). Other patterns join squeezed/case-folded learning only if BS-2 shows false-learn 0.
  4. **Residue rule on `shown`:** for each known value: `scan_holds` over the deleting views of the dropped form (squeezed and case-folded views are NOT used here). Then the put-back count test (below). A value `scan_holds` cannot scan follows "Short values". Any other `textnorm.TextnormError` withholds with `reason=residue`.
  5. **Put-back count test (quoted from `designs/lookalike-leak.md` section 5 item 3, frozen draft 11, which owns the formula):** for each checked text `t` and, when different, `undo(t)`, replace every genuine placeholder (a token matching `redact._PLACEHOLDER` whose entry is in the map and is not a seed entry) by `" " + original + " "`, in ONE pass (a token-shaped text inside a put-back original is not put back again), keeping a tally of how many placeholders of each original were put back. For each known value, `c` = the count of its scan key (the `isalnum` characters, case-folded) in the key of that form; `e` = the count the tally explains (copies inside the put-back originals). `c > e` withholds. The builder copies this section's algorithm and the rows LK-JAMO-PB and LK-UNFOLD into the fixtures file, character for character; if the frozen note changes, the ticket is returned to review.
  6. **Pattern fix in `redact.py`:** the SECRET assignment value extends over `&`; its stop-set stays white space, a quote and `;` (`,`, `)`, `>` do not end it; only `&` is added to the value characters.
  7. **`clean`:** NUL removal, ONE `redact_text(text, seeded, neutralise=_neutralise, on_residue="raise", source="card", approval_id=...)`, where `_neutralise` is `gate.sanitise_text(..., defang=False)` plus `withhold_commands`; then the joined pass (`_TAGS.sub`) with the same call; then `defang_text` on the result. The pre-mask of revision 1 is deleted. Fallback if BS-4 finds a kind the moved defang still breaks: a documented per-kind pre-mask for exactly that kind (BN-P1d-8).
  8. **`_blocks`, `requests.summary`, the other callers:** as in the table "Refusal behaviour".
- **Existing core code reused (checked as in the rung table):** `gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `redact.strip_ansi`/`_ANSI`, `strip_controls`, `runmap.undo`, `textnorm.fold/scan_holds/scan_cache`, `REDACT_BUDGET_S`, `InputTooLarge`, `TooDeep`. Checked and not reused: `textnorm.register_value`, `tools._secret_forms`.
- **Security and least-privilege notes:** no identity, right, secret or config beyond four constants. No new read of raw stored text (see "Operator route"). The learning pass holds found originals in memory for the call only; the operator line carries counts, never content (test greps the log for the key). Test values are built from parts; the only whole-key literal is the AWS documentation example key.
- **Rollback:** tag `pre-P1d` before the pull request. **Non-revertible semantic changes, marked in the CHANGELOG:** stored records and model text may now contain `WITHHELD_NOTICE`; `clean` raises `LookalikeCopy`; the SECRET value is masked over `&`; e-mail and host are masked in cards (the defang moves after redaction). Loud-failure test: `test_withheld_notice_is_loud` (a withheld text is never returned as if clear: the output equals the notice, a log line exists, and no key is in either).
- **Reviewers:** correctness (`egm-codebase-details`) + adversarial (`egm-design`, `egm-implementation-readiness`), fresh agents that get the diff, this ticket and the evidence only; redaction path, no round cap.
- **Done =** the plan's stop rule (a fresh round finds no blocker or major) and all gates green: tests (3.12 and 3.13), ruff check, ruff format --check, bandit -ll, guard tests, CodeQL, SonarCloud, CodeRabbit; ledger rows 001-004 and 007-008 FIXED-VERIFIED; the lead merges.

## Short values (ORDER 166 item 5)
`textnorm.scan_holds` raises `ViewTooShort` for a value below its minimum scan length `TN_MIN` (a named constant of `textnorm`, read at BS-0, never copied). For such a known value found at run time: (1) exact substring search in EVERY deleting view (not the squeezed view), with a word-boundary rule (the match may not sit inside a longer run of letters/digits); (2) a floor `P1D_MIN_KEY_CHARS` (proposed 8, set at BS-4): below the floor the value is OUTSIDE the guarantee (class: best effort, said in the CHANGELOG). (3) **Recording:** every call that used the exact fallback writes one INFO line `redaction coverage=exact_only values=%d` (no content). (4) **Strict mode unchanged:** `P1D` never calls `register_value`; the client-profile strict mode (`TEXTNORM_STRICT_COVERAGE`) still makes `register_value` raise `CoverageRefused` for the same value; guard row `test_strict_mode_still_refuses` pins that the fallback does not lift it. The exact fallback is a run-time check on found values, not a registration.

## Scope of S11 and S16 (ORDER 166 item 4)
Neither sits on the `redact_text` path: S11 (`k1b/redaction.py` `sensitive()`) decides whether a key NAME is a credential and never calls the redactor; S16 (`receiver.log_message`) calls no redaction at all (the fix is to add a call). They are therefore **P1d-b**, their own package, with ledger rows now (BL-core-p1d-006 and -009 below), written as a ticket directly after the P1d plan review is clean, and built right after P1d (S11 needs the views, which P1d keeps private; P1d-b's ticket promotes what it needs). Not deferred without an owner: P1d-b is on the build queue behind P1d.

## Failing inputs (fixtures in `tests/fixtures/p1d_cases.py`; tests are parametrised per family in `tests/test_p1d_rows.py` with the row id as the parameter id, so a killer is named by row)
**Literal constants (all built from parts):** K = `AKIAIOSFODNN7EXAMPLE` (`"AKIA" + "IOSFODNN7EXAMPLE"`; the allowed literal); K4 = `AKIA`; K16 = `IOSFODNN7EXAMPLE`. S = `"Tq7mZ" + "4xKp2Vb9Lr3NcW8dYh6uJs"` (27 chars, mixed case; S5 = `Tq7mZ`, S22 = `4xKp2Vb9Lr3NcW8dYh6uJs`). E = `"anna" + "." + "m" + "@" + "example" + "." + "org"`. PW(n) = the first n characters of `Qm8vRt2xLp5nZc7bKd3wHj` (mixed case, so its lower-case copy differs). KV = a known value: the text first holds `password=<S>` (so S is in the map), then the second copy named in the row.
**Groups.** Every fb row fails on post-P1b main by an assertion that the key or value is shown. pb rows pass on the base and after. ow rows are accepted over-withholds, excluded from the BS-1/BS-3 ceilings by name and reported separately.
| row | group | input | on base | expected after P1d |
|---|---|---|---|---|
| H01 | fb | `key AKIA**IOSFODNN7EXAMPLE** here` | key shown | withheld (the squeezed view also finds it; killers for deleting steps use KV rows) |
| H02-H06 | fb | `AKIA**IOSFODNN**7EXAMPLE`; `AKIAIO*SFODNN7EXAMPLE*`; `AKIA~~IOSFODNN7EXAMPLE~~`; ``AKIA`IOSFODNN7EXAMPLE` ``; `AKIA_*IOSFODNN7EXAMPLE*_` | shown | withheld |
| H07 | pb | `AKIA<b></b>IOSFODNN7EXAMPLE`; `AKIA<!-- -->IOSFODNN7EXAMPLE` | masked | masked, same output |
| H08 | pb | `AKIA&ZeroWidthSpace;IOSFODNN7EXAMPLE`; `&shy;`; `&NoBreak;`; `&InvisibleTimes;`; `&#8203;`; `&#x200B` (no `;`); `&amp;#8203;` | masked | masked, same |
| H09 | pb | `AKIA&#73;OSFODNN7EXAMPLE`; hex `&#x49;`; `&#73` (no `;`) | masked | masked, same |
| H10 | fb | KV, second copy `<S5>&amp;<S22>` | shown | withheld |
| H11 | fb | `AKIA\x1b[0mIOSFODNN7EXAMPLE` | shown as `AKIA IOSF...` | withheld |
| H12 | fb | four parametrised variants: `\x1b[38;5;196m` inside the key; C1 `\x9b0m`; OSC `\x1b]0;t\x07`; OSC 8 `\x1b]8;;http://x\x07` | shown | withheld (each its own case) |
| H13 | fb | `AKIA\\x1b[0mIOSFODNN7EXAMPLE` (escape written as text) | shown | withheld (over-refusal accepted: a person reading the literal joins it) |
| H14 | fb | `AKIA\x1bIOSFODNN7EXAMPLE` (lone ESC) | 19 of 20 chars shown | withheld |
| H15 | fb | `x\x08AKIAIOSFODNN7EXAMPLE`; `AKIA\x08IOSFODNN7EXAMPLE` | shown | withheld |
| H16 | fb | `AKIA\rIOSFODNN7EXAMPLE` | shown on two lines | withheld |
| H17 | pb | BEL, DEL, NEL `\x85`, VT, FF, NUL, ZWSP, ZWJ, WJ, U+202E, soft hyphen, each once between `AKIA` and `IOSFODNN7EXAMPLE` | masked | masked, same |
| H18 | fb | `AKIA` + U+0301 + `IOSFODNN7EXAMPLE`; U+0323 variant | shown | withheld |
| H19 | pb | the key in full-width forms | masked | masked |
| H20 | fb | KV, second copy `<S5>` + U+FF0A (full-width `*`) + `<S22>` | shown | withheld (needs step d) |
| H21 | fb | Cyrillic `А` (U+0410) for both `A` of `AKIA` | shown | withheld |
| H22 | fb | KV, second copy `<S5>**<S22>**` | shown | withheld |
| H23 | fb | KV, second copy S in lower case | shown | withheld |
| H24 | fb | KV, second copy `<S5>\n<S22>` | shown | withheld |
| H25 | fb | `password=<S5>\x1b[1m<S22>` | `<SECRET_1> ` + tail | withheld |
| H26 | fb | `contact <E> please` | `anna.m@example[.]org` | `contact <EMAIL_1> please` |
| H27 | fb | `host db01.corp.example.com down` | defanged text | the span `db01.corp` is ABSENT from the output (true whether or not P1c merged; the leftover `.example.com` may be defanged or not: not asserted) |
| H28 | fb | `anna.m**@example.org**`; `anna.m@exam\x1b[0mple.org` | shown | withheld (the squeezed view drops `@` and `.`, so only the deleting views decide) |
| H29 | fb | a NEW input: `passwor<span></span>d%3D<v1>%0D<v2>` with v1 = `Zx4cV7bN1mQa`, v2 = `Wl9sD3fG6hJk` (12 chars each) | tail shown (fail-before to be confirmed by BS-0; if it passes on the base, the row is moved to pb and M7 gets another killer) | masked tail |
| H30 | fb | H01's input as `req.summary` through `SlackChannel._blocks`; and `requests.summary` of a plan whose input holds the key split by `**` | shown | the card text, no buttons, no key, no retry |
| H31 | fb | `AKIAIOSFODN\nN7EXAMPLE` (not in the map) | shown | withheld |
| H32 | fb | `akiaiosfodnn7example` (lower case, not in the map; has the digit 7) | shown | withheld (case-folded learning) |
| H33 | fb | `AKIA&amp;IOSFODNN7EXAMPLE`; `AKIA.IOSFODNN7EXAMPLE`; `AKIA\*IOSFODNN7EXAMPLE` | shown | withheld (only the squeezed learning reaches the inserted character) |
| H34 | ow | `password=ab12&cd34ef56gh78ij` | `<SECRET_1>&cd34ef56gh78ij` | whole run masked; also `password=<S5>&amp;<S22>` masked |
| H35 | fb | `keyzAKIAIOSFODNN7EXAMPLE` | shown | withheld (unanchored shape) |
| H36 | fb | `anna%2Em@example.org`; `anna&#46;m&#64;example.org` | shown | withheld or masked (encoded e-mail, readiness nit 3) |
| H40 | fb | H01 as a plan input through `requests.summary` then `FakeChannel.send` | key shown | the fallback line, no key, no buttons; one send, no retry |
**Combination rows (fixed order proof):** C01 `AKIA**` + Cyrillic `О` + `SFODNN7EXAMPLE**`; C02 `AKIA**IO` + U+0301 + `SFODNN7EXAMPLE`; C03 `AKIA&ast;&ast;IOSFODNN7EXAMPLE`; C04 `AKIA&amp;ast;IOSFODNN7EXAMPLE`; C05 `AKIA\x1b[0m**IOSFODNN7EXAMPLE` (ANSI + marker; the label of rev 2 said entity + ANSI, which this input is not); C05b `AKIA&#27;[0mIOSFODNN7EXAMPLE` (entity + ANSI); C06 `AKIA\x1b[0m\nIOSFODNN7EXAMPLE`; C07 `akia**iosfodnn7example`; C08 `AKIA%2A%2AIOSFODNN7EXAMPLE`. Each KV-form twin (second copy of S written the same way) is a parametrised case too. Expected: withheld.
**Boundary rows (short values), with `TN_MIN` read at BS-0:** for n in {`TN_MIN-1`, `TN_MIN`, `TN_MIN+1`} and each variant {plain upper, lower, `**` inside, escape inside}: KV with PW(n). Expected: n >= `P1D_MIN_KEY_CHARS` withheld in every variant; n below the floor documented as outside the guarantee (the test pins that no crash and one `coverage=exact_only` line occur).
**Size rows:** X01 text of `P1D_MAX_TEXT_CHARS` with a split key at 100 characters before the end: withheld by the rule (checked); X02 cap+1 characters: `WITHHELD_NOTICE` with `reason=size` in default mode and `InputTooLarge` in raise mode; X03 a text whose view count passes `P1D_MAX_VIEWS` (nested encodings): `reason=views`, same two outcomes; X04 a clock stub that jumps past the deadline after the first view: `reason=clock`, same outcomes. Tests count characters and views, never seconds.
**Guard (pb) rows, output unchanged against base:** F01 ``Approve **restart** of `web-01` in ~~old~~ demo?``; F02 placeholders already in the text (seeds not put back); F03 a 40-hex commit id and a 64-hex digest in code spans; F04 a Markdown table with bold and code; F05 `Tom &amp; Jerry &lt;ok&gt; &#169; 2026`; F06 `\x1b[32mok\x1b[0m done`; F07 `10.0.0.1` twice (ViewTooShort path: exact search, not a withhold; coverage line recorded); F08 ``run `make`test``; F09 `password=<S>` masked as today; F10 `José Müller`; F11 a 3,000-character card (deadline not reached; the test asserts views and characters); F12 an ARN with its 12-digit account id inside a longer stored value; F13 Greek and Cyrillic prose words; F15 `https://x.example/?a=1&b=2`; F17 2,000 characters of prose with `**`, `*`, `~~`; F18 `k1b.redaction.sensitive` with the keys `bypass_cache` and `pass_through` (no new "sensitive"; readiness nit 6); F19 `test_strict_mode_still_refuses`. **ow rows:** F14 (``` `<25 letters and digits>`/`<26 letters and digits>` ``: deleting the backticks joins two identifiers into a 52-character run the high-entropy pattern masks; withheld, counted separately) and F16 (`password=hunter22&user=bob`, H34's over-mask).
**Sibling rows (model path):** S1-S5: H01's input through `redact_untrusted`, `prepare_output`, `error_reason`, `safe_head`, `redact_value`: each returns the notice or masked text, never the key, never raises. S6/S13 (P2d-2) are not in this package.
**Fail-before proof:** the new test files run on post-P1b main in a temporary worktree first (`git worktree add <tmp> <base>`; copy only the new test files and `tests/fixtures`): every fb row must FAIL by assertion (never by an import error); every pb row must PASS; ow rows are listed with their base result. No strict-xfail rows. Raw output to `handover/evidence/P1d/fail-before.txt`, head SHA on line 1.

## Build steps before any code (BS) — each has a stated output, and a rule that sends the ticket back to review
- **BS-0** list the 5 failing baseline tests (id, cause); pin the P1b head, `TN_MIN` and the `scan_holds` error classes (stop if different from V6); draw the import graph (`_views.py` or not); build the caller table by grep and complete "Refusal behaviour"; name the existing operator decision path and the approve path's access to the summary; list every reader of a `redact_value` result for a hash (R9); settle whether `gate._views` supplies the control step (M6).
- **BS-1** model-path false-withhold: a made-up corpus of 500 documents, tool results, logs (prose, JSON, stack traces, UUID-heavy logs, snake_case names, base64, code), fixed seed in `tools/p1d_corpus.py`, run through `redact_text`. Ceiling 0 withholds; report the rate as "0 of 500 supports a rate below about 0.6 percent at 95 percent (rule of three)", not as zero. Any withhold is listed and fixed or justified by a real hidden value.
- **BS-2** learning-pass false-learn per pattern on the same corpus plus hex digests, UUIDs, base64 blobs, 2,000 lines of code, and prose with the words "Asia" and "akia" in it. Any pattern with a learn on ordinary text is excluded from squeezed/case-folded learning. **Back to review** if AKIA/ASIA itself learns on ordinary text after the digit rule.
- **BS-3** card path: the guard rows and a corpus of 500 made-up cards; ceiling 0 withholds on non-secret cards. Report SEPARATELY: the false-withhold rate (guard rows, ow rows excluded and listed), the false-abstain rate, and the H34 over-mask rate (a query-string corpus of 200 made-up URLs and assignments; share of outputs where more than the secret value is masked).
- **BS-4** cost: `_healing_views` and `_finish` at 3,000, 30,000 and 120,000 characters; choose `P1D_MAX_TEXT_CHARS` as the largest size at which the 95th percentile of the BS-1 corpus plus the largest real-shaped document stays under `REDACT_BUDGET_S / 4` on the build machine, `P1D_MAX_VIEWS` as the smallest count that passes all C rows with 2x headroom, and `P1D_MIN_KEY_CHARS` from the BS-1 short-value false-withhold counts. Also the defang move on every pattern kind (31 kinds: a made-up sample of each through the redactor on raw text and on gated text, listing every kind where the output differs). **Back to review** if normal traffic holds documents above the cap, or if the cost at the cap exceeds the budget.
- **BS-5** the one-off `markdown-it-py` comparison on H01-H06, C01-C08. Rule: it is adopted only if it produces a view that makes a row fail today pass; otherwise it stays CUT.
Return-to-review also applies if BS-1 shows a refusal above ceiling that cannot be fixed by dropping a pattern, or if the textnorm error classes differ from V6.

## Mutation plan (`tests/p1d_mutants.py`; one mutant per mechanism; each with its killer row and the row where ONLY that step decides. A mutant that survives every row is declared equivalent with a written reason and the code it protects is deleted, or a combination row is added that kills it)
| mutant | planted change | killer (literal row; "only-this-step" row) |
|---|---|---|
| M1 | `_finish` call removed from `redact_text` | H01; only-this-step: H22 |
| M2 | `_blocks` posts the text unchecked | H30 |
| M3 | decode step (a) removed | H10, C03, C08; only-this-step: H10 (KV, squeezed unused) |
| M4 | marker deletion removed | H22, H28 (squeezed drops `@`, `.`) |
| M5 | ANSI deletion removed | H25, H11 on KV twin; H28 second input |
| M6 | control-character / line-break deletion removed | H24 (KV, newline), H15 on KV twin. Equivalent if `gate._views` supplies it AND BS-0 shows the mutant planted in `runmap` only is covered by the shared code; then declared equivalent with that reason |
| M7 | tag deletion removed | H29 |
| M8 | fold step (c) removed | H21 (Cyrillic KV twin), H18 |
| M9 | second DELETE (d) removed | H20 (KV full-width marker), C01 |
| M10 | step order changed (fold before decode) | C04, C02. If it survives, add a combination row that reaches it or declare equivalent |
| M11 | squeezed learning removed | H33 (inserted `.`/`&`) |
| M12 | case-folded learning removed | H32 |
| M13 | digit rule removed (all-letter match learned) | BS-2 row `asia-prose` (a prose text with the word Asia) must not withhold |
| M14 | dropped-form test removed | the builder names a row that only it decides; if none exists after the run, the dropped-form test is deleted (round-2 zoom-out finding 5) |
| M15 | put-back without the two spaces | LK-JAMO-PB (a) Korean and (b) Tamil copied into fixtures (literals: Korean V = 11 syllables `U+AC00` upwards, e.g. `chr(0xAC00+i*21*28)` for i in 0..10, then U+B85C; Tamil V = `"Tamilv"` + U+0B92; the builder copies the exact inputs from the frozen note) |
| M16 | `c > e` becomes `c >= e` | F09 |
| M17 | `TextnormError` swallowed as "no hit" | `test_textnorm_error_withholds`: a map value `"&#65018;" * 14600` (LK-UNFOLD: `undo` raises `InputTooLarge`) with a text that does not contain it |
| M18 | `ViewTooShort` fallback removed (value skipped) | boundary row at `TN_MIN-1`, KV with a marker |
| M19 | `ViewTooShort` fallback uses the squeezed view | F13 and a short-value false-withhold row (`10.0.0.1` inside `210.0.0.12` is NOT found: word-boundary rule) |
| M20 | seed entries put back | F02 |
| M21 | defang before redaction again | H26 |
| M22 | `LookalikeCopy` caught inside `clean` and the text returned | H01 asserts `type(exc) is LookalikeCopy` and that `clean` raised |
| M23 | `except` line no longer names `LookalikeCopy` (re-wrapped) | H01 asserts the exception type, not a parent |
| M24 | `on_residue` default flipped to `"raise"` | S1-S5 (model path never raises) |
| M25 | size cap off by one (`>=` for `>`) | X01 and X02 |
| M26 | `_blocks` keeps buttons for a withheld card | `test_no_approve_buttons_when_inputs_withheld` |
| M27 | `&` fix removed from SECRET | H34 |
| M28 | unanchored AKIA/ASIA shape removed | H35 |
| M29 | `requests.summary` fallback swapped (withheld treated as too deep) | H40 |
| M30 | joined pass uses the first map | `test_joined_pass_uses_its_own_map`: a text where only the joined text holds a known value: `password=<S5>` + `\n` + `<S22>` in a fixture where the two halves are joined only by `_TAGS.sub` (`<S5><b></b><S22>` after a seed that makes the first pass see the halves apart); the builder verifies the input fails under the mutant |
Mutation runner: `tools/mutation_runner.py` if on the base, else a subprocess loop in `tests/p1d_mutants.py`; every mutant restored in a `finally`; the tree checked clean at the end. 30 mutants (round-2 zoom-out asked for about 12; readiness asked for the extra mutants listed here: the `except` line, the `on_residue` default, the buttons, the cap edge; the builder may merge mutants whose killers coincide, and the report says which).

## Evidence commands (EVIDENCE RUNNER, a separate agent; raw output to `handover/evidence/P1d/evidence-<n>.md`, head SHA on line 1)
```
uv run --all-extras --group test ruff check
uv run --all-extras --group test ruff format --check
uv run --all-extras --group test pytest -q -rs -m "not live and not perf" tests/test_p1d_rows.py tests/test_p1d_callers.py
uv run --all-extras --group test pytest -q -rs -m "not live and not perf"      # full, Python 3.12 and 3.13
bandit -ll -r src
python tests/p1d_mutants.py                       # alone
python tools/p1d_corpus.py --seed 1 --kind bs1    # BS-1, BS-2, BS-3 corpus runs, fixed seed
python tools/p1d_cost.py                          # BS-4 sizes, alone, no other heavy job
```
Fail-before as in its section. Commands run with no cloud configuration in the environment.

## Build notes (BN-P1d-n)
- BN-P1d-1: cite the base SHA; rebase on whatever main holds after P1b merges and re-run the fail-before proof there too.
- BN-P1d-2: correct `gate._rendered`'s docstring (an entity that decodes to a visible character inserts it; row H33).
- BN-P1d-3: the learning pass is a private function, not a call of the public `redact_text`; the hook lint of `test_k5_round11.py` keeps working unchanged. If not, exempt by (file, function) with an assertion that the result is discarded.
- BN-P1d-4: views outer, values inner (V9).
- BN-P1d-5: P2d-2 promotes `_healing_views` / `_finish` (with an `extra=` argument) in its own ticket; the count rule has one copy, in `runmap`.
- BN-P1d-6: test texts never say "staging", "dev" or "test" as a stage name (R449); F01 says "demo".
- BN-P1d-7: remove the `gate._rendered` entry from `vulture_whitelist.py` in the same pull request (when the file exists on the base).
- BN-P1d-8: the per-kind pre-mask fallback of item 7, only for a kind BS-4 lists.
- BN-P1d-9: a ticket for operator review of withheld content (own read policy, own negative test) is NOT part of P1d; the ledger row BL-core-p1d-010 tracks it.
- BN-P1d-10: BS-0 pins exact line numbers for every `~` number in this ticket.

## Owner-facing wording (CHANGELOG and the card; plain words, checked against rule 14)
- Card line (posted once, no approve buttons): the literal in "Refusal behaviour".
- Model-bound text: the literal `WITHHELD_NOTICE` in "Refusal behaviour".
- CHANGELOG, Upgrade steps: "Text shown to a person or sent to a model: a password, key or e-mail address written with formatting characters inside it (bold or italic markers, a terminal colour code, a backspace, an accent mark, look-alike letters, another letter case, a line break or one extra character such as `&` or `.`) is no longer shown. An approval card for such a request is posted once without buttons and cannot be approved; an operator log line says why. Text sent to a model is replaced by a short notice. Texts longer than a stated limit are also replaced by the notice. E-mail addresses and internal host names in approval cards are now replaced by placeholders (before, they were shown with `[.]` in place of each dot). A password that contains `&` is now hidden up to the next space. Not covered: a secret that no pattern recognises and that is not already known (a plain password with no key word before it), and very short values (below a stated length) that are only matched exactly."
- Sentence for the owner's status message: "We found a gap where a key, password or e-mail address written with formatting characters inside it could be shown on an approval card or sent to the model. The fix is being built. Until it is merged, such values can be shown, so no real client data goes through this software."

## Ledger rows (`handover/ledger.md`; severity by the author, the lead confirms)
| id | package | severity | summary | status |
|---|---|---|---|---|
| BL-core-p1d-001 | P1d | BLOCKER | `clean` and `redact_text` show a key split by markers, escapes, controls, accents, look-alikes (H01-H25) | OPEN |
| BL-core-p1d-002 | P1d | BLOCKER | `clean` never masks e-mail and internal hosts (defang before redaction, H26-H28) | OPEN |
| BL-core-p1d-003 | P1d | MAJOR | `SlackChannel._blocks` second `redact_text` outside the check (H30) | OPEN |
| BL-core-p1d-004 | P1d | BLOCKER | the same split key passes every model producer (S1-S5) | OPEN |
| BL-core-p1d-005 | P2d-2 | MAJOR | handed-out secret echoed in another case or with markers (S6, S13); P2d-2 promotes the views. Lead acceptance of this hand-over: NEEDS-LEAD 3 | OPEN |
| BL-core-p1d-006 | P1d-b | MAJOR | `k1b.redaction.sensitive` misses disguised key names (S11); own package P1d-b, not on the `redact_text` path (ORDER 166 item 4) | OPEN |
| BL-core-p1d-007 | P1d | MAJOR | SECRET value ends at `&` (H34) | OPEN |
| BL-core-p1d-008 | P1d | MAJOR | glued, dotted or `&`-inserted key passes (H33, H35) | OPEN |
| BL-core-p1d-009 | P1d-b | MINOR | `receiver.log_message` logs a callback URL unredacted (S16); own package P1d-b | OPEN |
| BL-core-p1d-010 | P1d-c | MAJOR | no way for an operator to review the content of a withheld request (BN-P1d-9); ticket after P1d | OPEN |
The lead's cilint ledger row `BL-hadavin-sdk-cilint-001` (ORDER 146) is the parent of 001 to 004; the lead confirms the link.

## EGM steps needed, in order (R374, rule 13)
(1) brainstorm: not run, revision 1 is the brief; (2) draft: revision 3 (this file, `egm:egm-draft`, 2026-11-09); (3) plan review round 3: `egm-design` + `egm-implementation-readiness` + `egm-zoom-out`, fresh agents, given this ticket, the sibling report and the round-2 resolve only; (4) `egm:egm-resolve`; repeat (3)-(4) until a round finds no blocker or major (redaction path, no cap); (5) build after P1b merges; (6) EVIDENCE RUNNER; (7) result review by `egm:*` reviewers; (8) resolve, repeat until clean; (9) `egm:egm-drift-report`.

## Slot needs (rule 17)
Build iterations: only the new test files and the clean-related files (about 1-2 minutes). Final head, once: full suite on 3.12 and 3.13 (2 slots), the 30-mutant run (1 slot, alone with at most the other-Python suite), BS timing rows (1 slot, ALONE). Real clock: build 10-14 hours, evidence 1-2 hours, each review round 1-2 hours. P2d-2 and P5c also read `channel.py`: a rebase conflict, no slot conflict. P1d is first in the build queue after the P1b fix batch (ORDER 165) and blocks the P1b/PR 63 pilot merge.

## OPEN QUESTIONS for the lead (only what ORDER 165 and 166 did not answer)
1. P1b must expose the `textnorm` minimum scan length as a named constant and keep the `scan_holds` error classes stable (P1b fix batch is open). If it will not, P1d reads them at BS-0 and stops on a mismatch. (ORDER 166 item 5 accepted the fallback; this is the dependency on P1b.)
2. Which gate enforces "no client data before P1d" (ORDER 165 item 5)? Proposal in precondition 5: a marker constant `runmap.P1D_APPLIED` and a client-profile start refusal when absent.
3. S6 and S13 (a handed-out secret echoed with markers or another case) go to P2d-2 (ledger BL-core-p1d-005). Is that hand-over an accepted exception under fix-dont-defer (needs a third ticket), or does the lead want them in P1d?
4. The approve path of the EXISTING route refuses a withheld request by re-running the check; if BS-0 finds the approve path cannot reach the stored summary without a schema change, is a one-field addition (`display_withheld`) acceptable as the smallest change?
5. Cap instead of text slices: confirm that "exact up to a stated cap, withhold above it" is acceptable (round-2 resolve NEEDS-LEAD 8); the cap value comes from BS-4.

## UNVERIFIED (not read or not run by me in revision 3)
Every V number (revision 1's prototype); the 5 baseline failures' cause; `TN_MIN`; the existing operator decision path and the approve path; the caller table beyond the sibling report; row H29's fail-before; the AKIA digit rule's real effect; the BS-1 to BS-5 results; the standard section numbers; Python 3.13; the demo repositories; whether `vulture_whitelist.py` and `tools/mutation_runner.py` have reached the base; the Korean and Tamil literals of LK-JAMO-PB (copied by the builder from the frozen note).

## Rules cited
R233 (redaction fails closed), R337 (class-level fixes), R363 (no single dependency), R374 (EGM order), R447, R448 (CODE LAST, rung table), R449 (stage names), R450 (research and licence gate); studio preamble rules 3, 5, 6, 7, 12, 13, 14, 17, 19, 20, 21.

## Revision log
Rev 1 (2026-11-07): author draft without the skill. Rev 2 (2026-11-09): `egm:egm-draft` from round-1 reviews and ORDER 165. Rev 3 (2026-11-09): `egm:egm-draft` from round-2 reviews, `round2-resolve.md` G1-G12 and ORDER 166: no text slices (one deterministic cap, withhold above it), fixed-order view pipeline instead of a fixed point, private helpers, model path never raises, refusal-behaviour caller table, existing-route operator decision (deny/expire; approve refused), short values with `coverage=exact_only` and strict mode untouched, AKIA/ASIA digit rule against the "Asia" false learn, S11/S16 moved to P1d-b with ledger rows, literals in a fixtures file, 30 mutants with only-this-step rows, Rollback / Done / files / Reviewers / Neutral-default lines added.
