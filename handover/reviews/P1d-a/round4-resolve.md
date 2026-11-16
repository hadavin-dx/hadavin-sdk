Status: resolved (fixes applied to `handover/tickets/P1d-a.md` as revision 5; not committed)

# P1d-a plan review round 4: resolve (egm-resolve method, headless)

**Written:** 2026-11-09T08:41Z (IST 14:11), by `date -u`. **Target:** ticket rev 4 (full file, 293 lines). **Findings:** `round4-design.md` (0 Blocker / 4 Major / 7 Nit) + `round4-readiness.md` (2 Blocker / 3 Major / 4 Minor / 4 Nit) = 24 findings, merged into 19 groups (R4-G1..G19). **Path class:** redaction, no round cap.

**Counts:** PROPOSE FIX 24 (all applied in rev 5). CONTEST 0 (one example inside readiness nit "G3 `&name;`" is contested by probe P6, the finding itself is fixed). ESCALATE 0. DECLINE 0. NEEDS LEAD: 1 new (A15, NEEDS LEAD 4) + 3 carried (1-3). Unaddressed 0.

**Probe P6 (run by the resolver, read-only; scripts and raw output in `handover/evidence/P1d-a/probes-r4/`):** `git archive 0dabf1f src` into the session scratchpad; the handover `.venv` Python with `-I` and that `src` first on `sys.path` (the output's first line prints the imported package path, under the scratchpad copy). The redactor's generic SECRET entry (found by its exact value text, R3) replaced by the two rev-5 D2 entries (plain first, then query). Model path = `runmap.redact_text`; card = `channel.clean` with the BASE gate (D1 not built; every probed input holds no dot, so D1 does not change it). Results:
- Every "expected after" string of rows H34a-d, Q2, Q4-Q8, Q10-Q17, KV1, ENT, F16, F17, SC1, NE1, PU1 came out exactly as written in rev 5, placeholder numbers included (on both paths where the row lists both).
- 30 REAL lines (rev 5 BS-1): 0 mismatches on both paths with the rev-5 grammar; 1 line (R27, key after `&amp;`) fails with the rev-4 grammar on both paths; 20 of 30 fail on base (model path).
- Base cells of the new rows (unpatched `0dabf1f`): written in the rows table, marked (P6).
- Mutants A32-A35, A39, A40 checked as stand-alone regexes (reduced to the D2 entries, full key list): each changes its killer row's output.
- NOT probed: D1, D3, `undefang_text`, the properties, the BS-1 random shapes (S1-S7), anything on the build head.
- `curl https://url.spec.whatwg.org/` was refused by the proxy (403): the WHATWG section number is still UNVERIFIED.

---

## Blockers

### R4-G1 `test_stored_card_round_trip` fails on correct code (readiness 1, Blocker). PROPOSE FIX
Valid: `x = "a[.]b"`: `clean` leaves it; `_blocks` reads `[.]` between name characters as `.` (D1, by design, L15), so the Slack text is `a.b` and the property fires on correct code. **Fix:** the property draws from G-TXT-B (ALPHABET-B: no `[`, `]`, `[.]`, wide dots), with the reason written next to it. ALPHABET-B already existed for `test_defang_text_only_rewrites_dots`; it is now a named generator with its own stream.

### R4-G2 pre-redaction differential compares different chains (readiness 2, Blocker/Major). PROPOSE FIX
Valid: the right side applied `_PLACEHOLDER_DOT` only, while the left `defang_text` also defangs the domain after the placeholder (`<HOSTNAME_1>[.]example[.]com` against `<HOSTNAME_1>[.]example.com`). **Fix:** right = `defang_text(withhold_commands(sanitise_text(x)))`, the same final step D1 uses; the only allowed difference stays "the left withholds more".

## Majors

### R4-G3 no row has the query key after `&` (design M-1). PROPOSE FIX
Valid. Rows Q13 (pb, `?user=bob&password=ab12cd&next=/home x`) and Q14 (fb, `?user=bob&password=ab&cd34ef56 x`), card and model; mutants A32 (query lookbehind `[?&]` to `[?]`, killer Q14) and A33 (plain lookbehind without `&`, killer Q13). P6 confirms base and expected strings.

### R4-G4 key after `&amp;` takes the plain entry and over-masks (design M-2). PROPOSE FIX (one fix chosen)
Valid, and P6 shows it is not rare: REAL line R27 (an HTML-escaped address in a log) fails with the rev-4 grammar. **Fix chosen (one):** the query key lookbehind becomes `(?:(?<=[?&])|(?<=&amp;))` and the plain key gets `(?<!&amp;)`, so a key after `&amp;` is read in query form. "Record as accepted over-mask" was rejected: it hides the rest of every HTML-escaped address. Row Q15 (pb: base and after are both `?a=1&amp;password=<SECRET_1>&amp;next=/home x`; the rev-4 grammar would have broken it); mutants A34 (query `&amp;` lookbehind removed) and A35 (plain `(?<!&amp;)` removed), both killed by Q15. Query form definition, D2, Code shape and the redact.py comment updated.

### R4-G5 G3 and CHANGELOG claim more than the grammar does (design M-3; readiness nit "G3 `&name;` wording"). PROPOSE FIX
Valid for `;`, quotes and the comma rule: `password=ab&cd34;ef56` shows `;ef56` (P6). **Fix:** G3 now says a plain value still ends at white space, quote, `;` or a comma that starts `key=value`; query values end at `&`/`&amp;` only before `key=value`; the card hides exactly what the model path hides. CHANGELOG: "hidden up to the next space, quote or semicolon". Rows SC1 (fb) and NE1 (pb). Part CONTEST of the readiness example only: `password=ab&copy;cd x` is masked whole on base and with D2 on both paths (`password=<SECRET_2> x`, P6), so it does not show `cd`; it is pinned as row NE1.

### R4-G6 mutation plan gaps (design M-4). PROPOSE FIX
Each item:
- A5 covers only the split branch: new A43 drops the double-backtick guard, killed by new row G2 (`see ``note `evil.com` x`` now`; base and after `see ``note `evil[.]com` x`` now`, P6).
- Query `&amp;` unit look-ahead: A36 (`&amp;(?!...)` to `&amp;`), killed by Q7.
- Plain `&amp;` unit look-ahead: DROPPED from the design (reviewer's second option). Without it the unit only masks more (`password=ab&amp; x` hides `&amp;` too); no row needs it. Row PU1 pins the new output (`password=<SECRET_2> x`, P6). A23's `old` becomes `|&amp;|`.
- Fence marker: A37 (`ch == "`"` to `ch in "`~"`), killed by L4.
- `i % 2` swap: A38, killed by L2.
- Quotes in the segment class: A39 (on the `&` alternative, row Q16) and A40 (on the `&amp;` unit, row Q17).
- `-` and `\w` in the `_PLACEHOLDER_DOT` look-ahead: A41 (`(?=\w)`, new row D3f `<EMAIL_1>.-a.com`) and A42 (`(?=-)`, killed by D3b).
- A15: now RUN, not assumed equivalent. Reason it is expected to survive every row: it differs only where a key follows more than 40 key characters, and there it masks more (INFO-K41). Its acceptance is NEEDS LEAD 4 (the ticket rule: a survivor is a defect unless the lead accepts).

### R4-G7 generated inputs not reproducible (readiness 3, Major) + S311 decision (readiness Minor 8). PROPOSE FIX
Valid: joiner, token weight, length draw and G-EH shape were open, and `fuzzgen.py` is a SQL generator that suppresses S311. **Fix:** one draw function `d(stream, n)` from SHA-256 of `SEED:stream:k` (stdlib `hashlib`, no `random`, so no S311 and no suppression; stable across Python versions); ALPHABET-A as a 63-entry list with equal weight (asserted length), ALPHABET-B 57; G-TXT: length `d(201)`, no joiner; G-EH: exact line, word and kind draws, joiners. The BS-1 corpus uses the same `d`.

### R4-G8 no rule for a row that fails after build (readiness 4, Major). PROPOSE FIX
Valid. **Fix:** "When a row or a property fails after build": the builder may fix product code; if it judges an expected string (or seed, count, alphabet, allowed difference, assertion) wrong, it stops and sends row id or seed and index, input, output and expected to the lead and edits nothing. In addition P6 confirmed every redactor row's expected string, including the placeholder numbers the reviewer named (H34b, Q8, Q12, H34d, KV1); the card/defang rows that depend on D1 and D3 stay unprobed and are covered by the rule.

### R4-G9 BS-1 builder-authored parts (readiness 5, Major; design N-1). PROPOSE FIX
Valid. **Fix:** the 20 words (`alpha` to `tango`), the 7 keys, every tail and field draw, the S length draw (`8 + d(33)`), the `&` placement draw, S3 and S7 draws, the 100-character tail cut, and the 30 REAL lines with their hidden strings are written in the ticket. REAL lines were changed from the rev-4 description where the card legitimately rewrites the line (a `mysql`/`psql` command is withheld by the gate, an HTML tag is removed): they use `./backup`, `./migrate` and `link=` forms instead; P6 shows 30 of 30. Design N-1 (S may hit e-mail or other entries): an S that the redactor changes on its own is drawn again, and redraws are counted per shape.

## Minors

### R4-G10 builder action while NEEDS LEAD 1 is open (readiness 6). PROPOSE FIX
The builder runs BS-1 with the proposed gates and continues to evidence and review, but opens no pull request until the lead answers.

### R4-G11 ruff and ZWSP (readiness 7; design header: literal U+200B and rows Z1-Z4). PROPOSE FIX
`from collections.abc import Callable` written; `zip(out, seen, strict=True)` (B905); every ZWSP written as the escape `\u200b` (checked: the file holds 0 U+200B characters).

### R4-G12 `tools/p1d_corpus.py` import path (readiness 9). PROPOSE FIX
`tools/` is a package on `0dabf1f` (`tools/__init__.py`); every call is now `python -m tools.p1d_corpus` from the worktree root, so `tests` and `tools` import without a `sys.path` edit.

## Nits

### R4-G13 no reason for the length (design N-2; readiness nit). PROPOSE FIX
A "Why over 250 lines" line is the first paragraph after the title. Rev 5 is 326 lines (rev 4: 293); the growth is the generator procedure and the 30 REAL lines the readiness reviewer asked to be written out.

### R4-G14 row ids P1/P2 collide with probes P1-P5 (readiness nit). PROPOSE FIX
Rows renamed PF1, PF2; A25, A26 killers updated.

### R4-G15 replaced comment spans lines 609-611 (readiness nit). PROPOSE FIX
R3 now gives the comment's lines (609-614) and Code shape names the replaced sentence (lines 610-611 on `0dabf1f`, read by the resolver).

### R4-G16 stored pre-fix summary read through `clean` (design N-3). PROPOSE FIX
Confirmed by R7 (only `FakeChannel.send`, a test fake fed by current code); R7 now says `clean` does not undo `[.]`, so any other reader is a BS-0 STOP (already in the STOP rule).

### R4-G17 mutation_runner fields unverified (design N-4). PROPOSE FIX
Read on `0dabf1f`: `tools/mutation_runner.py` lines 73-88 (`Mutant` fields as listed in R8) and 365-376 (`run_mutants` signature, no `forbid_skips` yet: ORDER 181). R8 updated.

### R4-G18 WHATWG 5.1 citation unchecked (design N-5). PROPOSE FIX
Tried: the proxy refused the page (403). D2 now marks the section number UNVERIFIED; BS-0 step 8 records the section number and date.

### R4-G19 "raises TypeError" nit (design). PROPOSE FIX
D1 now says the error is raised when that call site runs, and names the rows that reach every call site (PF1, PF2, E1, I2, FB1, FB2, H26).

---

## Counts in rev 5 (recounted from the file)
Rows 68 (fb 35, pb 30, ow 3); new: Q13, Q14, Q15, Q16, Q17, SC1, NE1, PU1, D3f, G2; renamed PF1, PF2. Mutants 48 (47 with a killer, A15 an expected survivor; A22 decided equivalent, not run); new: A32-A43. BS-1: 635 samples (S1 50, S2 25, S2x 67, S3 25, S4 50, S5 50, S5x 268, S6 50, S7 20, REAL 30). Ticket 326 lines; U+200B characters 0.

## NEEDS LEAD (open)
1. BS-1 gates (carried). 2. Wide-dot host names and INFO-K41 (carried). 3. Stored-request render change, L15/L16 (carried). 4. NEW: accept A15 as a written equivalence (masks more only after a 40+ character key prefix), or rule that INFO-K41 is fixed in P1d-a.
