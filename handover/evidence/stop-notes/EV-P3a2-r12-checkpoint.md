# EV-P3a2-r12 evidence runner register
start 2026-11-11T15:37Z, time box 75 min (ends 16:52Z). Head 4d328e3d.
| id | purpose | started | expected end | state |
| worktree /home/user/build/EV-P3a2-4d328e3 | head | 15:38Z | end | live |
| venv /home/user/build/venv-evp3a2r12 | deps | 15:39Z | end | live |
| postgres /home/user/build/pg-evp3a2r12 port 56170 | test db | 15:39Z | end | starting |

## checkpoint 2026-11-11T15:52:11Z
done: full suite (rc 0), lint, bandit, scan, stage mutants (rc 0), step 5 (both settings), probes 6a/6b/6c (two passes), probe 7, gitleaks git (0), fail-before (rc 1: 68 failed, 1 collection error, 490 passed).
running: whole migrate mutant list via heavy.sh (log /home/user/build/evidence-raw/P3a2-4d328e3/migrate-mutants.log).
next: RESULTS.md, gitleaks dir, cleanup (stop postgres, drop postgres_fdw is moot once cluster removed, remove 2 worktrees + venv + pg dir).
not run: step 9 route probes and the split-word pass of 6c (my response writing them was stopped by a safety classifier; not retried).
