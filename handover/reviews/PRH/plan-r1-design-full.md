<!-- full hand-back report of sub-agent a6a4d892, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

VERDICT: NOT READY. Blocker 1, Major 7, Minor 12.

Method: I read the ticket in full, the round-8 zoom-out report, D-018 in AUTONOMOUS-DECISIONS.md, CLAUDE.md, the seven rule files, the first 30 lines of Q8b, and the main snapshot files you named. I also read agent_loop.py, evidence.py, extract.py, k1b/loop.py, judge.py, slack_channel.py and defaults.py. I ran nothing; every behaviour below is traced by reading the code. The main snapshot at /home/user/build/q8a2-dryrun/main-2a8c2aa has `src/` only, so claims that rest on tests (fact 17, case 790, T7) are unchecked.

## 1. Findings

### B1. BLOCKER. Section "Read first" item 3 and open question 8: case 790 is an open leak on the card path
- The author's own prototype leaks a 12-character piece of a secret on `channel.clean` and on the Slack producer. These are the only two paths where the escaping step is the gate's `_neutralise` (`withhold_commands(sanitise_text(...))`) and not `neutralise_untrusted`.
- A plan review cannot call the design achievable on the approval card while a prototype of that design leaks there. The cause is unknown and the ticket gives "no default".
- If the builder finds the cause is in the design, the plan returns to review after a build. That is the round-9 pattern.
- Likely suspects:
  - The gate's step rewrites the joined and spaced readings differently (`_INVISIBLE_IN_NAME` deletion, `_break_runs` inserts U+200B, entity and defang rules). The value found on the joined reading then cannot be located in the spaced one by the W2 step 5 gap pattern.
  - `clean` computes `_seeded(text)` and `_TAGS.sub` on the text before the strip (see M5).
- Smallest change: the author diagnoses case 790 before READY. The prototype and the failing case are in hand, and it is cheaper than a build round.
- If that is impossible, the ticket must give the exact pytest command, the seed and the failing output text.
- It must also say what the builder does for each outcome. "Stops and reports" has no recipient and no consequence for the rest of the PR.
- This falls under fix-dont-defer-be-honest rule 1: a failing check on a security path.

### M1. MAJOR. Section 4.2 W2 `_redact_stripped` step 4: the 256 fallback gives up promise 2 and is attacker-triggerable
- The count is every placeholder standing in `found.text`, not the number of values cut by hidden items.
- Any text with more than 256 distinct masked values and one colour code inside one word makes the output the joined result (hidden items deleted, no glue space).
- A big log with 300 IP addresses is ordinary. An attacker can pad a tool result with 257 distinct e-mail addresses plus one `x` + ESC `[0m` + `y`.
- Input: `"user" + "\x07" + KEY` plus that padding.
  - Main masks the key (BEL is a boundary).
  - The joined result reads `userAKIA...`, and the key is not masked.
- Main's own precedent for the same limit, `_decoded_masks` (runmap.py:441-442), refuses with `InputTooLarge` and never skips. This is a case of the "promise given up" the ticket mentions but must not.
- Smallest change: on more than 256, raise `InputTooLarge` as main does. Or count only the values that need the gap. Or apply `redact(spaced)` after `found`. Add a T9 shape with more than 256 values and one hidden item in a word.

### M2. MAJOR. Section 4.2 W2 and section 4.1 last paragraph: a hidden item produced by decoding that cuts an encoding token leaks
- `undo` (runmap.py:141-172) decodes to a fixed point. The ticket then runs `strip` once, after the decode.
- Input: `"id %4%1b[0m1KIAIOSFODNN7EXAMPLE"`.
  - `undo` turns `%1b` into ESC. `%4` ESC `[0m1KIA` stays undecoded.
  - `strip` then yields `%41KIAIOSFODNN7EXAMPLE`. Nothing decodes it again, and the AKIA pattern does not match `%41KIA`.
  - Reading 0 is unchanged text. The mapping does not change, so no reading replaces the output, and the key stays in an encoded spelling.
- Main promises `%41KIA...` in `redact_layered` and in the layers-in-any-order docstring. The "not promised" list only excludes handed-out secrets in encoded spellings (section 3, bullet "Hidden items inside an encoded spelling").
- Same shape for `\x1b[0m` spelled as text inside a `%XX` or entity token.
- Smallest change: put `strip` inside the `undo` round, or loop undo then strip to a fixed point. Add layers to the test axes (M7). Or add the case to "not promised" with a dated next step.

