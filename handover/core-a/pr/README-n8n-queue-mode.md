Check result: n8n/README-trigger.md ALREADY contains the queue mode statement, in two places. No new text is needed; the file is unchanged by this PR package.

Line 209 (end of the bullet on "Answer caller: taken"):
> What 202 really means: nothing is durable yet, neither in n8n beyond this one execution nor in Hadavin. Queue mode required for no event loss is the deployment requirement we ask for, unverified. Run n8n in queue mode (recommended; NOT VERIFIED here, queue mode was never run). In default mode a restart during a 60 s wait lost the run; waits of 70 s and 120 s survived once each; a restart during a send was not run.

Line 394 (end of the "Still UNVERIFIED" paragraph):
> ... the real Hadavin endpoint behind a real proxy, n8n Cloud and queue mode. The 202 to the caller is given before anything is stored in Hadavin. "Queue mode required for no event loss" is the deployment requirement we ask for, unverified. Run n8n in queue mode (recommended; NOT VERIFIED here, queue mode was never run). In default mode a restart during a 60 s wait lost the run; waits of 70 s and 120 s survived once each; a restart during a send was not run.

Lines 107 and 801 list "n8n Cloud and queue mode" / "NOT VERIFIED: n8n Cloud, queue mode, and an external task runner" as not run. [n8n/README-trigger.md]
