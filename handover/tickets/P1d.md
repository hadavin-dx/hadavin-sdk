# Package ticket P1d: a secret split by markup (markdown markers, an HTML entity, a terminal escape, a control character, another letter case, an inserted character) is shown unmasked by `approvals.channel.clean` and by `runmap.redact_text`. DRAFT revision 4 (plan review round 4 not yet run)

## The problem in plain words
A person (or a model) is shown a text after secrets and personal data were replaced by placeholders such as `<APIKEY_1>`. The redactor reads the text only as written. If a secret is written with extra characters inside it, for example `AKIA**IOSFODNN7EXAMPLE**` (the asterisks make half of it bold in Markdown), the pattern does not match and the key is shown. The same happens with a terminal colour code, a backspace, an accent mark, look-alike letters, another letter case, a line break or one inserted character: a person re-joins the pieces by eye, a model re-joins them too. Two more holes of the same kind: the approval gate changes every `.` in a domain to `[.]` BEFORE the redactor runs, so a plain e-mail address or internal host name is never masked; and a password that contains `&` shows the part after the `&`.

**Why this ticket is over 250 lines (template rule):** the failing-input tables are the specification (lead order 146 2(a)): about 90 lines of rows, 25 of mutants, 30 of pseudocode and caller table. History is in the revision log at the end; the three reviews and resolutions are in `handover/reviews/P1d/`.
**Status (2026-11-09 UTC; IST = UTC+5:30):** text only, no code, no pull request. Revision 4 applies `reviews/P1d/round3-resolve.md` (groups G1-G22) and the lead's ORDER 165, 166 and 167. **Not done, first:** nothing was run again for revisions 2 to 4; no reviewer and I read source for it (runmap, channel, gate and textnorm are not on branch `core/cloud-handover`), except one read of `textnorm._scan_key` on `origin/core/P1b-fixwip` (below). Items marked V come from revision 1's author probes (`handover/evidence/P1d/author-probes-2026-11-07.txt`, a scratch prototype, NOT the build); items marked UNVERIFIED are measured or read by the build step named beside them (BS-0 to BS-4) before their row counts. Marker: CODE-LAST v1.

## Lead rulings this revision implements
- ORDER 165: the fix is inside `runmap.redact_text`, one choke point, model path included, no P1e; the squeezed and case-folded passes are measured in P1d; a withheld card is a finished state (posted once) with an operator log line and a visible reason; H31-H35 are fixed in P1d; P1d is a HARD DEPENDENCY of any pilot or prod merge of P1b or PR 63 (no client data before it lands).
- ORDER 166: model path withholds by default, logs, never raises; the H34 over-mask is accepted and its rate reported separately; operator route = the EXISTING one, least new surface; S11/S16 are P1d-b; the `ViewTooShort` exact fallback only with `coverage=exact_only` recorded and client-profile strict mode still refusing.
- ORDER 167: P1b exposes the `textnorm` minimum scan length and keeps the `scan_holds` error classes stable (a test pins them); the hard dependency is enforced by the marker `runmap.P1D_APPLIED` plus a client-profile refusal while it is absent (negative test and a mutant); S6 and S13 may go to P2d-2 only as ledger rows with owner P2d-2 and the same hard dependency, and whichever sits on the `redact_text` path is folded into P1d (S13 is, S6 is not: ledger below); `display_withheld` only if the approve path can still reach the summary, proven by a test; one deterministic size cap, withhold above it, no text slices.

## Words used (defined once; one word keeps one meaning)
- **The choke point** = `guard/runmap.py::redact_text`. Every model-bound text, log text, tool result and approval card goes through it.
- **View** = another spelling of the same text. **Deleting views** (used for the residue test and for learning) are the ordered pipeline below. **Learning-only views**: **squeezed** (every character that is not a letter or digit removed) and **case-folded** (lower case of the squeezed view).
- **Known value** = an original the redactor masked in this call (the run map, seeds excluded) or one found by the **learning pass** (the patterns run on the views; the output is thrown away; only the found originals are kept).
- **Dropped form** = the shown text with each genuine placeholder (`<APIKEY_1>`) replaced by one space. **Put-back form** = the same with each placeholder replaced by `" " + original + " "`. Both test "could a person re-join the pieces".
- **Residue rule** = after masking, no known value may be readable in any deleting view of the dropped form, and the put-back count test (below) must pass. If either fails the text is **withheld**.
- **Withheld** = `redact_text` does not return the text. Default (`on_residue="withhold"`): it returns the fixed sentence `WITHHELD_NOTICE` and writes one operator log line. With `on_residue="raise"` (used only by the approval-card callers) it raises `runmap.LookalikeCopy`, for EVERY reason (residue, size, error). The model path never raises.
- **Not approvable** = a request whose card was withheld: it has no buttons and the approve path refuses it. ("Refused" is not used as a state name.)
- **Test row groups:** **fb** = must FAIL on the base commit (fail-before); **pb** = passes on the base and must stay unchanged (guard); **ow** = an accepted over-withhold, counted and reported separately.
- **Operator** = the person who runs the studio's deployment for the client.

