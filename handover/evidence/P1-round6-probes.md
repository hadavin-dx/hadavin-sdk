# P1 round 6 probes (run by the resolve session, Python 3.13.18, unicodedata 15.1.0, `python3 -I`, 2026-11-05)
No server, no repository code, no suite. Scripts were throwaway (not kept); the fold used in the probe is a copy of `fold` lines 65-77 of `748849c` `textnorm.py` WITHOUT the confusables table (the table does not matter for these claims). Output below is copied from the terminal.

## Probe A (ADV-R6-1, ADV-R6-2, COR-R6-4, COR-R6-5, COR-R6-7)
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
json.loads lone surrogate -> 'a\ud800b' len 3 category Cs
utf-8 encode raises UnicodeEncodeError
fold 10000 x U+D800 -> ''
Cn count 824718 first non-nonchar unassigned example 0x379
fold 8 x unassigned U+0378 -> ''
noncharacters 66 all Cn: True
isspace in Cc/Zl/Zp: ['0x9', '0xa', '0xb', '0xc', '0xd', '0x1c', '0x1d', '0x1e', '0x1f', '0x85', '0x2028', '0x2029']
fold of 8 x U+000C -> '        '
Cc minus tab/LF/CR: 62  of those isspace: 7
Co+Cs count 139516 bits/char 17.09
141,349 set bits/char 17.11 ; 64 isolated chars = 136.9 bytes
Cn bits/char 19.65
IVS example:  '辻󠄀' fold -> '辻'
Mongolian FVS example: 'ᠠ᠋' category U+180B Mn
fillers default-ignorable? (Lo, not Cf/Cc/Co): [('0x115f', 'Lo'), ('0x1160', 'Lo'), ('0x3164', 'Lo'), ('0xffa0', 'Lo'), ('0x2800', 'So')]
```
Reading: (1) a lone surrogate is reachable: `json.loads` returns a `str` holding one, and only a later UTF-8 encode raises; `fold` drops it (10,000 x U+D800 gives an empty string), so with rev 7 the key is empty and `has_hidden_channel` is False. (2) Unassigned code points (Cn, 824,718 of them, 66 of them noncharacters) are dropped the same way (8 x U+0378 gives an empty string); Cn is the largest alphabet, 19.65 bits per character. (3) Co + Cs = 139,516 code points, 17.09 bits per character; the rev 7 set is 141,349 code points, 17.11 bits, so 64 isolated characters carry about 137 bytes (the reviewer's figure holds). (4) The 9 % example of rev 7 (2.9 KB) is 23,593 characters at 1 bit each; it is right only for a two-symbol code. (5) Whitespace controls: 10 code points of Cc/Zl/Zp are `str.isspace()`: U+0009, 000A, 000B, 000C, 000D, 001C to 001F, 0085, plus U+2028, U+2029 (Zl, Zp); `fold` turns U+000C x 8 into 8 spaces, it does not drop them, so the Cc count of rev 7 (62, which excludes only tab, LF, CR) includes 7 characters that `fold` keeps as spaces (Cc minus tab/LF/CR = 62, of which 7 are `isspace`; Cc minus all ten = 55). (6) The four fillers U+115F, U+1160, U+3164, U+FFA0 are category Lo and U+2800 is So (so none is in Cf, Cc, Co); whether they are Default_Ignorable_Code_Point is NOT probed (`unicodedata` has no such property): UNVERIFIED. (7) `fold("辻" + U+E0100)` gives `辻`: an ideographic variation selector is dropped, as rev 7 says; the example is ordinary Japanese name data.

## Probe B (ADV-R6-2, ADV-R6-5: capacity numbers)
```
assigned non-ASCII non-selector code points (incl. Co): 286958 bits 18.13
without Co: 149490 bits 17.19
512 selectors x (bits+1) = 1164 bytes
prose-use Cf list size 27 all Cf: True bits 4.75
share channel at cap: 10% of 262144 = 26214 chars x 4.75 bits = 15581 bytes
N tier: 4 chars x 19.65 bits = 9.8 bytes ; 2.9KB example check: 9% of 262144 = 23593 chars x 1 bit = 2949 bytes
Cf outside the prose list and outside tags: 46
['0x890', '0x891', '0x180e', '0x2061', '0x2062', '0x2063', '0x2064', '0x206a', '0x206b', '0x206c', '0x206d', '0x206e', '0x206f', '0xfff9', '0xfffa', '0xfffb', '0x110bd', '0x110cd', '0x13430', '0x13431', '0x13432', '0x13433', '0x13434', '0x13435', '0x13436', '0x13437', '0x13438', '0x13439', '0x1343a', '0x1343b', '0x1343c', '0x1343d', '0x1343e', '0x1343f', '0x1bca0', '0x1bca1', '0x1bca2', '0x1bca3', '0x1d173', '0x1d174', '0x1d175', '0x1d176', '0x1d177', '0x1d178', '0x1d179', '0x1d17a']
```
Reading: the capacity of the emoji-selector rule is not 64 bytes: with a free base it is about 1.2 KB at 512 selectors (my bound; the reviewer's "about 5,300 bits, 730 bytes" has no stated basis: UNVERIFIED, mine is the larger and used). A named list of 27 prose-use format characters (the list in the probe, all category Cf) carries 4.75 bits per character; the share channel (10 % of 262,144 characters) is then about 15.6 KB, which is the honest price of letting Persian, Arabic and Indic text through. The other 46 Cf code points outside tags are listed above (Mongolian vowel separator, invisible math operators, deprecated format controls, interlinear annotation, Egyptian hieroglyph format controls, Duployan and musical formatting).

## Probe C (COR-R6-3: ruff line)
`git show ce70eb5:pyproject.toml | grep -n extend-select` printed `72:extend-select = ["B", "DTZ", "I", "S", "TID", "UP"]`; the same grep on the `748849c` snapshot printed the same line 72. The reviewer's "74 in ce70eb5" is wrong; the ticket's "72 in both" is right.

## Not probed
Timing of any scan; DerivedCoreProperties.txt; P2d's real k (P2d rev 4 was written during this window, see the resolve); CI behaviour; pickle and copy of `PreparedNeedles`.
