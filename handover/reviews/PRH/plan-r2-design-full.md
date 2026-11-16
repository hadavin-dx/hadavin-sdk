<!-- full hand-back report of sub-agent a0162532, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PR H plan review, round 2 (design critic). Verdict: NOT READY. I found 0 Blockers, 5 Majors, 6 Minors, 2 Nits. Round-1 B1 and M2 to M7 are answered in the design. M1 is only partly closed, and the answer opens a promise-2 gap of the same kind (D1 below). Line numbers refer to the plan file (631 lines). I read the plan, round-1 summaries, evidence README, c790d.out, cost-protofixes.out and repro-protofixes.out, the author report, the PRH-c stub, and main's runmap.py and redact.py at the cited places. I ran nothing.

## (1) Round-1 findings: are they closed by design?

- **B1 / readiness B2, case 790: closed, with a gap (D2).**
  - Section 8.1 and c790d.out give a coherent cause and a minimal input.
  - Longest-first is a real fix for nested spellings. Main's own sweep already sorts longest-first (redact.py:974), which supports the author's reading.
  - T4(b) with mutant 27 is a fair regression guard.
- **M1, the 256 fallback: partly closed.**
  - The new rule (W2 steps 3-5) counts only needed values and raises `InputTooLarge` above 256, as main's `_decoded_masks` does. That removes the old trigger.
  - Two problems remain: step 6 still has a joined-result fallback (D1), and the refusal path was never run (D5).
  - repro-protofixes.out rows M1a/M1b use 300 plain e-mails that are not "needed". They test the old failure, not the new refusal.
  - The cost row (line 404) says explicitly that no value needed the gap.
- **M2, decode-produced hidden item: closed.**
  - The new decoded reading and the in-round strip are reproduced on main and fixed. M2c is honestly excluded with a reason.
  - One more bypass remains in D1: a stripped-reading mismatch on handed-out secrets whose spelling is base64, base32 or hex.
- **M3, runs of items: closed (definition and table, lines 276-289).** It was never a leak (M3a-d MASKED on main).
- **M4, map clean-up: closed by splitting out.** The stub PRH-c is honest. Note that it names the same fragment-entry condition that causes 790 (D2).
- **M5, card seeding: closed for the shown inputs.**
  - M5a is fixed through `_no_created_shapes`; see section (3) for limits.
  - W4 no longer touches the gate.
- **M6, model-written inputs and grounding: closed in the contract (promises 4 and 5, T11).** It enlarges scope (D8).
- **M7, generator axes: closed (T1 lines 416-427).** The "shares no code" claim is narrowed to "shares the patterns".

## (2) Case 790 diagnosis: right for the nested case, not complete

**Major D2. Sibling classes the longest-first sort does not close (W2 `_keep_earlier_masks`, section 8.1 lines 529-530).**
- **Partial overlap.** The sort only helps when the shorter spelling lies wholly inside the longer one. Take two known values where a suffix of A is a prefix of B, e.g. view `xxxxPQRSTUVW` with A=`xxxxPQRS` and B=`PQRSTUVW`.
  - A is applied first and gives `<A>TUVW`.
  - B is no longer whole, and its tail stays readable.
  - The ticket's "sibling search" lists only the sweep and `replace_canonical`. It does not consider this overlap class, nor the same overlap inside `_redact_stripped` step 5, which also replaces values one after another.
- **Equal length.** `sorted` is stable, so equal lengths keep list order. Equal-length values cannot be nested but can overlap partially, so list order still decides.
- **Mixed spelling domains.** The pair list mixes raw, escaped, joined and spaced spellings. For example the escaped look-alike form of a short value can be longer than the raw spelling of a long one. Length is a proxy for containment only inside one domain.
- **Prefix overlap** (same start) is fine.
- **Unicode-normalised lengths** are fine. Spellings come from `undo` and NFKC and the view is NFKC, so lengths are in one domain. Only the neutralised pair (runmap.py:502-506) adds escape characters.
- **Unexplained precondition.** The ticket does not explain how the map came to hold a fragment value (SECRET_2 is 9 characters of PART1 plus the tab). PRH-c reports 386 of 7,066 inputs on main with one entry's value inside another's. That is the root condition of 790.
  - The sort treats a symptom in one function while the root is deferred to the stub.
  - The ticket also admits the ordering bug was never shown to trigger on main (lines 620, 629).
