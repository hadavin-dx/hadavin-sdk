<!-- full hand-back report of sub-agent ac9534ea, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PLAN review (zoom-out, REVIEW mode) of D-017, PR 77, before round 8. Read-only; nothing was run. Every behaviour below is traced by reading, not executed.

## Recommendation: a named mix, "C-small first, then B as a revert-and-complete"

Do not run round 8 on the round-7 head. Instead:
- First, a small pull request off main that strips controls and escape sequences once, at the choke point, before anything else reads the text.
- Then PR 77 goes back to its own head 76adadb, rebased on that, plus a small delta.

D-017's option B is right in direction, but wrong as worded in three ways:
- It is not "one" canonical text.
- It does not need a position map for controls and escape sequences.
- It leaves the tab question undecided.

Three strongest reasons:

1. **Main leaks today, and that fix does not depend on the look-alike feature.**
   - `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/guard/redact.py:825-838,920` strips escape sequences inside `find`, after `neutralise`, and puts a space where one stood between word characters. So `AKIA` + `ESC[0m` + `IOSFODNN7EXAMPLE` comes out with a space in it, unmasked.
   - `canonical` on main (`runmap.py:276-282`) removes only category Cf.
   - PR 77's diff against main is about 21,000 lines (textnorm, look-alike data, fold scan) and does not touch `tools.py`, `gate.py` or `channel.py`. Holding the leak fix behind that feature is the wrong coupling.

2. **B is the completion of code that already exists, not a replacement.**
   - Main has `canonical`, `_canonical_view` (offsets) and `replace_canonical`.
   - The PR head 76adadb has `_aligned_fold` (folded text plus `where` offsets plus look-alike flags), `_mask_in_place`, `_folded_line` and its withhold fallback.
   - What gets deleted is only the layer from rounds 5 to 7, which never reached the pull-request branch. improve-before-replace is satisfied; the written reason is the round-7 evidence.

3. **Most round-7 findings share one root: the redactor changes the text after `neutralise`, and three functions each parse escape sequences differently.**
   - Removing controls and sequences from the text itself, once, before `neutralise`, the scrub and the patterns, makes "raw" and "canonical" the same string for that class.
   - B1 and B2, the separator leaks, the tab over-masking and the private-module dependency then disappear by construction, not by a 25-item list.

## Findings on D-017 as written

- **Blocker: "ONE canonical text" cannot hold and would be a false claim again.**
  - Still needed: the iota spelling of the fold, the decode views in `runmap._views`, and at least one extra reading for escape sequences.
  - The ticket must state the exact number of readings and when each runs. Round 7's "ONE reading" was in fact up to 8.
- **Blocker: the tab rule is not decided, and it is the root of rounds 5 to 7.**
  - A canonical text cannot both delete and keep a tab.
  - This needs the owner's yes, because round 5 logged tab-inside-key as a leak (w5-s03).
- **Major: "existing patterns run unchanged, linear cost" undersells the mapping.**
  - Patterns run as a chain and depend on earlier placeholders (`<BANKCODE_n>`, values that are only placeholders).
  - The mapping back is therefore `_mask_in_place` with its round loop, journal and withhold fallback. Say that it is reused, not re-invented.
- **Major: the D-016 direction "one table imported by the approval gate" over-unifies.**
  - The gate models a browser and URL parser; its own comments keep ZWJ and ZWNJ on purpose.
  - Keep the gate's own set, with a test that it contains the control class.
  - Then round 8 does not edit `gate.py`, and Q8b need not wait on PR 77.

## Question 1: the hard cases, with the rule for each

Proposed contract: hidden items never help. The output is masked at least as well as the same text as a terminal or reader renders it.

**Controls and escape sequences.** Class H1 is the C0 and C1 controls (except tab, LF, CR and the white-space-like ones) plus ECMA-48 sequences.
- They are removed from the text itself at the choke point. No position map is needed.

**Tab inside a secret versus tab between cells.**
- Recommended rule: white space is white space. Tab, VT, FF, U+001C to U+001F, NEL, U+2028 and U+2029 read as a space; LF and CR stay line ends.
- Over-masks: nothing new. The six-cell pod row and the digit rows stay as they are.
- Misses: a key or token with a tab inside, exactly as a space or new line inside one is missed today (CHANGELOG lines 12 and 20 already say so).
- Fixes the separator cases: `Bearer` + tab + token and `mysql` + tab + `-p` match again.
- Alternative if the owner refuses: one extra reading with those controls deleted, for vendor-prefix and fixed-alphabet kinds only (never HIGHENTROPY, PHONE, ACCOUNTID or key=value). It can over-mask a cell that follows a cell starting with a vendor prefix.

