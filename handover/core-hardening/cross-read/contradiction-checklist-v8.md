# Contradiction check v8 (checker, read-only judge; nothing was fixed)
Date 2026-11-16. Files read in full: paste-check/LEAD-CHECKLIST-v5.md (CL), paste-check/LEAD-FILL-list-v5.md (LF), patches-ready/README.md (PR), inputs/DECISIONS-2026-11-16.md (DEC, items 1-12), ORDERS.md (ORD).

## NOT CHECKED (read first)
- The re-smoke plan itself (inputs/plan-wp6-resmoke-v5.md): the counts 24/10/2/1, the 17 markers on 10 lines, the plan line numbers 2, 3, 4, 125, 258, 275, 433, 434, 585, 586, and the checksum 67a0a195537de875 are NOT verified against it. I only checked that CL and LF agree with each other (they do, see C-10).
- Every sub-file PR cites (v5/README.md, v3/README.md, raw logs, review/*.md, STATUS-BOARD.md, ANSWER-Q18-lead.md, one-place-sweep-r1.md). Test counts and "12 of 12 mutants" are unverified; only their arithmetic was checked.
- evidence-c7g.md (CL line 3, LF line 50) not read. No command was run.
- ORD has no text for "Q18" (10:31Z) or "ORDER 004/011/014"; PR cites Q18 (PR:19). Unverifiable from ORD.

## FAILURES FIRST: contradictions and wrong statements
1. LF:2 says the edits are made "in the copy `PF` of `LEAD-CHECKLIST-v5.md` (step A8)". CL:52 (A8) makes `PF` a copy of the PLAN (`plan-wp6-resmoke-v5.md`), not of the checklist. LF is wrong; CL is right (CL:50, 66).
2. LF:17 says the lead runs steps "or asks the owner to paste the command and send back the output unchanged". DEC 7 (DEC:8) and ORD Q20.1 (ORD:145) say the owner only types y, the challenge and end, and never stops n8n. CL D2(3) (CL:138) also hands the owner a decision ("the owner decides; whoever decides ends it by its exact pid") for a foreign process. Both go beyond DEC 7. ORD Q20.1 confirms only the lead's side. Needs a lead ruling on whether the owner is ever asked to paste or decide.
3. PR:62 says the failing ids occur in "24 of 262,144 id shapes, about 1 test run in 2,731". The arithmetic does not hold: 262,144 / 24 = about 1 in 10,923. 24 of 65,536 gives 1 in 2,731. One of the numbers (262,144 or 24) is wrong. ORD Q16.1 (ORD:139) gives a different measure, "0.015 to 0.045 percent per run" (1 in 2,731 = 0.037 percent, inside that range). So 2,731 agrees with ORD, 262,144 does not agree with 24.
4. PR:12 says the 200_000 `max_tokens` ceiling number "must be confirmed by the studio head". DEC 4 (DEC:6) says the 200_000 question "is moot while C-01 is cut". PR keeps C-01-MINIMAL as OPTIONAL (PR:17, 26), so it is not cut; the minimal check is allowed by DEC 4 only "if the take's model program loads Route config (unverified, not in the video path)". The table row PR:26 drops that condition and adds "pilot and prod only"; PR:17 has the condition. Same file, two strengths. Also ORD Q14 (ORD:122) says "else nothing". Fix: copy the DEC 4 condition into the row and say the 200_000 question is moot unless the minimal patch is applied.
5. G5: ORD ORDER 009 item 3 (ORD:48) says DROP; ORD ORDER 007 item 2 (ORD:26) says drop; DEC 4 (DEC:6) and ORD Q14 (ORD:122) say wording KEEPS. PR:25 "APPLY NOW" matches the newest (DEC 4). But PR:25 states "no behaviour change" as fact; no evidence file is cited in that row. Mild over-claim (the suite count PR:49 is the only support).
6. DEC 11 (DEC:12): patch tests run on a clean sdk tree. PR:11 says guard tests ran on a git-initialised COPY with handover/ removed. ORD ORDER 019 (ORD:94) asked for a fresh `git clone` as the proof. PR does not say a fresh clone was used. Not the same as "clean sdk tree"; gap not stated.
7. CL:5 says questions "5, 7, 6 and 1 are answered inside C1, C2, C4 and C2b". CL:66, C2 (CL:78) and LF:12 say 5 and 7 are both answered in C2 (C1 only reads). The line-5 mapping (5 to C1) disagrees with line 66/78.
8. Folder deletion. LF Q4 (LF:11) says after exit 3 "13.9 has deleted the folder" (the runner deletes `$HOME/hadavin-smoke`). CL D2(4)(b) (CL:139) and LF Q2 (LF:9) say the lead deletes it by hand for a fresh start. Two different actors for the same folder; they cover different cases (S13 cleanup vs P-4b stop) but neither file says so. Make it explicit.
9. Version words: "v5" names the plan (plan-wp6-resmoke-v5), this checklist (CL title), the flows (real-v5), and the core patch folder (PR "v5/"); CL and LF are called "v5" but were written in "the v6 fix pass" and use `plan-v5-repin-v6.patch`. DEC 10 (DEC:11) says "OWNER-STEPS v4 and later replace v3": a version of the checklist is not the same kind of number. Breaks wording rule "one word keeps one meaning". Not a number contradiction, a labelling risk.

## Numbers, dates, shas stated differently
- Pin/base shas: PR uses base `b4cce5b` and head `de6b574` (PR:3, 8); ORD ORDER 009 (ORD:46) names repo2 head `58aa4031` (a different repo/desk, item cancelled); CL uses old pin `eec6ba4` (CL:97, 101) as the comparison base. No conflict found, but three different shas appear; only b4cce5b is in ORD (ORD:59).
- Test counts: PR table 9418 / 9413 / 9491 / 9514 / 9391 / 9389+2: arithmetic checks out (9391+27=9418; 23+4=27; 19 = 11+8; 9514 = 9491+23; 9389+2 = 9391; 9418+455=9873 = 9846+27). No difference found inside PR. Not checked against sources.
- Marker counts: CL:67 "17 markers on 10 lines", CL:42 "24, 10, 2, 1", CL:106 "0, 0, 2, 1", LF:2 "17 marker texts on ten lines". I recounted LF's "marker places" column: 17 texts on 10 distinct plan lines (258, 586, 4, 125, 433, 434, 3, 275, 2, 585). CL and LF agree.
- Dates: ORD Q21.1 (ORD:150): Mon 23 Nov 18:29 UTC = 23:59 IST and Wed 25 Nov 15:00 UTC = 20:30 IST: both conversions are right (+5:30). No date appears in CL, LF or PR that conflicts. PR cites decision times 10:02Z, 10:42Z: both match ORD (ORD:112, 138). "Q18 10:31Z" has no ORD text.
- Four-place pin: CL "FOUR places hold" matches ORD ORDER 017 guidance (header line 2, section 2 code row, first line of P-2, section 11 part A) (ORD:86). Consistent. CL:75 pin "20 rows" not checkable.

## Claims stronger than DECISIONS allows (decisions 1-12)
- DEC 5 forbids claiming "nothing can spend before both typed answers" and accepting the S9-1 fallback. None of the three files makes that claim. CL:3 and LF:3 say the LEAD-GO / LEAD-YES lines are a procedural gate only: this matches DEC 5. OK.
- DEC 2 / Q19: no delete call exists in the take. CL, LF, PR do not mention contacts. Not covered, nothing contradicted.
- DEC 8 (smoke replaced by loopback re-smoke plus one made-up lead) and ORD Q17 (label evidence "real-v5 minus ONE node", never "real-v5 passed"): CL, LF do not state the label. PR has no re-smoke claim. Not checked in plan.
- DEC 1: nothing in CL, LF or PR mentions film-v5 or scenes 5-11. Consistent.
- DEC 4: the PR row for C-01-MINIMAL (see failure 4) is the one over-strong item. PR:62-67 C7b: marked DESCRIBE-ONLY, matches ORD Q16.1. PR:66 admits the patch still needs the lead's independent result review; this is consistent with the reviewer-independence rule.
- PR:3 "Every number below names the file and line it was read from" is stronger than PR:57 (9391 "quoted from v3, not re-run"), PR:62 (262,144 has no source for the shape count) and PR:12 ("no provider page looked up"). Soften.
- CL:3 "Every command below was copied by a script from the patched plan, not retyped" cannot be checked here (plan not read).
- CL:103 says ACCEPT proves only the text `exit 3`/`return 3` exists; this is not stronger than ORD Q20.4 (ORD:148, lead reads the exit code at final head). Consistent.
- ORD Q19.1 (ORD:132): go condition 5 may be given only after the lead's final-head check. No CL, LF or PR text gives that condition. OK.

## Other points (hygiene, not contradictions)
- CL contains a personal Windows user name inside hard-coded paths (C1, C2b, C4, C5, C6, C9, D1, D2 and A8 default). The studio rule says no personal details and no hard-coded paths; the paths are labelled EDIT POINT/guess but the name is in the tracked text. Not changed by me.
- CL:75, 92 give `WT=` and `SF=` paths as a default guess; Q19.4 / DEC 7 not affected.
- No banned vendor brand word was written by me in this file.

## Verified consistent (no contradiction)
CL and LF on: the order of the two patches; markers per question and where each is answered (apart from failure 7); Q4 and CL D1 line 124 ("after kill exit=3 no R2, ever"); the P-4b rule vs ORD ORDER 017 (exit 3 = GONE-FAIL = STOP); Q5 default (no pin until the lead names the commit); runner count before P-1 and at P-2. PR vs ORD: kept scope v5, A-01 deferred, C-01 extras cut, G5 kept, C7b describe-only, branch artefact for the two guard failures.