- **Recommendation.** Do one of three things:
  - replace the loop with one alternation applied in a single leftmost-longest pass;
  - add a generator test for partially overlapping known values;
  - state partial overlap as "not promised" and give PRH-c an explicit dependency on this ticket.
- **T4 labelling is confusing (Nit, lines 433, 453).** T4(a) exercises an existing function with a hand-built input. It should be listed as fails-on-main, not "no old behaviour".

## (3) Rule "removing hidden items never creates a placeholder or marker"

It is good, and complete for the shown inputs: F1a-g, M5a and the `undo` in-round call. Its limits:
- **Counting, not positions (lines 348, 384).** Any placeholder string that occurs more often after removal than before is rewritten everywhere in that text.
  - A real placeholder and a forged copy of the same name in one text both become `‹…›`.
  - For model-written text the executor then gets the look-alike, and "a grounding step refuses" is not checked for every executor.
  - This is stated, but it is a behaviour change that only T3 covers.
- **Callers outside the choke point.** `redact()`, `redact_many()` and `sweep()` keep today's behaviour (W1). The `demos/` directory was not searched (line 630), so direct callers are unproven. T1 lists `redact_many` as a path but gives it "today's behaviour".
- **Ignorable items.** They are kept in the output and in the "before" text. A placeholder spelled with a zero-width character is not a created shape under 3b on non-untrusted paths (judge, vendor, card). Only untrusted paths get the canonical check.
- **Check is whole-string, not per-reading.** The rule also does not cover shapes that appear after the later decode steps on non-untrusted paths. Those callers get no `_refuse_forgery`, and promise 3b says "never creates", not "never".
- **Recommendation.** Promise 3b should be re-worded as "within the listed callers, for removal of the listed items".

## (4) Cost limit 1.25 times main

**Major D3. The 1.25x limit is unproven and not a gate (lines 406, 408, 619).**
- The only fast-path claim is "meant to bring them to at most 1.25 times". It was never measured.
  - The prototype shows 0.51 s against 0.38 s CPU for plain ASCII, i.e. 1.34 times.
  - The whole excess is attributed to the slow loop. A compiled search over 262k characters costs about a millisecond, so about 0.13 s of excess is unexplained. Candidates the ticket does not examine:
    - `_repair`;
    - the second `esc()` of the original;
    - `_no_created_shapes`;
    - `_views(e_joined)`;
    - the extra `undo`.
