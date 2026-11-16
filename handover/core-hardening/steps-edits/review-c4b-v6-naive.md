# C4b v6 naive-reader review (condensed copy of the inline report), 2026-11-16
Verdict: MAJOR (not blocker; sheet says "do nothing and ask" in most gaps, but several steps cannot be done from the sheet alone).
Fix before the owner gets it:
1. Who stops and restarts n8n, and who films, are still "open" (L55, L86, L88, L199): resolve or move out of the owner sheet.
2. No boxed warning before step E (first live run, paid model calls, real sends); add one. Step G: emptying Trash cannot be undone, box covers scope only.
3. Step 0 `cat <secret file name>` fails from the scripts folder (names only at L137, files in WSL home at L123): give `cat ~/<name>` or full path. Also "type unset if step 3 fails".
4. Missing table rows: throwaway-accounts message (rule 5), notice-vs-yes comparison, `echo $?` and paste, screenshots and clean-up messages, "done" after step J.
5. Editor notes left in owner text (L3, L13, L66, L136, L153, L168, L169, L173, L199, L214, L231): remove or move to the end.
6. Run date: aim "posted by Wed 18 Nov" vs stop time 23 Nov (L112); "default is no" claim (L47) not true for all rows.
7. Words with two meanings: lead, run, archive (3 senses), take, key/token, step, pass (exit 0), notice/notification.
8. Backstop: give a concrete rule to compare with the yes; explain "US$189 testing budget" (L19).
Minor: step F finding contacts by run name unchecked; expected count of contacts (2 or 3?) unclear; "closed input", "piped", "hard budget 8" unexplained; Words box too long (trim hook door, postgres, journal); "rules 1 to 7" count wrong (rule 8 exists).