### M3. MAJOR. Section 3 "Words" and section 4.1: the glue rule for runs of removed items is undefined, and promise 2 depends on it
- "Where a removed item stood between two word characters one space is left" reads per item.
- Input `"user" + BEL + BEL + KEY`:
  - Main masks it, because BEL is a boundary.
  - Per item, neither BEL sits between two word characters. No space is left, the key is glued to `user`, and it is not masked.
  - The same applies to `user` + ESC `[0m` + ESC `[1m` + KEY.
  - Main evaluates each match on original neighbours, so its second sequence sees `m` and `A` and glues.
- Smallest change: define the glue per maximal run of removed items. State what happens when a run is mixed with kept characters. Add runs of two or more, mixed with space-like and ignorable items, to T1 and add a mutant for it.

### M4. MAJOR. Section 4.2 W5 and T4: the map clean-up removes entries that protect later texts, and T4 requires it
- Rule: "an entry added during this call whose placeholder is not in the returned text is dropped"; T4 also demands that no added entry's value is a proper part of another.
- Scenario:
  - Pass one masks `hunter2` (entry A).
  - A later reading masks the longer `hunter2;rest` (entry B) and replaces the output.
  - W5 drops A. A later text, `the password hunter2 failed`, was masked on main by the sweep of known values. After W5 it is not.
- `k1b/redaction.py:172-195` builds one map in pass 1 and relies on it being complete in pass 2. Dropping A is a regression on exactly that path.
- W5 is also a different bug class (map hygiene) from hidden items.
- Smallest change: split W5 out into its own ticket with a test "a value a call saw stays registered for the run". Or drop only the entries whose value is covered by a kept entry and also keep the shorter one in a non-output set.

### M5. MAJOR. Sections 2.1 and 3 promise 3, W4, T3 last sentence: the approval card forges placeholders and the contract is silent
- `channel.clean` (channel.py:28) and `slack_channel._blocks` (:75-81) seed the map before the choke point reads the text. The seeding sees only plain `<IPV4_1>`.
- Input `clean("<" + ESC + "[0mIPV4_1> and 10.0.0.5")`:
  - The strip yields a genuine-shaped `<IPV4_1>`, which the gate's `_LT` keeps. It was never seeded, so the redactor issues `<IPV4_1>` to the real address.
  - The card shows two identical placeholders for two things.
  - Main behaves the same, so this is not a regression. But the ticket's title and T3 claim "hidden spelling equals joined spelling" for callers without the escaping step. The plain spelling is seeded and renumbered, so the hidden spelling output differs.
- W4 forbids editing channel.py and slack_channel.py, so the builder cannot fix it where it lives.
- Smallest change: either seed inside `redact_text` after the strip for non-untrusted callers, or write the card forgery into "not promised" and narrow the T3 sentence to name the paths it covers.

### M6. MAJOR. Sections 2.1 and 4.2 W2, plus honest-data lists: model-written text is mutated, and grounding changes
- Tool-call arguments and proposal inputs go through `redact_value` (agent_loop.py:534; evidence.py:191) and are later restored for the executor (`inputs_view`, agent_loop.py:280-295).
- After PR H the executor receives text with BEL, ESC, C1 characters and NUL removed and VT, FF and U+2028 turned into spaces. Example: a "write note" action with a form feed in its argument.
- The ticket's honest-data list (overstrike, C1 in words) and the CHANGELOG rules name only tool results and documents.
- `canonical` now also drops non-Cf ignorables. `grounded` (evidence.py:151) rejects any identifier where `canonical(value) != value`. `contains` (:87-88) compares canonical forms on both sides.
  - Effect: an identifier with U+FE0F is now refused, and an evidence text `po` + U+034F + `d-1` now grounds `pod-1`.
  - That is a security decision (grounding for actions) changed without a line in the contract.
- `ToolOutput.sha256` (tools.py:1197) hashes the `_sanitise` output. W3's NUL change alters the digest for NUL texts.
- Smallest change: add to section 3 and the CHANGELOG that model-written inputs reach the executor stripped. Add tests in the evidence tests for grounding with each non-Cf ignorable. Say what happens to the digest.

### M7. MAJOR. Section 5 T1 axes: the generator is exhaustive only over axes that omit where the ticket's own gaps are, so a round 9 is plausible
- Missing axes:
  - Encoding layers around the item (`%1b`, `\x1b`, `\033`, `\u001b`, `&#27;`) and around the key.
  - NFKC carriers (fullwidth letters of the key plus an item).
  - Model-written paths without the escaping step, and `redact_many`.
  - Hidden items at the size-cap seam.
  - Runs of two or more items.
- M2 and M3 are in the gaps. The `%1b` case exists only as one regression entry (L11).
- Smallest change: add a layers axis (item spelled five ways, key spelled plain and percent-encoded) and a run-length axis (1, 2, 3 of mixed families).
- The "no shared code" claim is also too strong. The expected class "masked" is computed by running the implementation's own `redact()` on the oracle's joined reading. That is acceptable but must be worded as "shares the redactor's patterns, nothing else".
- The "14,132 runs, 0 breaks" figures come from the author's own reader and oracle (as the ticket says in item 2). Do not cite them as evidence for the design.