## Verified facts (V = revision 1 probes on main `0dabf1f` / P1b `0d843b4`, not re-run; R = read by me on 2026-11-09)
- V1: `clean` gives the same output on main, P1b and `core/ci-lint-set` for every row below: the hole is on main.
- V2: `gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `_RENDERED_MARKUP` exist (`gate.py:197-226`) and nothing calls them; `gate.py:151` builds `_MD`. V3: `gate._rendered`'s docstring says `AKIA&amp;...` "shows a key joined"; a renderer shows `AKIA&IOSF...` (BN-P1d-2). V4: `redact.strip_ansi` puts a SPACE where an escape stood between two letters on purpose; a terminal shows the parts JOINED.
- V5: the redactor's own views (`runmap._views`; P1b adds `composed`) do not delete markers, escapes or control characters and do not fold case or look-alikes for PATTERN matching; `redact.py:~1204 _sweep` is literal and case-sensitive. The split key reaches the model through documents, tool results, tool errors and logs (sibling report S1-S5).
- V6: `textnorm.scan_holds(text, value)` holds `AKIAIOSFODNN7EXAMPLE` in `key AKIA**IOSFODNN7EXAMPLE** x` and in the lower-case copy; raises `ViewTooShort` for `10.0.0.1`; `textnorm.fold` turns Cyrillic look-alikes and a combining accent back into Latin but keeps `**`.
- **R1 (new, decisive for the design):** `textnorm._scan_key` (`origin/core/P1b-fixwip`, `textnorm.py:1088-1093`) keeps only letters and digits (`str.isalnum()` true, category not `Lm`) after its step function. So `scan_holds` ignores `*`, `_`, `~`, backtick, `.`, `&`, spaces, controls and line breaks BY ITSELF. Consequence: for the RESIDUE test only transformations that carry or change letters and digits matter (decode of entities, percent-codes and escapes; deletion of tags and escape sequences, whose payload is letters/digits such as `0m` or `b`; fold of look-alikes if `scan_holds` does not already do it, BS-0 reads that). Deleting markers, controls and line breaks matters only for the LEARNING pass (a pattern needs contiguous characters). UNVERIFIED: the P1b fix batch may change this; BS-0 re-reads it on merged P1b (stop rule in BS-0).
- V7: `register_value` (strict) raises `CoverageRefused` for Latin and digit values. P1d never calls it. V8: a prototype that ran the whole redactor BEFORE the gate broke two fuzz tests; only the defang moves.
- V9 (prototype cost, one 4-CPU container, shared machine): 3,000 chars 0.21 s (today 0.03 s); 30,000 chars 2.69 s (0.24 s); 120,000 chars 12.9 s (0.98 s). Loop order matters (views outer, values inner; 190 s the other way at 30,000).

## Merge-order preconditions (gates for the build start, BS-0)
1. P1a (PR 63) and P1b merged (P1b fix batch is open; P1d builds on MERGED P1b). The fail-before base is post-P1b main; a P1d test file imports `textnorm` only inside test functions.
2. P1b exposes the `textnorm` minimum scan length as a named constant `TN_MIN` and its tests pin the `scan_holds` error classes (`ViewTooShort`, `EmptyView`, `TextnormError`) (ORDER 167 item 1). BS-0 reads both; a difference from V6/R1 = STOP, back to review.
3. `defaults.py` can take the new constants; `vulture_whitelist.py` and `tools/mutation_runner.py` exist on the base (else `tests/p1d_mutants.py` uses a plain subprocess loop and says so).
4. The 5 baseline failures are listed by test id and cause and fixed here or recorded as environment with an owner before "done".
5. **Hard dependency (ORDER 167 item 2):** `runmap.P1D_APPLIED = True` is added by P1d; the client profile's start function (BS-0 names file and function) refuses to start when `getattr(runmap, "P1D_APPLIED", False)` is false, with a message naming P1d. Negative test `test_client_profile_refuses_without_marker` (monkeypatch the marker away) and mutant M22.

## RUNG TABLE (R447, R448, R450; scale of 2026-11-06: 1 no-code, 2 own core modules, 3 existing free tools, 4 free libraries, 5 own new code last. Tier C: a core change on a redaction path.)
Gate: core SDK change, no client, no fee, no new dependency. Rung 1 closed (R447). Rung 3 closed (a model feature cannot be exact and runs after the text left). **Guarantee class:** **exact** = holds for every value in the set named in the row, up to the stated cap, with a test; **best effort** = holds for the cases tested; **detection-only**. An unknown secret with no pattern (a plain password, no key word) is OUT of the guarantee. **In one line: reuse covers building the views; our new code is the residue check, the learning pass for one fixed-width key shape, and the wiring.**
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| views, decode, fold | read the text as a renderer, terminal or person shows it | 2 (`gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `redact._ANSI`, `strip_controls`, `runmap.undo`, `textnorm.fold`) | V2, V4, R1 | one private function with a fixed order | exact on the listed rows up to the cap, best effort for other combinations | CUT-TO-CONFIG+GLUE |
| Markdown library | rendered view | 4: `markdown-it-py` (already imported by `gate.py:72`) | CommonMark only; does not read Slack `*bold*` / `~strike~`; decided CUT now (no build step) | nothing | n/a | CUT |
| fold and scan | look-alikes, accents, case, separators | 2 (P1b `fold`, `scan_holds`, `scan_cache`) | V6, R1 | no second normaliser | exact for P1b's documented coverage; short values see below | CUT-TO-CONFIG+GLUE |
| learning pass | find an UNKNOWN AKIA/ASIA key with an inserted character or in lower case | 2 (same pattern, two more views) | UNVERIFIED; BS-2 measures false learn first | the shape on two views plus the digit rule | exact on the rows; best effort otherwise; ships only if BS-2 shows 0 false learns | KEEP-CODE (small) |
| residue rule | decide whether a known value is readable with placeholders put back | 4: detect-secrets, gitleaks, Presidio find SHAPES; none compares a text with OUR run map | not run (UNVERIFIED); test idea: row KV-case | redaction before a person (R447 guarantee) | exact for known values up to the cap | KEEP-CODE, about 80 lines (estimate) |
| fail closed, bounded cost | never return an unchecked text | 2 (`InputTooLarge`) | V9 | one deterministic cap, one catch-all | exact (the refusal) | KEEP-CODE, about 25 lines |
| defang after redaction | `[.]` must not split an e-mail or host before the redactor | 2 (`gate.sanitise_text`) | V8 | one parameter and one call order | exact | KEEP-CODE, about 15 lines |
**80 percent (R448):** the needs are: read as rendered; decode; fold; unknown shapes in other views; decide what is readable with placeholders put back; fail closed; mask before our own markup. Rungs 2 and 4 meet needs 1 to 3 (three of seven); no library works inside the choke point. Under 80 percent; a guarantee path in any case. **Cost (estimate):** build 10-14 agent-hours plus uncapped review rounds; 0 fees, 0 model tokens, 0 new dependency.

## Goals and Non-Goals
**Goals.** (G1) No known value is readable in any text `redact_text` returns or any card `clean` returns, for the families in the rows below, up to the cap. (G2) One implementation at the one choke point; `clean`, `SlackChannel._blocks`, documents, tool results, tool errors, logs and `redact_value` get it without a new call site. (G3) A text the rule cannot clear is withheld in a stated way (caller table). (G4) The false-withhold rate and the H34 over-mask rate are measured separately (BS-3). (G5) E-mail addresses and internal host names are masked in cards.
**Non-Goals.** (N1) An unknown secret with no pattern. (N2) What a person types after the card is posted. (N3) `tools._secret_forms` / `_scrub_layers` (S6): P2d-2. (N4) A new endpoint or console. (N5) Exactness above the cap: above it the text is withheld, not checked. (N6) All-letter AKIA/ASIA keys and keys with the inserted character inside the digits, when NOT already known and written in lower case or with an inserted character: best effort (R3).

## Alternatives considered
- **A1 Heal and show** (show the redacted healed view). Rejected: a fold or case view changes the characters, the card would differ from the request the approver approves, and the person's own bold markers vanish. Trigger: BS-3 shows a false-withhold rate above ceiling for deletion-only views; then A1 for those views only.
- **A2 Offset-mapped masking.** Rejected for now: needs span tracking inside `textnorm` (P1b frozen).
- **A3 Escape the markers in the shown text.** Rejected: no help on Slack `plain_text`; breaks code in cards.
- **A4 Check only in `clean`.** Rejected: the model path has the same hole, `_blocks` is a second call site.
- **A5 Pre-mask only e-mail and host before the gate.** Rejected: covers two kinds; replaced by moving the defang after redaction.
- **A6 A library** (Presidio, detect-secrets, gitleaks, markdown-it-py): none knows the run map (rung table).
- **A7 Text slices for large texts.** Rejected: filler longer than the overlap splits a key across slices; slices are a new bug class. Replaced by one cap and withhold above it (ORDER 167 item 5).
- **A8 Fixed-point loop for views.** Rejected: step order cannot matter in a fixed point. A fixed ordered pipeline; ONE bounded second round of steps (a)-(b) only if a combination row C01-C10 fails on one pass (decided by the row, BS-0/build).
- **A9 Approve-path field (`display_withheld`) or a result object.** Rejected as default: new surface in the approvals state. The approve path re-runs the same check on the stored summary (see "Operator route"); a field only if that cannot reach the summary (ORDER 167 item 4).
- **Chosen:** fixed-order views, a narrow learning pass, the residue rule, all inside `redact_text`; withhold by default; raise only for cards.