**Escape sequence whose final byte may be a letter of the secret.**
- Parse as ECMA-48 and strip. The letter is then absent from the output, so nothing is revealed that the rendered text lacks.
- Variable-length kinds still match the remainder. Fixed-length kinds (UUID, card) leave a visible partial value; state this.
- Keep one second reading (introducer and parameters removed, final byte kept) as a whole-text view in `runmap._views`, and in the handed-out-secret scrub, where the secret is known.
- Keep main's "sequence between two word characters may be a space" as one more view.
- Not covered: one item glued beside a token and another inside the same token. The same text without the items is also unmasked on main.

**Marks in non-Latin text.**
- Drop a mark for matching only when its base character is ASCII (or folds to ASCII).
- A Devanagari word then has no hidden item and needs no extra reading. That is what should remove the Hindi cost.
- Misses: a visible foreign letter inserted in a key; an extra mark in a non-Latin known value.

**Line break inside a key.** A line end, not masked, as stated today.

**Placeholders already in the text.**
- `neutralise` runs on the stripped text, so `find` no longer changes text after it.
- The last check reads raw output as well as `canonical(out)`.
- The sentinel scheme is not needed.

**Mapping back.**
- Only for the ignorable class (zero-width, variation selectors, marks on an ASCII base) and the fold.
- Replace the original span from the first to the last matched character, hidden characters inside included; items at the edges stay. `replace_canonical` and `_mask_in_place` do this now.

**Cost at 262,144 characters.**
- The strip is one linear pass. Plain lines cost as today (0.4 s stated).
- Hindi should fall from 6.1 s towards the one-reading cost. I did not measure it.

## Question 2: keep, change, delete

**Keep:**
- `canonical`, `_canonical_view`, `replace_canonical`
- `_aligned_fold`, `_mask_in_place`, `_apply_claims`, `_register_written`, `_folded_line`, `_fold_scan`
- `_LINES`, `_view_covers`, `_refuse_forgery`
- `is_hidden` and the ignorable table
- the thread-time deadline and clock checks

**Change:**
- `canonical`: white-space-like to space; the two wide dots mapped inside it.
- `_ANSI` and `strip_ansi`: one real parser, called before `neutralise`, not in `find`.
- `_view_specs`: mark-on-ASCII rule instead of marks-dropped views.
- `tools._sanitise`: delete NUL like `_clean`.
- `_refuse_forgery`: also read raw output.

**Delete:**
- `GAP`, `_gap_spans`, the `read` parameter
- `_reads_gap`, `_tolerate`, `_tolerant`, `_tolerant_patterns`, `_patterns_for`
- `_JOIN_CTLS`, `JOIN_RE`, `_JOIN_RUN`
- the keep-one-letter branch of `strip_ansi`
- the dots view and the marks-dropped view in `runmap._views`
- the second `_HIDDEN_ASCII`

## Question 3: what happens to the round-7 findings

**Fall away:**
- B1 and B2
- codebase M1 and M2
- most of design M4
- the private-module and rewritten-pattern-timing items
- the mutant findings about gap code
- the false CHANGELOG sentences (rewritten)

**Remain whatever the design:**
- escape-sequence grammar coverage
- the scrub's two readings
- the dots
- cost measurement
- the tests

**Separate tickets, each with its reason:**
- F7, scrub compares in two domains. Different bug class (encoding of the known secret), present on main, same file; schedule it straight after.
- Design M6, the cover rule. It is the decode-view mechanism on main, and "which text wins" needs its own decision.
- Vendor key glued to a word in plain ASCII. A pattern weakness, not a hidden-item one.
- F10 and fragment map entries, as the reviewer said.

**Do not carry over:** the removal of the mutation runner's `occurrences` guard.

## Question 4: option C

- C alone is not better. PR 77 stays open, and PR 74 still waits.
- C-small first is better, and it is low risk if it does not strip the ignorable characters from the output. They must only be ignored for matching, through main's existing canonical view; stripping them breaks Persian text and emoji.

## Risks of this recommendation, one input each

1. **Honest data changed by the strip.** nroff overstrike `N`, backspace, `N` becomes `NN`. An unterminated `ESC ]` blanks the rest of its line.
2. **Tab rule.** `Bearer ` + 8 letters + tab + 10 more: nothing masked. Needs the owner's yes.
3. **Mixed glue and cut.** `user` + `ESC[0m` + `AKIAIOS` + `ESC[0m` + `FODNN7EXAMPLE` stays unmasked. A result reviewer will call it a leak unless the contract is in the ticket.
4. **Fixed-length remainder.** A UUID with `ESC[` after its tenth character loses the following digits and shows the rest.
5. **Rebase.** PR 77 rewrites `redact.py` and `runmap.py`; rebasing 76adadb onto the small fix will conflict.
6. **76adadb itself may not be clean.** I could not tell from the material whether it is.

## Proposed scope, as a list for the ticket author

