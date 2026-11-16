# v10 NOTES FOR THE STUDIO LEAD (written Mon 16 Nov 2026; failures and unverified items first)

**Not checked by me:** I ran no program, no PowerShell, no n8n. I did not read the scripts, `stage.env`, the run card, or any click path. The sample notice in E.2 is INVENTED (labelled so). Day sheet is 240 lines, not 200; many lines are long, so the page count is still large. Next cut, if you want it: move step D and the I.1 screenshot rules to the appendix.

**Program facts the sheet relies on (answer = a go condition or a new card):**
- Q-A. Does `run_real_check_n8n.py` at the row 14 commit delete or archive contacts? The scope sheet (section 3, F-01) says it deletes by DELETE at the end; decision 2 says it must not. Go condition 5 needs your written statement of what you checked. If the code still deletes, F, G and the J ban need rewriting and this is a code change, not a sheet change.
- Q6. Does the program run under `python3 -I`? Isolated mode may drop the script's folder from the import path. I wrote `-I` everywhere as directed; the rehearsal must use the printed form exactly.
- Q-B. Does the film-pause line still say "end"? Does it print "archive"? The sheet stops the owner if it says delete or archive.
- `readlink -f` and `ls -ld` on the laptop: standard, not run.
- The made-up sample notice in E.2: please replace it with the real notice from the rehearsal (numbers and names compared, so layout is not binding).

**Decisions I made that you may veto:**
- Q1. Money rule: balance >= run total, and backstop <= money used so far + run total. I did not add a lower bound (a too-low backstop only stops the run; it cannot cause spend). If the page lags and understates "used so far", the check gets stricter, not looser. You set the backstop to (used + total) in your own session.
- Q2. A.0: the owner creates a NEW run-only model key. FACTS says a key is already saved and used in earlier runs; cancelling that one in I.0 might break other uses, so a new one is safer. If you prefer the saved key, tell me and A.0 changes to "name the existing key and its file".
- Q3. FACTS lists ONE throwaway Gmail mailbox; the sheet needs a separate sender. Per the FACTS rule please grep memory and set row 17. If only one account exists, the sheet's two-account checks (A, C.4, E.2, I.1) must be re-worded.
- Q4. A.2 asks the owner to compute the price per call. The owner said on 2026-11-15 "no limit questions, just tell him the number". The sheet asks no limit question; it asks him to check your numbers (binding money checks). Say if you would rather drop the arithmetic.
- Q5. Post-by date Wed 25 Nov 2026 15:00 UTC = 20:30 IST appears only in the old v3 sheet; the current inputs have no source. I labelled it and put it on row 7. The aim "Wed 18 Nov" has no time and is not in v10 as a time.
- Q7. Row 12 now also holds the longest film pause; row 4 now holds who edits and crops. Your run card template needs the two additions. 
- Q8. Go condition 7: you must state in writing which exit codes count as success (0, or 3 only when C is "unknown").
- Q9. E.4: a wrong confirmation line leaves the run name unused only if the marker is written after a correct line (scope sheet says so); you decide whether the name can be reused.
- Q10. Who restarts n8n (row 5) is still a card row; the owner may be that person; the two-window rule is in E.0.
- Q11. Release words: "go real run <run name>", "throwaway confirmed", "filmed", "model program stopped", "no more runs". The system map uses other words; pick one set.

**Items without a source in the five inputs (kept, labelled "planned" or "the studio lead confirms"):** 7 calls in step 0, 13 sends, 2 second minimum answer time, about 14 minutes start margin and 18:14:40 UTC, lock file name, exit codes 1, 2, 120, the retire-check limit of 3.

**Q15 answers applied:** clean start row (appendix step table row 2, go condition 9, one sentence in the day sheet); lease sentence (E, J, appendix 5 and 8); spend limit by owner eye plus the model program's stage checks (money rule).
