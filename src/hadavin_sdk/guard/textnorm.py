"""The shared text fold, for any place that compares or scans text for a protected value.

A kind or demo that needs a check name or a scan imports ``identity_keys`` / ``could_be_same_person`` / ``scan_holds`` from
here instead of keeping its own table. The public names are listed once, with one line each, under "THE PUBLIC NAMES" below.
Do not use ``fold`` to display or store text: it drops the non-spacing marks (category Mn: the breve of Cyrillic short i, accents, the
Hindi and Thai vowel signs that sit above or below a letter) and so over-collides, which is the safe side for a DENY. It KEEPS the spacing
marks (Mc: the Hindi vowel signs aa and i, visarga), the modifier letters (Lm, kept or read as the letter they look like) and the modifier symbols (Sk); see "MARKS AND SCANS" below.
The DENY check (``identity_keys``, ``could_be_same_person``) DROPS those three kinds in one of its readings, so it still matches two names that differ
only by such a mark.

WORDS (one word, one meaning). A SPELLING VARIANT is one of the at most three ways one text is read (see "SPELLING VARIANTS" below). A CHECK
NAME is the comparison text made from one spelling variant of the raw text or of the raw text with its spacing marks, modifier letters and modifier
symbols removed (see "MARKS AND SCANS"); the function names say "key" (``identity_key``, ``key_tag``) and mean the check name. A VIEW is a text that a
scan looks through: a spelling variant returned by ``fold_views`` or ``squeeze_views`` (also the same spelling variant with the spacing marks, modifier
letters and modifier symbols dropped, see "MARKS AND SCANS"), or a scan key of ``scan_keyset`` (``scan_views`` lists them all). "Same person" in
``could_be_same_person`` means the DENY test returns True: the texts may be one person or a look-alike name, which is the safe side.
Nothing in v1 stores a check name: a package that must keep a person or an id for a later
comparison stores the RAW text under its own access rules and folds it again with the current ``identity_key``.

THE RULE (read before using ``fold``): ``fold`` makes look-alike text EQUAL. That is what a DENY decision wants (separation of
duties: "alice" and the Cyrillic-a "alice" may be the same person; a blocklist; a leak scan). It is WRONG for an ALLOW decision ("this
address equals the verified address", an allowlist): folding there lets a look-alike address through.
  * ALLOW decision: ``allow_equal(a, b)`` is the WHOLE decision. EQUAL only for identical strings (``a == b``, no normalisation, so
    the text you verified is the text you use); VARIANT means a case, width, ligature or whitespace difference only (refuse); LOOKALIKE
    means the strings differ but fold to the same text through homoglyphs or invisible characters (a spoof attempt: refuse and audit it
    as such); DIFFERENT is an ordinary mismatch (refuse). The caller that wants
    case-insensitive domains lowercases the domain itself BEFORE comparing and uses the lowered text afterwards.
  * DENY decision: ``could_be_same_person(a, b)`` (built on ``identity_keys``, the SPELLING VARIANTS below, read with and without the spacing marks; it
    also answers True when either text holds a character this Python cannot name, see "UNNAMED CHARACTERS"). A scan for a protected value (a
    redaction, a blocklist) is ``scan_holds(text, value)``: it looks through every view of the text, BOTH ``fold_views`` AND ``squeeze_views`` (and
    the scan keys), and refuses a value it cannot scan (see "MARKS AND SCANS" and "THE DENY SCANS"). ``identity_key``, ``fold`` and ``squeeze`` give ONE
    spelling variant and are NOT DENY comparators or scans: one spelling variant is enough to be stable and to index, never to refuse. ``names_equal`` is
    neither: Unicode compatibility caseless equality for people's names in prose, no look-alikes.

``fold`` (stdlib only, linear):
  1. NFKD, so a base letter and its combining mark separate; 2. U+0345 becomes an iota after a Greek letter and is removed anywhere
  else (spelling variant (b) only; the other spelling variants always remove it, see SPELLING VARIANTS and U+0345 below); 3. drop control (Cc), format (Cf), non-spacing and enclosing mark (Mn, Me), private-use, surrogate and UNASSIGNED (Cn) characters, the
  invisible filler letters and U+FFFD (an unassigned code point that is a SOURCE of the look-alike table is kept for step 7 instead: gap 2; the
  table is the 15.1.0 one, so on the pinned interpreter there is none, but Python 3.12 has Unicode 15.0.0, where the code points added in 15.1.0
  are unassigned), EXCEPT that every whitespace character (``str.isspace``: space, tab, line feed, the line and paragraph separators
  U+2028 and U+2029, the no-break and ideographic spaces) is kept here and becomes a space in step 5; 4. NFKC; 5. every whitespace character becomes a space so words are never
  joined; 6. every Unicode decimal digit becomes an ASCII digit, every Unicode dash (category Pd) and the minus sign U+2212 becomes ``-``, the fraction and
  division slashes U+2044, U+2215, U+29F8, U+FF0F and U+2571 become ``/``, the typographic single quotes become ``'`` and the double quotes ``"`` (gap 4); 7. look-alike letters become the Latin letter or digit. Case is kept
  unless ``casefold`` is set (then ``casefold`` runs just BEFORE step 7, see below); ``collapse_ws`` squeezes runs of whitespace.

The look-alike table (step 7) is GENERATED from the Unicode UTS #39 ``confusables.txt`` MA table, version 15.1.0 (the Unicode version of the
pin; the generator refuses any other version), by ``tools/gen_confusables.py`` (pinned sha256, version and date in ``guard/_confusables.py``)
plus 16 explicit supplementary letters, one explicit override (the Cyrillic palochka U+04CF reads as ``l``, see the generator) and the
Unicode-name rules of the generator, all listed in the generator. NAME RULES COVER: small capitals, negative circled and negative squared letters, the crossed negative squared P, regional indicator letters, the squared small d, Latin letters with a stroke, hook or similar mark, and the circled, negative circled, double circled and sans-serif digits and numbers (0 to 10); the circled numbers 11 to 20 are read by NFKC, the negative circled numbers 11 to 20 are not read (a named gap). A look-alike letter that Unicode
listed only after 15.1.0 is NOT in the table. Runtime is stdlib only; the data file is not shipped. ``FOLD_VERSION`` names the fold that made
a check name. What is NOT read as an ASCII letter or digit is listed in ``tests/test_textnorm.py`` (``KNOWN_NAME_GAPS``) with the reason.

SPELLING VARIANTS (P1a fix3, review 3; alg ``fold4`` in P1a, ``fold5`` here: P1b changes what a check name can be, see the steps above). One spelling variant is not enough for a DENY: the same text can LOOK like two different words. A Greek
capital Eta looks like the Latin H, but the case-symmetric check name reads it as the small eta, which looks like n; a Greek letter followed by
U+0345 looks like the letter, but the iota rule reads it as the letter plus ``i``. So a text has a small FIXED SET of spelling variants (at most
three, never more; the number does not grow with the text), in this order:
  (a) the lower-side spelling variant: case folded first, the look-alike table of the case-fold image, U+0345 ALWAYS dropped;
  (b) the iota spelling variant: as (a), but U+0345 becomes an iota after a Greek letter. This is ``identity_key`` and ``fold``: it is what makes the
      precomposed Greek letters with ypogegrammeni case symmetric (see U+0345);
  (c) the upper-side (table-first) spelling variant: the look-alike table runs on the letter as written (capital Eta reads H, capital Mu M, capital Nu
      N, capital Upsilon Y), then case is folded, then the table of the case-fold image; U+0345 dropped.
``identity_keys(raw)`` gives the check names of these spelling variants of the raw text and, when the text holds a spacing mark, modifier letter or
modifier symbol, of the raw text with those removed (at most six check names, no repeats). ``could_be_same_person`` and ``allow_equal`` (LOOKALIKE)
compare check names: two texts match when ANY check name of one equals ANY check name of the other. A scan holds a protected value when ANY view of the text (``fold_views``, ``squeeze_views``) holds ANY view of the
value. The spelling variants only add matches to (b), so the relation is never narrower than ``identity_key`` equality; it is NOT transitive (capital Eta + "oward"
matches "howard" through (c) and "noward" through (a), and those two do not match each other), so it is never a unique index, a dedupe or a
group-by: use ``identity_key`` equality there, and outside tests only through an exemption (the ban table in ``pyproject.toml`` and the exemption list of
``tests/test_textnorm_meta.py``). The size cap is checked before any fold work; a public function that calls another checks again, which costs one more
length pass and changes no result.

IDEMPOTENT AND CASE-SYMMETRIC BY CONSTRUCTION (``identity_key``, ``could_be_same_person``, ``squeeze``; alg ``fold5``; the spelling variants (a) and (b)). The first order (table, then
casefold, with a table keyed by lower-case letters; alg ``fold1``) was neither: ``identity_key("\u00d8")`` kept the capital and ``identity_key("\u00f8")``
gave ``o``, so ``could_be_same_person("B\u00d8B", "bob")`` was False, a DENY bypass. Now, with P = NFKC after the drops after the U+0345 step after
NFKD, D = the digit table and C = ``casefold``: ``key(x) = tag + collapse(E(C(D(P(x)))))`` where E is the look-alike table MOVED ONTO THE CASEFOLD IMAGE
(``_CF_TABLE``): for every table entry whose source ``s`` has ``casefold(s)`` a single character, ``E[casefold(s)] = value.casefold()``;
when two sources reach one casefolded letter the entry of the letter that is its own case-fold wins over the entry of its capital
(11 letters, pinned by a test: e.g. Greek eta reads n, not the capital Eta's H; the spelling variant (c) gives the capital's entry, and
``has_mixed_script`` is a second backstop). The
argument: (1) CASE SYMMETRY: C is the only case-sensitive step, it runs before E, E has casefolded table keys only, so two texts that agree
after C agree in the check name; that ``C(P(c.upper())) == C(P(c.lower()))`` for every character is a fact about the Unicode data, which
``tests/test_textnorm.py`` checks for ALL non-surrogate code points (and for pairs built from the table, and for seeded random strings)
on every supported Unicode version, with the one stated exemption of U+0345 below. (2) IDEMPOTENCE: the image of E is lower-case ASCII; every other character of the result survived C and is not a check name of E
(the table keys of E are non-ASCII and casefold-stable, asserted), so a second C changes nothing and a second E changes nothing; that the
remaining steps (P, D, the drops) leave such characters alone is again a fact about the data, checked by the same tests. The final
form is therefore a fixed point of the whole function; a test that restores the old order fails. ``fold`` WITHOUT
``casefold`` keeps case and uses the raw table (no symmetry is promised for it); ``squeeze`` casefolds first.

U+0345 (COMBINING GREEK YPOGEGRAMMENI). Every other mark is dropped, and dropping is what
makes ``identity_key(x + mark) == identity_key(x)``. U+0345 is the one mark that cannot simply be dropped: its upper case and its case fold
are the letter iota, and a Greek letter with the mark (U+1FB3, alpha with ypogegrammeni) upper-cases to two letters (alpha, iota). Two
needs conflict: case symmetry (the check name of U+1FB3 must be the check name of its upper case, alpha iota) and mark insertion (the check name of
"admin" + U+0345 must be the check name of "admin"). The rule: U+0345 is read as an iota (U+03B9, then the table: ``i``) when the last kept
character before it is a Greek letter (an alphabetic character whose Unicode name starts with GREEK; characters the fold drops, such as other
marks or a zero-width space, are skipped when looking) and is REMOVED everywhere else (after a Latin or any other letter, after a space,
at the start). It happens on the NFKD text, so the precomposed U+1FB3 and alpha + U+0345 get one check name (``ai``). ``fold2`` (the first
order-fixed fold) case-folded the raw text before the drop step, which turned U+0345 into an iota everywhere ("admin" + U+0345 gave ``admini``, a DENY
bypass); ``fold3``, ``fold4`` and ``fold5`` have no early case fold (it is redundant once U+0345 is handled by name: 600,000 random strings gave the same check name
with and without it). Chosen for the SINGLE check name over "always drop" because always dropping breaks case symmetry for the precomposed Greek letters with
ypogegrammeni and for Greek text in capitals (U+1FB3 against alpha, iota in capitals), while this rule breaks nothing on them. But the single
check name alone is not safe: a Greek look-alike plus U+0345 ("alpha U+0345 dmin") reads as ``aidmin``, one invisible mark away from
"admin", and a run of marks gives a run of ``i``. The spelling variants fix it: (a) and (c) ALWAYS drop the mark, so for ``could_be_same_person`` and for every
scan "a Greek letter + U+0345" matches the letter, whatever follows, and the iota spelling variant (b) is kept for the case symmetry above.
What the single check name does NOT promise, both stated and tested: (1) after a Greek letter the mark is an iota, so ``identity_key(alpha + U+0345)``
is not ``identity_key(alpha)`` (the one "base + mark" pair that differs; ``could_be_same_person`` of the two is True through (a)); (2) a text that holds
a U+0345 with NO Greek letter before it (dropped characters skipped) is not case symmetric, because ``str.upper`` turns the mark into the
letter Iota while the fold removes it (``identity_key("ͅ")`` is ``""``, ``identity_key("Ι")`` is ``i``): the symmetry tests exempt
exactly that shape, nothing wider. No other code point is exempt from idempotence, case symmetry or mark insertion. ``fold`` without
``casefold`` applies the same step.

ONE PASS PER SPELLING VARIANT FOR THE CHECK NAMES, A BOUNDED LOOP FOR THE SCAN KEYS (P1a fix3 removed ``defaults.TEXTNORM_MAX_PASSES`` because
nothing read it; P1b adds it back with its reader and ``FoldNotConverged``): ``fold``, ``identity_key`` and ``identity_keys`` are one pass per
spelling variant; the idempotence above is by construction and by test, not by iterating. ``scan_keyset`` runs each of its two spelling
variants (A: table first with U+0345 dropped, B: case fold first with the iota rule) to a fixed point in at most
``defaults.TEXTNORM_MAX_PASSES`` passes (the confirming pass included) and raises ``FoldNotConverged`` otherwise; no code point needs more
than 2 changing passes plus the confirming one (capital Sigma on variant A; a test records the maximum).

THE DENY SCANS (P1b). ``scan_holds(text, value)`` is the one scan; its views are in ``scan_views(text, value)``: ``fold_views`` (case folded,
whitespace collapsed, with the script views of the VALUE), ``squeeze_views`` and ``scan_keyset``. It is True when ANY view of the text holds ANY
needle of the value (or a script needle with one extra letter of its own script, see "ONE INSERTED LETTER"), so a secret hidden with a spacing
mark is found through the squeezed views and the scan keys, which ``fold_views`` alone misses. ``scan_keyset`` (at most 16 keys: 2 spelling variants
x the tag texts T0 to T3, x2 for a text that holds a spacing mark (Mc) or a modifier symbol (Sk)) is made of letters and digits only, with the class maps
``z`` to ``3`` (Cyrillic Ze) and ``l`` to ``i``, modifier letters (Lm) removed from the raw text, and no escape decoder; a text that holds an Mc or an Sk
has the keys of the text as it is AND of the text without them (a few of them are look-alike letters: U+0C02 reads ``o``). ``could_be_same_person``
is NOT widened by the scan keys (the spelling variants of P1a are the whole name test; the ticket's erratum BN-20 says "not widened in P1b").

THE PUBLIC NAMES (33, pinned by ``tests/test_textnorm.py``; ``__all__`` is sorted). Errors: ``TextnormError`` (base, not a ``ValueError``),
``TextTooLong``, ``NotText``, ``UnidataMismatch``, ``FoldNotConverged``, ``EmptyView``, ``ViewTooShort``, ``CoverageRefused``. Check names (DENY and ALLOW):
``identity_key`` (one spelling variant), ``identity_keys`` (all), ``could_be_same_person``, ``allow_equal`` and ``AllowVerdict``, ``names_equal``
(prose only), ``fold`` (one spelling variant), ``squeeze`` (letters and digits only), ``key_tag`` and ``FOLD_VERSION`` (which fold made a check
name), ``FILLERS`` (the invisible filler characters). Views and scans: ``fold_views``, ``squeeze_views``, ``scan_keyset``, ``value_scripts``,
``scan_needles``, ``scan_views``, ``scan_views_no_value`` and ``scan_holds`` (the one scan), ``scan_cache`` (the only place where the views of a text are kept). Registration of a protected value: ``register_value`` and its result ``Coverage``. Signals: ``has_hidden_channel``, ``has_mixed_script``. Guard:
``require_pinned_unidata``. Everything else starts with an underscore. Two scripts systems exist on purpose: ``has_mixed_script`` asks "does a
word mix Latin with another writing system?" with the Unicode Script property of the pinned data (``guard/_scripts.py``, UTS #39 wants that one);
the script GROUPS of ``value_scripts`` ask "which letters may a person insert into this value without changing what it is?" and are the first
word of the Unicode name (Han, kana and the old variant kana merged; Hiragana and Katakana are two scripts in the first, one group in the second;
a letter with no name is the group UNNAMED, which holds more than one thing: the Tangut ideographs (U+17000 and on) and U+18D00 and on are pinned as unnamed on 3.12 and
3.13, while the Tangut COMPONENTS have names, so a Tangut value can split across groups; the closing mark U+3006 is its own group). Neither feeds the other.
The first word is not a script: U+2132 gives "TURNED" and U+2183 gives "ROMAN" (harmless for an insertion; found by hand, not by a machine sweep, that no
other first word covers two real scripts).

UNICODE DATA VERSION: the fold depends on the interpreter's Unicode data (which characters are unassigned, which are marks). The pinned version
is ``defaults.TEXTNORM_PINNED_UNIDATA`` (15.1.0). PRODUCTION AND PILOT MUST RUN PYTHON 3.13.x (Unicode 15.1.0); Python 3.12 (Unicode 15.0.0)
is for demos only. Python 3.14 (a later Unicode version) has NOT been checked: the pin guard refuses it for pilot and prod, and the unnamed-letter rule and the golden hashes were run on 3.12 and 3.13 only.
Moving the pin to a later Python (for example 3.14) is a DATA MIGRATION: new look-alike data, new golden hashes, a new
``alg``. Nothing here checks the version until a caller calls ``require_pinned_unidata()``. ``require_pinned_unidata()`` is the guard entry point: it raises ``UnidataMismatch`` (fail closed)
when the interpreter's version is not the pin; pilot and prod code calls it before using any check name (``app.build`` does, for pilot and prod). On another
interpreter (a demo run, or a CI run on Python 3.12, which has Unicode 15.0.0) the functions still run, and every check name then starts with
``key_tag()``: U+E000, ``alg=fold5|ud=<this interpreter's version>``, U+E000. U+E000 is private use, which the fold
always drops, so no check name made on the pinned version can ever start with it: a check name made on another version never equals one made on the
pinned version, and two other versions never equal each other. On the pinned version the tag is empty (the bare check name IS the check name of
``alg`` ``fold5``; changing the pin bumps ``alg``). ``identity_key`` of a text that already starts with the tag of this interpreter
removes it first, so the function is idempotent there too. The cost, stated and tested: a RAW text that starts with the tag of THIS
interpreter (typed exactly, U+E000 included) has the tag stripped and so gets the same check name as the text without it (an over-collision,
the safe side of a DENY); a text that starts with the tag of ANOTHER version is not stripped (its tag text becomes part of the check name). A
caller that did not call ``require_pinned_unidata()`` (``app.build`` does in pilot and prod; a demo or a test may not) gets tagged check names on every
interpreter whose Unicode data is not the pin, for example Python 3.12; such check names compare only with check names made on the same version.
A vendored copy of the Unicode character data (instead of the interpreter's) becomes the alternative when a deployment must run a Python
whose Unicode version is not the pin and cannot be changed.

MARKS AND SCANS. Three categories are NOT dropped by the spelling variants of ``fold``, on purpose, and a caller must know it:
  * Mc (spacing combining marks, 452 code points in Unicode 15.1.0, for example the Devanagari vowel signs aa and i): a spacing vowel sign
    changes a name, so the spelling variants and ``fold`` keep it. "ad" + U+0903 + "min" is NOT the spelling-variant check name of "admin" and the
    spelling-variant views of ``fold_views`` of "pass" + U+093E + "word" do NOT hold "password"; but the DENY check IS true for "ad" + U+0903 + "min" and
    "admin" (``identity_keys`` also holds the check name of the text with the mark removed), so a person must look. This is the cost of the
    ORDER 177 decision (a reversal of the earlier rule that a spacing vowel sign changes a name): on made-up Hindi names (94 names, 4,371 pairs) two
    pairs are now "could be the same person" (0 before) and on Thai names one (unchanged); the rate on a real population is not known.
  * Lm (modifier letters): a look-alike of the letter (superscript h reads as h), kept or read as that letter.
  * Sk (modifier symbols): a compatibility Sk (NFKD gives a space plus a mark: the diaeresis U+00A8, the small tilde U+02DC) becomes a space in
    the spelling-variant views; every other Sk (the grave accent U+0060, the circumflex U+005E, the arrow head U+02C2) is kept as the symbol. ``squeeze_views`` removes both.
  So that a mark inserted into a protected value cannot hide it, ``fold_views`` and ``squeeze_views`` return, besides the spelling-variant
  views, the same views built from the text with every Mc, Lm and Sk character REMOVED BEFORE the first normalisation and before the
  look-alike table (so an Lm or Mc that the table or NFKC would read as a letter is gone too: "pass" + U+0C02 + "word" holds "PASSWORD"). Every
  other drop (Mn, Me, format, control and the rest) already applies to every view. These marks-dropped views keep every script and every letter.
  "No exemption" holds for INSERTION only: a mark ADDED to the value is found for every Mc, Lm and Sk code point, with no exemption list. It does
  NOT hold for a modifier letter that REPLACES a letter AND another one inserted in the same text ("pa" + superscript s + "s" + superscript h + "word": the
  marks-dropped views lose the letter that the first modifier stood for, the other views read the inserted one as a letter): that mixed case is
  NOT caught, it is pinned as a limit by a test, and a caller who must catch it needs its own rule.
  At most six views per call of ``squeeze_views`` (three spelling variants, each with and without the marks); ``fold_views`` adds the script views below
  when it is given ``scripts``, so at most nine.
  A caller that must cut the ORIGINAL text at the place a view found a value (the redactor) builds the views one by one with ``fold_view(raw,
  marks_dropped=..., iota=...)`` (``fold_view(raw)`` is ``fold(raw)``; without ``casefold`` the two switches name every view ``fold_views`` returns),
  drops the marks of a text of its own with ``without_spacing_marks``, and reads ``SPACING_CATEGORIES`` (Mc, Lm, Sk) instead of keeping its own list.
  THE RULE FOR A SCAN (redaction, blocklist, has-secret): call ``scan_holds(text, value)``. It looks through BOTH the ``fold_views`` AND the
  ``squeeze_views`` of the text (and the scan keys), reads the text with the scripts of the VALUE (``scan_views(text, value)`` takes them from the
  value itself, so a caller cannot forget them), and takes the needles of the value with ``scan_needles``, which refuses a value without a long
  enough squeeze or script view (see "MINIMUM VIEW LENGTH"). ``fold_views`` is not a scan: it takes ``scripts`` as a REQUIRED keyword (pass
  ``frozenset()`` for none) so that a caller who builds its own scan has to decide, and its default is ``casefold=False`` for the display and
  comparison uses that keep case (a scan built without ``casefold=True, collapse_ws=True`` misses "Secret" against "SECRET"). ``tests/test_textnorm.py`` pins
  the insertion rule for EVERY Mc, Lm and Sk code point of the interpreter, for the scan views AND for the DENY check.
  WHAT A SCAN RELIES ON: A value with NO ASCII letter or digit (Chinese, Arabic, Hindi, Thai) is found by the script views of ``fold_views`` (the
  non-ASCII letters of the value's own scripts, with whitespace, punctuation, symbols, ASCII characters and the letters of every other script
  removed), so an inserted space, hyphen, line break, ASCII letter, mark or foreign-script letter does not hide it. One extra letter of the SAME
  script inserted into a script needle is found too, from a minimum length per script (see "ONE INSERTED LETTER"); two inserted letters, or a
  respelling of the value, are not covered.
  SCRIPT VIEWS (``fold_views`` with ``scripts``). The ASCII-only ``squeeze_views`` is ``""`` for a value in a script with no ASCII letter or digit, so
  ``fold_views`` also returns, for the marks-dropped spelling variants, the SCRIPT VIEW: the view with every character removed that is not a non-ASCII
  letter of one of the given scripts (whitespace, punctuation, symbols, ASCII letters and digits, the digits of other scripts that were turned into
  ASCII digits before, and the letters of every other script). ``value_scripts(value)`` gives the scripts of the VALUE: the script group of each
  non-ASCII letter left in the value's marks-dropped views. A script group is the first word of the Unicode character name (CYRILLIC, GREEK, HEBREW,
  ARABIC, DEVANAGARI, THAI, LATIN and so on; two words for the families that share a first word, such as OLD TURKIC and OLD ITALIC; the characters
  with no name, which are the Tangut ideographs and any other unnamed letter, are the group UNNAMED), with two merged families: every CJK ideograph
  is HAN, and Hiragana, Katakana and the old variant kana are KANA. So a Chinese value (HAN) is still found when a Cyrillic zhe, a Greek delta, a
  Hebrew alef, a kana or a Latin letter that the table does not read is inserted: those letters are not HAN and are dropped from the script view of
  the text, as an ASCII letter is. A letter of the SAME script (another ideograph in a Chinese value) is a different spelling: it is found only by
  the one-inserted-letter match. Only letters can stay: the digits and marks are gone before the script view is cut (Mn, Me, Mc, Lm, Sk, Cf, Cc and
  the rest are dropped or removed), so no mark is ever in a script view; a letter-like number (category Nl, for example the ideographic zero U+3007)
  is not a letter here, so it is not in the needle of a value that holds it and an inserted one is dropped. A view that would be empty is left out,
  and a script view equal to another view is not repeated.
  A caller reads the TEXT with the scripts of the VALUE. ``scan_views(text, value)`` and ``scan_holds(text, value)`` do it themselves; a caller of
  ``fold_views`` passes ``scripts=value_scripts(value)`` (the keyword has no default). With several protected values the scan reads the text once
  per set of scripts. The script view over-matches on purpose (the safe side): a value with ASCII letters AND a script has a script view of the
  script part alone, which any text with that script part holds, and two words of a text that end and begin with the value's letters match across
  a separator.
  TWO SCRIPT SYSTEMS, one by design: the script GROUPS above (first word of the character name, used for the script views and the insertion match)
  and the Unicode Script property that ``has_mixed_script`` reads (Latin mixed with Cyrillic, Greek and the rest). The first answers "which letters
  can an inserted copy be cut out with", the second "is this word a look-alike mix"; they are not interchangeable, and neither is derived from the other.
  MINIMUM VIEW LENGTH, one number per KIND of view (``defaults``; each is a whole number of at least 2, the floor, checked when this module is imported
  and again by every ``scan_needles``): SPELLING (``TEXTNORM_MIN_SPELLING_CHARS``, 2), SQUEEZE (``TEXTNORM_MIN_SQUEEZE_CHARS``, 4), SCRIPT
  (``TEXTNORM_MIN_SCRIPT_CHARS``, 4), IDEOGRAPH (``TEXTNORM_MIN_IDEOGRAPH_CHARS``, 2: for a value that is only Han ideographs, a name of two ideographs
  is scanned, one ideograph is refused) and DIGITS (``TEXTNORM_MIN_DIGIT_CHARS``, 6: for a squeeze view of ASCII digits only, a PIN or an account
  number; a short digit string is found in nearly every table of numbers). The ticket (P1) asked for 6 digits and the earlier build took 4: the
  ticket is followed. The cost, stated: a PIN of five digits or fewer is refused. An empty needle is found in every text and a short one in
  most, so ``scan_needles(raw)`` returns the views of a protected value that reach the minimum of their kind (from ``fold_views`` with
  ``casefold=True, collapse_ws=True`` and the scripts of the value, and from ``squeeze_views``). It raises ``ViewTooShort`` when no SQUEEZE or SCRIPT view
  reaches its minimum, even if a spelling view does: a spelling view keeps the separators, so one inserted space hides a value that only it can find
  (a three-letter name, "w" plus one ideograph). The cost, stated: a protected value of three letters or fewer is refused, and so is a mixed value
  whose script part is shorter than four letters; the caller looks for it with its own exact search. A caller that scans must use ``scan_needles``
  (no module of the SDK scans for a protected value through this module yet; the one that does must take its needles from it and not repeat the numbers).
  FRAGMENTATION, stated: a value whose letters the table reads as several ASCII letters (or digits) counts those, not the characters typed, so a
  value can pass with fewer characters than the minimum, and a value of the minimum length in a script the table does not read is refused if its
  script part is shorter than the minimum.
  THE COST FOR CYRILLIC AND GREEK, stated and measured (see the CHANGELOG): their letters are read as the Latin look-alikes only when they have
  one, so a short word of letters the table does not read stays a script needle of its own length, while a word of look-alike letters is a squeeze
  view of the same length; a short Cyrillic or Greek word is refused when fewer than four of its letters survive in either view. The examples are
  pinned in ``tests/test_textnorm_fixbatch.py``.
  ``scan_holds`` (P1b) takes its needles from ``scan_needles`` too, reads the text once per set of scripts with ``scripts=value_scripts(value)``, and
  also looks through ``scan_keyset``, which is made of letters and digits only; it lets ``ViewTooShort`` out (the caller REFUSES: a value too short to
  scan is never masked as "not found"). It raises ``EmptyView`` only when the value is too short AND has no letter or digit a scan can rely on
  (empty, invisible, punctuation or marks only; a lone spacing mark such as a Devanagari vowel sign is still EmptyView), so a Chinese, Arabic, Thai
  or Hindi value of enough letters IS scanned (the ticket asks for a scan of the script views, not a refusal). The match positions of the original
  text are lost by the drops: a caller that must cut the original text needs its own map.
  ONE INSERTED LETTER (``scan_holds``, ``defaults.TEXTNORM_INSERTION_*``): the exact match above cannot see a script value into which a letter of its
  OWN script was put ("密码测试" written "密的码测试": the inserted letter is not dropped from the script view). So ``scan_holds`` also looks, in the
  script views of the text, for each SCRIPT needle with at most ONE extra character between two of its characters. The match is bounded and
  linear for ordinary text: one half of the needle is always intact, it is found exactly with ``str.find``, and the other half is compared after
  skipping one character. The limits, each pinned by a test: a needle shorter than its script's minimum (``TEXTNORM_INSERTION_MIN_CHARS`` and
  ``..._BY_SCRIPT``) is matched exactly only, because "a?b" matches too many ordinary words; a needle longer than
  ``TEXTNORM_INSERTION_MAX_CHARS`` is matched exactly only (the worst case, a text made of copies of half the needle, costs the text length times the
  needle length); two inserted letters, a deleted letter and a changed letter are not matched; an insertion before the first or after the last
  character is not an insertion (the exact match holds it). A Latin value is not covered: its squeeze view is ASCII only, and a letter inserted
  into ASCII text is a different word to the squeeze view ("pasxsword"); that stays a limit.

WHERE ``could_be_same_person`` IS USED. It is a library primitive for the deny and check-name path only. It is wired into NO approval check, and no
approval compares people's names (``approvals/requests.py`` compares ids exactly). A use in an approval later is a new ticket with its own plan review
(a money and permission path, no round cap).

INPUT RULES (every public function): the argument must be a plain ``str`` (``type(x) is str``; a ``str`` subclass or an enum member is
refused with ``NotText``), its LENGTH must be within ``defaults.TEXTNORM_MAX_CHARS`` (``TextTooLong``, checked before any fold work: every weight is at
least the length, so a longer text is refused before any per-character work; a public function that calls another checks again, which costs one
more length pass and changes no result), and its WEIGHT W must be within the same cap. W is the sum, over the
characters of the text, of the longest string the pipeline makes from that one character (an ASCII text has W = its length). No check name
or view of any spelling variant is longer than W of its text (plus ``len(key_tag())`` on an unpinned interpreter), because every step acts per
character or only joins or drops. Messages hold lengths and constants, never the input.
Any ``TextnormError`` on a DENY or ALLOW path means REFUSE.

UNNAMED CHARACTERS (F6-5). The fold drops a code point of category Cn (unassigned on this Python), Co (private use) or Cs (surrogate). Dropped when
INSERTED into a name this over-matches (the safe side). When it REPLACES a letter ("al" + U+E000 + "ce" reads ``alce``) it would be a MISS: a
look-alike letter assigned after Unicode 15.1, or a private-use character drawn as a letter by a font, would hide the name. So ``could_be_same_person``
answers True when either text holds such a code point, and ``allow_equal`` follows (LOOKALIKE; identical strings stay EQUAL). Cost, stated plainly: a
name that holds an emoji newer than Unicode 15.1, or a private-use character, is "could be the same person" with EVERY other name, so a person must
look. The scan side (``fold_views``, ``squeeze_views``) has the same miss and is NOT changed here; it belongs to the packages that scan (the
redaction package and the hold check of P1b).

Honest limits: a letter in neither the data nor the supplement nor a name rule is not folded (the known cases are listed in ``tests/test_textnorm.py``). Dropping unassigned code points (Cn) depends on the
Python build's Unicode version (``require_pinned_unidata``): a look-alike letter assigned after Unicode 15.1 is DROPPED, not folded, on the
pinned interpreter (the DENY check fails closed on it, see above; the pinned-Unicode guard of ``app.build`` and a move of the pin close it). The table is the data of
Unicode 15.1.0, so look-alike pairs that Unicode added in later versions are not in it; the size of that loss has not been counted (it needs the later data file). The dashes, the
minus sign, the division slash and the typographic quotes ARE read as ``-``, ``/``, ``'`` and ``"`` (P1b, gap 4: "INV-2026" and "INV" + U+2212 +
"2026" are one check name). ``has_mixed_script`` is the fail-closed backstop: a word that mixes Latin
with Cyrillic, Greek, Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu, Runic, Tamil or any other non-East-Asian script is a deny signal whatever the
table knows (every script in the Unicode data except Common, Inherited and the East Asian scripts counts). Property: ``fold(x + mark) == fold(x) == fold(mark + x)`` for any non-spacing or enclosing mark (Mn, Me), format, private-use, surrogate or unassigned character that is not a table source (no unassigned code point is a table source on the pinned version) and any control character that is not
white space, with two exceptions: the one above (U+0345 after a Greek letter, for the single spelling variant (b) only) and a white-space control
(tab, line feed, vertical tab, form feed, carriage return, U+001C to U+001F, U+0085) or a line or paragraph separator (Zl, Zp), which becomes a
space (``fold("admin\\n") == "admin "``); ``identity_key``, ``squeeze`` and ``could_be_same_person`` are unaffected by those; for the spelling variants, any such mark, U+0345 included, leaves a shared spelling variant
(``could_be_same_person(x + mark, x)``). The property does NOT hold for a spacing mark (Mc), a modifier letter (Lm) or a modifier symbol (Sk) in the
spelling variants of ``fold``; the marks-dropped views of ``fold_views`` and ``squeeze_views`` hold it for those, and so does
``could_be_same_person`` (through the marks-dropped check names of ``identity_keys``).
"""

