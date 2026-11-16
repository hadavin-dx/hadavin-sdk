# resolve-r14: EDITS round 14 (builder text only; the lead runs the egm:* steps)

Files: `EDITS.md` (round 14, live), `EDITS.round13.md` (untouched round 13), `build-r14.py` and `build-r14-e48.py` (anchored patches, 0 anchor errors), `verify14.py`, `resolve-r14-check-output.txt` (exit 0, FAILURES 0, 97 negative controls caught, 41 of them new in round 14; verify14 FAILS on `EDITS.round13.md` in 30+ places). Still 56 rows, same ids, Apply now 44, Hold 12; no new row.
Nothing was run except text, count, weekday and scratch-apply checks. No program of the take, no click path, no shred, no live key.

## Not fixed, or fixed only in part (failures first)
1. **Naive minors not fixed this round** (time box; each needs a small edit, none needs a decision except the first): internal codes in text that the assistant reads (E-56 "Q23", "NOTE (F-01)", "r17", "re-pin"; E-31 "M-1", "Defect 1", "review-codebase-1.md"; E-26 "lead decision 10"; E-28 and E-30 and E-33 plan step numbers; E-29 "EG", "WP6"; held E-40, E-44, E-45 "Q23", "D2", "F-01"). They are fine only if the owner never reads AGENT-SCOPE. QUESTION 1 to the lead: does the owner read AGENT-SCOPE? If yes, I clean them in round 15. Also not fixed: E-07 and E-08 "nobody on this branch has read that evidence" (branch undefined); E-02 Why about branch names; E-23 still prints three take branch names; E-15 uses "take" as a verb; "run" for a take and a saved run (E-52); "post", "publish" and "send"; "label" with four senses; "reviewers who are not the assistant" against the studio lead's checks; E-12 part 2 mixes message content with owner instructions; the one-line reply of E-12 with the example `1.50` (left, because it is checked part by part); E-14 "company mail address"; E-16 reply `No` meaning "longer route"; E-51 "you open ..."; "retire-check" in the old text of E-58. The assistant's own checks are now defined in E-52 (round 14) but not renamed in E-03 and E-54.
2. **Security M-C only partly fixable.** A second repeating alarm was added and 3a now says "a promise by you backed by your alarms ... a procedure, not a control". The revoke still rests on a human alarm because Q26 forbids a timer. This stays a stated limit; the next step is the lead's: accept it, or allow a timer.
3. **Security M-H is text only.** The path rules of the clean-up (recorded full path, refuse home folder, `/mnt/c`, outside the recorded root, `..`, links) are an instruction to the assistant in E-16; nothing here shows a program enforces them. The owner's irreversible items 2 to 6 now wait for `no more takes` (E-55).
4. **Security M-G / naive M5: the margin is said plainly, not solved.** 18:04 UTC = 23:34 IST plus 14 min 20 s = 18:18:20 UTC, 40 s before 18:19 UTC = 23:49 IST, on an unmeasured 860 s. QUESTION 2: move the latest start we plan earlier (I propose 18:00 UTC = 23:30 IST in confirmation o, a figure I cannot check) or accept 40 s.
5. **Placeholder (naive M3):** kept in E-12, E-54 and R11 as the coordinator said, with a stated fallback sentence (the assistant proposes a time not later than the latest start we plan and the owner answers before any take). The words "LEAD" and "re-pin" are still inside the bracket. QUESTION 3: fill the time of day, or accept the fallback.
6. **Item 6 of step 22 (`shred -u ~/take-secrets/*`, input line 126)** has no row. E-48 now tells the owner to shred each of the two files one at a time by the shred rule and never to use `*`, so the owner text contradicts the input's own item 6. QUESTION 4: add a row E-59 that rewrites item 6 (count becomes 57 rows, Apply now 45), or keep the contradiction (the owner text says which applies).
7. **Other possible rows, not made:** input lines 144 and 171 (unchanged from round 13). Same question as 6.
8. **E-30 and ND9:** `.n8n/config` holds n8n's encryption key and in route B lives five days. I added a note to ND9; E-30's text (plain `rm`) is unchanged. QUESTION 5: choose ND9 again if route B is chosen.
9. **ND15 stays the lead's.** Both routes are written with exact conditions. The recommendation sentence is in ONE place, E-48 part 3c ("the assistant recommends route B"); ND15 lists the spots (E-57 and E-52 are neutral). The route is chosen by one message, `route A` or `route B`; `no more takes` alone does not choose it; a forced revoke at 18:19 UTC = 23:49 IST counts as `no more takes` and `cut accepted`.
10. **Confirmations:** h (margin not confirmed), m (L-A/B choices named `revoke it` and `leave it`, not literal), n (widened again: key copy and `~/take-secrets`) need the lead; new o (the 40-second margin). Letters now a to o.
11. UNVERIFIED and not checked: that the key list shows the last four characters; the click paths; shred on this disk; what the take does when its key is revoked; the 860 seconds; 18:14:40.

## Finding map
| Finding | Fix |
|---|---|
| Security M-A | E-48 3c, 3d, 3h; E-55: a revoke at the last time counts as `no more takes` and `cut accepted`; the assistant says so |
| Security M-B | E-37 (owner writes key name and last four first); E-48 3h default: revoke the one key made for this take |
| Security M-C | partly: second alarm, honest label (item 2 above) |
| Security M-D | E-48 3f: one shred rule for every file (full path, `..`, space, `*`, `?`, `[`, `realpath`, `ls -l` one name, trailing `/`), `rm --` fallback, closing paragraph |
| Security M-E | E-12 yes sentence, explanation, confirmation n |
| Security M-F | E-09 a, f, g, h, e and E-52 (clipboard history, `clear`, `umask 077`); E-48 3g new key storage |
| Security M-G | E-12, line 30, confirmation h and o, 18:14:40 once; question 2 |
| Security M-H | E-16 path rules; E-55 items 2 to 6 wait |
| Security minors | one recommendation sentence (ND15 lists spots); route B cost list complete; asks again after `cut accepted`; 3i `revoke`/`leave` (confirmation m); E-09 f/g scrollback and `umask`; HubSpot key of app 1 unless explained; Docker and WSL named; ND9 note (E-30 text not changed) |
| Naive B1 | E-16, E-48 3f, E-55: item 1 waits for `key revoked`/`key not revoked` and `shred done`/`shred not done`; new reply words |
| Naive M1 | 3j and E-12: no "unless"; "whatever the assistant says" |
| Naive M2 | E-37 note; 3h default |
| Naive M3 | item 5 above |
| Naive M4 | route message; reply on the last take in route B; costs of A and B; alarm 1 and 3c reconciled (3c says a revoke counts as `no more takes`) |
| Naive M5 | item 4 |
| Naive M6 | "test item", "counting program" renamed (whole file), E-52 defines three words; "retire-check" left |
| Naive minors | item 1 |
| Evidence r13 (7 missed mutations) | verify14: key end in 3h (r14m10), E-09 waits (r14m12f/g/h), weekday check over 40+ dates (r14m22, m23, m34), Q-number and L-id scan of owner text (r14m29, m30, nd) |
| Evidence r13 route ambiguity | one message selects the route (item 9) |
| Evidence r13 bare `no` | already `not sure` in 3e; verified by r14bareno |
| Evidence r13 placeholder on 3 lines | kept (item 5) |
