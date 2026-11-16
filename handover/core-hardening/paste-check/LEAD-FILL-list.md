# LEAD-FILL-list (C3b v3, 2026-11-16). Questions only the lead can answer. None of these is invented in the patch.
How to use: each row is one marker `LEAD-FILL <n>` in the patched plan (`inputs/plan-wp6-resmoke-v5.md`). If the lead is happy with the default, change the marker to `LEAD-DECIDED <n>` in that place; if not, replace the text by the answer. The runner counts the markers before P-2 (RE-PIN line, step d): any marker left = STOP, so an unanswered question can only stop the run, never change it.
| n | question | safe default (what happens if nothing is answered) | who answers | where in the plan |
|---|---|---|---|---|
| 1 | What is the exact command text of `pastes\P-4b.sh`: what counts as an "n8n-shaped" process and as "unreadable"? (derive both from the final-head `n8n_kill.py`; the proposal below is only a starting point) | no command text = STOP: P-3a ends with STOP, P-3b prints a P-4b line | the lead (needs the final-head `n8n_kill.py`) | P-4b (step list), UNVERIFIED 15 |
| 1b | NEW (from the second reviewer, major 1): the positive control file `pastes\P-4b.control.txt`: first line `P-4b.sh sha256 <hash>`, then the raw output of one run while a stand-in process existed, at least one line | file missing, under 2 non-empty lines, or first line not holding the sha256 of `P-4b.sh` = STOP in P-3b (tested: evidence-c3f.md 4.3). Not decided by me: that the control is tied to the file by sha256 (my addition; drop it if you want a lighter rule) | the lead, when writing P-4b.sh | P-4b, P-3a, P-3b, row U1 |
| 2 | After a P-4b STOP: who ends the unreadable process, and where does the run resume? | the run stays stopped; the process is ended outside the run by the lead or the owner; resume ONLY at P-4b (run again, read-only), then P-5; P-1 is not repeated (it needs `$HOME/hadavin-smoke` absent); for a fresh start the lead deletes that folder and restarts at P-1; the runner does not run S13 and kills nothing | the lead (and the owner if the process is his) | P-4b (STOP and recovery) |
| 3 | Which pid is written for `<pid>` in R2? | only the pid in the register row of the n8n of this run (it equals the content of that n8n's `n8n.pid`), and only after the lead's yes in PROGRESS; any other pid = STOP | the lead | WORDS (placeholder list) |
| 4 | After `GONE-FAIL` with `kill exit=3`: may the runner run R2, and what if no n8n of this run is alive? | no R2 and no kill of any kind; n8n of this run still alive = STOP and wait for the lead; none alive = write that in PROGRESS and go on with the other S13 steps | the lead | R2, 13.1, 13.3 |
| 5 | Which commit is the final head of round 5, and is round 5 final? | the commit checked out in the `nlite-fix5` worktree when the lead runs the fill command; no re-pin before the lead says "final" | the lead | RE-PIN line |
| 6 | In which folder of the tar are `run_real_check_n8n.py` and `real-run-n8n.env.example` (H1, H2)? | the 0.1 loop and the fill command keep looking in `scripts/`; a count 0 is REC, an error text (missing file) is STOP for H1 and H2 like for every row | the lead | 0.1, RE-PIN line |
| 7 | Are the round-5 worktree folder `nlite-fix5` and branch `take/nlite-int-r5` exactly right? | not answered when P-2 starts = STOP | the lead | header, RE-PIN names check, UNVERIFIED 14 |
Not in the list because the patch fixes them itself: last-check command, one-session fill command, `eec6ba4` fallback command, wording-diff acceptance rule, `gone` fails on any exit other than 0, placeholder owners (in WORDS), slash direction, stray blank line, WORDS scope, "171 min" history rows, round-5 names check.

## PROPOSAL for item 1: body of `pastes\P-4b.sh` (NOT part of the plan; the lead may use, change or discard it)
Read-only scan by uid of /proc. Definition used (my guess, to be replaced by the lead's from the final-head `n8n_kill.py`): "this uid" = the owner of /proc/<pid> equals the uid that runs the script; "unreadable" = opening /proc/<pid>/environ for reading fails; "n8n-shaped" = the command line contains `n8n` (case-insensitive). It prints `P-4b-HIT pid=<n>` per process, nothing else, and exits 0 also when it finds nothing (a plain `grep` would exit 1). It does not use env.sh, `$T`, `$R` or `$P`.
```bash
#!/bin/bash
# P-4b (PROPOSAL, lead to replace): read-only. Prints one line per process of THIS uid whose /proc/<pid>/environ cannot be read
# and whose command line mentions n8n. Never kills. No env.sh, no $T/$R/$P. Always exits 0.
me=$(id -u)
for d in /proc/[0-9]*; do
  p=${d#/proc/}
  [ "$p" = "$$" ] && continue
  u=$(stat -c %u "$d" 2>/dev/null) || continue
  [ "$u" = "$me" ] || continue
  if ! { : < "$d/environ"; } 2>/dev/null; then
    if tr '\0' ' ' < "$d/cmdline" 2>/dev/null | grep -qiF n8n; then echo "P-4b-HIT pid=$p"; fi
  fi
done
exit 0
```
Tests (evidence-c3f.md 4.4; STUB tests on this Linux container, not WSL): `bash -n` and `dash -n` rc 0; as root with nothing n8n-named: no output, exit 0; as uid 65534 with no stub: no output, exit 0 (negative control); as uid 65534 with a stub process whose command line contains `n8n-stub` and that is not dumpable (prctl PR_SET_DUMPABLE 0, so its environ is unreadable to that uid): prints `P-4b-HIT pid=<n>`, exit 0 (positive control). Not tested: real WSL Ubuntu, a real unreadable n8n process, a process that shows its command line only to root, `hidepid` mounts.
Positive-control instructions for the lead (to make `pastes\P-4b.control.txt`): (1) save the final `P-4b.sh`; (2) start a stand-in of this user whose command line contains `n8n` and whose environ this user cannot read (the stub above used `prctl(PR_SET_DUMPABLE, 0)` from python as a non-root user; root cannot test this, root reads everything); (3) run the script once: `bash pastes/P-4b.sh > /tmp/p4b-run.txt; echo "exit=$?"`, it must print at least one `P-4b-HIT` line and `exit=0`; (4) write the control file: first line `P-4b.sh sha256 ` + the output of `sha256sum < pastes/P-4b.sh | cut -d' ' -f1`, then the lines of `/tmp/p4b-run.txt`; (5) end the stand-in by its exact pid (you started it); (6) any later edit of `P-4b.sh` needs steps 1 to 4 again (P-3b compares the hash); (7) note in PROGRESS how the stand-in was made.