## Risks and mitigations
- R1 False withholds. Only a KNOWN value readable in a deleting view of the dropped form withholds; ceilings in BS-1 and BS-3; guard rows F01-F17.
- R2 Cost. One deterministic cap and a fast path (below); latency target BS-4. Tests count characters and views, never seconds.
- R3 The learning pass over-learns. Prose such as `Southeast Asia and Oceania` becomes `southeastasiaandoceania` squeezed. Rule (written now): on the squeezed and case-folded views the shape is `(AKIA|ASIA)([A-Z2-7]{16})` (the real base32 alphabet, so `0 1 8 9` break the run and year strings drop out), unanchored, case-insensitive, and a match counts only if its 16 trailing characters contain at least one of `2-7`. About 3.6 percent of real keys have no such digit; they are found when written as is (the redactor's own pattern) but not when lower-cased or split (best effort, N6). BS-2 measures; the squeezed/case-folded learning ships ONLY if BS-2 shows 0 false learns on its corpus. If BS-2 fails, rows H31-H33/H35, mutants M10-M12 and the squeezed branch of `_learn_unknown` are deleted by this rule, and the ticket is NOT re-reviewed for it (ORDER 165 item 2: H31-H35 are meant to be fixed; if they cannot be, the lead decides, NEEDS-LEAD 3).
- R4 A model-path text silently disappears. The notice is visible to the model and the operator log; no exception; a run is never ended by a withhold.
- R5 Guard-test change. The learning pass is a private function, not the public `redact_text`, so the hook lint of `test_k5_round11.py` needs no exemption (BN-P1d-3).
- R6 P1b changes under P1d. BS-0 pins the P1b head, `TN_MIN` and the error classes; P1d calls nothing private of `textnorm`.
- R7 The `&` fix over-masks (H34). Measured, accepted (ORDER 166 item 2).
- R8 Hostile text forces a withhold (`AKIA**...` in a document blanks it or makes a request not approvable). Fail-safe, accepted; the log line carries `source` and counts, the operator counts log lines; no alert threshold is built.
- R9 `redact_value` stores the notice in place of a leaf. If an approval-binding hash reads a stored redacted text, the bound content changes. BS-0 lists every reader; if one hashes, `redact_value` uses `on_residue="raise"` and that caller handles it (recorded in the BS-0 report).
- R10 Judge and vendor screens receive the notice instead of the text; a screen that returned "clean" for a notice would fail open inside a guard. Rule in the caller table; test `test_judge_refuses_on_notice`.

## Sinks
| sink | what a reader can re-join | views applied |
|---|---|---|
| Slack card (`plain_text`) | a person copies `AKIA**IOSF...**`; an entity shows `&amp;`; a colour code shows as junk | all |
| Markdown viewer / `notify` text | the viewer shows the key whole | all |
| `FakeChannel`, log | verbatim | all |
| model (documents, tool results, tool errors, `safe_head`, `redact_value`) | a model re-joins and may echo | all |
The weakest reader decides: the same rule for every sink.

## Constants (only two new; both in `defaults.py`, no literal in code)
- `P1D_MAX_TEXT_CHARS`: start **30000**. Commit rule (BS-4): the largest size at which the 95th percentile of `redact_text` over the BS-1 corpus and the largest real-shaped document stays under `REDACT_BUDGET_S / 4` on the build machine, **never below 30000**. If the bound cannot hold at 30000 even with the fast path: STOP, back to the lead (NEEDS-LEAD 1).
- `P1D_MIN_KEY_CHARS`: start **8**; effective floor `max(P1D_MIN_KEY_CHARS, TN_MIN)`, `TN_MIN` read at BS-0 (never copied).
- The number of views is NOT a constant: the pipeline is fixed (at most 5 deleting views); `_healing_views` asserts `len(views) <= PIPELINE_VIEWS` (a module constant, 5).
- Reasons: `residue | size | error`. No clock, no deadline, no alert-per-minute constant.

## The algorithm (pseudocode; no code; exact regexes are named, the builder writes them from this)
```
redact_text(text, mapping, neutralise=None, *, on_residue="withhold", source="", approval_id=""):
  try:
    text = text.replace("\x00", "")
    if len(text) > P1D_MAX_TEXT_CHARS:  return _withhold("size")
    shown, mapping2 = <the existing redaction, unchanged, incl. neutralise>
    views  = _healing_views(text)                      # deleting views of the INPUT
    learned = _learn_unknown(views, text)              # dict original->placeholder-free value, learning only
    known  = originals(mapping2, seeds excluded) | learned.values()
    return _finish(source, shown, mapping2, known, on_residue, approval_id)
  except LookalikeCopy: raise
  except Exception as exc:                             # InputTooLarge, TooDeep, TextnormError, RecursionError, MemoryError, bugs
    return _withhold("error", type(exc).__name__)      # logs the class name only; raise mode: raise LookalikeCopy from None

_withhold(reason):  log one WARNING line; if on_residue == "raise": raise LookalikeCopy else return WITHHELD_NOTICE

_healing_views(t):   # CUMULATIVE: each step takes the previous step's output; every output joins the set; de-duplicated
  fast path: if t is printable ASCII and has none of  & % \ < >  ESC and no C1 -> steps a-d return t itself: views = (t,)
  v0 = t
  a  = undo(v0)                                        # entities, percent-codes, backslash/JSON escapes, to P1b depth (BS-0 reads it; H08 needs two rounds)
  b1 = delete_carriers(a)                              # tags and comments  (gate._RENDERED_MARKUP, else  <!--.*?-->|</?[A-Za-z][^>]{0,200}>),
                                                       # ANSI/CSI/OSC/C1 sequences and a lone ESC  (redact._ANSI + \x1b + [\x80-\x9f])   -> their payload (letters/digits) is gone
  b2 = delete_noise(b1)                                # [*~`] always; "_" when NOT between two alphanumerics (so snake_case stays);
                                                       # controls [\x00-\x08\x0b-\x1f\x7f] , Cf/Cc invisibles, CR, LF, U+2028/2029
  c  = textnorm.fold(b2)                               # look-alikes, accents, full-width
  d  = delete_noise(c)                                 # a full-width marker becomes a plain one only after fold
  return dedupe((v0, a, b1, b2, c, d)); assert len(result) <= PIPELINE_VIEWS

_learn_unknown(views, text):
  found = {}
  for v in views:           run the redactor's pattern table on v, discard the output, keep each found ORIGINAL (the substring of v)
  for s in (squeezed(views[-1]), lower(squeezed(views[-1]))):
      for m in re.finditer(r"(?i)(AKIA|ASIA)([A-Z2-7]{16})", s):       # unanchored (H35), case-insensitive
          if re.search("[2-7]", m.group(2)): found.add(m.group(0))      # the digit rule; the value is the VIEW substring
  return found            # only when BS-2 passed; otherwise the second loop is absent

_finish(source, shown, mapping, known, on_residue, approval_id):
  for form in (dropped(shown), dropped(undo(shown)) if different):
      for v in _healing_views(form):                                     # views OUTER, values INNER, inside textnorm.scan_cache()
          for k in known: if _holds(v, k): return _withhold("residue")   # _holds = textnorm.scan_holds, or the exact fallback ("Short values")
  # the put-back count test, ALWAYS also run:
  for t in (shown, undo(shown) if different):
      p = put_back(t)        # ONE pass: each genuine placeholder (in the map, not a seed) -> " "+original+" "; a token-shaped text inside a put-back original is not put back again; tally per original
      for k in known: c = count(scan_key(k) in scan_key(p)); e = count the tally explains; if c > e: return _withhold("residue")
  return shown
