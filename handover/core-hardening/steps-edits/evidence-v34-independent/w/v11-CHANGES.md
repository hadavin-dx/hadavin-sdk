# v11 CHANGES: every finding and where it is fixed

Files: day sheet `OWNER-STEPS-realrun-v11.md` (209 lines; v10 had 240; the target of 180-200 is NOT met, and the file is about 1.8 KB BIGGER in bytes than v10 because the money rule, A.0 key method, go condition 5/6 and F.1 safe exit added text; the cut moved the run card, trial run, failed-run clean-up, retire table, character lists and ban list to the appendix, but not enough). Appendix `OWNER-STEPS-v11-APPENDIX.md` (184 lines). Nothing was run by the writer (no command, program or click path). Banned-word scan: 0 hits in both files. Locations are section labels (line numbers drift). Sources: Sec = review-v10-security.md (M1-M11, N1-N12); Nv = review-v10-naive.md (B1-B3, M1-M12, nits n1-n9 numbered by me in the order the review lists them); Cit = citation-check-v10.md; Lead = the task brief priorities 1-6 and ORDERS answers of 10:13Z.

NOT FIXED / PARTLY FIXED first: SecM7 part (checksums from the lead catch only drift: text says so, cannot be fixed by text); SecN6 (type icon: asked, not verifiable); NvM11 (length target missed); NvB3 (the cue is now "the program's own line", but the program may not print one: UNVERIFIED, lead question); Cit U1 (v9 sources not re-opened; no sheet defect). Items marked UNVERIFIED depend on facts I could not check: see v11-NOTES-FOR-LEAD.md.

