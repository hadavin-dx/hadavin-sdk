# DECISIONS of core-b (newest on top; the lead writes the verdict column)

| time UTC / IST | question | options | CHOSEN and why | gives up | reversible | lead verdict |
|---|---|---|---|---|---|---|
| 2026-11-20 05:20 UTC / 10:50 IST | Board has 7 tables (ORDER 003) but the template says keep it under 3 KB | cut tables; or keep tables and go over 3 KB | CHOSE keep all tables, short rows: ORDER 003 is newer and names the tables | the 3 KB limit of the template | yes | |
| 2026-11-20 05:20 UTC / 10:50 IST | Cron refused: how to keep the board fresh | retry cron; background shell loop; board at end of each tool batch | CHOSE end-of-batch board via tools/board.sh: it is the fallback ORDER 003 names; a shell loop breaks preamble rule 19 and would work around a denial | strict one-minute rhythm | yes | |
| 2026-11-20 05:20 UTC / 10:50 IST | Who does Q1, Q2, T1 | three agents; or split | CHOSE Q1 by me (one shell batch), Q2 by one lookup agent (fable), T1 by me: I write the tickets, so the plan must be in my own context | some parallel speed on T1 | yes | |
| 2026-11-20 05:20 UTC / 10:50 IST | Q3 to Q9 baselines | run them; skip | CHOSE skip: the lead's GO message item 4 says the lead runs them on the laptop | own evidence of inherited failures until the lead's results arrive | yes | |
| 2026-11-20 05:20 UTC / 10:50 IST | Pushing wip/cloud-core-b/* branches | push when step A is ready; hold | CHOSE hold: the owner's instruction to this session names only branch cloud/core-b; a new branch needs the owner's yes typed in this session. UPDATE 05:21 UTC: the owner typed the GO with wip/cloud-core-b/* in this session, hold lifted | nothing now | yes | |
