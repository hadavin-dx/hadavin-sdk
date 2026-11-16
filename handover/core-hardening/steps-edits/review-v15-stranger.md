# v15 owner sheet: stranger read (egm-comprehension), condensed copy, 2026-11-16
S = OWNER-STEPS-realrun-v15.md, C = card, A = appendix. Read only; nothing run.
## Blockers
1 Stop words conflict (S:35-38, 89, 95, 103; C:83-84; A:140): long string at A.1 says Freeze but table says Key exposed outranks; 0.5 filter hit says send "filter count <n>" vs Key exposed "send only a key-like text was on the screen"; App.15 step 2 "cannot find key list: Freeze" while key on screen; Freeze forbids typing only in program window, not check window; silence is a Freeze trigger (S:37, C:84) yet C:83 says silence expected during n8n restart; reconciling row 16 is blank.
2 "Stop" undefined where used most: steps 0.1-0.3 have no stop list (S:38); lowercase "stop" (A:140, 143); S:89 any Stop after probe key file exists means 0.6, but when the file is created is B20.
3 Day of step A unclear: Part 1 "Before the day" vs S:98 "made on the run day"; A.6 yes needed before go; order table (A:82-83) puts A before B-D which are run-day (S:111); row 1 (A:22) says B-D start days before.
4 Posting/video logistics missing (S:126-128, 142-146; A:136): recording software and file location, editor hand-over, "player", where to post, who uploads; shot list only PROPOSED.
5 People vs privacy: rows 4 and 15 never the owner, owner holds at most one of rows 5-7, so two other humans needed (B23 only a proposal); rule 9 and C:67 say nobody may see the screen, C:74 "people above are ready" and recording ON; S1 films the program window.
## Majors
6 One letter many meanings (steps A-J/T/G, blanks B1-B29, test persons A/B/C, "A reading"/"E reading", "C.1" vs "C unknown").
7 Two names for one thing: run name/take id; person id/lead key; money stop/window end; lead (sales contact)/studio lead; "key" always secret (S:28) but A:9 calls person id "the key"; program settings file/settings file/model settings file/stage.env; "window" four meanings; "row" two meanings (C:5 vs C:8; C:24 two values in one row vs A:18); "table" (A:12).
8 "Each defined before use" (S:19) false: backstop, ledger, usage page, run total, balance, Emergency cancel used at S:12, 36, 44 before S:64; undefined for non-technical reader: flows, node types, final-head check, Postgres, port, container, lock file, clean start, admin role, mf_leads, claim, "imported and activated", loopback, retake count, ledger code.
9 Money rule item 4 (S:71) ambiguous: which two reads; what to do with F.4 reading inside usage lag (B22).
10 A.5 (S:107) "open the private app of the HubSpot key in n8n" vs C.2 "never sign in to n8n".
11 Step 0 "tries to delete" a contact (S:89) vs C:89 "nothing in this card makes the program delete"; verbs remove/close outside the four verbs (S:29); revoke/cancel may not match button names.
12 Step 0 folder: 0.2/0.3 say "the cd line" (program folder, C:29) but hubspot_probe.py is in another folder (row 19, A:40); 0.4 does not say which window.
13 Clock checks (A:145): date, ls --time-style=full-iso, ps lstart print different zone formats; zone to compare not stated.
14 Price command (A:15) can print float noise (0.30000000000000004) but S:104 rejects anything but same value with extra zeros.
15 Go items 4 and 5 (S:54-55) are statements owner must trust; S:54 "You do not look in n8n"; A.6 yes invalid without item 5.
16 Exit-code rule (S:57, A:71) can make run unpostable: case C unknown is a normal result but only exit 0 accepted; not said up front (B2 blank).
17 Notice/printed result wording unknown (B9, A:55-71); ten-condition notice comparison (C:78) depends on wording nobody has seen.
## Nits
S:7 packs four marker types; 8x8 checksum comparison slow (S:22); App.17 "for the studio lead" inside owner doc; "the program" vs "the model program"; rule 10 forbids ~ but owner commands use it; S:44 five ideas in a paragraph; `<B28>` easy to leave; proof-screen number chosen but nothing filmed for it (A:135).
## Did not understand
How owner and studio lead exchange messages/"go message"; what UNVERIFIED asks me to do; who row 15 is and how they judge the ban list; ledger and backstop contents; lease sentence and crash test; whether rehearsal and trial run both needed; what to do if the notice still says delete/archive (C:78).
## Still needs a second person or technical guess after blanks filled
Two other humans plus room rule; lead's own statements (go items 4, 5, B3, B8, B10, crash-test result); judging command output (readlink -f vs ls -l, pgrep one line, ps/ls/date times, grep of settings file); finding account pages (B4), Windows labels, which HubSpot private app is n8n's (I.2), which model keys are this project's (A.0b); printed result if wording differs; recording tool/editor/upload (Blocker 4); unverified GUI paths differ means Freeze.
Not checked: v15-OPEN/CHANGES/check, scripts, any command or page, blank numbering consistency, money arithmetic beyond the worked example. Dates consistent (Mon 16, Wed 18, Mon 23, Wed 25 Nov; 23:59 IST = 18:29 UTC).