## 2. Claims about main checked against the code

Verified correct:
1. `redact_text` step lines :486, :488, :489-490, :491-492, :494, :512-515, :517-518, :519, :524-525.
2. `_ANSI` :820-822; `strip_ansi` :825-838; `find` :919-923; call sites :877, :920, :1254.
3. Table rows for `strip_ansi` on main:
   - OSC never ended eats the following lines (`[^\x07\x1b]*` crosses line feeds).
   - CSI with a BEL inside is not matched.
   - DCS, SOS, PM, APC lose only the two-character opener.
   - The C1 OSC introducer is not recognised.
   - ESC `M` is removed.
4. `canonical` removes Cf only (:276-282), and U+3164 becomes U+1160 under NFKC.
5. `_clean` :395-398 deletes NUL. `_sanitise` :730-732 turns NUL into U+FFFD. `prepare_output` order :951/:959/:967. `error_reason` :1002/:1005. Fact L8 (tool leaks, error masks) is consistent with this.
6. Producer rows:
   - judge.py:71 and bedrock_guardrail.py:98 have no escaping step.
   - tick.py:292 replaces only the line feed.
   - injection.py:96, extract.py:58, k1b/loop.py:187 and :194 are as listed.
   - agent_loop.py:412 and :580, evals.py:63, k1b/redaction.py:188 are as listed.
   - channel.py:29 and :36, slack_channel.py:81 are as listed.
7. gate.py `_CONTROL_CHARS` :125-136 holds C0 except tab and line feed (carriage return included), and U+007F-009F. The T8 claim is therefore true: every member of `REMOVED` and `SPACE_LIKE` is in the gate's set except U+2028 and U+2029. `strip_controls` :162, `normalise` :200-205, `_views` :212-220, `_ANSI_AS_TEXT` :197 and the `strip_ansi` import at :74 are as listed.
8. `MAX_DECODED_MASKS` 256 at :423; `defaults.REDACT_BUDGET_S` 6.0; `MAX_REDACT_CHARS` is the document size.
9. `canonical` is also used in evidence.py :57, :87, :88, :151.
10. "Reading counts": 2 + 6 x 2 = 14 is correct arithmetic.

Wrong or imprecise:
- Section 2.3 table, OSC row. "Ended by U+009C: removed whole" is wrong on main. `_ANSI` knows only BEL and ESC backslash as ends, so an OSC closed by U+009C also eats the following text up to the next BEL or ESC, or the end of the text.
- Section 2.5: the six forged inputs are F1a, F1b, F1c, F1d, F1e, F1g. There is no F1f. Say so or renumber.
- Section 2.1, answer to lead point 2: "the six callers without escaping that feed a model". The validation error at extract.py:62 is fed straight back to the model by `safe_head`. The grep claim "no frame" still holds, but the table should say that row feeds a model.

## 3. Departures from D-018 and the zoom-out review

- **"Find on joined, mask on spaced": right in direction, but underspecified and over-built.**
  - The zoom-out review kept main's glue space as "one more view". With a view, a joined view that finds a key would replace the output and lose boundaries (G3). The ticket's two-step is the correct fix.
  - Conditions: M1 (the fallback), M3 (runs) and the short-value over-masking below.
  - Step 5 replaces every occurrence of a found value in the spaced text. The sweep has length thresholds for a reason: a registered secret of 4 or more characters is replaced everywhere, 3 only as a whole word (Q8b line 11). The quoted-assignment rule takes values of 1 to 256 characters. A text with `secret="a"` plus one hidden item in a word has every `a` replaced.
  - Smallest change: reuse the redactor's own sweep and its thresholds, or apply the same length rules.
- **Keeping `strip_ansi` in `find`: acceptable.** "Improve, do not replace", and the departure is stated.
  - T7 proves only calls made through `runmap.redact`. `find` is also reached by `sweep` and `redact_many`, and a stored map from an older run may hold an original with ESC.
  - A one-line test with a stand-in on `_Redactor.find` is needed.
- **No change to judge, vendor screen or `safe_head`: right.**
  - Collapsing line ends changes what k1b stores (`out.raw`), and escaping placeholders in the judge would rewrite genuine ones. Both are different classes and are stated as such.
  - The stored raw reply loses control characters. Say so in the honest-data list.
- **Backslash-plus-line-break in scope: weakest fit, so split it out.**
  - It is visible text, not a hidden item.
  - It is inconsistent with the contract: a key cut by a tab or a plain line break is "not promised", while one cut by backslash-newline is masked.
  - It turns every multi-line shell result into a two-pass text, and the stated over-masking is a quality regression.
  - The ticket already has the removal path (mutants 18 and 19). Move it to its own small ticket on the same gap pattern, with a dated row, unless the lead decides otherwise.