```
- The put-back formula is quoted from `designs/lookalike-leak.md` section 5 item 3 (frozen draft 11, which owns the algorithm): `c` = count of the value's scan key (the `isalnum` characters, case-folded) in the scan key of the put-back form; `e` = the count the tally explains (copies inside put-back originals; adjacent originals count as one run because the scan key drops the spaces). The builder copies rows LK-JAMO-PB (Korean, Tamil) and LK-UNFOLD into the fixtures file character for character. The note is pinned by date; a later change there is a P2d-2 matter, not a P1d return-to-review. The dropped-form test is KEPT only if a row needs it only (M13 rule); the put-back count test stays because the dropped form has a space and cannot see a placeholder that joins a value back.
- **The text checked is the text returned:** `_finish` runs on the string `redact_text` returns, after `neutralise`. In `clean` the joined pass and `defang_text` come after; `defang_text` only inserts `[` `]` around `.`, which the scan key ignores (R1), and `_TAGS.sub` is itself run as ONE more call of `redact_text` (item 7), so the returned bytes always went through `_finish` last except for the defang. Test `test_returned_card_bytes_pass_the_check` re-runs `_finish` on the returned card for H01-H25.
- **Fast path:** cost V9; the fast path changes no outcome (steps a-d return the text itself for such text); the learning pass still runs on the squeezed and case-folded views. Mutant M20.

## Refusal behaviour: every caller of `clean` and `redact_text` (BS-0 completes this table from a grep on the base; a test fails if a caller is not in it; a caller that cannot be matched blocks the build)
One literal text per constant:
- `WITHHELD_NOTICE` = `(withheld: this text may hold a secret written with hidden formatting)`; helper `runmap.is_withheld(text) -> bool` (equality with the constant).
- Card text (posted once) = `Request <approval_id> cannot be shown safely. It may hold a password, key or e-mail address written with formatting inside it. It cannot be approved from this card. Ask the sender to send it again without formatting, or deny it.`
- Fallback line for plan inputs = `Inputs: not shown. They may hold a password or key written with formatting inside it.`
- Operator log line (WARNING, logger `hadavin_sdk.guard.runmap`) = `redaction withheld a text: reason=%s source=%s approval_id=%s chars=%d views=%d known=%d`; `reason` in `residue|size|error`; `source` empty on model-path callers is logged as `-`, so is an empty `approval_id`; never any content; the `error` case also logs `exc=<class name>`.
| caller | on withhold | buttons | pinning test |
|---|---|---|---|
| `SlackChannel._blocks` / `update` / `send` (`slack_channel.py:81,197`) | posts the card text once; `sent_at` set so `resend_unsent` finds nothing | no | `test_h30` |
| `requests.summary` (`requests.py:39,47`) | plan inputs replaced by the fallback line; the request is not approvable | no | `test_h40`, `test_no_approve_buttons_when_inputs_withheld` |
| `cards.py:59`, `channel.py:111` `post_card` | same as `_blocks` | no | `test_caller_cards`, `test_caller_post_card` |
| `channel.py:104` `notify` (top-level text) | the CARD text (with the id if known) replaces the message; one log line | n/a | `test_caller_notify` |
| `FakeChannel` | records one send of the card text | no | `test_h40` |
| `agent_loop._deliver` (`~560-567`) | nothing raises there; a test pins it | n/a | `test_deliver_never_sees_lookalikecopy` |
| model path: `redact_untrusted` (documents), `prepare_output`, `redact_layered` (tool results), `error_reason`, `safe_head` | returns `WITHHELD_NOTICE`, logs, **never raises**; a JSON tool result becomes the notice string and the consumer treats a non-JSON result as an error (fails closed) | n/a | rows S1-S5 |
| `redact_value` (`runmap.py:569-598`; stored records, audit, `evidence.py:191`) | the leaf becomes `WITHHELD_NOTICE` (model-path rule); R9 decides if one caller raises | n/a | row S5 and `test_redact_value_notice` |
| **guards:** `guard/judge.py:71`, `guard/bedrock_guardrail.py:98`, `evals.py:63` (S14, S15) | a notice means **refuse or escalate** (the existing "unsafe/escalate" verdict of that guard, named at BS-0), never "clean"; for `evals.py` the case is marked failed | n/a | `test_judge_refuses_on_notice`, `test_guardrail_refuses_on_notice` |
| `evidence.grounded` (N2, `evidence.py:135-163`) | a notice never grounds an action (a mismatch already fails closed) | n/a | `test_grounded_fails_on_notice` |
BS-0 adds every other caller it finds.

## Operator route (ORDER 166 item 3 and ORDER 167 item 4: the existing route, least new surface)
UNVERIFIED which files hold it; BS-0 greps the approvals package, names the file and function of (i) the EXISTING deny call, (ii) expiry, (iii) the approve function, and who may call each. **Design (one, no alternatives):** (1) a request whose card was withheld stays in the store like any other pending request; it carries no buttons. (2) It leaves the pending state through the existing deny call or the existing expiry, which need no view of the content; the operator reads the request id and reason from the log line. (3) The existing approve function **refuses** such a request: it re-runs `redact_text(stored summary, run map, on_residue="raise")` and refuses on `LookalikeCopy` with the existing refusal error class (no new stored field, no schema change, `receiver.py` untouched). Negative test `test_withheld_request_cannot_be_approved_by_callback` (a hand-made approve call on a withheld request is refused; mutant M21). **Stop rules for BS-0:** if the approve function cannot reach the stored summary or the run map, or if deny is reachable only from the card button, the ticket goes back to review with ONE allowed addition (a `display_withheld` field, proven by a test that the approve path reads it; or one operator deny call as a ticket line), as ORDER 167 item 4 allows. If the content must be reviewed by a person, that is P1d-c (ledger 010), not this package.

## Short values (ORDER 166 item 5, ORDER 167)
`textnorm.scan_holds` raises `ViewTooShort` for a value below `TN_MIN` (or when no view reaches its minimum). For such a known value found at run time: (1) **exact fallback `_holds`**: case-INSENSITIVE exact substring search in EVERY deleting view of the dropped form, with a boundary rule: `(?<![0-9A-Za-z])` before and `(?![0-9A-Za-z])` after the escaped value, each side applied only when the value's own first or last character is a letter or digit (a value that begins or ends with punctuation has no boundary on that side); (2) values shorter than the effective floor `max(P1D_MIN_KEY_CHARS, TN_MIN)` are OUTSIDE the guarantee (best effort, said in the CHANGELOG); (3) **recording:** one INFO line per call that used the fallback: `redaction coverage=exact_only values=%d` (no content); (4) **strict mode unchanged:** P1d never calls `register_value`; the client-profile strict mode (`TEXTNORM_STRICT_COVERAGE`) still makes `register_value` raise `CoverageRefused` for such a value; guard test `test_strict_mode_still_refuses` pins P1b's behaviour and that nothing in P1d lifts it. The fallback is a run-time check on found values, not a registration.

## Scope of S11, S16, S6, S13
- S11 (`k1b/redaction.py sensitive()`: decides if a key NAME is a credential, never calls the redactor) and S16 (`receiver.log_message`: no redaction call at all): **P1d-b**, own package, ledger 006 and 009, ticket written after this plan review is clean and built right after P1d. P1d keeps its helpers private; P1d-b promotes what it needs.
- S13 (`redact.py:1204 _sweep`, the known-value sweep inside `redact_text`): **in P1d** (ORDER 167 item 3): the residue rule covers it; rows H22-H24 and S13-1/S13-2 below; ledger 001 and 004 name it.
- S6 (`tools._secret_forms` / `_scrub_layers`, handed-out secrets in 11 fixed spellings): does NOT call `redact_text`; **P2d-2**, ledger 005, owner P2d-2, with the SAME hard dependency as P1d (no client data before both land).

## Template fields
- **Package id and name:** P1d, "split secrets at the choke point". One pull request on branch `core/P1d`, from main after P1a and P1b merge. **Path class:** redaction AND security; **extended review (no round cap): yes**, plan and result. **Depends on (merged first):** preconditions above; not P1c (row H27 holds with or without P1c).
- **Class (R337, R7):** "a value is matched only in the spelling as written, while a reader or renderer reads another spelling". Standards (cited from memory; read date UNVERIFIED, R450): CommonMark 0.31 sections 6.2, 6.1, 2.5; ECMA-48 sections 5.4, 8.3; Unicode UAX #15 and UTS #39.
- **Source of the code:** our own code only; nothing copied.
- **Neutral default / working alternative:** the redactor has no vendor; the neutral default is the built-in rule; the alternative A1 has its trigger. `on_residue` selects withhold (default) or raise.
- **Files (create / change / delete, each with the reason):**
  - change `src/hadavin_sdk/guard/runmap.py`: `redact_text`, `LookalikeCopy`, `WITHHELD_NOTICE`, `is_withheld`, private `_healing_views`, `_learn_unknown`, `_finish`, `_withhold`, `P1D_APPLIED`. The helpers stay in `runmap.py` (default: NO new module); BS-0 may move them to `guard/_views.py` only if importing `gate` privates would create a cycle or `runmap.py` would pass its size gate, and records why.
  - change `approvals/channel.py` (`clean`: raise mode, defang after redaction, pre-mask deleted), `approvals/slack_channel.py` (`_blocks`), `approvals/requests.py` (fallback line, not-approvable, approve check), `approvals/gate.py` (`sanitise_text(defang=)`, `defang_text`, docstring of `_rendered`), `approvals/cards.py` if the caller table needs it.
  - change `guard/redact.py`: SECRET value stop-set gains `&` (H34).
  - change `guard/judge.py`, `guard/bedrock_guardrail.py`, `evals.py`, `runtime/evidence.py`: handle the notice as in the table (only the few lines named there).
  - change the client-profile start function (file named by BS-0): the marker refusal.
  - change `defaults.py`: the two constants. change `vulture_whitelist.py` (remove the `gate._rendered` entry when the file exists on the base), `CHANGELOG.md`.
  - create `tests/test_p1d_rows.py`, `tests/test_p1d_callers.py` (rows in the caller table with inputs and assertions), `tests/fixtures/p1d_cases.py`, `tests/p1d_mutants.py`, `tools/p1d_corpus.py` (BS-1 to BS-3), `tools/p1d_cost.py` (BS-4), evidence files under `handover/evidence/P1d/`.
  - NOT in P1d: `k1b/redaction.py`, `approvals/receiver.py` (P1d-b), `tools.py` S6 (P2d-2).
- **Interface:** public: `runmap.LookalikeCopy(RedactionError)` (message = the class name only); `WITHHELD_NOTICE: str`; `is_withheld(text: str) -> bool`; `redact_text(text, mapping, neutralise=None, *, on_residue: Literal["withhold","raise"] = "withhold", source: str = "", approval_id: str = "") -> str` (`source` and `approval_id` only in the log line; no existing function loses an argument); `gate.sanitise_text(text, *, defang: bool = True)`; `gate.defang_text(text)`; `P1D_APPLIED: bool`. Private (underscore, no `__all__`; P2d-2 promotes what it needs): `_healing_views(text) -> tuple[str, ...]`; `_learn_unknown(views, text) -> set[str]`; `_finish(source, shown, mapping, known, on_residue, approval_id) -> str` (returns the text, `WITHHELD_NOTICE` or raises `LookalikeCopy`; computes and logs `chars`, `views`, `known`; the only place that logs).
- **Behaviour, exactly:** the algorithm block above, plus: (1) the pattern fix in `redact.py`: the SECRET assignment value extends over `&`; its stop-set stays white space, a quote and `;` (`,`, `)`, `>` do not end it); (2) `clean` = NUL removal, ONE `redact_text(text, seeded, neutralise=_neutralise, on_residue="raise", source="card", approval_id=...)` where `_neutralise` = `gate.sanitise_text(..., defang=False)` plus `withhold_commands`; then the joined pass (`_TAGS.sub`) as a SECOND `redact_text` call with a fresh copy of the same `seeded` map plus what the first call learned; then `defang_text` on the result; the pre-mask of revision 1 is deleted; (3) callers: the caller table. Fallback if BS-4 finds a kind the moved defang still breaks: a documented per-kind pre-mask for exactly that kind (BN-P1d-8).
- **Existing core code reused:** `gate._views`, `_rendered`, `_ANSI_AS_TEXT`, `_RENDERED_MARKUP`, `redact.strip_ansi`/`_ANSI`, `strip_controls`, `runmap.undo`, `textnorm.fold/scan_holds/scan_cache`, `InputTooLarge`, `TooDeep`. Checked and not reused: `textnorm.register_value`, `tools._secret_forms`.
- **Security and least-privilege notes:** no identity, right, secret or config beyond two constants. No new read of raw stored text: the approve check reads the summary the approve path already holds. The operator line carries counts, never content (a test greps the log for the key). Test values are built from parts; the only whole-key literal is `AKIAIOSFODNN7EXAMPLE`.
- **Rollback:** tag `pre-P1d` before the pull request. **Non-revertible semantic changes, marked in the CHANGELOG:** stored records and model text may contain `WITHHELD_NOTICE`; `clean` raises `LookalikeCopy`; the SECRET value is masked over `&`; e-mail and host are masked in cards. Loud-failure test `test_withheld_notice_is_loud` (a withheld text is never returned as if clear).
- **Reviewers:** correctness (`egm-codebase-details`) + adversarial (`egm-design`, `egm-implementation-readiness`), fresh agents with the diff, this ticket and the evidence only; redaction path, no round cap.
- **Done =** the plan's stop rule (a fresh round finds no blocker or major) and all gates green: tests (3.12 and 3.13), ruff check, ruff format --check, bandit -ll, guard tests, CodeQL, SonarCloud, CodeRabbit; ledger rows 001-004, 007, 008 FIXED-VERIFIED; hand-over rows 005, 006, 009, 010 carry a named owner package, the same hard-dependency note and a date (their status under `ledger_check` is NEEDS-LEAD 2); the lead merges.

## Failing inputs (literals in `tests/fixtures/p1d_cases.py`; parametrised, the row id is the test id)
**Literals (built from parts):** K = `"AKIA" + "IOSFODNN7EXAMPLE"`; K4 = `AKIA`; K16 = `IOSFODNN7EXAMPLE`. S = `"Tq7mZ" + "4xKp2Vb9Lr3NcW8dYh6uJs"` (S5 = `Tq7mZ`, S22 = `4xKp2Vb9Lr3NcW8dYh6uJs`). E = `"anna" + "." + "m" + "@" + "example" + "." + "org"`. PW(n) = the first n characters of `Qm8vRt2xLp5nZc7bKd3wHj`. **KV** = the text first holds `password=<S>` (S enters the map), then the second copy named in the row. H29: v1 = `Zx4cV7bN1mQa`, v2 = `Wl9sD3fG6hJk`. H36: E percent-encoded `anna%2Em%40example%2Eorg` and entity-encoded `anna&#46;m&#64;example&#46;org`.
Every fb row fails on post-P1b main by an assertion that the value is shown. By R1 (scan key) a KV row's second copy is found in the plain view; rows marked "(carrier)" need a transformation that carries letters or digits and so decide the residue test by themselves.
| row | group | input | on base | expected after P1d |
|---|---|---|---|---|
| H01 | fb | `key AKIA**IOSFODNN7EXAMPLE** here` | key shown | withheld (learned: squeezed view) |
| H02-H06 | fb | `AKIA**IOSFODNN**7EXAMPLE`; `AKIAIO*SFODNN7EXAMPLE*`; `AKIA~~IOSFODNN7EXAMPLE~~`; ``AKIA`IOSFODNN7EXAMPLE` ``; `AKIA_*IOSFODNN7EXAMPLE*_` | shown | withheld |
| H07 | pb | `AKIA<b></b>IOSFODNN7EXAMPLE`; `AKIA<!-- -->IOSFODNN7EXAMPLE` | masked | masked, same |
| H08 | pb | `AKIA&ZeroWidthSpace;IOSFODNN7EXAMPLE`; `&shy;`; `&NoBreak;`; `&InvisibleTimes;`; `&#8203;`; `&#x200B` (no `;`); `&amp;#8203;` | masked | masked, same |
| H09 | pb | `AKIA&#73;OSFODNN7EXAMPLE`; hex `&#x49;`; `&#73` (no `;`) | masked | masked, same |
| H10 | fb (carrier) | KV, second copy `<S5>&amp;<S22>` | shown | withheld |
| H11 | fb (carrier) | `AKIA\x1b[0mIOSFODNN7EXAMPLE` | shown as `AKIA IOSF...` | withheld |
| H12 | fb (carrier) | four variants: `\x1b[38;5;196m` inside the key; C1 `\x9b0m`; OSC `\x1b]0;t\x07`; OSC 8 `\x1b]8;;http://x\x07` | shown | withheld (each its own case) |
| H13 | fb | `AKIA\\x1b[0mIOSFODNN7EXAMPLE` (escape written as text) | shown | withheld (over-refusal accepted: a person reading the literal joins it) |
| H14 | fb | `AKIA\x1bIOSFODNN7EXAMPLE` (lone ESC) | 19 of 20 chars shown | withheld |
| H15 | fb | `x\x08AKIAIOSFODNN7EXAMPLE`; `AKIA\x08IOSFODNN7EXAMPLE` | shown | withheld |
| H16 | fb | `AKIA\rIOSFODNN7EXAMPLE` | shown on two lines | withheld |
| H17 | pb | BEL, DEL, NEL `\x85`, VT, FF, NUL, ZWSP, ZWJ, WJ, U+202E, soft hyphen, each once between `AKIA` and `IOSFODNN7EXAMPLE` | masked | masked, same |
| H18 | fb | `AKIA` + U+0301 + `IOSFODNN7EXAMPLE`; U+0323 variant | shown | withheld |
| H19 | pb | the key in full-width forms | masked | masked |
| H20 | fb | KV, second copy `<S5>` + U+FF0A (full-width `*`) + `<S22>` | shown | withheld |
| H21 | fb | Cyrillic `А` (U+0410) for both `A` of `AKIA` (key not in the map) | shown | withheld (learned after fold) |
| H22 | fb | KV, second copy `<S5>**<S22>**` | shown | withheld (S13) |
| H23 | fb | KV, second copy S in lower case | shown | withheld (S13) |
| H24 | fb | KV, second copy `<S5>\n<S22>` | shown | withheld (S13) |
| H25 | fb (carrier) | `password=<S5>\x1b[1m<S22>` | `<SECRET_1> ` + tail | withheld |
| H26 | fb | `contact <E> please` | `anna.m@example[.]org` | `contact <EMAIL_1> please` |
| H27 | fb | `host db01.corp.example.com down`, with a spy `neutralise` | the redactor receives `db01[.]corp...` | the redactor receives `db01.corp.example.com` unchanged (`test_redactor_sees_undefanged_text`); AND, when the base has a HOSTNAME kind (P1c merged), the output holds that kind's placeholder (token read at BS-0) and no `db01`; when it has none, the output is the defanged text and the row says so |
| H28 | fb | `anna.m**@example.org**`; `anna.m@exam\x1b[0mple.org` | shown | withheld |
| H29 | pb | `passwor<span></span>d%3D<v1>%0D<v2>` | decided at BS-0 by running it on the base: if the tail is shown the row is fb and tag deletion (M6) has this killer; if masked it is pb and M6's killer is H29b: KV, second copy `<S5><b></b><S22>` (carrier) | masked tail / withheld |
| H30 | fb | H01's input as `req.summary` through `SlackChannel._blocks`; and `requests.summary` of a plan whose input holds the key split by `**` | shown | the card text, no buttons, no key, no retry |
| H31 | fb | `AKIAIOSFODN\nN7EXAMPLE` (not in the map) | shown | withheld (BS-2 gated) |
| H32 | fb | `akiaiosfodnn7example` (lower case, not in the map; has a `7`) | shown | withheld (BS-2 gated) |
| H33 | fb | `AKIA&amp;IOSFODNN7EXAMPLE`; `AKIA.IOSFODNN7EXAMPLE`; `AKIA\*IOSFODNN7EXAMPLE` | shown | withheld (the squeezed view reaches the inserted character; BS-2 gated) |
| H34 | ow | `password=ab12&cd34ef56gh78ij`; also `password=<S5>&amp;<S22>` | `<SECRET_1>&cd34...` | whole run masked (two rows: fb for the `&` stop-set, ow for the over-mask of `&user=bob`) |
| H35 | fb | `keyzAKIAIOSFODNN7EXAMPLE` | shown | withheld (unanchored shape; BS-2 gated) |
| H36 | fb | the two encoded e-mails of the literals | shown | withheld |
| H37 | fb | **chosen at BS-0:** one fixed-prefix token kind OTHER than AKIA/ASIA from the redactor's pattern table, built from parts, split by `**` (H37a), by a newline (H37b) and by a full-width `*` (H37c), not in the map | shown | withheld (learned from the deleting views). If the table has no such kind, M4/M5-noise are declared equivalent and the noise-deleting steps (b2, d) are removed from the code |
| H40 | fb | H01 as a plan input through `requests.summary` then `FakeChannel.send` | key shown | the fallback line, no key, no buttons; one send, no retry |
| S13-1, S13-2 | fb | `password=<S>` in a document, then S in another case, then S split by `**`, through `redact_untrusted` | shown | the notice (model path) |
**Combination rows (one pass proof):** C01 `AKIA**` + Cyrillic `О` + `SFODNN7EXAMPLE**`; C02 `AKIA**IO` + U+0301 + `SFODNN7EXAMPLE`; C03 `AKIA&ast;&ast;IOSFODNN7EXAMPLE`; C04 `AKIA&amp;ast;IOSFODNN7EXAMPLE`; C05 `AKIA\x1b[0m**IOSFODNN7EXAMPLE`; C05b `AKIA&#27;[0mIOSFODNN7EXAMPLE`; C06 `AKIA\x1b[0m\nIOSFODNN7EXAMPLE`; C07 `akia**iosfodnn7example`; C08 `AKIA%2A%2AIOSFODNN7EXAMPLE`; **C09 (delete before decode)** `AKIA&a**mp;#73;OSFODNN7EXAMPLE` and `AKIA%2<b></b>AIOSFODNN7EXAMPLE`; **C10 (double decode)** `AKIA%252AIOSFODNN7EXAMPLE`. Each KV twin (the second copy of S written the same way) is a case too. Expected: withheld. If C09 or C10 fails on one pass, A8's bounded second round is added; the decision is by the row.
**Digit-rule rows (named tests, literal inputs):** `asia-prose` = `Southeast Asia and Oceania`, `Asia 2024 Q3 revenue growth`, `Eurasia 2025 results`, `Asia-Pacific 2025 results` (all expected NOT withheld); `asia-nodigit` = a made-up all-letter key `AKIA` + 16 letters from `A-Z` without `2-7` written in lower case: expected NOT withheld, documented as outside the guarantee (N6).
**Boundary rows (short values), `TN_MIN` read at BS-0:** n in {`TN_MIN-1`, `TN_MIN`, `TN_MIN+1`} and variants {plain, lower case, `**` inside, escape inside}: KV with PW(n). Expected: n >= the effective floor withheld in every variant (the fallback is case-insensitive); n below the floor: no crash and one `coverage=exact_only` line, documented outside the guarantee.
**Size and error rows:** X01 text of exactly `P1D_MAX_TEXT_CHARS` with a split key 100 characters before the end: checked and withheld; X02 cap+1: `WITHHELD_NOTICE` (`reason=size`) in default mode, `LookalikeCopy` in raise mode; E01 a failure injected into `_healing_views`: `WITHHELD_NOTICE`, `reason=error`, the class name logged, no content, default mode; E02 the same in raise mode: `LookalikeCopy`; E03 `InputTooLarge` from `undo` (LK-UNFOLD) treated like E01.
**Guard (pb) rows, output unchanged against base (base outputs measured by the evidence runner and pinned in the fixtures file before the ticket is frozen):** F01 ``Approve **restart** of `web-01` in ~~old~~ demo?``; F02 placeholders already in the text (seeds not put back); F03 a 40-hex commit id and a 64-hex digest in code spans; F04 a Markdown table with bold and code; F05 `Tom &amp; Jerry &lt;ok&gt; &#169; 2026`; F06 `\x1b[32mok\x1b[0m done`; F07 `10.0.0.1` twice, the value entering the map through the redactor's IP pattern (exact fallback, no withhold, one coverage line); F08 ``run `make`test``; F09 `password=<S>` masked as today (also pins `c > e`); F10 `José Müller`; F11 a 3,000-character card; F12 an ARN with its 12-digit account id inside a longer stored value; F13 Greek and Cyrillic prose words; F15 `https://x.example/?a=1&b=2`; F17 2,000 characters of prose with `**`, `*`, `~~`; F19 `test_strict_mode_still_refuses`. **ow rows:** F14 (``` `<25 letters and digits>`/`<26 letters and digits>` ```: deleting the backticks joins two identifiers into a 52-character run the high-entropy pattern masks) and F16 (`password=hunter22&user=bob`).
**Model-path rows:** S1-S5: H01's input through `redact_untrusted`, `prepare_output`, `error_reason`, `safe_head`, `redact_value`: each returns the notice or masked text, never the key, never raises (no `on_residue` argument passed).
**Fail-before proof:** the new test files run on post-P1b main in a temporary worktree (`git worktree add <tmp> <base>`; copy only the new test files and `tests/fixtures`): every fb row must FAIL by assertion (never by an import error), every pb row must PASS, ow rows list their base result. If P1b's merged `textnorm` differs from V6/R1, BS-0 stops and the cloud session reruns the plan review. Raw output to `handover/evidence/P1d/fail-before.txt`, head SHA on line 1.

