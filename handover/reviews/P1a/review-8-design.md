# PR 63 (P1a, fix7 head bf955e9) round 8 design review (fresh read-only reviewer)

Saved condensed from the returned report; paths scrubbed. The reviewer ran nothing (Read/Grep/Glob). Verdict: NO Blocker; 2 Major, 4 Minor, 3 Nit.

Read: textnorm.py (1-135, 255-740), tests/test_textnorm.py 2270-2510, test_textnorm_differential.py:281, CHANGELOG 500-545, the first 648 lines of the diff, evidence logs in reviews/P1a/fix7/ (fail-before, mutants, greps).

## MAJOR-1 same-script insertion still hides a script value (textnorm.py:460-474 `_script_view`, 594-603 `value_scripts`, tests/test_textnorm.py:2305)
Value "密码测试" (4 Han characters), text "密的码测试": the inserted Han character keeps the script view "密的码测试", `squeeze_views` is empty, the spelling view has the extra character, so no view finds it. The fix7 test pins this as the documented limit for Chinese, Hindi, Thai, Arabic, Hebrew. The limit is stated in the module docstring, `fold_views` docstring and CHANGELOG fix7 ("Limits, stated plainly"); no contradicting sentence found. But it is a known, trivially exploitable evasion on a redaction path and `.claude/rules/fix-dont-defer-be-honest.md` calls a documented limitation a defect. No cheap fix: (a) a one-inserted-character matcher for script needles (window one longer matching with one deletion; linear for k=1, P1b work) or (b) a written owner decision that script values get only separator-insertion and foreign-script protection. Either must be stated in the P1b brief and the lookalike-leak design (not found there by grep). A respelling of the same value (Hiragana vs Katakana, Traditional vs Simplified) is also not covered.

## MAJOR-2 default `scripts=frozenset()` is silent and fail-open (textnorm.py:606-631, docstring 622-624)
A call site that forgets `scripts=value_scripts(value)` gets no script view; `scan_needles` still returns script needles, so separator-, ASCII- or foreign-letter-inserted copies of a Chinese, Hindi or Thai value are missed while plain copies are still found, so a smoke test would not notice. "Visible in the tests" does not protect the next caller. Fix: make `scripts` a required keyword for scans, or one choke point (`scan_views(text, value)` or `scan_needles` returning (needles, scripts)) that P1b is told to use. State the cost: one text pass per distinct script set, about 0.7 s each at the cap.

## MINOR
1. The minimum floor is only 1 (`_validated_minimums`, 642-655): SQUEEZE=1 or SCRIPT=1 is accepted; tests try 0, -1, bool, float, str, None, never 1. Fix: per-kind floors (squeeze and script at least 2, preferably 3+) and a test that sets 1.
2. The minimum is per view, so a mixed look-alike value is fragmented then refused (673-699): Cyrillic "Ольга" folds to `oльгa`, squeeze view "OA" (2), script view "льг" (3), neither reaches 4, `ViewTooShort` for a 5-letter value. Fail-closed but not documented as a cost for Cyrillic/Greek; the offered fallback (caller's own exact search) is the weak search. Document it or define the minimum on the combined skeleton.
3. Mixed value with a short ASCII part ignores the script part (676-699): "密码2024": script view "密码" is 2 (< 4) and `ideographs_only` is false because of the squeeze view "2024", so the script view is dropped; the only proof needle is "2024", which over-redacts every text containing it, and "密码20a24" (ASCII letter in the digit run, Han intact) is missed. CHANGELOG's "mixed values over-match" omits the under-match. Consider a higher minimum for digit-only squeeze needles or requiring the script part when it has 2+ ideographs.
4. New tests fail on 2ff0afe for the wrong reason (fail-before.txt): 17 of 20 fail with AttributeError (`value_scripts`/constants missing) rather than behaviour; `test_the_pin_message_names_every_accepted_spelling...` (test_textnorm_differential.py:281) passes on old source (`_pin_violation` is in the test tree); Arabic/Hebrew rows sit inside the shared loop. The mutant list gives behavioural cover: 128/128 killed on py312 and py313 with named killers (mutants-py313.txt:95-130); killers' pinning by the meta test not checked beyond its name.

## NIT
1. UNNAMED covers more than one thing (U+17000, U+18D00 pinned UNNAMED; Tangut components have names so a Tangut value splits across groups; docstring says only "Tangut ideographs").
2. The 9-view bound holds by construction (3+3+3); highest found is 7; P1b bound 9+6+8 only with scripts.
3. `loose=True` can change `ideographs_only` (squeeze views loosened first); harmless.

## Round-7 items vs the code
MAJOR-A closed for foreign scripts, open for same-script (MAJOR-1). MAJOR-B closed (minimums SPELLING 2, SQUEEZE 4, SCRIPT 4, IDEOGRAPH 2) but floors unenforced (MINOR-1) and fragmentation (MINOR-2). Round-7 MAJOR-1 (false "marks stay" docs) closed. MINOR-C (lone exact needle) closed (`proof` flag, mutants 125-127). MINOR-D/E closed (Arabic/Hebrew in SCRIPT_VALUES), MINOR-3 adds a shape. `scan_needles` perf test added (test_textnorm_perf.py:148; 37 perf passed; not re-timed). MIN_VIEW_CHARS validation added but floor low. CHANGELOG history marked superseded.

## Evasion summary
Found: foreign-script letter, ASCII letter, separator, mark, look-alike that folds to ASCII (code and the Han sweep of 1M+ code points). Not found: same-script letter, respelling (MAJOR-1). Refused (fail-closed): value shorter than the minimums (evadable if the caller uses its own exact search). Documented: Latin samekh case. Foreign-letter tests exist for five scripts; no all-code-point sweep beyond Han.

## Judge logs
py312 11095 passed. py313 not-live-not-perf 11058 passed; the full py313 run showed one timing flake (`test_lexer_is_linear`) and Postgres-only failures without a DSN (outside P1a). Postgres-DSN run not yet read.

## Not checked
No test, mutant or timing run. Not read: `_confusables`, generator, golden hashes, manifest/CHANGELOG sha256, test diff beyond the main tests, `tests/textnorm_mutants.py` beyond a count, Hindi/Thai test bodies, the lookalike-leak design in full. Not verified: Python 3.12 (Unicode 15.0) behaviour, Tangut/UNNAMED claim, Unicode-name assertions, Cyrillic/Greek fragmentation with real table data (inference).