1. **Owner decision:** the tab rule and the "not worse than rendered" contract, with the not-promised list.
2. **PR H, off main.** A leaf module with one class table: removed; space-like; line end; ignorable-for-matching.
   - An ECMA-48 parser covering CSI, the nF, Fp, Fs and Fe escapes, the OSC, DCS, SOS, PM and APC payloads, the C1 forms, and a C0 control inside a CSI.
   - Unterminated strings are bounded to the line.
3. **PR H:** strip in `redact_text` before `neutralise`, in `tools` before the scrub, and in `safe_head` (which also collapses line ends). Remove the strip from `find`.
4. **PR H:** `canonical` extended; two extra views (sequence as space; final byte kept); scrub over the same readings; raw last check; NUL deleted on the tool path.
5. **PR H:** the test set under Question 5; prove fail-before on main.
6. **PR 77:** reset work to 76adadb, rebase on PR H, apply the mark-on-ASCII rule, keep `_apply_claims` and the clock checks, rewrite the CHANGELOG entry with the exact number of readings.
7. **Measure** the six cost shapes at the cap; state a size that passes with a margin of two.
8. **Open the separate tickets** above with dates.

## Question 5: test design

- **Oracle that shares no code with the implementation.**
  - Ignorable ranges generated from a pinned `DerivedCoreProperties.txt`.
  - A hand-written escape state machine in the tests.
  - Leak check on the oracle-rendered output.
- **Generator:** kind (prefix key, JWT, UUID, key=value, bearer, e-mail, command flag, PEM, handed-out secret) x item (one per class and per escape family) x position (inside key name, at separator, value start, inside value, value end, line end, before a placeholder-shaped literal).
  - Exhaustive for singles; seeded pairs.
  - Every case counted, with a minimum count asserted.
- **Each case carries an expected class** from the contract table: masked, or not promised with the reason.
- **Forgery invariants** are asserted on every output, on raw text.
- **Regression data file:** every reproduced input of rounds 5 to 7, sweep F1 to F4, the six main leaks and the two forgery inputs.
- **Clean corpus** (tab tables, logs, JSON, coloured output, Hindi, Persian, emoji): output identical to input, and the placeholder count not above main's.
- **Time at the cap,** with a doubling check.

## Question 6: standards and libraries

- **UAX #44 Default_Ignorable_Code_Point:** not in Python's `unicodedata`. Vendor the data file and generate, as `tools/gen_confusables.py` already does for UTS #39; this replaces the hand-typed 17 ranges.
- **ECMA-48 sections 5.3, 5.4 and 5.6, and ECMA-35** for the nF, Fp and Fs escapes. The Williams DEC parser diagram is the usual reference for controls inside sequences and for aborts.
- **UTS #46:** only the three dots.
- **White space:** `str.isspace`, as the fold already uses.
- **Libraries:** the `regex` package has the property but adds a dependency on the redaction path. A terminal library could serve as a test-only oracle after a licence check. I could not research either live.

## What should not be built

- pattern rewriting or any use of `re._parser`
- a gap stand-in character
- per-line withholding on a spent budget (measure first)
- sentinel-carried placeholders
- a table shared with the approval gate
- a tab-deleted reading for all kinds
- unifying all thirteen "hidden" definitions

## Not checked

- No code, test or timing was run.
- 76adadb was not read directly; its contents are inferred from `DIFF-vs-PR-head-76adadb.patch` function headers.
- Read in part only: the test files (names plus `test_redact_hidden_forms.py` lines 50-260), `redact_mutants.py`, `gate.py` (lines 110-360), `tools.py` (lines 690-1010), the CHANGELOG (lines 1-24), the two other diff patches.
- Not read: `k1b/redaction.py`, `SWEEP-findings-summary.md`, `defaults.py` beyond three constants, callers outside the snapshot.
- The Default_Ignorable list and the UTS #39 and ECMA section references are from memory.
- The Hindi cost estimate and all cost claims are unmeasured.

## Files read

- `/home/user/hadavin-sdk/handover/AUTONOMOUS-DECISIONS.md` (D-016, D-017)
- `/home/user/build/snap/p77-97fd202/src/hadavin_sdk/guard/redact.py`, `runmap.py`, `textnorm.py` (in full)
- `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/guard/redact.py` (lines 814-925) and `runmap.py` (lines 270-531)
- `/home/user/build/reports-raw/PR77-round7-design-full.md` and `PR77-round7-codebase-full.md`
- `/home/user/hadavin-sdk/handover/reviews/PR77/round7-design.md` and `round7-codebase.md`
- the three round-6 reports, `LEDGER-rows-w5-w6.txt`, `SWEEP-findings-full.md`
- `/home/user/hadavin-sdk/CLAUDE.md` and the six named rule files
- `/root/.claude/plugins/cache/egm/egm/0.1.1/agents/zoom_out.md` and `resources/document_standards/zoom-out-standard.md`
