# P1 round 8 probes (run by the revision 9 author, Python 3.13.18, Unicode 15.1.0, `python3 -I`, 2026-11-05 21:4x UTC)
Read-only: no repository code, no suite, no server. The script is `probe8.py` in the session scratchpad (not kept in the repository; it reads the `748849c` snapshot `_confusables.py` by path only). Output below is copied from the terminal. **What this is NOT:** a measurement of the final code. Rows R6-A to R6-F run a small stand-in for rules 5 to 7 (tier P is the 27-character list, tier N is only the four characters the rows use), so they check the ARITHMETIC of the rows (the percentages and which side of each limit they fall on), not the ticket's `has_hidden_channel`. The selector rule 3 and rule 4 are not run. Capacities are arithmetic from the same script.

```
python 3.13.18 unidata 15.1.0
Cc 65
Cf 170
Co 137468
Cs 2048
Cn 824718
Mn 1985
Me 13
Zl 1
Zp 1
tier P size 27 all Cf True
Mn3 cats ['Mn', 'Mn', 'Mn'] fillers ['Lo', 'Lo', 'Lo', 'So', 'Lo']
tier N size 964312 {'Cc': 55, 'Mn': 3, 'Cn': 824687, 'Cf': 46, 'Lo': 4, 'So': 1, 'Cs': 2048, 'Co': 137468} sum check 964312
isspace code points 29
log2 N 19.88 ; positions among 262144 (upper bound, one char) 18.00
tier N limit 1 symbols 19.9 bits = 2.48 bytes; log2 C(262144,1)=18.0; total 37.9 bits = 4.73 bytes; with 18-bit bound per char 37.9 bits = 4.73 bytes
tier N limit 4 symbols 79.5 bits = 9.94 bytes; log2 C(262144,4)=67.4; total 146.9 bits = 18.37 bytes; with 18-bit bound per char 151.5 bits = 18.94 bytes
tier P bits/char 4.755
tier P total branch at 64 : 64 x (4.75 + 18) = 1456 bits = 182.0 bytes
tier P total branch at 16 : 16 x (4.75 + 18) = 364 bits = 45.5 bytes
share branch: 26214 chars x 4.75 = 124645 bits = 15581 bytes = 15.22 KB(1024) ; H(0.1)=0.469 positions 122944 bits = 15368 bytes ; total 30949 bytes
selector: bits/selector 18.19 ; 512 symbols 9313 bits = 1164 bytes ; positions exact 5340 bits = 668 bytes ; approx 512*(log2(512)+1.44)... 5345 ; total 1832 bytes
note log2(262144/512)=9.00 + 1.44 = 10.44 per selector
12 chars x 7 bits = 84 bits = 10.5 bytes
R6-A len 150 ZWNJ 17 pct 11.33 rule5 False rule6 True rule7 False -> True expected True OK
R6-B len 200 ZWNJ 17 pct 8.50 rule5 False rule6 False rule7 False -> False expected False OK
R6-C len 100 ZWNJ 16 pct 16.00 rule5 False rule6 False rule7 False -> False expected False OK
R6-D len 10000 ZWNJ 17 pct 0.17 rule5 False rule6 False rule7 False -> False expected False OK
R6-E len 200 ZWNJ 20 pct 10.00 rule5 False rule6 False rule7 False -> False expected False OK
R6-F len 150 ZWNJ 17 pct 11.33 rule5 False rule6 True rule7 False -> True expected True OK
R6-F weighted-length denominator: W = 73 + 17 + 60*3 = 270 ; 17/W = 6.3%
1 isolated U+E000 rule7 False
2 isolated U+E000 rule7 True
10 isolated rule7 True
1 FDD0 rule7 False
2 FDD0 rule7 True
5 FDD0 rule7 True
2 ESC rule7 True
64 consecutive ZWSP in 1000 chars: rule5 True rule6 (share 6.4%) False
200 colour emoji: selectors are not tier P: 0
200 emoji with ZWJ? n/a
table entries 677 DATA_VERSION 18.0.0 MAX_VALUE_LEN 3
all-digit values 71 non-Nd 62 letters 54
letters by value {'2': 8, '3': 15, '4': 3, '5': 2, '6': 9, '7': 4, '8': 5, '9': 8}
value b entries 9 value 6 entries 9
Ze U+0437 -> 3 U+0417 -> 3
be U+0431 -> 6
```

## Reading (what the numbers say)
1. Category counts and tier sizes are unchanged from round 6 (Cf 170, Cc 65, Co 137,468, Cs 2,048, Cn 824,718). Tier P is 27 characters, all Cf. Tier N is 964,312 code points (Cc 55 + Mn 3 + Cn 824,687 + Cf 46 + the five fillers (4 Lo + 1 So) + Cs 2,048 + Co 137,468); the sum check printed equals the size.
2. Capacity at the NEW limits (arithmetic, "positions" bounded by 18 bits per character, the same method as revision 8): tier N at 1 character: 19.88 + 18.0 = 37.9 bits = **4.73 bytes** (the resolve wrote "about 4.8 bytes"; the exact figure is 4.73, the ticket uses "about 4.7 bytes"). Tier P total branch at 16: 16 x (4.75 + 18) = 364 bits = **45.5 bytes**. Tier P share branch (10 %): 15,581 bytes by symbols, 15,368 bytes of positions, 30,949 bytes in all (unchanged: the share limit did not move). Selector rule 3 at 512: 9,313 bits = 1,164 bytes by symbols plus 5,340 bits (exact log2 of the binomial; the approximation 512 x 10.44 gives 5,345) = 668 bytes of positions: **1,832 bytes, about 1.8 KB**. A 12-character secret at 7 bits is 84 bits = 10.5 bytes: it does not fit the tier N branch (4.73 bytes) and fits the other three.
3. Rows R6-A to R6-F: every row falls on the side the ticket states (A TRUE at 11.33 %, B FALSE at 8.50 %, C FALSE at 16 characters, D FALSE at 0.17 %, E FALSE at exactly 10 %, F TRUE at 11.33 % by `len`; by a weighted denominator it would be 17 / 270 = 6.3 %, below the limit, which is what row F separates).
4. Tier N rows at limit 1: 1 isolated U+E000 FALSE, 2 TRUE, 10 TRUE; 1 x U+FDD0 FALSE, 2 TRUE, 5 TRUE; two ESC colour sequences TRUE (ANSI is tier N: a stated false refusal). 64 consecutive ZWSP in a 1,000-character text: rule 5 TRUE, rule 6 FALSE (6.4 % is below 10 %), so that row tests rule 5, not rule 6.
5. Digit-valued table sources (probe B of round 7, re-run): 71 all-digit values, 62 of them from a source that is not category Nd, 54 of those letters, by value 2: 8, 3: 15, 4: 3, 5: 2, 6: 9, 7: 4, 8: 5, 9: 8; 9 entries read `b`, 9 read `6`; Cyrillic Ze U+0437 and U+0417 read `3`, Cyrillic small Be U+0431 reads `6`. (Round 7 wrote the same counts.) The table has 677 entries and the longest value has 3 characters.

## Not run
`has_hidden_channel`, `scan_keyset`, `scan_match`, any timing (S_call, SK-5 per-call cost), the entity step, the ideographic-selector row, the U+2063, U+0000, U+0600 and bidi-pair runs, `fold` on U+FFFD (probe A of round 7 stands; it is about `748849c`, not about P1b), Python 3.12 and 3.14.