## Build steps before any code (BS); each has an output and a stop rule
- **BS-0** (a) list the 5 baseline failures; pin the P1b head, `TN_MIN`, the `scan_holds` error classes; **read `_scan_key` and the step function of `scan_holds` on merged P1b: record whether non-alphanumerics, case and look-alikes are already ignored/folded there; if `_scan_key` no longer keeps only letters and digits, STOP, back to review**; (b) read `undo`'s decode depth; (c) build the caller table by grep and complete it; (d) name the deny, expiry and approve functions and prove the approve path reaches the stored summary and the run map; (e) list every reader of a `redact_value` result for a hash (R9); (f) name the client-profile start function for the marker; (g) pick H37's pattern kind; (h) check `defaults.py` takes the constants; (i) pin exact line numbers for every `~` in this ticket.
- **BS-1** model-path false-withhold: a made-up corpus of 500 documents, tool results, logs (prose, JSON, stack traces, UUID-heavy logs, snake_case, base64, code), fixed seed, `tools/p1d_corpus.py`, through `redact_text`. Ceiling 0 withholds; report as "0 of 500 supports a rate below about 0.6 percent at 95 percent (rule of three)". Any withhold is listed and fixed or justified by a real hidden value. Also report the share of corpus documents above 10,000 and 30,000 characters.
- **BS-2** learning-pass false-learn per pattern on the same corpus plus hex digests, UUIDs, base64 blobs, 2,000 lines of code and prose with "Asia"/"akia"; the learning-only views ship only at false-learn 0 (R3). Back to review if AKIA/ASIA itself learns on ordinary text after the digit rule.
- **BS-3** card path: guard rows plus 500 made-up cards (same corpus tool, one run); ceiling 0 withholds on non-secret cards. Reported SEPARATELY: the false-withhold rate (ow rows excluded and listed), the false-abstain rate, and the H34 over-mask rate (200 made-up URLs and assignments; share of outputs where more than the secret value is masked).
- **BS-4** cost: `_healing_views` and `_finish` at 3,000, 30,000, 120,000 characters, with and without the fast path; set the constants by the commit rule above; latency target: p95 at 3,000 and 30,000 characters under `REDACT_BUDGET_S / 4`; also the defang move on the 31 pattern kinds (made-up sample each, raw text versus gated text, list every kind whose output differs). Back to review if normal traffic holds documents above the cap, or the bound cannot hold at 30000.

