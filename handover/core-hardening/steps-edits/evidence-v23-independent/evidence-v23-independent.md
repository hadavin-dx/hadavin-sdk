# Independent evidence for owner sheet v23 (EVIDENCE RUNNER: recorded, not judged)

Run date 2026-11-16 (UTC). No git, no network, no spend, no real secret. No sheet edited. check-v23.py was run once (01b).

## Failures and facts found first (recorded, not fixed)
- F1: Stale "card Part 2 (b)" / "Part 2 permits" in note G41, note section 8, Open rows 49 and 50. check-v23 bans "Part 2" only in the sheet.
- F2: Open row 59 (keep R2 and R3 ids) contradicts Open row 68, the changes file and the sheet (R2 and R3 removed).
- F3: 860 s is written 14.4 in note section 2 and Open row 56, but 14.33 in the sheet, note G10 and Open row 11. v23-CHANGES lists this as fixed (P7).
- F4: v23-CHANGES says "about 8,470" sheet words; measured 8,455 (matches the checkpoint).
- F5: Open list header says "(v21 ...)"; note G18 says "v22 sheet 7.8"; Open row 53 quotes "the word at 6.3".
- F6: Sheet line 2 still mentions double-bracket A/B text after the markers are gone.
- F7: In variant B the card's cancel/revoke list reads (a), (c), (d); no (b).
- F8: STOP RULE (line 6) uses FREEZE, alive, R1, R10 and the card before they are defined.
- F9: R6's character rule is ambiguous against the commands in its own list.
- F10: R8 "only five words start or end a step" versus 6.6 (lead's answer carrying program start time with "go on" or "wait") and the card's last resort ("names one step in writing").
- F11: Key-save line, multi-line paste on an interactive shell: the second pasted line runs as a command. One Ctrl-D leaves the prompt waiting. Spaces are trimmed. A wrong non-empty paste is caught only by the size check at 6.6. The sheet states Ctrl-D, trimming and size, and marks multi-line paste UNVERIFIED, but does not say the second line would run.
- F12: Variant B wording "keys named in the message" has no matching sample.
- F13: check-v23 coverage gaps: my 54 plants, 32 caught, 22 missed (list in 06). The builder's own 22 of 22 is on its own plants.
- Sheet longest line grew 242 to 317 words; "FREEZE" mentions 11 to 24.
- Not checked: truth of any UNVERIFIED statement, the EGM review/resolve/drift steps, files outside steps-edits/, a real WSL terminal.

## 1 Hashes (01-sha256.txt)
All older files (v20, v21, v22 sheets) UNCHANGED against evidence-v22-independent/01-sha256.txt. v23 hashes listed. check-v23.py (01b): rc 0, 0 problems.

## 2 Arithmetic (02-recompute-raw.txt)
77 PASS, 0 FAIL: 0.27, 0.81, 13.21 = 1321 cents, 860 s = 14.33 min (run length 15), all UTC-IST pairs and weekdays (deadline Mon 23 Nov 2026 18:29 UTC = 23:59 IST; start 11:30, alarm 12:00, cancel-by 12:10 UTC) in sheet, note, open list, changes.

## 3 Pointers (03a, 03b, 03c)
Every N.M, R-number, card, step, "section N", "Open N" and G-number resolves; sheet pointers match their topics; rows numbered in order. Stale wording is F1, F2, F5.

## 4 Cancel rule restated outside the card (04-cancel-rule-raw.txt)
46 lines outside the card mention cancel/proof words; 32 use the word card (48 card mentions). Lines with the word card: 4, 6, 9, 24, 25, 28, 45, 48, 49, 50, 51, 53, 55, 57, 78, 95, 96, 97, 105, 108, 113, 114, 116, 117, 121, 122, 123, 124, 126, 127, 128, 132. Which add more than "do the card" is in the raw file.

## 5 Commands and key-save (05a to 05d)
bash -n: 16 spans plus the start line, all rc 0. Key-save line tested with a fake key built from parts (never printed) on pipe, pty and an interactive multi-line paste, 7 cases of the v22 run; results in raw files; see F11.

## 6 Planted mistakes (06-mutation-raw.txt)
54 planted in scratch copies, 32 caught, 22 missed.

## 7 Word counts (07-counts.txt)
| File | v22 | v23 |
|---|---|---|
| Sheet | 9,267 | 8,455 |
| Note | 8,349 | 8,780 |
| Open list | 3,583 | 4,088 |
Variants A (8,354 words) and B (8,152) both build with no markers left.

## 8 Banned words (08-banned-count.txt)
10 entries read by ast from tests/test_no_reference_material.py; 0 hits in my files (re-run after this report was written: see end of file 08).
