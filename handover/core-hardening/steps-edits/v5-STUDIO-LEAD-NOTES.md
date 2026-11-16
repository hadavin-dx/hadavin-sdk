# Studio lead notes for the recording run (moved out of the owner sheet, v5)

Not for the owner to act on. Moved from OWNER-STEPS-realrun-v4.md lines 172-184. Each point below has a default for the owner: do nothing until the studio lead says. The editor-history note of v4 line 3 is deleted.

1. Order of the rehearsal and any trial run on the live throwaway accounts (the rehearsal does not prove live Gmail or HubSpot).
2. Whether the run's fresh n8n needs the first-visit owner login and the three connections at all; which address and password; who switches the workflows on. The n8n database login is meant to be limited (read, add and change rows of the people table only, never the administrator login); who creates its password and who types it is open. The rule that the owner types secrets still applies; privileges are planned, not proven.
3. The address and port the owner opens n8n at. The rehearsal used `http://localhost:5690`; 5678 and 5679 are the owner's own n8n and are not touched. The port for the run is not chosen. Not checked: whether the Windows browser reaches n8n inside WSL (re-check).
4. The run date (no plan gives one) and the pattern for run names; whether the program needs the run name before the confirmation line (test addresses carry it).
5. Whether the owner's HubSpot key used by the run may delete contacts (a read-only key can check but not delete; the archive is a DELETE call).
6. Whether n8n's mail-sending step detail shows real addresses (the rehearsal can check).
7. Candidate proof screens to offer the owner.
8. Which HubSpot private apps are the run's (ask the owner, step I.2) and the final list to confirm.
9. The exact final words of the claim after the rehearsal, with a limit sentence if a crash between sending the mail and noting it can send the mail twice or was not tested.
10. Whether `shred` exists in the owner's WSL.
