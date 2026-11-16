# Look-alike leak design, round 10, correctness review (draft 10, commit 8cc31a9)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-codebase-details`, read-only, nothing run, did not read `reviews/`. Read LEAD-ORDERS 8, 11-15, amendments, P1.md rev 14, P2d.md rev 5 and the snapshot. Every trace UNVERIFIED. Commit shas unverifiable (not a git repo for the reviewer).

Verdict: no Blocker, 6 Major, 10 Nit.

## MAJOR

- **M-1 LK-KIND-NUM second input inconsistent (design line 109).** The id is 4/4/4 = 12 digits; "five groups of 2" is 10 digits; six groups of 2 with spaces is 17 characters, PHONE's maximum is 16. PHONE matches "12 34 56 78 90" and leaves the last 2 digits clear, so the key still holds the 12-digit needle with e = 0: REFUSED, not "masked whole". "Spaces (4-4-4 groups)" mixes space and hyphen. Fix: give the exact input string and expected mask or refusal; use a 3x4 spaced form (AADHAAR/PHONE mask it).
- **M-2 Nothing covers the truly empty UNFILTERED key list (lines 46, 84, 127, 128).** FR-44 uses a non-empty list whose keys are all under 8; M60/M61 cover the filtered list. `scan_keyset(O) == frozenset()` is reachable (a punctuation-only or invisible-only stored value). Bare `min()` would raise ValueError. Fix: FR row (V copy plus the token of a punctuation-only stored value: NOT refused) and a mutant (bare `min`, M63) with a named killer.
- **M-3 "Caught by nothing" contradicts line 25 (lines 9, 137(8), 159).** `tools.py` 744-759 `_secret_forms` scrubs hex and base64 spellings of a handed-out secret. P1 rev 14 (PENDING LEAD 46, relay 1) asks for the narrower text; the design does not take it. Fix: add the handed-secret exception or flag to the lead.
- **M-4 Self-refusal letter list reads exhaustive but is not (lines 2, 9).** Greek Gamma, Sigma, Omega and Cyrillic Б, Г, Ш also have two readings (per `_confusables.py`). Fix: write "include" and add them.
- **M-5 P-1's decision rule skewed by its own corpus (lines 133, 139).** The 40 Greek/Cyrillic texts count in the per-kind rates behind the 1-in-200 rule; 3 or more self-refusals among them push NAME/ADDRESS OUT for all clients. Fix: decide on the non-Greek/Cyrillic texts; report per-script rates separately; or ask the lead.
- **M-6 The M62 killer may not kill (lines 46, 127, 128).** If the mutant repeats put-back to a fixed point and also tallies the nested V placeholder, e for V's key is 1 and FR-45 passes. Killed only if e counts first-pass placeholders only. Fix: say so in item 3, or add an input where the nested put-back changes the count.

## NIT

- N-1: design cites P1 rev 11/13; rev 14 is on disk. Line 8 omits Lm step 1b and the final Lm drop; no modifier-letter/tatweel row; P-1 corpus has no Japanese or Arabic; key-length rule should say Lm no longer counts; PENDING LEAD 46 and 47 and the GOLD-1 jamo exclusion not taken.
- N-2: RES-1 is a sibling bullet in P1 (line 64), not under "P1b: other" (line 137(6)).
- N-3: LK-UNFOLD third input ambiguous (line 112); the `InputTooLarge`-from-`undo` path is isolated only by an entity-encoded input such as repeated `&#65018;`.
- N-4: FR-41 input (c) ambiguous (line 127); use several placeholders each within the cap.
- N-5: "8,008-key comb" and "nested-chain keys" in FR-8 are stale phrases (P1 allows at most 8 keys).
- N-6: P-1 corpus size ambiguous (200+100+100 = 400, +50 = 450; near-cap texts inside or extra?).
- N-7: line 51 claims straddling handed-out secrets leave their front clear; false for plain copies (`error_reason` scrubs first, tools.py 999-1002).
- N-8: "benign near-cap 2.6 to 4.0 s" omits the 7.2 s `curl -u` entry; REDACT_BUDGET_S comment says wall-clock but budget is thread CPU.
- N-9: `_seeded` cites differ across drafts (54-57 vs 51-55); 51-55 is correct.
- N-10: commit shas unverifiable.

## Verified correct (summary)

Counts: 46 table lines (79-124) = 44 single + 2 triple-id lines = 50 ids, plus GOLD-1; strict xfail 11 (+2 if outcome OUT); FR rows 39 (46 - 11 absent + 2 + 2); mutant names 65 (M1-M62 + M9b, M18b, M18c); deleted 22; live 43 (41 + M18b + M18c; 41 in P2d-2, M41 and M44 in P2d-2b); LKV 1-18 minus 11 and 13 = 16 open; PL-LK 1-56 present. Chance-match arithmetic and "2.4 billion / 100 million" correct. `_COMMON` words at most 10 characters. Traces FR-43, FR-44 (M60 killed), FR-45, FR-46/LK-TAG-PB (M61 killed), LK-PART, M57-M59, `\0seed`/FR-13 hold. Snapshot cites in redact.py, runmap.py, textnorm.py, channel.py, tools.py, defaults.py match. `LookalikeCopy` must be added to the `except (InputTooLarge, TooDeep)` tuple at runmap.py 522, else line 524 turns it into a plain `RedactionError`.