from __future__ import annotations

import bisect
import contextlib
import contextvars
import functools
import hashlib
import logging
import re
import sys
import types
import unicodedata
from collections import Counter
from collections.abc import Iterable, Iterator
from enum import Enum
from typing import NamedTuple

from hadavin_sdk import defaults
from hadavin_sdk.guard import _confusables, _scripts
from hadavin_sdk.guard._confusables import TABLE as _CONFUSABLES

__all__ = [
    "FILLERS",
    "FOLD_VERSION",
    "SPACING_CATEGORIES",
    "AllowVerdict",
    "Coverage",
    "CoverageRefused",
    "EmptyView",
    "FoldNotConverged",
    "NotText",
    "TextTooLong",
    "TextnormError",
    "UnidataMismatch",
    "ViewTooShort",
    "allow_equal",
    "could_be_same_person",
    "fold",
    "fold_view",
    "fold_views",
    "has_hidden_channel",
    "has_mixed_script",
    "identity_key",
    "identity_keys",
    "key_tag",
    "names_equal",
    "register_value",
    "require_pinned_unidata",
    "scan_cache",
    "scan_holds",
    "scan_keyset",
    "scan_needles",
    "scan_views",
    "scan_views_no_value",
    "squeeze",
    "squeeze_views",
    "value_scripts",
    "without_spacing_marks",
]