## Mutation plan (`tests/p1d_mutants.py`; one mutant per mechanism; a mutant that survives every row is declared equivalent with a written reason and the code it protects is deleted, or a combination row is added). Plain boundary checks (cap off by one, `c >= e`, `except` re-wrap, buttons kept) are ordinary assertions in the rows named, not mutants.
| mutant | planted change | killer; only-this-step row |
|---|---|---|
| M1 | `_finish` not called | H22; only this step: H22 |
| M2 | catch-all in `redact_text` removed | E01 |
| M3 | decode (a) removed | H10, C03; only this step: H10 (carrier) |
| M4 | tag/comment/ANSI/C1/ESC deletion (b1) removed | H11, H25, H29b; only this step: H25 (carrier; `1m` is letters/digits) |
| M5 | noise deletion (b2) and (d) removed | H37a-c (pattern kind other than AKIA/ASIA); equivalent for the residue test (R1); if H37 has no kind, deleted by the H37 rule |
| M6 | fold (c) removed | H21 (key not in the map, pattern needs fold); if BS-0 shows `scan_holds` already folds, H18/KV rows are NOT killers (R1) and H21 is the only one |
| M7 | squeezed learning removed | H33 |
| M8 | case-folded learning removed | H32 |
| M9 | digit rule / `[A-Z2-7]` class removed | `asia-prose`; only this step: `Asia 2024 Q3 revenue growth` |
| M10 | put-back without the two spaces | LK-JAMO-PB (a) Korean and (b) Tamil copied into the fixtures file (Korean V = 11 syllables `chr(0xAC00+i*21*28)` for i in 0..10, then U+B85C; Tamil V = `"Tamilv"` + U+0B92; the builder copies the exact inputs from the frozen note) |
| M11 | dropped-form test removed | a row that only it decides; if none exists after the run, the dropped-form test is deleted (stated decision) |
| M12 | `TextnormError` swallowed as "no hit" | E03 and `test_textnorm_error_withholds` (map value `"&#65018;" * 14600`, a text that does not contain it) |
| M13 | `ViewTooShort` fallback removed (value skipped) | boundary row `TN_MIN-1`, KV with `**` inside |
| M14 | fallback case-sensitive | boundary row, lower-case variant |
| M15 | fallback uses the squeezed view or drops the boundary rule | F13 and the `10.0.0.1` inside `210.0.0.12` row (NOT found) |
| M16 | seed entries put back | F02 |
| M17 | defang before redaction again | H26, `test_redactor_sees_undefanged_text` |
| M18 | `on_residue` default flipped to `"raise"` | S1-S5 |
| M19 | `LookalikeCopy` caught in `clean` and the text returned | H01 asserts `type(exc) is LookalikeCopy` |
| M20 | fast path takes texts with `%` | C08 KV twin; not killed by H10 (M3 is) |
| M21 | approve check removed | `test_withheld_request_cannot_be_approved_by_callback` |
| M22 | marker refusal removed from the client profile | `test_client_profile_refuses_without_marker` |
| M23 | judge/guardrail treats the notice as clean | `test_judge_refuses_on_notice` |
| M24 | `&` fix removed from SECRET | H34 (fb row) |
| M25 | unanchored AKIA/ASIA removed | H35 |
| M26 | joined pass reuses the first map | `test_joined_pass_fresh_map`: seed makes the first pass see the halves apart, `<S5><b></b><S22>`; the builder verifies it fails under the mutant |
Mutation runner: `tools/mutation_runner.py` if on the base, else a subprocess loop; every mutant restored in a `finally`; tree checked clean at the end. 26 mutants, one per mechanism; the builder may NOT merge two (a merge needs a written reason in the evidence). Required: M1-M10, M12, M13, M16, M17, M21, M22, M23; the rest follow the same rule.

