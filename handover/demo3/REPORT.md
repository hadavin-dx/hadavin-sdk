## MISTAKE FOUND AND FIXED 05:11Z: I pushed four n8n working folders by accident (commit d7cccdcf)

WHAT: while copying the GO-1 run logs I also copied each run's n8nhome folder (about 54 MB each, 4 folders). Each holds that run's throwaway n8n config (with the encryption key n8n generated for that run), a database with stand-in credentials only (made-up values: loopback fake servers, no real key, no real mailbox), and n8n's own cache. No real secret was involved, but it is secret-shaped and large, and it does not belong in git.
FIXED: removed from the branch in the next commit (git rm; only logs events.jsonl, mails.jsonl, crm/stage/smtp logs stay under kill/data/runs/go1-*).
NOT FIXED, needs the lead/owner: the files stay in the git HISTORY of demo/lane3 (about 220 MB) because I may not rewrite history or force-push. Decision for the lead: leave it (all values are made-up run-local stand-ins) or have the branch deleted and re-created without them. I did not touch any other branch.
---
## CORRECTION + FINAL STATE 05:11Z (2026-11-15), after STOP-2: one earlier line in my closeout was wrong

CORRECTION: my STOP-2 closeout said "0 processes running". That was incomplete: one background shell of mine (the first Postgres-start command of GO-1, which also ran a slow search over the whole disk) was still listed as running. I had killed the search but not the shell task. It is now stopped. Checked afterwards: no run script, fake mail/CRM/stage server, n8n, Postgres or agent of mine is running (ps shows none). Agents 0, loops 0, shells 0.
EVERYTHING FOR THE LEAD IS IN THE REPO (branch demo/lane3): REPORT.md (this block and the STOP-2 closeout below it), kill/PLAN-GO1.md, kill/make_go1.py, kill/flows-go1/ (fixed recovery flow, one new start trigger and one SQL), kill/run_p.sh (version 5 = fixed flows), kill/data/results.jsonl and kill/data/runs/go1-* (raw rows and logs of the four GO-1 runs), evidence/go1/ (the stopped agent's raw output: file diff, SQL review, one fixed KS run at 60 s; the mutant run never finished).
RESULT (unchanged): old v4 KS alert at 750 s; fixed flows 60 s in 3 of 3 runs, B90 on fixed flows 1 alert at 120 s. NOT reviewed (no egm:* reviewer ran), no mutant result, two-instance case not tested, not imported into the demo flows, no second alert channel (open item).
STOPPED: no further tool calls until an order starting with GO.

---
## FINAL CLOSEOUT, ORDER STOP-2 05:09Z (2026-11-15): GO-1 withdrawn mid-way; 0 agents, 0 processes running

STATUS: stopped by order. Evidence runner agent stopped (TaskStop), run scripts, fakes, n8n and Postgres stopped. Counts: agents 0, loops 0, run scripts 0 (a pgrep count of 2 was my own shell matching its own command line).
MEASURED (my harness, made-up data; raw rows kill/data/results.jsonl, raw agent output evidence/go1/): KS = kill n8n during the alert send. OLD v4 flows: alert at 750 s, 1 alert, 1 intake mail (go1-old-ks; the earlier n=2 runs were 780 s). FIXED flows (kill/flows-go1: n8n "started" trigger + one SQL clearing unsent alert claims): alert at 60 s in 3 of 3 runs (go1-fix-ks, go1-fix-ks2, and the agent's ev-go1-ks), 1 alert and 1 intake mail each. B90 (hold 90 s, no kill) on fixed flows: 1 alert at 120 s, no duplicate (1 run).
NOT DONE / NOT CHECKED: the agent was stopped before its mutant run finished (no mutant result), so "the test fails without the SQL" is shown only by old-flows vs fixed-flows, not by a mutant. No egm:* reviewer ran, so the fix is NOT reviewed. Two n8n instances at once (T11) not tested; the clear at start could duplicate an alert there. No second alert channel (open item by order). The flow file was not imported into the real demo; it is only under kill/flows-go1.
OPEN DECISIONS (lead): take kill/flows-go1/mf-recovery.json (or make_go1.py) into the demo flows, then review; run T11.
FILES: kill/make_go1.py, kill/flows-go1/, kill/PLAN-GO1.md, kill/run_p.sh (version 5), evidence/go1/.
STOPPED: no further tool calls until an order starting with GO.

---
## HB-GO1-2 04:59Z: fixed flow works in the first run; checks continue

STATUS: KS on the FIXED flows: alert at 60 s after the start of the run (kill at 40 s, restart at 46 s), counts alert 1, intake mail 1, alert_sent true, state unknown (row: kill/data results label go1-fix-ks). KS on the OLD v4 flows (lane 0, label go1-old-ks) was still waiting at 04:57Z with the claim set until 05:06:31Z (late, as before); final row due about 05:10Z.
RUNNING (1 agent, 2 run scripts): agent = EVIDENCE RUNNER (lane 2: diff of the flow files, KS rerun on fixed flows, one mutant); lane 0 = old KS; lane 1 = B90 on fixed flows, then KS repeat. Plan: kill/PLAN-GO1.md.
NOT DONE / NOT CHECKED: B90 on fixed flows; second KS repeat; mutant; reviewer; two-instance case (T11) will not be run.

---
## HB-GO1-1 04:52Z (2026-11-15): ORDER GO-1 started 04:47Z, stop 05:50Z. One item: alert 13 min late after an n8n kill during the alert send.

STATUS: Postgres restarted (data folder owner was reset by the sandbox restart; fixed with chown). Fix built: kill/make_go1.py adds to the demo v4 recovery flow an "n8n started" trigger plus one SQL that clears stale alert claims (alert_until, alert_token) for unsent alerts in state unknown/failed. Files: kill/flows-go1/.
RUNNING NOW (2 run scripts, 0 agents): lane 0 = KS on the OLD v4 flows (proof it fails again, expect about 780 s); lane 1 = KS on the FIXED flows (expect 1 alert soon after restart, well under 12 min). Each takes about 13 min at worst.
NEXT: B90 on the fixed flows (must still be exactly 1 alert), then an EVIDENCE RUNNER agent, then a fresh egm reviewer. Then FINAL CLOSEOUT by 05:50Z.
OPEN ITEMS (named): no second alert channel now (by order). Two n8n instances at once (T11) is NOT tested; the start-up clear could duplicate an alert there (a claim another live instance still holds).
NOT DONE / NOT CHECKED: everything above is not yet measured.

---
## FINAL CLOSEOUT, ORDER WRAP-1 done, re-stamped 18:30Z (first written 17:54Z) - lane3 branch demo/lane3: everything committed and pushed; 0 agents, 0 processes running

STATUS: all my work is in the repo on demo/lane3. Postgres, run scripts, fakes and n8n are stopped (pgrep count 0). No agent is running. Nothing is secret-like (scanned: no key or private-key patterns).

FILE-INDEX (paths under handover/demo3/):
- REPORT.md: this block. evidence/REPORT-archive-2026-11-14.md: all older blocks (HB1 to HB193).
- questions-for-lead.md: my questions and answers (Q-1 to Q-20). register.md: live register (rows for runs e to l are stale; the truth is kill/data/run_all.progress). ORDERS.md, FREEZE.md, MATRIX-1.md, WINDOWS-RUN-1.md: earlier orders, matrix, Windows run notes.
- kill/RESULTS.md: THE results file (generated by kill/make_all.sh from kill/data/results.jsonl): Part 1 kill points, faults, ERROR, burst, GREP; Part 2 v3/v4 alert cases; Part 3 recovery seconds (lease 120 s and 45 s); Part 4 = kill/COMPARE-demo.md (comparison with the demo table).
- kill/PLAN-V3-ALERT.md: plan and pass criteria written before the alert runs (A, B20, B90, C, then B780, KS).
- kill/harness.py (kill points, GREP, ERROR; env LANE for parallel lanes), kill/fakes.py (fake CRM, stage, SMTP with hold/refuse/dead switches), kill/v3.py (alert cases A, B20, B90, B780, C, KS), kill/prepare_probe.py (builds the import files from the demo flow folders), kill/analyze.py, kill/make_results*.py, kill/make_all.sh, kill/run_*.sh (queue scripts; run_p.sh and run_r.sh are the final lane scripts).
- kill/data/: results.jsonl (every run, voided runs labelled VOID-), run_all.progress, runs/<label>/ (events, mails, fake logs per run), last-run-*.out, trace-b90-report.md (agent trace of the v3 duplicate; verified items listed inside).
- evidence/: reviews, checkpoints, patches of the paused fix rounds. evidence/snapshot-b21/b22/b23-tree-vs-head-2026-11-14.patch = the full working tree of the three paused rounds against base f3c39cf (apply on that base). evidence/raw/: full-run and mutation logs (4 MB, added with git add -f; they were excluded locally).
- scratch/, tools/: helper scripts of the earlier rounds.

OPEN DECISIONS (for the lead/demo session): (1) KS: the alert after an n8n kill during the send comes 13 min late; suggestion: clear alert claims at n8n start (one SQL node). (2) B21, B22, B23 (fix-5, fix-2, fix-10) paused by order after rounds 11, 13, 7; the last state is in the three snapshot patches and evidence/checkpoint-b2x.md. (3) Not run on v4: T8, T10, T11, T13, T14; a failed alert mark after a sent alert; GREP on Postgres-backed n8n; a credential needle.

RUNNING AGENTS: none. Nothing will still be written.

RESTART STEPS for a NEW cloud session: 1) read this block, then kill/RESULTS.md and kill/COMPARE-demo.md (the truth for my numbers; raw rows in kill/data/results.jsonl). 2) The stack is not in the repo: Node 24, n8n 2.46.6, Postgres 16 (db kill_t, port 55432), flow files from the demo branch (demo/handover, folders n8n-flows-v3, n8n-flows-v4, n8n-flows-film-v4); build the import files with kill/prepare_probe.py SRC OUT; run cases with kill/v3.py LABEL CASE and kill/harness.py LABEL POINT (env FLOW_PROBE, FLOW_COMMIT, LANE). 3) Paused rounds: apply evidence/snapshot-bNN patch on base f3c39cf only if the lead un-pauses them.