class TextnormError(Exception):
    """Base of the errors of this module. It is NOT a ``ValueError`` or a ``TypeError``: a DENY caller that does
    ``except ValueError:`` must not swallow it. On any DENY or ALLOW path any ``TextnormError`` means REFUSE."""


class TextTooLong(TextnormError):
    """The weight of a text is over ``defaults.TEXTNORM_MAX_CHARS`` (see the module docstring)."""


class NotText(TextnormError):
    """The argument is not a plain ``str`` (a ``str`` subclass and an enum member are refused too); for ``scripts`` it is not a ``frozenset`` of
    plain ``str``."""


class ViewTooShort(TextnormError):
    """``scan_needles`` found no usable needle for a protected value: no view reaches the minimum of its kind (``defaults.TEXTNORM_MIN_SPELLING_CHARS``,
    ``TEXTNORM_MIN_SQUEEZE_CHARS``, ``TEXTNORM_MIN_DIGIT_CHARS`` for a number, ``TEXTNORM_MIN_SCRIPT_CHARS``, ``TEXTNORM_MIN_IDEOGRAPH_CHARS``), or only a view that keeps separators does (an
    inserted space would hide the value). Refuse to scan with the value: a needle that short is found in nearly every text. The message says so in
    plain words (a value that cannot be masked is REFUSED, never ignored) and what to do: register the longer form, or register the value for
    exact-match only, outside this scan. It never holds the value."""


class UnidataMismatch(TextnormError):
    """The interpreter's Unicode data is not the version the check names were pinned to (``require_pinned_unidata()``). Fail closed: the caller must refuse to run, not fall back."""


class FoldNotConverged(TextnormError):
    """A DENY spelling variant of ``scan_keyset`` was still changing after ``defaults.TEXTNORM_MAX_PASSES`` passes (the last one is the
    confirming pass). Fail closed: any ``TextnormError`` on a DENY path means REFUSE. Not seen on any code point or in the fuzz tests; it
    is the bound, not an expected answer."""


class EmptyView(TextnormError):
    """A protected value has no letter or digit that a scan can rely on: its squeeze views AND its script views are all empty (an empty value, an
    invisible one, punctuation only, marks only). An empty string is found in every text, so scanning with it would match everything; the scan
    refuses instead (``scan_holds``). A value in Chinese, Arabic, Hindi or Thai is NOT refused: it has no squeeze view but it has a script view.
    The message holds the length of the value, never the value."""


_DROP_CATEGORIES = frozenset({"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"})
SPACING_CATEGORIES = frozenset(
    {"Mc", "Lm", "Sk"}
)  # kept by the spelling variants, removed by the marks-dropped views of a scan
# Categories of a code point this Python cannot name: unassigned (Cn), private use (Co), surrogate (Cs). The fold DROPS them, so one that
# REPLACES a letter would make a miss; ``could_be_same_person`` fails closed on them (see "UNNAMED CHARACTERS" in the module docstring).
_UNNAMED_CATEGORIES = frozenset({"Cn", "Co", "Cs"})
FILLERS = frozenset(
    map(chr, (0x3164, 0x115F, 0x1160, 0x2800, 0xFFA0, 0x13441, 0x13442))
)  # invisible letters/symbols used to glue or split words (the last two: Egyptian hieroglyph full blank and half blank)
_REPLACEMENT = "\ufffd"  # U+FFFD: a way to hide a character between two letters; dropped from every check name whatever its source
_LOOKALIKES = types.MappingProxyType({chr(c): v for c, v in _CONFUSABLES.items()})
_TABLE = types.MappingProxyType(dict(_CONFUSABLES))


def _build_cf_table(table: dict[int, str]) -> dict[int, str]:
    """The look-alike table moved onto the case-fold image (see the module docstring): keyed by ``casefold(source)`` (single characters
    only; a source whose case fold is longer is looked up through its parts), valued by the lower-cased value. A letter that is its own
    case fold wins over its capital; otherwise the lowest code point wins (deterministic)."""
    own: dict[int, str] = {}
    derived: dict[int, str] = {}
    for cp in sorted(table):
        folded = chr(cp).casefold()
        if len(folded) != 1:
            continue
        (own if folded == chr(cp) else derived).setdefault(ord(folded), table[cp].casefold())
    return {**derived, **own}


_CF_TABLE = types.MappingProxyType(_build_cf_table(_CONFUSABLES))
_TABLE_SOURCES = frozenset(_CONFUSABLES)
_NON_ALNUM = re.compile(r"[^A-Z0-9]")
_LOOSE = types.MappingProxyType(
    str.maketrans("OILSBZGQ", "01158269")
)  # letters an attacker writes for digits


def _table_digest(table: types.MappingProxyType[int, str]) -> str:
    """SHA-256 of the table as lines ``f"{cp:06X}:{value}\\n"`` in ascending code point order, UTF-8 (as the generator writes it)."""
    lines = "".join(f"{cp:06X}:{table[cp]}\n" for cp in sorted(table))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


