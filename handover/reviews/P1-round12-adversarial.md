# P1 round 12, adversarial review (ticket revision 13, commit 3f0236f)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Target: `tickets/P1.md` revision 13 (on disk). Reviewer: `egm:egm-design`, read-only, ran nothing, so behaviour claims are UNVERIFIED by run. Did not open `reviews/`. Read ticket lines 1-224, 255-264, 312-318 (NOT 224-254 = PENDING LEAD 1-39, nor 264-311 = UNVERIFIED section and "Checked in revisions 8-12"); did not check the coverage sentence in PENDING LEAD 39 (confirmed byte-identical at lines 7, 19, 47, 50, 220; the ticket's line 314 says six copies match). Read snapshot `textnorm.py` 36-133, `_confusables.py` (grep), `redact.py` 1478-1503; P2a line 22; P2d lines 30-34; P4d lines 17 and 150; design "Values and keys" item (line 43).

Verdict: NOT CLEAN. 0 Blockers, 3 Majors, minor items. All counts recompute. This round does not count toward the two clean rounds.

## MAJOR
**M1 (UNVERIFIED by run). A letter-category modifier character inserted into a copy survives the scan key (example: Arabic tatweel U+0640).**
- Old fold drops categories Cc, Cf, Mn, Me, Zl, Zp, Co, Cs, Cn plus the five FILLERS (snapshot textnorm.py:42-45). The scan key drops characters whose `isalnum()` is False (ticket line 55). U+0640 is category Lm, not dropped, no table entry (grepped `_confusables.py`), and `isalnum()` is True for Lm. Same expected for U+30FC and U+FF70 (not grepped).
- Scenario: known value `bank12345-vault` (made up); the copy writes `ba` + U+0640 + `nk12345-vault`; key is not a substring of the value's key; the check misses it and the text is sent. The coverage sentence promises "other characters added between or on them (zero-width or other invisible characters, marks, line breaks, spaces, punctuation)"; no letter-category characters are listed.
- Fix: (a) drop Lm in step S2 or in the scan-key drop only (not `identity_key`), one row (`scan_keyset("ba"+U+0640+"nk12345") & scan_keyset("bank12345")` non-empty); or (b) state it as a limit in the sentence. No ticket mention of "tatweel".

**M2. The coverage sentence is not true as written (repeated in six places, called "identical").**
- (a) No carve-out for stored NAME and ADDRESS: order 13(1) and the design (line 43 `LOOKALIKE_WORD_KINDS`; row LK-WORD "OUT: strict xfail (sent)") say that above 1 in 200 refusals in P-1 they stay out; the sentence says "a known value of at least 12 characters" unconditionally. Fix: add "except stored NAME and ADDRESS values if precondition P-1 shows more than 1 in 200 refusals".
- (b) "Nothing in P1 or in the look-alike check catches an encoded copy ... base64 or hex" is false against the design: it refuses percent-encoded copies (LK-PCT, also `\uXXXX`), entity-written copies (LK-ENT through `runmap.undo`) and a decoded copy of a value holding entity-like text (LK-ENT-VAL). Design line 25 says a secret a tool was handed is scrubbed in fixed spellings (as is, hex, JSON, URL-quoted, base64) by `_secret_forms` in `prepare_output` (old tools.py, not opened by the reviewer). The CHANGELOG text at ticket line 77 repeats it. Order 14 asked for that wording, but it is the lead's shorthand: keep it only with "raw base64 of the value, or a hex string of its bytes (not %XX, entity or backslash escapes, which the design reads)"; confirm the final wording with the lead. Overstating what is uncaught is the safe direction but still untrue.
- (c) The "does NOT catch" list omits: a 12+ character value whose scan key is under 8 letters and digits (for example 5+ punctuation characters); the pass A/B Greek mixed-case limit (ticket 220(2)); Korean jamo (limit 12); M1 above.
- (d) Order 15 floor wording is faithfully applied. Nit: "only their plain copy is masked, by the redactor" is true for secret kinds (4+ characters swept everywhere, `_EVERY_COPY`) but only partly for NAME/ADDRESS (`_STANDALONE`; common words not swept). Say "secret kinds" or point to LK-SHORT.

