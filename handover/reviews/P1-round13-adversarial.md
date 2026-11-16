# P1 round 13, adversarial review (ticket revision 14, commit 8b5d849)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Target: `tickets/P1.md` revision 14 (336 lines). Reviewer: `egm:egm-design`, read-only, nothing run; every hand trace UNVERIFIED; several Unicode properties are from memory and could not be checked against a table (marked). Did not open `reviews/`.

Verdict: no Blocker, 2 Majors, 1 low-confidence Major candidate, 7 Nits. All counts recount. NOT CLEAN.

## MAJOR
**ADV-R13-1. The coverage sentence omits enclosed, negative-circled and dingbat forms** (lines 7, 19, 47, 50, 220, 254, six copies). Negative circled and negative squared letters U+1F150-1F189, regional indicators U+1F1E6-1F1FF, dingbat and circled digits U+2776-2793 and U+24F5-24FF (incl. U+24FF) have no NFKD decomposition (from memory) and no table entry (reviewer probed U+1F1xx, U+2776, U+24F5, U+24B6: none). The letters are category So and are dropped by the final isalnum filter (lost, not folded); the digits are category No, survive isalnum, and S4 maps only Nd, so they never equal ASCII digits. A copy of a made-up account number written with dingbat digits, or a name in negative-circled letters, matches no key and reaches the model. The six-copy sentence neither claims nor lists it. Fix: add the ranges to the generator SUPPLEMENT with table rows, or name them in the not-caught list in all six copies; add a data-driven pin row.

**ADV-R13-2. The Lm step 1b has false reasoning and a leak** (lines 7, 55, 106, 145-146). Step 1b removes every Lm character from the RAW text before S1, deleting superscript and subscript modifier letters (U+1D43, U+207F, U+2090, U+02B0 and others) that NFKD would fold to base letters. Substitution copies (a letter replaced by a superscript form) lose the letter in `scan_keyset(t)`; they are caught only because the design also scans `scan_keyset(undo(t))`, whose NFKC step folds them. A copy mixing one superscript substitution with one superscript insertion matches neither view: the t view deletes the substituted letter, the undo view keeps the inserted letter folded in. Line 146 says U+02B0 is "the one code point that the key drop alone cannot find"; that is false (dozens of Lm letters have letter decompositions). R12-LM tests insertion only; no row tests substitution. Fix: (a) state the limit and add a pin row for the mixed case, correct line 146; or (b) add a third reading (key count to 16 maximum; re-do the S_call estimate). Also add a test that no table source is Lm (raw removal would make such an entry dead).

**ADV-R13-3 (low confidence, UNVERIFIED, from memory). Blank-glyph characters outside FILLERS** (for example U+3164, 115F, 1160, 2800, FFA0, and Egyptian hieroglyph blank signs near U+13441) may be letters or symbols that survive isalnum and split a value. Fix: a data-driven test over all Default_Ignorable_Code_Point and White_Space characters and names containing BLANK or FILLER, asserting each is dropped or mapped.

## NIT
- N1: "every plain copy of a secret kind" holds only from 4 characters; other kinds replaced only when standalone, not all-digit under 6, not a common word, at least 3 characters (`redact.py` `_sweep`, `_COMMON`, about 1140-1217). Say "from 4 characters".
- N2: line 55: the Mc two-part vowel NFKC join in 11 scripts is missing from the stated limits although the Korean jamo join is listed.
- N3: `_checked` (lines 44-45): single loop; (oversize a, non-str b) gives TextTooLong not NotText. State the order or fold a row.
- N4: lines 145-146: the two new Lm mutants collide if both use the same `category(ch) != "Lm"` idiom (meta-test (g) forbids a search string occurring more than once). Make the search strings distinct.
- N5: the S_call estimate of 0.25 s per key predates the added `category()` call. Re-state.
- N6: line 265 relay: "nothing else" about encoded values would change if P2d adds base64 forms; add "as of `tools.py` `_secret_forms`".
- N7: the combined merge order puts P4d after P1b although P4d does not depend on P1.

## Lead wording versus ticket (PL46)
The lead's "caught by nothing" is untrue for handed secrets: `tools.py` `_secret_forms` (744-759) already makes hex, JSON, percent, base64 and urlsafe-base64 forms of a handed secret and `_scrub_layers` (906) applies them. The ticket's narrower text is true against that code. Orders 14(1), 14(2), 15 and Q12 are carried correctly. Keep the ticket's wording.

## Checked and sound (UNVERIFIED hand traces)
Six sentence copies word-for-word consistent; classes dropped by the final isalnum filter (Mc, Sk, Sm, So, Zs; Cf and Cc in S2); circled, parenthesized, squared letters, superscript digits, fullwidth and mathematical alphanumerics fold through NFKD; NB-1, R11-CYR, R11-GRK hold and the table has the letters they need; mutant lines and killers exist in the snapshot (promoted_mutants.py 379, 435, 1041, 1160, 1347; killers at test_promoted_controls.py 764, 853, 879, 1863, 2068, test_pr50_fix_batch.py:404); ci.yml, pyproject, defaults.py, runmap.py cites; runner facts (CHILD_ENV 84, JUNIT_REFUSED 94/278, ET.fromstring at mutation.py:91).
Recount, all match: P1m 21; re-pointed 28; P1a new 14; P1b new 18; distinct 81; runs 109+k (k <= 14, max 123); public names 19; constants 3; v1.1 rows 25; scan keys <= 8; 677 = 614+61+2; 733 = 677+56; 15 removed rows.
Cross-ticket: P2a line 22 depends on P1m, P3a and all five P4d pull requests, not on P1a/P1b; P2d 30, 315, 334 and P5a 21, 32, 57 stale as P1 says; P4d line 17 defaults order contradicts P2a line 22 (PL44 relays).
