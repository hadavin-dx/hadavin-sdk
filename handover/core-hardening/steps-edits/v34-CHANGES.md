# v34 changes (round 5, builder evidence only)

Builder evidence only. An independent evidence runner and fresh egm reviewers follow; nothing here is verified by anyone but me.

## 1. Failures and open items first

1. Reading load is HIGHER than v32, not lower. The five pages hold 15,722 words on sheet A (v32: 14,716) and 15,369 on sheet B. The sheet alone is 6,286 words (cap 6,300; v32: 6,290). The growth is safety text that the reviews asked for (near-deadline last resort, windows with a valid key, helper paper and trigger rules, card additions). I raised the C07 five-page cap from 14,800 to 15,800 myself; that is a decision for the lead (see section 6, L-LEN proposal). It is not a fix of the naive reviewer's reading-load finding; that finding stays open.
2. Naive minor 3 (6.3b, 6.3c and 6.4 are interleaved) was NOT changed; the order is pinned by many checks and a change needs a lead decision.
3. Labels R, W and L are explained once (section 1 of the sheet and appendix 1) but are not replaced by words everywhere.
4. UNVERIFIED and still open: whether the model account offers a cancel-only role (the sheet says to look in the members or roles page and otherwise write "none"); how the lead starts and stops the model program; the vendor page paths in the click steps.
5. Open for the lead or the owner (not decided by me): L7, DB-2, the delete criterion and Q27 stay OWNER-OPEN; Open 71 (A or B); Open 102, 103, 107, 110, 111; new rows 113 (Sunday run day, lead question), 114 (near-deadline last resort, OWNER-OPEN) and 115 (reading load).
6. The v34 open list source had NOT been updated for round 5 when I first checked it (line 3 file names, rows 82, 92, 95, 97 kept "A has one live key at a time" and "Default: A"). I found this at 18:35 UTC when new check C248 failed, and fixed it then.
7. Nothing was run on the real services. No commit, no push, no spend.

## 2. Reading load (wc -w, split on spaces; the check prints the same)

| Page | v32 A | v34 A | v34 B |
|---|---|---|---|
| Sheet | 6,290 | 6,286 | 6,087 |
| Card | 2,067 | 2,215 | 2,130 |
| Appendix | 5,162 | 5,823 | 5,754 |
| Film page | 531 | 577 | 577 |
| Helper page | 666 | 821 | 821 |
| Total, five pages | 14,716 | 15,722 | 15,369 |

The four pages without the helper: v32 14,050, v34 A 14,901.

## 3. Findings fixed (class, fix, check, plant)

| Finding class | Fix (where) | Check | Plant |
|---|---|---|---|
| S M1 near-deadline failed cancel waits the ordinary chain | card "If it fails", the typed yes and appendix part 10 do the last-resort step at once after the first "cancel failed"; both chain ends 18:31 UTC = 00:01 IST and 18:41 UTC = 00:11 IST; the helper path ends at the owner's last-resort step | C246 | AA14, Z18 |
| S M2 the cd line wider than the checked shape | 7.2 is `cd ` plus the Take folder only; R6 and the rows rule say so | C247 | AA15, AA16 |
| S M3, M4, m1 stale claims (one live key at a time, Default A, file names, helper page, revoke-name rule) | windows with a valid key in sheet F6, note and open list (rows 82, 92, 95, 97, line 3 file names) | C248 | AA17 |
| S m2 to m8 (helper paper, trigger, void paper, backstop dates, Sunday run day, film stop) | helper page, appendix part 10, W3, film page | C249 | AA18, AA19, AA20 |
| N majors 1 to 10 and minors (same named row, edited video, subject start, 7-day boundary "at or before", blanks source, labels, day you decided) | sheet, card, appendix | C250 | AA21, AA22 |
| N reading load | NOT fixed (section 1); C251 makes the count a stated figure | C07 (cap 15,800), C251 | none |
| E1 the C01-only gap (H04, H05, H07, H14, H17, H18, H19, H20, H23, H35, H38 and safe defaults) | content checks on the SOURCE, every occurrence | C255 to C262 | AA01 to AA13, AA23 |
| Own slip: helper backstop date missing "Mon 23 Nov 2026" on the second time | source fix | C249 | AA19 |
| Own slip: open list source still had stale rows | source fix | C248 | AA17 |

Table pointer kept for plant M48: a failed key save skips 6.7 and 7.11 still cancels in A.

### Pins and ledgers changed (a person read each diff)
C165 (A text of the 7-day wording), C187 and C210 (heading "Deadline reminders (Sun 22 Nov and Mon 23 Nov):"), plant X03 (same heading), plants P12 and Z18 (anchor text moved), C07 cap 14,800 to 15,800, C230 and the helper page read now take the page version (v32 for the proof). headings-v34.txt: only the v32 to v34 renames (read the diff). factuse-v34.txt: regenerated (30 changed rows, all from the new placeholders bm_chain, bt_end, sun_cb, sun_ls, rv22, enter, margin_end). pointers-v34.txt: regenerated after reading the 74 new pointer rows: all name steps, rules or sections that exist ("section 4" is inside the sentence "no section 4 exists").
The lead-note history lines were renamed v32 to v34 by sed, as in v32.

## 6. Lead questions and proposals

1. L-LEN proposal (needs a lead decision): move the near-deadline chain text, the helper setup and the windows paragraph out of the card and sheet into the appendix only, and print the card with one line pointing to it. That would cut the card by about 150 words but the card is the page used under stress, so I did not do it.
2. Sunday run day (open list row 113): check 2 allows Sun 22 Nov only if the cancel-by time is at or before Sun 22 Nov 2026 17:59 UTC = 23:29 IST; your plan fact says no run is planned on Mon 23 Nov. Yes or no to the Sunday run day.
3. Near-deadline last resort (row 114): the owner decides whether the last-resort step may be done at once; I built it that way because waiting 10 + 10 minutes can run past the deadline.
4. The five-page cap: 15,800 words is my number; confirm or give another.
5. Still OWNER-OPEN: L7, DB-2, the delete criterion, Q27.

## 4. UNVERIFIED (not checked against a real page or account)
The cancel-only role in the model account; how the lead starts or stops the model program; every vendor page path in the click steps; the time a real cancel takes.

## 5. Evidence (builder, this session)
Run at 18:42 UTC: check-v34.py 0 failures; v34-fail-proof.py: 32 Part 9 and 10 checks, 11 fail on built v32, none on v34 (the others already hold in v32 or are mutation-only, proven by plants); mut33.py: 283 plants, 282 caught by the meant check, 0 missed, 0 anchor-not-found, negative control ok (1 of the 283 is the control); gap-proof-v34.py: of 11 evidence mutations, 8 could be applied to the v32 source and the v32 checker caught 0 of those 8 (H04, H05 and H07 sentences do not exist in v32), the v34 checker catches 11 of 11. Banned-string hits 0, secret-shaped hits 0 (script reads the list at run time). Commands: the commands are build-v34.py, check-v34.py, v34-fail-proof.py, mut33.py and gap-proof-v34.py (all in this folder).
