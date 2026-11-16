# EDITS r12 security and money-path review (egm-design, uncapped; condensed copy of the inline report), 2026-11-16
Target: EDITS.md round 12 (56 rows). Read-only; nothing run. Verdict: 1 blocker, 5 majors, 6 minors. r12 fixed the order problem and the E-09 password retype; it did not fix the fail-open state of the model key.

## Prior r11 findings
E-09 password retype FIXED. E-48 vs E-57 revoke order PARTLY FIXED (one order now: `no more takes`, revoke, cut; new contradiction B-1). Revoke trigger PARTLY FIXED (no reply counts as `more takes`, key stays alive). Key copy / shared-key question FIXED IN TEXT but see B-1. E-09 overstatement FIXED for database passwords (gap M-1).

## BLOCKER
- B-1 The model key can stay alive in the likely case and the revoke rule contradicts itself. Unconditional: 3a, E-55, E-57, L-23NOV say revoke by 18:19 UTC = 23:49 IST in every case. Conditional: 3e revokes only for `yes` with `different key`; 3f for `no, other things use it`, `not sure` or `same key` does NOT revoke, no screenshot, key alive with no end date; 3h "if 3e applies to you". FACTS says the owner's own n8n holds a Claude credential and E-37/ND7 call `same key` likely, so the default outcome is a live paid key; `not sure` is the safe-looking answer and leaves it alive. 3a: no reply counts as `more takes`, so if the owner never writes `no more takes`, 3b never fires and no revoke steps are sent. No route that ends with the key dead (new key for the owner's own n8n first, then revoke the old); the open key is not flagged as a deviation from S9-3 and L-23NOV. The screenshot is only a record.

## MAJOR
- M-1 E-09 "who can see the password" covers only database passwords; the three n8n credentials (mailbox app password, HubSpot secret, database password) are stored encrypted, and E-30 says the encryption key is in n8n's environment and `.n8n/config`; step g's "none of them is a password" for n8n.env is a word game if the encryption key is there; the yes sentence does not say the assistant can reach them.
- M-2 Fail-open defaults and no reminder: the "no more takes or more takes" question depends on the assistant asking after every take; Q26 forbids a timer so the 23 Nov hard stop rests on memory or a live session at about 18:00 UTC; nothing says who prompts then.
- M-3 Step 22 item 1 (remove container, rm take folder incl. key copy; irreversible) keeps the v3 line 120 trigger "after the lead says the last take is done", different from the owner's `no more takes`; under option B the owner writes it only after `cut accepted`. Give line 120 the same trigger.
- M-4 E-48 3e does not say how to pick the right key in the provider list (name or last characters); the cropped screenshot cannot prove which key went.
- M-5 E-48 3g: for `same key` nothing about the owner's own n8n keys; "used recently" undefined (L-A/B uses 7 days); default "Revoke the others" is high blast radius (Q19.5).

## MINOR
shred path from a message (no `..`/symlink guard; owner runs it); E-12/E-54 "Wed 18 Nov 2026" without clock time; v3 line 171 "18:29Z ... 18:14Z" without IST, line 147 "By Mon 16" no time; E-12 cites "step 17" for 18:14 (source line 171); E-09 step f field name "Password" unchecked and the "tells you what to do instead" open door; E-51 settings-file location unverified; E-49 wording OK.

## Checked, consistent
Three credentials and the model key consistent across E-09 f, E-37, E-16, v3 lines 75/121; Q23 holds (no Apply now row says the take deletes or archives; E-56 flag; G1 rows Hold; every Hold block labelled); revoke order; UTC/IST arithmetic (18:19=23:49, 18:29=23:59, 18:04=23:34); E-16 removal exact reply, silence means No; the yes in E-12 is a chat line and the take needs a typed `y`, challenge and `end` by the owner.

## Not checked
Code, whether the start program reads a password file, n8n's real key storage, click paths, `shred` under WSL, whether any flow node uses a model credential, v3 lines not read in full, resolve-r12.md and check outputs.
