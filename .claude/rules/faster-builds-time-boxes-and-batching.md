---
name: faster-builds-time-boxes-and-batching
description: "Owner 2026-11-03: agents must be time-boxed (checkpoint note, stop at 60 min, resumed by a fresh agent), heavy jobs share 3 slots, batch repetitive runs, no polling loops"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3c13c170-55b8-4c77-8cca-2988a10a077d
  modified: 2026-11-03T15:36:02.765Z
---

Owner 2026-11-03: agents seem to run too long and loop; wanted a max agent time (summary written, stop, resume with a new agent from the note), fewer repeated heavy runs (batch them), and other ways to go faster without lowering quality.

Measured cause (2026-11-03 ~16:00 UTC): 14 agents + 10 Docker containers + 28 python processes at once = laptop CPU 100%, so every job ran several times slower. The lead broke its own max-4-heavy-jobs rule by launching 6 builders while 8 were running.

**Rules (apply to every brief and to the lead):**
1. Time box: every builder brief says "write a checkpoint note to egm\<topic>\checkpoint-<wp>.md every 30 min (done / next / blockers / commit SHA); at 60 min stop, commit, report". The lead checks ListAgents each turn; a builder past 60 min since its last start/resume gets TaskStop after it writes a note; a fresh agent resumes from the note. No polling loops: wait for one `gh pr checks --watch` with a timeout, or report and let the lead check.
2. Heavy jobs (full pytest, mutation run, Docker/Linux suite, Postgres suite) run ONLY through `python tools\heavy_slot.py --slots 3 --timeout 2400 -- <cmd>` (max 3 at once machine-wide).
3. Batch: while iterating run only the affected tests; ONE full suite, ONE sampled mutation run, ONE Linux container run per fix pass at the FINAL head (not per commit, not per finding); evidence for ten findings in one run.
4. Fix per CLASS, not per instance (rounds of whack-a-mole cost most: D10 four rounds, J8 two, PR50 eight); reviewers get a class checklist; stop at the owner's round caps except security/money paths.
5. One shared Postgres container for builders (separate database per builder) instead of one container each; reuse `uv` caches.
6. Reviews: launch the two reviewers in parallel from one snapshot; do not re-review unchanged files.
7. Max concurrent builders: 8 (lead's limit); more only if CPU stays under 70%.

**Why:** the owner wants speed without quality loss; repeated full runs and parallel heavy jobs were the biggest wastes.
**How to apply:** put rules 1-3 in every new brief; related [[parallel-agents-and-build-now]], [[review-loop-speed-rules]], [[keep-tool-output-small]].
