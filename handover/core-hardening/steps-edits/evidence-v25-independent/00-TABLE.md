# 00-TABLE: independent evidence for the v25 package (EVIDENCE RUNNER: raw results, no judgement)
Everything ran from `frozen/` (sha256 in 01-sha256-frozen.txt; re-checked after all runs: 0 files changed). Originals were not edited.
Frozen also holds files the brief did not list but the build/check need: LEAD-RELEASE-NOTE-v9-SOURCE.md, v25-OPEN-FOR-LEAD-SOURCE.md, v25-CHANGES.md.

| # | Command | Exit | Result line | File |
|---|---|---|---|---|
| 1 | `python3 -B build-v25.py <scratch>` then `cmp` against frozen built files | 0 | 4 of 4 byte-identical (A, B, lead note v9, open-for-lead) | 02-rebuild-output.txt |
| 2 | `python3 -B check-v25.py` (in frozen) | 0 | `check-v25: 0 failure(s)` | 03-check-output.txt |
| 3 | `python3 -B mut25.py` (in frozen, 25 s) | 0 | `TOTAL plants 111: caught 111, missed 0, anchor-not-found 0` | 04-mut25-output.txt |
| 4a | own extractor 05-extract-shell.py: `bash -n` on every fenced block | 2 (both) | Each sheet has exactly ONE fenced block; it is the sample numbers message (plain text, not shell), so `bash -n` rightly rejects it. There is NO fenced shell span in either sheet. | 05-bash-n-output.txt |
| 4b | own 05b-inline.py: `bash -n -c` on each unique inline `code` span (37 per sheet) | 6 spans fail per sheet | The 6 failures are not commands: `-b@`, `-c@`, `-rw-------` (my call passed them as bash flags), `<...>`, `run-<run name>`, `take-<run name>` (placeholders). The other 31 parse. This is a syntax check only; no command was executed. | 05b-inline-output.txt |
| 5 | own 06-numbers.py: all $ / US$ / USD amounts and minute figures | 0 | Dollar values in A and B (identical): 0.27, 0.81, 3.00, 15.00, 189.00 only. Not allowed-list violations: none. 13.21, 14.33 and 860 s do NOT occur in either sheet (they are in other files). Minute figures: 2 (page retry), 5 (notice compare, and "Type y" minutes sample), 10 (cancel-by margin; last resort 10 min; film pause 10), 3 silence, 40 give-up (sample). All explained in the sheet text. | 06-arithmetic-output.txt, 06b, 06c, 06d |
| 6 | `wc -w` and python split | 0 | A 6495 words, B 6467 words (limit 6500; margin only 5 for A, 33 for B). Regex `\w+` tokenisation gives 6520 / 6490: a different counter would put A over 6500. | 07-wordcount.txt |
| 7 | 08-banned.py (BANNED read from tests/test_no_reference_material.py, 10 entries) over the whole steps-edits folder incl. this evidence folder | 0 | total hits 0 (no string printed) | 08-banned-output.txt |
| 8 | 09-own-plants.py: 15 own plants on scratch copies | 0 | caught 9 of 15, MISSED 6 (see below) | 09-own-plants-output.txt |

## Step 8: my 15 plants (none are in mut25.py). Plants go into the SOURCE, rebuild, run check-v25; N07 goes into the built B file.
| id | plant | check-v25 |
|---|---|---|
| N01 | `IST = UTC + 5:30` changed to `UTC + 4:30` in the words list | MISSED |
| N02 | post-by line swapped to `20:30 UTC = 15:00 IST` | caught (C04) |
| N03 | key-looking string (built from parts) added | caught (C55) |
| N04 | `if 7.4 never happened` -> `7.5` | caught (C14j) |
| N05 | R5 "deleted or archived" -> "deleted or deleted" | MISSED |
| N06 | STOP RULE paragraph removed | caught (C23) |
| N07 | A wording left in built B file | caught (C01) |
| N08 | expected total 0.81 -> 0.84 | caught (C04) |
| N09 | pointer `(7.9)` -> `(7.19)` | caught (C19) |
| N10 | removed "(else do not press Enter: do the card)" before the cancel path | MISSED |
| N11 | post-by date Wed 25 Nov -> Thu 26 Nov (weekday kept consistent) | MISSED |
| N12 | R7 "You delete only..." -> "Only ... are deleted" (passive) | MISSED |
| N13 | `@example.com` -> `@example.org` for person A | caught (C57) |
| N14 | `date -u` -> `date` in 7.3 | MISSED |
| N15 | 60 filler words (A = 6555 words) | caught (C07) |

Missed = 6 real gaps in check-v25.py (N01, N05, N10, N11, N12, N14). The checker reported 0 FAIL lines and exit 0 on each. Not fixed here (evidence runner never edits originals); the lead decides.
Note: N01 means the one place the IST offset is explained to the owner is unchecked; C04 only checks UTC/IST pairs against 5:30 hard-coded in the checker. N11 means the post-by date in the sheet source is not tied to facts (the heading text came from the source, so changing source and not facts passes).

## Could not run / not checked
- No fenced shell spans exist, so (4) could only be done on the inline spans; commands were parsed, never executed.
- Dollar scan is regex based: amounts written without $/USD (e.g. "0.27" alone) were found separately in 06b and are all in the allowed list.
- LEAD-RELEASE-NOTE-v9.md and v25-OPEN-FOR-LEAD.md were checked only through rebuild, check-v25 and the banned scan, not through (4) to (6), as the brief limits those to the two sheets.
- I did not verify the factual content of the sheets (only mechanical checks).
