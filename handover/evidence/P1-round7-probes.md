# P1 round 7 probes (run by the resolve session, Python 3.13, `python3 -I`, read-only, against the `748849c` snapshot `src/hadavin_sdk/guard/`)

Nothing here is a measurement of the final code. Two facts the resolve needs, and the output copied from the terminal.

## Probe A: the characters the look-alike design could use as a stand-in for a placeholder

`textnorm.fold` at `748849c` on single characters (casefold and whitespace removal off, then on for the second line):
- U+FFFD stays U+FFFD; `fold("ab" + U+FFFD + "cd")` is `ab` + U+FFFD + `cd` (not dropped).
- `|`, `#`, `~`, `@` each stay themselves.
- `fold("ab#cd", casefold=True, collapse_ws=True)` is `ab#cd`.

Reading: at `748849c` U+FFFD survives. The P1 ticket (revision 8, entity-step paragraph) says P1b DROPS U+FFFD "everywhere (identity and scan keys)". So the design's stand-in character is dropped by `scan_keyset` as P1b is written, and the text on both sides of a placeholder would be joined. See finding RES-1 in `P1-round7-resolve.md`.

## Probe B: sources in the table whose value is a digit (ADV-R7-13)

`_confusables.TABLE` has 677 entries. Entries with an ASCII-digit value whose source is not category Nd: 62. Of these, the sources of letter categories (L*) by digit value: 2: 8, 3: 15, 4: 3, 5: 2, 6: 9, 7: 4, 8: 5, 9: 8 (total 54).
Names of the first sources per value (the shape they imitate): 2 = LATIN CAPITAL LETTER TONE TWO, COPTIC CAPITAL LETTER HORI, GEORGIAN CAPITAL LETTER YN; 3 = LATIN CAPITAL LETTER EZH, LATIN CAPITAL LETTER YOGH, CYRILLIC CAPITAL LETTER ZE, CYRILLIC SMALL LETTER ZE; 4 = CHEROKEE LETTER SE; 5 = LATIN CAPITAL LETTER TONE FIVE; 6 = COPTIC CAPITAL LETTER SHIMA, CYRILLIC SMALL LETTER BE; 7 = HANUNOO LETTER BA, CYRILLIC SMALL LETTER TALL TE; 8 = LATIN CAPITAL LETTER OU, LATIN SMALL LETTER OU; 9 = COPTIC CAPITAL LETTER DIALECT-P HORI, LATIN CAPITAL LETTER CON.
Entries whose value is the ASCII letter `b`: 9. Entries whose value is the digit `6`: 9.

Reading: these sources are named and drawn for the shape of a digit (tone two, tone five, ezh, "con"), so a known value that holds that digit and is written with one of them is already found (the source reads as the same digit). A class map would only add a case when a known value holds a LETTER and is written with a digit-shaped source (a leetspeak style rewrite). Cyrillic Ze (U+0437) is the one entry used both as the letter z and as the digit 3, which is why it has a class map.

Not done: no per-source visual comparison with an ASCII letter (that needs a font and a judgement); the statement "digit-shaped, not letter-shaped" rests on the Unicode names above and is stated as such.
