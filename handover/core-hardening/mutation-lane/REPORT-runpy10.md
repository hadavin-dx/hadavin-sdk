# REPORT-runpy10: run.py r9 and safety-tests.sh r9 (builder report; NOT self-approved)
Files are FINAL as of 15:33 UTC. Frozen byte-identical copies: evidence-r9/frozen/ (the final full run used them). r8 backups: run.r8.py, safety-tests.r8.sh.
sha256 run.py c81a7ba9f466587d2b967b312d8e1c60215ba1b7125799039a18dfec49673e6a ; safety-tests.sh b498dd0318c62d1baf98a7d437aab752851924d42e21d92689ed6ae917f8cbc5

## Failures and gaps first
1. It took FOUR full runs. Run 1 aborted by me at T42 (an old test T35c expected exit 0 from --restore with no marker: updated to the new 2). Run 2: 5 failed of 416 (T52b, T55b, T63c, T69c, T88-child): two REGRESSIONS of mine in run.py (my "two names" check refused a two-name file that already held the original; a settled control marker turned into exit 2). Run 3: 1 failed (T52b as root: marker mode 664 vs file 644, same check). Fixed in run.py, the tests were right. Run 4 (final files): `FAILED CHECKS: 0 (of 416 checks run)`, non-root child (uid 65534) `0 (of 61)`. Raw files: evidence-r9/full-run.txt (+ full-run-aborted..., full-run-2-five-failures.txt, full-run-3-one-failure-T52b.txt).
2. Behaviour change that may surprise: a file with two names that already holds the original is NOT chmod-ed any more (r8 changed the mode of the other name too); its mode stays as the tests left it. Content is what is verified.
3. Not done / limits (labels): (d) forged marker+backup with a matching hash and plain `--restore`: still accepted (same-user attacker can edit the target, run.py and tests directly; only --sha closes it, now also for the mode's execute bits). N5 setsid escape: impossible-now (needs cgroup/PID namespace; next step: run tests in one). N6/M1 root cause (a run whose TMPDIR is outside /tmp, /var/tmp, /dev/shm, TMP, TEMP is invisible): impossible-now to discover; mitigated by exit 2 and --sha; a fixed-location pointer file is a design choice for the lead (needs-lead). T96d proves doc and code agree only for the 4 scenarios listed plus the code set of exit codes, not every sentence. Dir fsync is proven by recorded calls, not by a power cut. T96f, T96b3, T96c3, T96h2, T96l2 and the T51b marker assertion are guards (pass on r8). Not run: nothing on other OS, no EGM skills, no git (not a repo), no R-numbers. Q29: run.py stays out of every PR; ruff check run.py: exactly the 2 known S603, 0 noqa; ruff format ok; bash -n ok.
4. Count difference to the independent r7 numbers (mine 33/61 root, 32/55 child; theirs 31/61, 33/67): NOT investigated. Likely different block lists and script versions (the child list differs: 55 vs 67 checks); I did not compare outputs.
5. Independent r8 run (0 of 395, child 0 of 41) read: nothing to fix. My first edits invalidated their first attempt; from now every evidence run of mine used frozen copies.

## Findings -> fix -> test -> fails on r8
Counts on r8 code (evidence-r9/new-tests-on-r8code.txt, T42 T51 T68 T96 as of 14:40, before T96h2/h3 and T35c/d were added): 15 failed of 68 (14 of the then 18 new T96 checks + T68). T96h3 and T35c fail on r8 by construction (r8 exits 0 / has no warning), not run on r8.
| Finding | Fix | Test | Fails on r8 |
|---|---|---|---|
| B1 docs vs code (restore exit 2 vs 0) | docstring table rewritten; code now matches (exit 2 = unknown, never "nothing planted") | T96d parses the table, maps 4 observed exits to rows, checks codes == EXIT_* | yes |
| M1 --restore exit 0 while planted | no marker anywhere + no --sha: exit 2 with both ways out; --sha: files compared with git (equal 0, different 3); settled control marker still 0 | T68, T35c/d, T96a, b, b2, c | yes |
| forged-marker exit 2 hint | text says exit 2 does not mean nothing is planted | T96h3 | yes |
| minor 1 signals before the first write | docstring exact; --restore --sha archive step interruptible (143) | T96j1 | yes (hung) |
| minor 2 no timeout on git/patch | run_cmd default 300 s, --helper-timeout, refusal | T96j2 | yes |
| minor 3 stranded stale marker | --restore --sha --discard-marker (tree must equal git, no live group) | T96e, e2 | yes |
| minor 4 T51b marker kept | assertion added | T51b | guard |
| minor 5 dir fsync | fsync_state_dir after write and unlink_state | T96k | yes |
| minor 6 chmod before nlink | check first; two-name file never chmod-ed | T96g, T52b, T63c | yes (T96g) |
| minor 7 targets in .venv/__pycache__ | safe_rel refuses | T96h (+h2 guard) | yes |
| minor 8 forged mode | --sha path compares execute bits; plain path = limit d | T96l | yes |
| minor 9 partial write | pinned with a 1 KiB file-size limit | T96f | guard |
| N4 gap output into state folder | refused (also --raw before mkdir) | T96i | yes |
| N6 gap | label above | - | - |
