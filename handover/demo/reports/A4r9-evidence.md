# A4r9 evidence status (cloud session, 00:3xZ 2026-11-10; IST = UTC+5:30). Raw facts only. NOT complete.

## Done (earlier, with files)
- Full suite on A4r9: `S1k-full.log` = 797 passed, 1 skipped, 2 known red (gitleaks hygiene, wordlist hygiene). Not re-run on a second machine state.
- `linux-evidence-1.md` is the older ORDER 199 output (tree fix1, not A4r9); nothing new was added to it.

## NOT done, and why
- Campaign (model-slow, model-timeout, catcher-slow) on A4r9: started 22:43:57Z, 23:06:58Z, 23:47:48Z, and again ~00:29Z. The sandbox machine restarted before each restart (`uptime` read "up 0 min" at 23:47Z and 00:27Z), which kills every process I started. Each earlier run produced no scenario result (model-slow never finished: the A4r7 run of this scenario took 671 s). No drain time, no check result, no model-timeout answer exists for A4r9.
- Mutation round (81 + 23 on A4r9): not started. It needs the campaign finished first (4 cores, timing), and a run of about 1-3 h cannot survive a machine restart every ~40 min.
- So there are NO A4r9 campaign or mutation counts to give. Earlier partial numbers (A4r7: mutation 61/62 killed at 65 of 104 with #48 equivalent; model-slow passes checks 1-6, fails drain only) are in `mutation-A4r7-PARTIAL.md` and APPLY-ORDER.md and are for A4r7, not A4r9.

## Next step
Campaign restarted 00:29Z and running detached (run9.sh). Mutation round follows it. If the machine restarts again, tell me whether to run a shorter plan (one scenario per start, results saved after each) instead; I will do that by default from the next restart: one scenario at a time, each result pushed when done.
