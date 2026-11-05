# Memo 1 (P0e item 1): which text fold is the base for `guard/textnorm.py`

Author: research-and-test agent (Sonnet 5.5), 2026-11-05. Status: DRAFT for `egm:egm-review-loop`; I do not rate it final.
Evidence: `egm\hadavin-sdk\core-complete\p0e\text\compare.py` (run on Python 3.13.3, Unicode 15.1.0), raw output `...\text\compare-output.txt`, copies of every variant in `...\text\variants\` (read-only copies; no original touched). `dump_cp.py` is a small helper for the cross-interpreter check.

## 1. Answer in four lines

1. **Base = PR #50's `textnorm.py` + `_confusables.py` (table generated from Unicode UTS #39 data).** On my corpus it is a superset of PR #49's fold except one case-order bug (below), and it is the only one that has the DENY/ALLOW API (`fold_key`, `same_person`, `allow_equal`, `has_mixed_script`).
2. **PR #49's textnorm is dropped** (92-letter hand table, fewer catches: 239 vs 247 of 274 attack pairs; no `fold_key`). Keep nothing from it except `mixed_script` is already covered by `has_mixed_script`.
3. **PR #50 alone is NOT enough.** Six gaps must be closed before it can replace every copy (section 5). The biggest: (a) a case-order bug (114 code points are not idempotent), (b) unassigned code points are deleted, so a look-alike from a newer Unicode vanishes instead of folding, (c) no decoding of hidden tag characters, (d) no dash/slash/quote tidy-up for ids, (e) no "spaced" view, (f) the stored key does not record the Unicode version it was made under.
4. **Three named views, not one function,** are needed by the consumers (section 6). One key cannot serve identity, scan and display.

## 2. Variants found and facts

All "sha" are sha256 prefixes of the file I copied. Lines = file lines.

| Variant (where) | sha | Lines | What it is | Table |
|---|---|---|---|---|
| PR #50 `guard/textnorm.py` (`origin/pr/50` 2e8a28c; local `pr50b3-local` 748849c is byte-identical) | fd9d0ffdbe7d | 181 | NFKD, drop Cc/Cf/Mn/Me/Zl/Zp/Co/Cs/Cn + 5 fillers, NFKC, spaces, digits to ASCII, table, casefold. API: `fold`, `fold_key`, `squeeze(loose)`, `same_person`, `allow_equal` (4 verdicts), `names_equal`, `has_mixed_script` | `_confusables.py` sha 41740c11734e, 692 lines, 677 entries, from UTS #39 `confusables.txt` v18.0.0 (sha 6ed3ee96...), small-caps names read with Python's Unicode 15.1.0; generator `tools/gen_confusables.py` (129 lines) |
| PR #49 `guard/textnorm.py` (`origin/pr/49` cd62212; `-r8-b` same) | c1f9a17756ab | 131 | same pipeline; API: `fold`, `squeeze`, `safe_equal`, `confusable_not_equal`, `mixed_script` (5 scripts only) | hand table, 92 letters |
| apexc `src/apexc/textnorm.py` | 1a0574b4c175 | 181 | = PR #50 | = PR #50 table (same sha) |
| dealdesk `core_copy/textnorm.py` | 1f1c482fed85 | 181 | = PR #50 | same |
| refunds `core_copy/textnorm.py` | 88f432215cb6 | 181 | = PR #50 | same |
| Intake `core_copy/textnorm.py` (df5-a12 and intake-wp3 identical) | 31220ff0f63f | 172 | OLDER revision of PR #50 | same table |
| Intake `confusables_data.py` + `tools/gen_confusables_wp3.py` (wp3 and a12 identical: e744c5b86916) | dc9ee35ff5a8 | 133 / 96 | own generator, same UTS #39 v18.0.0 file, 1,582 single-letter entries, lower-cased, no supplement, no filter for "can it fire" | used only in `invoicecheck._f` |
| Intake `invoicecheck._f` + `checks.fold` (not a textnorm file; imported live) | n/a | n/a | the Intake money-path fold: html.unescape, deletes default-ignorables, table before and after casefold, dashes, slashes, line breaks, tag-char decoding | merged table 1,704 |
| dealdesk `textnorm.py` wrapper | 2c1527bff731 | 45 | `views()` = (glued, spaced) both through the PR #50 fold; cached | via PR #50 |
| refunds `textnorm.py` wrapper | f60119e2c365 | 137 | `normalise`, `normalise_spaced`, `normalise_keep_marks` (no table), `skeleton`=`fold_key`, `hidden_text` (decodes tag chars), `text_ok`, `contains_marker` | via PR #50 |
| portal kit `hadavin_kit/textnorm.py` | 751a2dc79331 | 35 | NFKC + casefold + drop Cc/Cf + collapse whitespace. No look-alikes, no digits | none |

Facts that correct the inventories (checked by diff and by running):
- The demo "two hash versions" of PR #50 textnorm are **behaviour-identical**: apexc, dealdesk and refunds differ from PR #50 only on two docstring lines and the import line (0 output differences on the whole corpus). Real drift is only Intake's older copy: its `has_mixed_script` does not treat a newline as a word break, so "abc<newline>(Cyrillic word)" is flagged there and not in PR #50 (a false positive, fail-closed; probe in the output, section F).
- PR #49 and PR #50 are not rivals of equal rank: PR #50 is a later, larger design (generated table, ALLOW/DENY split).
- Import cost of the PR #50 module is about 20 ms (it builds a decimal-digit table over code points below U+20000 at import).
- The shared test vectors file `tests/fixtures/textnorm_vectors.json` is in PR #50 and PR #49, identical to apexc's copy.

## 3. What the script ran (and how to read it)

- **Corpus**: 274 attack pairs (attack string, plain twin it should read as) in 33 categories (homoglyph Cyrillic/Greek/Armenian/Cherokee/Coptic/fullwidth/math alphabets, digit scripts incl. Arabic-Indic, Devanagari, math digits, N'Ko, supplier names, invoice numbers, IBAN, e-mail, 37 invisible/bidi/filler characters, tag chars, controls, NFC/NFD pairs, zalgo, ligatures, circled/super/subscripts, case oddities, whitespace kinds, unassigned/private/surrogate, dashes/quotes, amounts) plus **364 string literals harvested from the tests** of apexc, dealdesk, refunds, the portal kit and Intake (df5-a12) plus the shared vectors file. Total 719 distinct strings.
- **Catch matrix** (section B): per variant, did `key(attack) == key(twin)`. Totals of 274: PR #50 fold_key **247**, PR #49 **239**, Intake `_f` **232**, Intake `checks.fold` **201**, `squeeze(loose)` **268**, `squeeze` 260, kit `fold` **105** (no table), refunds `normalise` 139 (no table, by design).
- **Superset matrix** (section C): for variant R, count groups of strings that R makes equal and column C splits; 0 = C is a superset of R on the corpus. This tests equivalences only on strings in the corpus.
- **Timing** (section D): best of 3, up to 100,000 characters.
- **Cross-interpreter** (section E): fold of every code point under Python 3.13.3 (Unicode 15.1.0), 3.12.10 and 3.12.14 (Unicode 15.0.0).

## 4. Where each variant differs, and who is a superset

- **PR #50 vs PR #49**: PR #50 makes 9 groups of equivalences PR #49 misses (digit look-alikes such as U+01BC, small-capital letters, Cherokee, ligature AE, ...). PR #49 makes 1 equivalence PR #50 misses: Greek capital Sigma vs lower sigma (details in gap 1). Everything else PR #49 equates, PR #50 equates. So PR #50 is a superset of PR #49 **except gap 1**; with gap 1 fixed it is a superset on the corpus.
- **PR #50 vs the three demo copies**: identical behaviour (0 differences).
- **PR #50 vs kit `fold`**: 5 groups kit equates that PR #50 splits. All five are the same bug (gap 1): capital letter and lower-case letter of Eta, Nu, Upsilon, palochka and Sigma map to different Latin letters, so they do not compare equal after casefold.
- **PR #50 vs refunds `normalise`/`normalise_spaced`/`keep_marks`**: these equate strings differing only by control characters or line separators as a space (`a<NUL>b` ~ `a b`), which PR #50 treats as glued `ab`. This is not a missing equivalence in the table; it is a second view (gap 5).
- **PR #50 vs Intake `_f`** (9 groups) and **`checks.fold`** (7): Intake equates (a) dash variants and fraction/division slashes (`INV-2026` with U+2010, U+2212, U+2013, U+2014), (b) letter O and zero, capital I/l and one in ids ("loose"), (c) hidden tag characters decoded to the ASCII text they hide, (d) Cyrillic Ze with Latin z (PR #50 reads it as 3). Intake's other 1,582-entry data adds nothing live: 1,449 entries give the same result as PR #50; of the 133 that differ, 39 are changed by NFKC first, 45 are digits that PR #50 maps to digits (better), 49 are code points unassigned in Unicode 15.1 (gap 2).
- **Nobody is a superset of everyone.** Two disagreements are choices, not bugs: Greek capital vs lower letters pointing to different Latin letters (gap 1b), and Cyrillic Ze as 3 or z.

Smallest union needed: PR #50 + fixes for gaps 1 to 6. No part of PR #49, the kit fold or Intake's generated data is needed (Intake's generator is replaced by an improved PR #50 generator that keeps entries for currently unassigned code points).

## 5. Gaps to close in the base (each is a test that must fail on today's PR #50)

1. **Case-order bug (class bug).** The table is applied before `casefold`. A capital whose table entry is missing (Greek Sigma U+03A3, O-stroke U+00D8, Thorn U+00DE, D-stroke U+0110, L-stroke U+0141 ...) is lower-cased AFTER the table and ends up as a letter the table would have mapped. Measured over all of Unicode: **114 code points where `fold_key(fold_key(x)) != fold_key(x)`** (a key is not stable), 232 where `key(c) != key(c.casefold())`. A first fix (translate, casefold, translate again, repeat to a fixed point, as Intake `_f` does) takes non-idempotent code points to **0** and closes Sigma/O-stroke. It leaves 152 code points where `key(c) != key(c.casefold())`:
   - 1b. For Eta, Nu, Upsilon and palochka, capital and lower letter honestly look like different Latin letters (H vs n, N vs v, Y vs u, I vs l). A single key cannot make both equal without also equating Latin h/n/v. Needs a design choice (my recommendation, an ML-engineer/architect call for the lead): keep ONE stable identity key (casefix) and make the scan view test a set of keys (key before and after case, any overlap = hit). Do not make it transitive-silent.
2. **Unassigned code points are deleted, so a newer look-alike disappears.** `fold` drops category Cn before the table lookup, and the generator filters out entries that the running Python cannot fire. Result on Python 3.13: 49 UTS #39 entries (for example U+113D4 as l, U+1CCD6 as a, U+16EB6 as b) are lost, and `pаyp` plus such a character folds to a shorter word instead of to the Latin word. Fix: the generator keeps every MA single-source entry; `fold` applies the table to a code point BEFORE the Cn drop; the unassigned drop stays for the rest. Also test that a code point assigned in a newer Unicode still maps on an older Python.
3. **Hidden tag characters (U+E0020 to U+E007E) are dropped, not decoded.** PR #50 returns an empty key for a string that spells "approved" in tag characters; Intake `fold` and refunds `hidden_text` decode them to ASCII so the scan sees the hidden word. The scan view must append the decoded text (not drop it).
4. **No punctuation tidy-up.** Dashes (all Pd, U+2212 minus), fraction/division slashes and typographic quotes are left as they are: `INV-2026` with U+2010 is not `INV-2026` in `fold_key`. `squeeze` hides this (it drops punctuation) but then `1,000.00` equals `1000.00`, which is wrong for amounts; amounts must use typed fields (R171), not a fold.
5. **No "spaced" view.** Dropping format characters glues words (`ja<ZWSP>vascript` -> `javascript`); turning them into a space splits them. dealdesk and refunds both need both views for name scans and phrase scans. Make `fold_views(raw) -> (glued, spaced)` part of core; the dealdesk wrapper is the model (but it uses an `lru_cache(maxsize=65536)` keyed by strings up to 20,000 characters: up to roughly 1.3 GB in a worst case; bound it by total bytes).
6. **Stored-key version** (section 7).

Minor items seen: `has_mixed_script` flags a lone Greek delta glued to Latin (documented false positive); U+FFFD is kept; no ASCII-only look-alike handling (`rn` vs `m`, `vv` vs `w`: not equal, and out of scope on purpose); Devanagari vowel signs are dropped (documented over-collision, safe for a DENY, wrong for display).

## 6. Named views the consumers need

| View | Use | Built from | Exists in PR #50? |
|---|---|---|---|
| `identity_key(raw)` (DENY identity: names, e-mail, domain, separation of duties, blocklist) | stable stored/compared key | `fold_key` + casefix (gap 1) + table before the Cn drop (gap 2) | `fold_key` yes, fixes missing |
| `id_key(raw, loose=True)` (ids: invoice no., PO, IBAN, bank detail; alnum only, O/0 I/l 1/L swaps) | invoice/PO identity | `squeeze(loose=True)` + dash/slash fold + tag decode | `squeeze` yes, rest missing |
| `scan_views(raw)` (leak scan, injection phrases, name scan, marker scan) | many keys: glued, spaced, tag-decoded, key-set for case-ambiguous letters | `fold_views` + hidden-text decode | no |
| `allow_equal(a, b)` (ALLOW) | exact equality, verdicts EQUAL/VARIANT/LOOKALIKE/DIFFERENT | PR #50 | yes (keep as is) |
| `visible(raw)` (display / allow-list host: NFKC, drop invisibles, KEEP marks and exact letters, no table) | refunds `normalise_keep_marks`, `text_ok` | not present | no (refunds has its own) |

Rule to keep at the front of the module: `fold` makes look-alikes EQUAL, so it is for DENY and scans only, never for ALLOW or display (this is already PR #50's "THE RULE"; it fits R171 "free-text matching is evidence, not proof").

## 7. What the stored-key version (FOLD_VERSION) must cover

Measured: the same PR #50 code gives **different keys on different Python builds**. Fingerprint of `fold_key` over all code points: Python 3.13.3 (Unicode 15.1.0) `84d6fd604e2af2bf`; 3.12.10 and 3.12.14 (Unicode 15.0.0) `6d7186ffdd478ade`; **627 code points differ** (CJK and others that 15.1 assigned; 15.0 deletes them). So a key stored under one interpreter can silently stop matching under another. The version string must therefore hold, and a mismatch must force recomputation from the raw text (never a silent comparison):
- algorithm id (step order, drop-category set, fillers, digit range, casefix rule, view definitions);
- table data: UTS #39 version + sha256 + entry count, supplement list, name-rule generator version;
- `unicodedata.unidata_version` of the running interpreter (the Cn drop, NFKC, casefold, `isspace` and `isdecimal` depend on it), checked at import against the pinned value;
- the golden fingerprint (hash of the fold of every code point) is a CI test per supported Python, and the Python versions allowed for production are pinned in the repo.
Also decide: keys stored in a client database carry the version in a column; on a bump, re-key in the same migration.

## 8. Risks

- Merge order: demos pin byte copies; any change of the base changes keys. Do the version tag first (gap 6), then gaps 1 to 5, then re-pin the four demos (the three copies are already identical in behaviour, so the re-pin is a diff of docstring and import only; Intake needs the newer copy and drops `confusables_data.py` + its generator).
- Over-collision is by design for DENY, a false deny is possible (Devanagari example, Greek delta). Needs a documented false-positive list per consumer.
- Performance: all variants are linear. Worst case measured: 10,000 copies of U+FDFA (expands 18x to 180,000 characters) = 121 ms for PR #50 `fold_key`, 347 ms for Intake `_f`; 100,000 ASCII characters = 21 ms. Callers must still bound length (the module says so; dealdesk bounds at 20,000).
- Single-dependency audit: stdlib only at run time, the UTS #39 data is vendored and pinned (Unicode License v3 notice carried in the generated header). Lock-in risk is the interpreter's Unicode data (section 7); the alternative is a vendored `unicodedata` snapshot or the `unicodedata2` package behind the same interface; I did NOT test that alternative.

## 9. What the script did NOT cover

- No test of `egress_text.py`, `redact.py`, or any consumer code of the fold; only the fold functions and their wrappers.
- The harvested fixtures supply inputs, not expected outputs, so they show where variants differ, not which is right (the 335 of 364 that differ among five variants mostly differ by case/upper-casing style, e.g. Intake `checks.fold` upper-cases).
- Only Unicode 15.0 and 15.1 interpreters were available; Python 3.14+ (Unicode 16+) was not run, so the gap-2 fix cannot be proven on a newer Python here.
- Twins in my corpus are my judgement. Two twin mistakes of mine were fixed before the final run (Cyrillic en is read as H in the table; a Hebrew twin had a space). ASCII-shape pairs (`rn`/`m`, `vv`/`w`, `I`/`l`, `0`/`O`) and amounts are listed in the matrix as expected-not-equal under `fold_key`; they appear as "missed" in the totals.
- No fuzzing, no property-based run beyond idempotence and case checks over all code points; no memory measurement; no multi-threaded import test; no check of the generator output being reproducible (it needs the vendored 763 KB data file; not re-run).
- Not run: the demos' own test suites against the proposed fix. The "casefix" in the output is a prototype inside `compare.py`, not a patch.
- Unicode normalisation of the IBAN/bank-detail "format" (checksums) is outside textnorm.

## 10. Bible rules used

No bible rule is about Unicode folding; I searched `bible\RULES.md` for fold, normalis, look-alike, homoglyph, NFKC, invisible, zero-width, confusable, bidi. Nearest rules, cited as context only: **R143** (re-test exact-token search with look-alike ids), **R171** (free-text number matching is evidence, not proof; typed fields decide), **R354** (fail closed), **R197** (reduce injection damage: filter output), **R228, R230, R233** (redact before the model; prove it; regex redaction always on). Gap: the bible should get a rule that a fold key carries a version (section 7); that is the lead's call.

## 11. Per brief rule 12 (report summary for the lead)

Done: variants extracted, compared, memo written. Not done: nothing deferred inside the brief; the open choices are for the lead (gap 1b key-set vs single key; Ze as 3 or z; unidata pinning). Next EGM step: `egm:egm-review-loop` on this memo.
