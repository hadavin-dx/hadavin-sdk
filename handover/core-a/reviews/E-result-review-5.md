# E result review 5: nit decisions

| Nit | Decision | Action |
|---|---|---|
| 1 read error at `__exit__` leaves flag | fix | `crash.py`: new `_look()` reports a refused read (PermissionError); `__exit__` then still runs `_disarm()` (same retry), reports "never fired" if deleted, "could not be deleted" if stuck. Directory/undecodable bytes stay "not armed, no error". Test `test_a_failed_read_when_leaving_the_block_still_deletes_the_flag`. |
| 2 docstring claim "nth does not advance on read error" untested | fix | Test `test_a_failed_read_does_not_advance_the_nth_count` (nth=2, read fails once, count not advanced, crash on the second counted call). |
| 3 misnamed test | fix | Renamed to `test_a_delete_refused_for_every_try_but_the_last_is_still_reported_as_never_fired`. |
| 4 global time.sleep patch, exact list | fix | `stub_unlink` records only calls equal to `_UNLINK_PAUSE_S`; other sleeps run for real. |
| 5 e41 ids, missing docstring, unused tmp_path | fix | Renamed to `e51`, docstring added to the second test, `tmp_path` removed from `stub_unlink` and its callers. |
| 6 lines over 100 | fix | Wrapped in crash.py (docstring lines, one more at line 45) and tests (4 lines plus 1 extra); ruff check and format clean. |
| 7 stale ticket text | fix | Ticket: "print marker" and "`print` is used once" now say `os.write(1, ...)`; the unverified list says `os.write`. The Python 3.12 on Windows claim for `_still_there` stays unverified on Windows (not run there). |
