# B-PR89 r27 checkpoint 2
done: issues 1-9 coded and documented (runner, killer, derived/hand lists, pin counts, CHANGELOG round 27, manifest pins). mypy figure became 14 (my _narrowable adds a fifth os.getuid place); measured with mypy 2.4.1 overlay on 3.12.3 and 3.13. Fail-before runs done (fb logs in /home/user/build/B-PR89-r27-fb-*.log). FAILBEFORE-TABLE drafted in the worktree.
running: full mutant list as root and as nobody, full pytest (own PG port 56941), all via heavy.sh.
next: stage_mutants, gitleaks, evidence RESULTS, commit, push, pr-notes. Not committed yet (base 916c71ea).

# checkpoint 3 (01:20Z)
done: committed code at 6690bb5f (local branch). Root mutant list 329 of 329 good. Round-26 code as nobody: "folders between" is WRONG_REASON (PermissionError) = the bug proven. 
running: non-root full list, full pytest (full2.log), stage_mutants (queued via heavy.sh).
next: evidence files (RESULTS, FAILBEFORE-TABLE logs), gitleaks, evidence commit, push, pr-notes.
