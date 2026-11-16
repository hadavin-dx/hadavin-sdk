p='OWNER-SHEET-v32-SOURCE.md'; s=open(p,encoding='utf-8').read()
def rep(old,new):
    global s
    assert s.count(old)==1,(s.count(old),old[:80]); s=s.replace(old,new)
# 5.1b shorter, detail to F6
rep("your other channel and your backup person (describe each without a mail address or phone number, for example \"the studio mail\" or \"my brother, by phone\"), and the day you decided to use the money already in the account (R4).",
    "your other channel and your backup person(((F6 Why and background (rationale that is not a step):: Step 5.1b, describe the other channel and the backup person without a mail address or phone number, for example \"the studio mail\" or \"my brother, by phone\"; the lead asks how to reach them later on the other channel. )))), and the day you decided to use the money already in the account (R4).")
# 5.8
rep("The numbers message holds the lead's exact sentence, which must equal the pattern of appendix 8 word for word except the values.(((F8", "The numbers message holds the lead's exact sentence.(((F8")
rep("and give your cancel helper (if you named one) the page OWNER-HELPER-v32.md and their paper (appendix 10).", "and give your cancel helper (if any) their page and paper (appendix 10).")
# 6.7 tick
rep("; if 6.7 failed: no run, the card for your own key, then 7.11 for the older key]]", "; 6.7 failed: the card for your key, then 7.11]]")
# R4
rep("when 6.7 did not cancel it (the run ended earlier, or 6.7 failed or did not run);", "when 6.7 did not cancel it;")
# 7.11 backstop sentence shorter
rep("**Deadline backstop (an owner action on Sun 22 Nov and on Mon 23 Nov):** if the older key (name and creation date equal the blanks) or a key of L1 is still valid when a deadline reminder of 5.8 rings ({{bs}} or {{bm}}), cancel it by the card's L2 or L1, steps 2 to 4, by the backstop time ({{rv23}}) at the latest on Mon 23 Nov. Who acts",
    "**Deadline backstop (Sun 22 Nov and Mon 23 Nov):** when a deadline reminder of 5.8 rings ({{bs}} or {{bm}}), cancel a still valid older key (name and creation date equal the blanks) or key of L1 by the card's L2 or L1, by the backstop time ({{rv23}}) at the latest. Who acts")
# 6.1 Recall shorter
rep("if there is no such page this is a STOP, not a tolerated difference: describe what Settings shows and wait for the lead's written answer in the message place, which rests only on your description (the lead cannot see your screen); no answer: no key);", "if there is no such page this is a STOP: describe what Settings shows and wait for the lead's written answer, which rests only on your description (the lead cannot see your screen); no answer: no key);")
# intro
rep(" and the cancel helper (if you name one) only OWNER-HELPER-v32.md.", "; the cancel helper reads only OWNER-HELPER-v32.md.")
# check 2 detail to appendix
rep("the latest start is at most {{gap_max}} minutes after the earliest key time; the latest start and the alarm time are at least {{sum}} minutes apart (the three waits of the message added: the y minutes ({{y}} in the sample), the run length ({{rl}}) and the film pause ({{fp}}); your think times fall inside the y minutes and the run length).",
    "the latest start is at most {{gap_max}} minutes after the earliest key time; the latest start and the alarm time are at least {{sum}} minutes apart(((F2 The sample numbers message (made-up values, never real):: Check 2, the sum {{sum}}: the three waits of the message added: the y minutes ({{y}} in the sample), the run length ({{rl}}) and the film pause ({{fp}}); your think times fall inside the y minutes and the run length.))).")
open(p,'w',encoding='utf-8').write(s)