# Which fold made a check name: ``alg`` is bumped BY HAND in the pull request that changes what a check name can be (the golden file shows the change),
# ``tbl`` is the first 12 hex characters of the digest of the in-memory table and its entry count, ``ucd`` the UTS #39 data version,
# ``ud`` the interpreter's Unicode version. Nothing stores a check name in v1.
_ALG = "fold5"
FOLD_VERSION = (
    f"alg={_ALG}|tbl={_table_digest(_TABLE)[:12]}:{len(_TABLE)}"
    f"|ucd={_confusables.DATA_VERSION}|ud={unicodedata.unidata_version}"
)


def _build_digit_table() -> dict[int, str]:
    return {
        cp: str(int(chr(cp)))
        for cp in range(sys.maxunicode + 1)
        if chr(cp).isdecimal() and not ("0" <= chr(cp) <= "9")
    }  # every decimal digit that is not ASCII


def _build_punct_table() -> dict[int, str]:
    """Gap 4: every dash (category Pd) and the minus sign read as ``-``; the fraction, division and big solidus forms as ``/``; the
    typographic single and double quotes as ``'`` and ``"``. Applied after NFKC, so compatibility forms (U+2011, U+FE63) are already
    their base."""
    table = {
        cp: "-"
        for cp in range(sys.maxunicode + 1)
        if unicodedata.category(chr(cp)) == "Pd" and cp != 0x2D
    }
    table[0x2212] = "-"
    table.update({cp: "/" for cp in (0x2044, 0x2215, 0x29F8, 0xFF0F, 0x2571)})
    table.update({cp: "'" for cp in (0x2018, 0x2019, 0x201B)})
    table.update({cp: '"' for cp in (0x201C, 0x201D, 0x201F)})
    return table


_PUNCT = types.MappingProxyType(_build_punct_table())
_DIGITS = types.MappingProxyType(
    _build_digit_table()
)  # built once at import: no lazy fill, so no thread can see a half-filled table


@functools.lru_cache(
    maxsize=8192
)  # a pure function of the character; a text of one script repeats a few dozen of them thousands of times
def _char_weight(c: str) -> int:
    """The weight of ``c``: the larger of the single-pass weight of ``c`` and of its case fold (the case-folding path folds case first).

    Why this is not ``guard.runmap._nfkd_len``: that function counts only the NFKD length of one character, which bounds a text that is normalised and
    nothing else. This fold also expands through the digit table, the look-alike table, the case fold and the table of the case-fold image, any of
    which can be longer than NFKD (a bound by NFKD alone would let a text through that makes a longer check name). ``runmap`` is a sibling module
    with its own owner (P1b); importing it would couple the two folds, so each keeps its own bound."""
    return max(_pass_weight(c), _pass_weight(c.casefold()))


def _pass_weight(c: str) -> int:
    """The longest string the pipeline makes from the character ``c``: after NFKD, after NFKC, after the digit and look-alike tables and after
    the case fold with the table of its image (drops only shorten, so they are left out: an upper bound). The upper-side spelling variant, which runs the
    table, then the case fold, then the table of the image, is never longer than the longest of these for any code point.
    This is the weight of ONE pass. The repeated passes of ``_converge`` (up to ``defaults.TEXTNORM_MAX_PASSES``) are not bounded here by a proof:
    the bound is checked on the finished keys, for every code point, by ``test_identity_keys_and_could_be_same_person_hold_for_every_code_point_*``."""
    nfkd = unicodedata.normalize("NFKD", c)
    nfkc = unicodedata.normalize("NFKC", nfkd)
    digits = nfkc.translate(_DIGITS)
    mapped = digits.translate(_TABLE)
    cased = digits.casefold()
    return max(
        1,
        len(nfkd),
        len(nfkc),
        len(mapped),
        len(mapped.casefold()),
        len(cased),
        len(cased.translate(_CF_TABLE)),
    )


_WEIGHT_MEMO_MIN = 1024  # a shorter text is weighed again each time (a few dozen distinct characters at most is cheaper than a digest)
_WEIGHT_MEMO_MAX = 32
_WEIGHT_MEMO: dict[
    bytes, int
] = {}  # SHA-256 of a long text -> its weight (no text is kept); a caller that folds one line several times weighs it once


def _weight(text: str) -> int:
    """W(text): the sum of the character weights. An ASCII text has W = its length. Computed once per DISTINCT character of the text. The weight of
    a LONG text is remembered under its SHA-256 digest (measured: 0.41 s for 200,000 distinct characters; the redactor folds one line several
    times), at most 32 entries, so no text is kept in memory by this function."""
    if text.isascii():
        return len(text)
    if len(text) < _WEIGHT_MEMO_MIN:
        return sum(_char_weight(c) * n for c, n in Counter(text).items())
    key = hashlib.sha256(text.encode("utf-8", "surrogatepass")).digest()
    weight = _WEIGHT_MEMO.get(key)
    if weight is None:
        weight = sum(_char_weight(c) * n for c, n in Counter(text).items())
        if len(_WEIGHT_MEMO) >= _WEIGHT_MEMO_MAX:
            _WEIGHT_MEMO.pop(
                next(iter(_WEIGHT_MEMO)), None
            )  # the oldest entry (dicts keep the order of insertion)
        _WEIGHT_MEMO[key] = weight
    return weight


def _checked(*texts: str) -> None:
    """The two input rules, in one place: every argument, left to right, is a plain ``str`` and has a weight within the cap. Every
    weight is at least the length, so a text LONGER than the cap is refused from its length alone, BEFORE any per-character work."""
    for text in texts:
        if type(text) is not str:
            raise NotText("a text must be a plain str (a subclass or an enum member is refused)")
        if len(text) > defaults.TEXTNORM_MAX_CHARS:
            raise TextTooLong(
                f"the text is too long: {len(text)} of {defaults.TEXTNORM_MAX_CHARS} allowed"
            )
        weight = _weight(text)
        if weight > defaults.TEXTNORM_MAX_CHARS:
            raise TextTooLong(
                "the text is too long once look-alike letters are expanded: "
                f"{weight} of {defaults.TEXTNORM_MAX_CHARS} allowed"
            )


# COMBINING GREEK YPOGEGRAMMENI: the only mark whose case fold is a letter (iota); see "U+0345" in the module docstring
_YPOGEGRAMMENI = "\u0345"
_IOTA = "\u03b9"


def _is_greek_letter(ch: str) -> bool:
    """A letter whose Unicode name starts with GREEK: the Greek and Coptic block, Greek Extended and the few Greek letters elsewhere
    (U+1D26 to U+1D2A, U+AB65). Coptic letters are not Greek here."""
    return ch.isalpha() and unicodedata.name(ch, "").startswith("GREEK ")


def _kept(ch: str) -> bool:
    """True for a character the drop step keeps (whitespace is kept and later becomes a space). An unassigned (Cn) code point that is a source
    of the look-alike table is kept too, so the table can read it (gap 2); every other dropped category is dropped before the table. U+FFFD
    is dropped whatever its source."""
    if ch.isspace():
        return True
    if ch in FILLERS or ch == _REPLACEMENT:
        return False
    category = unicodedata.category(ch)
    return category not in _DROP_CATEGORIES or (category == "Cn" and ord(ch) in _TABLE_SOURCES)


def _subscript_iota(s: str) -> str:
    """U+0345 on an NFKD text: an iota (U+03B9) when the last kept character before it is a Greek letter, otherwise removed. Characters the
    fold drops anyway (other marks, format characters, fillers) are skipped when looking for that letter, so inserting one never changes the
    result. A run of U+0345 after a Greek letter gives a run of iotas. This is the one place where a mark is kept (module docstring)."""
    if _YPOGEGRAMMENI not in s:
        return s
    out: list[str] = []
    last = ""  # the last character kept by the drop step
    for ch in s:
        if ch == _YPOGEGRAMMENI:
            if last and _is_greek_letter(last):
                out.append(_IOTA)
                last = _IOTA
            continue
        out.append(ch)
        if _kept(ch):
            last = ch
    return "".join(out)


# The SPELLING VARIANTS (module docstring): a text is read at most three ways, a fixed set. Each is (iota rule, table first):
# (a) lower side, U+0345 always dropped; (b) lower side, U+0345 an iota after a Greek letter (this is ``identity_key``);
# (c) upper side: the look-alike table runs on the letter as written, then case is folded, then the table of the case-fold image;
# U+0345 dropped. A fourth spelling variant is a change of the algorithm id and of the tests that pin three.
_READINGS = (
    (False, False),
    (True, False),
    (False, True),
)


def _without_spacing_marks(text: str) -> str:
    """``text`` without any Mc, Lm or Sk character. It runs on the RAW text, before the first normalisation: NFKD and NFKC read a modifier
    letter such as U+02B0 as the letter h, so a mark must be gone before they run."""
    return "".join(ch for ch in text if unicodedata.category(ch) not in SPACING_CATEGORIES)


# Two or more words of a Unicode character name are the script for these first words ("OLD TURKIC" and "OLD ITALIC" are two scripts).
_TWO_WORD_SCRIPTS = frozenset({"OLD", "NEW", "TAI", "LINEAR", "INSCRIPTIONAL", "MEROITIC"})
# First words that name one script together: the Han ideographs (CJK UNIFIED and COMPATIBILITY IDEOGRAPH) and the two kana syllabaries with
# the old variant kana. Hangul stays one group (jamo and syllables share the word), Bopomofo, Latin, Greek, Cyrillic, Hebrew, Arabic and the
# rest are one group per first word. IDEOGRAPHIC (the closing mark U+3006, a letter by category) is NOT Han here: a value must hold it itself.
_SCRIPT_GROUPS = types.MappingProxyType(
    {"CJK": "HAN", "HIRAGANA": "KANA", "KATAKANA": "KANA", "HENTAIGANA": "KANA"}
)


def _script_of(ch: str) -> str:
    """The script group of the letter ``ch``, from its Unicode character name only (``unicodedata``; no data file): the first word of the name
    ("CYRILLIC", "GREEK", "HEBREW", "THAI", "DEVANAGARI", "ARABIC", "LATIN"), two words for the families that share a first word, and the
    groups of ``_SCRIPT_GROUPS`` (Han; kana). A letter with no name (the Tangut ideographs and the other unnamed letters) is the group ``UNNAMED``. The first word is not
    always a script (U+2132 is ``TURNED``, U+2183 is ``ROMAN``). Not the UTS #24 script
    property: it is the cheapest rule that separates the scripts a person mixes into a value."""
    words = unicodedata.name(ch, "").split()
    if not words:
        return "UNNAMED"
    head = f"{words[0]} {words[1]}" if words[0] in _TWO_WORD_SCRIPTS else words[0]
    return _SCRIPT_GROUPS.get(head, head)


def _scripts_in(views: Iterable[str]) -> frozenset[str]:
    """The script groups of the non-ASCII letters of ``views``."""
    out: set[str] = set()
    for view in views:
        out.update(_script_of(ch) for ch in set(view) if not ch.isascii() and ch.isalpha())
    return frozenset(out)


def _script_view(view: str, scripts: frozenset[str]) -> str:
    """The SCRIPT VIEW of a view: only the non-ASCII letters whose script group is in ``scripts`` stay. Whitespace, punctuation, symbols, ASCII
    letters and digits (and the digits of other scripts, which are ASCII by now) are removed, and so is a letter of any OTHER script, so a
    separator, an ASCII letter or a foreign-script letter inserted into a value cannot hide it. Marks are not here: the view is made from a
    text whose Mn and Me marks were dropped and whose Mc, Lm and Sk characters were removed. A letter of the SAME script stays (a different spelling)."""
    group: dict[str, bool] = {}
    kept: list[str] = []
    for ch in view:
        if ch.isascii() or not ch.isalpha():
            continue
        if ch not in group:
            group[ch] = _script_of(ch) in scripts
        if group[ch]:
            kept.append(ch)
    return "".join(kept)


def _prefix(nfkd: str, *, iota: bool, marks: bool = False) -> str:
    """The spelling variant-independent steps on an NFKD text: U+0345 (an iota after a Greek letter when ``iota``, otherwise it is dropped like any
    mark), the drops (with ``marks``, also every Mc, Lm and Sk character), whitespace, NFKC, the digits and the dash/slash/quote map (gap 4)."""
    s = _subscript_iota(nfkd) if iota else nfkd
    s = "".join(
        " " if ch.isspace() else ch
        for ch in s
        if _kept(ch) and not (marks and unicodedata.category(ch) in SPACING_CATEGORIES)
    )
    s = unicodedata.normalize("NFKC", s)
    return s.translate(_DIGITS).translate(_PUNCT)


def _finish(s: str, *, casefold: bool, table_first: bool, collapse_ws: bool) -> str:
    # casefold BEFORE the table and use the table moved onto the casefold image: idempotent and case-symmetric (module docstring);
    # table first is the spelling variant by the letter's own case (capital Eta reads h)
    if not casefold:
        s = s.translate(_TABLE)
    elif table_first:
        s = s.translate(_TABLE).casefold().translate(_CF_TABLE)
    else:
        s = s.casefold().translate(_CF_TABLE)
    return " ".join(s.split()) if collapse_ws else s


def _prepare(raw: str, *, iota: bool = True) -> str:
    """The steps before the table, on a raw text, for one pass of a scan spelling variant: NFKD, the U+0345 rule (``iota``), the drops,
    NFKC, the digit table and the dash/slash/quote map."""
    return _prefix(unicodedata.normalize("NFKD", raw), iota=iota)


def _fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    """ONE spelling variant, the iota spelling variant (b): what ``fold`` and ``identity_key`` return."""
    prefix = _prefix(unicodedata.normalize("NFKD", raw), iota=True)
    return _finish(prefix, casefold=casefold, table_first=False, collapse_ws=collapse_ws)


