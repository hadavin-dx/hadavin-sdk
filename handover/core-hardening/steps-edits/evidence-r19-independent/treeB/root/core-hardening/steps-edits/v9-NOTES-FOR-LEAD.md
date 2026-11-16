# v9 NOTES FOR THE STUDIO LEAD: questions only you can answer (safe default already written in the sheet)

Written Mon 16 Nov 2026. Failures and unverified items first.

**UNVERIFIED program facts the sheet now relies on (I could not read the scripts):**
- Q2. Whether `run_real_check_n8n.py` still ends the film pause with the typed word `end`, and that it no longer deletes contacts (decision 2). Default in the sheet: `end` stays; the program deletes nothing; step F.3 and G.2 delete by hand from your list; the sheet tells the owner to stop if a program line says it will delete or archive. If the program still deletes at `end`, F, G and the J ban need rewriting.
- Q4. Whether a wrong line at the `end` prompt, typed-ahead keys, or a closed terminal end the pause early (assumed; rule 11 forbids typing there).
- Q10. `python3` is not in any source for `run_real_check_n8n.py` (v3 says `python`). Default: sheet says `python3`, owner stops if it is not found. Please confirm on the laptop.
- Q11. What `hubspot_probe.py` does when the token is empty (the new 0.4 line passes the key by a prefix assignment; if `cat` fails the token is empty). Default: the owner stops on "No such file" and on a "refused" line.
- Q13. Whether the step 0 result file really holds no more than the list (the new 0.5 filter catches long tokens and any `@` that is not `@example.com`; a line flagged = owner pastes nothing).

**Questions (answer = a new run card or message):**
- Q1. SECOND GMAIL ACCOUNT. FACTS-ALREADY-DONE says one throwaway Gmail; v3 says receiver and sender. v9 no longer calls the sender "already done". Default: run card row 17 must say "yes" for the separate sender account, otherwise no start. If there is only one account, tell me; the sheet's two-account checks (A, E.2, E.3, I.1) must be re-worded.
- Q3. Masked sender/receiver. Decision S9-4 (deferred) means the program may not print them. Your brief asked for "not printed = do not start". That would block the run if the program never prints them. Default written: if your step A message says the program prints them, the owner compares them on the notice; if it says it does not, the owner's yes carries the honest sentence "the program does not show me the accounts; I rely on the studio lead's message"; if the message is silent, no yes. Change it to a hard stop if you prefer.
- Q5. Backstop. The file may still show US$180 (FACTS/SCOPE). Rule: backstop must be no higher than the yes total (3 times the price). Default: owner answers no, you lower the setting in your own session, and send a new step A message. Alternative (not applied): owner accepts up to the backstop in his yes.
- Q6. Step A now needs from you: model name, max tokens in and out, the two prices per million tokens, the price page address, the model account page address, the two setting-line names (also on row 8), the first line of the rehearsal result file, the date the model key is cancelled, and "key used only for this run: yes/no". If any is missing the owner answers no.
- Q7. Model key lifetime. S9-3 says the owner revokes at clean-up. v9 puts it as step I.0 right after the last run (not waiting for H or the retire check). No provider-side per-key limit is claimed (not shown). Change back to clean-up if you prefer.
- Q8. Retire check limit: v8 said "twice in all" for "could not tell"; v9 says at most 3 runs in all, any outcome (my default; asked for in the naive review M9). Both kept-on-purpose: you write "retire check not required: kept on purpose" and the end date.
- Q9. Crash-safe and "processed once": both only on your written statement naming a result on the real n8n (the plan says only a DM PASS lets the claim cover that window). v8 contradicted itself; v9 uses one rule. The rehearsal is described as "fake Gmail and HubSpot stand-ins, no model call"; the plan runs real n8n with stub mail/CRM. Please say whether the rehearsal uses real n8n; I did not claim either.
- Q12. Words I did not unify by script: "send", "run", "program/script/code/tool". The "lead", "owner", "table", "portal", "check", "delete/revoke/cancel/remove" words were unified.
- Q14. Release words. system-map's owner cards use "start now", "program paused", "film done, type end", "last run done". v9 uses "go real run <run name>", "throwaway confirmed", "filmed" (from the person on row 4) and "model program stopped". Two owner documents with different gates is a take-day risk; pick one set.
- Q15. Who restarts n8n while C is sent (row 5). system-map's card says the studio lead and the owner touches nothing; v9 keeps the row open (the person is named on the card; no name = no run). Also the n8n line goes only in a second Ubuntu window.
- Q16. "2 or 3 contacts": cross-read found the contact existed even when the mail was missing in the lane3 stand-in runs; v9 keeps "2 or 3" and adds that the contacts stay until the owner deletes them. Not tested on the real stack.
- Q17. Lead reading: v9 says you read only masked outputs and the masked result file, never the secret files or real-run folder files (S9-12). The owner sheet cannot enforce this (same Linux login); the sheet says so.
- Q18. F.3: the list you send must hold lead key (person id) and contact id, masked. The owner matches by the test address and the run name.
- Q19. G now also covers contacts after a trial; demo mails are deleted only after a failed run or a trial (as in v8), not after the real run.

**Decision effects (2026-11-16):**
- Step 0 is kept, simple, as the 7-call probe of the read/create/change paths. Its delete line no longer gates anything ("delete works" is replaced by "paths work"). If you prefer to drop step 0, say so; the go message conditions and step A then quote your reason.
- S9-1 and S9-4: described in the appendix only. The sheet does NOT claim that nothing can spend before both typed answers, and does not accept the "lead switches on flows after the owner's typed y" fallback.
- S9-2 kept as the owner's own compare with the honest sentence that the program does not print the backstop or the money used so far.
- Decision 8 (no extra real smoke) and decisions 3, 4, 11, 12: nothing in the owner sheet.
