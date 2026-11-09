# Checkpoint bd-P4da2 (builder, PR75 round-1 fixes)

Done (uncommitted in worktree /home/user/build/B-P4da2 until the full suite ends): M1 constructor validation, M2 one kill-switch helper, M4 back-off pins (multiplier is valid in tenacity 9.2.1), M5 batched purge, M6 unweakened tests, agent-loop rounding rows, lock-order/SELECT-only/race proofs file, ceiling rows, suppressions removed (TRY004, type-ignore, S608, DTZ001, S106), uv.lock back to revision 5.
Next: one full suite on PG16, commit, push, report.
Blockers: none. Stray processes: pg cluster bpa2 (port 56175), stopped at the end.