**M3. The P1b mutant "allow_equal accepting same_person where it must say DIFFERENT" cannot be checked by meta-test (g) and has no named killer.** Ticket line 146: no search string, no line; killer "the ALLOW rows with look-alike pairs". In the old code (textnorm.py:118-127) `allow_equal` already returns LOOKALIKE through `same_person` by design; "where it must say DIFFERENT" is undefined; looks like a duplicate of moved mutants #13, #14, #26. Fix: name the exact line (for example `if same_person(a, b):` replaced by `if True:`) and a row (`allow_equal("abc","xyz")` is DIFFERENT), or cut it (order 8); cutting gives P1b 16, distinct 80, runs 108+k, max 123.

## NIT / smaller
- N1: the type-check mutant and meta-test (g) can disagree. Line 145 says `isinstance(text, str)` replaced by a check accepting subclasses; the rule (line 44) says `type(x) is str` in nine public functions. Inlined in each, the search string occurs 9 times and (g) fails; require ONE helper (for example `_text(x)` doing type and size). Same for the size-rule mutant on the second argument (three two-argument functions: `same_person`, `allow_equal`, `names_equal`). `names_equal` has no row for a huge second argument although line 44 says the rule applies: add `names_equal("a", U+A516 x 87,382)` raises TextTooLong, or drop the claim.
- N2: the v1.1 table has a row whose trigger is "none: P1b adds it" (ticket line 195); the table is headed "each row has its trigger". Deleting it gives 25 rows.
- N3: hand traces that held: TAG-T0..T3, NB-1, NB-2, SK-3 (U+0406 row), `squeeze("SBZGQ", loose=True) == "58269"`, and the table entries for R11-CYR/R11-GRK (U+0430, 0442, 051B, 04CF, 03B1, 03C4, 03C5 all present). "Isolating" only partly checked for TAG-T1/T3.
- N4 (UNVERIFIED): mutant "the loop confirming pass removed" with killer "FoldNotConverged boundary row" (lowers `TEXTNORM_MAX_PASSES` to 2) may be equivalent; the builder must prove a KILLED verdict.

## Stale or wrong cross-references
- X1: ticket line 24 says P2d-2 follows P1b "(order 11 and P2d's own Depends line)"; P2d.md lines 30, 33, 34 still say P1a only / no P1b / "edits no constant". Change to "(P2d.md lines 30, 33 and 34 still say otherwise; relayed)".
- X2: revision 12 relayed nine stale P2d lines (3, 30, 33, 34, 264, 266, 315, 334, 339); revision 13 line 262 names only four (30, 33, 315, 334). The nine are still stale on disk; restore the list.
- X3: P4d.md line 17 says `defaults.py` order "P1a, P2a, P2d-1, P1b, P2d-2" while P4d line 150 / P2a line 22 put P2a after all five P4d PRs, so P4d contradicts itself; P1 relays this as PL44 (adequate; wording "P4d 17 contradicts P2a 22" is only partly right).
- X4: the ticket asserts P2a/P2d/P4d details it did not open; quoted P2d 33, P4d 17, P2a 22 confirmed.
- X5: P4d line 150 and P2a line 22 agree (P2a follows all five P4d PRs).

## Counts: all recomputed from the ticket's lists
P1b new 17 (4+4+2+4+2+1); P1a new 15 (listed); P1m 21 (3+13+5); re-pointed 28; distinct 81; runs 109+k, k 0..15, max 124 (21+43+45+k); public names 19 (17+2); constants 3, all P1a; v1.1 26 rows (lines 176-201); moved textnorm tests 13; P1m moved tests 14+7=21; edited moved tests 5. Header "rows +2" is a delta only.

## Order 8 cut candidates
The v1.1 "none" row (N2); the M3 mutant; `FILLERS` as a public name has no named caller in this ticket (demos UNVERIFIED): private would give P1a 16 names, total 18 (optional, changes counts). Pass B and T0 were decided by the lead or contested: no change.

## Nothing real found
Context-independence of keys (casefold per character, no final sigma; table keys single code points; NFKC joining after marks are dropped leaves only Hangul and Mc, both stated); P1's own merge chain; money path (none in P1); no real-looking secret or model id in the text read.
