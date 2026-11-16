Terms for this page: see work/t19-terms.md (one glossary for all T19 pages).
Fix block (16 Nov 2026, from cold read 832): the real owner of both checks is NOT SET; the lead assigns one (no date). T19 proposal: studio lead sends one made-up lead twice with the same lead id through the take's webhook; expected 1 mail, 1 HubSpot write, 1 stored row in the stored-leads table (name NOT SET); run command NOT SET (fill_flows.py not built). F8 proposal: after clean-up (clean-up = the steps on OWNER-CLEANUP-CARD.md, done by the owner), a query returns 0 rows for the test lead id in each n8n table; the table list is NOT SET. Pass rule for F8: that 0-row result; it has not run. Words not used below (KeyOk, Claim, recovery, F-002, T1-8) are not defined; ignore them.

# T19 and stored-data steps: CURRENT (16 Nov 2026). Nothing here has run. History: work/t19-history.md (not current; do not run it).
Words: T19 = send one made-up test contact twice and expect 1 mail, 1 HubSpot write and 1 stored lead row (UNVERIFIED, from the old page). F8 = after clean-up, no test-contact data remains in n8n (UNVERIFIED). Studio lead = the Claude session. Studio head = the human who runs the studio. mf_leads = the table of stored leads (meaning from L1c line 237). KeyOk, Claim, recovery, row 2, REPORT item 3, F-002, T1-8: meaning not recorded; owner for these: unnamed, the studio head names one (no date set).
| Step | Actor | Command | Expected | UTC / IST |
|---|---|---|---|---|
| T19 send twice | studio lead (the Claude session) | NOT SET (send one made-up lead twice with the same lead id to the take's webhook) | mail 1, HubSpot write 1, stored-leads table (mf_leads, name NOT SET) rows 1 | not run; time NOT SET |
| F8 check after clean-up | NOT SET (no actor named) | NOT SET (query the n8n tables for the test lead id) | 0 rows (pass rule proposed, NOT SET by anyone) | not run; time NOT SET |
The F8 pass rule and table list: NOT SET.
