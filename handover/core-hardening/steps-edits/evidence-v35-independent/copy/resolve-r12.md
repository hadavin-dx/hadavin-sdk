# Resolve round 12 (EDITS.md, built by build-r12.py from EDITS.round11.md)

The egm:egm-resolve skill was not used; the lead runs the EGM steps. This file is the builder's own list and counts as unverified until the lead's reviewers and the independent evidence runner have read EDITS.md.

## Failures and gaps first
- Not fixed, with reason:
  - The personal Windows folder name in OWNER-STEPS v3 step 22 item 4 stays: it is in an input file (I may not edit inputs) and is the owner's own folder; changing it needs a new row and the owner's choice of a neutral folder. Next step: owner or lead decides.
  - Two quoted old texts keep a UTC time with no IST in their OLD block (the old step 21 heading, "18:29 UTC", and the old E-12 line "23:59 IST" with no UTC). OLD blocks must be verbatim input lines. The partner time is given in the Why and in the new text (E-12, E-57). The checker prints the pairing note for these two quotes only.
  - "journal" and "spend record" remain in the held row E-49 only (held, not shown to the owner).
- UNVERIFIED (nothing in this round proved it): what HubSpot app 2 is for (L-APP2: unknown; evidence that would settle it is the saved flow export or the plan's credential list; recorded in E-52 and confirmation k); gate G1 / Q23 (does the take program send a delete request; whether "archived" means deleted); the take stopping safely on a revoked key; the take id rule; whether a Docker volume holds the databases; the 14-minute take length; the Start-menu path, the nano keys, the n8n field name "Password", and the model provider's key-list page; that the database server program reads the password file.
- Owner-only: ND15 (when `no more takes` is written; default A, revoke early).

## Findings
| Finding | Status | Where |
|---|---|---|
| Naive B1: how to see the password again, n8n field name, copy-paste route | fixed | E-09 step f |
| Naive B2 / design M1: define the last accepted take, revoke trigger, E-48 versus E-57 conflict, take versus cut | fixed (safer wording chosen: revoke follows `no more takes`; a bad cut then needs a new key and yes); owner choice recorded | E-48 3a-3b, E-52, E-55, E-57, E-58, ND15, rules R7 and R10 |
| Design M2: shred the take-folder copy at once, shred is not a revoke and unreliable, ask whether the key is the one in his n8n | fixed | E-48 3d, 3c, E-37, ND7a2 |
| Design M3: password visible to the assistant through the programs' settings; forbid command-line fallback | fixed | E-09 paragraph "Who can see the password", step e |
| Naive M1 merge the two request lists | fixed | E-12 parts 1 and 2 |
| Naive M2 evidence reply form, one slot per file kind | fixed (four fixed labels; confirmation l asks the lead to confirm no other file is needed) | E-12 |
| Naive M3 define studio lead, exit code, final code, finding | fixed | E-12, E-52 |
| Naive M4 "delete request"; "archived" = deleted not settled (Q23) | fixed; no text says the take deletes or archives | E-12, E-37 |
| Naive M5 container, volume, database server, wipe, shred; split E-16 with consequences | fixed | E-16, E-52 |
| Naive M6 WSL window / terminal / screen | fixed by naming the older words in E-52 (not edited in place; in-place edits would need new rows) | E-52 |
| Naive M7 one reply convention | fixed | E-52 "How you reply" |
| Naive M8 failed check word; crash check "not run" is no | fixed | E-12 |
| Naive M9 split E-48; E-58 conditional | fixed | E-48, E-58 |
| Design minors: chmod 600 n8n.env first; shred path inside take folder; look at key name and last-used date; E-49 "planned"; E-07/E-08 duplicate Why notes | fixed (E-08 Why checked: no duplicate left; E-07 merged) | E-09 g, E-48 3d and 3g, E-49, E-07 |
| Evidence notes: missing partner times | fixed in the new E-57 heading and E-12 text; two quoted old lines excepted (see above) | E-12, E-57 |
| L-23NOV: no take on 23 Nov; latest start 18:04 UTC = 23:34 IST; revoke by 18:19 UTC = 23:49 IST | applied | E-12, E-48, E-55, E-57, E-58 |
| L-APP2 | marked UNVERIFIED with settling evidence | E-52, confirmation k |
| Naive minor lists not named here: not individually re-checked beyond the rows above; the lead's next review will show any left |

## Check
`python3 -I verify12.py` exit 0; output in `resolve-r12-check-output.txt` (FAILURES 0, banned scan 0 hits, 38 negative controls caught, 0 not caught). This only proves the file is self-consistent against the input files; it does not prove the owner texts are understandable (no stranger has read them).
