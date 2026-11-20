Check result: n8n/README-trigger.md ALREADY contains the queue mode statement, in two places. No new text is needed; the file is unchanged by this PR package.

Line 209 (end of the bullet on "Answer caller: taken"):
> What 202 really means: nothing is durable yet, neither in n8n beyond this one execution nor in Hadavin. Queue mode required for no event loss: without it, an n8n restart loses the event after the caller was told 202.

Line 394 (end of the "Still UNVERIFIED" paragraph):
> ... the real Hadavin endpoint behind a real proxy, n8n Cloud and queue mode. Queue mode required for no event loss: the 202 to the caller is given before anything is stored in Hadavin, and in the default (non-queue) mode an n8n restart loses the execution that holds the event.

Lines 107 and 801 list "n8n Cloud and queue mode" / "NOT VERIFIED: n8n Cloud, queue mode, and an external task runner" as not run. [n8n/README-trigger.md]