- **The rejection of "as a terminal shows it": right** (backspace overstrike makes the oracle wrong), and honestly argued.

## 4. The unresolved failing test (focus 4)

Making case 790 the builder's first job and a blocker is safe only if the ticket says what happens on each outcome (B1). As written it also contradicts "Status: nothing is built" plus "plan reviewers judge before any build". A failing guard test under the prototype is evidence about the design, not a build chore.

## 5. Scope

Smallest honest scope:
- `hidden.py`, `strip_ansi` delegation, the W2 wiring, W3 scrub, and the tests for those.
- Split out W5 (M4). Split out line continuation (above). Keep the Unicode table as is.

Missing from scope:
- Model-written arguments and grounding (M6).
- The card seeding (M5).
- `_first_decoded` (tools.py:786-791). After the change it returns `""` for a removed control, and `"" in "&\\%"` is true, so the skip guard at :867 does not skip. Every such position now costs a `_decoded_clean` call over the tail. Add a test and a bound.

Q8b overlap:
- The two shared files (ci.yml and CHANGELOG.md) are additive.
- The ticket understates the coupling. Q8b's own coupling list (lines 13-14 of its ticket) says `canonical` and `strip_ansi` decide which spellings its N4 and ESC rows mask. PR H changes both, and Q8b's builder started in parallel (D-018). Q8b's merge-order sentence ("PR77 lands first", line 9) is now stale.
- Name the instruction for the Q8b builder in section 6: rerun the XPASS and fail-on-base procedure after PR H, and which files rebase.
- Gate behaviour changes through `strip_ansi`. DCS, SOS, PM and APC payloads on the card are now deleted instead of shown, and the approver sees less than the sender wrote. This is a deliberate default of open question 2 that no gate test covers. It needs a one-line statement and a test (Minor).

## 6. Test design and acceptance

Acceptance items not checkable by a command (Minor):
- Item 3: "skip list is the same as main's" has no diff command.
- Item 4: "alone on the machine" is not a command.
- Item 5: gitleaks "if not installed, say so" is not pass or fail.
- Item 8: the heredoc has no body.
- Item 9: only raw numbers, with no pass line. The 1.25 times and 3.0 s limits live in T9, but T9 on the branch has no source for "main's CPU time in the same session" unless a fixture is recorded.
- Item 11: "the evidence runner's own script" is not in the ticket.
- Item 12: "check by reading".
- Python 3.12 may not be installable offline. Say how it is obtained.

## 7. Cost and dependency

- Dependency: stdlib only. The Unicode file has an alternative source with a named trigger, which satisfies no-single-dependency.
- The licence line is "from memory". A file generated from perl needs the right notice. Name the check date.
- Ladder rung 3 (libraries) is unresearched because there is no network. State a dated next step per rule fix-dont-defer 2(c).
- Cost limits are plausible and honestly labelled as rough. Gaps:
  - W2 step 5 (up to 256 gap substitutions over 262,144 characters) is never measured.
  - The hostile shape in T9 must include M1's more-than-256-values shape.
  - Hindi and Persian are not under the 1.25 times limit. The extra `is_ignorable` call per character in the three canonical views may cost more than that.
  - The time budget is checked only between readings, so one reading with two passes plus 256 substitutions can overrun by more than "one reading".

## 8. Wording (wording-clear-for-everyone)

- "Reading" has two meanings: section 3 "Number of readings" says a reading is one pass of all patterns, while "joined reading" and "spaced reading" are versions of the text. The ticket then counts 14 "readings" that are passes. Use "pass" for the first and keep "reading" for the second.
- C0, C1, CSI, ST, CAN, SUB, DEL, nF, Fp, Fe, Fs appear in section 4.1 without a plain explanation. Section 1 explains only "escape sequence".
- "Fail to the safe side", "found", "joined" and "gap" are internal.
- The CHANGELOG wording rules (section 6) are good. They should also forbid "reading" without the clarified meaning.

## 9. Not checked

- No tests, scripts or prototype outputs were run or opened (`/home/user/build/prh-author/scratch` not read). Tests are absent from the main snapshot.
- Everything the ticket marks "from memory" (ECMA-48, ECMA-35, Unicode derivation, CWE, licence).
- Whether Python 3.12 and 3.13 agree on the Cf set the table equality test relies on.
- I did not read AUTONOMOUS-LOG, sweep F1-F9, the round-7 reports, RESULTS.md, `gate._clean_line` and below, or Q8b past line 30.
- I did not trace `withhold_commands` or `sanitise_text`, so the case 790 suspects are hypotheses.
