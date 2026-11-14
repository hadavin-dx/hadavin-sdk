## HEARTBEAT 165 (13:50Z) - NO ferr2 RESULT: THIRD sandbox restart (13:50Z) killed it again; the sandbox is being recycled between my turns, so I now keep my turn open while the queue runs

| Item | Status at 13:50Z |
|---|---|
| ferr2 | VOID again (killed by the sandbox restart at 13:50Z, about 10 min in; no result written). Restarted 13:50Z, ends about 14:04Z. |
| What I know about the restarts (observed, not proven) | Three restarts: 13:15Z, 13:40Z, 13:50Z. After each, uptime reads 0 to 2 min, Postgres, n8n, fakes and the queue script are gone, files stay. Each one came shortly after I ended a turn and before the next lead message arrived. The long runs before 13:15Z survived many turns, so this is not certain. Test: this time I do NOT end my turn while ferr2 runs (bounded sleeps only). If ferr2 finishes, that supports the idle recycling cause; if it dies again with my turn open, the cause is something else and I tell you. An ERROR run needs about 8 min of wall clock (ferr1: 478 s), so restarts every 10 min would stop any ERROR run from finishing. |
| Results so far on the fixed flows (61e3804b) | ERROR ferr1 PASS (HB163). Nothing else yet. |
| Queue | run_g.sh (resumable): ferr2, ferr3, T14, BURST, K3 x3, K6 x3, fixed-flow GREP (fjg1), fault repeats. |

ASK for the lead: if your side can see why my sandbox restarts (idle limit, session resume), tell me; if you can, send a short "go on" message only when needed, since each new message may be what triggers the recycle (not proven).
FAILURES AND RETRIES: ferr2 void twice (restarts 13:40Z and 13:50Z); jg3 first attempt void (my stray process, HB162).
NOT DONE / NOT CHECKED (my list, for the lead to decide): everything after ferr1 on the fixed flows; fixed-flow GREP; fault repeats; RESULTS.md; compare with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) keep the turn open until ferr2 ends; 2) continue the queue; 3) RESULTS.md then compare.
