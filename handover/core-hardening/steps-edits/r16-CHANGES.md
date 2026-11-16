# Round 16 changes (builder). Failures and open items FIRST.

## 1. What is NOT done or NOT met (plain)
1. **L-LEN is not met.** The sheet after the Apply now rows is 18,632 words (counted in `scratch16/scratch-apply11/OWNER-STEPS-realrun-v3.md`, which the checker rebuilds on every run), against the order of at most 6,300 words. The row text of E-48 grew from 3,492 to 3,647 words (the card, key steps D.1 to D.5 and the new word were added); 928 words of detail moved into Appendix K (key steps A, C, D, F, G, H, I). Nothing was deleted. The owner-facing NEW text of all OWNER-STEPS rows grew from 15,780 to 16,464 words. A real cut to 6,300 words needs the studio lead to say what the "one sheet" is (the applied OWNER-STEPS file, or a new short owner card) and a separate pass; I did not do it and did not pretend to.
2. **E-09 "What the assistant can reach" was not moved to an appendix block (K-8).** Not done (time).
3. **E-12 "Block 2" labels and the reply-line wording** (stranger minor): only "Your reply" and "list of test items" were fixed; the "Block 2, point N" labels are still as in round 15. Not done.
4. **E-37 item (4)**: the own list is widened to "a secret you saved" (security m8). The sentence about where the key file is placed was not rewritten. Not done.
5. **Confirmation o is still OPEN** (owner or studio lead): is 18:00 UTC = 23:30 IST, the time you START TYPING, acceptable? With 1 minute of typing and 860 seconds of take the margin is 3 minutes 40 seconds (round 15 said 4 minutes 40 seconds; that ignored the typing). OWNER-OPEN question for the owner: "Do you accept a latest start of 18:00 UTC = 23:30 IST on Mon 23 Nov 2026, or do you want an earlier one?"
6. **Route A or route B (ND15) is not chosen.** Both stay, the assistant recommends route B in one sentence, the owner reads the last-used time of the older key first. Route B keeps a live paid key and its copy on the laptop for up to five days: the exposure is stated in ND15 and in K-D, not removed.
7. Nothing was run on the take. No click path was checked (key list page, clipboard setting). The EGM review of this result is for the studio lead.
8. Limits of the checker, honestly: two of my negative controls (`r16wd`, `r16code`) are caught by older checks, not by a new r16 check; the nine mutations of the independent runner were planted on r16 text (controls `r16m15` to `r16m51b`), not re-planted on r15 and re-run through verify15.

## 2. Findings fixed (class, place, check)
| Finding | Fix | Check that fails if it is undone |
|---|---|---|
| Security F1 | new word `key gone, no more decisions` (key step B, D.5, E-55); `key revoked` counts as the confirmation only when typed after 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 with no earlier `no more takes` | r16F1word, r16F1time |
| Security F2 | exact addresses `take-<id>-a/-b/-c@example.com`, at most 3, in E-04, E-42 and new row E-62 (input line 112); "made-up names" removed | r16F2a, r16F2b, r16F2c |
| Security F3 | shred part (d) = password files and editor copies; own list = every file that holds a secret you saved; `shred done 2` includes (c) and (d) | r16F3 |
| Security F4 | one numbered order (the card in E-48, E-16, E-55); item 1 never starts while the key copy exists and the key is not revoked; the E-16 sentence about doing items first is gone | r16F4a to r16F4d |
| Security m1 to m8 | take folder new and empty, never home; owner reads the item-1 list, stop if a recording is inside; `please stop looking` before the click that creates a key; `ok stand-in test` and `ok flow rehearsal`; alarm 3 at 18:09 UTC = 23:39 IST; Counts paragraph (60 rows, 48 Apply now, ids); route B exposure; other secret files | r16m1, r16m5, r16m3, r16m15 |
| Stranger M1 | typed-message rule = key step B; revoke page = key step I (E-09, E-12, E-16, E-52) | r16M1 |
| Stranger M2 | margin arithmetic computed in the checker: 18:00:00 + 1:00 + 14:20 = 18:15:20 UTC = 23:45:20 IST, 3 minutes 40 seconds before 18:19 UTC = 23:49 IST; the false claim "4 minutes longer still ends before 18:19" deleted | r16M2 |
| Stranger M3 to M7 | key step D split into D.1 to D.5 (one answer per route); E-16 broken sentence and false promise replaced; alarm 1 timing and "do not shred part (a) while a take runs"; same-key owner path | r16F4c, E-48 checks |
| Stranger minors | E-23 branch names out; E-56 codes out; E-57 "default" out; E-54 heading split; E-52 file names out, handoff, take root and cap defined, retake already defined; E-60 plain; E-37 app 2 marked UNVERIFIED; E-09 `<folder>` and "type Postgres" | r16plain, r16e54 and the owner-code scan |
| Runner: 9 missed mutations | verify16 catches #15, #17 (wait for `not looking`), #18 (E-09 scope list), #19 (`ls -l`), #22 (`shred -u`), #24 (take-10 prefix), #31, #32 (alarm names), #51 (key-shaped text with hyphens after `sk-`; widened pattern, sample built from parts) | r16m15, r16m17, r16m18, r16m19, r16m22, r16m24, r16m31, r16m32, r16m51a, r16m51b |
| Runner: useful checks of mychk.py | index equals headers, owner-code scan over all OWNER-STEPS NEW text, UTC=IST pair check with seconds, weekday scan, banned scan (counts only, read at run time), input modification times read at run time | r16idx, r16pair, r16wd, r16banned, r16code |

## 3. Evidence (commands and output files)
- `python3 build-r16.py` printed `written 1056 lines` with no anchor error.
- `python3 verify16.py > v16-check-output.txt` (copy: `resolve-r16-check-output.txt`): `FAILURES 0`, 161 negative controls caught, 0 not caught, 60 rows, Apply now 48, Hold 12, 146 UTC=IST pairs, 69 weekday-date pairs, banned 0 of 10, secret-shaped 0.
- `EDITS_PATH=EDITS.round15.md NO_NEG=1 python3 verify16.py > v16-on-r15-output.txt`: 45 FAIL lines, exit code 1 (the new checker fails on r15).
- Banned-string scan (reads the list at run time, counts only) over EDITS.md, every build and verify script and the two output files: 0 hits each. No absolute path in the scripts.

## 4. Word counts
E-48 NEW 3,492 (r15) to 3,647 (r16); Appendix K 928 (new); OWNER-STEPS NEW text of all rows 15,780 to 16,464; whole EDITS.md 49,925 to 52,771; applied sheet 18,632 (see item 1 of section 1).