def _readings(
    raw: str,
    *,
    casefold: bool,
    collapse_ws: bool,
    marks_dropped: bool = False,
    marks_only: bool = False,
) -> list[tuple[bool, str]]:
    """Every spelling reading of ``raw`` as ``(marks, view)`` in the order of ``_READINGS``, WITH repeats: ``marks`` is False for the readings of
    the text itself and True for those of the text without its Mc, Lm and Sk characters (``marks_dropped``; with ``marks_only`` only those are
    made). Without ``casefold`` there is no upper side (the table already runs on the letter as written), so only (a) and (b) remain."""
    texts = [raw]
    if marks_dropped:
        texts.append(_without_spacing_marks(raw))
    out: list[tuple[bool, str]] = []
    for marks, text in enumerate(texts):
        if marks_only and not marks:
            continue
        nfkd = unicodedata.normalize("NFKD", text)
        with_iota = _prefix(nfkd, iota=True, marks=bool(marks))
        prefixes = {
            True: with_iota,
            False: _prefix(nfkd, iota=False, marks=bool(marks))
            if _YPOGEGRAMMENI in nfkd
            else with_iota,
        }
        for iota, table_first in _READINGS:
            if table_first and not casefold:
                continue
            view = _finish(
                prefixes[iota], casefold=casefold, table_first=table_first, collapse_ws=collapse_ws
            )
            out.append((bool(marks), view))
    return out


def _pairs_from(
    readings: Iterable[tuple[bool, str]], scripts: frozenset[str]
) -> list[tuple[str, str]]:
    """``(kind, view)`` pairs, kind ``"spelling"`` or ``"script"``, from ``_readings``; a pair is not repeated (the same text may be both kinds).
    With ``scripts`` (not empty) the SCRIPT VIEW of each marks-dropped reading follows it (``_script_view``; left out when empty)."""
    pairs: list[tuple[str, str]] = []
    for marks, view in readings:
        if ("spelling", view) not in pairs:
            pairs.append(("spelling", view))
        if scripts and marks:
            only = _script_view(view, scripts)
            if only and ("script", only) not in pairs:
                pairs.append(("script", only))
    return pairs


def _view_pairs(
    raw: str,
    *,
    casefold: bool,
    collapse_ws: bool,
    marks_dropped: bool = False,
    marks_only: bool = False,
    scripts: frozenset[str] = frozenset(),
) -> list[tuple[str, str]]:
    """Every view of ``raw`` as ``(kind, view)``, kind ``"spelling"`` or ``"script"``, in the order of ``_READINGS``; a pair is not repeated (the
    same text may be both kinds). With ``marks_dropped`` the same spelling variants of the text WITHOUT its Mc, Lm and Sk characters follow (a
    scan wants them; the DENY check names use them too, through ``_keys``, which asks for them only when the text can differ); with ``marks_only`` only those are made. With ``scripts`` (not empty) the SCRIPT
    VIEW of each marks-dropped view follows it (``_script_view``; left out when empty)."""
    return _pairs_from(
        _readings(
            raw,
            casefold=casefold,
            collapse_ws=collapse_ws,
            marks_dropped=marks_dropped,
            marks_only=marks_only,
        ),
        scripts,
    )


def _views(
    raw: str,
    *,
    casefold: bool,
    collapse_ws: bool,
    marks_dropped: bool = False,
    scripts: frozenset[str] = frozenset(),
) -> tuple[str, ...]:
    """Every view of ``raw`` as a string, without repeats (``_view_pairs`` without the kinds): at most three spelling variants, twice as many with
    ``marks_dropped`` (the check names of ``identity_keys`` are these, at most six), three times as many with ``scripts``."""
    out: list[str] = []
    for _kind, view in _view_pairs(
        raw,
        casefold=casefold,
        collapse_ws=collapse_ws,
        marks_dropped=marks_dropped,
        scripts=scripts,
    ):
        if view not in out:
            out.append(view)
    return tuple(out)


