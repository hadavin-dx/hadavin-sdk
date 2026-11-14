## HEARTBEAT 193 (17:22Z) - lease 45 s kill points done: 15 valid runs, all correct; caption numbers below; ERROR (CRM refuses every call) at lease 45 s x3 now running

WORKERS: 3 lanes (my script processes), 0 language-model agents. Each lane runs ONE script: the ERROR case at lease 45 s (CRM answers 500 to every call from the start), n = 3 in parallel; ends about 17:35Z. Criteria as before: state failed, exactly 1 alert naming the lead, 0 mails to intake, 0 CRM rows, within 3 x lease + 150 s.

CAPTION NUMBERS (film-v4, lease 45 s, demo 873a908a, start point = the KILL):
| Point | n | Final state | Intake / alerts / CRM rows | Kill to final s, median / max | n8n up to final s, median / max |
|---|---|---|---|---|---|
| K1 (killed at CRM write) | 5 | done | 1 / 0 / 1 | 60.8 / 61.9 | 52.9 / 54.9 |
| K2 (killed after the mail step) | 5 | done | 1 / 0 / 1 | 60.9 / 61.2 | 52.9 / 52.9 |
| K3 (killed after CRM write) | 5 | unknown | 0 / 1 / 1 | see Part 3 of kill/RESULTS.md | 52.8 to 54.9 |
| K6 (killed after mail stored) | 3 | unknown | 1 / 1 / 1 | see Part 3 | 52.8 to 54.8 |
So the caption can say: "about a minute after the crash" (61 to 62 s at the worst in 18 valid runs; my restart takes 7 to 9 s of it; measured every 2 s). Nothing lost, nothing doubled: 1 CRM row in every run.
Not run: K3B (my harness has no such point; I do not know the case and may not read the demo results; one line from you and I run it).

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list): ERROR at lease 45 s (running); K3B; failed mark after a sent alert; comparison with the demo table (I have saved all numbers; will compare after ERROR).
WHAT I WOULD DO NEXT (ranked): 1) ERROR x3 result; 2) compare with the demo table, state differences plainly; 3) one video line; then stop all processes and report counts.
