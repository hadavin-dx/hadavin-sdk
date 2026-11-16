# Checkpoint repin7 (16:29 UTC / 21:59 IST)
Done: v7 script (lead-repin-verify.v7.sh), guide v7, mutate.py v17-v29, signals launcher fix, v7-CHANGES.md.
Found at 16:28: self-test HUP case failed (exit 0) in both shells because the batch was started with nohup (HUP ignored at entry; no script can catch it). Fixed: the case now says NOT TESTED when the caller ignores HUP. First batch stopped by me (my own pids only) and rerun without nohup at 16:29.
Next: read 11/11b/12/13/14 results, 1 MB timing, non-root run, banned-string count, 00-RESULTS.md. Stop 16:47.
Blockers: lead-repin-verify.sh still v6 (overwrite refused by the permission system); lead promotes v7.
