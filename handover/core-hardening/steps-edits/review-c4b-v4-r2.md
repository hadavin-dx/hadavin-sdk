# C4b v4 round 2, naive reader (egm comprehension), condensed copy, 2026-11-16
Reader read only OWNER-STEPS-realrun-v4.md. Readiness: BLOCKER. Nothing edited.
## Contradictions to fix
1 Retire check (l.126) runs a script inside the take folder, but l.122 says the studio lead removes the take folder first. Say where the script lives.
2 Take id (l.27, owner invents it) vs take config (l.28, lead prepares, owner does not edit) vs command l.78 `--take <config>`: how the id reaches the program is not stated.
3 n8n sign-in: l.71 "do not open n8n until the lead gives the address" vs l.73 profile must sign in to n8n before the take.
4 Take date: l.16 "lead sets date, not fixed" vs l.118,121,157 hard-code Mon 23 Nov; l.119 "no further take" vs step G needing a new take; 18:14 + watch + clean-up cannot end by 18:29; l.157 "about 14 min before 18:29" is 18:15 not 18:14.
5 l.5 says approval of the recorded take is done, l.54 and step A need a written yes before every paid take, l.169 says it does not exist yet.
6 l.101 only take-<id>-a/b/c@example.com may show, but top-bar account address and To/From (receiver/sender throwaway addresses) are also checked; how mail to @example.com reaches the receiver is never explained.
7 l.48 "most the take can cost is the number in your yes" vs "program does NOT enforce a fixed ceiling"; "sensible price" has no example.
8 l.43 says Archive is not used; l.96 prompt says "archive"; HubSpot archive is recoverable but "gone" is claimed.
9 l.84 "up to 3 mails" vs l.26 sends A twice, B ten times, C once: unexplained.
10 l.22 says "lead" appears once; "studio lead" appears dozens of times and "lead id" twice (l.132).
## Leftovers and structure
Editor note l.3 (history of versions). Step F is under "The take" but l.14 says after the take. l.172-184 studio-lead section sits inside the owner sheet (move to a separate file).
## Words not understood
the plan; flows; public repository; Hook door/two doors; Loopback (defined, never used); Retire check; company address; "made-up keys" vs key=secret; cut; STILL WORKS / remove that credential; shred -u (what, which files); "list that folder" no command; lock file take-<name>.lock; "keys already used"; label demo as folder; mailed-by; stage.journal, spend record; take folder; WSL open and ~; "your answer on the take date".
## Steps unclear
A: "look at two values on the lead's screen" (lead is a Claude session, no screen). B: no click path for sleep/lid. C.1: does label demo exist, how made, are Spam/Trash empty. C.2: which password/keys, how to copy from WSL to Chrome, which owner login. C.3: what "label demo only" means. D: id not in command; proof screen choice with nothing to choose from. Who films / starts recording / edits the cut never stated. E: how lead knows filming is done before `end`. F: how to hide top-bar address. G: "remove demo mails" = delete, trash or label? I.1 screenshot may show real address. I.2 how to tell which private app the key belongs to. I.4 "rerun later" no timing.
## Money / data loss without warning
No figure for 3 worst-case calls; a failed take costs again; other costs. "Retry at most once": of what, does it spend. Step G delete only take-<id> contacts and only receiver-account mails. shred -u permanent, files not listed, rm fallback unchecked. Deleting private apps irreversible, say what breaks. l.98 delete leftover contacts: how, how many. Never delete ~/.hadavin-take-tags/<id>.used. The `end` warning is buried at end of step D.
## Two meanings
take (run / n8n takes in / program / date / id / config / folder / lock / paid take) is worst; lead (studio lead / lead desk / lead id / lead on screens); remove/delete/archive/revoke (about 7 acts); real (real run vs made-up); window (time / terminal / WSL); profile (Chrome vs Gmail menu); key (secret vs made-up); cut; run; practice run vs rehearsal; contact/person/people/lead.
## Steps for someone else
lead's screen; lead stops/restarts n8n on owner laptop; filming and recording; frame scan (editor job); HubSpot/Google admin and retire check are owner steps though l.5 says lead does checks; config placement; whole studio-lead section; the must-NOT-say list should be checked by someone else before posting.
Notes: IST/UTC conversions right (18:14 UTC = 23:44 IST; 15:00 UTC = 20:30 IST). Retire-check exit codes (0,3,2) differ from take exit codes (0,1,2,3).
