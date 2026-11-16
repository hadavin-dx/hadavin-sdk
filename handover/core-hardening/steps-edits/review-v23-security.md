# Owner sheet v23: security and money review (condensed copy of the reviewer's report)
Saved by the lead session. Reviewer read OWNER-SHEET-v23.md, LEAD-RELEASE-NOTE-v7.md and v23-OPEN-FOR-LEAD.md only. Nothing was run. Vendor page behaviour UNVERIFIED.

## Verdict (failures first)
NOT releasable. 0 Blockers, 6 Majors, 11 Nits. The three v22 majors are only partly closed.

## v22 majors, status
1. Card "only list" missing app passwords and HubSpot app secrets: mostly closed. Gap: a HubSpot app secret shown on screen has no immediate revoke (R1 routes only an app password to (c)); (d) needs "model key cancelled", never told if no key was made.
2. Clean-up template lacked HubSpot apps: closed.
3. Older-key cancel A/B: correctly still open; bracket text leaves traps in both variants.

## Majors
- M1 Variant B has no route for the older key's identity (lines 102, 85, 107, 109, 63): 5.1 and check 6 are A-only, yet the numbers message, the yes and key-list check 1 need that name. Lead may type a stale or guessed name. Fix: 5.1 report and check 6 apply to both variants.
- M2 Variant B leaves a paid key alive after the run with no authority to cancel it, even if its text leaks (lines 34, 48, 49). Fix: B rule allowing cancel of the older key if its text appears, plus a post-run line on its fate.
- M3 A run that never reaches key creation can never trigger clean-up or revoke (lines 133, 34(d), 32): 8.2 needs "model key cancelled". Fix: allow "no key was made" in its place.
- M4 The date is never checked at run time (lines 120, 113, 81): "date -u before latest start" reads as time of day only. Fix: 6.3 and 7.1 require the full date to equal the run day.
- M5 Balance and auto-reload read only before the yes, never again before key or run (lines 107, 109, 120). Fix: re-read at 6.2 or 7.1 and compare with the yes.
- M6 HubSpot "rotate" can create a new live secret on screen (line 135) and conflicts with R1 and card (d); the card's last-resort step (lines 43, 30) is unbounded and not named in the yes. Fix: allow only delete or revoke; bound the last-resort step and name it in the yes.

## Nits
N1 card not self-contained (points to 6.5, 7.9, 8.1, 8.7, FREEZE; step 3 loops over list (a) only). N2 R1 card applies only while a key is alive. N3 R6 character rule forbids characters used in listed commands (-l, -u, $?, ^, =, ~, quotes). N4 R8 forbids a semicolon used in the example tell text (line 14). N5 R4 under B plural vs check 3 singular. N6 R1 "file that holds a secret" vs 6.6 key file path: say "file contents". N7 line 2 explains A/B markers after they are deleted. N8 no step on key scope (UNVERIFIED whether options exist). N9 no proof the cancelled key is refused; lead erases the key file first (lead decision). N10 stale references: "card Part 2 (b)" in Note line 136 and Open 2, 49, 50, 62; v23-OPEN-FOR-LEAD line 3 says v21; Note has unbracketed A-only text (117, 136, 63). N11 R9(a) vs the receiver Gmail list showing the sender address.

## Held up
Numbers (0.27, 0.81, 1321 cents, 860 s, 18:14:40 UTC = 23:44:40 IST, 18:29 UTC = 23:59 IST, 17:39 UTC, 23 Nov example, weekday, 13 submissions); cancel rule stated once in the card; alarm arithmetic (30 min).

## Not verified
check-v23.py not read (the Note's claim that it proves each variant consistent is unconfirmed; M1, M2, N10 suggest it does not).