## Evidence commands (EVIDENCE RUNNER, a separate agent; raw output to `handover/evidence/P1d/evidence-<n>.md`, head SHA on line 1; no cloud configuration in the environment)
```
uv run --all-extras --group test ruff check
uv run --all-extras --group test ruff format --check
uv run --all-extras --group test pytest -q -rs -m "not live and not perf" tests/test_p1d_rows.py tests/test_p1d_callers.py
uv run --all-extras --group test pytest -q -rs -m "not live and not perf"      # full, Python 3.12 and 3.13
bandit -ll -r src
python tests/p1d_mutants.py                       # alone
python tools/p1d_corpus.py --seed 1 --kind all    # BS-1, BS-2, BS-3, one run
python tools/p1d_cost.py                          # BS-4, alone, no other heavy job
```

## Build notes
BN-P1d-1 cite the base SHA; rebase on whatever main holds after P1b merges and rerun fail-before there. BN-P1d-2 correct `gate._rendered`'s docstring (an entity that decodes to a visible character inserts it; H33). BN-P1d-3 the learning pass is a private function; if the hook lint of `test_k5_round11.py` objects, exempt by (file, function) with an assertion that the result is discarded. BN-P1d-4 views outer, values inner. BN-P1d-5 P2d-2 promotes `_healing_views`/`_finish` (with an `extra=` argument) in its own ticket; the count rule has one copy. BN-P1d-6 test texts never say "staging", "dev" or "test" as a stage name (R449); F01 says "demo". BN-P1d-7 remove the `gate._rendered` entry from `vulture_whitelist.py`. BN-P1d-8 per-kind pre-mask only for a kind BS-4 lists. BN-P1d-9 operator review of withheld content is P1d-c (ledger 010), not this package. BN-P1d-10 the markdown-it-py comparison is not built (CUT, rung table).