- **Hidden extra `undo` on hidden-free text.** The new decoded reading `undo(text, strip_hidden=True)` is computed for any text with `\`, `%` or `&` before it is deduplicated against the plain one. A JSON, URL or HTML log therefore pays a second full-text decode to a fixed point even when it holds no hidden item. The JSON row at 0.47 s CPU against 0.40 s is the only evidence, under the slow reader.
- **Non-ASCII shapes are excluded without a reason.**
  - Hindi is 1.27 s against 0.80 s (about 1.59 times). Persian is 1.88 s against 1.43 s (about 1.31 times).
  - The `is_ignorable` frozenset test per character is the likely cause.
- **"The four shapes with no hidden item" is never named.** The table has coloured output, which does contain hidden items.
- **Not a gate.** The 1.25x check lives only in the evidence table (acceptance 9). It compares two worktrees by hand-run medians of three. Neither the ticket nor the CI turns it into a pass or fail on this repository.

**Testing it reliably.**
- Measure process time only (`time.process_time`), with a minimum or median of five or more runs, in one process, ratio against an in-process baseline. The ticket never says which clock T9 uses, and the cited rule file `tests/fixtures/timing.py` was not available to me.
  - For example, assert that `hidden.strip` on hidden-free text costs less than 5 percent of `redact_text` on the same text.
  - Separately, assert that the hidden-free path takes the same number of passes as main (1) and makes no extra `undo` call, using counting stand-ins.
- The 3.0 s limit leaves Persian at 1.88 s, 63 percent of the limit. On a loaded CI machine that will flake. Prefer pass counts as the gate and keep seconds as the evidence.

**Major D4. Worst case (18 passes) is unmeasured and turns into refusal.**
- Line 247 bounds the work at 2 + 8 x 2 = 18 passes, with a 6-second wall budget checked before every pass. Main's worst case is 4 passes.
- The costs are roughly 0.8 s per pass for Persian and 0.4 s for ASCII at the cap. A legitimate large (above about 100k characters) non-ASCII log with a coloured grep match inside a word and one `%` gets 8 readings x 2 passes.
  - That is over the budget, so `InputTooLarge` refuses the whole text.
- This is an availability regression on real input, not only a hostile shape. It is also attacker-triggerable: a document can be made unreadable.
- The cost table has no shape that reaches more than 2 passes per reading; the hostile row is 0.82 s (line 404, cost-protofixes.out line 20).
- Add a measured worst-case row and either lower the count (build the joined-reading views only when the text readings differ) or state the refusal.

## (5) Security: ways a secret survives, fail-open on oversize

**Major D1. Promise 2 ("no step back") is contradicted by the design itself.**
- Promise 2 is unconditional (line 219). Two designed exceptions give it up:
  - `_scrub` second branch (line 361): when a handed-out secret is found, the scrubbed joined text is returned. A hidden item that acted as a word boundary no longer does.
  - `_redact_stripped` step 6 fallback (line 355): when a held placeholder is missing, the joined result is returned.
- Failure scenario for `_scrub`:
  - A tool prints an auth failure that echoes the handed-out token (the usual way a token appears in output).
  - The same result also holds `INFO` + ESC `[0m` + a key. Main masks the key because the escape acts as a boundary. After PR H the key stays readable.
- This is the round-1 M1 pattern (a fallback gives up promise 2), re-created with a different trigger.
- Step 6 has the same defect and nothing shows it can be reached. No test is described that forces it, and mutant 23 names no killer. If it is unreachable it is dead code that still loses promise 2 if wrong. If it is reachable, an attacker can choose when it fires.
- T1's no-step-back test never combines a boundary-only key with a handed-out secret or with a cut value.
- Fix: mask in place on the raw text (a gap pattern, as in step 5) instead of returning the joined text. Alternatively, state the exceptions in promise 2, put them in the CHANGELOG "not promised" list, and add combination cases.

**Minor D5. The `InputTooLarge` above 256 needed values is attacker-triggerable and hits legitimate input.**
- A coloured `grep` output highlights partial e-mails or hosts. Each highlight cuts a value, so it counts as "needed". More than 256 distinct ones refuse the whole tool result.
- Main passes it through with a leak, so this is a regression in availability only. It should be stated in the CHANGELOG.
- T9's M1 shape ("more than 256 distinct values plus a hidden item inside a word") needs distinct cut values, not just distinct addresses.

**Minor D6. Step 5 "linear, no nested repetition" is asserted, not shown.**
- The pattern for a value with spaces (a quoted password) has several optional-space tokens between literal spaces.
- Python's `re` has no memoisation. A long run of spaces after such a start can multiply work per start position. The time budget is checked only between passes, never inside a regex.
- Add a T9 shape with a spaced value (a quoted password) and a long run of spaces.

**Stated residuals, not new (acceptable only if in the CHANGELOG):**
- hidden items inside base64, base32 or hex spellings of a handed-out secret (line 239). That is the most sensitive class left open, and it is cheap for a hostile tool to produce;
- encoded pattern-shaped secrets;
- cuts by tab, line break or backslash plus line break (line 231), which a model can rejoin trivially;
- cursor and overstrike effects;
- an unterminated string sequence blanks the rest of its line (an attacker can delete a legitimate line tail, a data change rather than a leak).

**Fail-open on oversize:** I found none on the redaction path. `_within_cap`, `fits_after_nfkc` after every escaping, and a refusal on the budget all fail closed. The unmeasured 18-pass case is the exception on the availability side (D4).

## (6) Rung table (lines 254-263)

- **Major D7. Present, but the library row has no evidence.**
  - The table exists, and its own rung 3 row is marked UNVERIFIED with research deferred to 2026-11-18. "Not chosen" without research means the "rung tried" column does not describe a rung that was tried.
  - I did not read rule 20 or R447/R448 text, so say if the rule forbids deferral. As written, the plan cannot justify "KEEP-CODE" for a new roughly 150-line module with its own parser.
  - Higher rungs not weighed: the `regex` package (carries Default_Ignorable_Code_Point; you chose not to add a dependency); and a policy rung (refuse or replace instead of strip) that was not considered against the removal approach.
  - The table also omits the generator tool, the oracle and the `_scrub`/`_sanitise` changes as components.
- The Unicode file row (line 260) is honest about the derived data.

## (7) Scope creep and new dependencies

**Minor D8. Scope is wider than the title.**
- Promise 4 (model-written arguments stripped, form feed becomes a space) and promise 5 (grounding refuses any identifier with an ignorable item) are behaviour changes for evidence and executors. They come from `canonical` being shared. A separate Cf-only function for `evidence.py` would avoid both and leave PR H narrower.
- The digest change for NUL results (W3), 37 mutants with a new blocking CI step, a roughly 9,000-case generator and a 12-item acceptance list all sit on one pull request.
- The time boxes (60 minutes per work package) do not look feasible for WP2, which holds three source files, tests T1 to T8, T11, T12 and fixtures.

**Minor D9. Unicode data file, generator and hash pin are heavier than needed.**
- A 17-range literal in `hidden.py`, tested against the derivation rule over `unicodedata`, would do. The committed data file, the hash pinned in a unit test, and a generator with three modes (`--from-codepoints`, `--from-ucd`, and a default) are three extra artifacts. The perl mode is not usable by the builder.
- The equality test against live `unicodedata` over all code points will break when Python moves to Unicode 16 (or the file stays at 15.0). It is a time bomb for a maintainer on a new Python. Gate it by `unicodedata.unidata_version`.
- The data licence text is unverified (line 265); the licence-notice step is vague.
- No new runtime package: good.

## (8) Wording for non-technical readers

**Minor D10.**
- Section 1 is a good plain-words start.
- Dense or undefined jargon in the sections the lead needs to judge:
  - "oracle", "mutant", "glue rule", "held", "needed", "seed entry", "found" and "mask" appear before or without a definition. "Held" and "needed" are defined only inside W2 steps (lines 351-352).
  - The 8.1 cause paragraph (line 528) lists SECRET_1 and SECRET_2 and "escaped spelling", with no one-line summary.
  - "Choke point" is used throughout; define it once in section 1.
- Rev 2 change item 1 should say in one sentence what a user sees: a fragment of a secret stayed readable on the card.

## Nits

- Line 26, "Read first" item 2: "14,132 runs, 0 breaks" is quoted although not evidence.
- Line 433 names mutant 27 as T4(b)'s killer but section 5 lists no killer per mutant.

## What I did not check

- Rule 20 text, R447/R448 and the studio rules cited (so D7 is conditional).
- `tests/fixtures/timing.py` and `tests/test_migration_numbers.py`. The clean main snapshot has `src/` only. Copies exist only in on-disk checkouts, which I was told to ignore, so the "processor-time style" advice in (4) is from general practice, not from that file.
- All unrun claims: I ran nothing, so the counts (7,505 passed, 43 files, 4,174 code points, 14,132 runs) are the author's. I did not open the fuzz or targeted-proto logs, the author scripts, or the PRH-b stub.
- The Unicode derivation, ECMA-48 and CWE statements.
- Main code beyond `_views`, `_decoded_masks`, `_keep_earlier_masks`, `redact_text` and the sweep ordering line. Not checked: `tools.py`, the gate, `evidence.py`, `canonical`. The cited line numbers outside runmap.py and redact.py were not re-verified.
- Whether any attacker input actually reaches the step 6 fallback. I could not construct one by reading, so D1 for step 6 is "unproven and untested", not "exploited".
- Reachability of overlapping known values on main (D2). The author could not show it either.

Files read: `/home/user/build/snap/prh-plan-r2/tickets/PRH-strip-hidden-controls-at-the-choke-point.md` (plan), `/home/user/build/snap/prh-plan-r2/evidence/c790d.out`, `cost-protofixes.out`, `repro-protofixes.out`, `README.md`, `/home/user/build/snap/prh-plan-r2/tickets/PRH-c-map-entries-hygiene.md`, `/home/user/build/snap/prh-plan-r2/reviews/plan-r1-design.md` and `plan-r1-readiness.md`, `/home/user/build/snap/prh-plan-r2/reviews/author-errata-rev2-report.md`, and main's `guard/runmap.py` and `guard/redact.py` under `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/`.
