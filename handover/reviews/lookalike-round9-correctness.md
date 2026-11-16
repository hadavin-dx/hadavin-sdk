# Look-alike design round 9, correctness review (draft 9, 194 lines)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Target: `designs/lookalike-leak.md` draft 9. Reviewer: `egm:egm-codebase-details`, read-only, ran nothing (every trace by reading), did not open `reviews/`. Read LEAD-ORDERS (orders 8, 11-15), amendments.md, the full design, P1.md (rev 13), P2d.md; citations against the snapshot (748849c).

Verdict: no Blocker. 2 Major (F3, F4; both UNVERIFIED by running code), 11 Nits. Rules are sound; the Majors concern one test row that probably does not give its stated result, and one cost the design may underestimate.

## MAJOR
- **F3 (UNVERIFIED). LK-KIND-NUM probably does not give "refused".** Python `\d` matches Arabic-Indic and Devanagari digits. In redact.py, PHONE (lines 478-485: 10-16 characters of digits and spaces) and the `_fold_scan` / `_aligned_fold` path (1027-1107; digits of other scripts fold to ASCII and are masked in place) most likely mask the copy as `<PHONE_n>`. The put-back original then explains its own key, so c <= e and nothing is refused. The claim that the row fails on 748849c is probably wrong; the note "checked with python3 -I" covers only NFKC. Fix: pick a digit shape that PHONE and ACCOUNTID do not match, or assert as a row precondition that no placeholder stands where the copy is. Run the row once before relying on it.
- **F4 (UNVERIFIED which letters). The FR-42 cost can fire in real use.** Any stored value whose two readings differ (Greek capital Eta, Nu, Upsilon and similar) has its own token refused; its self-needle is explained only by min(count) = 0. With NAME/ADDRESS IN, Greek stored names or addresses end every text holding their token. The P-1 corpus (1 in 200) has no Greek benign texts, so the precondition cannot see this. Fix: a self-explanation rule for a needle derived from the same original, or add Greek benign texts to P-1.

## NIT
- F1: wrong P1 item name for the `l`-to-`i` class map, the `isalnum` removal and the tag texts (sections 1, 4, 8(3)); they sit in the bullet "P1b: the DENY keys (A1: ...)", not "P1b: identity, the readings, the keys".
- F2: "Relays to this design" is not a P1 item name; the content is under "Couplings" (its Relays text).
- F5: LK-ETA-COUNT does not say V must also be stored (the needle key(V)).
- F6: LK-ENT-VAL-PH, "plain and in Cyrillic spelling", must mean each in its own input; both in one text (c=2 > e=1) draft 8 would also refuse and M57 would not be killed.
- F7: M57 is defined against draft 8's "largest" rule; against draft 9's smallest rule only FR-2c kills it (adding undo(O) keys to the min makes FR-2c refused). State the implementation and the killer.
- F8: LK-ENT-VAL on the PW and MANY ways: the `password=` capture may stop at `&`, so the stored value could be only a prefix. Make the `&not` value MAP-only.
- F9: P2d stale lists incomplete: tickets/P2d.md lines 78, 170 and 307 also say "limit 4 per text". Lines 90, 149, 169 mention P1b but are not stale (say so).
- F10: LK-INSERT and LK-INSERT-SHORT behave identically under the count form, so the "checked / unchecked" distinction is gone; re-word or merge.
- F11: "PENDING LEAD 34" (P1's item) versus PL-LK-34 (redact_many kept) is ambiguous in the LK-UNFOLD row and section 5 item 1.
- F12: M9 is a prefix of M9b, so M9 has no unique search string.
- F13 NOTE (not a defect): "only plain copies" for 8-11 character secrets is order 15 verbatim; `redact_text` also masks full-width and zero-width copies and PL-LK-42 says so.

## Verified
- Counts by hand: 49 LK ids in 45 table lines plus GOLD-1; 11 strict xfail rows always (+2 if NAME/ADDRESS out); 39 FR rows; 62 mutant names, 22 deleted, 40 live = 38 in P2d-2 + 2 in P2d-2b; constants 2 or 3; PL-LK 1-51 none missing; LKV 1-16 with 11 and 13 withdrawn.
- Order 15 applied verbatim (only plain copies for 8-11 char secrets; LKV-2 trigger "before any pilot with real client data"). Nothing relies on the cut P1 entity step (order 14). P1 at rev 13; every cited P1 item name exists except F1/F2.
- Snapshot cites correct: runmap.py (redact_text catches InputTooLarge/TooDeep, wraps others as RedactionError(type name), map updated only after success 526-527); redact.py (sweep, _place, redact_many without a size cap, PHONE 478-485, _ACCT_WORD 89, _ACCT_DIGITS 93-96, _BANK_CONTEXT 100-110, _BANK_WINDOW 111, _bank_context 114-120, _fold_scan 1027, bank_near 1059, _aligned_fold 1082); tools.py (error_reason, secret() 501-514, secrets_handed_out() 645); textnorm.py `_DROP_CATEGORIES` line 42; `_confusables.py` 677 entries (U+0397 to H, U+03B7 to n, U+0431 to 6, U+0437 to 3); defaults.py MAX_MAP_ENTRIES 24.
- Hand traces that pass: LK-ENT-VAL-X, FR-2c, LK-ETA-COUNT, FR-41, FR-42 (as specified; cost is F4), FR-43, GOLD-1 related-values mode, LK-PH-FRAG, LK-PH-SWALLOW, LK-PH-NESTED, LK-PH-UNDO, LK-ERRMAP, FR-13, LK-FAKEPH, LK-FW/ZW, LK-PCT-PLAIN, LK-KIND, LK-BUNDLE, LK-CARD; LK-TAG a/b passes, UNVERIFIED against P1b code; LK-ENT-VAL-PH passes under the F6 reading. Each named mutant killer kills (caveats F6, F7, F12); M57-M59 have killers.
- NOT CHECKED: evidence.py 85-110 and 169-220; tools.py 498-513 and 645-647 beyond names; whether `_scrub` is case-insensitive (LK-HANDED-UP); P1 PENDING LEAD 31/34/44 text; whether "unique search string" means P1's meta-test (g).
