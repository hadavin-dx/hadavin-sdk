17:01 UTC: BATCH 4 builder started on 3210f93a, clean tree. Next: edit receiver + tests
17:02 UTC: receiver, CHANGELOG, tests edited, 117 pass. Next: fail-before, mutants, gates, PG, full suite
17:07 UTC: design final (finally-based log + thread-local reported flag, log_message kinds). mutants running -> q8a2-fb4/mutants.log. Next: gates, PG, full suite
17:07 UTC: PG port 56083 data /home/user/build/pg-q8a2-b4 (stop+delete at end)
17:07 UTC: PG port 56083 data /home/user/build/pg-q8a2-b4 (stop+delete at end)
17:12 UTC: final src edit done; mutants + stage_mutants running; then commit, full suite, push
17:20 UTC: committed 0bed3fd0 locally (not pushed); full suite queued (q8a2-fb4/full-pytest.log)
17:26 UTC: added backlog fix (item from lead: 45/50 held connections), head c19d87dc local; mutants+stage_mutants running; full suite next (full.sh), then push
17:34 UTC: 14 receiver mutants killed, stage 37/37; full suite on c19d87dc started
17:41 UTC: full run 1 rc=1 (only test_migration_numbers quadratic timing test, flaky on 3210f93a too: 5 of 6 fail solo); rerunning once
17:48 UTC: BATCH 4 DONE head pushed ff; full rc=0 10845 passed 1 skipped; PG 56083 stopped+deleted; wt-old removed
