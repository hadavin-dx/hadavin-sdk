# EDITS round 10 design review (egm-design, condensed copy of the inline report), 2026-11-16
Target: steps-edits/EDITS.md (54 rows). Read-only; old-text uniqueness checked by eye, not by script. Verdict: 0 blockers, 4 majors, 9 minors.

## MAJOR
- M1 Credential count (E-09 step f, E-37, v3 lines 75, 79, 83, 121): E-09 calls the Postgres credential "a fourth saved credential, besides HubSpot, the model and Gmail"; E-37 tells the owner to type "HubSpot, the model, Gmail and the take's database" into n8n. v3 and plan v5 list three n8n credentials (SMTP, HubSpot, Postgres). The model key is read by the stage from a key file, so typing it into n8n would put a paid secret in n8n's database outside the model stage's ledger. Fix: drop "the model" from E-09 f and E-37, state three credentials, or change E-48 and step 22 item 1 if a model credential really exists.
- M2 Held E-53 MUST NOT reads as a permission to start the stage with a real key file when a written yes with a number is quoted; contradicts Apply-now E-11 (assistant never starts the model stage with the real key file's path). Fix: plain MUST NOT, or say who starts the stage and how, and reconcile E-11.
- M3 v3 steps 21, 22 and the send table (lines 117, 119-120, 147) contradict E-48 and E-55 on key-revoke timing: step 21 says "Mon 23 Nov before 18:29 UTC: you watch the cut ... Retirement follows"; E-48/E-55 revoke the model key right after the take, by 18:19 UTC = 23:49 IST. Revoking right after the take also conflicts with step 20 (a retake after a failure). Fix: key revoke is the first retirement item, independent of the cut; say what happens if a retake is still possible; align lines 117 and 147.
- M4 E-13 hold labels (lines 313, 321) are "NEW 1 [HOLD G3..." and "NEW 2 [HOLD G3..." while line 20 says every Hold label starts with "NEW [HOLD Gx: DO NOT APPLY]"; a script that skips on the prefix "NEW [HOLD" would write the literal placeholder into v3 lines 99 and 11. Fix: relabel "NEW [HOLD G3: DO NOT APPLY] (1)" and "(2)", or correct line 20.

## MINOR
1. E-12 drops Q25's condition (no take on 23 Nov unless the Q27 reading of the final code is shown); only the Why mentions Q27. Put it in the owner text.
2. E-09 step b omits `umask 077` (v3 line 58 uses it); the password file is world-readable until the chmod in step d.
3. E-09 step g does not say how n8n.env gets its other required lines; if the assistant writes them, "never opens n8n.env" is wrong.
4. E-51 has the assistant show two lines of the stage settings file; whether that file sits under an owner-only secret folder is not shown.
5. E-04 and E-42 (held) do not say "delete only the contacts on the list".
6. E-16: removing the container also deleting n8n's database and the take's table is unverified if a Docker volume is used; the "folder of its own" for copied results is unnamed.
7. E-48 older-keys bullet "except the one made for this take" is ambiguous if the take key is shared (ND7a "no").
8. E-03 says "You do nothing for the two tests unless the assistant asks", while E-11 needs a written "ok" before each test.
9. E-09 sits in step 8 ("When the lead says n8n is running") while its steps a to e must come before n8n starts; move it out of step 8 in v4.

## Checked and consistent (reviewer)
All 54 old texts match their lines and occur once; no overlaps; counts 54, 35/15/4, 42/12 and five type counts (15, 10, 14, 14, 1) hold; no Apply-now text states as fact that the take deletes or archives (Q23); all UTC/IST pairs correct (18:29 = 23:59, 18:19 = 23:49, 18:04 = 23:34, 18:14 = 23:44); weekdays correct; no secret printed.

## Could not check
Old-text uniqueness by script; plan v5 beyond a grep; code facts (run_real_check_n8n.py:1051, crm_hubspot.py:504-509, the 860 s start margin, stage behaviour on a revoked key); whether stage.env is under a secret folder; Docker volume behaviour; vendor click paths; EL-1 to EL-7 source.