| Id | Where fixed in v11 | Status |
|---|---|---|
| SecM1 old model keys | money rule first sentence (review whole key list, older keys are live spend paths, owner decides, may cancel any time); A.0 (1); E.0 redo; I.0 warning (also cancels older keys the owner decided) | fixed |
| SecM2 backstop counter | money rule: counters (1) account total / (2) run's own, both stated by the lead in the A message (A message list); backstop check as an increase above the reading; no answer = no; 180 vs 189 note keeps "lead changes setting" | fixed; real counter UNVERIFIED (NOTES Q2) |
| SecM3 owner sees only two settings | A.1 grep per EVERY setting name; F.2 compares the usage page's per-model line with the model named; A message list has every setting name and value | fixed |
| SecM4a emergency wording | money rule: "increased since the latest reading by more than your run total", or charge with no run | fixed |
| SecM4b no lever in the run | money rule: cancel any key at any time | fixed |
| SecM4c I.0 vs emergency contradiction | I.0 warning: cancel the run key by name and any other key the review decided; emergency path cancels any key the owner cannot account for | fixed |
| SecM4d key live after non-zero exit | I.0: may cancel at once after any non-zero code; repeat needs new yes and key | fixed |
| SecM4e I.0 no owner deadline | I.0: row 7 deadline or 60 minutes after F.2 whichever earlier, cancel without messages (60 min = my suggestion) | fixed; value UNVERIFIED |
| SecM5 stale figures | E.0 redoes the whole money rule; E reading replaces A reading | fixed |
| SecM6 / Lead 3 decision 5 wording | removed "No one can start without your written yes" (day sheet old paragraph and the same idea in appendix 3, now reworded to what you never allow, with an explicit sentence that nothing is claimed about earlier starts); removed "Typing nothing starts nothing and deletes nothing"; DO THIS FIRST item 3 states the lead may already have started parts; E warning; appendix 8 first ban line; appendix 14 | fixed |
| SecM7 owner cannot verify go conditions 4,5,6 | go condition 6: `ls -l --time-style=full-iso`, `ps -o lstart= -p`, `date`; condition 5 statement names file and line; condition 2 first line must name row 14 commit; 0.2 compare commit with public branch if pushed, else honest sentence | fixed as far as text can (UNVERIFIED commands; cannot see which key the process loaded: said) |
| SecM8 n8n stop line | appendix 10 prints permitted stop/start forms with placeholders; row 5 words; E.0 points to it | fixed as form; real commands UNVERIFIED (NOTES Q3) |
| SecM9 section 7 secret display | appendix section 7 deleted; C.3 says stop if n8n asks; lead enters values; appendix intro says so | fixed |
| SecM10 decision 8 vs step 0 and T | step 0 warning: runs only if "go step 0" quotes owner's written yes; appendix 11: trial needs written "yes step T"; leftover-delete authority unified (lead names the one @example.com address, owner deletes, before D.9) | fixed; whether owner already lifted decision 8: NOTES Q4 |
| SecM11 step 0 file left behind | 0.6: `rm` of the result file in every branch including key-like | fixed |
| SecN1 "E.5" | E warning now says E.4; scan: no "E.5" | fixed |
| SecN2 I.0 "delete" key | I.0 uses "cancel"; Words list defines the five verbs (console button may say Delete) | fixed |
| SecN3 yes before C.4; "rely on lead's message" | accounts check moved to A.5 before the yes (A.6); fallback sentence now "my A.5 check is my protection" | fixed |
| SecN4 think time changed by lead | removed "unless the studio lead changed it"; E.4 says 2 seconds from the earlier sheet | fixed (also Cit nit) |
| SecN5 rows 15/16 lead-authored | appendix 2 and warning before I: "kept" counts only with owner's written yes, reason and end date UTC+IST | fixed |
| SecN6 C.3 names only | C.3 also reads the type beside each name | partly (icon/type cannot be verified) |
| SecN7 0.1 compare with memory | 0.1 compares with go message AND the name you remember | fixed |
| SecN8 "stop" defined late | Words list: "Stop and wait" defined in the day sheet | fixed |
| SecN9 delete authority D124 vs D161 | one rule (see SecM10) | fixed |
| SecN10 J depends on lead's lease confirmation | unchanged, stated as such in J | not changed (by design: claim needs the written confirmation) |
| SecN11 "just before E.2" vs E.0 | go condition 6 and E.0 both say E.0 | fixed |
| SecN12 warnings only in appendix | J ban list restated inline (7 lines); clipboard caution inline in A.0; lock-file removal stays in appendix 9 with its box, pointer from section list and I.6 | partly (lock-file box only in appendix) |
| NvB1 where to save the made key | A.0 "Saving the key without printing it": one command with hidden input, no-overwrite, permissions, size check, clipboard clearing, honest limits, all marked UNVERIFIED | fixed as method; unverified |
| NvB2 F.1 vs "deletes nothing" | go condition 5 is a hard stop before E with a time limit; F.1 safe exit with time limit (cancel key, close window, step G); flat "deletes nothing" removed (0 hits) | fixed (UNVERIFIED: closing window effect) |
| NvB3 n8n cue | E "What is normal": row 5 acts only on the program's own stop/start lines, row 5 gives exact words, no words = no run, lead gives no cue because it cannot see; start fallback after row 12 minutes | partly: UNVERIFIED that the program prints such lines |
| NvM1 y prompt no max wait | E.2: about 5 minutes then `n` (writer's limit, labelled) | fixed |
| NvM2 credentials never created | C.3 last paragraph: made earlier by owner (FACTS), not created here; missing = tell lead; ports 5678/5679 explained | fixed |
| NvM3 order of day; A.5/C.4 circular | order list: T last and needs own A; accounts check now A.5 before yes | fixed |
| NvM4 money rule fails on notes' figures | rule now by counter and increase; notes' figures mentioned with what happens | fixed |
| NvM5 word clashes | five verbs; stop; check/test; "printed result" vs three result files; "model token" vs key; "take" avoided except program names; send/type | fixed |
| NvM6 labels before definition | Words list defines backstop, stop time, label demo, sender/receiver, private app, film pause, lease, unknown, Postgres preview (appendix 1), notice, printed result | fixed |
| NvM7 placeholders | `<N>`, `<your Windows user name>`, `<path 1>` `<path 2>`, sample notice uses `<your run name>` and `<6 digits>`; sample lines marked never to type; rule 10 lists in appendix with exception sentence | fixed |
| NvM8 0.5 filter | match-viewing command with `cut -c1-40`; 64-char checksum harmless; counts as `<n>` | fixed |
| NvM9 no sample result | appendix 5 sample printed result (INVENTED, labelled); F.2 and J point to it | fixed |
| NvM10 proof screen criteria | DO THIS FIRST item 2 states purpose and criteria; row 10 "pictures of counts only" | fixed |
| NvM11 length and split | three parts; T, G, I.4 table, run card, L43 paragraph, rule 10 lists, ban list moved; day sheet 209 lines | PARTLY: 209 lines, bytes not smaller |
| NvM12 trial run `end` | appendix 11 and F.1: nobody films, owner looks, types `end` | fixed |
| Nv n1 run name rule | DO THIS FIRST item 2: letters+digits, starting letter, 4-12 chars (my suggestion), `ls ~/.hadavin-take-tags` | fixed; length rule UNVERIFIED |
| Nv n2 "type" for sending | send/type defined and used | fixed |
| Nv n3 Delete vs D.9 | step 0 leftover says delete before D.9 | fixed |
| Nv n4 18:14:40 no date | E.0 and appendix 9 give Mon 23 Nov 2026 | fixed |
| Nv n5 I.1/I.3 screenshots, Windows path | I.1 ties screenshots to row 13/I.3; I.3 explains the Windows user name, full path | fixed (my reading of row 13 as covering I.1 shots) |
| Nv n6 internal codes in appendix 8 | codes (BL-wp6-G1, S9-x, decision numbers) replaced by plain words in appendix 14; file:line references kept | fixed |
| Nv n7 masked format | appendix 5 shows `de…r@example.net` | fixed |
| Nv n8 "laptop cannot enforce" | appendix 3 rewritten gently and honestly | fixed |
| Nv n9 end date no UTC/IST | rows 15/16 and warnings say UTC and IST | fixed |
| Cit M1 A.1 to A.5 labels | step A items are labelled A.0 to A.6 (A.5 accounts, A.6 yes) and references use them | fixed (labels differ from v10: A.5 = accounts, A.6 = yes; appendix order table uses them) |
| Cit M2 "decision 7" untraceable | v11 cites decisions by full name ("owner decision 5 of 2026-11-16"); the v10 phrase meant item 7 of DECISIONS-2026-11-16 (n8n first-visit setup, lead imports flows) | fixed |
| Cit U1 sources not opened | not a sheet defect | not fixed: no change |
| Cit post-by date single source | J heading says it comes from the v3 sheet only | unchanged label kept |
| Cit "unless lead changed it" | see SecN4 | fixed |
| Lead 2 go condition 5 hard stop + F.1 safe exit | go condition 5; E.0; E.2 (archive line); F.1 | fixed |
| Lead 4 print n8n stop line | appendix 10 | fixed as form |
| Lead 4 commands for go condition 6 | go condition 6 | fixed (UNVERIFIED) |
