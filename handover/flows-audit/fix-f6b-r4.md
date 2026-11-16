# fix-f6b-r4: final pass on F6B-AUDIT.md (only that file edited)

## Not done / not verified
- Nothing run; all SQL stays UNTESTED. No review round after this fix.
- UNVERIFIED: whether switching a flow off stops an execution already running (now stated in step 1).
- Which of the 12 old recovery files were imported: UNVERIFIED.
- Which leads scenes 6 to 9 really leave behind: UNVERIFIED (F6B-13); the re-take rule works whatever they are, but needs the owner to name each row.

## Done
1. M1: step 2 and 3 now have a first-pass rule (only `done`) and a re-take rule: SELECT lead_key, state, created_at, updated_at; truncate only if every row is a film-set made-up lead the owner can name; otherwise stop and ask. Step 3 and F6B-02 and F6B-01 aligned.
2. M2: step 1 switches off whichever set is active (real four on first pass, film four on re-take, both if unsure); step 4 says it switches the film set back on.
3. Nits: wait a few seconds for runs in progress and re-run the check (small insert window noted); angle brackets must be gone, '' for a quote in the key; result must read UPDATE 1, UPDATE 0 = nothing reset; recipe A gets mail_sent=false (checked build_mainframe.py:103: MarkFailed sets failed only when mail_sent is false, so harmless; equals B2 apart from matched state); empty table or empty SELECT is fine; review rows stop step 2 on the first pass (what to do: ask the owner), named film-set review rows allowed on a re-take.
