# TAKE-CHECKLIST round 41 stranger read, lines 114-400 (agent aaf323f0, egm-comprehension), Blockers/Majors only, non-security
Saved by flows-audit, condensed. Reviewer words unverified; static. NOT read: lines 1-113 and 401-end. 0 Blockers, 11 Majors. IST conversions and the 269-minute arithmetic from 04:00Z checked correct.
M1 Step 1 start conflicts: L212 "03:31Z start of RUNBOOK step 1" vs L116/126/183 step 1 at 04:00Z (03:31Z+269 = 08:00Z matches L127; 04:00Z+269 = 08:29Z matches L116). Fix: one start time, recompute the other.
M2 "decision 1" edit (L119; L384 condition) would fail Row 3 (L204: any other .py/.sh in git diff --name-only $FINAL_SHA $PATCH_BRANCH = NOT PASSED); nothing says the edit lands on $BRANCH before Block R3 with FINDINGS and LEDGER edits in that commit.
M3 Row 3 (e) "prints nothing" (L204) cannot fail cleanly (unknown ref prints to stderr). Fix: test -z "$(git ...)" && echo code-diff-clean with need_set.
M4 Step 0 (L135) prints "step0 ok: " with empty branch in detached HEAD. Fix: test -n "$(git -C "$REPO" branch --show-current)".
M5 Once-only sha guard (L148 vs L197) appends a second line (sha-written-repeat); later line silently wins. Fix: refuse and print both values.
M6 Placeholder table not "the ONE table" (L137): $KEY/$KEYS/$ADDR (L148, 154, 175), $REPORT (L165, 183), SHA names (L157, 177) appear twice with different suppliers.
M7 Names used, never defined: $TESTLOG (L206), $GATELOG (only L148), $SHA_PIN2 (L197, 300).
M8 R7j hardcodes F-041 (L365) while L171 says $JUDGE_ITEM is typed in R6j or R7j and L208 says edit the block for F-011. Fix: "$JUDGE_ITEM" in R7j and need_set.
M9 Two rules for a hit in the viewer files (L362): lead may read a hit as harmless vs "a human reading a hit as harmless is not enough". Fix: delete the exception for those two files.
M10 Input nobody is named to supply: $JUDGE_WHO BLOCKED due Tue 04:00Z (L183); pin reviewer "owner or another named human" (L192, 396 item 6); Row 4 exits 4 until named (L205). Fix: name person and channel, deadline before 04:26Z.
M11 No runnable command: check 4 (a)/(b) (L388) SQL with $KEY, no psql/connection/need_set; check 5b (L390) "send two made-up mails with two different lead IDs" with no command; check 6 mail count cannot reach PASS/FAIL.
Unsettled: L198 `( cd "$REPO" && ... )` for Row 3 not found; cd "" succeeds in bash so such a block needs need_set.