CHECKS (raw output, taken before this block's last commit; the re-run after the push is stated in my chat reply):
$ git status --porcelain
 M handover/demo3/REPORT.md
$ git status --ignored -s | head -50
 M REPORT.md
!! kill/__pycache__/
!! scratch/__pycache__/
!! scratch/foreignA/tools/__pycache__/
!! scratch/foreignB/tools/__pycache__/
!! scratch/foreignD/tools/__pycache__/
!! scratch/fs/cwd/empty.key
!! scratch/fs/cwd/in.key
!! scratch/fs/outside/dir/
!! scratch/fs/outside/outside.key
!! scratch/fs/tmp/tmp.key
$ git fetch origin; git log origin/demo/lane3..HEAD
$ git diff origin/demo/lane3 --stat
 handover/demo3/REPORT.md | 44 ++++++++++++++++++++++++++++++++------------
 1 file changed, 32 insertions(+), 12 deletions(-)
$ git stash list
$ git worktree list
/home/user/hadavin-sdk  e1a3e971 [demo/lane3]
$ ls /home/user/work/kill | wc -l (outside repo: probe copies of demo flows, pg data, n8n runs; not needed)
44
Ignored files that matter: none (scratch/fs/*.key are empty or made-up test fixtures for the key-file tests, recreated by scratch/fs_cases.sh; __pycache__ is generated).

WRAP-1 notes: Core r7v and EV7U: not mine (lane3 is the demo kill and alert lane), nothing of them here. Free disk 2.5 GB; I freed space only by deleting my own finished run folders (n8n user folders), never evidence. No secret-like strings (scan repeated). 0 agents, 0 processes. STOPPED: no further tool calls until an order starting with GO.