def fold(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    """ONE spelling variant of ``raw`` (the iota spelling variant, see the module docstring), NOT a scan or a DENY comparator: a scan uses ``fold_views``. Linear in
    the weight of ``raw``, which is bounded first."""
    _checked(raw)
    return _fold(raw, casefold=casefold, collapse_ws=collapse_ws)


def _checked_scripts(scripts: frozenset[str]) -> None:
    if type(scripts) is not frozenset or any(type(item) is not str for item in scripts):
        raise NotText("scripts must be a frozenset of str (the result of value_scripts)")


def _value_scripts(raw: str) -> frozenset[str]:
    """``value_scripts`` on a text that was already checked: the marks-dropped views only (a modifier letter of the value is not a script of it)."""
    return _scripts_in(
        view
        for _kind, view in _view_pairs(
            raw, casefold=True, collapse_ws=False, marks_dropped=True, marks_only=True
        )
    )


def value_scripts(raw: str) -> frozenset[str]:
    """The script groups of the PROTECTED VALUE ``raw``: the groups (``_script_of``: the first word of the Unicode name, Han and kana grouped) of the
    non-ASCII letters that are left in its marks-dropped views after the fold. Empty for a value that is only ASCII letters, digits and
    separators once folded (a Latin value: ``squeeze_views`` covers it). A scan of a text for this value passes the result as ``scripts`` to
    ``fold_views`` so that a letter of any OTHER script in the text is dropped from its script views."""
    _checked(raw)
    return _value_scripts(raw)


def fold_view(
    raw: str,
    *,
    marks_dropped: bool = False,
    iota: bool = True,
    casefold: bool = False,
    collapse_ws: bool = False,
) -> str:
    """ONE named view of ``raw`` (one of the strings ``fold_views`` returns): ``iota`` False drops U+0345 everywhere (spelling variant (a)),
    True reads it as an iota after a Greek letter (spelling variant (b), what ``fold`` returns); ``marks_dropped`` builds the view from the text
    without its Mc, Lm and Sk characters. A caller that must know WHICH view found a value (the redactor cuts the original text with a
    position map of one view) asks for the views one by one; ``fold_view(raw)`` is ``fold(raw)``. Without ``casefold`` there is no
    upper-side spelling variant, so these two switches name every view ``fold_views`` returns."""
    _checked(raw)
    text = _without_spacing_marks(raw) if marks_dropped else raw
    prefix = _prefix(unicodedata.normalize("NFKD", text), iota=iota, marks=marks_dropped)
    return _finish(prefix, casefold=casefold, table_first=False, collapse_ws=collapse_ws)


def without_spacing_marks(raw: str) -> str:
    """``raw`` without any spacing mark (Mc), modifier letter (Lm) or modifier symbol (Sk) character (ASCII ``^`` and the backtick are modifier
    symbols too): the text the marks-dropped views are made from. A caller that needs the same drop on a text of its own (a second-pass view)
    uses this function and keeps one definition."""
    _checked(raw)
    return _without_spacing_marks(raw)


def fold_views(
    raw: str,
    *,
    scripts: frozenset[str],
    casefold: bool = False,
    collapse_ws: bool = False,
) -> tuple[str, ...]:
    """Every view of ``raw`` for a SCAN: a redaction or a blocklist looks for the secret in EVERY view of the text (module docstring, "MARKS AND SCANS").
    The views are the spelling variants of ``raw`` (at most three: two without ``casefold``; ``fold(raw, ...)`` is one of them), then the same
    spelling variants of ``raw`` with every spacing mark (Mc), modifier letter (Lm) and modifier symbol (Sk) removed before the first
    normalisation (all scripts are kept), then, only when ``scripts`` is given, the SCRIPT VIEW of each of those (the non-ASCII letters of the
    scripts in ``scripts`` only; left out when empty or repeated). At most nine views (six without ``casefold``), none repeated. A secret
    hidden by inserting such a mark is found in the marks-dropped views.

    THE RULE FOR A SCAN: pass ``casefold=True`` (and ``collapse_ws=True``). The default ``False`` keeps the case of the text (the display and comparison callers want that), so a scan
    built without it misses "SECRET" when the protected value is "secret". A redaction MUST ALSO scan ``squeeze_views`` (the ASCII letters and digits with
    every separator removed) and take its needles with ``scan_needles``. ``scripts`` is REQUIRED (pass ``frozenset()`` for no script view): a caller
    that builds its own scan has to decide. To scan a TEXT for a value in a script, pass ``scripts=value_scripts(value)`` (the scripts of the
    VALUE, never those of the text: a text that holds a letter of another script would otherwise keep it). ``scan_views`` and ``scan_holds`` do that
    themselves.

    A value with NO ASCII letter or digit (Chinese, Arabic, Hindi, Thai) is found by the script views of ``fold_views`` (the non-ASCII letters of the value's own
    scripts, with whitespace, punctuation, symbols, ASCII characters and the letters of every other script removed), so an inserted space, hyphen,
    line break, ASCII letter, mark or foreign-script letter does not hide it. A letter of the SAME script inserted is found only by
    ``scan_holds`` (see "ONE INSERTED LETTER" in the module docstring); a respelling of the value is not covered."""
    _checked(raw)
    _checked_scripts(scripts)
    return _views(
        raw, casefold=casefold, collapse_ws=collapse_ws, marks_dropped=True, scripts=scripts
    )


_MINIMUM_NAMES = (
    "TEXTNORM_MIN_SPELLING_CHARS",
    "TEXTNORM_MIN_SQUEEZE_CHARS",
    "TEXTNORM_MIN_SCRIPT_CHARS",
    "TEXTNORM_MIN_IDEOGRAPH_CHARS",
    "TEXTNORM_MIN_DIGIT_CHARS",
)
_MINIMUM_FLOOR = 2  # a needle of one character is found in nearly every text of its script: no minimum below this is accepted


def _whole_number(name: str, floor: int) -> int:
    """``defaults.<name>`` as a plain ``int`` of at least ``floor`` (``bool`` is refused). The message names the constant and the type, and the
    value only when it is an ``int``."""
    value = getattr(defaults, name, None)
    if type(value) is not int or value < floor:
        shown = value if type(value) is int else f"of type {type(value).__name__}"
        raise TextnormError(
            f"defaults.{name} must be a whole number of at least {floor}, not {shown}"
        )
    return value


def _validated_minimums() -> tuple[int, int, int, int, int]:
    """The five minimum lengths of ``defaults`` (spelling, squeeze, script, ideograph, digits), each a plain ``int`` of at least
    ``_MINIMUM_FLOOR`` (2; ``bool`` is refused). Run when the module is imported and again whenever ``scan_needles`` runs, so a wrong
    value fails closed in both places."""
    out = tuple(_whole_number(name, _MINIMUM_FLOOR) for name in _MINIMUM_NAMES)
    return out[0], out[1], out[2], out[3], out[4]


def _validated_max_passes() -> int:
    """``defaults.TEXTNORM_MAX_PASSES``: a plain ``int`` of at least 1 (a float makes ``range`` raise ``TypeError``, zero or a negative number
    makes every scan raise ``FoldNotConverged``). Run when the module is imported and again whenever a scan key is made."""
    return _whole_number("TEXTNORM_MAX_PASSES", 1)


def _validated_pins() -> None:
    """The two pin constants of ``defaults`` (the Unicode data version and the Python minor version that carries it) must be non-empty ``str``.
    Run at import and by ``require_pinned_unidata``: a wrong value fails closed in both places. The message names the constant, never the value."""
    for name in ("TEXTNORM_PINNED_UNIDATA", "TEXTNORM_PINNED_PYTHON"):
        value = getattr(defaults, name, None)
        if type(value) is not str or not value:
            raise TextnormError(
                f"defaults.{name} must be a non-empty str, not of type {type(value).__name__}"
            )


_validated_minimums()  # fail closed at import
_validated_pins()
_validated_max_passes()


def _needle_pairs(raw: str, *, loose: bool = False) -> list[tuple[str, str]]:
    """``scan_needles`` on a text that was already checked, with the kind of each needle (``"spelling"``, ``"squeeze"`` or ``"script"``), no
    repeats. Raises ``ViewTooShort`` when no squeeze or script view reaches its minimum."""
    spelling_min, squeeze_min, script_min, ideograph_min, digit_min = _validated_minimums()
    scripts = _value_scripts(raw)
    squeezed = squeeze_views(raw, loose=loose)
    ideographs_only = scripts == frozenset({"HAN"}) and not any(squeezed)
    pairs = [
        *_view_pairs(raw, casefold=True, collapse_ws=True, marks_dropped=True, scripts=scripts),
        *(("squeeze", view) for view in squeezed),
    ]
    needles: dict[
        str, str
    ] = {}  # needle -> kind; a script view equal to a spelling view is a script needle
    proof = False  # a squeeze or script needle: an inserted separator cannot hide it
    for kind, view in pairs:
        if kind == "squeeze":
            minimum = digit_min if view.isdigit() else squeeze_min
        elif kind == "script":
            minimum = ideograph_min if ideographs_only else script_min
        else:
            minimum = spelling_min
        if len(view) < minimum:
            continue
        proof = proof or kind != "spelling"
        if needles.get(view, "spelling") == "spelling":
            needles[view] = kind
    if not proof:
        digits = (
            " It is a number: a number needs at least {digit_min} digits to be scanned."
            if raw.isdigit()
            else ""
        )
        raise ViewTooShort(
            f"this protected value ({len(raw)} characters) is too short to mask: no squeeze view and no script view of it is long enough "
            f"(minimums: squeeze {squeeze_min}, digits only {digit_min}, script {script_min}, ideograph {ideograph_min}).{digits.format(digit_min=digit_min)} "
            "A value that cannot be masked is REFUSED, never ignored. What to do: register the longer form of it (the whole token or the "
            "whole phrase, not a fragment), or register it for exact-match only (a plain search that does not fold, outside this scan)"
        )
    return [(kind, view) for view, kind in needles.items()]


def scan_needles(raw: str, *, loose: bool = False) -> tuple[str, ...]:
    """The needles of a PROTECTED VALUE ``raw`` for a scan, without repeats: the views of ``fold_views(raw, casefold=True, collapse_ws=True)`` (the
    spelling views and, with the scripts of the value, its script views) and of ``squeeze_views(raw, loose=loose)`` that reach the minimum of their
    KIND: spelling ``defaults.TEXTNORM_MIN_SPELLING_CHARS``, squeeze ``TEXTNORM_MIN_SQUEEZE_CHARS`` (``TEXTNORM_MIN_DIGIT_CHARS`` when the view is
    ASCII digits only), script ``TEXTNORM_MIN_SCRIPT_CHARS`` (``TEXTNORM_MIN_IDEOGRAPH_CHARS`` when the value has no ASCII letter or digit and only Han
    ideographs; ``loose=True`` loosens the squeeze views first, so it can change whether the value counts as ideographs only: harmless, the needles are still the views that reach
    their minimum). A view shorter than that, an empty one above all, is not a needle: it is found in every text. Raises ``ViewTooShort`` when NO
    squeeze or script view reaches its minimum: the spelling views keep separators, so a value that only they can find is hidden by one inserted
    space, and the caller must REFUSE to scan with that value (it is empty, invisible, a short Latin word, a short number, a short script word, or
    one ideograph). ``loose=True`` loosens only the squeeze half (the digit-like letters become digits in the squeeze views); the spelling and script
    views are the same. The needles are exact strings: a copy of the value with ONE extra letter of its own script inserted holds none of them
    (``scan_holds`` also finds that copy, see "ONE INSERTED LETTER"). A caller that scans uses ``scan_holds``; one that takes the needles itself
    reads the text with ``scan_views(text, value)`` and misses that copy."""
    _checked(raw)
    return tuple(needle for _kind, needle in _needle_pairs(raw, loose=loose))


def squeeze(raw: str, *, loose: bool = False) -> str:
    """ONE reading, not a scan: a scan uses ``squeeze_views`` and ``scan_needles``. Folded, upper-case letters and digits only; ``loose`` also treats the digit-like letters O I L S B Z G Q as the
    digits 0 1 1 5 8 2 6 9. The result is ``""`` for a text without an ASCII letter or digit after the fold (a name in Chinese or Hindi, for
    example): an empty needle matches every text, so a caller must REFUSE an empty result, never scan with it."""
    _checked(raw)
    s = _fold(raw, casefold=True).upper()
    if loose:
        s = s.translate(_LOOSE)
    return _NON_ALNUM.sub("", s)


def squeeze_views(raw: str, *, loose: bool = False) -> tuple[str, ...]:
    """Every view of ``raw`` squeezed as ``squeeze`` does (at most six, none repeated): the views a scan on letters and digits looks through.
    They are the spelling variants (at most three; ``squeeze(raw, loose=loose)`` is one of them) and the same spelling variants of ``raw`` with
    every spacing mark (Mc), modifier letter (Lm) and modifier symbol (Sk) removed BEFORE the first normalisation and before the look-alike table,
    so "pass" + U+0C02 + "word" holds ``PASSWORD`` (the table would read U+0C02 as the letter o). A view is ``""`` for a text without an ASCII letter or
    digit after the fold: an empty needle matches every text, so a caller must REFUSE an empty view of a protected value, never scan with it. A
    scan reads these views AND ``fold_views`` (module docstring, "MARKS AND SCANS")."""
    _checked(raw)
    return _squeezed(raw, loose=loose)


def _squeezed(raw: str, *, loose: bool = False) -> tuple[str, ...]:
    """``squeeze_views`` on a text that was already checked."""
    out: list[str] = []
    for view in _views(raw, casefold=True, collapse_ws=False, marks_dropped=True):
        s = view.upper()
        if loose:
            s = s.translate(_LOOSE)
        s = _NON_ALNUM.sub("", s)
        if s not in out:
            out.append(s)
    return tuple(out)


def key_tag() -> str:
    """``""`` on the pinned Unicode version; otherwise U+E000 + ``alg=<alg>|ud=<this interpreter's Unicode version>`` + U+E000, which
    ``identity_key`` puts in front of its check name so a check name made on another version never equals a check name made on the pinned one. Read at call
    time. U+E000 is private use: the fold drops it, so no untagged key can start with the tag."""
    version = unicodedata.unidata_version
    if version == defaults.TEXTNORM_PINNED_UNIDATA:
        return ""
    return f"\ue000alg={_ALG}|ud={version}\ue000"


def _canon(s: str) -> str:
    """Unicode compatibility caseless matching: NFKD, case fold, NFKD, case fold; a case fold of a composed letter can leave a
    sequence that normalises again, which is why Unicode writes it with two folds. The second fold is kept because the standard has it; on
    Unicode 15.0 and 15.1 it changes no result for any single code point (checked), so no test can tell it from a single fold. What the
    tests do pin is the NFKD step against the old NFKC (eight code points were not case symmetric). Whitespace is collapsed."""
    folded = unicodedata.normalize("NFKD", unicodedata.normalize("NFKD", s).casefold()).casefold()
    return " ".join(unicodedata.normalize("NFKD", folded).split())


def identity_key(raw: str) -> str:
    """ONE spelling variant of ``raw``, NOT a DENY comparator: ``fold`` with case folded and whitespace collapsed (the iota spelling variant, see the module
    docstring). Stable and idempotent, so it stays the check name to keep and to index (outside tests only through an exemption: the ban table in ``pyproject.toml``
    and the exemption list of ``tests/test_textnorm_meta.py``); but a DENY decision compares ``identity_keys`` (``could_be_same_person``).
    The empty string and invisible-only text give ``""`` on the pinned Unicode version (never a value to store or index). On another version
    the check name starts with ``key_tag()``."""
    _checked(raw)
    tag = key_tag()
    if tag and raw.startswith(tag):
        # already a check name of this interpreter: the function stays idempotent
        raw = raw[len(tag) :]
    return tag + _fold(raw, casefold=True, collapse_ws=True)


def _untagged(raw: str) -> str:
    """``raw`` without the tag of THIS interpreter at its start (``key_tag()``; nothing to remove on the pinned version)."""
    tag = key_tag()
    return raw[len(tag) :] if tag and raw.startswith(tag) else raw


def _keys(raw: str) -> tuple[str, ...]:
    tag = key_tag()
    raw = _untagged(raw)
    # The marks-dropped reading is made only when it can differ from the plain one: the raw text holds a spacing mark, modifier letter or modifier
    # symbol, OR its NFKD text does (61 code points, for example U+0149 and U+1B06, decompose into one although the raw text holds none). This gate
    # lives HERE and not in ``_view_pairs``: there the script views are made in the marks-dropped pass (F6-1b).
    marks_dropped = _holds_spacing(raw) or _holds_spacing(unicodedata.normalize("NFKD", raw))
    return tuple(
        tag + view
        for view in _views(raw, casefold=True, collapse_ws=True, marks_dropped=marks_dropped)
    )


def _holds_spacing(text: str) -> bool:
    """True when ``text`` holds an Mc, Lm or Sk character."""
    return any(unicodedata.category(ch) in SPACING_CATEGORIES for ch in set(text))


def _holds_unnamed(text: str) -> bool:
    """True when ``text`` holds a code point of category Cn (unassigned), Co (private use) or Cs (surrogate) on this interpreter."""
    return any(unicodedata.category(ch) in _UNNAMED_CATEGORIES for ch in set(text))


def identity_keys(raw: str) -> tuple[str, ...]:
    """The check names of ``raw`` for a DENY decision, at most SIX, no repeats, in a fixed order: one per spelling variant of the raw text ((a), (b), (c) of
    the module docstring; ``identity_key(raw)`` is one of them), then the same for the raw text with every spacing mark (Mc), modifier letter (Lm) and
    modifier symbol (Sk) removed, which is made only when the text holds one (or its NFKD text does). Two texts match when ANY check name of one equals ANY
    check name of the other (``could_be_same_person``). Not transitive, so NEVER a unique index, a group-by or anything stored: use ``identity_key`` for those
    (through an exemption)."""
    _checked(raw)
    return _keys(raw)


def could_be_same_person(a: str, b: str) -> bool:
    """DENY comparator (separation of duties, a blocklist): True when ANY check name of ``a`` equals ANY check name of ``b`` (``identity_keys``).
    Look-alike letters, case, width, ligatures, non-spacing and enclosing marks (Mn, Me), invisible characters AND spacing marks (Mc), modifier letters
    (Lm) and modifier symbols (Sk) compare equal, which is the safe side for a DENY: two names that differ only by such marks are "could be the same
    person", so a person must look ("ali" + U+0903 + "ce" against "alice"; on made-up Hindi names two pairs in 4,371, see the module docstring).
    It is also True when either text holds a character this Python cannot name (unassigned Cn, private use Co or surrogate Cs: the fold drops such a
    character, so one that replaces a letter would hide a name): a name with an emoji newer than Unicode 15.1 is "could be the same person" with every
    other name. Dashes, the minus sign, the division slashes and the typographic quotes are read as ``-``, ``/``, ``'`` and ``"`` (gap 4, since
    P1b): "O'Brien" and "O" + U+2019 + "Brien" are the same person here, and so are a Unicode hyphen (U+2010) and "-" (corpus rows r114 to r117).
    Not widened by the scan keys: "Li Na" and "Lina" are DIFFERENT here (``allow_equal`` says so too) and share a scan key (``scan_keyset``).
    Not transitive. NEVER an ALLOW.

    Where it is used: a library primitive for the deny and check-name path only. It is wired into NO approval check, and no approval compares people's
    names (``approvals/requests.py`` compares ids exactly). A use in an approval later is a new ticket with its own plan review."""
    _checked(a, b)
    if _holds_unnamed(_untagged(a)) or _holds_unnamed(_untagged(b)):
        return True  # fail closed (F6-5): the fold drops such a character, so one that replaces a letter would hide a name
    return not set(_keys(a)).isdisjoint(_keys(b))


class AllowVerdict(Enum):
    """Result of ``allow_equal``. A plain ``Enum`` on purpose: ``if allow_equal(a, b):`` raises ``TypeError`` instead of being always
    true. Compare with ``is AllowVerdict.EQUAL``."""

    EQUAL = "EQUAL"  # identical strings: the only verdict that allows
    DIFFERENT = "DIFFERENT"  # an ordinary mismatch: refuse
    VARIANT = "VARIANT"  # differs only in case, width, ligature or whitespace (NFKD + casefold equal): refuse, a plain mistake or a variant
    LOOKALIKE = "LOOKALIKE"  # differs but folds equal through homoglyphs, invisible characters or (spacing) marks, or holds a character Python cannot name: refuse and audit as a spoof

    def __bool__(self) -> bool:
        raise TypeError("an AllowVerdict has no truth value: compare with 'is AllowVerdict.EQUAL'")


def allow_equal(a: str, b: str) -> AllowVerdict:
    """The whole ALLOW decision for "is this the verified value?": only ``EQUAL`` allows. No normalisation: the comparison is ``a == b``
    so the value that was verified is the value that is used. Both arguments are checked (type, then size) before any work."""
    _checked(a, b)
    if a == b:
        return AllowVerdict.EQUAL
    if _canon(a) == _canon(b):
        return AllowVerdict.VARIANT
    # any spelling variant of one equals any spelling variant of the other
    if could_be_same_person(a, b):
        return AllowVerdict.LOOKALIKE
    return AllowVerdict.DIFFERENT


def names_equal(a: str, b: str) -> bool:
    """People's names in prose: Unicode compatibility caseless equality (NFKD, case fold, NFKD, case fold), whitespace insensitive. NOT an ALLOW decision (``allow_equal``) and NOT a DENY decision
    either (``could_be_same_person``: this one does not fold look-alikes, so a Cyrillic-a name is a different name here). Never stored, never a check name."""
    _checked(a, b)
    return _canon(a) == _canon(b)


# ---- the DENY scans -----------------------------------------------------------------------------------------------------------------
_TAG_FIRST, _TAG_LAST = 0xE0000, 0xE007F
_TAG_PRINTABLE_FIRST, _TAG_PRINTABLE_LAST = 0xE0020, 0xE007E


def _tag_texts(raw: str) -> list[str]:
    """T0 to T3 (hidden channel in tag form): T0 = the text without any tag character; T1 = tag characters U+E0020 to U+E007E decoded in
    place to their ASCII letters (the other tag characters removed); T2 = T0 followed by the decoded tag characters in order; T3 = the
    decoded tag characters alone. A text with no tag character has only T0."""
    if not any(_TAG_FIRST <= ord(ch) <= _TAG_LAST for ch in raw):
        return [raw]
    t0: list[str] = []
    t1: list[str] = []
    decoded: list[str] = []
    for ch in raw:
        cp = ord(ch)
        if _TAG_FIRST <= cp <= _TAG_LAST:
            if _TAG_PRINTABLE_FIRST <= cp <= _TAG_PRINTABLE_LAST:
                letter = chr(cp - _TAG_FIRST)
                t1.append(letter)
                decoded.append(letter)
        else:
            t0.append(ch)
            t1.append(ch)
    text0 = "".join(t0)
    return [text0, "".join(t1), text0 + "".join(decoded), "".join(decoded)]


def _converge(text: str, step) -> str:
    """Repeat ``step`` until its output equals its input, for at most ``defaults.TEXTNORM_MAX_PASSES`` passes (the confirming pass
    included); a text still changing after that raises ``FoldNotConverged``."""
    passes = _validated_max_passes()
    for _ in range(passes):
        out = step(text)
        if out == text:
            return out
        text = out
    raise FoldNotConverged(f"a spelling variant was still changing after {passes} passes")


def _pass_a(text: str) -> str:
    """Scan spelling variant A, one pass: the look-alike table first (each letter by its own case: capital Eta reads ``H``), then the case
    fold; U+0345 is dropped, as in the spelling variants (a) and (c) of ``identity_keys``."""
    return _prepare(text, iota=False).translate(_TABLE).casefold()


def _pass_b(text: str) -> str:
    """Scan spelling variant B, one pass: the case fold first, then the table on the case-fold image (capital Eta becomes eta and reads
    ``n``); U+0345 is an iota after a Greek letter, as in the spelling variant (b), which is ``identity_key``."""
    return _prepare(text).casefold().translate(_CF_TABLE)


# The bound on the number of scan keys: 2 spelling variants (the text as it is, the text without Mc/Sk) x 4 tag texts x 2 passes = 16. The most a
# real text reaches is 2 x 6 + 1 = 13: the fourth tag text (the decoded tags alone) is ASCII and does not depend on the variant, and both passes
# read ASCII alike, so it makes ONE key, not four.
_SCAN_KEY_CAP = 16


# Cyrillic Ze reads 3 and the table sends stroke look-alikes to l or i: join the classes.
_CLASS_MAP = str.maketrans("zl", "3i")


def _scan_key(text: str, step) -> str:
    """One scan key of one spelling variant of one tag text: the spelling variant to its fixed point, the class maps ``z`` to ``3`` and ``l``
    to ``i``, then only letters and digits (every character for which ``str.isalnum()`` is False, and every modifier letter (category
    Lm), is removed)."""
    s = _converge(text, step).translate(_CLASS_MAP)
    return "".join(ch for ch in s if ch.isalnum() and unicodedata.category(ch) != "Lm")


def scan_keyset(raw: str) -> frozenset[str]:
    """The scan keys of a text: a small set of strings made of letters and digits only. They are one of the views a DENY scan looks through
    (``scan_views``); a caller that scans uses ``scan_holds``, which reads ALL the views. Contract SK-1 to SK-6: the one parameter is
    ``raw``; at most 2 spelling variants x 4 tag texts = 8 keys for a text with no spacing mark (Mc) and no modifier symbol (Sk), 16 for a text
    with one (the keys of the text as it is and of the text without them), by construction (13 is the most a text can reach, because the
    decoded tags alone are ASCII; a guard raises ``TextTooLong`` above 16, which cannot happen), each at most as long as the weight of ``raw``; a text
    over the size rule raises ``TextTooLong``, a non-``str`` ``NotText``; over-matching is the safe side; there is no clock or deadline;
    the keys hold letters and digits only (spaces, punctuation, ``#``, ``~``, ``@``, ``|`` and U+FFFD are dropped). Invisible-only text
    gives ``frozenset()``, and no key is ever ``""``.

    Order: the size rule on the raw text; every modifier letter (Lm) is removed from the raw text, and, for a text that holds a spacing mark (Mc)
    or a modifier symbol (Sk), the keys are made twice, once of that text and once of the text with every Mc and Sk removed too (so a Telugu
    anusvara put between the letters of "password" cannot hide it, and the same character written instead of an "o" is still read as one); the tag texts T0 to T3 (a text with no
    tag character has only T0); for each text two spelling variants, A (table first, each letter by its own case) and B (case fold first),
    each repeated to its fixed point; the class maps; the drop. Every step acts on one character at a time except NFKC, which only joins,
    so a copy's key does not depend on its neighbours. No escape decoder runs (HTML entities, percent and backslash escapes come from the
    caller's own decoded view). Scan keys carry no ``key_tag()``: they are compared at once, never stored."""
    _checked(raw)
    return _scan_keys(raw)


def _scan_keys(raw: str) -> frozenset[str]:
    """``scan_keyset`` on a text that was already checked."""
    no_lm = "".join(ch for ch in raw if unicodedata.category(ch) != "Lm")
    # A spacing mark (Mc) or a modifier symbol (Sk) is a table source in a few cases (U+0C02, U+0C82, U+0D02, U+0D82 read as ``o``, U+0B03 as
    # ``8``): written INSTEAD of a letter it must still be read (the text as it is), and written between letters it must not split the word (the
    # text without them). So a text that holds one has the keys of BOTH, and a text that holds none has the keys it always had.
    no_marks = "".join(ch for ch in no_lm if unicodedata.category(ch) not in ("Mc", "Sk"))
    keys = {
        _scan_key(text, step)
        for variant in dict.fromkeys((no_lm, no_marks))
        for text in dict.fromkeys(_tag_texts(variant))
        for step in (_pass_a, _pass_b)
    }
    keys.discard("")
    # A fail-closed guard against a change of the construction above, not a truncation: more keys than the bound are refused, never cut off.
    if len(keys) > _SCAN_KEY_CAP:
        raise TextTooLong(
            f"a text made {len(keys)} scan keys, more than the {_SCAN_KEY_CAP} the construction allows"
        )
    return frozenset(keys)


_Bundle = tuple[tuple[tuple[bool, str], ...], tuple[str, ...], tuple[str, ...]]

# The views of one text, kept ONLY inside ``with scan_cache():`` (the variable is None everywhere else, so nothing is kept between calls). The
# key is the SHA-256 digest of the text, never the text; the scope keeps at most two texts and is emptied when it ends, also on an exception.
_SCAN_CACHE: contextvars.ContextVar[dict[str, _Bundle] | None] = contextvars.ContextVar(
    "hadavin_textnorm_scan_cache", default=None
)
_SCAN_CACHE_TEXTS = 2


@contextlib.contextmanager
def scan_cache() -> Iterator[None]:
    """A SCOPE in which the views of the texts being scanned are built once and shared: ``with scan_cache(): [scan_holds(text, v) for v in values]``
    costs one text pass for the shared part, not one per value. Outside a scope NOTHING is kept between calls, so a text that may hold a secret
    is not retained after the call that read it (the views are folded copies of the text, so they are as sensitive as it is). Inside the scope at most the last two texts are kept,
    under the SHA-256 digest of the text as the key (the key holds no text); the scope empties the cache when it ends, also when an exception
    ends it. A scope inside a scope shares the outer cache. The scope is per task and per thread (a ``contextvars`` variable)."""
    if _SCAN_CACHE.get() is not None:
        yield
        return
    token = _SCAN_CACHE.set({})
    try:
        yield
    finally:
        cache = _SCAN_CACHE.get()
        if cache is not None:
            cache.clear()
        _SCAN_CACHE.reset(token)


def _text_bundle(raw: str) -> _Bundle:
    """What every scan of one TEXT shares, whatever the protected value: the spelling readings (``_readings``, case folded, whitespace collapsed,
    with the marks-dropped ones), the squeeze views and the sorted scan keys. Built once per ``scan_cache`` scope (see there) and again for every
    call outside one; only the script views depend on the value, and they are cut from the marks-dropped readings in a pass over each. All
    tuples of ``str``, so nothing it returns can be changed. The text must be checked before."""
    cache = _SCAN_CACHE.get()
    key = ""
    if cache is not None:
        key = hashlib.sha256(raw.encode("utf-8", "surrogatepass")).hexdigest()
        hit = cache.get(key)
        if hit is not None:
            return hit
    bundle: _Bundle = (
        tuple(_readings(raw, casefold=True, collapse_ws=True, marks_dropped=True)),
        _squeezed(raw),
        tuple(sorted(_scan_keys(raw))),
    )
    if cache is not None:
        if len(cache) >= _SCAN_CACHE_TEXTS:
            del cache[next(iter(cache))]
        cache[key] = bundle
    return bundle


def _all_views(
    raw: str, scripts: frozenset[str] = frozenset(), bundle: _Bundle | None = None
) -> list[str]:
    """Every view of a checked text that a DENY scan looks through, empty ones included, no repeats, in a fixed order: ``fold_views``
    (case folded, whitespace collapsed, with the script views of ``scripts`` when given), then ``squeeze_views``, then the sorted ``scan_keyset``."""
    readings, squeezed, keys = bundle if bundle is not None else _text_bundle(raw)
    out: list[str] = []
    for view in (*(v for _kind, v in _pairs_from(readings, scripts)), *squeezed, *keys):
        if view not in out:
            out.append(view)
    return out


def scan_views(raw: str, value: str) -> tuple[str, ...]:
    """Every view of a TEXT that a DENY scan (a redaction, a blocklist, a has-secret check) looks through for the PROTECTED ``value``: ``fold_views``
    (case folded, whitespace collapsed, with the script views of ``value_scripts(value)``), ``squeeze_views`` and ``scan_keyset``, no repeats,
    empty views left out (an empty view of a text holds nothing). This is the one place that decides which scripts the text is read with:
    it takes them from ``value`` itself, so a caller cannot forget them: ``value`` has no default and ``None`` raises ``NotText`` (an unset
    configuration field must not turn into a scan without script views). A text with NO protected value (the injection check, which looks for ASCII steering phrases)
    uses ``scan_views_no_value``. At most 9 + 6 + 16 = 31 views (``fold_views``: three spelling variants, the same three with the Mc, Lm and Sk characters
    removed, and the script view of each of those three; ``squeeze_views``: the first six; ``scan_keyset``: sixteen at most). The bound 9 is by
    construction (seven was the highest ``fold_views`` count found, ``tests/test_textnorm_perf.py`` and the CHANGELOG name the search). Neither ``fold_views`` nor ``squeeze_views`` is enough alone: a value with no ASCII letter
    or digit has an empty ``squeeze_views``; ``scan_keyset`` adds the tag texts and the class maps. A scan holds a value when ANY view of the
    text holds ANY needle of the value, or the value with one extra letter of its own script: use ``scan_holds``."""
    _checked(raw, value)
    return tuple(view for view in _all_views(raw, _value_scripts(value)) if view)


def scan_views_no_value(raw: str) -> tuple[str, ...]:
    """The views of a TEXT for a check that has NO protected value (the injection check): the same views as ``scan_views`` without a script view,
    so at most 6 + 6 + 16 = 28. It is a separate function on purpose: ``scan_views`` refuses ``None``, so a missing value can never turn into a
    scan that reads no script."""
    _checked(raw)
    return tuple(view for view in _all_views(raw, frozenset()) if view)


_JAPANESE_GROUPS = frozenset({"HAN", "KANA"})


def _insertion_minimum(needle: str) -> int:
    """The fewest characters a script needle needs for the one-inserted-letter match. A needle of ONE script group takes that group's minimum
    (``defaults.TEXTNORM_INSERTION_MIN_CHARS`` for a group not listed in ``TEXTNORM_INSERTION_MIN_CHARS_BY_SCRIPT``). A needle of several groups takes
    the LARGEST of their minimums (the cautious side: an unmeasured mixture is not matched more loosely than its strictest part), EXCEPT a needle that
    holds both Han and kana and nothing else (a Japanese name or word): it takes the SMALLEST (Han's), because that mixture was measured on its own
    (CHANGELOG, order 137 D3) and its false-positive rate at that length stays within the bound of the other scripts."""
    by_script = dict(defaults.TEXTNORM_INSERTION_MIN_CHARS_BY_SCRIPT)
    groups = _scripts_in([needle]) or frozenset({""})
    minimums = [by_script.get(group, defaults.TEXTNORM_INSERTION_MIN_CHARS) for group in groups]
    return min(minimums) if groups == _JAPANESE_GROUPS else max(minimums)


def _one_off(window: str, target: str) -> bool:
    """True when ``window`` is ``target`` with exactly one character inserted anywhere (or is ``target`` plus nothing): the first mismatch splits
    them and the rest must agree after skipping one character of ``window``. ``len(window)`` is ``len(target) + 1`` (shorter at the end of a text:
    then it can only be an exact match)."""
    n = len(target)
    i = 0
    while i < n and i < len(window) and window[i] == target[i]:
        i += 1
    return window[i + 1 :] == target[i:] if i < n else True


def _holds_with_one_insertion(view: str, needle: str) -> bool:
    """True when ``view`` holds ``needle`` with at most ONE extra character inserted between two of its characters. Bounded and linear in the text
    for a text that is not built to defeat it: whatever the insertion is, one half of the needle is intact, so the text is searched for each half
    exactly (``str.find``) and each hit is checked against the other half by ``_one_off``. Needles of 2 characters or fewer, and the callers'
    length limits (``defaults.TEXTNORM_INSERTION_MAX_CHARS``), are the caller's business. The needle's two ends are not insertion points: a longer
    text around the needle is the exact match."""
    m = len(needle)
    h = m // 2
    first, second = needle[:h], needle[h:]
    start = view.find(first)
    while start != -1:  # the first half is intact: the insertion is in or before the second half
        stop = start + h
        if _one_off(view[stop : stop + (m - h) + 1], second):
            return True
        start = view.find(first, start + 1)
    start = view.find(second)
    while start != -1:  # the second half is intact: the insertion is in or after the first half
        lo = max(start - h - 1, 0)
        if _one_off(view[lo:start][::-1], first[::-1]):
            return True
        start = view.find(second, start + 1)
    return False


def _has_proof_character(value: str, scripts: frozenset[str]) -> bool:
    """True when the value has a squeeze view or a script view with at least one character in it (a letter or digit that an inserted separator
    cannot hide). A value without one is empty, invisible, punctuation or marks only."""
    return any(_squeezed(value)) or any(
        kind == "script"
        for kind, _view in _view_pairs(
            value, casefold=True, collapse_ws=True, marks_dropped=True, scripts=scripts
        )
    )


def _value_needles(value: str) -> list[tuple[str, str]]:
    """The needles ``scan_holds`` searches for: ``_needle_pairs`` (the minimums of ``scan_needles``) and the scan keys of the value that reach
    the minimum of their kind (squeeze; the digit minimum for a key of digits only). A key shorter than that is left out: it would be found in almost any text. Raises ``EmptyView`` or ``ViewTooShort`` (see ``scan_holds``)."""
    squeeze_min = _validated_minimums()[1]
    digit_min = _validated_minimums()[4]
    needles = _needle_pairs(value)
    known = {needle for _kind, needle in needles}
    for key in sorted(_scan_keys(value)):
        if key not in known and len(key) >= (digit_min if key.isdigit() else squeeze_min):
            needles.append(("key", key))
            known.add(key)
    return needles


def _needles_or_refuse(value: str, scripts: frozenset[str]) -> list[tuple[str, str]]:
    """``_value_needles`` for a checked value, with ``EmptyView`` in place of ``ViewTooShort`` when the value has no letter or digit at all."""
    try:
        return _value_needles(value)
    except ViewTooShort:
        if not _has_proof_character(value, scripts):
            raise EmptyView(
                f"a protected value of {len(value)} characters has no letter or digit that a scan can rely on: "
                "it would match every text, so it cannot be scanned for"
            ) from None
        raise


def scan_holds(text: str, value: str) -> bool:
    """THE DENY SCAN (redaction, blocklist, has-secret): True when ANY view of ``text`` (``scan_views(text, value)``) holds ANY needle of the
    protected ``value`` (``scan_needles`` and the scan keys of the value that reach their minimum), or holds a script needle of the value with
    one extra letter of the value's own scripts inserted (see "ONE INSERTED LETTER"). Over-matching is the safe side. REFUSES, and never answers
    False for a value it cannot scan: ``EmptyView`` if the value has no squeeze view and no script view with a character in it (it is empty,
    invisible or only punctuation, or only marks: nothing that an inserted separator cannot hide); ``ViewTooShort`` (from ``scan_needles``) if no
    squeeze or script view of the value reaches its minimum (a Latin value of three letters or fewer, a number of five digits or fewer, a
    value only a spelling view can find). A value in Chinese, Arabic, Hindi or Thai has no squeeze view but a script view, so it IS scanned. The
    caller treats every ``TextnormError`` like any other on a DENY path: REFUSE, and looks for such a value with its own exact search. Both
    arguments are checked (type, then size) before any work. Nothing of the text is kept after the call; to scan ONE text for
    hundreds of values at the cost of one text pass, call this inside ``with scan_cache():``."""
    _checked(text, value)
    scripts = _value_scripts(value)
    needles = _needles_or_refuse(value, scripts)
    bundle = _text_bundle(text)
    views = [view for view in _all_views(text, scripts, bundle) if view]
    if any(needle in view for view in views for _kind, needle in needles):
        return True
    limit = defaults.TEXTNORM_INSERTION_MAX_CHARS
    inserts = [
        needle
        for kind, needle in needles
        if kind == "script" and _insertion_minimum(needle) <= len(needle) <= limit
    ]
    if not inserts:
        return False
    script_views = {_script_view(view, scripts) for marks, view in bundle[0] if marks} - {""}
    return any(
        _holds_with_one_insertion(view, needle) for view in script_views for needle in inserts
    )


_LOG = logging.getLogger("hadavin_sdk.guard")
_FUZZY = "fuzzy"
_EXACT_ONLY = "exact_only"


class Coverage(NamedTuple):
    """What a scan can do for one registered protected value (``register_value``). ``coverage`` is ``"fuzzy"`` when the value has a script needle in
    the one-inserted-letter band (the copy of it with one extra letter of its own script is found too) and ``"exact_only"`` when it has not: a Latin
    or digit value (a separator, an invisible character, a look-alike or a different case is covered by the views, one inserted LETTER is not) or a
    script value outside the band (shorter than the minimum of its script, longer than ``defaults.TEXTNORM_INSERTION_MAX_CHARS``). ``narrowed`` is
    True when the value holds ASCII letters or digits but no squeeze needle reaches its minimum (a number of five digits next to a Chinese word):
    only the script part is searched, so a text with only the ASCII part is not found. ``reason`` says why, in words; ``needles`` counts them.
    Never the value or a needle."""

    coverage: str
    reason: str
    narrowed: bool
    needles: int


class CoverageRefused(TextnormError):
    """``register_value`` in strict mode found a value that a scan covers only EXACTLY (or only in part): a value we cannot cover loudly is
    acceptable, a value we cannot cover silently is not. The message says what to do: register the longer form, or register the value with
    ``strict=False`` and keep its own exact search for the inserted letter."""


def register_value(value: str, *, strict: bool | None = None) -> Coverage:
    """THE REGISTRATION CHECK of a protected value: what ``scan_holds`` can and cannot do for it, said out loud. It raises what ``scan_holds`` raises
    (``EmptyView``, ``ViewTooShort``: a value that cannot be scanned at all is REFUSED, never ignored), and otherwise returns a ``Coverage`` and logs it
    on ``hadavin_sdk.guard`` (INFO for ``fuzzy``, WARNING for ``exact_only`` or ``narrowed``; the log holds the length, never the value). With
    ``strict`` (the default is ``defaults.TEXTNORM_STRICT_COVERAGE``, True: the strict default is the one of the client profile) an ``exact_only``
    or ``narrowed`` value raises ``CoverageRefused`` instead of being registered. A caller that registers values calls this once per value; the
    modules of this package call it from no code path yet (the consumers arrive with the redaction package, see the CHANGELOG)."""
    _checked(value)
    if strict is None:
        strict = defaults.TEXTNORM_STRICT_COVERAGE
    if type(strict) is not bool:
        raise NotText("strict must be a bool or None")
    needles = _needles_or_refuse(value, _value_scripts(value))
    limit = defaults.TEXTNORM_INSERTION_MAX_CHARS
    script_needles = [needle for kind, needle in needles if kind == "script"]
    if any(_insertion_minimum(n) <= len(n) <= limit for n in script_needles):
        coverage, reason = (
            _FUZZY,
            "a script needle is in the one-inserted-letter band: one extra letter of its own script is found",
        )
    elif script_needles:
        coverage, reason = (
            _EXACT_ONLY,
            (
                "every script needle is outside the one-inserted-letter band (shorter than the minimum of its script, or longer than "
                f"{limit}): an inserted letter hides the value"
            ),
        )
    else:
        coverage, reason = (
            _EXACT_ONLY,
            "Latin letters or digits: a separator, an invisible character, a look-alike or another case is covered, one inserted letter is not",
        )
    narrowed = any(ch.isascii() and ch.isalnum() for ch in value) and not any(
        kind == "squeeze" for kind, _needle in needles
    )
    result = Coverage(coverage, reason, narrowed, len(needles))
    level = logging.INFO if coverage == _FUZZY and not narrowed else logging.WARNING
    _LOG.log(
        level,
        "textnorm: protected value of %d characters registered with coverage=%s narrowed=%s (%s)",
        len(value),
        coverage,
        narrowed,
        reason,
    )
    if strict and (coverage == _EXACT_ONLY or narrowed):
        raise CoverageRefused(
            f"this protected value ({len(value)} characters) is covered {'only in part' if narrowed else 'only exactly'}: {reason}"
            f"{'; its ASCII part has no needle of its own, so a text with only that part is not found' if narrowed else ''}. "
            "A value that cannot be covered is REFUSED in strict mode (the setting defaults.TEXTNORM_STRICT_COVERAGE, True by default, or strict=True), never silently accepted. "
            "What to do: register the longer form, or register it with strict=False and keep your own search for the inserted letter"
        )
    return result


# The hidden channel: characters that show nothing and can carry text or bits. Exactly two rules: (1) the tag block U+E0000 to U+E007F;
# (2) every Variation_Selector other than the two emoji selectors U+FE0E and U+FE0F (Mongolian free selectors U+180B-180D and U+180F,
# U+FE00-FE0D, U+E0100-E01EF). Other invisible characters, combining marks, whitespace, U+FE0E, U+FE0F and characters written as HTML
# entities are NOT counted and are unbounded: ``fold`` drops them, and the look-alike check (not this signal) catches a known value
# hidden with them. The text is read RAW: no escape decoder runs, so a caller that checks decoded views calls this on each view.
_HIDDEN_CHANNEL = re.compile(
    r"[\U000e0000-\U000e007f\u180b-\u180d\u180f\ufe00-\ufe0d\U000e0100-\U000e01ef]"
)


def has_hidden_channel(text: str) -> bool:
    """True when the RAW ``text`` holds a tag character or a free variation selector (the two rules above). A caller decides what to do;
    England, Scotland and Wales flag emoji (tag letters) and an ideographic variation selector after a Japanese name are reported (the safe
    side)."""
    _checked(text)
    return _HIDDEN_CHANNEL.search(text) is not None


def require_pinned_unidata(expected: str | None = None) -> None:
    """GUARD ENTRY POINT for pilot and prod (the application start-up of the package that wires this module in calls it): raise ``UnidataMismatch`` unless the interpreter's Unicode data
    version is ``expected`` (default ``defaults.TEXTNORM_PINNED_UNIDATA``, read when the function runs, so a patched constant is seen).
    Fail closed: it never warns and never returns on a mismatch. A demo run or a CI run may use another version; their keys carry
    ``key_tag()``. The message says what to do: for the pin it names Python 3.13."""
    _validated_pins()
    if expected is None:
        expected = defaults.TEXTNORM_PINNED_UNIDATA
    if unicodedata.unidata_version != expected:
        fix = (
            f"run Python {defaults.TEXTNORM_PINNED_PYTHON} (Unicode {expected})"
            if expected == defaults.TEXTNORM_PINNED_UNIDATA
            else f"run a Python with Unicode {expected}"
        )
        raise UnidataMismatch(
            f"this Python uses Unicode {unicodedata.unidata_version}; {fix} for pilot or prod"
        )


_SCRIPT_STARTS = tuple(first for first, _, _ in _scripts.RANGES)  # sorted: the lookup is a bisect
_SCRIPT_NAMES = _scripts.SCRIPT_NAMES
# Scripts that may share a word with Latin letters (UTS #39 allows Latin with these in one identifier: Chinese, Japanese, Korean). Every
# other script in the Unicode data (Common and Inherited are neutral) next to Latin is a deny signal.
_EXEMPT_WITH_LATIN = frozenset({"Han", "Hiragana", "Katakana", "Hangul", "Bopomofo"})
# What has_mixed_script removes before it splits words: the dropped categories and the modifier symbols (Sk). A symbol has no script, so removing it
# joins the two halves of a word it split, the same rule that applies to invisible characters.
_MIXED_REMOVED = _DROP_CATEGORIES | {"Sk"}
_UNIT_SYMBOLS = frozenset(
    map(chr, (0xB5, 0x2126))
)  # micro sign, ohm sign: unit symbols (5 us, 50 kOhm) that NFKC turns into Greek letters


def _script(ch: str) -> str | None:
    """The Unicode script of ``ch`` from the generated data (``_scripts``, Scripts.txt of the pinned version), or None for Common, Inherited
    and a code point the data does not list."""
    cp = ord(ch)
    i = bisect.bisect_right(_SCRIPT_STARTS, cp) - 1
    if i >= 0:
        first, last, index = _scripts.RANGES[i]
        if first <= cp <= last:
            return _SCRIPT_NAMES[index]
    return None


def has_mixed_script(text: str) -> bool:
    """True if any word mixes Latin letters with letters of another script, except Han, Hiragana, Katakana, Hangul and Bopomofo (UTS #39
    allows those with Latin), or a Latin letter with a spacing mark of another script that no letter of the word owns. The script of a letter comes
    from the generated data of the pinned Unicode version (``guard/_scripts.py``, made by ``tools/gen_confusables.py`` from ``Scripts.txt``), so
    every script the data names is covered: Cyrillic, Greek, Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu, Runic, Tamil and the rest. Invisible
    characters, non-spacing marks and modifier symbols (Sk) are removed first (a zero-width space or a ``^`` inside a word does not split it).
    A word is a run of letters, digits, ``_`` and spacing marks (Mc). The micro sign and the ohm sign are exempt (unit symbols); a Greek mu or omega
    typed as a Greek letter next to Latin letters is flagged. The micro and ohm signs are removed BEFORE the analysis, so a word that holds only such a
    sign plus a look-alike letter (micro sign + Cyrillic a) is not flagged by this function; the fold and the table still see the Cyrillic letter. A
    fail-closed deny signal that does not depend on the look-alike table. Digits and punctuation are script-neutral.

    Two rules: (a) a Latin letter and a letter of another script in one word; (b) a Latin letter and a spacing mark (Mc) whose script group
    is not Latin and is the group of no letter in the word ("ali" + U+0903 + "ce" and "iPhone" + U+093E are flagged; a Devanagari mark next to a
    Devanagari letter adds nothing to what rule (a) says about that letter: "Ramesh" + a Devanagari syllable is flagged by rule (a)). A modifier letter (Lm) is a letter: NFKC turns most into their Latin letter, so it never flags by itself;
    the DENY check catches an inserted one. A non-spacing sign (Mn) of another script inserted into a Latin word is not flagged here (it is
    removed first; the fold drops it, so the DENY check catches it).

    Honest limits: rule (a) uses the Script property, not Script_Extensions, so a letter shared by several scripts counts as the one script the data
    gives it; rule (b) names the script group of a mark by its Unicode name (``_script_of``). Greek letters next to Latin ones are flagged, so a
    technical word with a Greek delta or theta glued to Latin letters is a false positive; only the micro and ohm signs are exempt. A word of Latin
    and Arabic, Devanagari, Thai and so on is flagged too. The deny is fail-closed by design. A code point added to Unicode after the pinned
    version is not in the data and counts as neutral."""
    _checked(text)
    kept = "".join(
        " " if ch.isspace() else ch  # a newline or tab separates words, as in fold
        for ch in text
        if ch.isspace()
        or (
            ch not in _UNIT_SYMBOLS
            and ch not in FILLERS
            and unicodedata.category(ch) not in _MIXED_REMOVED
        )
    )
    return any(_word_is_mixed(word) for word in _words(unicodedata.normalize("NFKC", kept)))


def _words(text: str) -> list[str]:
    """The words of ``text``: maximal runs of alphanumeric characters, ``_`` and spacing combining marks (Mc), so a spacing mark does not split a word."""
    words: list[str] = []
    start = -1
    for i, ch in enumerate(text):
        if ch.isalnum() or ch == "_" or unicodedata.category(ch) == "Mc":
            if start < 0:
                start = i
        elif start >= 0:
            words.append(text[start:i])
            start = -1
    if start >= 0:
        words.append(text[start:])
    return words


def _word_is_mixed(word: str) -> bool:
    """Rule (a): a Latin letter and a letter of another script (the data script, ``_script``; ``_EXEMPT_WITH_LATIN`` do not count) in one word. Rule (b): a
    Latin letter and a spacing mark (Mc) whose script group is not Latin and is the group of no letter of the word."""
    latin = other = False
    marks: list[str] = []
    for ch in word:
        if not ch.isalpha():
            if unicodedata.category(ch) == "Mc":
                marks.append(ch)
            continue
        script = _script(ch)
        if script == "Latin":
            latin = True
        elif script is not None and script not in _EXEMPT_WITH_LATIN:
            other = True
        if latin and other:
            return True
    if not (latin and marks):
        return False
    own = {_script_of(ch) for ch in word if ch.isalpha()}
    return any(group != "LATIN" and group not in own for group in map(_script_of, marks))