## Owner-facing wording (plain words, checked against rule 14)
- The card and notice literals are in "Refusal behaviour".
- CHANGELOG, Upgrade steps: "Text shown to a person or sent to a model: a password, key or e-mail address written with formatting characters inside it (bold or italic markers, a terminal colour code, a backspace, an accent mark, look-alike letters, another letter case, a line break or one extra character such as `&` or `.`) is no longer shown. An approval card for such a request is posted once without buttons and cannot be approved; an operator log line says why. Text sent to a model is replaced by a short notice, and so is any text longer than a stated limit. E-mail addresses and internal host names in approval cards are now replaced by placeholders (before, they were shown with `[.]` in place of each dot). A password that contains `&` is now hidden up to the next space. Not covered: a secret that no pattern recognises and that is not already known (a plain password with no key word before it), very short values (below a stated length) that are only matched exactly, and keys written in lower case or split by an extra character that contain no digit from 2 to 7."
- For the owner's status message: "We found a gap where a key, password or e-mail address written with formatting characters inside it could be shown on an approval card or sent to the model. The fix is being built. Until it is merged, such values can be shown, so no real client data goes through this software."

## Ledger rows (`handover/ledger.md`; severity by the author, the lead confirms)
| id | package | severity | summary | status |
|---|---|---|---|---|
| BL-core-p1d-001 | P1d | BLOCKER | `clean` and `redact_text` show a key split by markers, escapes, controls, accents, look-alikes, and a known value in another case or split (H01-H25, S13) | OPEN |
| BL-core-p1d-002 | P1d | BLOCKER | `clean` never masks e-mail and internal hosts (defang before redaction, H26-H28) | OPEN |
| BL-core-p1d-003 | P1d | MAJOR | `SlackChannel._blocks` second `redact_text` outside the check; a withheld request must not be approvable (H30, H40) | OPEN |
| BL-core-p1d-004 | P1d | BLOCKER | the same split key passes every model producer (S1-S5, S13) | OPEN |
| BL-core-p1d-005 | P2d-2 | MAJOR | handed-out secret echoed in another case or with markers (S6 only; `tools._scrub_layers`, not on the `redact_text` path); same hard dependency as P1d: no client data before both land (ORDER 167 item 3) | OPEN |
| BL-core-p1d-006 | P1d-b | MAJOR | `k1b.redaction.sensitive` misses disguised key names (S11); same hard dependency | OPEN |
| BL-core-p1d-007 | P1d | MAJOR | SECRET value ends at `&` (H34) | OPEN |
| BL-core-p1d-008 | P1d | MAJOR | glued, dotted or `&`-inserted key passes (H33, H35) | OPEN |
| BL-core-p1d-009 | P1d-b | MINOR | `receiver.log_message` logs a callback URL unredacted (S16) | OPEN |
| BL-core-p1d-010 | P1d-c | MAJOR | no way for an operator to review the content of a withheld request (BN-P1d-9) | OPEN |
The lead's cilint row `BL-hadavin-sdk-cilint-001` (ORDER 146) is the parent of 001 to 004; the lead confirms the link.

## EGM steps, in order (R374, rule 13)
(1) brainstorm: not run, revision 1 is the brief; (2) draft: revision 4 (`egm:egm-draft`, 2026-11-09); (3) plan review round 4: fresh `egm-design`, `egm-implementation-readiness`, `egm-zoom-out`, given this ticket, the sibling report and the round-3 resolve only; (4) `egm:egm-resolve`; repeat (3)-(4) until a round finds no blocker or major (redaction path, no cap); (5) build after P1b merges; (6) EVIDENCE RUNNER; (7) result review by `egm:*` reviewers; (8) resolve, repeat until clean; (9) `egm:egm-drift-report`.

## Slot needs (rule 17)
Build iterations: only the new test files and the clean-related files (1-2 minutes). Final head, once: full suite on 3.12 and 3.13 (2 slots), the 26-mutant run (1 slot, alone with at most the other-Python suite), BS timing (1 slot, ALONE). Real clock: build 10-14 hours, evidence 1-2 hours, each review round 1-2 hours. P2d-2 and P5c also read `channel.py` (a rebase conflict, no slot conflict). P1d is first in the build queue after the P1b fix batch and blocks the pilot merge of P1b/PR 63.

## OPEN QUESTIONS for the lead (only what ORDER 165, 166 and 167 did not answer)
1. **Document size floor (NEEDS-LEAD 1):** the model path withholds any text above `P1D_MAX_TEXT_CHARS`; the ticket starts at 30000 (V9: 2.69 s per call at 30000 before the fast path) and BS-4 may raise but never lower it. Is a 30000-character floor acceptable, or do you have real document sizes?
2. **Hand-over rows under `ledger_check` (NEEDS-LEAD 2):** may rows 005 (S6, P2d-2), 006, 009 (P1d-b) and 010 (P1d-c) stand as OPEN hand-over rows with a named owner package and the hard-dependency note without blocking "Done" for P1d, or must they be closed or reclassified?
3. If BS-2 shows the squeezed/case-folded learning cannot reach false-learn 0, H31-H33 and H35 cannot be fixed as ORDER 165 item 4 wants: does the lead then accept "best effort, documented" for those four rows, or hold P1d?

## UNVERIFIED (not read or run by me in revision 4)
Every V number; the 5 baseline failures' cause; `TN_MIN`; whether `scan_holds` folds look-alikes by itself; `undo`'s decode depth; the existing deny, expiry and approve functions; the caller table beyond the sibling report; H29's base result; H37's pattern kind; the effect of the digit rule and the fast path; the BS results; the standard section numbers; Python 3.13; whether `vulture_whitelist.py` and `tools/mutation_runner.py` have reached the base; the Korean and Tamil literals (copied by the builder from the frozen note); `textnorm._scan_key` was read once on the P1b fix-branch head and may change.

## Rules cited
R233 (redaction fails closed), R337 (class-level fixes), R363 (no single dependency), R374 (EGM order), R447, R448 (CODE LAST, rung table), R449 (stage names), R450 (research and licence gate); studio preamble rules 3, 5, 6, 7, 12, 13, 14, 17, 19, 20, 21.

## Revision log
Rev 1 (2026-11-07): author draft without the skill. Rev 2 (2026-11-09): from round-1 reviews and ORDER 165. Rev 3 (2026-11-09): from round-2 reviews and ORDER 166 (no slices, fixed-order pipeline, private helpers, model path never raises, caller table, existing-route operator decision, short values, digit rule, S11/S16 to P1d-b, fixtures file, mutants with only-this-step rows). Rev 4 (2026-11-09): from the round-3 reviews (design 1B/9M, readiness 3B/15M, zoom-out 6M), `round3-resolve.md` G1-G22 and ORDER 167: `scan_holds` scan key read (R1) so the residue test needs only letter/digit-carrying steps and marker deletion is learning-only; one operator design (no result object, no field; approve path re-checks); pseudocode for the pipeline, learning pass, residue test and put-back count; two constants with start values and a commit rule, view count, clock and alert constants dropped; catch-all and one exception class in raise mode; judge, guardrail, evals and grounded callers in the table; S13 into P1d, S6 to P2d-2 with the hard dependency; `[A-Z2-7]` digit rule with best-effort label; case-insensitive exact fallback with a boundary regex; marker `P1D_APPLIED` plus client-profile refusal; fast path; returned bytes checked; 26 mutants one per mechanism (was 30); BS-5 and the markdown library comparison removed; history moved here.
