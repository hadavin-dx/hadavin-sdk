# v9 CHANGES: every finding folded into OWNER-STEPS-realrun-v9.md

v9 line numbers are of the file OWNER-STEPS-realrun-v9.md as saved (first line where the anchor text sits). Sources: Sec = review-c4b-v8-security, Nv = review-c4b-v8-naive, Adv = review-c4b-v7-adversarial (items already fixed in v8 are marked where I checked), Cit = citation-check-v8, Dec = DECISIONS-2026-11-16 (and the coordinator messages of 10:02 UTC).

| Finding | What changed in v9 | v9 line | Status |
|---|---|---|---|
| Sec-B1 | Spend check: own grep of two named lines, price sanity check, account usage page before and after, only real ceiling = balance | 206 | changed |
| Sec-B2 | n8n holds no model key; C.3 limited to named non-model files; lead confirms in writing before yes | 9 | changed |
| Sec-M1 | Model key cancelled right after last run (I.0), not gated on H, edit or retire check; I.4 and I warning except I.0 | 306 | changed |
| Sec-M2 | Step 0 delete gate dropped (decision 2); the probe-key = program-key question is moot because the program never deletes | 184 | moot by lead decision 2 |
| Sec-M3 | HubSpot key only in the one command line (prefix assignment); unset in the box as a precaution | 177 | changed |
| Sec-M4 | Mechanical grep filter for long tokens and any @ not @example.com before pasting; --plan host named on row 14 | 180 | changed |
| Sec-M5 | Rule 10: allowed characters, typed by hand, quoted, ls -l reject '->', kept-on-purpose rows; full paths for shred/rm | 160 | changed |
| Sec-M6 | Masked lines: start condition becomes: printed = compare; message says not printed = owner's yes says so; message silent = answer no. Last letter added. Not a hard 'not printed = do not start' because decision S9-4 is deferred (program does not print them) | 269 | changed, partly different from the brief: see NOTES Q3 |
| Sec-M7 | Post gated on exit 0, A and B right in the printed result, lead's written confirmation; no number/claim not in the result; send counts not repeated | 342 | changed |
| Sec-M8 | Boxed warning before J: if unsure, do not post | 339 | changed |
| Sec-N1 | Run folder added to row 8 | 63 | changed |
| Sec-N2 | grep instead of cat for settings; C.3 clipboard sync check and overwrite | 227 | changed |
| Sec-N3 | I.2 crop; Recycle Bin and OneDrive bin emptied | 321 | changed |
| Sec-N4 | Retire check limit stated as at most 3 runs in all | 332 | changed (default, NOTES Q8) |
| Sec-N5 | Real-run go defined and added to Words box, step list and E have-ready list | 15 | changed |
| Sec-N6 | Step A and money checks added to the not-overridable list; waiver replaced by a quoted reason | 7 | changed |
| Sec-N7 | Scope check by opening the private app page; T cannot be done without G; G mails ticked one by one | 292 | changed |
| Nv-B1 | Notice comes after the start command: compare on the notice (E.2), E.3 sentence then wait for reply, y only after (E.4) | 258 | changed |
| Nv-B2 | Go messages defined; in Words box, step list, E have-ready list | 15 | changed |
| Nv-B3 | F.1 end then F.2 finish; result prints only after end; model program keeps running in the pause; echo $? only when $ is back; nothing typed in the run window except y, number+name, end; n8n line in a second window | 274 | changed |
| Nv-B4 | Row 13 reduced to I.3 only; C.1, C.2, D, G, I.7 never skipped; T needs G | 68 | changed |
| Nv-B5 | Kept app password gets its own retire-check path; 'revoke again' only if not kept | 327 | changed |
| Nv-B6 | Author text removed (BL-wp6-G1 moved to the appendix); 'plan's check' sentence removed; dangling bullet moved into I.1; 'database passwords' explained; crash-safe and exit 120 reworded | 41 | changed |
| Nv-M1 | Owner reads two named lines himself; 'backstop no higher than yes' is stated | 22 | changed |
| Nv-M2 | Type n at the y prompt (box, E.2, E warning) | 5 | changed |
| Nv-M3 | Gmail label and filter: Words box and new row 17 | 72 | changed |
| Nv-M4 | Conditions of C.1, C.2, D, C.3 (row 9), I.2 (row 15), T (row 6), row 5 now identical in the step list and prose | 68 | changed |
| Nv-M5 | Labels E.1 to E.5, F.1 to F.3, I.0 to I.7, 0.1 to 0.6 exist in both; I.5 appears once | 306 | changed |
| Nv-M6 | Step 0 leftover contact: lead names it by its made-up address; owner deletes only that one | 189 | changed |
| Nv-M7 | Money limit between runs stated: only the account balance; cancel date named in step A | 146 | changed |
| Nv-M8 | I.1: sign in to receiver, then to the sender; account check before each delete | 321 | changed |
| Nv-M9 | Retire-check limit counts every run | 332 | changed |
| Nv-M10 | D is the pre-run list; H applies the same list to the finished video | 315 | changed |
| Nv-M11 | Proof screen chosen before step E (step list, order of the day, have-ready) | 84 | changed |
| Nv-nits | Words: lead / owner / table / portal / check / delete-revoke-cancel-remove given one meaning each; 'the lead's' to 'the studio lead's'; alert mail, unknown, scope names, result file, stand-in programs, model account, python3 -I explained; '(path not checked)' marks removed and rule 8 says none was checked; '\_local' fixed; lock-file leftover pointed to Other refusals. NOT changed: 'send', 'run' and 'program/script/code/tool' still vary in places (reason: too many uses to retag safely by script; listed in NOTES Q12) | 44 | partly changed |
| Adv-B1 | Same as Nv-B3 (n8n line only in a second window; echo $? after F.1; E.5 moved to F.2) | 278 | changed |
| Adv-B2 | E.3 real look at own accounts, sentence extended to HubSpot, also 0.1 for step 0 | 174 | changed |
| Adv-M3 | y only after compare and reply; run name typed from own message | 270 | changed |
| Adv-M4 | Money used so far + total must not exceed the backstop; step 0 answer listed in A | 208 | changed |
| Adv-M5 | stage.env cat removed; C.3 value shown only after clipboard-sync check, window closed, clipboard overwritten | 227 | changed |
| Adv-M6 | Blank row 13 no longer switches checks off (see Nv-B4) | 68 | changed |
| Adv-M7 | Row 5 missing = no run starts | 60 | changed |
| Adv-M8 | Account check before every delete in G and I; normal profile warning | 294 | changed |
| Adv-M9 | Rule 12: any non-zero number, delete nothing, send number and last line; C unknown exit number may be 0 or 3, lead says which | 162 | changed |
| Adv-M10 | Exit 1/2: no rerun, type by hand | 379 | changed |
| Adv-M11 | I.2 screenshot crop | 322 | changed |
| Adv-M12 | E have-ready list lists C.1, C.2, D, step 0 answer, rehearsal, go, balance | 249 | changed |
| Adv-M13 | Lead's reply awaited before y (and go message before start) | 269 | changed |
| Adv-N14-17 | Step 0 not-zero meaning kept; @ scan added; key shown means lead names the private app to delete; cd line form; checksum first/last 8 and length; shred full paths + ls -l first; alert mail address from the card; run-name search note in F.1; rehearsal first line read with head. Retry and stop-time interplay: not changed (reason: stop-time refusals are the program's own and unchanged from v8) | 175 | changed |
| Cit-1 | Second Gmail account no longer 'already done'; row 17; sheet says do not start if it does not exist | 9 | changed (NOTES Q1) |
| Cit-2 | Owner action when the file shows more than the yes total: answer no; lead lowers the setting | 206 | changed |
| Cit-3 | Row 13 gating made consistent (C.3 by row 9, I.2 by row 15, T by row 6, I.3 by row 13) | 68 | changed |
| Cit-4 | BL-wp6-G1 is the take-time literal substitution of $env.* in the flows, not built; wrong sentence removed; moved to the appendix | 398 | changed |
| Cit-5 | Crash-safe and 'processed once' use the same rule: only the lead's written result on real n8n; rehearsal wording corrected (fake Gmail/HubSpot stand-ins, no claim about n8n) | 349 | changed (NOTES Q9) |
| Cit-6 | Row 8 now lists the two setting-line names; 'holds settings and no key' text removed | 63 | changed |
| Cit-7 | Reference to 'step 0 item 7' fixed (now 0.5) | 39 | changed |
| Cit-8 | E.3 and the finish step have labels in the prose (E.1-E.5, F.1-F.3) | 269 | changed |
| Cit-9 | python3 stays; E says stop if python3 not found; flagged unsourced | 250 | changed (NOTES Q10) |
| Cit-10 | Bad login exit code marked 'usually exit code 2; the studio lead confirms' | 253 | changed |
| Cit-11-14 | Line-number errors are in v8-CHANGES/NOTES, not in the sheet; nothing to change in v9 | 76 | not changed: no sheet text affected |
| Dec-1 | Real-v5 only: appendix last line; no film-v5, scene 5 or 60.1-61.9 text in the sheet body (none was there; checked by grep) | 411 | changed (appendix); body had none |
| Dec-2 | The program never deletes contacts: F.3 and G.2 delete by hand from the lead's list; Delete definition; warnings E/F; J ban; step 0 gate removed; step 0 kept as the 7-call probe | 288 | changed (flag: `end` UNVERIFIED, NOTES Q2) |
| Dec-5 | S9-5 and S9-12 text (not overridable list; lead reads only masked outputs); S9-2 owner compare with honest sentence; S9-3 key cancelled by owner; S9-1 and S9-4 in the appendix; no claim that nothing spends before both answers | 399 | changed |
| Dec-6 | Ports 5678/5679 are the owner's own; real run uses its own port | 9 | changed |
| Dec-7 | n8n setup done; lead imports/activates flows; owner only types y, challenge, end | 9 | changed |
| Dec-8 | No real-account smoke beyond loopback and one made-up lead: appendix only | 396 | changed (appendix) |
| Dec-9 | Proof screen is a rehearsal screenshot or Postgres node preview | 35 | changed |
| Dec-10 | Wording 'one Postgres server with two databases (n8n's own and the run's)' in the J ban list and the appendix | 351 | changed |
| Dec-3-4-11-12 | Parked / core patches / licences / rehearsal timing: lead-side, nothing in the owner sheet | 392 | not changed: no owner step |

Note: where a status says changed, I checked that the v9 text holds the fix; I did not separately record which of the v7 adversarial items v8 had already fixed.
