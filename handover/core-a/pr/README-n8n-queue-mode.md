Check result (state of 2026-11-20 after the lead's order 015): `n8n/README-trigger.md` ALREADY contains the queue mode statement, in the places below. No new text is needed; the file is unchanged by this part of the PR package. The root README.md needs no queue mode sentence, because no root text mentions n8n (core-b merges only the door section named in handover/core-b/requests/from-core-a-B8-text.md).
The coordinator strips every `[path:line]` proof in square brackets before pasting.

The statement stands as follows in the file. Do not reword it: one phrase of it is pinned by a test. [tests/triggers/test_n8n_template.py:1620]

- Line 209, end of the bullet on "Answer caller: taken": "What 202 really means: nothing is durable yet, neither in n8n beyond this one execution nor in Hadavin. Queue mode required for no event loss is the deployment requirement we ask for, unverified. Run n8n in queue mode (recommended; NOT VERIFIED here, queue mode was never run). In default mode a restart during a 60 s wait lost the run; waits of 70 s and 120 s survived once each; a restart during a send was not run." [n8n/README-trigger.md:207-209]
- Line 393, end of the "Still UNVERIFIED" paragraph: the same sentences, after "the real Hadavin endpoint behind a real proxy, n8n Cloud and queue mode". [n8n/README-trigger.md:392-393]
- Lines 107 and 883 list "n8n Cloud and queue mode" and "NOT VERIFIED: n8n Cloud, queue mode, and an external task runner" as not run. [n8n/README-trigger.md:107; n8n/README-trigger.md:883]

What this means for the PR text, in plain words:
- Queue mode is the deployment we recommend. It was never run, so no claim of "no event loss" is made. [n8n/README-trigger.md:209]
- The caller's 202 is given before anything is stored in Hadavin. A 202 therefore means "taken by the workflow", not "done". [n8n/README-trigger.md:207-209; n8n/README-trigger.md:393]
- In default mode (not queue mode) one restart during a 60 second wait lost the run, and waits of 70 and 120 seconds survived once each. [n8n/README-trigger.md:209]
- The template as a whole ran once, in n8n 2.47.7. [n8n/README-trigger.md:3]
- What the sender must do after a 2xx is in the section "What the sender must do: poll the run state". There is no read address; polling means sending the same signed key and document again. [n8n/README-trigger.md:596-626]

Other lines of that README change only on the merged tree: the default `max_running` 4 and the `triggers` block in the config code. That text is in `README-trigger-postmerge.md`.
