# OWNER-STEPS owner part (lines 9-176) stranger read r18 (agent af592a0; reviewer words unverified)
Saved by flows-audit, condensed. Reviewer opened no source files; ran nothing. Arithmetic (13 rows, 21 "missing" rows, 22 reply forms, 7 items/8 rules/6 causes, UTC/IST pairs, weekdays) reported passing.
Verdict: no Blockers, 9 Major, 10 Nit.
Major
1 L33/107/118: take decision 09:30-10:00 but typing message arrives by 09:00; owner has no signal at 10:00 that take is on or moved. Say lead posts "starting now"/"moved" at 10:00, or owner types at named times unless a new-day message came.
2 L116 says after a cancelled day "the only such reply is 'missing: new day'"; rule 6 (L60) and L175 keep starter and kind B replies. Fix L116.
3 L99 tells owner to write "missing: take-prep message" at 08:00/08:30 without "unless Wednesday was already NO-GO" (rule 7 cause 1).
4 L102 chat window covers only Tue 08:00-16:00 and Wed 07:00-18:00Z; owner also must write "missing: new day" 08:00 Thu 19-Sun 22, answer morning messages (L120), follow a new take day. Say when to be reachable; late take shifts times but not the 18:00 end.
5 Retake logic (L47-50, 90, 123, 126): Case A question unconditional but retake exists only if lead found a fault; "retake yes" to unconditional question counts as retake under way; Case B can turn into Case A but L126 allows "retake yes" in Case A only; no rule if lead's 12:00 word never comes.
6 L60/108/2b: what repeats after a move (cause 5) or ended take (cause 6): take-prep, item 6 question, HubSpot test, delete message 1; delete message for a contact left by an ended take.
7 L94 vs L160: "stop" holds delete message 2, but L160 tells owner to write "missing: delete message 2". Add "or you wrote stop and the lead has not yet written back".
8 L46: lead may ask for more money but no reply words (L126 "exactly these"). Add form "yes, up to US$<amount>"/"no" or say it never happens.
9 L60/96: last "missing: new day" Sun 22, latest take day Mon 23; nothing for no day by Mon 23; model key stays unrevoked; is item 4 still wanted if no take.
Nit
1 L14/16-17 "explained in the order you meet the words" false: forward uses (NOT YET DECIDED, safety test, ceiling, retake case, item 6, "the flows", item 3/5, rule 2 before rules, UTC/IST before rule 1). 2 "the audit", "this sheet" undefined for owner. 3 lead-only terms: T19-T21 (L39), "the sending mailbox" (L121). 4 L16 when the lead's first message comes. 5 L12 "Do nothing until re-check done" vs kind B replies: reword "act on no request". 6 rule 2 (L56) fixed 14:00 vs rule 7 heading (L61) every Tuesday time planned. 7 rule 3 (L57) times move vs rule 8 (L73) post fixed 15:00Z; take at 12:00 Mon 23 contradicts. 8 "deleted" L129 vs step 5 L144 "recently deleted"; "not deleted" normal list vs view not named. 9 L118 how to reach remote typing window; unconfirmed word typing; L87 at computer until 11:15 even if overruns. 10 L84/99 08:00 boundary race.
Constraint for fixer: lead part (line 177 onward) must stay byte-identical (cmp against backup).
