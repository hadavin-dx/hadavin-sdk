# P3a-2 3c checkpoint (about 01:51 UTC, 07:21 IST)
Done (uncommitted in /home/user/build/B-P3a2-3c): dead comparison code and its tests deleted; promise table in docstring and CHANGELOG with a test; check_version label; could_not_run class name; non-plain-name skip in step 4 (test added); extension remedy text (test added); 17 mutants retired, 38 re-pointed; early-return check (7.8) with its own test (found and fixed one real early return in TPG); reduced outcome matrix (36 cells + 2 controls) passes on the head and fails 12 of 36 on 4d328e3d; gates ruff/format/bandit/scan_repo green.
Running: V-mutant killer discovery (/tmp/trial.log), single process, outside heavy.sh.
Next: write V mutants into tests/migrate_mutants.py, run both mutant lists via heavy.sh alone, full suite via heavy.sh, commit, push wip/cloud-p3a2-3c.
Not built: the generated 37x13 matrix with 200 compositions and 12 controls (ticket items 8 and 10): commit 5.

## 02:21 UTC update
Commit fb2166a2 local (not pushed). Batch 1 (V01-V60): 57 of 60 killed; V25 (mutation text), V45 and V48 (killers) fixed and re-queued. Queued via heavy.sh: mutants rest A (145 ids incl. V25 V45 V48, DB mutdb1), rest B (142, DB mutdb2), full suite (shared DB). Not built: generated 37x13 matrix (commit 5). Next: read logs, numbers mutants (40), commit, gitleaks (not installed), push wip/cloud-p3a2-3c.
