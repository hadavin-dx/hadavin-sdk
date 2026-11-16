# fix-f6b-r3: final pass on F6B-AUDIT.md

## Not done / not verified
- Nothing run; all SQL stays UNTESTED. No review round after this fix.
- Which of the 12 old recovery files were imported into the take n8n: UNVERIFIED (not in repository).
- The `<K>` quoting was applied to every recipe by text replace; I did not re-read each recipe after the edit beyond a count.
- Film-flow check "constant addresses ending in example.test" comes from the earlier audit text, not re-read this pass.

## Done
1. TRUNCATE: "not certain this is the demo database, stop and ask" added (steps 2, 3, F6B-02 row); non-done states: stop, do not truncate, why (only record lost, running lead's writes find no row).
2. Said plainly: truncating deletes scene 1-4 lead rows (intended: they are done, exist in real CRM); in-flight lead stops you at step 2.
3. Order is now: 1 switch off, 2 check, 3 truncate, 4 switch film set on, 5-6 run-sheet notes. Cross-references renumbered.
4. Summary count reading stated (alert mail not counted as "a mail"; otherwise 3 take Blockers); line 27 label now "Blocker counts".
5. F6B-13 text now starts "IF ... (UNVERIFIED)"; step 5 too.
6. Step 1: how to check (n8n list, search "recovery"; all 12 files share title "Lead desk main frame: recovery (every 30 s)", NOT "mf-recovery"; 12 folders listed). Step 4 lists the four film-v5 flow names/files.
Nits: `'<K>'` quoted with a note; F6B-01 cell shortened, evidence moved to "Evidence for F6B-01" below the table.
