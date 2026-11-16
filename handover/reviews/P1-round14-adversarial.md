# P1 round 14, adversarial review (ticket revision 15, commit afbaac9)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-design`, read-only, nothing run, did not open `reviews/`. All traces UNVERIFIED.

Verdict: NOT CLEAN. No Blocker. Two Majors; item 3 is a Major if the coverage sentence is meant to be exhaustive.

## BLOCKER
None found. No route to a model for a known value of 12+ characters that is not already a stated limit.

## MAJOR

**1. FILL-NAMES predicted to fail on correct code (line 88; PENDING LEAD 51; UNVERIFIED section ~line 284).** U+2422 BLANK SYMBOL is category So, not in `_DROP_CATEGORIES` (Cc, Cf, Mn, Me, Zl, Zp, Co, Cs, Cn) and not in the 7-character FILLERS (snap textnorm.py 42, 71). `fold` keeps it, so a row asserting every name-matched blank or filler folds away is red on a correct build; U+2423 OPEN BOX is similar. The ticket's only remedy is "the builder narrows the row". Fix: restrict to characters whose category is in the drop set (Lo, Cf, Mn) or assert against an explicit set; list U+2422 and U+2423 as known exceptions in the row, in the ticket.

**2. Re-pointed mutants #7, #8, #9 and #18 (lines 121-123, 132) cannot end KILLED.** Each deletes one line of `_confusables.py`. P1a adds an import-time TABLE_DIGEST check (line 41), so the mutated tree fails at import. `judge()` (testing/mutation.py 44-68) returns ERROR for a collection-error exit other than 0, 1, 5; on exit 1 the first line is not an AssertionError, so CRASH. KILLED needs an AssertionError first line. These have no allow_crash, and the plan says every one KILLED. The snapshot has no import-time digest check, so they worked there; the rev-15 change breaks them undiscussed. P1b's regenerated 733-entry table also needs search strings and line numbers re-derived. Fix: (a) each mutant also patches TABLE_DIGEST and the entry count in the same edit (then the search string is not unique to a line; meta-test g must check each patched string), or (b) declare the four with allow_crash and a pinned test expecting the import error (caught-by-digest, not table-coverage kills). Reviewer prefers (a).

**3. MAJOR/NIT: the coverage sentence reads as exhaustive about enclosed and dingbat forms (identical at lines 7, 19, 47, 50, 221, 255).** From memory, UNVERIFIED: U+24EB-24F4 (negative circled 11-20) and U+1F10B, U+1F10C (dingbat circled sans-serif digit zero) are not in the listed ranges; PIN-ENCL's hand ranges (line 106) omit them. If not caught, the sentence over-claims. Fix: "for example" wording; build PIN-ENCL from unicodedata names (CIRCLED, PARENTHESIZED, DIGIT ... FULL STOP, DINGBAT ...), not hand ranges. The sentence must stay byte-identical at all six places.

## NIT

4. "One word that mixes capital and small Greek letters" understates the limit; line 55 says any single copy needing pass A in one place and pass B in another fails to match, including across words or hyphens. Reword to "one copy".
5. The "does NOT catch" list covers only digit-written-as-letter (needle 5, text S); the letter-written-as-digit direction (needle l, o, b; text 1, 0, 6) is missing. PIN-NOT-MATCHED rows and the leetspeak v1.1 row cover it, but the sentence is the lead's coverage statement.
6. Cites to line numbers inside the ticket ("line 55") and other tickets ("line 18/114") are brittle; use section or row names.

## Attacked and held

Sentence byte-identical at six places; orders 14/15 wording true against the redactor floors and tools.py (`_derived`, `_secret_forms`, `_scrub_layers`); R13-LM-MIX claim that `runmap.undo` reads NFKC first (runmap.py 96-125); counts P1m 21, 28 re-pointed, P1a 14, P1b 18, distinct 81, runs 109+k max 123, `__all__` 17+2 = 19, constants 3; exactly two P1m CRASH mutants (snapshot 1179-1180 FileNotFoundError, 1753-1759 ValueError); squeeze mutants killable; "fold: fillers kept" has unique search string `ch not in FILLERS` near snapshot line 407; tag rows T0-T3 isolate by set membership; Mc and Mn dropped by the final non-isalnum drop; look-alike refusal and length rules consistent; no stale revision-14 text in the parts read.

## Not checked

v1.1 count of 26 and table counts 677/733; search-string uniqueness of the 13 runner mutants and P1a/P1b strings after the P1b rewrite; relays to P2a, P2d, P4d, P5a; the design file; Unicode counts (Lm 397, NFKD-to-ASCII Lm 65 and 266), NB-P, timings; P-1 rates and order 13 threshold.
